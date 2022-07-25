#!/usr/bin/env python
# -*- encoding:utf-8 -*-

import re
from setuptools import setup


with open('mtable.py') as f:
    content = f.read()
    mo = re.search(r"VERSION = '([\d\.]+)'\n", content)
    VERSION = mo.group(1)

with open('README.rst', encoding='utf-8') as f:
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
