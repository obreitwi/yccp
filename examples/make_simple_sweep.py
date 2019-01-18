#!/usr/bin/env python2
# encoding: utf-8

import os.path as osp

from yccp import sweeps


if __name__ == "__main__":
    # a sweep constitutes a set of transformations to perform on parameter set
    sweep = sweeps.Sweep()

    # Increase the toplevel value "regularValue" by 5.
    sweep.add(sweeps.transforms.AddValue(path_to="regularValue", value=5))

    # In the toplevel dictionary "nestedValue", set the two values "foo" and
    # "bar in tandem:
    # * foo <- 2, bar <- 4
    # * foo <- 3, bar <- 12
    # * foo <- 9, bar <- 10
    # * foo <- 1, bar <- -1
    # For each combination, a new parameter set is produced.
    sweep.add(sweeps.ranges.Range(
        transforms=[
                sweeps.transforms.FactorValue(path_to="nestedValue/foo"),
                sweeps.transforms.SetValue(path_to="nestedValue/bar"),
            ],
        range_tuples=[
            (2, 4),
            (3, 12),
            (9, 10),
            (1, -1),
        ]))

    # We can also generate new parametersets by applying a custom generator. A
    # generator takes a parameter set and yields as many new parameter sets as
    # it desires. Each new parameterset will be passed down the
    # "yccp.sweeps-pipeline".
    def custom_generator(paramset):
        # If we are planning to yield more than one parameter set, it is
        # advised to make a copy first.
        ps = paramset.copy()

        # Instead of several square brackets, yccp supports a shorter notation:
        # ps["nestedValue"]["bar"] -> ps["nestedValue/bar"]
        #
        # List elements can be accessed by specifying integer indices:
        # ps["nestedValue/bar/hypotheticalList/0/foobar"] = 42
        ps["regularValuePlusOne"] = ps["nestedValue/bar"] + ps["regularValue"]
        yield ps

        ps["regularValuePlusOne"] = ps["nestedValue/bar"] - ps["regularValue"]
        yield ps
    sweep.add(custom_generator)

    # We can apply filters (funtions that map parameter sets to bool). Only if
    # all filters return True for a given parameter set, it will be written to
    # disk.
    sweep.add_filter(lambda ps: ps["nestedValue/bar"] > 0)

    # The names for parameter sets can be auto generated:

    # Created one folder-level, the name consists of the integer-formatted
    # values for 'nestedValue/foo' and 'regularValue' that are renamed to give
    # foo_<int>-regular_<int>
    #
    # The utility yccp-sbn is provided to effectively sort over files/folders
    # that adhere to this naming scheme.
    sweep.add_namers_folder(
        sweeps.namers.create_formatted("nestedValue/foo", "foo",
                                       value_format="d"),
        sweeps.namers.create_formatted("regularValue", "regular",
                                       value_format="d"),
    )

    # Same for the name of the actual parameter-file. It will be called:
    # bar_<int>-ValP1_<int>.yaml
    #
    # The utility yccp-sbn is provided to effectively sort over files/folders
    # that adhere to this naming scheme.
    sweep.set_namers_file(
        sweeps.namers.create_formatted("nestedValue/bar", "bar",
                                       value_format="d"),
        sweeps.namers.create_formatted("regularValuePlusOne", "ValP1",
                                       value_format="d"),
    )

    scriptfolder = osp.dirname(osp.abspath(__file__))
    # Only now do we need to actually load the parameter set..
    paramset = sweeps.ParameterSet(osp.join(scriptfolder, "simple.yaml"))

    # ..and pass it to the Sweep-object to generate our actual parameter files.
    # We generate the parameter file in the same folder the script resides in.
    sweep.dump(paramset,
               basefolder=scriptfolder,
               write_files=True)
