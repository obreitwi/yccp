#!/usr/bin/env python2
# encoding: utf-8

import yccp

import os
import os.path as osp

DIRNAME = osp.dirname(osp.abspath(__file__))

if __name__ == "__main__":
    sweep = yccp.sweeps.Sweep()

    paramset = yccp.sweeps.ParameterSet(osp.join(DIRNAME, "simple.yaml"))

    sweep.add(yccp.sweeps.transforms.AddValue(path_to="regularValue", value=5))

    sweep.add(yccp.sweeps.ranges.Range(
        transforms=[
                yccp.sweeps.transforms.FactorValue(path_to="nestedValue/foo"),
                yccp.sweeps.transforms.SetValue(path_to="nestedValue/bar"),
            ],
        range_tuples=[
            (2, 4),
            (3, 12),
            (9, 10),
            (1, -1),
        ]))

    def custom_generator(paramset):
        # always make a copy so that the paramset is not modified inplace
        ps = paramset.copy()

        ps["regularValuePlusOne"] = ps["nestedValue/bar"] + ps["regularValue"]
        yield ps

        ps["regularValuePlusOne"] = ps["nestedValue/bar"] - ps["regularValue"]
        yield ps

    sweep.add(custom_generator)

    sweep.add_filter(lambda ps: ps["nestedValue/bar"] > 0)

    sweep.add_namers_folder(
        yccp.sweeps.namers.create_formatted("nestedValue/foo", "foo",
            value_format="d"),
        yccp.sweeps.namers.create_formatted("regularValue", "regular",
            value_format="d"),
    )

    sweep.set_namers_file(
        yccp.sweeps.namers.create_formatted("nestedValue/bar", "bar",
            value_format="d"),
        yccp.sweeps.namers.create_formatted("regularValuePlusOne", "ValP1",
            value_format="d"),
    )

    sweep.dump(paramset, basefolder=DIRNAME, write_files=True)


