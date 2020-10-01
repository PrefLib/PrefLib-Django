from django.db import models
from django.contrib.auth.models import User

from .choices import *

class DataSet(models.Model):
	name = models.CharField(max_length = 1000)
	abbreviation = models.CharField(max_length = 100)
	extension = models.CharField(choices = DATASETEXTENSIONS, max_length = 5)
	seriesNumber = models.SlugField()
	description = models.TextField()
	requiredCitations = models.TextField()
	selectedStudies = models.TextField()
	publicationDate = models.DateTimeField(auto_now = True)
	modificationDate = models.DateTimeField(auto_now = True)

	class Meta:
		ordering = ('extension', 'seriesNumber')
		unique_together = ('extension', 'seriesNumber')

	def __str__(self):
		return self.extension + "-" + self.seriesNumber + " - " + self.name

class DataPatch(models.Model):
	dataSet = models.ForeignKey(DataSet, on_delete = models.CASCADE)
	name = models.CharField(max_length = 1000)
	description = models.CharField(max_length = 1000)
	seriesNumber = models.SlugField()
	publicationDate = models.DateTimeField(auto_now = True)
	modificationDate = models.DateTimeField(auto_now = True)

	class Meta:
		unique_together = ('dataSet', 'seriesNumber')
		ordering = ['name']

	def __str__(self):
		return self.name

class DataFile(models.Model):
	dataPatch = models.ForeignKey(DataPatch, on_delete = models.CASCADE)
	dataType = models.CharField(choices = DATATYPES, max_length = 5)
	modificationType = models.CharField(choices = MODIFICATIONTYPES, max_length = 20)
	fileName = models.CharField(max_length = 1000, unique = True)
	fileSize = models.FloatField(default = 0)
	publicationDate = models.DateTimeField(auto_now = True)
	modificationDate = models.DateTimeField(auto_now = True)

	class Meta:
		unique_together = ('dataPatch', 'fileName')
		ordering = ['fileName']

	def shortName(self):
		return self.fileName.split('.')[0][3:]

	def __str__(self):
		return self.fileName

class DataProp(models.Model):
	dataFile = models.OneToOneField(DataFile, on_delete = models.CASCADE, related_name = "proptofile")
	image = models.CharField(max_length = 1000, null = True)
	text = models.TextField(null = True)
	nbAlternatives = models.IntegerField(null = True)
	nbVoters = models.IntegerField(null = True)
	nbSumVoters = models.IntegerField(null = True)
	nbDifferentOrders = models.IntegerField(null = True)
	largestBallot = models.IntegerField(null = True)
	smallestBallot = models.IntegerField(null = True)
	maxNbIndif = models.IntegerField(null = True)
	minNbIndif = models.IntegerField(null = True)
	largestIndif = models.IntegerField(null = True)
	smallestIndif = models.IntegerField(null = True)
	isSinglePeaked = models.BooleanField(null = True)
	minNumPeaks = models.IntegerField(null = True)
	isSingleCrossed = models.BooleanField(null = True)
	isApproval = models.BooleanField(null = True)
	isStrict = models.BooleanField(null = True)
	isComplete = models.BooleanField(null = True)
	hasCondorcet = models.BooleanField(null = True)
	graphEqClass = models.CharField(max_length = 30, null = True)

	class Meta:
		ordering = ["dataFile"]

	def __str__(self):
		return "MetaData for " + self.dataFile.fileName

class Paper(models.Model):
	name = models.CharField(max_length = 50, unique = True)
	title = models.CharField(max_length = 1000)
	authors = models.CharField(max_length = 1000)
	publisher = models.CharField(max_length = 1000)
	year = models.IntegerField(default = 0)
	url = models.URLField(max_length = 1000)
	publicationDate = models.DateTimeField(auto_now = True)

	class Meta:
		ordering = ['-year', 'title']

	def __str__(self):
		return self.authors.split(' ')[1] + "_" + self.year

class Log(models.Model):
	log = models.TextField()
	logType = models.CharField(max_length = 200)
	logNum = models.IntegerField(default = 0)
	publicationDate = models.DateTimeField()

	class Meta:
		ordering = ['-publicationDate']
		unique_together = ('logType', 'logNum')

	def __str__(self):
		return self.logType + " #" + str(self.logNum) + " - " + str(self.publicationDate)