from django.core.management.base import BaseCommand
from django.contrib.staticfiles import finders
from django.db.models import Max
from django.core import management
from pysat.solvers import Glucose3
from datetime import datetime
from django.apps import apps
from copy import deepcopy

import matplotlib.pyplot as plt
import networkx as nx
import numpy as np

import traceback
import itertools
import time
import os

class Command(BaseCommand):
	help = "Update the metadata of the data file"

	def add_arguments(self, parser):
		parser.add_argument('--dataset', nargs = '*', type = str)

	def handle(self, *args, **options):
		dataDir = finders.find("data")
		if not dataDir:
			print("The folder data was not found, nothing has been done.")
			return
		lock = open(os.path.join(dataDir, "metadata.lock"), "w")
		lock.close()

		try:
			Log = apps.get_model("preflibApp", "Log")
			newLogNum = Log.objects.filter(logType = "metadata").aggregate(Max('logNum'))['logNum__max']
			if newLogNum == None:
				newLogNum = 0
			else:
				newLogNum += 1

			DataFile = apps.get_model("preflibApp", "DataFile")
			DataProp = apps.get_model("preflibApp", "DataProp")

			try:
				os.makedirs(tmpDir)
			except Exception as e:
				pass

			print(options)

			if options["dataset"] == None:
				datafiles = DataFile.objects.all().order_by("fileName")
			else:
				datafiles = DataFile.objects.filter(dataPatch__dataSet__abbreviation__in = options["dataset"]).order_by("fileName")

			log = ["<h4> Updating the metadata #" + str(newLogNum) + " - " + str(datetime.now()) + "</h4>\n<p><ul>"]
			startTime = time.time()
			for dataFile in datafiles:
				print("\nData file " + str(dataFile.fileName) + "...")
				log.append("\n\t<li>Data file " + str(dataFile.fileName) + "... ")
				self.updateDataProp(dataFile, DataProp)
				log.append(" ... done.</li>\n")
					
			log.append("\n<p>Regeneration of the zip files successfully completed in ") 
			log.append(str((time.time() - startTime) / 60) + " minutes</p>\n")

			print("Finished, collecting statics")
			management.call_command("collectstatic", no_input = False)
		except Exception as e:
			log.append("\n</ul>\n<p><strong>" + str(e) + "<br>\n" + str(traceback.format_exc()) + "</strong></p>")
			print(traceback.format_exc())
			print("Exception " + str(e))
		finally:
			os.remove(os.path.join(dataDir, "metadata.lock"))
			Log.objects.create(
				log = ''.join(log),
				logType = "metadata", 
				logNum = newLogNum,
				publicationDate = datetime.now())

	def updateDataProp(self, dataFile, DataProp):
		dataSet = dataFile.dataPatch.dataSet
		folder = finders.find(os.path.join("data", dataSet.extension, dataSet.abbreviation))
		prefLibInst = PreflibInstance()
		if dataFile.dataType in ["soc", "soi", "toc", "toi"]:
			prefLibInst.parseWeakOrder(os.path.join(folder, dataFile.fileName))
			prefLibInst.drawOrder(os.path.join(folder, 'img', dataFile.fileName.replace('.', '_') + '.png'))
			os.system("convert " + os.path.join(folder, 'img', dataFile.fileName.replace('.', '_') + '.png') + 
				" -trim " + os.path.join(folder, 'img', dataFile.fileName.replace('.', '_') + '.png'))
			DataProp.objects.update_or_create(
				dataFile = dataFile,
				defaults = {
					"image": dataFile.fileName.replace('.', '_') + '.png',
					"nbAlternatives": prefLibInst.nbAlternatives,
					"nbVoters": prefLibInst.nbVoters,
					"nbSumVoters": prefLibInst.nbSumVoters,
					"nbDifferentOrders": prefLibInst.nbDifferentOrders,
					"largestBallot": prefLibInst.largestBallot(),
					"smallestBallot": prefLibInst.smallestBallot(),
					"maxNbIndif": prefLibInst.maxNbIndif(),
					"minNbIndif": prefLibInst.minNbIndif(),
					"largestIndif": prefLibInst.largestIndif(),
					"smallestIndif": prefLibInst.smallestIndif(),
					"isApproval": prefLibInst.isApproval(),
					"isStrict": prefLibInst.isStrict(),
					"isComplete": prefLibInst.isComplete(),
					"isSinglePeaked": prefLibInst.isSP() if dataFile.dataType in ["soc"] else None,
					"isSingleCrossed": prefLibInst.isSC() if dataFile.dataType in ["soc"] else None})
		elif dataFile.dataType in ["tog", "mjg", "wmg", "pwg"]:
			prefLibInst.parseGraph(os.path.join(folder, dataFile.fileName))
			prefLibInst.graph.draw(os.path.join(folder, 'img', dataFile.fileName.replace('.', '_') + '.png'))
			os.system("convert " + os.path.join(folder, 'img', dataFile.fileName.replace('.', '_') + '.png') + 
				" -trim " + os.path.join(folder, 'img', dataFile.fileName.replace('.', '_') + '.png'))
			DataProp.objects.update_or_create(
				dataFile = dataFile,
				defaults = {
					"image": dataFile.fileName.replace('.', '_') + '.png',
					"nbAlternatives": prefLibInst.nbAlternatives,
					"nbVoters": prefLibInst.nbVoters,
					"nbSumVoters": prefLibInst.nbSumVoters,
					"nbDifferentOrders": prefLibInst.nbDifferentOrders,
					"hasCondorcet": prefLibInst.graph.hasCondorcet(dataFile.dataType)})
		elif dataFile.dataType == "wmd":
			prefLibInst.parseGraph(os.path.join(folder, dataFile.fileName), isWMD = True)
			prefLibInst.graph.draw(os.path.join(folder, 'img', dataFile.fileName.replace('.', '_') + '.png'), isWMD = True)
			os.system("convert " + os.path.join(folder, 'img', dataFile.fileName.replace('.', '_') + '.png') + 
				" -trim " + os.path.join(folder, 'img', dataFile.fileName.replace('.', '_') + '.png'))
			DataProp.objects.update_or_create(
				dataFile = dataFile,
				defaults = {
					"image": dataFile.fileName.replace('.', '_') + '.png',
					"nbAlternatives": prefLibInst.nbAlternatives,
					"nbVoters": prefLibInst.nbVoters,
					"isSinglePeaked": None})
		elif dataFile.dataType in ["dat", "csv"]:
			file = open(os.path.join(folder, dataFile.fileName))
			lines = file.readlines()
			DataProp.objects.update_or_create(
				dataFile = dataFile,
				defaults = {
					"nbVoters": len(lines),
					"text": ("".join(lines[:10]))
				})
			file.close()

