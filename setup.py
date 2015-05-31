#!/usr/bin/env python

from setuptools import setup

setup(name='Pyment',
      version='0.3.2-dev',
      description='',
      author='A. Daouzli',
      author_email='',
      url='https://github.com/dadadel/pyment',
      packages=['pyment'],
      test_suite='tests.test_all',
      entry_points={
        'console_scripts': [
            'pyment = pyment.pymentapp:main'
            ]
        },
      )
