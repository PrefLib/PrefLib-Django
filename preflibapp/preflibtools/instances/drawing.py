""" This module describes procedures to draw images out of PrefLib instances.
"""

import matplotlib.pyplot as plt
import networkx as nx
import numpy as np

import time

from ..properties.basic import borda_scores


def draw_instance(instance, img_file_path):
    """ Generate an image file of the instance.

        :param instance: The instance to draw.
        :type instance: :class:`preflibtools.instances.preflibinstance.PreflibInstance`
        :param img_file_path: Path to which save the image.
        :type img_file_path: str or path
    """
    if instance.data_type in ["soc", "soi", "toc", "toi"]:
        draw_order(instance, img_file_path)
    elif instance.data_type in ["tog", "mjg", "wmg", "pwg"]:
        draw_graph(instance, img_file_path)
    elif instance.data_type == "wmd":
        draw_graph(instance, img_file_path, is_WMD=True)
    elif instance.data_type in ["dat", "csv"]:
        pass
    else:
        raise SyntaxError("File extension " + str(instance.data_type) + " is unknown to PrefLib instance. " +
                          "This file cannot be parsed.")


def draw_graph(instance, img_file_path, max_num_node=100, is_WMD=False):
    """ Generates the image file for an instance representing a graph.

        :param instance: The instance to draw.
        :type instance: :class:`preflibtools.instances.preflibinstance.PreflibInstance`
        :param img_file_path: Path to which save the image.
        :type img_file_path: str or path
        :param max_num_node: The maximum number of nodes of the graph to draw, default is 100.
        :type max_num_node: int
        :param is_WMD: True if the graph to parse represents weighted matching data, default is False.
        :type is_WMD: bool
    """
    print("Drawing: " + str(img_file_path))
    start_time = time.time()
    plt.close('all')
    nx_graph = nx.DiGraph()
    nx_graph.add_nodes_from([n for n in instance.graph.dict if n <= max_num_node])
    print(str(len(nx_graph.nodes())) + " nodes added to nx_graph: " + str(time.time() - start_time))
    for e in instance.graph.edges():
        if e[0] <= max_num_node and e[1] <= max_num_node:
            nx_graph.add_edge(e[0], e[1], weight=e[2])
    print(str(len(nx_graph.edges())) + " edges added to nx_graph: " + str(time.time() - start_time))

    node_color = []
    for n in nx_graph.nodes():
        node_color.append(sum([e[2] for e in instance.graph.outgoing_edges(n) if e[1] <= max_num_node]))
    print("Nodes color computed: " + str(time.time() - start_time))

    layout = nx.drawing.layout.kamada_kawai_layout(nx_graph) if is_WMD else nx.drawing.layout.circular_layout(nx_graph)
    print("Layout computed: " + str(time.time() - start_time))

    plt.figure(figsize=(10, 10))
    nx.draw_networkx(nx_graph,
                     pos=layout,
                     arrowstyle='-|>',
                     arrowsize=15,
                     with_labels=False,
                     node_color=node_color,
                     cmap="winter",
                     edge_color='darkslategrey')
    plt.axis('off')
    print("Figure generated: " + str(time.time() - start_time))
    plt.savefig(img_file_path)
    print("Finished: " + str(time.time() - start_time))
    plt.close('all')


def draw_order(instance, img_file_path):
    """ Generates the image file for an instance representing orders.

        :param instance: The instance to draw.
        :type instance: :class:`preflibtools.instances.preflibinstance.PreflibInstance`
        :param img_file_path: Path to which save the image.
        :type img_file_path: str or path
    """
    b = borda_scores(instance)
    plt.close('all')
    plt.figure(figsize=(10, 10))
    cmap = plt.get_cmap("winter")
    plt.bar(range(len(b)), list(b.values()), align='center',
            color=cmap(np.array(list(b.values())) / max(b.values())))
    plt.xticks([])
    plt.yticks([])
    plt.savefig(img_file_path)
    plt.close('all')