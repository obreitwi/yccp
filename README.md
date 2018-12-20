# yccp

_Please note: `yccp` is still under active development and not yet considered
fully stable!_

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
parameter-files that are still human-readable afterwards.


## Example
```python
import yccp
import os.path

sweep = yccp.sweeps.Sweep()

paramset = yccp.sweeps.ParameterSet("examples/simple.yaml")

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
