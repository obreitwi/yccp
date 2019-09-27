#!/usr/bin/env python
# encoding: utf-8
#
"""
    Everything related to meta-programming.
"""

import copy
import functools as ft
import logging
from pprint import pformat as pf

from . import utils as u

log = logging.getLogger(__name__.split(".")[0])


__all__ = [
        "InheritDefaults",
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

            for k,v in to_update.items():
                if k in all_nonrec_updates:
                    updated_defaults.setdefault(k, {}).update(v)
                else:
                    updated_defaults[k] = v
        for k,v in dct.get(mcs.attr_defaults, {}).items():
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
        cls, cls.__class__.attr_defaults))

    not_recursively_updated_attributes = getattr(
        cls, cls.__class__.attr_nonrec_update, set())

    # update the default parameters with whatever was proved
    for k, v in copy.deepcopy(parameters).items():
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
