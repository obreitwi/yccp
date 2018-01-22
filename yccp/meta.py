#!/usr/bin/env python2
# encoding: utf-8
#
"""
    Everything related to meta-programming.
"""

import copy
import functools as ft
import logging

from . import utils as u

log = logging.getLogger(__name__.split(".")[0])

__all__  = [
        "InheritDefaults",
        # These two have not been tested yet, only copied from SEMf
        #  "Registry",
        #  "RegistryBaseclass",
    ]

class InheritDefaults(type):
    """
        Classes inherit a `default_parameters` dictionary from their ancestors
        that represents keyword arguments which can be updated when creating an
        object of the given type.

        Subclasses can overwrite and update parameters by adjusting the
        `default_parameters` dictionary as well as discard parameters via the
        `discard_parameters` dictionary.

        Per default all dictionaries are recursively updated, i.e., the
        dictionary in the default parameters is updated with the supplied
        dictionary and not replaced. If some dictionary-type parameters should
        only be replaced "as a whole" , they have to be added to the
        `_no_recursive_update`-attribute.

        Note: __init__-functions should not accept any further arguments! It is
        only intended for initialization, the class has a prms-attribute after
        all.

        Note #2: In order to avoid possible naming conflicts, names of all
        attributes used by the meta-class can be customized if needed.
    """

    attr_defaults = "default_parameters"
    attr_discard = "discard_parameters"
    attr_parameters = "prms"
    attr_nonrec_update = "_no_recursive_update"

    func_get_parameters = "_get_updated_parameters"

    def __new__(mcs, name, bases, dct):
        updated_defaults = {}

        # update the parent classes default dict with our own
        #
        # NOTE: If there are several parent classes with the same key but
        #       different values, the user should make sure to define his
        #       own in the subclass. No guarantee is given which value will
        #       be used as default.

        all_nonrec_updates = []
        if mcs.attr_nonrec_update in dct:
            all_nonrec_updates = dct[mcs.attr_nonrec_update]
            assert isinstance(all_nonrec_updates, (list, set)), \
                "'{}.{}' should be of type list, got '{}' instead.".format(
                        name,
                        mcs.attr_nonrec_update,
                        all_nonrec_updates.__class__.__name__)

        else:
            # per default, recursively update all dictionaries
            all_nonrec_updates = []

        all_nonrec_updates = set(all_nonrec_updates)

        for base in (b for b in reversed(bases)
                if hasattr(b, mcs.attr_nonrec_update)):
            # update the recursive parameters
            nonrec_updates = getattr(base, mcs.attr_nonrec_update)

            all_nonrec_updates |= set(nonrec_updates)

        for base in (b for b in reversed(bases)
                if hasattr(b, mcs.attr_defaults)):
            to_update = copy.deepcopy(getattr(base, mcs.attr_defaults))

            if log.getEffectiveLevel() <= logging.DEBUG:
                log.debug("Updating from base {}: {}".format(base.__name__,
                    pf(to_update)))

            for to_delete in dct.get(mcs.attr_discard, []):
                if to_delete in to_update:
                    if log.getEffectiveLevel() <= logging.DEBUG:
                        log.debug("Deleting {} of base {}.".format(to_delete,
                            base.__name__))
                    del to_update[to_delete]

            for k,v in to_update.iteritems():
                if k in all_nonrec_updates:
                    updated_defaults.setdefault(k, {}).update(v)
                else:
                    updated_defaults[k] = v
        for k,v in dct.get(mcs.attr_defaults, {}).iteritems():
            if k in all_nonrec_updates:
                updated_defaults.setdefault(k, {}).update(v)
            else:
                updated_defaults[k] = v

        mcs.update_init_if_needed(name, bases, dct)

        dct[mcs.attr_defaults] = updated_defaults
        dct[mcs.func_get_parameters] = classmethod(_get_updated_parameters)
        dct[mcs.attr_nonrec_update] = list(all_nonrec_updates)

        return super(InheritDefaults, mcs).__new__(
                mcs, name, bases, dct)

    @classmethod
    def update_init_if_needed(mcs, name, bases, dct):
        """
            Updates the __init__ function so that upon class creation, the
            default parameters are automatically updated by supplied kwargs and
            made available via the 'prms'-attribute.
        """

        def plain_init(self, *args, **kwargs):
            pass

        init = dct.get("__init__", plain_init)

        @ft.wraps(init)
        def wrapped_init(self, *args, **kwargs):
            if len(args) > 0:
                raise ValueError(
                    "{} can only be instanciated with kwargs!".format(
                        self.__class__.__name__))

            # we need to make sure that the parameters haven't been set in a
            # derived class already!
            if not hasattr(self, mcs.attr_parameters):
                # retrieve parameter update function
                getparams = getattr(self, mcs.func_get_parameters)
                # update parameter with supplied kwargs
                params = getparams(kwargs)
                # set parameters correspondingly
                setattr(self, mcs.attr_parameters, params)

            # call original __init__ function (or the dud above)
            init(self)

        dct["__init__"] = wrapped_init


