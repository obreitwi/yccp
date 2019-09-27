#!/usr/bin/env python
# encoding: utf-8

"""
    Transformators used in sweeps.
"""

from .. import meta as _m
from .. import utils as _u


class Transform(object, metaclass=_m.InheritDefaults):
    """
        Transform a single parameter set.
    """

    default_parameters = {}

    def apply(self, paramset):
        """
            Transform dataset.
        """
        self.modify(paramset)
        self.record(paramset)
        return paramset

    def __call__(self, paramset):
        new = paramset.copy()
        self.apply(new)
        yield new

    def modify(self, paramset):
        """
            Actually modify the parameter set.
        """
        raise NotImplementedError

    def describe(self, paramset):
        """
            Return an object describing the transformation.
        """
        raise NotImplementedError

    def record(self, paramset):
        """
            Record that this transformation took place.
        """
        paramset.metainfo["transforms"].append({
                "name" : self.__class__.__name__,
                "description" : self.describe(paramset),
            })


class SetValue(Transform):
    """
        Set a single value.
    """

    default_parameters = {
                # path_to where to find the value to set
                "path_to" : None,
                # self-explanatory
                "value" : None,
            }

    def set_value(self, value):
        """
            Change the used value after the fact (i.e. from Ranges).
        """
        self.prms["value"] = value

    def modify(self, paramset):
        _u.set_recursive(paramset.data,
                self.prms["path_to"], self.prms["value"])

    def describe(self, paramset):
        """
            Return an object describing the transformation.
        """
        return "Changed {} to {}.".format(
                self.prms["path_to"],
                self.prms["value"])


class CopyValue(Transform):
    """
        Copy one value.
    """

    default_parameters = {
            "path_from" : None,
            "path_to" : None,
        }

    def modify(self, paramset):
        assert self.prms["path_from"] is not None
        assert self.prms["path_to"] is not None

        value = _u.get_recursive(paramset.data, self.prms["path_from"])
        _u.set_recursive(paramset.data, self.prms["path_to"], value)

    def describe(self, paramset):
        return "Copied {} to {} ({})".format(
                self.prms["path_from"],
                self.prms["path_to"],
                _u.get_recursive(paramset.data, self.prms["path_from"])
            )


class AddValue(SetValue):
    """
        Add a single value to a given (this can also be used for appending
        strings).
    """
    default_parameters = {
                # if not None, this value will be used as original instead.
                "path_from" : None,
            }

    def get_orig_value(self, paramset):
        if self.prms["path_from"] is not None:
            self.orig_value = _u.get_recursive(paramset.data,
                self.prms["path_from"])
        else:
            self.orig_value = _u.get_recursive(paramset.data,
                self.prms["path_to"])

    def modify(self, paramset):
        self.get_orig_value(paramset)
        self.final_value = self.orig_value + self.prms["value"]
        _u.set_recursive(paramset.data,
                self.prms["path_to"], self.final_value)

    def describe(self, paramset):
        return "Added {} to {} ({} -> {}){}.".format(
                self.prms["value"],
                self.prms["path_to"],
                self.orig_value,
                self.final_value,
                "" if self.prms["path_from"] is None else
                    " [taken from {}]".format(self.prms["path_from"]))


class FactorValue(AddValue):
    """
        Multiply a single value with a factor.
    """

    def modify(self, paramset):
        self.get_orig_value(paramset)

        self.final_value = self.orig_value * self.prms["value"]
        _u.set_recursive(paramset.data,
                self.prms["path_to"],
                self.final_value)

    def describe(self, paramset):
        """
            Return an object describing the transformation.
        """
        return "Multiplied {} by {} ({} -> {}){}.".format(
                self.prms["path_to"],
                self.prms["value"],
                self.orig_value,
                self.final_value,
                "" if self.prms["path_from"] is None else
                    " [taken from {}]".format(self.prms["path_from"]))


class ApplyFunction(AddValue):
    """
    Apply the path_from value to function and save in path_to
    """
    default_parameters = {
        "path_from": None,
        "path_to": None,
        "function": None,
    }

    def modify(self, paramset):
        assert callable(self.prms['function'])
        self.get_orig_value(paramset)

        self.final_value = self.prms['function'](self.orig_value)
        _u.set_recursive(
            paramset.data,
            self.prms["path_to"],
            self.final_value)

    def describe(self, paramset):
        """
            Return an object describing the transformation.
        """
        assert callable(self.prms['function'])
        import inspect
        try:
            function_name = inspect.getsource(self.prms["function"])
        except IOError:
            function_name = "a function"
        return "applied {} to {} and saved at {} ({} -> {}).".format(
            function_name,
            self.prms["path_from"],
            self.prms["path_to"],
            self.orig_value,
            self.final_value,
        )


class ApplyFunctionElaborate(AddValue):
    """
    Apply the values of given dict to function and save in path_to
    """
    default_parameters = {
        "dict": {},
        "path_to": None,
        "function": None,
        "orig_values": {},
    }

    def get_orig_value(self, paramset):
        self.orig_values = {}
        for local_key, yaml_key in self.prms['dict'].items():
            self.orig_values[local_key] = _u.get_recursive(
                paramset.data,
                yaml_key)

    def modify(self, paramset):
        assert callable(self.prms['function'])
        self.get_orig_value(paramset)

        self.final_value = self.prms['function'](**self.orig_values)
        _u.set_recursive(
            paramset.data,
            self.prms["path_to"],
            self.final_value)

    def describe(self, paramset):
        """
            Return an object describing the transformation.
        """
        assert callable(self.prms['function'])
        import inspect
        try:
            function_name = inspect.getsource(self.prms["function"])
        except IOError:
            function_name = "a function"
        return "applied {} to {} and saved at {} ({} -> {}).".format(
            function_name,
            self.prms["dict"],
            self.prms["path_to"],
            self.orig_values,
            self.final_value,
        )


class DeleteValues(Transform):
    """
        Deletes the selected values from the parameterset.
    """

    default_parameters = {
            "paths" : [],
        }

    def modify(self, paramset):
        for path_to in self.prms["paths"]:
            split = path_to.split("/")
            if len(split) > 0:
                base = _u.get_recursive(paramset.data, "/".join(split[:-1]))
            else:
                base = paramset.data
            if base is not None:
                try:
                    del base[split[-1]]
                except KeyError:
                    pass

    def describe(self, paramset):
        return "Removed paths: \n" + "\n".join(self.prms["paths"])


