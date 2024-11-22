"Modelizes a graph object"
from itertools import count
from pgGraphs.abstractions import GFALine, Orientation, reverse
from pgGraphs.gfaparser import GFAParser
from gzip import open as gz_open
from typing import Any, Generator
from concurrent.futures import ThreadPoolExecutor
from multiprocessing import cpu_count
from typing import Callable
from collections.abc import Iterable


def futures_collector(
    func: Callable,
        argslist: list,
        kwargslist: list[dict] | None = None,
        num_processes: int = cpu_count(),
) -> list:
    """
    Spawns len(arglist) instances of func and executes them at num_processes instances at time.

    * func : a function
    * argslist (list): a list of tuples, arguments of each func
    * kwargslist (list[dict]) a list of dicts, kwargs for each func
    * num_processes (int) : max number of concurrent instances.
        Default : number of available logic cores
    * memory (float|None) : ratio of memory to be used, ranging from .05 to .95. Will not work if *resource* is incompatible.
    """
    if kwargslist is None or len(kwargslist) == len(argslist):
        with ThreadPoolExecutor(max_workers=num_processes) as executor:
            futures = [
                executor.submit(
                    func,
                    *args if isinstance(args, Iterable) else args
                ) if kwargslist is None else
                executor.submit(
                    func,
                    *args if isinstance(args, Iterable) else args,
                    **kwargslist[i]
                ) for i, args in enumerate(argslist)
            ]
        return [f.result() for f in futures]
    else:
        raise ValueError(
            f"""Positionnal argument list length ({len(argslist)})
            does not match keywords argument list length ({len(kwargslist)}).""")


def revcomp(string: str, compl: dict = {'A': 'T', 'C': 'G', 'G': 'C', 'T': 'A', 'N': 'N'}) -> str:
    """Tries to compute the reverse complement of a sequence

    Args:
        string (str): original character set
        compl (dict, optional): dict of correspondances. Defaults to {'A': 'T', 'C': 'G', 'G': 'C', 'T': 'A'}.

    Raises:
        IndexError: Happens if revcomp encounters a char that is not in the dict

    Returns:
        str: the reverse-complemented string
    """
    try:
        return ''.join([compl[s] for s in string][::-1])
    except IndexError as exc:
        raise IndexError(
            "Complementarity does not include all chars in sequence.") from exc


