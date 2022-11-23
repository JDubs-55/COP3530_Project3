

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import oracledb as db

import os


def main():
    print("Hello World")


class Graph(object):
    def __init__(self, graph_dict=None):

        if graph_dict is None:
            graph_dict = {}
        self.__graph_dict = graph_dict

    def vertices(self):
        return list(self.__graph_dict.keys())

    def edges(self):
        return self.__generate_edges()

    def add_vertex(self, vertex):
        if vertex not in self.__graph_dict:
            self.__graph_dict[vertex] = []

    def add_edge(self, edge):
        edge = set(edge)
        (vertex1, vertex2) = tuple(edge)
        if vertex1 in self.__graph_dict:
            self.__graph_dict[vertex1].append(vertex2)
        else:
            self.__graph_dict[vertex1] = [vertex2]

    def __generate_edges(self):
        edges = []
        for vertex in self.__graph_dict:
            for neighbour in self.__graph_dict[vertex]:
                if {neighbour, vertex} not in edges:
                    edges.append({vertex, neighbour})
        return edges

    def find_isolated_vertices(self):
        graph = self.__graph_dict
        isolated = []
        for vertex in graph:
            if not graph[vertex]:
                isolated += [vertex]
        return isolated

    def __str__(self):
        res = "vertices: "
        for k in self.__graph_dict:
            res += str(k) + " "
        res += "    edges: "

        for edge in self.__generate_edges():
            res += str(edge) + " "
        return res

    def find_path(self, start_vertex, end_vertex, path=None):
        graph = self.__graph_dict
        if path is None:
            path = []
        path = path + [start_vertex]
        if start_vertex == end_vertex:
            return path
        if start_vertex not in graph:
            return None
        for vertex in graph[start_vertex]:
            if vertex not in path:
                extended_path = self.find_path(vertex,
                                               end_vertex,
                                               path)
                if extended_path:
                    return extended_path
        return None

    def find_all_paths(self, start_vertex, end_vertex, path=None):
        graph = self.__graph_dict
        if path is None:
            path = []
        path = path + [start_vertex]
        if start_vertex == end_vertex:
            return [path]
        if start_vertex not in graph:
            return []
        paths = []
        for vertex in graph[start_vertex]:
            if vertex not in path:
                extended_paths = self.find_all_paths(vertex,
                                                     end_vertex,
                                                     path)
                for p in extended_paths:
                    paths.append(p)
        return paths

    def find_shortest_path(self, start_vertex, end_vertex, path=None):
        if path is None:
            path = []
        graph = self.__graph_dict
        path = path + [start_vertex]
        if start_vertex == end_vertex:
            return path
        if start_vertex not in graph:
            return None
        shortest = None
        for vertex in graph[start_vertex]:
            if vertex not in path:
                newpath = self.find_shortest_path(vertex,
                                                  end_vertex,
                                                  path)
                if newpath:
                    if not shortest or len(newpath) < len(shortest):
                        shortest = newpath
        return shortest

    def find_longest_path(self, start_vertex, end_vertex, path=None):
        if path is None:
            path = []
        graph = self.__graph_dict
        path = path + [start_vertex]
        if start_vertex == end_vertex:
            return path
        if start_vertex not in graph:
            return None
        longest = None
        for vertex in graph[start_vertex]:
            if vertex not in path:
                newpath = self.find_longest_path(vertex,
                                                 end_vertex,
                                                 path)
                if newpath:
                    if not longest or len(newpath) > len(longest):
                        longest = newpath
        return longest

    def find_all_paths_with_length(self, start_vertex, end_vertex, path=None, length=0):
        if path is None:
            path = []
        graph = self.__graph_dict
        path = path + [start_vertex]
        if start_vertex == end_vertex:
            if length == len(path):
                return [path]
            else:
                return []
        if start_vertex not in graph:
            return []
        paths = []
        for vertex in graph[start_vertex]:
            if vertex not in path:
                extended_paths = self.find_all_paths_with_length(vertex,
                                                                 end_vertex,
                                                                 path, length)
                for p in extended_paths:
                    paths.append(p)
        return paths

    def find_all_paths_with_length_less_than(self, start_vertex, end_vertex, path=None, length=0):
        if path is None:
            path = []
        graph = self.__graph_dict
        path = path + [start_vertex]
        if start_vertex == end_vertex:
            if length >= len(path):
                return [path]
            else:
                return []
        if start_vertex not in graph:
            return []
        paths = []
        for vertex in graph[start_vertex]:
            if vertex not in path:
                extended_paths = self.find_all_paths_with_length_less_than(vertex,
                                                                           end_vertex,
                                                                           path, length)
                for p in extended_paths:
                    paths.append(p)
        return paths

    def getWeight(self, node):
        return self.__graph_dict[node][0]

    def __iter__(self):
        self._iter_obj = iter(self._graph_dict)
        return self._iter_obj

    def __next__(self):
        return next(self.__graph_dict)

    def __getitem__(self, item):
        return self.__graph_dict[item]

    def __setitem__(self, key, value):
        self.__graph_dict[key] = value

    def __delitem__(self, key):
        del self.__graph_dict[key]

    def __len__(self):
        return len(self.__graph_dict)


class Edges:
    def __init__(self, u, v, w):
        self.__graph_dict = None
        self.u = u
        self.v = v
        self.w = w

    def __lt__(self, other):
        return self.w < other.w

    def __str__(self):
        return str(self.u) + " - " + str(self.v) + " : " + str(self.w)

    def __repr__(self):
        return self.__str__()

    def __eq__(self, other):
        return self.u == other.u and self.v == other.v and self.w == other.w

    def __hash__(self):
        return hash(self.__str__())

    def find_path(self, start_vertex, end_vertex, path=None):
        if path is None:
            path = []
        graph = self.__graph_dict
        path = path + [start_vertex]
        if start_vertex == end_vertex:
            return path
        if start_vertex not in graph:
            return None
        for vertex in graph[start_vertex]:
            if vertex not in path:
                extended_path = self.find_path(vertex,
                                               end_vertex,
                                               path)
                if extended_path:
                    return extended_path
        return None
