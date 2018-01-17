#!/usr/bin/env python2
# encoding: utf-8

"""
    Ranges are essentially generators that successively same
    transformations with different parameters to ParameterSets.
"""

import collections as c
import itertools as it

from .. import utils as u

from . import transforms as t

__all__ = ["Range"]

class Range(object):
    """
        Define one or more parameter ranges that are swept over.

        Transforms and ranges in the same Range-object are swept over
        simultaneously. If you need the cartesian product of several Ranges
        then add them seperately to your Sweep.
    """

    def __init__(self, transforms, range_tuples):
        """
            Transforms is a list of Transform-objects and range_tuples is a
            list of tuples of length len(transforms).

            Tranforms can also be single Transform with accompanying range.
        """
        if isinstance(transforms, t.Transform):
            transforms = [transforms]
            range_tuples = [(tr,) for tr in range_tuples]

        if not (isinstance(transforms, c.Sequence)
                and isinstance(range_tuples, c.Sequence)):
            raise ValueError("Both transforms and values must be sequences")

        if any(len(tr) != len(transforms) for tr in range_tuples):
            info = \
                "Transforms and ranges in the same Range-object are swept "\
                "over simultaneously. If you need the cartesian product "\
                "of several Ranges then add them seperately to your Sweep."
            raise ValueError(info)

        self.transforms = transforms
        self.range_tuples = range_tuples

    def __call__(self, paramset):
        # apply several transformations at once

        for tr in self.range_tuples:
            p = paramset.copy()

            for t, v in it.izip(self.transforms, tr):
                t.set_value(v)
                t.apply(p)

            yield p


