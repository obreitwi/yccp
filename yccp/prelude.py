#!/usr/bin/env python
# encoding: utf-8

"""
    This submodule contains all functions related to loading and dumping
    yaml-data with our custom tags.
"""


__all__ = [
        "YccpDumper",
        "YccpLoader",
        "dump",
        "load",
    ]


import numpy as np
import yaml

# if available, load c-based implementaiton
try:
    from yaml import CLoader as YccpLoader, CDumper as YccpDumper
except ImportError:
    from yaml import Loader as YccpLoader, Dumper as YccpDumper


########
# tags #
########
yccp_tags = {
    "eval": ["!eval", "!ee"],
    "get":  ["!get",  "!cc"],
}
# "__prelude__" used to be called "cache" → keep it for backwards compatability
default_prelude_attr = ["__prelude__", "cache"]

####################################################
# convenience functions to load/dump with our tags #
####################################################

class RawExpression(object):
    """
        Helper class to make sure expression evaluation can be dumped in raw
        form.
    """

    def __init__(self, expression):
        self.expression = expression

    def dump(self, dumper):
        return dumper.represent_scalar("!eval", self.expression)


class RawPreludeEntry(object):
    """
        Helper class to make sure expression evaluation can be dumped in raw
        form.
    """

    def __init__(self, expression):
        self.expression = expression

    def dump(self, dumper):
        return dumper.represent_scalar("!get", self.expression)


class ExpressionEvaluatorWithPrelude(object):
    """
        Evaluate python expressions in the context of a prelude.
    """

    class Prelude(object):
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
        self.prelude_empty()

    def prelude_add(self, name, value):
        self.prelude.add(name, value)

    def prelude_dump(self, dct):
        """
            Dump all contents into the given dictionary.
        """
        self.prelude.dump(dct)

    def prelude_empty(self):
        self.prelude = self.Prelude()

    def enable(self):
        self.evaluate = True

    def disable(self):
        self.evaluate = False

    def eval(self, value):
        if isinstance(value, (RawExpression, RawPreludeEntry)):
            value = value.expression
        if not isinstance(value, str):
            return value
        eval_globals = {"np": np}
        eval_locals = {
                "get": self.prelude,
                # provide cc for backwards compatibility
                "cc": self.prelude
            }
        return eval(value, eval_globals, eval_locals)

    def __call__(self, loader, node):
        value = loader.construct_scalar(node)
        if node.tag in yccp_tags["get"]:
            if self.evaluate:
                value = getattr(self.prelude, value)
            else:
                value = RawPreludeEntry(value)
        elif node.tag in yccp_tags["eval"]:
            if self.evaluate:
                value = self.eval(value)
            else:
                value = RawExpression(value)
        return value


evaluate_expression = ExpressionEvaluatorWithPrelude()


# Constructors
for k, v in list(yccp_tags.items()):
    for tag in v:
        yaml.add_constructor(tag, evaluate_expression, Loader=YccpLoader)

# Representations
yaml.add_representer(RawExpression,
                     lambda dumper, re: re.dump(dumper),
                     Dumper=YccpDumper)
yaml.add_representer(str, lambda dumper, value:
                     dumper.represent_scalar('tag:yaml.org,2002:str', value),
                     Dumper=YccpDumper)


def dump(data, stream=None, **kw):
    "Return yaml representation."
    kwargs = {"default_flow_style": False}
    kwargs.setdefault("indent", 4)
    kwargs.update(kw)
    return yaml.dump(data, stream, Dumper=YccpDumper, **kwargs)


def load(obj, verbatim=False, **kwargs):
    """
        Load a yaml with a little preprocessor.

        The toplevel prelude-attribute `name_prelude` has to contain a list of
        value mappings in form of a dictionaries String -> String. The values
        will be evaluated and stored under their corresponding key in the prelude
        object (shorthand "cc"). Furthermore, the numpy library will be
        available under the shorthand "np".

        `name_prelude` can also be a list of attributes that will be tried in
        order until the first is found.

        If verbatim is enabled, expressions are not evaluated and instead kept
        in their raw form RawExpression.

        The object is parsed twice in total.
    """
    if verbatim:
        return load_data_verbatim(obj, **kwargs)
    else:
        return load_data_with_prelude(obj, **kwargs)


def load_data_verbatim(obj, name_prelude=None, **kwargs):
    """
        Load data from object as is, without evaluating expressions.
    """
    # chache_attr is just to remove it from the kwargs dict passed to load
    evaluate_expression.disable()
    data = load(obj, **kwargs)
    evaluate_expression.enable()
    return data


def load_data_with_prelude(obj, name_prelude=default_prelude_attr, **kwargs):
    """
        Load a yaml with a little preprocessor.
    """
    filepos = None
    try:
        filepos = obj.tell()
    except AttributeError:
        pass

    # disable the expression evaluater and empty prelude
    evaluate_expression.disable()
    evaluate_expression.prelude_empty()

    raw_object = raw_load(obj, **kwargs)
    evaluate_expression.enable()

    prelude = None
    # find prelude under different names
    if not isinstance(name_prelude, list):
        name_prelude = [name_prelude]
    for name_prelude_found in name_prelude:
        if name_prelude_found in raw_object:
            prelude = raw_object[name_prelude_found]
            break

    # compute prelude if it exists
    if prelude is not None:
        if isinstance(prelude, dict):
            prelude = [prelude]
        elif not (isinstance(prelude, list)
                  and all((isinstance(v, dict) for v in prelude))):
            raise ValueError(
                "The {} attribute needs to be either a dictionary or a list "
                "of dictionaries".format(name_prelude_found))

        for dct in prelude:
            for k, v in dct.items():
                evaluate_expression.prelude_add(
                    k, evaluate_expression.eval(v))

    if filepos is not None:
        obj.seek(filepos)

    final_object = raw_load(obj, **kwargs)
    if name_prelude_found in raw_object:
        del final_object[name_prelude_found]

    final_object[name_prelude_found] = prelude = {}
    evaluate_expression.prelude_dump(prelude)
    evaluate_expression.prelude_empty()

    return final_object


def raw_load(obj, verbatim=False, name_prelude=default_prelude_attr, **kw):
    "Load yaml from object."
    return yaml.load(obj, Loader=YccpLoader, **kw)