class Graph():
    """Modelizes a GFA graph in memory from a `.gfa` file.

    Returns
    -------
    Graph
        object made of dicts holding informations about the datastructure
    """
    __slots__ = [
        'segments',
        'lines',
        'paths',
        'headers',
        'metadata'
    ]

    def __init__(
        self,
        gfa_file: str | None = None,
        with_sequence: bool = True,
        low_memory: bool = False,
        with_reverse_edges: bool = False,
        regexp: str = ".*",
    ) -> None:
        """Constructor for GFA Graph object.

        Parameters
        ----------
        gfa_file : str | None, optional
            A file path to a valid GFA file, by default None
        with_sequence : bool, optional
            If sequence should be included in nodes. Consumes more memory with huge graphs, by default True
        low_memory : bool, optional
            If the minimal number of information should be loaded or not. If yes, will only load length of the nodes and the paths but not the edges, by default False
        with_reverse_edges : bool, optional
            If loading the graph should include computation of each reverse edge
        regexp : str, optional
            Regular expression to keep from the paths names (used to standardize/reduce them), by default ".*"
        """
        # Declaring format attributes, generators...
        self.metadata: dict = {
            'version': GFAParser.get_gfa_format(gfa_file_path=gfa_file) if gfa_file and not low_memory else 'unknown',
            'next_node_name': (x for x in count(start=1) if str(x) not in self.segments) if not low_memory else 'unknown',
            'with_sequence': with_sequence
        }
        self.segments: dict[str, dict] = {}
        self.lines: dict[tuple[str, str], dict] = {}
        self.paths: dict[str, dict] = {}
        self.headers: list[dict] = []

        # Parsing the gfa file
        if gfa_file and (gfa_file.endswith('.gfa') or gfa_file.endswith('.gfa.gz')):
            with open(gfa_file, 'r', encoding='utf-8') if gfa_file.endswith('.gfa') else gz_open(gfa_file, 'rt') as gfa_reader:
                for gfa_line in gfa_reader:

                    name, line_type, datas = GFAParser.read_gfa_line(
                        datas=[__.strip() for __ in gfa_line.split('\t')],
                        load_sequence_in_memory=with_sequence and not low_memory,
                        regexp_pattern=regexp,
                        memory_mode=low_memory,
                    )
                    match line_type:
                        case GFALine.SEGMENT:
                            self.segments[name] = datas
                        case GFALine.WALK | GFALine.PATH:
                            self.paths[name] = datas
                        case GFALine.LINK:
                            if name not in self.lines:
                                self.lines[name] = datas
                            else:
                                [_ors,] = datas['orientation']
                                self.lines[name]['orientation'].add(
                                    (_ors[0], _ors[1]))
                            if with_reverse_edges:
                                if name[::-1] not in self.lines:
                                    [_ors,] = datas['orientation']
                                    self.lines[name[::-1]] = {
                                        'orientation': set(
                                            [(reverse(_ors[1]), reverse(_ors[0]))]
                                        )
                                    }
                                else:
                                    self.lines[name[::-1]]['orientation'].add(
                                        (reverse(_ors[1]), reverse(_ors[0])))

                        case GFALine.HEADER:
                            self.headers.append(datas)
                        case _:
                            pass

    def __str__(self) -> str:
        """Returns a textual description of the object.

        Returns
        -------
        str
            a string which informs that the graph object is loaded.
        """
        return f"GFA Graph object ({self.metadata['version']}) containing {len(self.segments)} segments, {len(self.lines)} edges and {len(self.paths)} paths."

    def save_graph(self, output_file: str, minimal: bool = False, output_format: bool | Any = False) -> None:
        """Given a GFA graph loaded in memory, writes it to disk in a GFA-compatible format.

        Parameters
        ----------
        output_file : str
            path on disk where to output the GFA file
        minimal : bool, optional
            if only required tags should be written in the output file, by default False
        output_format : bool | Any, optional
            a GFA subformat to write to, by default False
        """
        GFAParser.save_graph(
            graph=self,
            output_path=output_file,
            force_format=output_format,
            minimal_graph=minimal,
        )

    def compare_pathnames_to_string(self, string_to_search: str) -> str | bool:
        for path_name, path_data in self.paths.items():
            if any(
                path_data['id'] == string_to_search,
                f"{path_data['name']}#{path_data['origin']}#{path_data['id']}" == string_to_search,
                f"{path_data['name']}.{path_data['origin']}.{path_data['id']}" == string_to_search,
                f"{path_data['name']}#{path_data['origin']}#{path_data['id']}#{path_data['origin']}" == string_to_search,
            ):
                return path_name
        return False

    def reconstruct_sequences(self) -> dict[str, Generator]:
        """Reads the paths (if they exists) that describes genomes in the graph
        Aggregates the nodes (by their reading direction) per path

        Returns
        -------
        dict[str, Generator]
            mapping between name of path and generator of every substring in the path

        Raises
        ------
        RuntimeError
            if the graph does not have paths
        """
        if not self.metadata['with_sequence']:
            raise RuntimeError(
                'You loaded the graph with `low_memory` activated, hence the segments do not have a `seq` property.'
            )
        return {
            path_name: (self.segments[node_name]['seq'] if ori == Orientation.FORWARD else revcomp(self.segments[node_name]['seq']) for node_name, ori in self.paths[path_name]['path']) for path_name in self.paths.keys()
        }

