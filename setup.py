#!/usr/bin/env python
# -*- encoding:utf-8 -*-

from setuptools import setup


VERSION = '0.1.0'


setup(
    name='mtable',
    version=VERSION,
    description='format data to reStructedText and Markup Table',
    url='https://github.com/liuyug/mtable',
    license='BSD',
    author='Yugang LIU',
    author_email='liuyug@gmail.com',
    python_requires='>=3',
    py_modules=['mtable'],
    install_requires=['chardet'],
)
