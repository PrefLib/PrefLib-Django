from django.core.management.base import BaseCommand
from django.contrib.staticfiles import finders
from django.db.models import Max
from django.core import management
from django.apps import apps

from datetime import datetime

import os
import sys
import zipfile
import time
import traceback

class Command(BaseCommand):
	help = "Generate the zip files of the data"

	def handle(self, *args, **options):
		dataDir = finders.find("data")
		lock = open(os.path.join(dataDir, "zip.lock"), "w")
		lock.close()

		try:
			Log = apps.get_model("preflibApp", "Log")
			newLogNum = Log.objects.filter(logType = "zip").aggregate(Max('logNum'))['logNum__max']
			if newLogNum == None:
				newLogNum = 0
			else:
				newLogNum += 1

			DataSet = apps.get_model("preflibApp", "Dataset")
			DataPatch = apps.get_model("preflibApp", "DataPatch")
			DataFile = apps.get_model("preflibApp", "DataFile")

			log = ["<h4> Zipping log #" + str(newLogNum) + " - " + str(datetime.now()) + "</h4>\n"]
			startTime = time.time()
			log.append("<p>Zipping data sets...</p>\n<ul>\n")
			for ds in DataSet.objects.all():
				print("Zipping dataset " + str(ds))
				log.append("\t<li>Zipping dataset " + str(ds) + "... ")
				self.zipDataSet(ds, dataDir, DataFile)
				log.append(" ... done.</li>\n")
			log.append("</ul>\n<p>... done.</p>\n")

			try:
				os.makedirs(os.path.join(dataDir, "types"))
			except Exception as e:
				pass

			log.append("\n<p>Zipping data files by type</p>\n<ul>\n")
			for dataType in DataFile.objects.order_by().values('dataType').distinct():
				dataType = dataType['dataType']
				print("Zipping type " + dataType)
				log.append("\t<li>Zipping type " + dataType + "... ")
				self.zipType(dataType, dataDir, DataFile)
				log.append(" ... done.</li>\n")
			log.append("</ul>\n<p>... done.</p>\n")

			log.append("\n<p>Regeneration of the zip files successfully completed in ") 
			log.append(str((time.time() - startTime) / 60) + " minutes</p>\n")

			print("Finished, collecting statics")
			management.call_command("collectstatic", no_input = False)
		except Exception as e:
			log.append("\n<p><strong>" + str(e) + "<br>\n" + str(traceback.format_exc()) + "</strong></p>")
			print(traceback.format_exc())
			print(e)
		finally:
			os.remove(os.path.join(dataDir, "zip.lock"))
			Log.objects.create(
				log = ''.join(log),
				logType = "zip", 
				logNum = newLogNum,
				publicationDate = datetime.now())

	def zipDataSet(self, ds, dataDir, DataFile):
		dsDir = os.path.join(dataDir, ds.extension, ds.abbreviation)
		zipf = zipfile.ZipFile(os.path.join(dsDir, ds.abbreviation + ".zip"), "w", zipfile.ZIP_DEFLATED)

		infoFile = open(os.path.join(dsDir, "info.txt"), "w")
		infoFile.write("Name: " + ds.name + "\n\n")
		infoFile.write("Abbreviation: " + ds.abbreviation + "\n\n")
		infoFile.write("Extension: " + ds.extension + "\n\n")
		infoFile.write("Series Number: " + ds.seriesNumber + "\n\n")
		infoFile.write("Path: " + ds.extension + "/" + ds.abbreviation + "\n\n")
		infoFile.write("Description: " + ds.description + "\n\n")
		infoFile.write("Required Citations: " + ds.requiredCitations + "\n\n")
		infoFile.write("Selected Studies: " + ds.selectedStudies + "\n\n")
		infoFile.write("description, status, file_name\n")

		for df in DataFile.objects.filter(dataPatch__dataSet = ds):
			zipf.write(os.path.join(dsDir, df.fileName), df.fileName)
			infoFile.write(df.dataPatch.description + ", " + df.modificationType + ", " + df.fileName + "\n")

		infoFile.close()
		zipf.write(os.path.join(dsDir, "info.txt"), "info.txt")
		zipf.close()

	def zipType(self, dataType, dataDir, DataFile):
		zipf = zipfile.ZipFile(os.path.join(dataDir, "types", dataType + ".zip"), "w", zipfile.ZIP_DEFLATED)
		for df in DataFile.objects.filter(dataType = dataType):
			zipf.write(os.path.join(dataDir, df.dataPatch.dataSet.extension, df.dataPatch.dataSet.abbreviation, 
				df.fileName), df.fileName)
		zipf.close()