################################################# EDIT CYCLES #################################################

    def unfold(
        self
    ) -> None:
        """[EXPERIMENTAL, WIP]
        Applies an unfolding on cycles, that allows them to be linearized
        WARNING: May solely be used on graphs with paths.
        WARNING: Not fully tested yet, use at your own discretion.
        TODO: fix closing edge of cycle not destroyed.

        Raises
        ------
        NotImplementedError
            the graph does not have paths
        RuntimeError
            the graph was loaded in incorrect mode
        """
        if len(self.paths) == 0:
            raise NotImplementedError(
                "Function is not implemented for graphs without paths.")
        if not self.metadata['with_sequence']:
            raise RuntimeError(
                'You loaded the graph with `low_memory` or `with_sequence` activated, hence the segments do not have a `seq` property.'
            )
        # The node name correspondance is graph-level
        nodes_correspondances: dict[str, list] = dict()
        for _, path_data in self.paths.items():
            # Whereas the count is path-level
            encountered_node_count: dict[str, int] = dict()
            for i, (node, ori) in enumerate(path_data['path']):
                encountered_node_count[node] = encountered_node_count.get(
                    node, 0) + 1
                if encountered_node_count[node] > 1:
                    # We need to duplicate the node

                    try:
                        next_node_name: str = nodes_correspondances.get(
                            node, None)[encountered_node_count[node]-1]
                        # If succed, node already created
                    except:
                        # If fail, node does not exists, we need to create it
                        next_node_name: str = self.get_free_node_name()
                        nodes_correspondances[node] = nodes_correspondances.get(
                            node, []) + [next_node_name]
                        self.add_node(
                            next_node_name,
                            self.segments[node]['seq']
                        )
                    self.add_edge(
                        path_data['path'][i-1][0], path_data['path'][i-1][1], next_node_name, ori)
                    path_data['path'][i] = (next_node_name, ori)

################################################# NAVIGATE GRAPH #################################################

    def add_dovetails(
        self
    ) -> None:
        """
        Adds dovetails on tips of the graph (at the start/end of each path)
        """
        for x in ['source', 'sink']:
            self.add_node(
                name=x,
                sequence=''
            )
        for path_datas in self.paths.values():
            self.add_edge(
                source='source',
                ori_source=path_datas['path'][0][1],
                sink=path_datas['path'][0][0],
                ori_sink=path_datas['path'][0][1],
            )
            self.add_edge(
                source=path_datas['path'][-1][0],
                ori_source=path_datas['path'][-1][1],
                sink='sink',
                ori_sink=path_datas['path'][-1][1],
            )
            path_datas['path'] = [('source', '+')] + \
                path_datas['path'] + [('sink', '+')]

################################################# ADD ELEMNTS TO GRAPH #################################################

    def add_node(
        self,
        name: str,
        sequence: str,
        **metadata: dict
    ) -> None:
        """Applies the addition of a node on the currently edited graph.

        Parameters
        ----------
        name : str
            a name for the node to be added
        sequence : str
            a label (substring) associated to the node
        **metadata : Any
            optional, additional informations for the node (must be GFA-compatible)
        """
        if not self.metadata['with_sequence']:
            self.segments[name] = {
                'length': len(sequence),
                **metadata
            }
        else:
            self.segments[name] = {
                'seq': sequence,
                'length': len(sequence),
                **metadata
            }

    def add_edge(
        self,
        source: str,
        ori_source: str,
        sink: str,
        ori_sink: str,
        **metadata: dict
    ) -> None:
        """Applies the addition of an edge to the current graph

        Parameters
        ----------
        source : str
            the node form where the edge extrudes
        ori_source : str
            the orientation from which the edge comes
        sink : str
            the node to which the edge goes
        ori_sink : str
            the orientation the edge enters the target node
        **metadata : Any
            optional, supplementary GFA-compatible tags.

        Raises
        ------
        ValueError
            specified orientation is not compatible with GFA format
        """
        if not ori_sink in ['+', '-', '?', '=']:
            try:
                ori_sink = ori_sink.value
            except:
                raise ValueError("Not compatible with GFA format.")
        if not ori_source in ['+', '-', '?', '=']:
            try:
                ori_source = ori_source.value
            except:
                raise ValueError("Not compatible with GFA format.")
        if (source, sink) not in self.lines:
            self.lines[(source, sink)] = {
                'orientation': set([(Orientation(ori_source), Orientation(ori_sink))]),
                **metadata
            }
        else:
            self.lines[(source, sink)]['orientation'] = self.lines[(source, sink)].get(
                'orientation', set()) | set([(Orientation(ori_source), Orientation(ori_sink))])

    def add_path(
        self,
        identifier: str,
        name: str,
        chain: list[tuple[str, Orientation]],
        start: int = 0,
        end: int | None = None,
        origin: str | None = None,
        **metadata: dict
    ) -> None:
        """Applies the addition of a path on the currently edited graph.
        Please note that it does not add any of the maybe missing nodes or edges
        (as we cound not assume the length of nodes nor the orientation of edges)

        Parameters
        ----------
        name : str
            name of the path
        chain : list[tuple[str, Orientation]]
            a series of tuples describing node_name,orientation)
        start : int, optional
            starting offset for the path, by default 0
        end : int | None, optional
            ending offset of the path (length - start), by default None
        origin : str | None, optional
            alternative name, used for W-line formatting, by default None
        """
        self.paths[name] = {
            "id": identifier,
            "name": name,
            "origin": origin,
            "start_offset": start,
            "stop_offset": end if end is not None else sum([self.segments[x]['length'] for x, _ in chain]),
            "path": chain,
            **metadata
        }

