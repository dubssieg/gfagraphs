"Abstractions over GFA formats"
from enum import Enum


class Orientation(Enum):
    """Describes the way a node is read. Minus is reversecomp and plus is forward.
    Please refer to http://gfa-spec.github.io/GFA-spec/GFA1.html for examples and full description of the format.

    Parameters
    ----------
    Enum : str
        Could be a GFA-compatible tag (+ or -) or ? to specify 'Any' or = to specify 'both'.
    """
    FORWARD = '+'
    REVERSE = '-'
    ANY = '?'
    BOTH = '='


class EdgeOrientation(Enum):
    """Describes the way an edge direction is encoded

    Parameters
    ----------
    Enum : str
        One of the following: +/+, +/-, -/+, -/-
    """
    FF = '+/+'
    RR = '-/-'
    FR = '+/-'
    RF = '-/+'


def reverse(orientation: EdgeOrientation) -> EdgeOrientation:
    """Returns the orientation of the reverse edge

    Parameters
    ----------
    orientation : EdgeOrientation
        _description_

    Returns
    -------
    EdgeOrientation
        The complementary operation
    """
    return {
        EdgeOrientation.FF: EdgeOrientation.RR,
        EdgeOrientation.RR: EdgeOrientation.FF,
        EdgeOrientation.RF: EdgeOrientation.FR,
        EdgeOrientation.FR: EdgeOrientation.RF,
    }


class GFAFormat(Enum):
    """Describes the different possible gfa-like formats.
    Please refer to http://gfa-spec.github.io/GFA-spec/GFA1.html for examples and full description of the format.

    Parameters
    ----------
    Enum : str
        One of rGFA | GFA1 | GFA1.1 | GFA1.2 | GFA2 | unknown
    """
    RGFA = 'rGFA'
    GFA1 = 'GFA1'
    GFA1_1 = 'GFA1.1'
    GFA1_2 = 'GFA1.2'
    GFA2 = 'GFA2'
    ANY = 'unknown'


class GFALine(Enum):
    """Describes the different GFA line formats.
    Please refer to http://gfa-spec.github.io/GFA-spec/GFA1.html for examples and full description of the format.

    Parameters
    ----------
    Enum : str
        One of S | L | W | P | H | # | ?. See GFA-spec.
    """
    SEGMENT = 'S'
    LINE = 'L'
    WALK = 'W'
    PATH = 'P'
    HEADER = 'H'
    COMMENT = '#'
    ANY = '?'
