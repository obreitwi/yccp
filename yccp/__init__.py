#!/usr/bin/env python2
# encoding: utf-8

__all__ = [
        "RawCacheEntry",
        "RawExpression",
        "__version__"
        "dump",
        "rget",
        "load",
        "rset",
    ]

from .cache import RawCacheEntry
from .cache import RawExpression
from .cache import load_data_verbatim
from .cache import load_data_with_cache

from .version import __version__
from .utils import dump, get_recursively, set_recursively


def load(obj, verbatim=False, **kwargs):
    """
        Load a yaml with a little preprocessor.

        The toplevel cache-attribute `cache_attr` has to contain a list of
        value mappings in form of a dictionaries String -> String. The values
        will be evaluated and stored under their corresponding key in the cache
        object (shorthand "cc"). Furthermore, the numpy library will be
        available under the shorthand "np".

        If verbatim is enabled, expressions are not evaluated and instead kept
        in their raw form RawExpression.

        The object is parsed twice in total.
    """
    if verbatim:
        return load_data_verbatim(obj, **kwargs)
    else:
        return load_data_with_cache(obj, **kwargs)


rget = get_recursively
rset = set_recursively
