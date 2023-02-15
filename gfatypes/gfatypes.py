"Tools to represent GFA format"
from enum import Enum
from re import sub, match
from typing import Callable
from json import loads


def gtype(tag_type: str) -> type | Callable:
    """Interprets tags of GFA as a Python-compatible format

    Args:
        tag_type (str): the letter that identifies the GFA data type

    Raises:
        NotImplementedError: happens if its an array or byte array (needs doc)
        ValueError: happens if format is not in GFA standards

    Returns:
        type | Callable: the cast method or type to apply
    """
    if tag_type == 'i':
        return int
    elif tag_type == 'f':
        return float
    elif tag_type == 'A' or tag_type == 'Z':
        return str
    elif tag_type == 'J':
        return loads
    elif tag_type == 'H' or tag_type == 'B':
        raise NotImplementedError()
    raise ValueError(f"Type identifier {tag_type} is not in the GFA standard")


def supplementary_datas(datas: list, length_condition: int) -> dict:
    """Computes the optional tags of a gfa line and returns them as a dict

    Args:
        datas (list): parsed data line
        length_condition (int): last position of positional field

    Returns:
        dict: mapping tag:value
    """
    mapping: dict = dict()
    nargs: int = length_condition
    if len(datas) > length_condition:  # we happen to have additional tags to our line
        for additional_tag in datas[length_condition:]:
            if match('[A-Z]{2}:[a-zA-Z]{1}:', additional_tag):  # matches start of the line
                mapping[additional_tag[:2]] = gtype(
                    additional_tag[3])(additional_tag[5:])
            else:
                mapping[f"ARG{nargs}"] = additional_tag
                nargs += 1
    return mapping


class Orientation(Enum):
    "Describes the way a node is read"
    FORWARD = '+'
    REVERSE = '-'


class GfaStyle(Enum):
    "Describes the different possible formats"
    RGFA = 'rGFA'
    GFA1 = 'GFA1'
    GFA1_1 = 'GFA1.1'
    GFA1_2 = 'GFA1.2'
    GFA2 = 'GFA2'


class LineType():
    "Modelizes the line type in GFA format by the meaning of first char of sequence"

    def __init__(self, key: str) -> None:
        mapping: dict = {
            'H': (header, Header),
            'S': (segment, Segment),
            'L': (line, Line),
            'C': (containment, Containment),
            'P': (path, Path),
            'W': (walk, Walk),
            'J': (jump, Jump)
        }
        self.type = mapping[key][1]
        self.func = mapping[key][0]


class Header():
    "Empty type to define linestyle"
    datas: dict
    gfastyle: GfaStyle
    linetype: LineType


class Segment():
    "Empty type to define linestyle"
    datas: dict
    gfastyle: GfaStyle
    linetype: LineType


class Line():
    "Empty type to define linestyle"
    datas: dict
    gfastyle: GfaStyle
    linetype: LineType


class Containment():
    "Empty type to define linestyle"
    datas: dict
    gfastyle: GfaStyle
    linetype: LineType


class Path():
    "Empty type to define linestyle"
    datas: dict
    gfastyle: GfaStyle
    linetype: LineType


class Walk():
    "Empty type to define linestyle"
    datas: dict
    gfastyle: GfaStyle
    linetype: LineType


class Jump():
    "Empty type to define linestyle"
    datas: dict
    gfastyle: GfaStyle
    linetype: LineType


def header(datas: list, gfa_style: GfaStyle) -> dict:
    """Extracts the data from a header line

    Args:
        datas (list): parsed GFA line
        gfa_style (GfaStyle): informations about gfa subformat

    Returns:
        dict: mapping tags:values
    """
    if gfa_style == GfaStyle.RGFA:
        raise ValueError(
            f"Incompatible version format, H-lines vere added in GFA1 and were absent from {gfa_style}.")
    return supplementary_datas(datas, 0)


def segment(datas: list, gfa_style: GfaStyle) -> dict:
    """Extracts the data from a segment line

    Args:
        datas (list): parsed GFA line
        gfa_style (GfaStyle): informations about gfa subformat

    Returns:
        dict: mapping tags:values
    """
    line_datas: dict = dict()
    line_datas["name"] = sub('\D', '', datas[1])
    line_datas["length"] = len(datas[2])
    return {**line_datas, **supplementary_datas(datas, 3)}


def line(datas: list, gfa_style: GfaStyle) -> dict:
    """Extracts the data from a line line

    Args:
        datas (list): parsed GFA line
        gfa_style (GfaStyle): informations about gfa subformat

    Returns:
        dict: mapping tags:values
    """
    line_datas: dict = dict()
    line_datas["start"] = sub('\D', '', datas[1])
    line_datas["end"] = sub('\D', '', datas[3])
    line_datas["orientation"] = f"{datas[2]}/{datas[4]}"
    return {**line_datas, **supplementary_datas(datas, 5)}


def containment(datas: list, gfa_style: GfaStyle) -> dict:
    """Extracts the data from a containment line

    Args:
        datas (list): parsed GFA line
        gfa_style (GfaStyle): informations about gfa subformat

    Returns:
        dict: mapping tags:values
    """
    if gfa_style == GfaStyle.RGFA:
        raise ValueError(
            f"Incompatible version format, C-lines vere added in GFA1 and were absent from {gfa_style}.")
    return supplementary_datas(datas, 0)


