"Tools to represent GFA format"
from enum import Enum
from re import sub, match
from typing import Callable
from math import log10
from json import loads, dumps
from networkx import MultiDiGraph
from tharospytools import get_palette


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


def dtype(data: object) -> str:
    """Interprets tags of GFA as a Python-compatible format

    Args:
        tag_type (str): the letter that identifies the GFA data type

    Raises:
        NotImplementedError: happens if its an array or byte array (needs doc)
        ValueError: happens if format is not in GFA standards

    Returns:
        type | Callable: the cast method or type to apply
    """
    if isinstance(data, int):
        return 'i'
    elif isinstance(data, float):
        return 'f'
    elif isinstance(data, str):
        return 'Z'
    else:
        try:
            _: str = dumps(data)
            return 'J'
        except (TypeError, OverflowError) as exc:
            raise ValueError(
                f"Type {type(data)} is not in the GFA standard") from exc


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
    UNK = 'unknown'


class LineType():
    "Modelizes the line type in GFA format by the meaning of first char of sequence"
    __slots__ = ['type', 'func']

    def __init__(self, key: str) -> None:
        default_value: tuple = (default, Other)
        mapping: dict = {
            'H': (header, Header),
            'S': (segment, Segment),
            'L': (line, Line),
            'C': (containment, Containment),
            'P': (path, Path),
            'W': (walk, Walk),
            'J': (jump, Jump)
        }
        self.func, self.type = mapping.get(key, default_value)


class Header():
    "Empty type to define linestyle"
    datas: dict
    gfastyle: GfaStyle
    linetype: LineType

    def __repr__(self) -> str:
        return '\t'.join([f"{key}:{dtype(value)}:{value}" for key, value in self.datas.items()])


class Segment():
    "Empty type to define linestyle"
    datas: dict
    gfastyle: GfaStyle
    linetype: LineType

    def __repr__(self) -> str:
        return f"{self.datas['name']}\t{self.datas['seq'] if 'seq' in self.datas else 'N'*self.datas['length']}\t" + '\t'.join([f"{key}:{dtype(value)}:{value}" for key, value in self.datas.items() if key not in ['length', 'seq', 'name']])


class Line():
    "Empty type to define linestyle"
    datas: dict
    gfastyle: GfaStyle
    linetype: LineType

    def __repr__(self) -> str:
        ori1, ori2 = self.datas['orientation'].split('/')
        return f"{self.datas['start']}\t{ori1}\t{self.datas['end']}\t{ori2}\t" + '\t'.join([f"{key}:{dtype(value)}:{value}" for key, value in self.datas.items() if key not in ['orientation', 'start', 'end']])


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


class Other():
    "Empty type to define linestyle"
    datas: dict
    gfastyle: GfaStyle
    linetype: LineType


