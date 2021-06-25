from django.core.management.base import BaseCommand
from datetime import datetime
from django.apps import apps

from preflibApp.models import Metadata 
from preflibApp.choices import *

import traceback
import time
import os

class Command(BaseCommand):
	help = "Initializes the database, to be run once at the beginning"

	def handle(self, *args, **options):
		self.initializeMetadata()

	def initializeMetadata(self):

		metadataNumAlt = Metadata.objects.update_or_create(
			name = "Number of alternatives",
			defaults = {
				"category": "general",
				"description": "The number of alternatives is the number of elements agents had to vote on. It is only available for data representing orderings of the alternatives.",
				"isActive": True,
				"isDisplayed": True,
				"appliesTo": 'soc,soi,toc,toi,tog,mjg,wmg,pwg,wmd',
				"innerModule": "preflibtools.properties",
				"innerFunction": "nbAlternatives",
				"innerType": "int",
				"searchWidget": "range",
				"shortName": "numAlt",
				"searchQuestion": "Number of alternatives:",
				"searchResName": "#Alternatives",
				"orderPriority": 1})

		metadataNumVot = Metadata.objects.update_or_create(
			name = "Number of voters",
			defaults = {
				"category": "general",
				"description": "The number of voters is the number of ballots that were submitted. For weighted matching graphs",
				"isActive": True,
				"isDisplayed": True,
				"appliesTo": ",".join([t[0] for t in DATATYPES]),
				"innerModule": "preflibtools.properties",
				"innerFunction": "nbVoters",
				"innerType": "int",
				"searchWidget": "range",
				"shortName": "numVot",
				"searchQuestion": "Number of voters:",
				"searchResName": "#Voters",
				"orderPriority": 2})

		metadataSumVote = Metadata.objects.update_or_create(
			name = "Sum of vote count",
			defaults = {
				"category": "general",
				"description": """The sum of the weights of the ballots cast. See the data <a href="/data/format#election">format page</a> for more information.""",
				"isActive": True,
				"isDisplayed": True,
				"appliesTo": ",".join([t[0] for t in DATATYPES]),
				"innerModule": "preflibtools.properties",
				"innerFunction": "nbSumVoters",
				"innerType": "int",
				"searchWidget": "range",
				"shortName": "sumVot",
				"searchQuestion": "Sum of vote count:",
				"searchResName": "Sum Vote Count",
				"orderPriority": 3})

		metadataUniqOrders = Metadata.objects.update_or_create(
			name = "Number of unique orders",
			defaults = {
				"category": "general",
				"description": "The number of distinct ballots that were casts.",
				"isActive": True,
				"isDisplayed": True,
				"appliesTo": ",".join([t[0] for t in DATATYPES]),
				"innerModule": "preflibtools.properties",
				"innerFunction": "nbDifferentOrders",
				"innerType": "int",
				"searchWidget": "range",
				"shortName": "numUniq",
				"searchQuestion": "Number of unique orders:",
				"searchResName": "#Unique Ballots",
				"orderPriority": 4})

		# metadataNumNodes = Metadata.objects.update_or_create(
		# 	name = "Number of nodes",
		# 	update_or_create(
		#	defaults = {
		#		"category": "general",
		# 		"description": "For data representing graphs, it represents the number of nodes in the graph.",
		# 		"isActive": True,
		#		"isDisplayed": True,
		# 		"appliesTo": 'tog,mjg,wmg,pwg,wmd',
		# 		"innerModule": "preflibtools.properties",
		# 		"innerFunction": "nbAlternatives",
		# 		"innerType": "int",
		# 		"searchWidget": "range",
		# 		"shortName": "numNodes",
		# 		"searchQuestion": "Number of nodes:",
		#		"searchResName": "",
		#		"orderPriority": "")

		metadataIsStrict = Metadata.objects.update_or_create(
			name = "Strict orders",
			defaults = {
				"category": "preference",
				"description": "A boolean value set to True if all the ballots that were cast represent strict linear orders.",
				"isActive": True,
				"isDisplayed": False,
				"appliesTo": 'soc,soi,toc,toi',
				"innerModule": "preflibtools.properties",
				"innerFunction": "isStrict",
				"innerType": "bool",
				"searchWidget": "ternary",
				"shortName": "isStrict",
				"searchQuestion": "Is strict?",
				"searchResName": "Strict",
				"orderPriority": 11})

		metadataIsComplete = Metadata.objects.update_or_create(
			name = "Complete orders",
			defaults = {
				"category": "preference",
				"description": "A boolean value set to True if all the ballots that were cast represent complete linear orders.",
				"isActive": True,
				"isDisplayed": False,
				"appliesTo": 'soc,soi,toc,toi',
				"innerModule": "preflibtools.properties",
				"innerFunction": "isComplete",
				"innerType": "bool",
				"searchWidget": "ternary",
				"shortName": "isComplete",
				"searchQuestion": "Is complete?",
				"searchResName": "Complete",
				"orderPriority": 12})

		metadataIsApp = Metadata.objects.update_or_create(
			name = "Approval profile",
			defaults = {
				"category": "preference",
				"description": "A boolean value set to True if the ballots can be interpreted as approval ballots. That is the case if, either every ballot consist of a single set of indifferences, or every ballots is complete and consist of two set of indifferences.",
				"isActive": True,
				"isDisplayed": True,
				"appliesTo": 'soc,soi,toc,toi',
				"innerModule": "preflibtools.properties",
				"innerFunction": "isApproval",
				"innerType": "bool",
				"searchWidget": "ternary",
				"shortName": "isApproval",
				"searchQuestion": "Is an approval profile?",
				"searchResName": "Approval",
				"orderPriority": 13})

		metadataIsSP = Metadata.objects.update_or_create(
			name = "Single-peaked",
			defaults = {
				"category": "preference",
				"description": """A boolean value set to True if the set of ballots cast represents <a href="https://en.wikipedia.org/wiki/Single_peaked_preferences">single-peaked preferences</a>. To check this property, we used the <a href="https://github.com/zmf6921/incompletesp">code of Zack Fitzsimmons and Martin Lackner</a> available on GitHub that we want to thank here.""",
				"isActive": True,
				"isDisplayed": True,
				"appliesTo": 'soc',
				"innerModule": "preflibtools.properties",
				"innerFunction": "isSP",
				"innerType": "bool",
				"searchWidget": "ternary",
				"shortName": "isSP",
				"searchQuestion": "Is single-peaked?",
				"searchResName": "Single-Peaked",
				"orderPriority": 14})

		metadataIsSC = Metadata.objects.update_or_create(
			name = "Single-crossing",
			defaults = {
				"category": "preference",
				"description": "A boolean value set to True if the set of ballots cast represents single-crossing preferences.",
				"isActive": True,
				"isDisplayed": True,
				"appliesTo": 'soc',
				"innerModule": "preflibtools.properties",
				"innerFunction": "isSC",
				"innerType": "bool",
				"searchWidget": "ternary",
				"shortName": "isSC",
				"searchQuestion": "Is single-crossing?",
				"searchResName": "Single-Crossing",
				"orderPriority": 15})

		metadataLargBallot = Metadata.objects.update_or_create(
			name = "Size of the largest ballot",
			defaults = {
				"category": "ballot",
				"description": """Given a set of ballots, how many alternatives have been submitted in the ballot with the highest number of submitted alternatives. In data representing complete orders (<a href="/data/types#soc">SOC</a> and <a href="/data/types#toc">TOC</a>), this should be equal to the number of alternatives.""",
				"isActive": True,
				"isDisplayed": True,
				"appliesTo": 'soc,soi,toc,toi',
				"innerModule": "preflibtools.properties",
				"innerFunction": "largestBallot",
				"innerType": "int",
				"searchWidget": "range",
				"shortName": "largestBallot",
				"searchQuestion": "Size of the largest ballot:",
				"searchResName": "Largest Ballot",
				"orderPriority": 6})

		metadataSmalBallot = Metadata.objects.update_or_create(
			name = "Size of the smallest ballot",
			defaults = {
				"category": "ballot",
				"description": """Given a set of ballots, how many alternatives have been submitted in the ballot with the smallest number of submitted alternatives. In data representing complete orders (<a href="/data/types#soc">SOC</a> and <a href="/data/types#toc">TOC</a>), this should be equal to the number of alternatives.""",
				"isActive": True,
				"isDisplayed": True,
				"appliesTo": 'soc,soi,toc,toi',
				"innerModule": "preflibtools.properties",
				"innerFunction": "smallestBallot",
				"innerType": "int",
				"searchWidget": "range",
				"shortName": "smallestBallot",
				"searchQuestion": "Size of the smallest ballot:",
				"searchResName": "Smallest Ballot",
				"orderPriority": 5})

		metadataMaxNumIndif = Metadata.objects.update_or_create(
			name = "Maximum number of indifferences",
			defaults = {
				"category": "ballot",
				"description": """In a given ballot, an indifference is a position in the order such that more than one alternative is ranked at this position. Given a set of ballots, the maximum number of indifferences is the number of indifferences in the ballot with the highest number of them. In data witout ties (<a href="/data/types#soc">SOC</a> and <a href="/data/types#soi">SOI</a>), this should be 0.""",
				"isActive": True,
				"isDisplayed": True,
				"appliesTo": 'soc,soi,toc,toi',
				"innerModule": "preflibtools.properties",
				"innerFunction": "maxNbIndif",
				"innerType": "int",
				"searchWidget": "range",
				"shortName": "maxNumIndif",
				"searchQuestion": "Maximum number of indifferences:",
				"searchResName": "Max #Indif.",
				"orderPriority": 8})

		metadataMinNumIndif = Metadata.objects.update_or_create(
			name = "Minimum number of indifferences",
			defaults = {
				"category": "ballot",
				"description": """In a given ballot, an indifference is a position in the order such that more than one alternative is ranked at this position. Given a set of ballots, the minimum number of indifferences is the number of indifferences in the ballot with the smallest number of them. In data witout ties (<a href="/data/types#soc">SOC</a> and <a href="/data/types#soi">SOI</a>), this should be 0.""",
				"isActive": True,
				"isDisplayed": True,
				"appliesTo": 'soc,soi,toc,toi',
				"innerModule": "preflibtools.properties",
				"innerFunction": "minNbIndif",
				"innerType": "int",
				"searchWidget": "range",
				"shortName": "minNumIndif",
				"searchQuestion": "Minimum number of indifferences:",
				"searchResName": "Min #Indif.",
				"orderPriority": 7})

		metadataLargIndif = Metadata.objects.update_or_create(
			name = "Size of the largest indifference",
			defaults = {
				"category": "ballot",
				"description": """In a given ballot, an indifference is a position in the order such that more than one alternative is ranked at this position. Given a set of ballots, the size of the largest indifference is the maximal number of alternatives which are tied in a ballot. In data witout ties (<a href="/data/types#soc">SOC</a> and <a href="/data/types#soi">SOI</a>), this should be 0.""",
				"isActive": True,
				"isDisplayed": True,
				"appliesTo": 'soc,soi,toc,toi',
				"innerModule": "preflibtools.properties",
				"innerFunction": "largestIndif",
				"innerType": "int",
				"searchWidget": "range",
				"shortName": "largestIndif",
				"searchQuestion": "Size of the largest indifference:",
				"searchResName": "Largest Indif.",
				"orderPriority": 10})

		metadataSmalIndif = Metadata.objects.update_or_create(
			name = "Size of the smallest indifference",
			defaults = {
				"category": "ballot",
				"description": """In a given ballot, an indifference is a position in the order such that more than one alternative is ranked at this position. Given a set of ballots, the size of the largest indifference is the maximal number of alternatives which are tied in a ballot. In data witout ties (<a href="/data/types#soc">SOC</a> and <a href="/data/types#soi">SOI</a>), this should be 0.""",
				"isActive": True,
				"isDisplayed": True,
				"appliesTo": 'soc,soi,toc,toi',
				"innerModule": "preflibtools.properties",
				"innerFunction": "smallestIndif",
				"innerType": "int",
				"searchWidget": "range",
				"shortName": "smallestIndif",
				"searchQuestion": "Size of the smallest indifference:",
				"searchResName": "Smallest Indif.",
				"orderPriority": 9})

		# metadataObj = Metadata.objects.update_or_create(
		# 	name = "Condorcet winner",
		# 	update_or_create(
		#	defaults = {
		#		"category": "graph",
		# 		"description": """A boolean value set to True if the ballot represented as a graph admits a <a href="https://en.wikipedia.org/wiki/Condorcet_criterion">Condorcet winner</a>.""",
		# 		"isActive": True,
		#		"isDisplayed": True,
		# 		"appliesTo": 'tog,mjg,wmg,pwg',
		# 		"innerModule": "preflibtools.properties",
		# 		"innerFunction": "hasCondorcet",
		# 		"innerType": "bool",
		# 		"searchWidget": "ternary",
		# 		"shortName": "hasCondorcet",
		# 		"searchQuestion": "Has a Condorcet winner?",
		#		"searchResName": "",
		#		"orderPriority": "")

		metadataNumAlt[0].upperBounds.set([])
		metadataNumAlt[0].upperBounds.add(metadataSmalBallot[0])
		metadataNumAlt[0].upperBounds.add(metadataLargBallot[0])
		metadataNumAlt[0].upperBounds.add(metadataSmalIndif[0])
		metadataNumAlt[0].upperBounds.add(metadataLargIndif[0])

	def initializePaper(self, Paper):
		pass