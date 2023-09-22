#!/usr/bin/env python3
from sys import version_info, stderr
from setuptools import setup, find_packages

NAME = "gfagraphs"
CURRENT_PYTHON = version_info[:2]
REQUIRED_PYTHON = (3, 10)

if CURRENT_PYTHON < REQUIRED_PYTHON:
    stderr.write(
        f"{NAME} requires Python 3.10 or higher and your current version is {CURRENT_PYTHON}.")
    exit(1)


setup(
    name=NAME,
    version='0.1.75',
    description='Abstraction layer for GFA file format',
    url='https://github.com/Tharos-ux/gfatypes',
    author='Tharos',
    author_email='dubois.siegfried@gmail.com',
    license='MIT',
    packages=find_packages(),
    zip_safe=False,
    install_requires=['networkx', 'tharos-pytools']
)
