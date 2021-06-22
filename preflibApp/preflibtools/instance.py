from .graph import Graph
from .drawing import *

from copy import deepcopy

class PreflibInstance(object):
	def __init__(self):
		self.fileName = ""
		self.dataType = None
		self.nbAlternatives = 0
		self.alternativesName = {}
		self.nbVoters = 0
		self.nbSumVoters = 0
		self.nbDifferentOrders = 0
		self.nbEachOrder = []
		self.orders = []
		self.graph = None

	# Parses the file name and call the correct function based on file extension
	def parse(self, fileName):
		self.dataType = fileName.split('.')[-1]
		if self.dataType in ["soc", "soi", "toc", "toi"]:
			self.parseWeakOrder(fileName)
		elif self.dataType in ["tog", "mjg", "wmg", "pwg"]:
			self.parseGraph(fileName)
		elif self.dataType == "wmd":
			self.parseGraph(fileName, isWMD = True)
		elif self.dataType in ["dat", "csv"]:
			pass
		else:
			raise SyntaxError("File extension is unknown to PrefLib instance. " +
				"This file cannot be parsed.")

	# Generate the image file based on file extension
	def draw(self, outFileName):
		if self.dataType in ["soc", "soi", "toc", "toi"]:
			drawOrder(self, outFileName)
		elif self.dataType in ["tog", "mjg", "wmg", "pwg"]:
			drawGraph(self, outFileName)
		elif self.dataType == "wmd":
			drawGraph(self, outFileName, isWMD = True)
		elif self.dataType in ["dat", "csv"]:
			pass
		else:
			raise SyntaxError("File extension is unknown to PrefLib instance. " +
				"This file cannot be parsed.")

	# Also parses strict orders but considers them as weak orders
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
				# If there is something in w
				if w != "{}" and len(w) > 0:
					# If we are entering a series of ties (grouped by {})
					if w.startswith("{"):
						if w.endswith("}"):
							w = w[:-1]
						inBraces = True
						weakPref.append(int(w[1:]) - 1)
					# If we finished reading a series of ties (grouped by {})
					elif w.endswith("}"):
						inBraces = False
						weakPref.append(int(w[:-1]) - 1)
						pref.append(deepcopy(weakPref))
						weakPref = []
					# Otherwise, we are just reading numbers
					else:
						# If we are in a serie of ties, we add in the equivalence class
						if inBraces:
							if int(w) - 1 not in weakPref:
								weakPref.append(int(w) - 1)
						# Otherwise, we add the strict preference.
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
		# For Weighted Matching Data, the meaning are not the same
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