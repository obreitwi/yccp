
"""
    ParameterSet and related concepts.
"""


from .. import utils as u
from .. import prelude as pl

import copy
import os
import os.path as osp

import logging
log = logging.getLogger(__name__.split(".")[0])


__all__ = ["ParameterSet"]


class ParameterSet(object):
    """
        ParameterSet to keep track of changes.
    """

    def __getitem__(self, key):
        return u.get_recursive(self.data, key)

    def __init__(self, filename=None, verbatim=False):
        """Create a new dataset.

        Args:
            filename:
                If not None, load an existing parameter set (i.e. a YAML-file)
                from disk.

            verbatim:
                If True, do not resolve the yccp-specific YAML tags (e.g., !get
                and !eval). Instead, they will be mapped to regular strings.
                The parameter set will be loaded as it  is on disk (i.e.,
                verbatim).

        Returns:
            The created ParameterSet.
        """
        self.data = {}
        if filename is not None:
            self.load(filename, verbatim=False)

    def __setitem__(self, key, value):
        u.set_recursive(self.data, key, value)

    def copy(self):
        """
            Return a copy of this ParameterSet.
        """
        cp = self.__class__()
        cp.data = copy.deepcopy(self.data)

        return cp

    def load(self, filename, verbatim=False):
        """
            Load data from a certain yaml file.

            verbatim == True does not resolve the cache or any !ee tags.
        """
        base, ext = osp.splitext(filename)

        if ext == "":
            log.debug("No extention found, assuming yaml.")
            ext = ".yaml"

        if ext not in [".yaml"]:
            log.error("Unsupported input file format.")

        param_filename = base+ext

        with open(param_filename, "r") as f:
            self.data = pl.load(f, verbatim=verbatim)

        self.setup_metadata(param_filename)

        log.info("Read parameters from {}.".format(param_filename))

    @property
    def metainfo(self):
        return self.data.get("_metainfo", {})

    def setup_metadata(self, orig_file):
        self.data["_metainfo"] = {
                "original_file": osp.abspath(orig_file),
                "transforms": [],
            }

    def write(self, filename, overwrite=False, failOnOverwrite=True):
        """
            Dump data into filename.
        """
        if not filename.endswith(".yaml"):
            filename += ".yaml"

        folder = osp.dirname(filename)
        if not osp.isdir(folder):
            log.info("Creating folder: {}".format(folder))
            os.makedirs(folder)

        if osp.isfile(filename) and not overwrite:
            log.error(
                "File {} exists and overwrite was not set to True".format(
                    filename))
            if failOnOverwrite:
                exit()
            else:
                return 1
        else:
            with open(filename, "w") as f:
                pl.dump(self.data, stream=f)
                return 0
