
from setuptools import setup

import os
import os.path as osp

versionfile = osp.join(
    osp.dirname(osp.abspath(__file__)), "yccp", "version.py")
with open(versionfile) as f:
    code = compile(f.read(), versionfile, 'exec')
    exec(code, globals(), locals())

setup(
        name="yccp",
        version=".".join(map(str, __version__)),
        install_requires=["PyYAML>=3.12"],
        packages=["yccp", "yccp.cli", "yccp.sweeps"],
        entry_points={
            "console_scripts" : [
                "yccp-sbn=yccp.cli.sort_by_numbers:main"
            ]
        },
        url="https://github.com/obreitwi/yccp",
        license="GNUv3",
        zip_safe=True,
    )
