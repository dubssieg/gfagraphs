"This implementation is purely theorical and experimental, and should not be used in development for now."
from tharospytools.bio_tools import revcomp
from tharospytools.overloading import overload
from pgGraphs import Graph as FullGraph
from re import split as resplit
# Bubble object with fields:
# - nodes inside
# - paths inside
# - sequences described by paths (can be seen as sort of local gapless alingments)


class Bubble():

    __slots__ = [
        "__decompose__",
        "name",
        "nodes",
        "paths",
        "handle_left",
        "handle_right",
        "base_weight",
    ]

    def __str__(self) -> str:
        return self.name

    def __repr__(self) -> str:
        return self.name

    def __init__(self, bubble_name: str, segments: dict, local_paths: dict) -> None:
        """
        nodes is a list of all nodes inside the bubble
        content is a dict mapping paths to sequences
        segments are supposed to be a sub part of a gfagraphs.pgGraphs.Graph segment dict
        local_paths is a mapping path_name:path_composantes (as list of tuples)
        """
        self.name: str = bubble_name
        self.nodes: set[str] = list(segments.keys())
        self.base_weight: int = sum([len(seq) for seq in segments.values()])
        self.paths: dict[str, str] = {
            path_name: ''.join([(segments[seg_name], revcomp(segments[seg_name]))[seg_ori == '-'] for (seg_name, seg_ori) in path_sequence]) for path_name, path_sequence in local_paths.items()
        }
        # TODO: think of a higher compression level for this not_human readable string
        self.__decompose__: str = ';'.join([path_name+'#'+':'.join([node_name+node_ori+str(len(segments[node_name])) for (
            node_name, node_ori) in path_sequence]) for path_name, path_sequence in local_paths.items()])

    def __alt__(self, bubble_name: str, nodes: set[str], paths: dict[str, str], decomposition: str) -> None:
        """
        Objective of this function is to be able to reload a previously saved bubble
        by loading in memory all its fields and hopefully using unfold it reveals its internals
        (not recursive in this first implementation)
        """
        self.name: str = bubble_name
        self.nodes: set[str] = nodes
        self.paths: dict[str, str] = paths
        self.__decompose__: str = decomposition

    def unfold(self) -> tuple[str, dict, dict]:
        """Given a decomposition string of a bubble and its contents, return paths and nodes

        Returns:
            tuple[str,dict,dict]: _description_
        """
        segments: dict = dict()
        local_paths: dict[str, list] = dict()
        for path in self.__decompose__.split(';'):
            pos_counter: int = 0
            path_name, _, path_value = path.partition('#')
            local_paths[path_name] = list()
            for node_info in path_value.split(':'):
                node_name, node_ori, node_length = resplit(
                    '([+|-])', node_info)
                segments[node_name] = self.paths[path_name][pos_counter:(
                    pos_counter := pos_counter+int(node_length))]
                if node_ori == '-':
                    segments[node_name] = revcomp(segments[node_name])
                local_paths[path_name].append((node_name, node_ori))
        return (self.name, segments, local_paths)


class BubbleGraph():
    """
    Basically is a chain of bubbles.
    Bubbles have a right and a left handle, to be filled with references to other bubbles.
    Navigate the graph is a traversal of left or right neigbors
    """
    @staticmethod
    def get_neighbors(bubble: Bubble) -> list[Bubble]:
        return [getattr(bubble, 'handle_left', None), getattr(bubble, 'handle_right', None)]


if __name__ == "__main__":
    # Trying to populate an example structure with a GFA
    """
    gfa: FullGraph = FullGraph(
        gfa_file="path_to_some_gfa",
        with_sequence=True,
        low_memory=False,
    )
    """
    # creating some fake bubble
    segs: dict = {
        '1': 'AAA',
        '2': 'CAC',
        '3': 'AAA',
        '4': 'TTTTTTTTTTTTTTT',
        '5': 'AAA',
        '6': 'GGG',
    }
    paths: dict = {
        'seq1': [('1', '+'), ('2', '+'), ('6', '+')],
        'seq2': [('1', '+'), ('4', '-'), ('6', '+')],
        'seq3': [('1', '+'), ('3', '+'), ('4', '+'), ('5', '+'), ('6', '+')],
    }
    name: str = 'my_bubble'

    my_bubble: Bubble = Bubble(name, segs, paths)

    print(my_bubble.paths)
    print(my_bubble.nodes)
    print(my_bubble.__decompose__)
    print(my_bubble.unfold())
    print(my_bubble.base_weight)

    print(BubbleGraph.get_neighbors(my_bubble))
    my_bubble.handle_left = my_bubble
    print(BubbleGraph.get_neighbors(my_bubble))
