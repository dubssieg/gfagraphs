from networkx import MultiDiGraph, DiGraph
from pgGraphs.graph import Graph
from tharospytools.matplotlib_tools import get_palette


class GFANetwork:

    @staticmethod
    def compute_backbone(
        graph: Graph
    ) -> DiGraph:
        """Computes a networkx representation of the graph, for computing purposes

        Returns:
            DiGraph: a networkx graph featuring the backbone of the pangenome graph
        """
        backbone: DiGraph = DiGraph()

        for node_name, node_datas in graph.segments.items():
            backbone.add_node(
                node_name,
                offsets=node_datas['PO'] if 'PO' in node_datas else None,
                sequence=node_datas.get('seq', '')
            )
        for edge_datas in graph.lines.values():

            backbone.add_edge(
                edge_datas['start'],
                edge_datas['end'],
                label=edge_datas["orientation"],
            )
        graph.metadata['backbone']
        return backbone

    @staticmethod
    def compute_networkx(
        graph: Graph,
        node_prefix: str | None = None,
        node_size_classes: tuple[list] = (
            [0, 1], [2, 10], [11, 50], [51, 200], [201, 500], [
                501, 1000], [1001, 10000], [10001, float('inf')]
        )
    ) -> MultiDiGraph:
        """Computes the networkx representation of the GFA.
        This function is intended to be used for graphical representation purposes, and not for computing metrics on the graph.

        Args:
            node_prefix (str): a prefix used when displaying multiple graphs to prevent node name collisions

        Returns:
            MultiDiGraph: a networkx graph featuring the maximum of information
        """
        # Define empty graph
        nx_graph: MultiDiGraph = MultiDiGraph()
        # Creating the palette for node class colors
        node_palette: list = get_palette(
            len(node_size_classes),
            cmap_name='cool',
            as_hex=True
        )
        graph.metadata['colors'] = {
            f"bp{bound_low}-{bound_high}": node_palette[i] for i, (bound_low, bound_high) in enumerate(node_size_classes)
        }
        node_prefix = f"{node_prefix}_" if node_prefix is not None else ""
        # Iterating on nodes
        for node_name, node_datas in graph.segments.items():
            node_title: list = []
            for key, val in node_datas.items():
                if isinstance(val, dict):
                    node_title.extend([f"{k} : {v}" for k, v in val.items()])
                else:
                    node_title.append(f"{key} : {val}")
            nx_graph.add_node(
                f"{node_prefix}{node_name}",
                title='\n'.join(node_title),
                color=node_palette[[index for index, (low_limit, high_limit) in enumerate(
                    node_size_classes) if node_datas["length"] >= low_limit and node_datas["length"] <= high_limit][0]],
                size=10,
                offsets=node_datas['PO'] if 'PO' in node_datas else None,
                sequence=node_datas.get('seq', '')
            )
        # Define a palette for paths
        palette: list = get_palette(
            len(graph.paths),
            as_hex=True
        )
        # Updating metadata
        graph.metadata['colors'] = {
            **graph.metadata['colors'],
            **{path_name: palette[i] for i, path_name in enumerate(graph.paths.keys())}
        }
        # If paths are available, we iterate on them
        if len(graph.paths) > 0:
            for y, (path_name, path_datas) in enumerate(graph.paths.items()):
                for i in range(len(path_datas["path"])-1):
                    left_node, left_orient = path_datas["path"][i]
                    right_node, right_orient = path_datas["path"][i+1]
                    nx_graph.add_edge(
                        f"{node_prefix}{left_node}",
                        f"{node_prefix}{right_node}",
                        title=path_name,
                        color=palette[y],
                        label=f"{left_orient.value}/{right_orient.value}",
                        weight=3
                    )
        # Otherwise we use edges
        else:
            for edge_datas in graph.lines.values():
                nx_graph.add_edge(
                    f"{node_prefix}{edge_datas['start']}",
                    f"{node_prefix}{edge_datas['end']}",
                    color='darkred',
                    label=edge_datas["orientation"],
                    weight=3
                )
        # Adding NX representation to metadata
        graph.metadata['graph'] = nx_graph
        return graph.metadata['graph']

    def get_most_external_nodes(self) -> list[str]:
        """Get nodes that are on the edges of the graph (starting and ending nodes)
        Those are characterized by their in/out degree : one of those has to be 0.

        Returns:
            list[str]: nodes names matching the condition.
        """
        bone: DiGraph = self.compute_backbone()
        return [x for x in bone.nodes() if bone.out_degree(x) == 0 or bone.in_degree(x) == 0]
