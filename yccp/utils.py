#!/usr/bin/env python2
# encoding: utf-8

__all__ = [
    "YamlLoader",
    "YamlDumper",
    "load",
    "dump",
]

import yaml

# if available, load c-based implementaiton
try:
    from yaml import CLoader as YamlLoader, CDumper as YamlDumper
except ImportError:
    from yaml import Loader as YamlLoader, Dumper as YamlDumper


####################################################
# convenience functions to load/dump with our tags #
####################################################


def load(obj, verbatim=False, name_cache="cache", **kw):
    "Load yaml from object."
    return yaml.load(obj, Loader=YamlLoader, **kw)


def dump(data, stream=None, **kw):
    "Return yaml representation."
    kwargs = {"default_flow_style": False}
    kwargs.setdefault("indent", 4)
    kwargs.update(kw)
    return yaml.dump(data, stream, Dumper=YamlDumper, **kwargs)