def _get_updated_parameters(cls, parameters):
    """
        Updates the default parameters with the parameters in `parameters`,

        but only if they are already present in the default dictionary.

        Returns the updated dictionary.
    """
    if log.getEffectiveLevel() <= logging.DEBUG:
        log.debug("Supplied parameters for {}:\n".format(
            cls.__name__) + pf(parameters))
    # get a deep-copy of the default parameters to be updated
    prms = copy.deepcopy(getattr(
        cls, cls.__metaclass__.attr_defaults))

    not_recursively_updated_attributes = getattr(
        cls, cls.__metaclass__.attr_nonrec_update, set())

    # update the default parameters with whatever was proved
    for k, v in copy.deepcopy(parameters).iteritems():
        if k in prms:
            if isinstance(v, dict)\
                    and k not in not_recursively_updated_attributes:
                u.update_dict_recursively(prms[k], v)
            else:
                prms[k] = v
        else:
            warning = "Parameter-Mismatch: "\
                + "`{0}` no parameter of class {1}!".format(
                    k, cls.__name__)
            log.warn(warning)
            raise ValueError(warning)

    if log.getEffectiveLevel() <= logging.DEBUG:
        log.debug("Updated Parameters for {0}:\n{1}".format(
            cls.__name__, pf(prms)))

    return prms


# REGISTRY
#
# The registry allows to refer to classes via strings which should help when
# pickling/storing parameters between network runs.