################################################# GET ELEMENTS FROM GRAPH #################################################

    def get_out_edges(self, node_name: str) -> list[tuple[tuple[str, str], dict]]:
        """Return all the exiting edges of a node

        Parameters
        ----------
        node_name : str
            a node in the graph

        Returns
        -------
        list[tuple[tuple[str, str], dict]]
            for each edge matching criterion, the source and target as well as the supplementary tags
        """
        return [((source, sink), datas) for (source, sink), datas in self.lines.items() if source == node_name]

    def get_in_edges(self, node_name: str) -> list[tuple[tuple[str, str], dict]]:
        """Return all the entering edges of a node

        Parameters
        ----------
        node_name : str
            a node in the graph

        Returns
        -------
        list[tuple[tuple[str, str], dict]]
            for each edge matching criterion, the source and target as well as the supplementary tags
        """
        return [((source, sink), datas) for (source, sink), datas in self.lines.items() if sink == node_name]

    def get_edges(self, node_name: str) -> list[tuple[tuple[str, str], dict]]:
        """Return all the edges of a node

        Parameters
        ----------
        node_name : str
            a node in the graph

        Returns
        -------
        list[tuple[tuple[str, str], dict]]
            for each edge matching criterion, the source and target as well as the supplementary tags
        """
        return [((source, sink), datas) for (source, sink), datas in self.lines.items() if source == node_name or sink == node_name]

