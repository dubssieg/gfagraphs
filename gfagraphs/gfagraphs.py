"Tools to represent GFA format"
from os.path import exists
from os import stat
from enum import Enum
from re import sub, match
from typing import Callable
from copy import deepcopy
from json import loads, dumps
from itertools import chain
from networkx import MultiDiGraph, DiGraph
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
    UNKNOWN = '?'


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

    def __str__(self) -> str:
        return '\t'.join([f"{key}:{dtype(value)}:{value}" for key, value in self.datas.items()])

    def __repr__(self) -> str:
        return self.__str__()


class Segment():
    "Empty type to define linestyle"
    datas: dict
    gfastyle: GfaStyle
    linetype: LineType

    def __init__(self, name: str, seq: str, **kwargs) -> None:
        self.datas: dict = {'name': name, 'seq': seq, **kwargs}

    def __str__(self) -> str:
        return f"{self.datas['name']}\t{self.datas['seq'] if 'seq' in self.datas else 'N'*self.datas['length']}\t" + '\t'.join([f"{key}:{dtype(value)}:{value}" for key, value in self.datas.items() if key not in ['length', 'seq', 'name']])

    def __repr__(self) -> str:
        return self.__str__()


class Line():
    "Empty type to define linestyle"
    datas: dict
    gfastyle: GfaStyle
    linetype: LineType

    def __init__(self, start: str, ori_start: str, end: str, ori_end: str, **kwargs) -> None:
        self.datas: dict = {'start': start, 'end': end,
                            'orientation': f"{ori_start}/{ori_end}", **kwargs}

    def __str__(self) -> str:
        ori1, ori2 = self.datas['orientation'].split('/')
        return f"{self.datas['start']}\t{ori1}\t{self.datas['end']}\t{ori2}\t" + '\t'.join([f"{key}:{dtype(value)}:{value}" for key, value in self.datas.items() if key not in ['orientation', 'start', 'end']])

    def __repr__(self) -> str:
        return self.__str__()


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
    return supplementary_datas(datas, 1)


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
    return supplementary_datas(datas, 1)


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
    return supplementary_datas(datas, 1)


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

    def __str__(self) -> str:
        return "RawRecord()"

    def __repr__(self) -> str:
        return self.__str__()


