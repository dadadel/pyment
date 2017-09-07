#!/usr/bin/env python

from setuptools import setup
from os import path

curr_dir = path.abspath(path.dirname(__file__))

with open(path.join(curr_dir, "README.rst")) as f:
    long_desc = f.read()


setup(name='Pyment',
      version='0.3.2-dev3',
      description='Generate automatically the doc from your code signature',
      long_description=long_desc,
      author='A. Daouzli',
      author_email='',
      license='GPLv3',
      keywords="pyment numpydoc doc development generate auto",
      classifiers = [
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
