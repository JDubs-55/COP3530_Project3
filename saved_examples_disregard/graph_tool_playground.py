import pandas as pd
import neo4j
import py2neo
import numpy as np
from gi.overrides import Gtk, Gdk, GObject, GLib
from graph_tool.all import *

df = pd.read_csv('NewGraphData.csv')
# print(df.head(5))
R = Graph()
R.vertex_properties['reporter'] = R.new_vertex_property("string")
R.vertex_properties['partner'] = R.new_vertex_property("string")
R.vertex_properties['product'] = R.new_vertex_property("string")
R.vertex_properties['trade'] = R.new_vertex_property("string")
R.vertex_properties['year1988'] = R.new_vertex_property("float")
R.vertex_properties['year2013'] = R.new_vertex_property("float")
R.vertex_properties['differences'] = R.new_vertex_property("float")

reporter = R.add_vertex(10)
for v in R.get_vertices()[0:10]:
    R.vp['reporter'][v] = df['REPORTERNAME'][v]

partner = R.add_vertex(145)
for v in R.get_vertices()[10:155]:
    R.vp['partner'][v] = df['PARTNERNAME'][v]

product = R.add_vertex(340)
for v in R.get_vertices()[155:495]:
    R.vp['product'][v] = df['PRODUCTDESCRIPTION'][v]
    R.vp['trade'][v] = df['TRADEFLOW'][v]

year = R.add_vertex(62605)
for v in R.get_vertices()[495:62600]:
    R.vp['year1988'][v] = df['1988'][v]
    R.vp['year2013'][v] = df['2013'][v]

trade = R.add_vertex(1)
for v in R.get_vertices()[62600:62601]:
    R.vp['trade'][v] = df['TRADEFLOW'][v]

R.vp['differences'][v] = df['2013'][v] - df['1988'][v]

for s, t in zip(reporter, partner):
    R.add_edge(s, t)

for s, t in zip(product, partner):
    R.add_edge(s, t)

for s, t in zip(year, product):
    R.add_edge(s, t)


for e in bfs_iterator(R):
    print(reporter, product, year, partner)
    print(e.source(), "->", e.target())



#Version 2
edge_list = []

g = load_graph_from_csv('NewGraphData.csv', directed=True, hashed=True, csv_options={"delimiter": ","},
                        ecols=[1, 3, 4, 6, 7, 8, 9])

g.vertex_properties['reporter'] = g.new_vertex_property("string")
g.vertex_properties['partner'] = g.new_vertex_property("string")
g.vertex_properties['product'] = g.new_vertex_property("string")
g.vertex_properties['trade'] = g.new_vertex_property("string")
g.vertex_properties['year1988'] = g.new_vertex_property("float")
g.vertex_properties['year2013'] = g.new_vertex_property("float")
g.vertex_properties['differences'] = g.new_vertex_property("float")

for e in bfs_iterator(g):
    print(reporter, partner, product, year, trade)
    print(e.source(), "->", e.target())


graph_tool.draw.graph_draw(g, vertex_text=g.vp['reporter'], vertex_font_size=18, output_size=(2000, 2000), output="graph.png")
graph_tool.draw.graph_draw(R, vertex_text=R.vp['reporter'], vertex_font_size=18, output_size=(2000, 2000), output="graphVERSION1.png")
# props = g.add_edge_list(df[['1988', '2013', 'Difference']].values, hashed=True)
