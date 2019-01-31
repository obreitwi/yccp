#!/usr/bin/env python2
# encoding: utf-8

import errno
import inspect
import itertools as it
import logging
import os
import os.path as osp

log = logging.getLogger(__name__.split(".")[0])

from .. import utils as u

from . import namers as n
from . import ranges as r
from . import transforms as t

__all__ = ["Sweep"]


class Sweep(object):
    """
        A sweep is the main object to generate ParameterSets.

        You can add Ranges, Transforms and filters (which are just functions
        ParameterSet -> bool).

    """
    # string to inserted between name components
    filename_component_sep = "-"

    def __init__(self):
        # one namer per folder
        self.namer_folders = []
        self.namer_file = []

        self.generator_functions = []
        self.filters = []

    def add(self, func):
        """
            Add `func` (a Transform or Range or any function object that maps
                ParameterSet -> Iterator over Parameters
        """
        if not (isinstance(func, t.Transform)
                or isinstance(func, r.Range)
                or inspect.isgeneratorfunction(func)):
            raise ValueError("{} is not a generator function.".format(
                func.__class__.__name__))

        self.generator_functions.append(func)

    def add_filter(self, filter):
        """
            Add a filter to trim the number of generated ParameterSets. A
            filter is as simple function that maps ParameterSet -> bool.
        """
        self.filters.append(filter)

    def add_namers_folder(self, *namers):
        """
            Add all namers for a new folder in the hierachy at once.
        """
        self.namer_folders.append(
            n.join(namers, sep=self.filename_component_sep))

    def dump(self,
             paramset,
             basefolder=None,
             write_files=True,
             overwrite_files=False,
             failOnOverwrite=True):
        """
            Generate new ParameterSets from paramset by applying all
            transforms, ranges and filters that were added.

            The ParameterSets will be generated under basefolder (or the
            current working directory if None specified).

            If write_files is False, no files will be written, but the
            ParamaterSets will be generated one by one (useful for test runs).
        """
        written_filenames = set()
        overwritten_files = set()
        for count, ps in enumerate(self.generate(paramset)):
            fn = self.get_filename(ps, basefolder=basefolder)

            if write_files:
                log.info("Writing: {}".format(fn))
                try:
                    ps.write(fn, overwrite=overwrite_files)
                    written_filenames.add(fn)
                except OSError as e:
                    if e.errno == errno.EEXIST and not failOnOverwrite:
                        overwritten_files.add(fn)
                    else:
                        raise
            else:
                log.info("Would write: {}".format(fn))
                written_filenames.add(fn)

        log.info("{} {} parameter sets ({} unique names).".format(
            "Wrote" if write_files else "Would write",
            count + 1, len(written_filenames)))
        if write_files:
            log.info("Name collision for {} files, overwrite set to {}".format(
                len(overwritten_files), str(overwrite_files)))

    def generate(self, paramset):
        for p in u.chain_generator_functions(
                self.generator_functions)(paramset):
            if all(f(p) for f in self.filters):
                yield p

    def get_filename(self, paramset, basefolder=None):
        """
            Get filename under which the ParameterSet should be written.

            It will be created under basefolder (or the current working
            directory if None specified).
        """
        if basefolder is None:
            basefolder = os.getcwd()

        components = [basefolder]
        components.extend((namer(paramset) for namer in self.get_namers()))

        return osp.join(*components) + ".yaml"

    def get_namers(self):
        return it.chain(self.namer_folders, (self.namer_file,))

    def set_namers_file(self, *namers):
        """
            Add another namer for the filename.
        """
        self.namer_file = n.join(namers, sep=self.filename_component_sep)
