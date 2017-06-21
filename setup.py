
from setuptools import setup

import os
import os.path as osp

execfile(osp.join(osp.dirname(osp.abspath(__file__)), "yccp", "version.py"))

setup(
        name="yccp",
        version=".".join(map(str, __version__)),
        install_requires=["PyYAML>=3.12"],
        packages=["yccp"],
        url="https://github.com/obreitwi/yccp",
        license="GNUv3",
        zip_safe=True,
    )
