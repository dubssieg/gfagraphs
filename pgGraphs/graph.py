"Modelizes a graph object"
from pgGraphs.abstractions import GFALine, Orientation
from pgGraphs.gfaparser import GFAParser


class Graph():
    """
    Modelizes a GFA graph
    """
    __slots__ = [
        'segments',
        'lines',
        'paths',
        'headers',
        'metadata'
    ]

    def __init__(self, gfa_file: str | None = None, with_sequence: bool = True) -> None:
        """Constructor for GFA Graph object.

        Args:
            gfa_file (str | None, optional): A file path to a valid GFA file. Defaults to None.
            with_sequence (bool, optional): If sequence should be included in nodes. Consumes more memory with huge graphs. Defaults to False.

        Raises:
            ValueError: A line does not start with a capital letter
        """
        # Declaring format attributes
        self.metadata: dict = {'version': GFAParser.get_gfa_format(
            gfa_file_path=gfa_file) if gfa_file else 'unknown'}
        self.segments: dict[str, dict] = {}
        self.lines: dict[tuple[str, str], dict] = {}
        self.paths: dict[str, dict] = {}
        self.headers: list[dict] = []

        # Parsing the gfa file
        if gfa_file:
            with open(gfa_file, 'r', encoding='utf-8') as gfa_reader:
                for gfa_line in gfa_reader:

                    if not gfa_line[0].isupper() and len(gfa_line.strip()) != 0:
                        raise ValueError(
                            "All GFA lines shall start with a capital letter. Wrong format, please fix."
                        )

                    name, line_type, datas = GFAParser.read_gfa_line(
                        gfa_line.split('\t'), with_sequence)
                    match line_type:
                        case GFALine.SEGMENT:
                            self.segments[name] = datas
                        case GFALine.WALK | GFALine.PATH:
                            self.paths[name] = datas
                        case GFALine.LINE:
                            self.lines[name] = datas
                        case GFALine.HEADER:
                            self.headers.append(datas)
                        case _:
                            pass

    def __str__(self) -> str:
        """Provides a text representation of the graph

        Returns:
            str: a string describing the graph
        """
        return f"GFA Graph object ({self.metadata['version']}) containing {len(self.segments)} segments, {len(self.lines)} edges and {len(self.paths)} paths."

    def save_graph(self, output_file: str) -> None:
        """Given a GFA graph loaded in memory, writes it to disk in a GFA-compatible format.

        Args:
            output_file (str): path where to output the graph
        """
        GFAParser.save_graph(self, output_path=output_file)

################################################# EDIT CYCLES #################################################

    def unfold(
        self
    ) -> None:
        """Applies an unfolding on cycles, that allows them to be linearized
        WARNING: May solely be used on graphs with paths.
        WARNING: Not fully tested yet, use at your own discretion.
        """
        if len(self.paths) == 0:
            raise NotImplementedError(
                "Function is not implemented for graphs without paths.")
        number_of_nodes: int = len(self.segments)
        for path_datas in self.paths.values():
            iters: int = 0
            encountered: dict = {}
            for i, (node, oriT) in enumerate(path_datas['path']):
                # Getting the number of times we've see this node, then storing it
                encountered[node] = encountered.get(node, 0)+1
                if encountered.get(node, 1)-1:
                    # Node has been seen more than one time!
                    new_name: str = str(number_of_nodes+iters)
                    # Adding new node
                    self.add_node(
                        name=new_name,
                        sequence=self.segments[node]['seq'],
                        metadata=self.segments[node]
                    )
                    # Renaming in path
                    path_datas['path'][i][0] = new_name
                    # We need to add new edge
                    try:
                        self.add_edge(
                            source=path_datas['path'][i-1][0],
                            ori_source=path_datas['path'][i-1][1],
                            sink=new_name,
                            ori_sink=oriT
                        )
                    except:
                        # Will happen if loop at first position in the graph (that would not happen normally)
                        pass
                    finally:
                        iters += 1

        # If we did calculate positions, those are not accurate anymore, needs recomputing
        if 'PO' in self.metadata:
            self.sequence_offsets(recalculate=True)


