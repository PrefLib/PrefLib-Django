from django.db import models
from django.contrib.auth.models import User

from pydoc import locate

from .choices import *

# ===========================
#    Profile for the users   
# ===========================

class UserProfile(models.Model):
	user = models.OneToOneField(User, 
		on_delete = models.CASCADE)
	firstname = models.CharField(max_length = 100)
	lastname = models.CharField(max_length = 100)
	email = models.EmailField()
	affiliation = models.TextField(null = True)
	personnalURL = models.URLField(null = True)

	class Meta:
		ordering = ['user']

	def __str__(self):
		return self.firstname + " " + self.lastname

# ================================
#    Models related to the data  
# ================================

class DataTag(models.Model):
	name = models.CharField(max_length = 30, 
		unique = True)
	description = models.TextField()
	parent = models.ForeignKey('DataTag', 
		on_delete = models.CASCADE, 
		null = True, 
		blank = True, 
		related_name = "children")

	class Meta:
		ordering = ['name']

	def __str__(self):
		return self.name

class DataSet(models.Model):
	name = models.CharField(max_length = 1000)
	abbreviation = models.CharField(max_length = 100, 
		unique = True)
	category = models.CharField(choices = DATACATEGORY, 
		max_length = 5)
	seriesNumber = models.SlugField()
	description = models.TextField()
	tags = models.ManyToManyField(DataTag,
		blank = True)
	requiredCitations = models.TextField(blank = True, 
		null = True)
	selectedStudies = models.TextField()
	publicationDate = models.DateField()
	modificationDate = models.DateField(auto_now = True)

	def get_tag_list(self):
		return ', '.join([str(tag) for tag in self.tags.all()])

	class Meta:
		ordering = ('category', 'seriesNumber')
		unique_together = ('category', 'seriesNumber')

	def __str__(self):
		return self.category + "-" + self.seriesNumber + " - " + self.name

class DataPatch(models.Model):
	dataSet = models.ForeignKey(DataSet, 
		on_delete = models.CASCADE)
	seriesNumber = models.SlugField()
	name = models.CharField(max_length = 1000)
	description = models.CharField(max_length = 1000)
	representative = models.ForeignKey("DataFile",
		on_delete = models.CASCADE,
		blank = True,
		null = True)
	publicationDate = models.DateField()
	modificationDate = models.DateField(auto_now = True)

	class Meta:
		unique_together = ('dataSet', 'seriesNumber')
		ordering = ['name']

	def __str__(self):
		return self.name

class Metadata(models.Model):
	name = models.CharField(max_length = 100, 
		unique = True)
	shortName = models.CharField(max_length = 100, 
		unique = True)
	category = models.CharField(choices = METADATACATEGORIES, 
		max_length = 100)
	description = models.TextField()
	isActive = models.BooleanField()
	isDisplayed = models.BooleanField()
	appliesTo = models.CharField(max_length = 1000)
	upperBounds = models.ManyToManyField('self', 
		symmetrical = False, 
		related_name = "upperBoundedBy", 
		blank = True)
	innerModule = models.CharField(max_length = 100)
	innerFunction = models.CharField(max_length = 100)
	innerType = models.CharField(max_length = 100)
	searchWidget = models.CharField(choices = SEARCHWIDGETS,
		max_length = 100)
	searchQuestion = models.CharField(max_length = 1000)
	searchResName = models.CharField(max_length = 100)
	orderPriority = models.IntegerField()

	class Meta:
		ordering = ["orderPriority", "name"]

	def getAppliesToList(self):
		return self.appliesTo.split(',')

	def __str__(self):
		return self.name

class DataFile(models.Model):
	dataPatch = models.ForeignKey(DataPatch, 
		on_delete = models.CASCADE)
	fileName = models.CharField(max_length = 255, 
		unique = True)
	dataType = models.CharField(choices = DATATYPES, 
		max_length = 5)
	metadatas = models.ManyToManyField(Metadata, 
		through = "DataProperty")
	modificationType = models.CharField(choices = MODIFICATIONTYPES, 
		max_length = 20)
	fileSize = models.FloatField(default = 0)
	image = models.CharField(max_length = 1000, null = True)
	publicationDate = models.DateField()
	modificationDate = models.DateField(auto_now = True)

	class Meta:
		ordering = ['fileName']

	def shortName(self):
		return self.fileName.split('.')[0][3:]

	def __str__(self):
		return self.fileName

class DataProperty(models.Model):
	dataFile = models.ForeignKey(DataFile, 
		on_delete = models.CASCADE)
	metadata = models.ForeignKey(Metadata, 
		on_delete = models.CASCADE)
	value = models.CharField(max_length = 1000)

	def getTypedValue(self):
		if self.metadata.innerType == "bool":
			return self.value == "True"
		return locate(self.metadata.innerType)(self.value)

	class Meta:
		unique_together = ("dataFile", "metadata")
		ordering = ("dataFile", "metadata")

	def __str__(self):
		return self.dataFile.__str__() + " - " + self.metadata.name


# ===================================
#    Papers that are using PrefLib     
# ===================================

class Paper(models.Model):
	name = models.CharField(max_length = 50, 
		unique = True)
	title = models.CharField(max_length = 1000)
	authors = models.CharField(max_length = 1000)
	publisher = models.CharField(max_length = 1000)
	year = models.IntegerField(default = 0)
	url = models.URLField(max_length = 1000)

	class Meta:
		ordering = ['-year', 'title']

	def __str__(self):
		return self.authors.split(' ')[1] + "_" + str(self.year)

# ==============================
#    Logs for the admin tasks   
# ==============================

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