class Registry(type):
    """
        Establishes a registry for the baseclass (that should be
        abstract, otherwise use RegistryBaseclass) and allows subclasses to be calls via
        baseclass.make(subclass_name, *args, **kwargs)
    """

    baseclass_attribute = "_registry_base"


    def __new__(mcs, name, bases, dct):
        reg_base = mcs.find_registry_base(bases)
        if reg_base is None:
            return mcs.setup_baseclass(name, bases, dct)
        else:
            return mcs.register_subclass(reg_base, name, bases, dct)


    @classmethod
    def find_registry_base(mcs, bases):
        """
            Tries to find the baseclass containing a registry

            return None if None could be found
        """
        possible_bases = [b for b in bases]
        while len(possible_bases) > 0:
            reg_base = possible_bases.pop(0)

            if getattr(reg_base, mcs.baseclass_attribute, False):
                # we found the correct baseclass (there should only be one!)
                break
            else:
                possible_bases.extend(
                    (b for b in reg_base.__bases__ if b not in possible_bases))
        else:
            reg_base = None

        return reg_base


    @classmethod
    def setup_baseclass(mcs, name, bases, dct):
        log.debug("Setting up registry in class {0}".format(name))
        dct["_registry"] = {}
        dct["_registry_aliases"] = {}
        dct[mcs.baseclass_attribute] = True
        dct["make"] = classmethod(mcs.make)
        dct["exists"] = classmethod(mcs.exists)
        dct["alias_exists"] = classmethod(mcs.alias_exists)
        dct["_register"] = classmethod(mcs.register)
        dct["_register_alias"] = classmethod(mcs.register_alias)
        dct["get_reversed_aliases"] = classmethod(mcs.get_reversed_aliases)
        dct["get"] = classmethod(mcs.get)
        dct["list_entries"] = classmethod(mcs.list_entries)
        dct["list_alias_entries"] = classmethod(mcs.list_alias_entries)

        return super(Registry, mcs).__new__(mcs, name, bases, dct)


    @classmethod
    def register_subclass(mcs, reg_base, name, bases, dct):
        log.debug("Adding {0} to registry in class {1}".format(name,
            reg_base.__name__))
        dct[mcs.baseclass_attribute] = False
        # search for the appropriate baseclass containing the registry

        successful_aliases = []
        if "alias" in dct:
            aliases = [a.lower() for a in ensure_list(dct["alias"])]
            del dct["alias"]
            for alias in aliases:
                if reg_base._register_alias(alias, name):
                    successful_aliases.append(alias)

        docfuncs = dct.setdefault("_doc_update_funcs", [])
        if len(successful_aliases):
            docfuncs.append(ft.partial(mcs.prepend_alias,
                aliases=successful_aliases))

        # we found the baseclass, now add the name of our class in lower case to
        # it
        cls = super(Registry, mcs).__new__(mcs, name, bases, dct)
            # UNDELME
            # dct["__doc__"] = mcs.prepend_alias(successful_aliases,
                    # dct["__doc__"])
        return reg_base._register(name.lower(), cls)

    @staticmethod
    def prepend_alias(docstring, aliases):
        split_up_docstring = docstring.split("\n")
        whitespace = formatting.find_whitespace(split_up_docstring)
        return "{}Aliases: {}\n{}".format(
                whitespace, ", ".join(aliases), docstring)

    @staticmethod
    def make(self, name, *args, **kwargs):
        return self.get(name.lower())(*args, **kwargs)

    @staticmethod
    def exists(self, name):
        return name.encode().lower() in self._registry

    @staticmethod
    def alias_exists(self, alias):
        return alias.encode().lower() in self._registry_aliases

    @staticmethod
    def get_reversed_aliases(self):
        rev_aliases = {}
        for k,v in self._registry_aliases.iteritems():
            rev_aliases.setdefault(v, []).append(k)
        return rev_aliases

    @staticmethod
    def get(self, name):
        name_encoded = name.encode().lower()
        if self.exists(name):
            return self._registry[name_encoded]
        elif self.alias_exists(name):
            return self._registry[self._registry_aliases[name_encoded]]
        else:
            raise KeyError("{} not found in baseclass {}.".format(name,
                self.__name__))


    @staticmethod
    def register(self, name, mcs):
        """
            Registers the following class in the registry under the specified
            name.
        """
        log.debug("Registering {0} as {1}".format(
            mcs.__name__, name))
        if name not in self._registry:
            self._registry[name] = mcs
        else:
            log.error("When trying to register {0}. "\
                    "Name {1} already used in registry!".format(
                        mcs.__name__, name))
        return mcs

    @staticmethod
    def register_alias(self, alias, name):
        """
            Registers an alias for name.

            Returns whether the alias was successfully added.
        """
        log.debug("Registering {} as alias for {}.".format(
            alias, name))
        if not self.alias_exists(alias):
            log.debug("Registering alias {} for class {}.".format(
                alias, name))
            self._registry_aliases[alias.encode().lower()] = name.encode().lower()
            return True

        else:
            # if log.getEffectiveLevel() <= logging.DEBUG:
            log.warn("Alias {} for class {} already exists!".format(
                    alias, name))
            return False

    @staticmethod
    def list_entries(self):
        """
            List all registry entries.
        """
        return sorted(self._registry.keys())

    @staticmethod
    def list_alias_entries(self):
        """
            List all registry entries.
        """
        return sorted(self._registry_aliases.keys())


_baseclass_registry = {}

def get_baseclass(name):
    return _baseclass_registry[name.encode().lower()]

def baseclass_exists(name):
    return name.encode().lower() in _baseclass_registry

def list_baseclasses():
    return _baseclass_registry.keys()

def register_baseclass(name, mcs):
    _baseclass_registry[name.lower()] = mcs
    return mcs


class RegistryBaseclass(Registry):
    "Also registers baseclasses to a registry."

    @classmethod
    def setup_baseclass(mcs, name, bases, dct):
        cls = super(RegistryBaseclass, mcs).setup_baseclass(
                                                     name, bases, dct)
        return register_baseclass(name, cls)

