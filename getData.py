import cx_Oracle
import networkx as nx
import matplotlib.pyplot as plt
from config import config

def getData():

    G = nx.Graph()
    try: 
            con = cx_Oracle.connect(user=config["db"]["username"], password=config["db"]["password"], dsn="oracle.cise.ufl.edu:1521/orcl", encoding="UTF-8")

            cur = con.cursor()

            cur.execute("SELECT * FROM JWELLER.Project3SampleData sd WHERE sd.TRADEFLOWNAME = \'Gross Exp.\' AND sd.PRODUCTCODE=4")
            rows = cur.fetchall()

            #This is unnecessary for inserting nodes, can just use insert edge. 
            nodes = []
            for row in rows:
                nodes.append(row[1])
                nodes.append(row[3])

            nodes = set(nodes)


            edges = []
            for row in rows:
                edges.append((row[1], row[3]))

            edges = set(edges)
            cleaned_edges = []
            for edge in edges:
                if (edge[0]!="All" and edge[1]!="All"):
                    cleaned_edges.append(edge)

            for item in cleaned_edges:        
                G.add_edge(item[0], item[1])

            print("Node Count: " + str(len(nodes)))
            print("Edge Count: " + str(len(edges)))
            print("Cleaned Edges Count: " + str(len(cleaned_edges)))
            
            options = {
                'node_color': 'black',
                'node_size': 50,
                'width': 0.5,
                'font_weight': 'bold',
                'with_labels': False,

            }

            nx.draw_kamada_kawai(G, **options)
            plt.savefig("path.png")
            print("Success")

    except cx_Oracle.DatabaseError as e:

        print("Something happened")


    finally:
        if cur:
            cur.close()
        if con:
            con.close()