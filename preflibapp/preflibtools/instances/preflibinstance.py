""" This module describes the main class to deal with PrefLib instances..
"""

from .sampling import *

from copy import deepcopy
from os import path

import urllib


class PreflibInstance(object):
    """ This is the class representing a PrefLib instance. It basically contains the data and information
         written within a PrefLib file.

        :param file_path: The path to the file the instance is taken from. If a path is provided as a parameter,
            the file is immediately parsed and the instance populated accordingly.
        :type file_path: str, optional

        :ivar file_path: The path to the file the instance is taken from.
        :ivar file_name: The name of the file the instance is taken from.
        :ivar data_type: The data type of the instance. Whenever a function only applies to certain types of data
            (strict and complete orders for instance), we do so by checking this value.
        :ivar num_alternatives: The number of alternatives in the instance.
        :ivar alternatives_name: A dictionary mapping alternative (int) to their name (str).
        :ivar num_voters: The number of voters in the instance.
        :ivar sum_vote_count: The sum of the weights of the voters. In most cases, it is equal to the num_voters,
            but not if we have induced a relation like generating a pairwise graph from a set of linear orders
            for instance.
        :ivar num_unique_order: The number of unique orders in the instance.
        :ivar order_multiplicity: A dictionary mapping each order to the number of voters who submitted that order.
        :ivar orders: The list of all the distinct orders in the instance.
        :ivar graph: An instance of the :class:`preflibtools.instances.graph` for when the instance represents
            a graph.
    """

    def __init__(self, file_path=""):
        self.file_path = file_path
        self.file_name = ""
        self.data_type = ""
        self.num_alternatives = 0
        self.alternatives_name = {}
        self.num_voters = 0
        self.sum_vote_count = 0
        self.num_unique_order = 0
        self.order_multiplicity = {}
        self.orders = []
        self.graph = None

        # If a filePath is given as argument, we parse it immediately
        if len(file_path) > 0:
            self.parse_file(file_path)

    def parse_lines(self, lines):
        """ Parses the lines provided as argument. The parser to be used is deducted from the instance's value of
            data_type.

            :param lines: A list of string, each string being one line of the ``file'' to parse.
            :type lines: list
        """
        # Parsing the file based on the file extension
        if self.data_type in ["soc", "soi", "toc", "toi"]:
            self.parse_order(lines)
        elif self.data_type in ["tog", "mjg", "wmg", "pwg"]:
            self.parse_graph(lines)
        elif self.data_type == "wmd":
            self.parse_graph(lines, is_WMD=True)
        elif self.data_type in ["dat", "csv"]:
            pass
        else:
            raise SyntaxError("File extension " + str(self.data_type) + " is unknown to PrefLib instance. " +
                              "This file cannot be parsed.")

    def parse_file(self, filepath):
        """ Parses the file whose path is provided as argument and populates the PreflibInstance object accordingly.
            The parser to be used (whether the file describes a graph or an order for instance) is deduced based
            on the file extension.

            :param filepath: The path to the file to be parsed.
            :type filepath: str
        """

        # Populating basic properties of the instance
        self.file_path = filepath
        self.file_name = path.split(filepath)[1]
        self.data_type = path.splitext(filepath)[1][1:]

        # Read the file
        file = open(filepath, "r", encoding="utf-8")
        res = []
        lines = file.readlines()
        file.close()

        self.parse_lines(lines)

    def parse_str(self, string, data_type, file_name = ""):
        """ Parses the string provided as argument and populates the PreflibInstance object accordingly.
            The parser to be used (whether the file describes a graph or an order for instance) is deduced based
            on the file extension passed as argument.

            :param string: The string to parse.
            :type string: str
            :param data_type: The data type represented by the string.
            :type data_type: str
            :param file_name: The value to store in the file_name member of the instance. Default is the empty string.
            :type file_name: str
        """

        self.file_path = "parsed_from_string"
        self.file_name = file_name
        self.data_type = data_type

        self.parse_lines(string.splitlines())

    def parse_url(self, url):
        """ Parses the file located at the provided URL and populates the PreflibInstance object accordingly.
            The parser to be used (whether the file describes a graph or an order for instance) is deduced based
            on the file extension.

            :param url: The target URL.
            :type url: str
        """

        data = urllib.request.urlopen(url)
        lines = [line.decode("utf-8").strip() for line in data]
        data.close()

        self.file_path = url
        self.file_name = url.split('/')[-1].split('.')[0]
        self.data_type = url.split('.')[-1]

        self.parse_lines(lines)

    def write(self, filepath):
        """ Writes the instance to the file whose path is provided as argument. If the file path does not contain
            a file extension, is provided the data type of the instance is used. The function to call (whether 
            the instance describes a graph or an order for instance) is deduced based on the data type of the 
            instance.

            :param filepath: The path where to write the file.
            :type filepath: str
        """

        # Writing the instance based on the data type
        if self.data_type in ["soc", "soi", "toc", "toi"]:
            self.write_order(filepath)
        elif self.data_type in ["tog", "mjg", "wmg", "pwg"]:
            self.write_graph(filepath)
        elif self.data_type == "wmd":
            self.write_graph(filepath, is_WMD=True)
        elif self.data_type in ["dat", "csv"]:
            pass
        else:
            raise SyntaxError("File extension " + str(self.data_type) + " is unknown to PrefLib instance. " +
                              "This instance cannot be written.")

    def vote_map(self):
        """ Returns the instance described as a vote map, i.e., a dictionary whose keys are orders, mapping
            to the number of voters with the given order as their preferences. This format can be useful for some
            applications. It also ensures interoperability with the old preflibtools (vote maps were the main object).

            :return: A vote map representing the preferences in the instance.
            :rtype: dict of (tuples, int)
        """
        vote_map = {}
        for order in self.orders:
            vote_map[order] = self.order_multiplicity[order]
        return vote_map

    def full_profile(self):
        """ Returns a list containing all the orders appearing in the preferences, with each order appearing as
            many times as their multiplicity.

            :return: A list of preferences (lists of alternatives).
            :rtype: list
        """
        res = []
        for order in self.orders:
            res += [order] * self.order_multiplicity[order]
        return res

    def flatten_strict(self):
        """ Because strict orders are represented as orders with indifference classes of size 1, this function
            flattens them.

            :return: A list of tuples of preference order and multiplicity.
            :rtype: list
        """
        res = []
        for order in self.orders:
            if len(order) != self.num_alternatives:
                print("WARNING: You are flattening a non-strict order.")
            res.append((tuple(indif_class[0] for indif_class in order), self.order_multiplicity[order]))
        return res

    def infer_type_orders(self):
        """ Loops through the orders of the instance to infer whether the preferences strict and/or complete, assuming
            the instance represents orders.

            :return: The data type of the instance.
            :rtype: str 
        """
        strict = True
        complete = True
        tmp_type = "soc"
        for order in self.orders:
            if len(order) != self.num_alternatives:
                strict = False
                tmp_type = "toc"
            if len([alt for indif_class in order for alt in indif_class]) != self.num_alternatives:
                complete = False
                tmp_type = "soi"
            if not strict and not complete:
                return "toi"
        return tmp_type

    def append_order_list(self, orders):
        """ Appends a vote map to the instance. That function incorporates the new orders into the instance and
            updates the set of alternatives if needed.

            :param orders: A list of tuples of tuples, each tuple representing a preference order. 
            :type orders: list
        """
        alternatives = set(alt for order in orders for indif_class in order for alt in indif_class)
        for alt in alternatives:
            if alt not in self.alternatives_name:
                self.alternatives_name[alt] = "Alternative " + str(alt)
        self.num_alternatives = len(self.alternatives_name)

        self.num_voters += len(orders)
        self.sum_vote_count += len(orders)

        for order in orders:
            multiplicity = len([o for o in orders if o == order])
            if order in self.order_multiplicity:
                self.order_multiplicity[order] += multiplicity
            else:
                self.order_multiplicity[order] = multiplicity

        self.num_unique_order = len(self.order_multiplicity)
        self.orders += deepcopy(orders)

        self.data_type = self.infer_type_orders()

    def append_vote_map(self, vote_map):
        """ Appends a vote map to the instance. That function incorporates the new orders into the instance and
            updates the set of alternatives if needed.
            
            :param vote_map: A vote map representing preferences. A vote map is a dictionary whose keys represent
                orders (tuples of tuples of int) that are mapped to the number of voters with the given order as 
                their preferences. We re-map the orders to tuple of tuples to be sure we are dealing with the correct
                type.
            :type vote_map: dict of (tuple, int)
        """
        for ballot, multiplicity in vote_map.items():
            order = tuple(tuple(indif_class) for indif_class in ballot)
            if order not in self.orders:
                self.orders.append(order)
                self.order_multiplicity[order] = multiplicity
            else:
                self.order_multiplicity[order] += multiplicity
            self.num_voters += multiplicity
            self.sum_vote_count += multiplicity

            for indif_class in ballot:
                for alt in indif_class:
                    if alt not in self.alternatives_name:
                        self.alternatives_name[alt] = "Alternative " + str(alt)

        self.num_alternatives = len(self.alternatives_name)
        self.num_unique_order = len(self.order_multiplicity)

        self.data_type = self.infer_type_orders()

    def populate_IC(self, num_voters, num_alternatives):
        """ Populates the instance with a random profile of strict preferences taken from the impartial culture
            distribution. Uses :math:`preflibtools.instances.sampling.urnModel` for sampling.

            :param num_voters: Number of orders to sample.
            :type num_voters: int
            :param num_alternatives: Number of alternatives for the sampled orders.
            :type num_alternatives: int
        """
        self.append_vote_map(generate_IC(num_voters, list(range(num_alternatives))))

    def populate_IC_anon(self, num_voters, num_alternatives):
        """ Populates the instance with a random profile of strict preferences taken from the impartial anonymous
            culture distribution. Uses :class:`preflibtools.instances.sampling` for sampling.

            :param num_voters: Number of orders to sample.
            :type num_voters: int
            :param num_alternatives: Number of alternatives for the sampled orders.
            :type num_alternatives: int
        """
        self.append_vote_map(generate_IC_anon(num_voters, list(range(num_alternatives))))

    def populate_urn(self, num_voters, num_alternatives, replace):
        """ Populates the instance with a random profile of strict preferences taken from the urn distribution.
            Uses :class:`preflibtools.instances.sampling` for sampling.

            :param num_voters: Number of orders to sample.
            :type num_voters: int
            :param num_alternatives: Number of alternatives for the sampled orders.
            :type num_alternatives: int
            :param replace: The number of replacements for the urn model.
            :type replace: int
        """
        self.append_vote_map(generate_urn(num_voters, list(range(num_alternatives)), replace))

    def populate_mallows(self, num_voters, num_alternatives, mixture, dispersions, references):
        """ Populates the instance with a random profile of strict preferences taken from a mixture of Mallows'
            models. Uses :class:`preflibtools.instances.sampling` for sampling.

            :param num_voters: Number of orders to sample.
            :type num_voters: int
            :param num_alternatives: Number of alternatives for the sampled orders.
            :type num_alternatives: int
            :param mixture: A list of the weights of each element of the mixture.
            :type mixture: list of positive numbers
            :param dispersions: A list of the dispersion coefficient of each element of the mixture.
            :type dispersions: list of float
            :param references: A list of the reference orders for each element of the mixture.
            :type references: list of tuples of tuples of int
        """
        self.append_vote_map(generate_mallows(num_voters, num_alternatives, mixture, dispersions, references))

    def populate_mallows_mix(self, num_voters, num_alternatives, num_references):
        """ Populates the instance with a random profile of strict preferences taken from a mixture of Mallows'
            models for which reference points and dispersion coefficients are independently and identically 
            distributed. Uses :class:`preflibtools.instances.sampling` for sampling.

            :param num_voters: Number of orders to sample.
            :type num_voters: int
            :param num_alternatives: Number of alternatives for the sampled orders.
            :type num_alternatives: int
            :param num_references: Number of element
            :type num_references: int
        """
        self.append_vote_map(generate_mallows_mix(num_voters, list(range(num_alternatives)), num_references))

    def parse_order(self, lines):
        """ Parses the strings provided as argument, assuming that the latter describes an order.

            :param lines: A list of string, each string being one line of the ``file'' to parse.
            :type lines: list
        """

        # The first line gives us the number of alternatives, then comes the names of the alternatives
        self.num_alternatives = int(lines[0])
        for i in range(1, self.num_alternatives + 1):
            self.alternatives_name[i] = lines[i].split(",")[1].strip()

        # We've reached the description of the preferences. We start by some numbers...
        self.num_voters = int(lines[self.num_alternatives + 1].split(",")[0])
        self.sum_vote_count = int(lines[self.num_alternatives + 1].split(",")[1])
        self.num_unique_order = int(lines[self.num_alternatives + 1].split(",")[2])

        # ... and finally comes the preferences
        for l in lines[self.num_alternatives + 2:]:
            # The first element indicates the multiplicity of the order
            elements = l.strip().split(",")
            multiplicity = int(elements[0])

            # Then we deal with the rest
            in_braces = False
            order = []
            indif_class = []
            for w in elements[1:]:
                # If there is something in w
                if w != "{}" and len(w) > 0:
                    # If we are entering a series of ties (grouped by {})
                    if w.startswith("{"):
                        # If w also ends with a }, we remove it
                        if w.endswith("}"):
                            w = w[:-1]
                        in_braces = True
                        indif_class.append(int(w[1:]))  # The first element of w is {, so we go beyond that
                    # If we finished reading a series of ties (grouped by {})
                    elif w.endswith("}"):
                        in_braces = False
                        indif_class.append(int(w[:-1]))  # The first element of w is }, so we go beyond that
                        order.append(tuple(indif_class))
                        indif_class = []
                    # Otherwise, we are just reading numbers
                    else:
                        # If we are facing ties, we add in the indifference class
                        if in_braces:
                            if int(w) not in indif_class:
                                indif_class.append(int(w))
                        # Otherwise, we add the strict preference.
                        else:
                            if (int(w),) not in order:
                                order.append((int(w),))
            self.orders.append(tuple(order))
            self.order_multiplicity[tuple(order)] = multiplicity

    def parse_graph(self, lines, is_WMD=False):
        """ Parses the strings, assuming that the latter describes a graph.

            :param lines: A list of string, each string being one line of the ``file'' to parse.
            :type lines: list
            :param is_WMD: True if the graph to parse represents weighted matching data, default is False.
            :type is_WMD: bool
        """

        # For Weighted Matching Data, the meaning are not the same
        if is_WMD:
            self.num_alternatives = int(lines[0].strip().split(",")[0])
            self.num_voters = int(lines[0].strip().split(",")[1])
        else:
            self.num_alternatives = int(lines[0])
        for i in range(1, self.num_alternatives + 1):
            self.alternatives_name[i] = lines[i].split(",")[1].strip()
        if not is_WMD:
            self.num_voters = int(lines[self.num_alternatives + 1].split(",")[0])
            self.sum_vote_count = int(lines[self.num_alternatives + 1].split(",")[1])
            self.num_unique_order = int(lines[self.num_alternatives + 1].split(",")[2])
        # Skip the lines that describe the data
        graph_first_line = self.num_alternatives + 1 if is_WMD else self.num_alternatives + 2
        self.graph = Graph()
        for l in lines[graph_first_line:]:
            if is_WMD:
                (vertex1, vertex2, weight) = l.strip().split(",")
            else:
                (weight, vertex1, vertex2) = l.strip().split(",")
            weight = int(weight)
            vertex1 = int(vertex1)
            vertex2 = int(vertex2)
            self.graph.add_edge(vertex1, vertex2, weight)

    def write_order(self, filepath):
        """ Writes the instance into a file whose destination has been given as argument, assuming the instance
            represents an order. If no file extension is provided the data type of the instance is used.

            :param filepath: The destination where to write the instance.
            :type filepath: str
        """
        if len(path.splitext(filepath)[1]) == 0:
            filepath += str(self.data_type)
        file = open(filepath, "w", encoding="utf-8")
        # Writing number of alternatives and their names
        file.write(str(self.num_alternatives) + "\n")
        for alt, name in self.alternatives_name.items():
            file.write("{},{}\n".format(alt, name))
        # Writing the ballot counts
        file.write("{},{},{}\n".format(self.num_voters, self.sum_vote_count, self.num_unique_order))
        # Writing the actual ballots with their multiplicity
        for order in self.orders:
            order_str = ""
            for indif_class in order:
                if len(indif_class) == 1:
                    order_str += str(indif_class[0]) + ","
                else:
                    order_str += "{" + ",".join((str(alt) for alt in indif_class)) + "},"
            file.write("{},{}\n".format(self.order_multiplicity[order], order_str[:-1]))
        file.close()

    def write_graph(self, filepath, is_WMD=False):
        """ Writes the instance into a file whose destination has been given as argument, assuming the instance
            represents a graph. If no file extension is provided the data type of the instance is used.

            :param filepath: The destination where to write the instance.
            :type filepath: str
            :param is_WMD: True if the graph to parse represents weighted matching data, default is False.
            :type is_WMD: bool
        """
        if len(path.splitext(filepath)[1]) == 0:
            filepath += str(self.data_type)
        file = open(filepath, "w", encoding="utf-8")
        # Writing number of alternatives, or edges and nodes in the case of WMD
        if is_WMD:
            file.write("{},{}\n".format(self.num_alternatives, self.num_voters))
        else:
            file.write(str(self.num_alternatives) + "\n")
        # Writing alternative names
        for alt, name in self.alternatives_name.items():
            file.write("{},{}\n".format(alt, name))
        # Writing the ballot counts when not WMD
        if not is_WMD:
            file.write("{},{},{}\n".format(self.num_voters, self.sum_vote_count, self.num_unique_order))
        # Writing the actual graph
        nodes = sorted(list(self.graph.nodes()))
        for n in nodes:
            out_egdes = sorted(list(self.graph.outgoing_edges(n)), key=lambda x: x[1])
            for (vertex1, vertex2, weight) in out_egdes:
                if is_WMD:
                    file.write("{},{},{}\n".format(vertex1, vertex2, weight))
                else:
                    file.write("{},{},{}\n".format(weight, vertex1, vertex2))
        file.close()


