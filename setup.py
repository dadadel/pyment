#!/usr/bin/env python

from setuptools import setup
from os import path
import pyment


curr_dir = path.abspath(path.dirname(__file__))

with open(path.join(curr_dir, "README.rst")) as f:
    long_desc = f.read()


setup(name='Pyment',
      version=pyment.__version__,
      description='Generate/convert automatically the docstrings from code signature',
      long_description=long_desc,
      long_description_content_type="text/x-rst",
      author='A. Daouzli',
      author_email='dadel@hadoly.fr',
      license='GPLv3',
      keywords="pyment docstring numpydoc googledoc restructuredtext epydoc epytext javadoc development generate auto",
      platforms=['any'],
      classifiers=[
          'Intended Audience :: Developers',
          'Topic :: Documentation',
          'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
          'Programming Language :: Python :: 2.7',
          'Programming Language :: Python :: 3',
          'Programming Language :: Python :: 3.0',
          'Programming Language :: Python :: 3.1',
          'Programming Language :: Python :: 3.2',
          'Programming Language :: Python :: 3.3',
          'Programming Language :: Python :: 3.4',
          'Programming Language :: Python :: 3.5',
          'Programming Language :: Python :: 3.6'
          ],
      url='https://github.com/dadadel/pyment',
      packages=['pyment'],
      test_suite='tests.test_all',
      entry_points={
        'console_scripts': [
            'pyment = pyment.pymentapp:main'
            ]
        },
      )
