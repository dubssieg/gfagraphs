from networkx import MultiDiGraph, DiGraph
from pgGraphs.graph import Graph
import matplotlib as mpl
from matplotlib.colors import rgb2hex
from pgGraphs.abstractions import GFAFormat


def get_palette(number_of_colors: int, cmap_name: str = 'viridis', as_hex: bool = False) -> list:
    """Returns a number_of_colors-sized palette, as a list,
    that one can access with colors[i].

    Args:
        number_of_colors (int): number of colors needed
        cmap_name (str, optionnal) : name of the matplotlib colormap. Defaults to viridis.
        hex (bool) : specifies if colors shall be returned by rgb values (False, default) or hex (True)

    Returns:
        list: palette of colors
    """
    try:
        colormap = mpl.colormaps[cmap_name].resampled(number_of_colors)
    except Exception as exc:
        raise ValueError(
            f"The colormap {cmap_name} is not a valid colormap") from exc
    return [
        rgb2hex(colormap(x/number_of_colors)) if as_hex
        else colormap(x/number_of_colors) for x in range(number_of_colors)
    ]


class GFANetwork:
    """Abstract class for visualization and modelization of GFA in a NetworkX object

    Returns
    -------
    None
        Methods are static and should be used passing arguments.
    """

    @staticmethod
    def compute_backbone(
        graph: Graph
    ) -> DiGraph:
        """Computes a networkx representation of the graph, for computing purposes.
        This backbone contains the exact information of paths, nodes, edges... that is described in the loaded structure.
        Allows to use every method of networkx library on the graph to perform traversal, neighborhood...

        Parameters
        ----------
        graph : Graph
            a gfa graph loaded in memory using this library

        Returns
        -------
        DiGraph
            a networkx object, in the form of a directed graph.
        """
        backbone: DiGraph = DiGraph()

        for node_name, node_datas in graph.segments.items():
            backbone.add_node(
                node_name,
                offsets=node_datas['PO'] if 'PO' in node_datas else None,
                sequence=node_datas.get('seq', '')
            )
        for (start, end), edge_data in graph.lines.items():
            backbone.add_edge(
                start,
                end,
                label=' | '.join(
                    [f'{x.value}/{y.value}' for (x, y) in edge_data["orientation"]]),
            )
        return backbone

    @staticmethod
    def compute_networkx(
        graph: Graph,
        enforce_format: GFAFormat | None = None,
        node_prefix: str | None = None,
        node_size_classes: tuple[list] = (
            [0, 1], [2, 10], [11, 50], [51, 200], [201, 500], [
                501, 1000], [1001, 10000], [10001, float('inf')]
        ),
        start_stop_ref: tuple | bool = False,
    ) -> MultiDiGraph:
        """Computes the networkx representation of the GFA.
        This function is intended to be used for graphical representation purposes, and not for computing metrics on the graph.

        Parameters
        ----------
        graph : Graph
            a gfa graph loaded in memory using this library
        node_prefix : str | None, optional
            a name to put before every node, by default None
        node_size_classes : tuple[list], optional
            classes of size for coloring nodes, by default ( [0, 1], [2, 10], [11, 50], [51, 200], [201, 500], [ 501, 1000], [1001, 10000], [10001, float('inf')] )
        start_stop_ref : tuple | bool, optional
            defines starting and ending offset on the reference, by default False

        Returns
        -------
        MultiDiGraph
            a networkx object, in the form of a bidirected graph.
        """
        if start_stop_ref:
            graph.sequence_offsets(recalculate=True)
            start, stop, ref = start_stop_ref
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
        if len(graph.paths) > 0 and enforce_format != GFAFormat.RGFA:
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
            for (start, end), edge_data in graph.lines.items():
                nx_graph.add_edge(
                    f"{node_prefix}{start}",
                    f"{node_prefix}{end}",
                    color='darkred',
                    label=' | '.join(
                        [f'{x.value}/{y.value}' for (x, y) in edge_data["orientation"]]),
                    weight=3
                )
        return nx_graph

    def get_most_external_nodes(self) -> list[str]:
        """Get nodes that are on the edges of the graph (starting and ending nodes)
        Those are characterized by their in/out degree : one of those has to be 0.

        Returns
        -------
        list[str]
            nodes matching the criterion.
        """
        bone: DiGraph = self.compute_backbone()
        return [x for x in bone.nodes() if bone.out_degree(x) == 0 or bone.in_degree(x) == 0]
