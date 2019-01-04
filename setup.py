#!/usr/bin/env python
# -*- encoding:utf-8 -*-

from setuptools import setup


VERSION = '0.1.8'


with open('README.rst') as f:
    long_description = f.read()

requirements = []
with open('requirements.txt') as f:
    for line in f.readlines():
        line.strip()
        if line.startswith('#'):
            continue
        requirements.append(line)


setup(
    name='mtable',
    version=VERSION,
    description='format data to reStructedText and Markup Table',
    long_description=long_description,
    url='https://github.com/liuyug/mtable',
    license='BSD',
    author='Yugang LIU',
    author_email='liuyug@gmail.com',
    python_requires='>=3',
    py_modules=['mtable'],
    install_requires=requirements,
)
