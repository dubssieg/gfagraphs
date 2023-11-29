[![](https://img.shields.io/badge/Python-3.10-blue.svg)]()
[![](https://img.shields.io/badge/Python-3.11-blue.svg)]()
[![](https://img.shields.io/badge/Python-3.12-blue.svg)]()
[![](https://img.shields.io/badge/documentation-unfinished-orange.svg)]()

# GFAGraphs - A Python GFA library

This Python library aims to be an abstraction layer for GFA file format.
Two implementations are proposed:
+ a legacy one, which will remain until deprecated, in `gfagraphs/`
+ a new, cleaner and faster implementation, in `pgGraphs/`

> [!WARNING]\
> Moving forward, features will only be added to `pgGraphs`, while `gfagraphs` will remain as it, until full migration is done in [pancat](https://github.com/Tharos-ux/pancat) tool.

## Package pgGraphs

![](https://media.discordapp.net/attachments/874430800802754623/1179353568105467964/library.png)

The package is organized in 4 modules:
+ `pgGraphs.abstractions` contains abstractions over GFA formats
+ `pgGraphs.gfaparser` contains an abstract class for parsing and saving GFA file format
+ `pgGraphs.graph` contains the main `Graph` class that represents a GFA graph in memory, and edit functions
+ `pgGraphs.networkx` conains an abstract class for visualization and modelization of GFA in a NetworkX object

> [!NOTE]\
> Want to contribute? Feel free to open a PR on an issue about a missing, buggy or incomplete feature!

