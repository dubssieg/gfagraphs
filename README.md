[![](https://img.shields.io/badge/Python-3.10-blue.svg)]()
[![](https://img.shields.io/badge/Python-3.11-blue.svg)]()
[![](https://img.shields.io/badge/Python-3.12-blue.svg)]()
[![Documentation Status](https://readthedocs.org/projects/gfagraphs/badge/?version=latest)](https://gfagraphs.readthedocs.io/en/latest/?badge=latest)

# GFAGraphs - A Python GFA library

This Python library aims to be an abstraction layer for GFA file format.

> [!WARNING]\
> `gfagraphs` is not actively maintained as I moved to Rust for my main research work. However, as the library is used in some projects, the library remains available as is.

## Package `gfagraphs`

![](https://media.discordapp.net/attachments/874430800802754623/1179353568105467964/library.png)

The package is organized in 4 modules:
+ `gfagraphs.abstractions` contains abstractions over GFA formats
+ `gfagraphs.gfaparser` contains an abstract class for parsing and saving GFA file format
+ `gfagraphs.graph` contains the main `Graph` class that represents a GFA graph in memory, and edit functions
+ `gfagraphs.networkx` conains an abstract class for visualization and modelization of GFA in a NetworkX object

> [!NOTE]\
> Want to contribute? Feel free to open a PR on an issue about a missing, buggy or incomplete feature!