def default(datas: list, gfa_style: GfaStyle, **kwargs) -> dict:
    """Extracts the data from a unknown line

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


def header(datas: list, gfa_style: GfaStyle, **kwargs) -> dict:
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


def segment(datas: list, gfa_style: GfaStyle, **kwargs) -> dict:
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
    if kwargs['ws']:
        line_datas["seq"] = datas[2]
    return {**line_datas, **supplementary_datas(datas, 3)}


def line(datas: list, gfa_style: GfaStyle, **kwargs) -> dict:
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


def containment(datas: list, gfa_style: GfaStyle, **kwargs) -> dict:
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


def path(datas: list[str], gfa_style: GfaStyle, **kwargs) -> dict:
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


def walk(datas: list[str], gfa_style: GfaStyle, **kwargs) -> dict:
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
    line_datas["id"] = datas[3]
    line_datas["origin"] = int(datas[2])
    line_datas["name"] = datas[1]
    line_datas["start_offset"] = datas[4]
    line_datas["stop_offset"] = datas[5]
    line_datas["path"] = [
        (
            node[1:],
            Orientation(node[0])
        )
        for node in datas[6].replace('>', ',+').replace('<', ',-')[1:].split(',')
    ]
    return {**line_datas, **supplementary_datas(datas, 7)}


def jump(datas: list, gfa_style: GfaStyle, **kwargs) -> dict:
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
    __slots__ = ['gfastyle', 'linetype', 'datas', '__class__']

    def __init__(self, gfa_data_line: str, gfa_type: str, kwargs: dict = {}) -> None:
        datas: list = gfa_data_line.strip('\n').split('\t')
        self.gfastyle: GfaStyle = GfaStyle(gfa_type)
        self.linetype: LineType = LineType(gfa_data_line[0])
        self.datas: dict = self.linetype.func(datas, self.gfastyle, **kwargs)
        self.__class__ = self.linetype.type


class Graph():
    """
    Modelizes a GFA graph
    """
    __slots__ = ['version', 'graph', 'headers', 'segments',
                 'lines', 'containment', 'paths', 'walks', 'jumps', 'others', 'colors']

    def __init__(self, gfa_file: str, gfa_type: str, with_sequence: bool = False) -> None:
        self.version: GfaStyle = GfaStyle(gfa_type)
        self.graph = MultiDiGraph()
        with open(gfa_file, 'r', encoding='utf-8') as gfa_reader:
            gfa_lines: list[Record] = [
                Record(gfa_line, gfa_type, {'ws': with_sequence}) for gfa_line in gfa_reader]
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
        self.others: list[Other] = [
            rec for rec in gfa_lines if isinstance(rec, Other)]
        del gfa_lines

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

    def assert_format(self) -> GfaStyle:
        """Given the loaded file, asserts the GFA standard it is

        Returns:
            GfaStyle: a gfa subformat descriptor
        """
        ver: GfaStyle = self.version
        if len(self.others) > 0:
            ver = GfaStyle.GFA2
        elif len(self.jumps) > 0:
            ver = GfaStyle.GFA1_2
        elif len(self.walks) > 0:
            ver = GfaStyle.GFA1_1
        elif len(self.headers) > 0 or len(self.paths) > 0:
            ver = GfaStyle.GFA1
        else:
            ver = GfaStyle.RGFA
        self.version = ver
        return ver

    def compute_networkx(self, node_prefix: str | None = None) -> MultiDiGraph:
        """Computes the networkx representation of the GFA.

        Returns:
            MultiDiGraph: a networkx graph featuring the maximum of information
        """
        node_prefix = f"{node_prefix}_" if node_prefix is not None else ""
        for node in self.segments:
            node_title: list = []
            for key, val in node.datas.items():
                if isinstance(val, dict):
                    node_title.extend([f"{k} : {v}" for k, v in val.items()])
                else:
                    node_title.append(f"{key} : {val}")
            self.graph.add_node(
                f"{node_prefix}{node.datas['name']}",
                title='\n'.join(node_title),
                color='darkslateblue',
                size=10+log10(node.datas["length"]),
                offsets=node.datas['PO'] if 'PO' in node.datas else None
            )
        palette: list = get_palette(
            len(path_list := self.get_path_list()), as_hex=True)
        self.colors = {p.datas["name"]: palette[i]
                       for i, p in enumerate(path_list)}
        if len(path_list) > 0:
            visited_paths: int = 0
            for visited_path in path_list:
                for i in range(len(visited_path.datas["path"])-1):
                    left_node, left_orient = visited_path.datas["path"][i]
                    right_node, right_orient = visited_path.datas["path"][i+1]
                    self.graph.add_edge(
                        f"{node_prefix}{left_node}",
                        f"{node_prefix}{right_node}",
                        title=str(visited_path.datas["name"]),
                        color=palette[visited_paths],
                        label=f"{left_orient.value}/{right_orient.value}",
                        weight=3
                    )
                visited_paths += 1
        else:
            for edge in self.lines:
                self.graph.add_edge(
                    f"{node_prefix}{edge.datas['start']}",
                    f"{node_prefix}{edge.datas['end']}",
                    color='darkred',
                    label=edge.datas["orientation"],
                    weight=3
                )
        return self.graph

    def save_graph(self, output_path: str, output_format: GfaStyle | None = None) -> None:
        """Given a gfa Graph object, saves to a valid gfa file the Graph.

        Args:
            output_path (str): a path on disk where to save
            output_format (GfaStyle): a format to choose for output.
                if None, default graph format will be used.
        """
        output_format = output_format or self.version
        line_number: int = 0
        with open(output_path, 'w', encoding='utf-8') as gfa_writer:
            if len(self.headers) and output_format != GfaStyle.RGFA:
                for head in self.headers:
                    gfa_writer.write(f"H\t{head}\n")
            if len(self.segments):
                for seg in self.segments:
                    gfa_writer.write(f"S\t{seg}\n")
            if len(self.lines):
                for lin in self.lines:
                    gfa_writer.write(f"L\n{lin}\n")
            if len(pathlist := self.get_path_list()):
                for pathl in pathlist:
                    gfa_writer.write(
                        f"{write_path(pathl,output_format,line_number)}")
                    line_number += 1


def write_path(way: Walk | Path, gfa_format: GfaStyle, line_number: int) -> str:
    """Selects if path should be saved in P or W format, and creates the repr string

    Args:
        way (Walk | Path): the Walk or Path object we want to represent
        format (GfaStyle): the output GFA format

    Returns:
        str: a gfa compatible string describing path
    """
    if gfa_format == GfaStyle.GFA1:  # P-line
        strpath: str = ','.join(
            [f"{node_name}{'+' if orient == Orientation.FORWARD else '-'}" for node_name, orient in way.datas['path']])

        return f"P\t{way.datas['name']}\t{strpath}\t*"

    elif gfa_format == GfaStyle.GFA1_1 or gfa_format == GfaStyle.GFA1_2 or gfa_format == GfaStyle.GFA2:
        # W-line
        offset_start: int | str = way.datas['start_offset'] if 'start_offset' in way.datas else '?'
        offset_stop: int | str = way.datas['stop_offset'] if 'stop_offset' in way.datas else '?'
        strpath: str = ''.join(
            [f"{'>' if orient == Orientation.FORWARD else '<'}{node_name}" for node_name, orient in way.datas['path']])
        return f"W\t{way.datas['name']}\t{line_number}\t{way.datas['name']}\t{offset_start}\t{offset_stop}\t{strpath}\t*"
    return ""
