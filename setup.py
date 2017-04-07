#!/usr/bin/env python
from setuptools import setup, find_packages

setup(
    name='pylibs',
    version='0.0.1',
    description='Pylibs for development',
    author='Dimoha',
    author_email='dimoha@controlstyle.ru',
    url='http://gitlab.controlstyle.ru/Dimoha/pylibs/',
    install_requires=[
        'requests[security]==2.12.1',
    ],
    packages=map(lambda x: "pylibs.{}".format(x), find_packages()),
    package_dir={'': 'pylibs'}
)
