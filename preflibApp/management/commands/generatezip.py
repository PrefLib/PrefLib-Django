from django.core.management.base import BaseCommand
from django.contrib.staticfiles import finders
from django.core import management
from django.utils import timezone
from django.db.models import Max
from django.apps import apps

from preflibApp.models import *

import traceback
import zipfile
import sys
import os

class Command(BaseCommand):
	help = "Generate the zip files of the data"

	def handle(self, *args, **options):
		# Finding the data dir in the static folder
		dataDir = finders.find("data")

		# Creating the lock
		lock = open(os.path.join(dataDir, "zip.lock"), "w")
		lock.close()

		try:
			# Initializing a new log
			newLogNum = Log.objects.filter(logType = "zip").aggregate(Max('logNum'))['logNum__max']
			if newLogNum == None:
				newLogNum = 0
			else:
				newLogNum += 1

			# Starting the log
			log = ["<h4> Zipping log #" + str(newLogNum) + " - " + str(timezone.now()) + "</h4>\n"]
			startTime = timezone.now()

			# We start by zipping the data sets
			log.append("<p>Zipping data sets...</p>\n<ul>\n")
			for ds in DataSet.objects.all():
				print("Zipping dataset " + str(ds))
				log.append("\t<li>Zipping dataset " + str(ds) + "... ")
				self.zipDataSet(ds, dataDir)
				log.append(" ... done.</li>\n")
			log.append("</ul>\n<p>... done.</p>\n")

			# We will now zip the files per type, starting by creating the corresponding folder
			try:
				os.makedirs(os.path.join(dataDir, "types"))
			except Exception as e:
				pass

			# We actually zip the types
			log.append("\n<p>Zipping data files by type</p>\n<ul>\n")
			for dataType in DataFile.objects.order_by().values('dataType').distinct():
				dataType = dataType['dataType']
				print("Zipping type " + dataType)
				log.append("\t<li>Zipping type " + dataType + "... ")
				self.zipType(dataType, dataDir)
				log.append(" ... done.</li>\n")
			log.append("</ul>\n<p>... done.</p>\n")

			# We finish the log
			log.append("\n<p>Regeneration of the zip files successfully completed in ") 
			log.append(str((timezone.now() - startTime).total_seconds() / 60) + " minutes</p>\n")

			# And finally collect the statics
			print("Finished, collecting statics")
			management.call_command("collectstatic", no_input = False)

		except Exception as e:
			# If anything happened, we log it and move on
			log.append("\n<p><strong>" + str(e) + "<br>\n" + str(traceback.format_exc()) + "</strong></p>")
			print(traceback.format_exc())
			print(e)

		finally:
			# In any cases we remove the lock and save the log
			os.remove(os.path.join(dataDir, "zip.lock"))
			Log.objects.create(
				log = ''.join(log),
				logType = "zip", 
				logNum = newLogNum,
				publicationDate = timezone.now())

	# Function to create the zip of dataset
	def zipDataSet(self, ds, dataDir):
		# First locate the dataset folder
		dsDir = os.path.join(dataDir, ds.category, ds.abbreviation)
		# Create the zip file for the dataset
		zipf = zipfile.ZipFile(os.path.join(dsDir, ds.abbreviation + ".zip"), "w", zipfile.ZIP_DEFLATED)

		# Re-create the info file based on the details in the database
		infoFile = open(os.path.join(dsDir, "info.txt"), "w")
		infoFile.write("Name: " + ds.name + "\n\n")
		infoFile.write("Abbreviation: " + ds.abbreviation + "\n\n")
		infoFile.write("Category: " + ds.category + "\n\n")
		infoFile.write("Series Number: " + ds.seriesNumber + "\n\n")
		infoFile.write("Path: " + ds.category + "/" + ds.abbreviation + "\n\n")
		infoFile.write("Description: " + ds.description + "\n\n")
		infoFile.write("Required Citations: " + ds.requiredCitations + "\n\n")
		infoFile.write("Selected Studies: " + ds.selectedStudies + "\n\n")
		infoFile.write("description, status, file_name\n")

		# Add all the files to the zip archive and their info in the info file
		for df in DataFile.objects.filter(dataPatch__dataSet = ds):
			zipf.write(os.path.join(dsDir, df.fileName), df.fileName)
			infoFile.write(df.dataPatch.description + ", " + df.modificationType + ", " + df.fileName + "\n")

		# Add the info.txt file to the archive
		infoFile.close()
		zipf.write(os.path.join(dsDir, "info.txt"), "info.txt")

		# Closing the archive
		zipf.close()

	# Function to zip a type of data
	def zipType(self, dataType, dataDir):
		zipf = zipfile.ZipFile(os.path.join(dataDir, "types", dataType + ".zip"), "w", zipfile.ZIP_DEFLATED)
		for df in DataFile.objects.filter(dataType = dataType):
			zipf.write(os.path.join(dataDir, df.dataPatch.dataSet.category, df.dataPatch.dataSet.abbreviation, 
				df.fileName), df.fileName)
		zipf.close()