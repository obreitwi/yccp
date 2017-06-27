#!/usr/bin/env python2
# encoding: utf-8

__all__ = [
    "YamlLoader",
    "YamlDumper",
    "load",
    "dump",
    "get_recursive",
    "set_recursive",
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


##########################################################
# convenience functions to retrieve data from deep dicts #
##########################################################

def get_recursive(base, path, sep="/"):
    """
        For every name in path seperated by `sep`, a new dictionary with that
        name will be created if `create==True`.

        If the name is a number it will descend into that element of the list.

        If the path is found it will be returned, otherwise None.
    """
    return retrieve_path(base, path, sep, create=False)


def set_recursive(base, path, value, sep="/"):
    """
        For every name in path seperated by `sep`, a new dictionary with that
        name will be created.

        If the name is a number it will descend into that element of the list
        or append to the list if the list is one shorter in length.

        If the name is 0 a new list will be created.

        If the path is found it will be returned, otherwise None.

        Afterwards key in path will be set to value.
    """
    split_path = path.split(sep)
    key = split_path[-1]
    path = sep.join(split_path[:-1])
    container = retrieve_path(base, path, sep, create=True)
    if container is not None:
        if key.isdigit():
            idx = int(key)
            if isinstance(container, list):
                if idx < len(container):
                    container[idx] = value
                elif idx == len(container):
                    container.append(value)
                else:
                    raise ValueError("List {} has wrong length.".format(path))

            else:
                raise ValueError("Expected list for path {}.".format(path))
        else:
            container[key] = value
    else:
        raise ValueError("Did not find path {}".format(path))


def retrieve_path(base, path, sep="/", create=False):
    """
        For every name in path seperated by `sep`, a new dictionary with that
        name will be created if `create==True`.

        If the name is a number it will descend into that element of the list
        or append to the list if the list is one shorter in length if
        `create==True`.

        If the name is 0 a new list will be created if `create==True`.

        If the path is found it will be returned, otherwise None.
    """
    if path is None or path == "/" or path == "":
        return base
    current = base
    completed_names = []
    split_path = path.split(sep)
    for i, name in enumerate(split_path):
        current_path = sep.join(completed_names)
        if name.isdigit():
            if isinstance(current, list):
                idx = int(name)
                if idx < len(current):
                    current = current[idx]
                elif idx == len(current) and create:
                    # append next type to current
                    if i+1 < len(split_path) and split_path[i+1].isdigit():
                        current.append([])
                    else:
                        current.append({})
                    current = current[idx]
                else:
                    return None
            else:
                return None
        elif name in current:
            current = current[name]
        elif create:
            # append next type to current
            if i+1 < len(split_path) and split_path[i+1].isdigit():
                current[name] = []
            else:
                current[name] = {}
            current = current[name]
        else:
            return None
        completed_names.append(name)
    return current