def path(datas: list, gfa_style: GfaStyle) -> dict:
    """Extracts the data from a path line

    Args:
        datas (list): parsed GFA line
        gfa_style (GfaStyle): informations about gfa subformat

    Returns:
        dict: mapping tags:values
    """
    line_datas: dict = dict()
    if gfa_style == GfaStyle.RGFA:
        raise ValueError(
            f"Incompatible version format, P-lines vere added in GFA1 and were absent from {gfa_style}.")
    line_datas["name"] = datas[1]
    line_datas["path"] = [
        (
            node[:-1],
            Orientation(node[-1])
        )
        for node in datas[2].split(',')
    ]
    return {**line_datas, **supplementary_datas(datas, 7)}


def walk(datas: list, gfa_style: GfaStyle) -> dict:
    """Extracts the data from a walk line

    Args:
        datas (list): parsed GFA line
        gfa_style (GfaStyle): informations about gfa subformat

    Returns:
        dict: mapping tags:values
    """
    line_datas: dict = dict()
    if gfa_style in [GfaStyle.RGFA, GfaStyle.GFA1]:
        raise ValueError(
            f"Incompatible version format, W-lines vere added in GFA1.1 and were absent from {gfa_style}.")
    line_datas["id"] = datas[1]
    line_datas["origin"] = int(datas[2])
    line_datas["name"] = datas[3]
    line_datas["target"] = datas[4]
    line_datas["length"] = datas[5]
    line_datas["path"] = [
        (
            node[1:],
            Orientation(node[0])
        )
        for node in datas[6].replace('>', ',+').replace('<', ',-')[1:].split(',')
    ]
    return {**line_datas, **supplementary_datas(datas, 7)}


def jump(datas: list, gfa_style: GfaStyle) -> dict:
    """Extracts the data from a jump line

    Args:
        datas (list): parsed GFA line
        gfa_style (GfaStyle): informations about gfa subformat

    Returns:
        dict: mapping tags:values
    """
    if gfa_style in [GfaStyle.RGFA, GfaStyle.GFA1, GfaStyle.GFA1_1]:
        raise ValueError(
            f"Incompatible version format, J-lines vere added in GFA1.2 and were absent from {gfa_style}.")
    return supplementary_datas(datas, 0)


class Record():
    """
    Modelizes a GFA line
    """

    def __init__(self, gfa_data_line: str, gfa_type: str) -> None:
        datas: list = gfa_data_line.split('\t')
        self.gfastyle: GfaStyle = GfaStyle(gfa_type)
        self.linetype: LineType = LineType(gfa_data_line[0])
        self.datas: dict = self.linetype.func(datas, self.gfastyle)
        self.__class__ = self.linetype.type


class Graph():
    """
    Modelizes a GFA graph
    """

    def __init__(self, gfa_file: str, gfa_type: str) -> None:
        self.version: GfaStyle = GfaStyle(gfa_type)
        with open(gfa_file, 'r', encoding='utf-8') as gfa_reader:
            gfa_lines: list[Record] = [
                Record(gfa_line, gfa_type) for gfa_line in gfa_reader]
        self.headers: list[Header] = [
            rec for rec in gfa_lines if isinstance(rec, Header)]
        self.segments: list[Segment] = [
            rec for rec in gfa_lines if isinstance(rec, Segment)]
        self.lines: list[Line] = [
            rec for rec in gfa_lines if isinstance(rec, Line)]
        self.containment: list[Containment] = [
            rec for rec in gfa_lines if isinstance(rec, Containment)]
        self.paths: list[Path] = [
            rec for rec in gfa_lines if isinstance(rec, Path)]
        self.walks: list[Walk] = [
            rec for rec in gfa_lines if isinstance(rec, Walk)]
        self.jumps: list[Jump] = [
            rec for rec in gfa_lines if isinstance(rec, Jump)]
        gfa_lines = list()

    def __str__(self) -> str:
        return f"GFA Graph object (version {self.version.value}) containing {len(self.segments)} segments, {len(self.lines)} edges and {len(self.paths)+len(self.walks)} paths."

    def get_segment(self, node: str) -> Segment:
        """Search the node with the corresponding node name inside the graph, and returns it.

        Args:
            node (str): a string, identifier of the node

        Raises:
            ValueError: if node is not in graph

        Returns:
            Segment: the line describing the node
        """
        node = str(node)
        for seg in self.segments:
            if seg.datas["name"] == node:
                return seg
        raise ValueError(f"Node {node} is not in graph.")

    def get_path_list(self) -> list[Path | Walk]:
        """Returns all paths in graphs, described as P or W lines.

        Returns:
            list: all walks and paths
        """
        return self.paths + self.walks

    def get_path(self, name: str) -> Path | Walk:
        """Given a path name, search that path inside the paths of the graph

        Args:
            name (str): a string identifying the path within the graph

        Raises:
            ValueError: the name is not inside the graph

        Returns:
            Path | Walk: the required path
        """
        for gpath in self.get_path_list():
            if gpath.datas["name"] == name:
                return gpath
        raise ValueError(
            f"Specified name {name} does not define a path in your GFA file.")
