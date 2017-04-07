#!/usr/bin/env python
from distutils.core import setup

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
    packages=['pylibs']
)