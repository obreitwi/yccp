#!/usr/bin/env python2
# encoding: utf-8

__all__ = ["log"]

import logging
import os
import os.path as osp
import sys

log = logging.getLogger(__name__.split(".")[0])

format_verbose = "%(asctime)s %(levelname)s %(funcName)s (%(filename)s:"\
        "%(lineno)d): %(message)s"
format_default = "%(asctime)s %(levelname)s: %(message)s"
format_date = "%y-%m-%d %H:%M:%S"

ch = logging.StreamHandler()

if "DEBUG" in os.environ:
    ch.setFormatter(logging.Formatter(format_verbose, datefmt=format_date))
    ch.setLevel(logging.DEBUG)
    log.setLevel(logging.DEBUG)
else:
    ch.setFormatter(logging.Formatter(format_default, datefmt=format_date))
    ch.setLevel(logging.INFO)
    log.setLevel(logging.INFO)

log.addHandler(ch)

