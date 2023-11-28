from tharospytools.path_tools import path_allocator
from graph import Graph
from abstractions import GFAFormat, Orientation
from gfaparser import GFAParser


class GFAIO:

    @staticmethod
    def save_graph(graph: Graph, output_path: str) -> None:
        """Given a gfa Graph object, saves to a valid gfa file the Graph.

        Args:
            output_path (str): a path on disk where to save
            output_format (GfaStyle): a format to choose for output.
                if None, default graph format will be used.
        """
        line_number: int = 0
        with open(path_allocator(output_path), 'w', encoding='utf-8') as gfa_writer:
            if graph.headers:
                for header in graph.headers:
                    gfa_writer.write(
                        "H\t"+'\t'.join([f"{key}:{GFAParser.get_python_type(value)}:{value}" if not key.startswith('ARG') else str(value) for key, value in header.items()])+"\n")
            if graph.segments:
                for segment_name, segment_datas in graph.segments.items():
                    gfa_writer.write("S\t"+f"{segment_name}\t{segment_datas['seq'] if 'seq' in segment_datas else 'N'*segment_datas['length']}\t" + '\t'.join(
                        [f"{key}:{GFAParser.get_python_type(value)}:{value}" if not key.startswith('ARG') else str(value) for key, value in segment_datas.items() if key not in ['length', 'seq']])+"\n")
            if graph.lines:
                for line in graph.lines:
                    ori1, ori2 = line['orientation'].split('/')
                    gfa_writer.write(f"L\t"+f"{line['start']}\t{ori1}\t{line['end']}\t{ori2}\t" + '\t'.join(
                        [f"{key}:{GFAParser.get_python_type(value)}:{value}" if not key.startswith('ARG') else str(value) for key, value in line.items() if key not in ['orientation', 'start', 'end']])+"\n")
            if graph.paths:
                for path_name, path_datas in graph.paths.items():
                    if graph.metadata['version'] == GFAFormat.GFA1:  # P-line
                        gfa_writer.write(
                            f"P\t{path_name}\t{','.join([node_name+'+' if orient == Orientation.FORWARD else node_name+'-' for node_name, orient in path_datas['path']])}\t*")
                    else:
                        # W-line
                        offset_start: int | str = path_datas['start_offset'] if 'start_offset' in path_datas else '?'
                        offset_stop: int | str = path_datas['stop_offset'] if 'stop_offset' in path_datas else '?'
                        strpath: str = ''.join(
                            [f"{'>' if orient == Orientation.FORWARD else '<'}{node_name}" for node_name, orient in path_datas['path']])
                        return f"W\t{path_name}\t{path_datas['origin'] if 'origin' in path_datas else line_number}\t{path_datas['name']}\t{offset_start}\t{offset_stop}\t{strpath}\t*\n"
                    line_number += 1
