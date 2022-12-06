


import numpy as np
import json
import networkx as nx


#Function for BFS Traversal of the graph - O(V+E) Since every vertex and edge must be iterated over
def bfsTraversal(jsonData):

    data = json.loads(jsonData)
    
    g = nx.DiGraph()

    elist = []
    ##Add all edges in data to the graph
    for edge in data["links"]:
        
        source = str(edge["source"])
        target = str(edge["target"])
        
        elist.append((source, target))

    
    ##Add edges
    g.add_edges_from(elist)

    ##Find the Breadth First search order
    travRes = nx.edge_bfs(g, source=data["nodes"][0]["id"])

    return travRes


#Function for DFS Traversal of the graph - O(V+E) since every vertex and edge must be iterated over. 
def dfsTraversal(jsonData):

    data = json.loads(jsonData)

    g = nx.DiGraph()

    elist = []

    for edge in data["links"]:
        
        source = str(edge["source"])
        target = str(edge["target"])

        elist.append((source, target))

        
    g.add_edges_from(elist)

    travRes = nx.edge_dfs(g, source=data["nodes"][0]["id"])

    return travRes