class Graph(object):
    """ This class is used to represent (weighted) graphs.

        :ivar dict: The dictionary representing the graph mapping each node to its neighbourhood (set of nodes
            to which it is connected). A node can be of any hashable type.
        :ivar weight: The dictionary mapping every node to its weight.
    """

    def __init__(self):
        self.dict = dict()
        self.weight = dict()

    def neighbours(self, node):
        """ Returns all the neighbours of a given node.

            :param node: The node whose neighbours we want to know.

            :return: The set of the neighbours of the node.
            :rtype: set
        """
        return self.dict[node]

    def outgoing_edges(self, node):
        """ Returns all the edges leaving a given node.

            :param node: The node whose edges we want to get.

            :return: The set of the tuples (node, neighbour, edgeWeight) representing (weighted) edges.
            :rtype: set of tuples
        """
        return {(node, n, self.weight[(node, n)]) for n in self.dict[node]}

    def add_node(self, node):
        """ Adds a node to the graph if the node does not already exist.

            :param node: The node to add.
        """
        if node not in self.dict:
            self.dict[node] = set()

    def add_edge(self, node1, node2, weight):
        """ Adds an edge to the graph. If the nodes do not exist in the graph, those are also added.

            :param node1: The departure node of the edge.
            :param node2: The arrival node of the edge.
            :param weight: The weight of the edge.
        """
        self.add_node(node1)
        self.add_node(node2)
        self.dict[node1].add(node2)
        self.weight[(node1, node2)] = weight

    def edges(self):
        """ Returns the set of all the edges of the graph.

            :return: A set of tuples (node, neighbour, weight) representing (weighted) edges.
            :rtype: set of tuples
        """
        return {(n1, n2, self.weight[(n1, n2)]) for n1 in self.dict for n2 in self.dict[n1]}

    def nodes(self):
        """ Returns the set of all the nodes of the graph.

            :return: The set of all the nodes of the graph.
            :rtype: set
        """
        return self.dict.keys()

    def __str__(self):
        """ Returns the string used when printing the graph """
        res = "Graph with {} vertices and {} edges :\n".format(len(self.dict), len(self.edges()))
        for node in self.dict:
            res += str(node) + ": "
            for edge in self.outgoing_edges(node):
                res += str(edge) + " "
            res = res[:-1] + "\n"
        return res[:-1]
