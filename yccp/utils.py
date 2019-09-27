#!/usr/bin/env python
# encoding: utf-8

__all__ = [
    "get_recursive",
    "set_recursive",
    "update_dict_recursively",
    "chain_generator_functions",
]

import collections as c
import copy

##########################################################
# convenience functions to retrieve data from deep dicts #
##########################################################

def get_recursive(dct, path, default=None, sep="/"):
    """
        For every name in path seperated by `sep`.

        If the name is a number it will descend into that element of the list.

        If the path is found it will be returned, otherwise `default`.
    """
    retval = retrieve_path(dct, path, sep, create=False)
    if retval is None:
        if default is None:
            raise KeyError("YCCP: Did not find {} in the given document. "
                           "Skip this by giving sensible (not None) default".format(path))
        retval = default
    return retval


def set_recursive(dct, path, value, sep="/"):
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
    container = retrieve_path(dct, path, sep, create=True)
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


def retrieve_path(dct, path, sep="/", create=False):
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
        return dct
    current = dct
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


##########################################################
# regular convenience functions                          #
##########################################################

def update_dict_recursively(d, u):
    """
        Dictionary d with the contents from u in recursive manner.
    """
    for k, v in copy.deepcopy(u).items():
        if isinstance(v, c.Mapping):
            if k in d and not isinstance(d.get(k), c.Mapping):
                raise ValueError(
                        "Only dictionaries should be updated recursively")
            d[k] = update_dict_recursively(d.get(k, {}), v)
        else:
            d[k] = v
    return d


def chain_generator_functions(generator_functions):
    """
        Takes a list of functions that take one value and return generators and
        successively applies them.

        Returns a single generator over all generators returned by the
        generator_functions for all inputs.

        Note: This function currently does NOT check if the generators modify
        an item inplace!
    """
    def chained(start_value):
        generators = [generator_functions[0](start_value)]

        while len(generators) > 0:
            try:
                value = next(generators[-1])

                if len(generators) < len(generator_functions):
                    generators.append(
                            generator_functions[len(generators)](value))

                else:
                    yield value

            except StopIteration:
                generators.pop()
    return chained
