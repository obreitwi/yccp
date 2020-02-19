# yccp

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.3675311.svg)](https://doi.org/10.5281/zenodo.3675311)

**Y**AML with pre-**C**omputed **C**ommon **P**arameters is a library for easy
parameter-file handling. It allows for simple computations on common parameters
which can then be referenced in the rest of the parameter file.

Furthermore, `yccp` provides convenience functions that ease the process of
generating parameter-files that are still human-readable afterwards.
The names of every parameter file is generated from pretty-formatted parameter
values.


# Pre-computed common parameters

In a given set of parameters, there often are interdependencies between some of
values. Some parameters might be scaled versions of others or represent some
form of normalization. An example would be realizing synapse loss by re-scaling
connection densities. These common parameters (i.e. the synapse loss) often
times appear in several locations in a given parameter file. When changing
these common parameters, it is easy to miss all occurrences - especially when
they appear as literals in the parameter file.

`yccp` allows for common parameters to be specified at the beginning of the 
YAML parameter file in a custom section. They can then be retrieved via a
custom `!get` YAML-tag.

Furthermore, `yccp` provides a simple `!eval` YAML-tag for evaluating
relatively simple python statements (we are in the parameter-file and not our
simulation code, after all). The given one liner have access to the `numpy`
module (imported as `np`) as well as all values computed in the `__prelude__`
section.

The `__prelude__` section represents a list of dictionaries which are evaluated
in-order (the order of evaluation within a dictionary is undefined!).


## Example

```yaml
__prelude__:
    - synapse_loss: 0.25
      foo: !eval 1+2 * np.arange(100)
      bar: 1024
    - foobar: !eval get.foo + get.bar

connection_density:
    from_a_to_b: !eval 0.9  * get.synapse_loss
    from_b_to_a: !eval 0.75 * get.synapse_loss

regularValue: !get bar
regularArray: !get foobar
regularValuePlusOne: !eval get.bar + 1

nestedValue:
    foo: !eval get.foobar.size
    bar: !get bar
```


# Generating parameter sweeps

`yccp` provides convenience functions that ease the process of generating
parameter-files that are still human-readable afterwards. See the
[example](examples/make_simple_sweep.py) for details:

## Example
```python
#!/usr/bin/env python
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
```

When executed, it produces:
```
19-01-18 21:29:16 INFO: Read parameters from /home/obreitwi/git/yccp/examples/simple.yaml.
19-01-18 21:29:16 INFO: Writing: /home/obreitwi/git/yccp/examples/foo_200-regular_1029/bar_4-ValP1_1033.yaml
19-01-18 21:29:16 INFO: Writing: /home/obreitwi/git/yccp/examples/foo_200-regular_1029/bar_4-ValP1_-1025.yaml
19-01-18 21:29:16 INFO: Writing: /home/obreitwi/git/yccp/examples/foo_300-regular_1029/bar_12-ValP1_1041.yaml
19-01-18 21:29:16 INFO: Writing: /home/obreitwi/git/yccp/examples/foo_300-regular_1029/bar_12-ValP1_-1017.yaml
19-01-18 21:29:16 INFO: Writing: /home/obreitwi/git/yccp/examples/foo_900-regular_1029/bar_10-ValP1_1039.yaml
19-01-18 21:29:16 INFO: Writing: /home/obreitwi/git/yccp/examples/foo_900-regular_1029/bar_10-ValP1_-1019.yaml
19-01-18 21:29:16 INFO: Wrote 6 parameter sets (6 unique names).
```


# `yccp-sbn`: Sort by numbers
```
Usage:
    yccp-sbn [-v] [-R] [-f KEY]... [-l KEY]... [-r KEY]... FILENAME...
    yccp-sbn -h | --help
    yccp-sbn --version

    Receives a bunch of FILENAMEs and sorts them according to the numbers
    contained in key-number pairs in the filename. A pair has the form
    <KEY>_<NUM>. Several pairs are conjoined by "-". NUM can be integers or
    floats (in regular or scientific notation).

    This script was written to sort the result-plots of parameter-sweeps
    in different orders before viewing them.

Options:
    -h --help         Show this help.

    --version         Show version.

    -v --verbose      Be verbose

    -r --reverse KEY  Order KEY in reverse.

    -R --reverse-all  Order all keys reverse. If -r is specified, those
                      keys will not be sorted in reverse.

    -f --first KEY    Sort by KEY first (in order of specification).

    -l --last KEY     Sort by KEY last (in order of specification).
```

# Requirements:
* Python 3 just [because](https://pythonclock.org/).
* [PyYAML](https://github.com/yaml/pyyaml)