class PreflibInstance(object):
	def __init__(self):
		self.fileName = ""
		self.nbAlternatives = 0
		self.alternativesName = {}
		self.nbVoters = 0
		self.nbSumVoters = 0
		self.nbDifferentOrders = 0
		self.nbEachOrder = []
		self.orders = []
		self.graph = None

	def parseWeakOrder(self, fileName):
		self.fileName = fileName
		file = open(self.fileName, "r", encoding="utf-8")
		res = []
		lines = file.readlines()
		self.nbAlternatives = int(lines[0])
		for i in range(1, self.nbAlternatives + 1):
			self.alternativesName[i] = lines[i].split(",")[1].strip()
		self.nbVoters = int(lines[self.nbAlternatives + 1].split(",")[0])
		self.nbSumVoters = int(lines[self.nbAlternatives + 1].split(",")[1])
		self.nbDifferentOrders = int(lines[self.nbAlternatives + 1].split(",")[2])
		# Skip the lines that describes the data
		for l in lines[self.nbAlternatives + 2:]:
			pref = []
			weights = l.strip().split(",")
			# Skip the first value
			self.nbEachOrder.append(int(weights[0]))
			inBraces = False
			weakPref = []
			for w in weights[1:]:
				if w != "{}" and len(w) > 0:
					if w.startswith("{"):
						if w.endswith("}"):
							w = w[:-1]
						inBraces = True
						weakPref.append(int(w[1:]) - 1)
					elif w.endswith("}"):
						inBraces = False
						weakPref.append(int(w[:-1]) - 1)
						pref.append(deepcopy(weakPref))
						weakPref = []
					else:
						if inBraces:
							if int(w) - 1 not in weakPref:
								weakPref.append(int(w) - 1)
						else:
							if [int(w) - 1] not in pref:
								pref.append([int(w) - 1])
			self.orders.append(pref)
		file.close()

	def parseGraph(self, fileName, isWMD = False):
		self.fileName = fileName
		file = open(self.fileName, "r", encoding="utf-8")
		res = []
		lines = file.readlines()
		if isWMD:
			self.nbAlternatives = int(lines[0].strip().split(",")[0])
			self.nbVoters = int(lines[0].strip().split(",")[1])
		else:
			self.nbAlternatives = int(lines[0])
		for i in range(1, self.nbAlternatives + 1):
			self.alternativesName[i] = lines[i].split(",")[1].strip()
		if not isWMD:
			self.nbVoters = int(lines[self.nbAlternatives + 1].split(",")[0])
			self.nbSumVoters = int(lines[self.nbAlternatives + 1].split(",")[1])
			self.nbDifferentOrders = int(lines[self.nbAlternatives + 1].split(",")[2])
		# Skip the lines that describes the data
		graphFirstLine = self.nbAlternatives + 1 if isWMD else self.nbAlternatives + 2
		self.graph = Graph()
		for l in lines[graphFirstLine:]:
			if isWMD:
				(vertex1, vertex2, weight) = l.strip().split(",")
			else:
				(weight, vertex1, vertex2) = l.strip().split(",")
			weight = int(weight)
			vertex1 = int(vertex1)
			vertex2 = int(vertex2)
			self.graph.addEdge(vertex1, vertex2, weight)
			if isWMD:
				self.graph.addEdge(vertex2, vertex1, weight)

		file.close()

	def bordaScores(self):
		res = dict([])
		for order in self.orders:
			i = self.nbAlternatives
			for candSet in order:
				i -= len(candSet)
				for cand in candSet:
					if cand not in res:
						res[cand] = i
					else:
						res[cand] += i
		res = {key: value for key, value in sorted(res.items(), key = lambda x: x[0])}
		return res

	def drawOrder(self, imgFilePath):
		b = self.bordaScores()
		plt.close('all')
		plt.figure(figsize = (10, 10))
		cmap = plt.get_cmap("winter")
		plt.bar(range(len(b)), list(b.values()), align = 'center', 
			color = cmap(np.array(list(b.values())) / max(b.values())))
		plt.xticks([])
		plt.yticks([])
		plt.savefig(imgFilePath, bbox_inches='tight')

	def largestBallot(self):
		return max([sum([len(p) for p in o]) for o in self.orders])

	def smallestBallot(self):
		return min([sum([len(p) for p in o]) for o in self.orders])

	def maxNbIndif(self):
		return max([len([p for p in o if len(p) > 1]) for o in self.orders] + [0])

	def minNbIndif(self):
		return min([len([p for p in o if len(p) > 1]) for o in self.orders] + [0])

	def largestIndif(self):
		return max([len(p) for o in self.orders for p in o if len(p) > 1] + [0])

	def smallestIndif(self):
		return min([len(p) for o in self.orders for p in o if len(p) > 1] + [0])

	def isApproval(self):
		m = max([len(o) for o in self.orders])
		if m == 1:
			return True
		elif m == 2:
			return self.isComplete()
		else:
			return False

	def isStrict(self):
		return self.largestIndif() == 0

	def isComplete(self):
		return self.smallestBallot() == self.nbAlternatives

	# Test if a given profile is single peaked using algorithm in Bartholdi and Trick (1986)
	# by first constructing the correct matrix and second using a SAT solver to check whether
	# the matrix has the consecutive ones property.
	# The SAT solver code has been taken from: Zack Fitzsimmons (zfitzsim@holycross.edu) and
	# Martin Lackner (lackner@dbai.tuwien.ac.at)
	def isSP(self):
		print("Testing single-peaked with {} alternatives and {} agents".format(self.nbAlternatives, self.nbVoters))
		def leftof(x, y):
			return x * num_cols + y + 1

		matrix = np.zeros((len(self.orders) * (len(self.orders[0]) - 1), len(self.orders[0])))
		for i in range(len(self.orders)):
			order = self.orders[i]
			for c in range(len(order)):
				matrix[i * (len(order) - 1) + order.index([c]): i * (len(order) - 1) + len(order) - 1, c] = 1

		STEP = 5

		g = Glucose3()
		num_rows = len(matrix)
		num_cols = len(matrix[0])
		if num_cols <= 10:
			cols = range(num_cols)
		else:
			cols = range(10)
		while True:
			# transitivity
			for x, y, z in itertools.combinations(cols, 3):
				# leftof(x,y) and leftof(y,z) imples leftof(x,z) =
				# not leftof(x,y) or not leftof(y,z) or leftof(x,z) =
				g.add_clause([-leftof(x, y), -leftof(y, z), leftof(x, z)])
			# totality
			for x, y in itertools.combinations(cols, 2):
				g.add_clause([-leftof(x, y), -leftof(y, x)])
				g.add_clause([leftof(x, y), leftof(y, x)])
			constraints = set()
			for i in range(num_rows):
				ones = []
				zeros = []
				for j in cols:
					if matrix[i][j] == 1:
						ones.append(j)
					if matrix[i][j] == 0:
						zeros.append(j)
				for x, y in itertools.combinations(ones, 2):
					for z in zeros:
						# NOT(leftof(x,z) and leftof(z,y)) =
						constraints.add((-leftof(x, z), -leftof(z, y)))
						# NOT(leftof(y,z) and leftof(z,x)) =
						constraints.add((-leftof(y, z), -leftof(z, x)))
			for c in constraints:
				g.add_clause(c)

			if not g.solve():
				return False
			if len(cols) == num_cols:
				break
			cols = range(min(num_cols, len(cols)+STEP))

		pos = [0] * len(cols)
		model = g.get_model()
		for x in cols:
			for y in cols:
				if leftof(x, y) in model:
					pos[x] += 1
		return [a[1] for a in sorted(zip(pos, cols), reverse = True)]

	def isSC(self):
		print("Testing single-crossed with {} alternatives and {} agents".format(self.nbAlternatives, self.nbVoters))
		def prefers(a, b, o):
			return o.index(a) < o.index(b)

		def conflictSet(o1, o2):
			res = set([])
			for i in range(len(o1)):
				for j in range(i + 1, len(o1)):
					if ((prefers(o1[i], o1[j], o1) and prefers(o1[j], o1[i], o2)) or 
						(prefers(o1[j], o1[i], o1) and prefers(o1[i], o1[j], o2))):
						res.add((min(o1[i][0], o1[j][0]), max(o1[i][0], o1[j][0])))
			return res

		def isSCwithFirst(i, profile):
			for j in range(len(profile)):
				for k in range(len(profile)):
					conflictij = conflictSet(profile[i], profile[j])
					conflictik = conflictSet(profile[i], profile[k])
					if not (conflictij.issubset(conflictik) or conflictik.issubset(conflictij)):
						return False
			return True

		for i in range(len(self.orders)):
			if isSCwithFirst(i, self.orders):
				return True
		return False

