import cx_Oracle
import networkx as nx
import matplotlib.pyplot as plt
from pyvis.network import Network
from config import config

def getData():

    G = nx.Graph()
    try: 
            con = cx_Oracle.connect(user=config["db"]["username"], password=config["db"]["password"], dsn="oracle.cise.ufl.edu:1521/orcl", encoding="UTF-8")

            cur = con.cursor()

            cur.execute("WITH Ordered as (\
                            SELECT ReporterISO3, PartnerISO3, TradeValue,\
                            ROW_NUMBER() OVER(PARTITION BY ReporterISO3 ORDER BY TradeValue DESC) AS row_number\
                            FROM (\
                                SELECT * \
                                    FROM \"JWELLER\".Project3SampleData \
                                    WHERE PRODUCTCODE = 1 \
                                        AND TRADEFLOWNAME = 'Gross Imp.' \
                                        AND ReporterISO3 != 'All' \
                                        AND PartnerISO3 != 'All' \
                            )\
                        )\
                        SELECT *\
                        FROM Ordered\
                        WHERE row_number<6")

            rows = cur.fetchall()

            #This is unnecessary for inserting nodes, can just use insert edge. 
            nodes = []
            for row in rows:
                nodes.append(row[0])
                nodes.append(row[1])

            nodes = set(nodes)

            edges = []
            for row in rows:
                edges.append((row[0], row[1]))

            edges = set(edges)
            cleaned_edges = []
            count=0

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

            nt = Network('500px', '500px')
            # populates the nodes and edges data structures
            nt.from_nx(G)
            nt.show('nx.html')

    except cx_Oracle.DatabaseError as e:

        print("Something happened")


    finally:
        if cur:
            cur.close()
        if con:
            con.close()