################################################# EDIT GRAPH #################################################

    def get_next_unused_node_name(self) -> str:
        """Returns the next available integer as str to identify a new node to be created, within the minmax range of nodes defined in the graph.

        Returns
        -------
        str
            a possible node name in the graph which is not used currently
        """
        return str(min(set(range(1, max([int(__) for __ in self.segments.keys()])+1)) - set([int(__) for __ in self.segments.keys()])))

    def split_segments(
        self,
        segment_name: str,
        future_segment_name: list,
        position_to_split: list
    ) -> None:
        """Given a segment to split and a series/single new name(s) + position(s),
        breaks the node in multiple nodes and includes splits them in the Graph data

        If you want to split the segment A into A,B, ... you must provide
        self.split_segments(
            A,[A,B, ...],[(start_A,end_A),(start_B,end_B), ...])

        Parameters
        ----------
        segment_name : str
            the node to split
        future_segment_name : list
            the futures names of the nodes. The current name will be used for the first node of the splitting series
        position_to_split : list
            a list of breakpoints where to split to.

        Raises
        ------
        ValueError
            the number of specified breakpoints is incompatible with the number of names provided
        """
        # First, we check if input parameters are correct
        node_to_split: dict = self.segments[segment_name]
        if not isinstance(future_segment_name, list):
            future_segment_name = [future_segment_name]
        if not isinstance(position_to_split, list):
            position_to_split = [position_to_split]
        if len(future_segment_name) != len(position_to_split):
            raise ValueError(
                "Number of breakpoints and future node names does not match.")

        # This is to handle possible multi-split
        sequence = node_to_split['seq'] if 'seq' in node_to_split else 'N' * \
            node_to_split['length']

        # Get incomming and exuting edges
        edges_of_node: list[tuple[tuple[str, str], dict]
                            ] = self.get_edges(segment_name)
        for (_, edge) in edges_of_node:
            if edge['start'] == segment_name:
                orient: str = edge.datas['orientation'].value.split('/')[0]
                # Edge is output, should be changed
                edge['start'] = future_segment_name[-1]
            else:
                orient: str = edge['orientation'].value.split('/')[-1]
                # Edge is incomming edge, should be kept

        # Edit first node
        node_to_split['seq'] = node_to_split['seq'][:position_to_split[0][1]
                                                    ] if 'seq' in node_to_split else 'N'*position_to_split[0][1]

        for i, positions in enumerate(position_to_split):
            # If the segment is the original, remove the segment
            if future_segment_name[i] == segment_name:
                del self.segments[node_to_split]
            # Divide the node by creating an new one and updating attributes
            pos1, pos2 = positions
            self.add_node(
                name=future_segment_name[i],
                sequence=sequence[pos1:pos2]
            )
            # Create new edge between, re-assign sorting edges to new node
            try:
                # Get orientation of incomming edge and output edge, mix them for orientation of the new edge
                self.add_edge(
                    source=future_segment_name[i],
                    ori_source=orient,
                    sink=future_segment_name[i+1],
                    ori_sink=orient
                )
            except IndexError:
                pass

        # Add to paths by inserting after node to be splitted
        for path_datas in self.paths.values():
            new_path: list[tuple] = list()
            for i, (node_name, orientation) in path_datas['path']:
                if node_name == segment_name:
                    new_path.extend([(new_name, Orientation(
                        orient)) for new_name in future_segment_name])
                else:
                    new_path.append((node_name, orientation))

    def rename_node(
        self,
        old_name: str,
        new_name: str
    ) -> None:
        """Replace the node name and all its references
        be it in path, node accessions, edges

        Parameters
        ----------
        old_name : str
            the current name of the node
        new_name : str
            the new name to be given to the node
        """
        try:
            node_data: dict = self.segments.pop(old_name)
        except KeyError:
            # The node is not in the graph
            return
        # Changing the name of the node
        self.segments[new_name] = node_data
        # Changing the name inside edges
        edges_to_edit: list = self.get_edges(old_name)
        for (edge_index, _) in edges_to_edit:
            edge_datas: dict = self.lines.pop(edge_index)
            if edge_datas['start'] == old_name:
                edge_datas['start'] = new_name
            else:
                edge_datas['end'] = new_name
            # Update edge in dict
            self.lines[(edge_datas['start'], edge_datas['end'])] = edge_datas
        # Updataing path names
        for path in self.paths.values():
            for idx, (node_name, orientation) in enumerate(path['path']):
                if node_name == old_name:
                    path['path'][idx] = (new_name, orientation)

    def merge_segments(
        self,
        *segs: str,
        merge_name: str | None = None
    ) -> None:
        """Given a series of nodes, merges it to the first of the series.

        Parameters
        ----------
        merge_name : str | None, optional
            the name to merge to. If not specified, uses the first of the series, by default None
        *segs : Series[str]
            a series of nodes to be merged. Must be consecutive and don't disturb other paths.
        """
        # Remove old nodes
        new_node_seq: str = ""
        for node_name in segs:
            node_datas: dict = self.segments.pop(node_name)
            new_node_seq += node_datas['seq'] if 'seq' in node_datas else 'N' * \
                node_datas['length']
        # Add new node
        self.add_node(name=merge_name, sequence=new_node_seq)
        # Reconnect edges
        left_edges, right_edges = self.get_in_edges(
            segs[0]), self.get_out_edges(segs[-1])
        for (edge_index, _) in left_edges:
            edge_datas: dict = self.lines.pop(edge_index)
            edge_datas['end'] = merge_name
            self.lines[(edge_index[0], merge_name)] = edge_datas
        for (edge_index, _) in right_edges:
            edge_datas: dict = self.lines.pop(edge_index)
            edge_datas['start'] = merge_name
            self.lines[(merge_name, edge_index[-1])] = edge_datas
        # Edit paths
        for path in self.paths.values():
            path_nodes: list[str] = [x[0] for x in path['path']]
            positions: list[int] = [i for i in range(
                len(path['path'])-len(segs)+1) if (segs == path_nodes[i:i+len(segs)])][::-1]
            # We go backwards to dodge index collisions
            for pos in positions:
                path['path'][pos:pos-len(segs)+1] = [merge_name]