class Graph(object):
	def __init__(self):
		self.dict = dict()
		self.weight = dict()

	# Returns the neighbours of a given node
	def neighbours(self, node):
		return self.dict[node]

	# Returns the list of all outgoing edges from a node
	def outgoingEdges(self, node):
		return {(node, n, self.weight[(node, n)]) for n in self.dict[node]}

	# Adds a node to the graph
	def addNode(self, node):
		if node not in self.dict:
			self.dict[node] = set([])

	# Adds an edge to the graph, and the nodes if they do not exist
	def addEdge(self, node1, node2, weight):
		self.addNode(node1)
		self.addNode(node2)
		self.dict[node1].add(node2)
		self.weight[(node1, node2)] = weight

	def edges(self):
		return {(n1, n2, self.weight[(n1, n2)]) for n1 in self.dict for n2 in self.dict[n1]}

	def nodes(self):
		return self.dict.keys()

	def hasCondorcet(self, dataType):
		print("Testing Condorcet with {} nodes".format(len(self.nodes())))
		if dataType in ["tog", "wmg", "mjg"]:
			for n in self.dict:
				if len(self.neighbours(n)) == len(self.dict) - 1:
					return True
			return False
		if dataType == "pwg":
			for n in self.dict:
				canBeCondorcet = True
				for m in self.dict:
					if n != m:
						if (n, m) in self.weight and (m, n) in self.weight:
							if self.weight[(n, m)] < self.weight[(m, n)]:
								canBeCondorcet = False
						else:
							canBeCondorcet = False
				if canBeCondorcet:
					return True
			return False

	# Draws the graph using networkx and matplotlib
	def draw(self, imgFilePath, maxNumNode = 100, isWMD = False):
		plt.close('all')
		nxGraph = nx.DiGraph()
		nxGraph.add_nodes_from([n for n in self.dict if n <= maxNumNode])
		for e in self.edges():
			if e[0] <= maxNumNode and e[1] <= maxNumNode:
				nxGraph.add_edge(e[0], e[1], weight = e[2])

		node_color = []
		for n in nxGraph.nodes():
			node_color.append(sum([e[2] for e in self.edges() if e[0] == n and e[1] <= maxNumNode]))

		plt.figure(figsize = (10, 10))
		nx.draw_networkx(nxGraph,
			pos = nx.drawing.layout.kamada_kawai_layout(nxGraph) if isWMD else nx.drawing.layout.circular_layout(nxGraph),
			arrowstyle = '-|>', 
			arrowsize = 15, 
			with_labels = False,
			node_color = node_color, 
			cmap = "winter",
			edge_color = 'darkslategrey')
		plt.axis('off')
		plt.savefig(imgFilePath, bbox_inches='tight')

	# Returns the string used when printing the graph
	def __str__(self):
		res = "Graph with {} vertices and {} edges :\n".format(len(self.dict), len(self.edges()))
		for node in self.dict:
			res += str(node) + ": "
			for edge in self.outgoingEdges(node):
				res += str(edge) + " "
			res = res[:-1] + "\n"
		return res[:-1]