class Graph():
    """
    Modelizes a GFA graph
    """
    __slots__ = ['version', 'graph', 'headers', 'segments',
                 'lines', 'containment', 'paths', 'walks', 'jumps', 'others', 'colors']

    def __init__(self, gfa_file: str | None = None, gfa_type: str = 'unknown', with_sequence: bool = False) -> None:
        """Constructor for GFA Graph object.

        Args:
            gfa_file (str | None, optional): A file path to a valid GFA file. Defaults to None.
            gfa_type (str, optional): A descriptor for the GFA sub-format : ['rGFA','GFA1','GFA1.1','GFA1.2','GFA2']. Defaults to 'unknown'.
            with_sequence (bool, optional): If sequence should be included in nodes. Consumes more memory with huge graphs. Defaults to False.

        Raises:
            OSError: The file does not exists
            IOError: The file descriptor is invalid
            IOError: The file is empty
            ValueError: A line does not start with a capital letter
        """
        # Declaring attributes
        self.version: GfaStyle = GfaStyle(gfa_type)
        self.headers: list[Header] = []
        self.segments: list[Segment] = []
        self.lines: list[Line] = []
        self.containment: list[Containment] = []
        self.paths: list[Path] = []
        self.walks: list[Walk] = []
        self.jumps: list[Jump] = []
        self.others: list[Other] = []
        self.graph = MultiDiGraph()
        if gfa_file:
            # We try to load file from disk
            # Checking if path exists
            if not exists(gfa_file):
                raise OSError(
                    "Specified file does not exists. Please check provided path."
                )
            # Checking if file descriptor is valid
            if not gfa_file.endswith('.gfa'):
                raise IOError(
                    "File descriptor is invalid. Please check format, this lib is designed to work with Graphical Fragment Assembly (GFA) files."
                )
            # Checking if file is not empty
            if stat(gfa_file).st_size == 0:
                raise IOError(
                    "File is empty."
                )
            # All lines shall start by a captial letter (see GFAspec). If not, we raise ValueError
            with open(gfa_file, 'r', encoding='utf-8') as gfa_reader:
                for gfa_line in gfa_reader:

                    if not gfa_line[0].isupper() and len(gfa_line.strip()) != 0:
                        raise ValueError(
                            "All GFA lines shall start with a capital letter. Wrong format, please fix."
                        )
                    # We parse the GFA line with the record class
                    record: Record = Record(
                        gfa_line,
                        gfa_type,
                        {
                            'ws': with_sequence
                        }
                    )
                    # We put record in the right list
                    if isinstance(record, Header):
                        self.headers.append(record)
                    elif isinstance(record, Segment):
                        self.segments.append(record)
                    elif isinstance(record, Line):
                        self.lines.append(record)
                    elif isinstance(record, Containment):
                        self.containment.append(record)
                    elif isinstance(record, Path):
                        self.paths.append(record)
                    elif isinstance(record, Walk):
                        self.walks.append(record)
                    elif isinstance(record, Jump):
                        self.jumps.append(record)
                    else:
                        self.others.append(record)
            # Checking GFA style

    def __str__(self) -> str:
        return f"GFA Graph object (version {self.version.value}) containing {len(self.segments)} segments, {len(self.lines)} edges and {len(self.paths)+len(self.walks)} paths."

    def split_segments(self, segment_name: str, future_segment_name: str | list, position_to_split: tuple | list) -> None:
        """Given a segment to split and a series/single new name(s) + position(s),
        breaks the node in multiple nodes and includes splits them in the Graph data

        If you want to split the segment A into A,B, ... you must provide
        self.split_segments(A,[A,B, ...],[(start_A,end_A),(start_B,end_B), ...])

        Args:
            segment_name (str): the name of the node to break
            future_segment_name (str | list): the name(s) of the future nodes
            position_to_split (int | list): the position(s) where to split the sequence (start,stop)

        Raises:
            ValueError: if the provided args aren't compatible
        """
        node_to_split: Segment = self.get_segment(segment_name)
        if not isinstance(future_segment_name, list):
            future_segment_name = [future_segment_name]
        if not isinstance(position_to_split, list):
            position_to_split = [position_to_split]
        if len(future_segment_name) != len(position_to_split):
            raise ValueError("Parameters does not have the same length.")

        # Possible multi-split
        sequence = node_to_split.datas['seq'] if 'seq' in node_to_split.datas else 'N' * \
            node_to_split.datas['length']

        # Get incomming and exuting edges
        edges_of_node: list[Line] = self.get_edges(segment_name)
        orient: str = "?"
        for edge in edges_of_node:
            if edge.datas['start'] == segment_name:
                orient: str = edge.datas['orientation'].split('/')[0]
                # Edge is output, should be changed
                edge.datas['start'] = future_segment_name[-1]
            else:
                orient: str = edge.datas['orientation'].split('/')[-1]
                # Edge is incomming edge, should be kept

        # Edit first node
        node_to_split.datas['seq'] = node_to_split.datas['seq'][:position_to_split[0][1]
                                                                ] if 'seq' in node_to_split.datas else 'N'*position_to_split[0][1]

        for i, positions in enumerate(position_to_split):
            # Divide the node by creating an new one and updating attributes
            pos1, pos2 = positions
            new_seg: Segment = Segment(
                future_segment_name[i], sequence[pos1:pos2])
            new_seg.datas['length'] = len(new_seg.datas['seq'])
            self.segments.append(new_seg)

            if future_segment_name[i] == segment_name:
                # Remove the original segment
                self.segments.remove(node_to_split)

            # Create new edge between, re-assign sorting edges to new node
            try:
                new_edge: Line = Line(
                    future_segment_name[i], orient, future_segment_name[i+1], orient)
                # Get orientation of incomming edge and output edge, mix them for orientation of the new edge
                self.lines.append(new_edge)
            except IndexError:
                pass

        # Add to paths by inserting after node to be splitted
        for ipath in self.get_path_list():
            edited: bool = False
            for posx, sparkl in enumerate(ipath.datas['path']):
                node, _ = sparkl
                if node == segment_name and not edited:
                    edited = True
                    ipath.datas['path'].remove(sparkl)
                    ipath.datas['path'][posx:posx] = [(nname, Orientation(
                        orient)) for nname in future_segment_name]

    def rename_node(self, old_name: str, new_name: str, edit_paths: bool = True) -> Segment | None:
        "Performs node name edition operation on graph"
        new_name = str(new_name)
        old_name = str(old_name)
        try:
            to_edit: Segment = self.get_segment(old_name)
        except ValueError:
            print(f"Node {old_name} not found.")
            return None
        # Changing the name of the node
        to_edit.datas['name'] = new_name
        # Changing the name inside edges
        edges_to_edit: list = self.get_edges(old_name)
        for e in edges_to_edit:
            if e.datas['start'] == old_name:
                e.datas['start'] = new_name
            else:
                e.datas['end'] = new_name
        # Updataing path names
        if edit_paths:
            for p in self.walks:
                for idx, (nname, ori) in enumerate(p.datas['path']):
                    if nname == old_name:
                        p.datas['path'] = p.datas['path'][:idx] + \
                            [(new_name, ori)]+p.datas['path'][idx+1:]
            for p in self.paths:
                for idx, (nname, ori) in enumerate(p.datas['path']):
                    if nname == old_name:
                        p.datas['path'] = p.datas['path'][:idx] + \
                            [(new_name, ori)]+p.datas['path'][idx+1:]

    def merge_segments(self, *segs: str, merge_name: str | None = None, reversed: bool = False) -> str:
        """Given a series of nodes, merges it to the first of the series.
        """

        # Re-ordering nodes for edition POURQUOI
        segments_positions: list = [self.get_segment_position(s) for s in segs]
        left_most: Segment = self.segments[segments_positions[0]]
        if merge_name:
            self.rename_node(
                left_most.datas['name'], merge_name, edit_paths=False)
        right_most: Segment = self.segments[segments_positions[-1]]
        names_to_be_deleted: list[str] = [
            self.segments[segments_positions[i]].datas['name'] for i in range(1, len(segments_positions))]

        # Editing properties of node
        left_most.datas['length'] += sum([int(self.segments[i].datas['length'])
                                         for i in segments_positions[1:]])
        if 'seq' in left_most.datas:
            left_most.datas['seq'] = ''.join(
                [self.segments[i].datas['seq'] for i in segments_positions])

        # Find anchors for last node, and replicates it for first node
        edges_to_edit = self.get_edges_positions(
            right_most_name := right_most.datas['name'])
        left_most_name: str = left_most.datas['name']
        for edge_pos in edges_to_edit:
            if self.lines[edge_pos].datas['start'] == right_most_name:
                self.lines[edge_pos].datas['start'] = left_most_name
            else:
                self.lines[edge_pos].datas['end'] = left_most_name

        edges_to_delete = list(chain(*[self.get_edges_positions(
            self.segments[node_pos].datas['name']) for node_pos in segments_positions[1:-1]]))

        # Edit the paths by iterating over all paths
        # We assert position matching, and we reverse the ordering to edit without destrying info
        for ipath in self.get_path_list():
            sequence_length: int = len(names_to_be_deleted)
            path_segments: list = [waypoint[0]
                                   for waypoint in ipath.datas['path']]
            pos_to_edit: list = [i for i in range(len(path_segments)-sequence_length+1) if (
                names_to_be_deleted == path_segments[i:i+sequence_length])]
            for pos in pos_to_edit[::-1]:
                ipath.datas['path'] = ipath.datas['path'][:pos-1] + [(left_most_name, ipath.datas['path'][pos][1])] +\
                    ipath.datas['path'][pos+len(names_to_be_deleted):]

        # Delete nodes and edges that are not relevant anymore
        self.segments = [seg for i, seg in enumerate(
            self.segments) if i not in segments_positions[1:]]
        self.lines = [lin for i, lin in enumerate(
            self.lines) if i not in edges_to_delete]

        # Cleaning
        for sline in self.lines:
            if sline.datas['start'] == sline.datas['end']:
                self.lines.remove(sline)

        return left_most_name

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

    def remove_duplicates_segments(self) -> None:
        """Search for all nodes that are duplicates of each other, and keeps only one instance per node name"""
        # Cleaning node names
        for seg in self.segments:
            seg.datas["name"] = sub('\D', '', seg.datas["name"])
        # Purging duplicate values
        self.segments = list(
            {fseg.datas['name']: fseg for fseg in self.segments}.values())

    def remove_duplicates_edges(self) -> None:
        """Search for all nodes that are duplicates of each other, and keeps only one instance per node name"""
        set_of_nodes = [node.datas['name'] for node in self.segments]
        # Purging duplicate values
        self.lines = list(
            {f"{fedg.datas['start']}_{fedg.datas['end']}": fedg for fedg in self.lines if fedg.datas['end'] != fedg.datas['start'] and fedg.datas['end'] in set_of_nodes and fedg.datas['start'] in set_of_nodes}.values())
        # Cleaning edge names
        for edg in self.lines:
            edg.datas["start"] = sub('\D', '', edg.datas["start"])
            edg.datas["end"] = sub('\D', '', edg.datas["end"])

    def duplicate_segments(self, ntimes: int = 1):
        "Duplicate graph segments"
        duplicates: list = list()
        for _ in range(ntimes):
            duplicates += deepcopy(self.segments)
        self.segments += duplicates

    def get_segments_by_id(self, node: str | int) -> list[Segment]:
        """Search the node with the corresponding node name inside the graph, and returns it.

        Args:
            node (str): a string, identifier of the node

        Returns:
            Segment: a list of lines describing the node
        """
        node = str(node)
        matching_segments: list = list()
        for seg in self.segments:
            if sub('\D', '', seg.datas["name"]) == str(node):
                matching_segments.append(seg)
        return matching_segments

    def get_segment_position(self, node: str):
        """Search the node with the corresponding node name inside the graph, and returns it.

        Args:
            node (str): a string, identifier of the node

        Raises:
            ValueError: if node is not in graph

        Returns:
            Segment: the line describing the node
        """
        node = str(node)
        for i, seg in enumerate(self.segments):
            if seg.datas["name"] == node:
                return i
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

    def get_edges(self, node: str) -> list[Line]:
        """_summary_

        Args:
            node (str): _description_

        Returns:
            list[Line]: _description_
        """
        return [edge for edge in self.lines if node ==
                edge.datas['start'] or node == edge.datas['end']]

    def get_edges_positions(self, node: str) -> list[int]:
        """_summary_

        Args:
            node (str): _description_

        Returns:
            list[Line]: _description_
        """
        return [i for i, edge in enumerate(self.lines) if node ==
                edge.datas['start'] or node == edge.datas['end']]

    def get_most_external_nodes(self) -> list[str]:
        """Get nodes that are on the edges of the graph (starting and ending nodes)
        Those are characterized by their in/out degree : one of those has to be 0.

        Returns:
            list[str]: nodes names matching the condition.
        """
        bone: DiGraph = self.compute_backbone()
        return [x for x in bone.nodes() if bone.out_degree(x) == 0 or bone.in_degree(x) == 0]

    def compute_backbone(self) -> DiGraph:
        """Computes a networkx representation of the graph, for computing purposes

        Returns:
            DiGraph: a networkx graph featuring the backbone of the pangenome graph
        """
        backbone: DiGraph = DiGraph()

        for node in self.segments:
            backbone.add_node(
                node.datas['name'],
                offsets=node.datas['PO'] if 'PO' in node.datas else None,
                sequence=node.datas.get('seq', '')
            )
        for edge in self.lines:

            backbone.add_edge(
                edge.datas['start'],
                edge.datas['end'],
                label=edge.datas["orientation"],
            )
        return backbone

    def compute_networkx(self, node_prefix: str | None = None, node_size_classes: tuple[list] = ([0, 1], [2, 10], [11, 50], [51, 200],
                         [201, 500], [501, 1000], [1001, 10000], [10001, float('inf')])) -> MultiDiGraph:
        """Computes the networkx representation of the GFA.
        This function is intended to be used for graphical representation purposes, and not for computing metrics on the graph.

        Args:
            node_prefix (str): a prefix used when displaying multiple graphs to prevent node name collisions

        Returns:
            MultiDiGraph: a networkx graph featuring the maximum of information
        """
        node_palette: list = get_palette(
            len(node_size_classes), cmap_name='cool', as_hex=True)
        self.colors = {f"{bound_low}-{bound_high} bp": node_palette[i]
                       for i, (bound_low, bound_high) in enumerate(node_size_classes)}
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
                color=node_palette[[index for index, (low_limit, high_limit) in enumerate(
                    node_size_classes) if node.datas["length"] >= low_limit and node.datas["length"] <= high_limit][0]],
                size=10,
                offsets=node.datas['PO'] if 'PO' in node.datas else None,
                sequence=node.datas.get('seq', '')
            )
        palette: list = get_palette(
            len(path_list := self.get_path_list()), as_hex=True)

        self.colors = {**self.colors, **{p.datas["name"]: palette[i]
                       for i, p in enumerate(path_list)}}
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
            if self.headers and output_format != GfaStyle.RGFA:
                for head in self.headers:
                    gfa_writer.write(
                        "H\t"+'\t'.join([f"{key}:{dtype(value)}:{value}" if not key.startswith('ARG') else str(value) for key, value in head.datas.items()])+"\n")
            if self.segments:
                for seg in self.segments:
                    gfa_writer.write("S\t"+f"{seg.datas['name']}\t{seg.datas['seq'] if 'seq' in seg.datas else 'N'*seg.datas['length']}\t" + '\t'.join(
                        [f"{key}:{dtype(value)}:{value}" if not key.startswith('ARG') else str(value) for key, value in seg.datas.items() if key not in ['length', 'seq', 'name']])+"\n")
            if self.lines:
                for lin in self.lines:
                    ori1, ori2 = lin.datas['orientation'].split('/')
                    gfa_writer.write(f"L\t"+f"{lin.datas['start']}\t{ori1}\t{lin.datas['end']}\t{ori2}\t" + '\t'.join(
                        [f"{key}:{dtype(value)}:{value}" if not key.startswith('ARG') else str(value) for key, value in lin.datas.items() if key not in ['orientation', 'start', 'end']])+"\n")
            if self.get_path_list():
                for pathl in self.get_path_list():
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

    else:
        # W-line
        offset_start: int | str = way.datas['start_offset'] if 'start_offset' in way.datas else '?'
        offset_stop: int | str = way.datas['stop_offset'] if 'stop_offset' in way.datas else '?'
        strpath: str = ''.join(
            [f"{'>' if orient == Orientation.FORWARD else '<'}{node_name}" for node_name, orient in way.datas['path']])
        return f"W\t{way.datas['name']}\t{way.datas['origin'] if 'origin' in way.datas else line_number}\t{way.datas['name']}\t{offset_start}\t{offset_stop}\t{strpath}\t*\n"
