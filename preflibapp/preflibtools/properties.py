from pysat.solvers import Glucose3

import numpy as np

import itertools

def hasCondorcet(instance):
	if instance.data_type in ["tog", "wmg", "mjg"]:
		for n in instance.graph.dict:
			if len(instance.graph.neighbours(n)) == len(instance.graph.dict) - 1:
				return True
		return False
	if instance.data_type == "pwg":
		for n in instance.graph.dict:
			canBeCondorcet = True
			for m in instance.graph.dict:
				if n != m:
					if (n, m) in instance.graph.weight and (m, n) in instance.graph.weight:
						if instance.graph.weight[(n, m)] < instance.graph.weight[(m, n)]:
							canBeCondorcet = False
					else:
						canBeCondorcet = False
			if canBeCondorcet:
				return True
		return False

def nbAlternatives(instance):
	return instance.nbAlternatives

def nbVoters(instance):
	return instance.nbVoters
	
def nbSumVoters(instance):
	return instance.nbSumVoters

def nbDifferentOrders(instance):
	return instance.nbDifferentOrders
	
def largestBallot(instance):
	return max([sum([len(p) for p in o]) for o in instance.orders])

def smallestBallot(instance):
	return min([sum([len(p) for p in o]) for o in instance.orders])

def maxNbIndif(instance):
	return max([len([p for p in o if len(p) > 1]) for o in instance.orders] + [0])

def minNbIndif(instance):
	return min([len([p for p in o if len(p) > 1]) for o in instance.orders] + [instance.nbAlternatives])

def largestIndif(instance):
	return max([len(p) for o in instance.orders for p in o if len(p) > 0] + [0])

def smallestIndif(instance):
	return min([len(p) for o in instance.orders for p in o if len(p) > 0] + [instance.nbAlternatives])

def isApproval(instance):
	m = max([len(o) for o in instance.orders])
	if m == 1:
		return True
	elif m == 2:
		return isComplete(instance)
	else:
		return False

def isStrict(instance):
	return largestIndif(instance) == 0

def isComplete(instance):
	return smallestBallot(instance) == instance.nbAlternatives

# Test if a given profile is single peaked using algorithm in Bartholdi and Trick (1986)
# by first constructing the correct matrix and second using a SAT solver to check whether
# the matrix has the consecutive ones property.
# The SAT solver code has been taken from: Zack Fitzsimmons (zfitzsim@holycross.edu) and
# Martin Lackner (lackner@dbai.tuwien.ac.at)
def isSP(instance):
	def leftof(x, y):
		return x * num_cols + y + 1

	matrix = np.zeros((len(instance.orders) * (len(instance.orders[0]) - 1), len(instance.orders[0])))
	for i in range(len(instance.orders)):
		order = instance.orders[i]
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

def isSC(instance):

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

	for i in range(len(instance.orders)):
		if isSCwithFirst(i, instance.orders):
			return True
	return False