################################################# ADD ELEMNTS TO GRAPH #################################################

    def add_node(
        self,
        name: str,
        sequence: str,
        **metadata: dict
    ) -> None:
        """Applies the addition of a node on the currently edited graph.

        Args:
            name (str): name of the future node
            sequence (str): DNA sequence associated to node
            metadata (dict,optional) additional tags (GFA-compatible) for the node
        """
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

        Args:
            source (str): name of source node
            ori_source (str): orientation from the exiting node
            sink (str): name of sink node
            ori_sink (str): orientation in the entering node
            metadata (dict,optional) additional tags (GFA-compatible) for the edge
        """
        self.lines[(source, sink)] = {
            'start': source,
            'end': sink,
            'orientation': f"{ori_source}/{ori_sink}",
            **metadata
        }

    def add_path(
        self,
        name: str,
        chain: list[tuple[str, Orientation]],
        start: int = 0,
        end: int | None = None,
        origin: str | None = None,
        **metadata: dict
    ) -> None:
        """Applies the addition of a path on the currently edited graph.

        Args:
            name (str): name for the future path
            chain (list[tuple[str, Orientation]]): a list of couples node_name/orientation that describes the walk of a genome
            start (int, optional): Starting offset of the path. Defaults to 0.
            end (int | None, optional): Ending offset of the path. Defaults to None.
            origin (str | None, optional): Haplotype number. Defaults to None.
            metadata (dict,optional) additional tags (GFA-compatible) for the path
        """
        self.paths[name] = {
            "id": name,
            "origin": origin,
            "start_offset": start,
            "stop_offset": end if end is not None else sum([self.segments[x]['length'] for x, _ in chain]),
            "path": chain,
            **metadata
        }

################################################# GET ELEMENTS FROM GRAPH #################################################

    def get_out_edges(self, node_name: str) -> list[tuple[tuple[str, str], dict]]:
        """Return all the exiting edges of a node

        Args:
            node_name (str): the query

        Returns:
            list[tuple[tuple[str, str], dict]]: the edges matching the condition
        """
        return [((source, sink), datas) for (source, sink), datas in self.lines.items() if source == node_name]

    def get_in_edges(self, node_name: str) -> list[tuple[tuple[str, str], dict]]:
        """Return all the entering edges of a node

        Args:
            node_name (str): the query

        Returns:
            list[tuple[tuple[str, str], dict]]: the edges matching the condition
        """
        return [((source, sink), datas) for (source, sink), datas in self.lines.items() if sink == node_name]

    def get_edges(self, node_name: str) -> list[tuple[tuple[str, str], dict]]:
        """Return all the edges of a node

        Args:
            node_name (str): the query

        Returns:
            list[tuple[tuple[str, str], dict]]: the edges matching the condition
        """
        return [((source, sink), datas) for (source, sink), datas in self.lines.items() if source == node_name or sink == node_name]

################################################# EDIT GRAPH #################################################

    def split_segments(
        self,
        segment_name: str,
        future_segment_name: str | list,
        position_to_split: tuple | list
    ) -> None:
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
                orient: str = edge.datas['orientation'].split('/')[0]
                # Edge is output, should be changed
                edge['start'] = future_segment_name[-1]
            else:
                orient: str = edge['orientation'].split('/')[-1]
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
        """Tries to replace all node name references

        Args:
            old_name (str): the name to replace
            new_name (str): the name to be replaced with
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

        Args:
            *segs (list): names of the nodes to merge
            merge_name (str | None, optional): name for the merging node. Defaults to None.
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

    def sequence_offsets(self, recalculate: bool = False) -> None:
        """
            Calculates the offsets within each path for each node
            Here, we aim to extend the current GFA tag format by adding tags
            that do respect the GFA naming convention.
            A JSON string, PO (Path Offset) positions, relative to paths.
            Hence, PO:J:{'w1':[(334,335,'+')],'w2':[(245,247,'-')]} tells that the walk/path w1
            contains the sequence starting at position 334 and ending at position 335,
            and the walk/path w2 contains the sequence starting at the offset 245 (ending 247),
            and that the sequences are reversed one to each other.
            Note that any non-referenced walk in this field means that the node
            is not inside the given walk.
        """
        if not 'PO' in self.metadata or recalculate:
            for walk_name, walk_datas in self.paths.items():
                start_offset: int = int(
                    walk_datas['start_offset']) if 'start_offset' in walk_datas.keys() and isinstance(walk_datas['start_offset'], int) is None else 0
                for node, vect in walk_datas["path"]:
                    if 'PO' not in self.segments[node]:
                        self.segments[node]['PO']: dict[str,
                                                        list[tuple[int, int, Orientation]]] = dict()
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
