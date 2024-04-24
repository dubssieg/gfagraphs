from os import path as opath
from sys import path as spath
from importlib.metadata import version
from datetime import datetime
spath.insert(0, opath.abspath('../pgGraphs'))

project = 'gfagraphs'
copyright = f'{datetime.now().year}, Siegfried Dubois'
author = 'Siegfried Dubois'
release = version('gfagraphs')

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.mathjax',
    'sphinx.ext.napoleon',
]

napoleon_google_docstring = False
napoleon_numpy_docstring = True

templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']

html_theme = 'furo'
html_static_path = ['_static']
