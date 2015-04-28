#!/usr/bin/env python
# -*- coding: utf-8 -*-

# This file is part of resourcealchemy.
# https://github.com/TomNeyland/resource-alchemy

# Licensed under the TBD license:
# http://www.opensource.org/licenses/TBD-license
# Copyright (c) 2015, Tom Neyland <tcneyland+github@gmail.com>

from setuptools import setup, find_packages
from resourcealchemy import __version__

tests_require = [
    'mock',
    'nose',
    'coverage',
    'yanc',
    'preggy',
    'tox',
    'ipdb',
    'coveralls',
    'sphinx',
]

setup(
    name='resourcealchemy',
    version=__version__,
    description='Easily create SqlAlchemy backed API endpoints and resources',
    long_description='''
Easily create SqlAlchemy backed API endpoints and resources
''',
    keywords='sqlalchemy flask rest resource json api sql',
    author='Tom Neyland',
    author_email='tcneyland+github@gmail.com',
    url='https://github.com/TomNeyland/resource-alchemy',
    license='TBD',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: TBD License',
        'Natural Language :: English',
        'Operating System :: Unix',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: Implementation :: PyPy',
        'Operating System :: OS Independent',
    ],
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        # add your dependencies here
        # remember to use 'package-name>=x.y.z,<x.y+1.0' notation (this way you get bugfixes)
    ],
    extras_require={
        'tests': tests_require,
    },
    entry_points={
        'console_scripts': [
            # add cli scripts here in this form:
            # 'resourcealchemy=resourcealchemy.cli:main',
        ],
    },
)
