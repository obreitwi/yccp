#!/usr/bin/env python2
# encoding: utf-8

import numpy as np
import yaml


from .utils import YamlLoader, YamlDumper, load


class RawExpression(object):
    """
        Helper class to make sure expression evaluation can be dumped in raw
        form.
    """

    def __init__(self, expression):
        self.expression = expression

    def dump(self, dumper):
        return dumper.represent_scalar(u"!ee", self.expression)


class RawCacheEntry(object):
    """
        Helper class to make sure expression evaluation can be dumped in raw
        form.
    """

    def __init__(self, expression):
        self.expression = expression

    def dump(self, dumper):
        return dumper.represent_scalar(u"!cc", self.expression)


class ExpressionEvaluatorWithCache(object):
    """
        Evaluate python expressions in the context of a cache.
    """

    class Cache(object):
        def __init__(self):
            self._data = {}

        def add(self, name, value):
            self._data[name] = value

        def __getattr__(self, name):
            return self._data[name]

        def dump(self, dct):
            dct.update(self._data)

    def __init__(self):
        # control whether we actually evaluate or
        self.evaluate = True
        self.cache_empty()

    def cache_add(self, name, value):
        self.cache.add(name, value)

    def cache_dump(self, dct):
        """
            Dump all contents into the given dictionary.
        """
        self.cache.dump(dct)

    def cache_empty(self):
        self.cache = self.Cache()

    def enable(self):
        self.evaluate = True

    def disable(self):
        self.evaluate = False

    def eval(self, value):
        if isinstance(value, (RawExpression, RawCacheEntry)):
            value = value.expression
        if not isinstance(value, basestring):
            return value
        return eval(value,
                    {"np": np},
                    {"cc": self.cache})

    def __call__(self, loader, node):
        value = loader.construct_scalar(node)
        if node.tag == "!cc":
            if self.evaluate:
                value = getattr(self.cache, value)
            else:
                value = RawCacheEntry(value)
        else:
            if self.evaluate:
                value = self.eval(value)
            else:
                value = RawExpression(value)
        return value


evaluate_expression = ExpressionEvaluatorWithCache()


# Constructors
yaml.add_constructor(u"!ee", evaluate_expression, Loader=YamlLoader)
yaml.add_constructor(u"!cc", evaluate_expression, Loader=YamlLoader)

# Representations
yaml.add_representer(RawExpression,
                     lambda dumper, re: re.dump(dumper),
                     Dumper=YamlDumper)
yaml.add_representer(unicode, lambda dumper, value:
                     dumper.represent_scalar(u'tag:yaml.org,2002:str', value),
                     Dumper=YamlDumper)


def load_data_with_cache(obj, cache_attr="cache", **kwargs):
    """
        Load a yaml with a little preprocessor.
    """
    filepos = None
    try:
        filepos = obj.tell()
    except AttributeError:
        pass

    # diable the expression evaluater because the cache is empty
    evaluate_expression.disable()
    evaluate_expression.cache_empty()

    raw_object = load(obj, **kwargs)
    evaluate_expression.enable()

    # compute cache if it exists
    if cache_attr in raw_object:
        for dct in raw_object[cache_attr]:
            for k, v in dct.iteritems():
                evaluate_expression.cache_add(
                    k, evaluate_expression.eval(v))

    if filepos is not None:
        obj.seek(filepos)

    final_object = load(obj, **kwargs)
    if cache_attr in raw_object:
        del final_object[cache_attr]

    final_object[cache_attr] = cache = {}
    evaluate_expression.cache_dump(cache)
    evaluate_expression.cache_empty()

    return final_object


def load_data_verbatim(obj, cache_attr=None, **kwargs):
    """
        Load data from object as is, without evaluating expressions.
    """
    # chache_attr is just to remove it from the kwargs dict passed to load
    evaluate_expression.disable()
    data = load(obj, **kwargs)
    evaluate_expression.enable()
    return data
