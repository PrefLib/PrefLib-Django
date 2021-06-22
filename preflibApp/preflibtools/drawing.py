import matplotlib.pyplot as plt
import networkx as nx
import numpy as np

import time

# Draws the graph using networkx and matplotlib
def drawGraph(instance, imgFilePath, maxNumNode = 100, isWMD = False):
	print("Drawing: " + str(imgFilePath))
	startTime = time.time()
	plt.close('all')
	nxGraph = nx.DiGraph()
	nxGraph.add_nodes_from([n for n in instance.graph.dict if n <= maxNumNode])
	print(str(len(nxGraph.nodes())) + " nodes added to nxGraph: " + str(time.time() - startTime))
	for e in instance.graph.edges():
		if e[0] <= maxNumNode and e[1] <= maxNumNode:
			nxGraph.add_edge(e[0], e[1], weight = e[2])
	print(str(len(nxGraph.edges())) + " edges added to nxGraph: " + str(time.time() - startTime))

	node_color = []
	for n in nxGraph.nodes():
		node_color.append(sum([e[2] for e in instance.graph.outgoingEdges(n) if e[1] <= maxNumNode]))
	print("Nodes color computed: " + str(time.time() - startTime))

	layout = nx.drawing.layout.kamada_kawai_layout(nxGraph) if isWMD else nx.drawing.layout.circular_layout(nxGraph)
	print("Layout computed: " + str(time.time() - startTime))

	plt.figure(figsize = (10, 10))
	nx.draw_networkx(nxGraph,
		pos = layout,
		arrowstyle = '-|>',
		arrowsize = 15,
		with_labels = False,
		node_color = node_color,
		cmap = "winter",
		edge_color = 'darkslategrey')
	plt.axis('off')
	print("Figure generated: " + str(time.time() - startTime))
	plt.savefig(imgFilePath)
	print("Finished: " + str(time.time() - startTime))
	plt.close('all')

def bordaScores(instance):
	res = dict([])
	for order in instance.orders:
		i = instance.nbAlternatives
		for candSet in order:
			i -= len(candSet)
			for cand in candSet:
				if cand not in res:
					res[cand] = i
				else:
					res[cand] += i
	res = {key: value for key, value in sorted(res.items(), key = lambda x: x[0])}
	return res

def drawOrder(instance, imgFilePath):
	b = bordaScores(instance)
	plt.close('all')
	plt.figure(figsize = (10, 10))
	cmap = plt.get_cmap("winter")
	plt.bar(range(len(b)), list(b.values()), align = 'center', 
		color = cmap(np.array(list(b.values())) / max(b.values())))
	plt.xticks([])
	plt.yticks([])
	plt.savefig(imgFilePath)
	plt.close('all')