############### POsitionnal tag ###############

    def compute_orientations(self) -> None:
        """
        Computes both predecessors and successors, by their orientations
        This function is O(n) with n being the number of edges.
        """
        for node in self.segments.keys():
            self.segments[node]['out'] = {
                Orientation.FORWARD: set(),
                Orientation.REVERSE: set(),
            }
            self.segments[node]['in'] = {
                Orientation.FORWARD: set(),
                Orientation.REVERSE: set(),
            }
        for (from_node, to_node), datas in self.lines.items():
            for from_orientation, to_orientation in datas['orientation']:
                self.segments[from_node]['out'][from_orientation].add(
                    (to_node, to_orientation))
                self.segments[to_node]['in'][to_orientation].add(
                    (from_node, from_orientation))

    def compute_neighbors(self) -> None:
        """
        Computes both predecessors and successors
        This function is O(n) with n being the number of edges.
        """
        for node in self.segments.keys():
            self.segments[node]['successors'] = set()
            self.segments[node]['predecessors'] = set()
        for from_node, to_node in self.lines.keys():
            self.segments[from_node]['successors'].add(to_node)
            self.segments[to_node]['predecessors'].add(from_node)

    def compute_child_nodes(self) -> None:
        """
        For each edge in the graph, annotates extruding nodes from the edges info
        This function is O(n) with n being the number of edges.
        """
        for node in self.segments.keys():
            self.segments[node]['successors'] = set()  # set[str]
        for from_node, to_node in self.lines.keys():
            self.segments[from_node]['successors'].add(to_node)

    def compute_parent_nodes(self) -> None:
        """
        For each edge in the graph, annotates intruding nodes from the edges info
        This function is O(n) with n being the number of edges.
        """
        for node in self.segments.keys():
            self.segments[node]['predecessors'] = set()  # set[str]
        for from_node, to_node in self.lines.keys():
            self.segments[to_node]['predecessors'].add(from_node)

    def global_offset(self, reference: str, threads: int = 1) -> None:
        """We want to create a global offset (GO) for each node, which consists
        in the positions the sequences would have if they were represented as a left-normalized multiple alignement, with gaps.
        Positions are stored in the segments, with the "GO" tag.
        Warning: if reference has loops, positions are going to be ambiguous.
        Moreover, in this first version, only one coordinate per node is assigned, meaning loops wont be annotated twice.
        As of now function is NOT RECOMMANDED to use for production.
        This fonction is RECURSIVE and will FAIL on HUGE GRAPHS.

        Parameters
        ----------
        reference : str
            name of the path we want to use as backbone for our position system
        threads : int, optional
            number of threads to use for computation (max parallel deep seaches), by default 1
        """
        # We pre-compute successors of nodes for easy walks in the graph
        self.compute_child_nodes()

        # We create list of nodes we shall investigate from
        ref_path: list[str] = [x for x, _ in self.paths[reference]['path']]

        # We initialize all positions for all nodes to 0
        for seg in self.segments.keys():
            self.segments[seg]['GO'] = [0, 0]  # list[int, int]

        def start_recursion(node_name: str, current_coord: int, thread_name: str = 't0'):
            for seg in self.segments.keys():
                self.segments[seg][thread_name] = False
            explore(node_name=node_name, current_coord=current_coord,
                    thread_name=thread_name)
            for seg in self.segments.keys():
                del self.segments[seg][thread_name]

        def explore(node_name: str, current_coord: int, thread_name: str) -> None:
            """Recursive function that is guided by the net to explore all nodes in graph and annotates them

            Parameters
            ----------
            node_name : str
                the node we're in at the current iteration
            current_coord : int
                position we're at
            thread_name : str
                identifier for thread for visited boolean tracking
            """
            self.segments[node_name]['GO'][0] = max(
                self.segments[node_name]['GO'][0], current_coord)
            self.segments[node_name]['GO'][1] = self.segments[node_name]['GO'][0] + \
                self.segments[node_name]['length']

            for successor_name in self.segments[node_name]['successors']:
                # Node as already been visited or is in reference, we end recursion
                if self.segments[successor_name][thread_name] or successor_name in ref_path:
                    self.segments[successor_name]['GO'][0] = max(
                        self.segments[successor_name]['GO'][0], current_coord)+self.segments[node_name]['length']
                    self.segments[successor_name]['GO'][1] = self.segments[successor_name]['GO'][0] + \
                        self.segments[successor_name]['length']
                # Node is reachable, has not been visited yet, and is not in reference.
                else:
                    explore(successor_name,
                            self.segments[node_name]['GO'][1], thread_name)

        # Recursion loop over successive reference nodes
        futures_collector(
            func=start_recursion,
            argslist=[
                (seg, self.segments[seg]['GO'][1]) for seg in ref_path
            ],
            kwargslist=[
                {'thread_name': f't{i}'} for i in range(len(ref_path))
            ],
            num_processes=threads,
        )

    def sequence_offsets(self, recalculate: bool = False) -> None:
        """Calculates the offsets within each path for each node
        Here, we aim to extend the current GFA tag format by adding tags
        that do respect the GFA naming convention.
        A JSON string, PO (Path Offset) positions, relative to paths.
        Hence, PO:J:{'w1':[(334,335,'+')],'w2':[(245,247,'-')]} tells that the walk/path w1
        contains the sequence starting at position 334 and ending at position 335,
        and the walk/path w2 contains the sequence starting at the offset 245 (ending 247),
        and that the sequences are reversed one to each other.
        Note that any non-referenced walk in this field means that the node
        is not inside the given walk.

        Parameters
        ----------
        recalculate : bool, optional
            If the offsets should be re-computed from scratch, by default False
        """
        if not 'PO' in self.metadata or recalculate:
            for walk_name, walk_datas in self.paths.items():
                start_offset: int = int(
                    walk_datas['start_offset']) if 'start_offset' in walk_datas.keys() and isinstance(walk_datas['start_offset'], int) is None else 0
                for node, vect in walk_datas["path"]:
                    if 'PO' not in self.segments[node]:
                        # dict[str,list[tuple[int, int, Orientation]]]
                        self.segments[node]['PO'] = dict()
                    if walk_name in self.segments[node]['PO']:
                        # We already encountered the node in this path
                        self.segments[node]['PO'][walk_name].append(
                            (start_offset, start_offset+self.segments[node]['length'], vect.value))
                    else:
                        # First time we encounter this node for this path
                        self.segments[node]['PO'][walk_name] = [
                            (start_offset, start_offset+self.segments[node]['length'], vect.value)]
                    start_offset += self.segments[node]['length']
        self.metadata['PO'] = True

    def __enter__(self):
        return self

    def __exit__(self, *exc_info) -> None:
        del self

    def get_free_node_name(self) -> str:
        """Asks the generator for the next available node name

        Returns
        -------
        str
            the generator should be computed and won't work in `low_memory` mode
        """
        return str(next(self.metadata['next_node_name']))
