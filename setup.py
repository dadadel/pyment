#!/usr/bin/env python

import pathlib
from os import path

from setuptools import setup

import pymend

curr_dir = path.abspath(path.dirname(__file__))

long_desc = pathlib.Path(path.join(curr_dir, "README.rst")).read_text(encoding="utf-8")
setup(
    name="Pymend",
    version=pymend.__version__,
    description="Generate, fix and convert docstrings.",
    long_description=long_desc,
    long_description_content_type="text/x-rst",
    author="J-E. Nitschke",
    author_email="janericnitschke@gmail.com",
    license="GPLv3",
    keywords="pymend docstring",
    platforms=["any"],
    classifiers=[
        "Intended Audience :: Developers",
        "Topic :: Documentation",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    url="https://github.com/JanEricNitschke/pymend",
    packages=["pymend"],
    test_suite="tests.test_all",
    entry_points={"console_scripts": ["pymend = pymend.pymendapp:main"]},
)
