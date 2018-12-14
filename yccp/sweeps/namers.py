#!/usr/bin/env python
# encoding: utf-8

"""
    Namers are functions that take a ParameterSet and return a string that is
    to be inserted into the filename.

    This way the generated parameter files have more descriptive names than
    mere hashes etc.

    The easiest way to create namers for numerical-value is the
    `create_formatted_namer` function, but every function that takes a
    ParameterSet and returns a string is a valid namer.
"""

__all__ = [
        "create_formatted",
        "join",
    ]

import hashlib
import logging
log = logging.getLogger(__name__.split(".")[0])

from .. import utils
rget = utils.get_recursive


def create_custom(listOfPaths, name,
                  func=lambda lst: hashlib.md5(str(lst)).hexdigest(),
                  length=0):
    """Go through the listOfPaths and pass them together to a function given by user."""
    assert callable(func)

    def namer(paramset):
        lst = [rget(paramset.data, path) for path in listOfPaths]
        val = func(lst)
        val = val[:length] if length > 0 else val
        return "{}_{}".format(
            name,
            val)
    return namer


def create_formatted(path, name, value_format=".0f",
        format="{{name}}_{{value:{value_format}}}"):
    """
    Convenience function to generate a namer

    Create a namer that extracts a certain path  from the given ParameterSet
    and formats it with the given value_format-string (floating
    point/integer/scientific etc).

    Finally, in the generated filename the value will be presented under
    shortname (e.g. MyValueA).

    Example:

    create_formatted_namer(
        path=paramset-A/subparameters-B/my_value,
        name=valAB,
        value_format=.2f)

    takes a ParameterSet containing the following
        (...)
        paramset-A:
            (...)
            subparameters-B:
                (...)
                my_value: 42.4242123
                (...)
            (...)
        (...)

    and will add "valAB_42.42" somewhere in its name.
    """
    format = format.format(value_format=value_format)
    def formatter(paramset):
        value = rget(paramset.data, path)
        try:
            return format.format(name=name, value=value)
        except ValueError:
            log.error("Formatter {} received wrong value {} for value_format {}.".format(
                name, value, value_format))
            raise

    return formatter


def join(namers, sep="-"):
    """
    Convenience function that combines several namers into a single one.
    """
    def joined_namers(paramset):
        return sep.join(n(paramset) for n in namers)
    return joined_namers

