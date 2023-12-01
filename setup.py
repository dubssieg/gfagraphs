#!/usr/bin/env python3
from setuptools import setup, find_packages
from subprocess import run, PIPE
from sys import version_info, stderr
from setuptools import setup
from pkg_resources import require
from sys import argv

NAME: str = "gfagraphs"
AUTHOR: str = "Siegfried Dubois",
AUTHOR_EMAIL: str = "siegfried.dubois@inria.fr",
LICENCE: str = "LICENCE"
DESCRIPTION: str = "Library to parse, edit and handle in memory GFA graphs"
REQUIRED_PYTHON: tuple = (3, 10)
OVERRIDE_VN: bool = True
VN: str = "0.2.2"
URL: str = "https://github.com/Tharos-ux/gfagraphs"
REQUIREMENTS: list[str] = ['networkx', 'tharos-pytools']


if argv[1] in ('install', 'sdist', 'bdist_wheel'):
    # Checking if Python version is correct
    if version_info[:2] < REQUIRED_PYTHON:
        stderr.write(
            f"{NAME} requires Python {'.'.join(REQUIRED_PYTHON)} or higher and your current version is {version_info[:2]}.")
        exit(1)

    # Computing version number
    if OVERRIDE_VN:
        _iv: str = VN
    else:
        try:
            _iv: list = [int(x) for x in require(NAME)[0].version.split('.')]
            _iv[-1] += 1
        except:
            _iv: list = [0, 0, 0]
        finally:
            _iv: str = '.'.join([str(x) for x in _iv])

    _sb, _eb = "{", "}"
    with open('pyproject.toml', 'w', encoding='utf-8') as tomlwriter:
        tomlwriter.write(
            f"""[build-system]
    requires = ["setuptools>=61.0"]
    build-backend = "setuptools.build_meta"

    [project]
    name = "{NAME}"
    version = "{_iv}"
    authors = [
    {_sb} name="{AUTHOR[0]}", email="{AUTHOR_EMAIL[0]}" {_eb},
    ]
    description = "{DESCRIPTION}"
    readme = "README.md"
    requires-python = ">={'.'.join([str(x) for x in REQUIRED_PYTHON])}"
    classifiers = [
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ]

    [project.urls]
    "Homepage" = "{URL}"
    "Bug Tracker" = "{URL}/issues"
    """
        )
else:
    _iv: str = VN if OVERRIDE_VN else require(NAME)[0].version

# Install procedure
setup(
    name=NAME,
    version=_iv,
    description=DESCRIPTION,
    url=URL,
    author=AUTHOR,
    author_email=AUTHOR_EMAIL,
    zip_safe=False,
    packages=find_packages(),
    install_requires=REQUIREMENTS,
    long_description=open("README.md", encoding='utf-8').read(),
    long_description_content_type='text/markdown',
)
