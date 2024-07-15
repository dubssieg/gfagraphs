from re import match
from typing import Callable
from json import loads, dumps
from os import path, stat
from tharospytools.path_tools import path_allocator
from pgGraphs.abstractions import Orientation, GFALine, GFAFormat
from gzip import open as gz_open
from re import search


class GFAParser:
    """This class implements static methods to get informations about the contents of a GFA file, and to parse them.

    Returns
    -------
    None
        Methods are static and should be used passing arguments.

    Raises
    ------
    OSError
        The file does not exists
    IOError
        File is empty
    IOError
        File descriptor is invalid
    NotImplementedError
        Byte-array or array is saved to GFA
    ValueError
        Data format not in GFA standards
    """

    @staticmethod
    def get_gfa_format(gfa_file_path: str | list[str]) -> str | list[str]:
        """Given a file, or more, returns the gfa subtypes, and raises error if file is invalid or does not exists.
        Objective is to asses GFA subformat on files for pre-processing purposes, or algorithm choices.

        Parameters
        ----------
        gfa_file_path : str | list[str]
            a series of paths, or a single one

        Returns
        -------
        str | list[str]
            per path, a tag identifying the gfa type

        Raises
        ------
        OSError
            Specified file does not exists
        IOError
            File descriptor is invalid
        IOError
            File is empty
        """
        styles: list[str] = list()
        if isinstance(gfa_file_path, str):
            gfa_file_path = [gfa_file_path]
        for gfa_file in gfa_file_path:
            # Checking if path exists
            if not path.exists(gfa_file):
                raise OSError(
                    "Specified file does not exists. Please check provided path."
                )
            # Checking if file descriptor is valid
            if not gfa_file.endswith('.gfa') and not gfa_file.endswith('.gfa.gz'):
                raise IOError(
                    "File descriptor is invalid. Please check format, this lib is designed to work with Graphical Fragment Assembly (GFA) files."
                )
            # Checking if file is not empty
            if stat(gfa_file).st_size == 0:
                raise IOError(
                    "File is empty."
                )

            with open(gfa_file, 'r', encoding='utf-8') if gfa_file.endswith('.gfa') else gz_open(gfa_file, 'rt') as gfa_reader:
                header: str = gfa_reader.readline()
                if header[0] != 'H':
                    styles.append('rGFA')
                else:
                    try:
                        version_number: str = GFAParser.supplementary_datas(
                            header.strip('\n').split('\t'), 1
                        )["VN"]
                        if version_number == '1.0':
                            styles.append('GFA1')
                        elif version_number == '1.1':
                            styles.append('GFA1.1')
                        elif version_number == '1.2':
                            styles.append('GFA1.2')
                        elif version_number == '2.0':
                            styles.append('GFA2')
                        else:
                            styles.append('unknown')
                    except KeyError:
                        styles.append('rGFA')
        if len(styles) == 1:
            return styles[0]
        return styles

    @staticmethod
    def get_gfa_type(tag_type: str) -> type | Callable:
        """Interprets tags of GFA as a Python-compatible format.
        Given a letter used as a tag in the GFA standard, return the type or function to cast the data to.
        This function is used in input scenarios, to read a file from disk and interpret its content

        Parameters
        ----------
        tag_type : str
            a GFA tag

        Returns
        -------
        type | Callable
            a cast descriptor to use on the data

        Raises
        ------
        NotImplementedError
            Byte-array or array
        ValueError
            Type identifer is not in the GFA-spec
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
        raise ValueError(
            f"Type identifier {tag_type} is not in the GFA standard")

    @staticmethod
    def set_gfa_type(tag_type: str) -> type | Callable:
        """Interprets tags of GFA as a Python-compatible format.
        Given a letter used as a tag in the GFA standard, return the type or function to cast the data to.
        This function is used in output scenarios, to write a file to disk.

        Parameters
        ----------
        tag_type : str
            a GFA tag

        Returns
        -------
        type | Callable
            a cast descriptor to use on the data
        """
        if tag_type == 'J':
            return dumps
        else:
            return str

    @staticmethod
    def get_python_type(data: object) -> str:
        """From a python variable, tries to identify the best suiting tag, and validates it.
        See http://gfa-spec.github.io/GFA-spec/GFA1.html#optional-fields for more details.

        Parameters
        ----------
        data : object
            the data we try to add to the GFA file

        Returns
        -------
        str
            a one-letter code for an optional filed of the GFA-spec

        Raises
        ------
        ValueError
            data type could not be encoded in the GFA-spec
        """
        if isinstance(data, int):
            return 'i'
        elif isinstance(data, float):
            return 'f'
        elif isinstance(data, str):
            return 'Z'
        else:
            try:
                _: str = dumps(data, indent=0, separators=(',', ':'))
                return 'J'
            except (TypeError, OverflowError) as exc:
                raise ValueError(
                    f"Data {data} of type {type(data)} is not in the GFA standard") from exc

    @staticmethod
    def supplementary_datas(datas: list, length_condition: int) -> dict:
        """Computes the optional tags of a gfa line and returns them as a dict.

        Parameters
        ----------
        datas : list
            a list of tags and their values
        length_condition : int
            the tags that are mandatory (and already processed)

        Returns
        -------
        dict
            interpreted tags in their right types
        """
        mapping: dict = dict()
        nargs: int = length_condition
        if len(datas) > length_condition:  # we happen to have additional tags to our line
            for additional_tag in datas[length_condition:]:
                if match('[A-Z]{2}:[a-zA-Z]{1}:', additional_tag):  # matches start of the line
                    mapping[additional_tag[:2]] = GFAParser.get_gfa_type(
                        additional_tag[3])(additional_tag[5:])
                else:
                    mapping[f"ARG{nargs}"] = additional_tag
                    nargs += 1
        return mapping

    @staticmethod
    def read_gfa_line(datas: list[str], load_sequence_in_memory: bool = True, regexp_pattern: str = ".*", memory_mode: bool = True) -> tuple[str, GFALine, dict]:
        """Calls methods to parse a GFA line, accordingly to it's fields described in the GFAspec github.
        Parses a single line and return the information it contains

        Parameters
        ----------
        datas : list[str]
            the list of tab-separated elements of the GFA line.
        load_sequence_in_memory : bool, optional
            if it is a node, if the sequance should be or not loaded, by default True
        regexp_pattern : str, optional
            a pattern to keep for path names, by default ".*"
        memory_mode : bool, optional
            if additional information should be loaded in the struct, by default True

        Returns
        -------
        tuple[str, GFALine, dict]
            Contains `id_of_line`, `type_of_line`, `datas_of_line`
        """
        line_datas: dict = dict()
        if not (datas[0].isupper() or len(datas) == 0):
            return (None, None, None)

        match (line_type := GFALine(datas[0])):
            case GFALine.SEGMENT:
                line_datas["length"] = len(datas[2])
                if load_sequence_in_memory:
                    line_datas["seq"] = datas[2]
                if memory_mode:
                    return (datas[1], line_type, {**line_datas, **GFAParser.supplementary_datas(datas, 3)})
                else:
                    return (datas[1], line_type, line_datas)
            case GFALine.LINE:
                if not memory_mode:
                    line_datas["orientation"] = set(
                        [
                            (
                                Orientation(datas[2]),
                                Orientation(datas[4]),
                            )
                        ]
                    )
                    return ((datas[1], datas[3]), line_type, {**line_datas, **GFAParser.supplementary_datas(datas, 5)})
                else:
                    return (None, None, None)
            case GFALine.WALK:
                line_datas["name"] = datas[1]
                line_datas["id"] = datas[3]
                line_datas["origin"] = datas[2]
                line_datas["start_offset"] = datas[4]
                line_datas["stop_offset"] = datas[5]
                line_datas["path"] = [
                    (
                        node[1:],
                        Orientation(node[0])
                    )
                    for node in datas[6].replace('>', ',+').replace('<', ',-')[1:].split(',')
                ]
                try:
                    label: str = search(
                        regexp_pattern, datas[3]).group(1).upper()
                except:
                    label: str = datas[3].upper()
                return (label, line_type, {**line_datas, **GFAParser.supplementary_datas(datas, 7)})
            case GFALine.PATH:
                line_datas["name"] = datas[1]
                line_datas["id"] = datas[1]
                line_datas["origin"] = None
                line_datas["start_offset"] = None
                line_datas["stop_offset"] = None
                line_datas["path"] = [
                    (
                        node[:-1],
                        Orientation(node[-1])
                    )
                    for node in datas[2].split(',')
                ]
                try:
                    label: str = search(
                        regexp_pattern, datas[1]).group(1).upper()
                except:
                    label: str = datas[1].upper()
                return (label, line_type, {**line_datas, **GFAParser.supplementary_datas(datas, 7)})
            case GFALine.HEADER | GFALine.ANY:
                return (None, line_type, GFAParser.supplementary_datas(datas, 1))

    @ staticmethod
    def save_graph(graph, output_path: str, force_format: GFAFormat | bool = False, minimal_graph: bool = False) -> None:
        """Given a gfa Graph object, saves to a valid gfa file the Graph.

        Parameters
        ----------
        graph : Graph
            the graph object loaded in memory
        output_path : str
            a path to an existing (or not) dile on the disk
        force_format : GFAFormat | bool, optional
            the output gfa subformat, by default False
        minimal_graph : bool, optional
            if only mandatory tags should be kept, by default False

        """
        # Haplotype number serves when we convert GFA1 to GFA1.1 for W-lines
        haplotype_number: int = 0
        gfa_format: GFAFormat = graph.metadata['version'] if not force_format else force_format

        with open(path_allocator(output_path), 'w', encoding='utf-8') as gfa_writer:
            if graph.headers and gfa_format != GFAFormat.RGFA:
                # Writing hearder to output file if file is not rgfa
                for header in graph.headers:
                    supplementary_text: str = '' if minimal_graph else '\t' + \
                        '\t'.join(
                            [str(value) for key, value in header.items() if key.startswith('ARG')])
                    gfa_writer.write(
                        "H\t"
                        +
                        '\t'.join(
                            [
                                f"{key}:{GFAParser.get_python_type(value)}:{GFAParser.set_gfa_type(GFAParser.get_python_type(value))(value)}" for key, value in header.items() if not key.startswith('ARG')
                            ]
                        )
                        +
                        supplementary_text
                        +
                        "\n"
                    )
            if graph.segments:
                # Whichever the format, those should be written
                for segment_name, segment_datas in graph.segments.items():
                    supplementary_text: str = '' if minimal_graph else "\t" + '\t'.join(
                        [f"{key}:{GFAParser.get_python_type(value)}:{GFAParser.set_gfa_type(GFAParser.get_python_type(value))(value)}" if not key.startswith('ARG') else str(value) for key, value in segment_datas.items() if key not in ['length', 'seq']])
                    gfa_writer.write(
                        "S\t"+f"{segment_name}\t{segment_datas['seq'] if 'seq' in segment_datas else 'N'*segment_datas['length']}{supplementary_text}\n")
            if graph.lines:
                for (source, sink), line in graph.lines.items():
                    supplementary_text: str = '' if minimal_graph else "\t" + '\t'.join(
                        [f"{key}:{GFAParser.get_python_type(value)}:{GFAParser.set_gfa_type(GFAParser.get_python_type(value))(value)}" if not key.startswith('ARG') else str(value) for key, value in line.items() if key not in ['orientation', 'start', 'end']])
                    # We accomodate for all alternatives orientation versions that are described in the input graph file to be written back
                    for alt in line['orientation']:
                        ori1, ori2 = alt
                        gfa_writer.write(
                            f"L\t"+f"{source}\t{ori1.value}\t{sink}\t{ori2.value}\t0M{supplementary_text}\n")
            if graph.paths:
                for path_name, path_datas in graph.paths.items():
                    supplementary_text: str = '' if minimal_graph else "\t" + '\t'.join(
                        [f"{key}:{GFAParser.get_python_type(value)}:{GFAParser.set_gfa_type(GFAParser.get_python_type(value))(value)}" if not key.startswith('ARG') else str(value) for key, value in path_datas.items() if key not in ['path', 'start_offset', 'stop_offset', 'origin', 'name', 'id']])
                    if gfa_format == GFAFormat.GFA1 or gfa_format == GFAFormat.ANY:  # P-line
                        strpath: str = ','.join(
                            [node_name+'+' if orient == Orientation.FORWARD else node_name+'-' for node_name, orient in path_datas['path']])
                        gfa_writer.write(
                            f"P\t{path_name}\t{strpath}{supplementary_text}\n")
                    elif gfa_format == GFAFormat.GFA1_1 or gfa_format == GFAFormat.GFA1_2 or gfa_format == GFAFormat.GFA2:
                        # W-line
                        offset_start: int | str = path_datas[
                            'start_offset'] if 'start_offset' in path_datas and path_datas['start_offset'] else 0
                        offset_stop: int | str = path_datas['stop_offset'] if 'stop_offset' in path_datas and path_datas['stop_offset'] else sum(
                            [graph.segments[x]['length'] for (x, _) in path_datas['path']])
                        strpath: str = ''.join(
                            [f"{'>' if orient == Orientation.FORWARD or orient == '+' else '<'}{node_name}" for node_name, orient in path_datas['path']])
                        gfa_writer.write(
                            f"W\t{path_name}\t{path_datas['origin'] if 'origin' in path_datas and path_datas['origin'] else haplotype_number}\t{path_name}\t{offset_start}\t{offset_stop}\t{strpath}{supplementary_text}\n")
                    # In the case graph format is rgfa, we don't write any paths to output file
                    haplotype_number += 1

    @staticmethod
    def save_subgraph(graph, output_path: str, nodes: set[str], force_format: GFAFormat | bool = False, minimal_graph: bool = False) -> None:
        """Given a gfa Graph object, saves to a valid gfa file the Graph.

        Parameters
        ----------
        graph : Graph
            the graph object loaded in memory
        output_path : str
            a path to an existing (or not) dile on the disk
        force_format : GFAFormat | bool, optional
            the output gfa subformat, by default False
        minimal_graph : bool, optional
            if only mandatory tags should be kept, by default False

        """
        # Haplotype number serves when we convert GFA1 to GFA1.1 for W-lines
        haplotype_number: int = 0
        if not force_format:
            gfa_format: GFAFormat = graph.metadata['version'] if isinstance(
                graph.metadata['version'], GFAFormat) else GFAFormat(graph.metadata['version'])
        else:
            gfa_format: GFAFormat = force_format

        with open(path_allocator(output_path), 'w', encoding='utf-8') as gfa_writer:
            if graph.headers and gfa_format != GFAFormat.RGFA:
                # Writing hearder to output file if file is not rgfa
                for header in graph.headers:
                    supplementary_text: str = '' if minimal_graph else '\t' + \
                        '\t'.join(
                            [str(value) for key, value in header.items() if key.startswith('ARG')])
                    gfa_writer.write(
                        "H\t"
                        +
                        '\t'.join(
                            [
                                f"{key}:{GFAParser.get_python_type(value)}:{GFAParser.set_gfa_type(GFAParser.get_python_type(value))(value)}" for key, value in header.items() if not key.startswith('ARG')
                            ]
                        )
                        +
                        supplementary_text
                        +
                        "\n"
                    )
            if graph.segments:
                # Whichever the format, those should be written
                for segment_name, segment_datas in graph.segments.items():
                    if segment_name in nodes:
                        supplementary_text: str = '' if minimal_graph else "\t" + '\t'.join(
                            [f"{key}:{GFAParser.get_python_type(value)}:{GFAParser.set_gfa_type(GFAParser.get_python_type(value))(value)}" if not key.startswith('ARG') else str(value) for key, value in segment_datas.items() if key not in ['length', 'seq']])
                        gfa_writer.write(
                            "S\t"+f"{segment_name}\t{segment_datas['seq'] if 'seq' in segment_datas else 'N'*segment_datas['length']}{supplementary_text}\n")
            if graph.lines:
                for (source, sink), line in graph.lines.items():
                    if source in nodes and sink in nodes:
                        supplementary_text: str = '' if minimal_graph else "\t" + '\t'.join(
                            [f"{key}:{GFAParser.get_python_type(value)}:{GFAParser.set_gfa_type(GFAParser.get_python_type(value))(value)}" if not key.startswith('ARG') else str(value) for key, value in line.items() if key not in ['orientation', 'start', 'end']])
                        # We accomodate for all alternatives orientation versions that are described in the input graph file to be written back
                        for alt in line['orientation']:
                            ori1, ori2 = alt
                            gfa_writer.write(
                                f"L\t"+f"{source}\t{ori1.value}\t{sink}\t{ori2.value}\t0M{supplementary_text}\n")
            if graph.paths:
                for path_name, path_datas in graph.paths.items():
                    supplementary_text: str = '' if minimal_graph else "\t" + '\t'.join(
                        [f"{key}:{GFAParser.get_python_type(value)}:{GFAParser.set_gfa_type(GFAParser.get_python_type(value))(value)}" if not key.startswith('ARG') else str(value) for key, value in path_datas.items() if key not in ['path', 'start_offset', 'stop_offset', 'origin', 'name', 'id']])
                    if gfa_format == GFAFormat.GFA1 or gfa_format == GFAFormat.ANY:  # P-line
                        strpath: str = ','.join(
                            [node_name+'+' if orient == Orientation.FORWARD else node_name+'-' for node_name, orient in path_datas['path'] if node_name in nodes])
                        gfa_writer.write(
                            f"P\t{path_name}\t{strpath}{supplementary_text}\n")
                    elif gfa_format == GFAFormat.GFA1_1 or gfa_format == GFAFormat.GFA1_2 or gfa_format == GFAFormat.GFA2:
                        # W-line
                        offset_start: int | str = path_datas[
                            'start_offset'] if 'start_offset' in path_datas and path_datas['start_offset'] else 0
                        offset_stop: int | str = path_datas['stop_offset'] if 'stop_offset' in path_datas and path_datas['stop_offset'] else sum(
                            [graph.segments[x]['length'] for (x, _) in path_datas['path']])
                        strpath: str = ''.join(
                            [f"{'>' if orient == Orientation.FORWARD or orient == '+' else '<'}{node_name}" for node_name, orient in path_datas['path'] if node_name in nodes])
                        gfa_writer.write(
                            f"W\t{path_name}\t{path_datas['origin'] if 'origin' in path_datas and path_datas['origin'] else haplotype_number}\t{path_name}\t{offset_start}\t{offset_stop}\t{strpath}{supplementary_text}\n")
                    # In the case graph format is rgfa, we don't write any paths to output file
                    haplotype_number += 1
