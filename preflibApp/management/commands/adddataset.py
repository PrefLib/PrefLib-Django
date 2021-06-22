from itertools import permutations, combinations, combinations_with_replacement
from django.core.management.base import BaseCommand
from django.contrib.staticfiles import finders
from django.core import management
from django.utils import timezone
from django.conf import settings
from django.db.models import Max
from django.apps import apps

from preflibApp.choices import *
from preflibApp.models import *

import traceback
import zipfile
import os

class Command(BaseCommand):
	help = "Add datasets to database"

	def add_arguments(self, parser):
		parser.add_argument('--file', nargs = '*', type = str)
		parser.add_argument('--all', action = 'store_true')

	def handle(self, *args, **options):
		# Looking for the datatoadd folder
		dataToAddDir = finders.find("datatoadd")
		if not dataToAddDir:
			print("The folder datatoadd was not found, no dataset has been added.")
			return 

		# Putting the lock on
		lock = open(os.path.join(dataToAddDir, "dataset.lock"), "w")
		lock.close()

		try:
			# Initializing the log
			newLogNum = Log.objects.filter(logType = "dataset").aggregate(Max('logNum'))['logNum__max']
			if newLogNum == None:
				newLogNum = 0
			else:
				newLogNum += 1

			# Looking for the data folder, creating it if its not there
			dataDir = finders.find("data")
			if not dataDir:
				try:
					os.makedirs(dataToAddDir[0:-9] + "data")
					dataDir = dataToAddDir[0:-9] + "data"
				except Exception as e:
					pass

			# Creating a tmp folder to extract the zip in
			tmpDir = os.path.join(dataToAddDir, "tmp")
			try:
				os.makedirs(tmpDir)
			except Exception as e:
				pass

			# Starting the log
			log = ["<h4> Adding dataset #" + str(newLogNum) + " - " + str(timezone.now()) + "</h4>\n"]
			log.append("<ul>\n\t<li>args : " + str(args) + "</li>\n\t<li>options : " + str(options) + 
				"</li>\n</ul>\n")

			# If the option 'all' has been passed, we add all the datasets in the datatoadd folder
			# to the 'file' option
			if options['all']:
				options['file'] = []
				for filename in os.listdir(dataToAddDir):
					if filename.endswith(".zip"):
						options['file'].append(str(filename))

			# Starting the real stuff
			log.append("<p>Adding datasets</p>\n<ul>\n")
			startTime = timezone.now()
			for fileName in options['file']:
				# We only consider zip files
				if fileName.endswith('.zip'):
					# Let's work on the dataset
					fileName = fileName.split(os.path.sep)[-1]
					print("Dataset " + str(fileName))
					log.append("\n\t<li>Dataset " + str(fileName) + "... ")
					try:
						# Actually adding the dataset
						self.addDataset(tmpDir, dataToAddDir, dataDir, fileName, log)
						log.append(" ... done.</li>\n")
					except Exception as e:
						# If something happened, we log it and move on
						log.append("</li>\n</ul>\n<p><strong>" + str(e) + "<br>\n" + str(traceback.format_exc()) + 
						"	</strong></p>\n<ul>")
					finally:
						# In any cases, we delete all the temporary stuff we have created
						for fileName in os.listdir(tmpDir):
							os.remove(os.path.join(tmpDir, fileName))

			# Removing the tmp folder
			os.rmdir(tmpDir)

			# Finalizing the log
			log.append("</ul>\n<p>The datasets have been successfully added in ")
			log.append(str((timezone.now() - startTime).total_seconds() / 60))
			log.append(" minutes.</p>")
			
			# Collecting the statics once everything has been done
			print("Finished, collecting statics")
			management.call_command("collectstatic", no_input = False)
		except Exception as e:
			# If anything happened during the execution, we log it and move on
			log.append("\n<p><strong>" + str(e) + "<br>\n" + str(traceback.format_exc()) + "</strong></p>")
			print(traceback.format_exc())
			print(e)
		finally:
			# In any cases, we remove the lock and save the log
			os.remove(os.path.join(dataToAddDir, "dataset.lock"))
			Log.objects.create(
				log = ''.join(log),
				logType = "dataset", 
				logNum = newLogNum,
				publicationDate = timezone.now())

	# Function that reads the info file in the zip file to get the details of the dataset
	def readInfoFile(self, fileName, tmpDir):
		infos = {"datafiles": []}
		file = open(fileName, 'r')
		# We go line per line trying to match the beginning of the line to a known header
		for line in file.readlines():
			if len(line) > 1:
				if line.startswith('Name:'):
					infos['name'] = line[5:].strip()
				elif line.startswith('Abbreviation:'):
					infos['abb'] = line[13:].strip()
				elif line.startswith('Category:'):
					infos['cat'] = line[10:].strip()
				elif line.startswith('Extension:'):
					infos['cat'] = line[10:].strip()
				elif line.startswith('Series Number:'):
					infos['series'] = line[14:].strip()
				elif line.startswith('Description:'):
					infos['descr'] = line[12:].strip()
				elif line.startswith('Required Citations:'):
					infos['cite'] = line[19:].strip() if line[19:].strip() != "None" else ""
				elif line.startswith('Selected Studies:'):
					infos['studies'] = line[17:].strip() if line[17:].strip() != "None" else ""
				elif line.startswith('description,status,file_name') or line.startswith('Path:'):
					pass
				# If it's not one the above header, it must be the list of the files contained in the
				# dataset, we parse this here
				else:
					tmp = {}
					tmpline = line.split(',')
					tmp['descr'] = tmpline[0].strip()
					tmp['status'] = tmpline[1].strip().lower()
					tmp['fileName'] = tmpline[2].strip()
					try:
						tmp['size'] = os.path.getsize(os.path.join(tmpDir, tmpline[2].strip()))
					except:
						tmp['size'] = 0
					infos["datafiles"].append(tmp)
		file.close()
		return infos

	# All the details of adding a dataset
	def addDataset(self, tmpDir, dataToAddDir, dataDir, zipfileName, log):
		# We start by extracting the zip file
		with zipfile.ZipFile(os.path.join(dataToAddDir, zipfileName), 'r') as archive:
			archive.extractall(tmpDir)

		# We try to read and parse the info file, if we don't find the info.txt file,
		# we skip the dataset
		infos = None
		for fileName in os.listdir(tmpDir):
			if fileName == "info.txt":
				infos = self.readInfoFile(os.path.join(tmpDir, fileName), tmpDir)
				os.remove(os.path.join(tmpDir, fileName))
				break
		if infos == None:
			raise Exception("No info.txt file has been found for " + str(zipfileName) + " ... skipping it.")
	
		# Now that we have all the infos, we can create the dataset object in the database
		datasetObj = DataSet.objects.update_or_create(
			category = infos['cat'],
			seriesNumber = infos['series'],
			defaults = {
				'name': infos['name'],
				'abbreviation': infos['abb'],
				'description': infos['descr'],
				'requiredCitations': infos['cite'],
				'selectedStudies': infos['studies'], 
				'modificationDate': timezone.now()})

		# We create a folder for the dataset in the data folder
		try:
			os.makedirs(os.path.join(dataDir, infos['cat'], infos['abb']))
		except Exception as e:
			pass
		# We create the 'img' folder in the previously created folder, this folder
		# will contain all the visializations of the datafiles 
		try:
			os.makedirs(os.path.join(dataDir, infos['cat'], infos['abb'], 'img'))
		except Exception as e:
			pass

		# Let's now add the datafiles to the database
		for fileName in os.listdir(tmpDir):
			# We only do it if it actually is a file we're interested in
			if isAChoice(DATATYPES, fileName.split('.')[-1]):
				# Move the file to the folder of the dataset
				os.rename(os.path.join(tmpDir, fileName), os.path.join(dataDir, infos['cat'], infos['abb'], fileName))
				# Looking through the infos we collected to see if the file appears there
				infoFile = None
				for i in infos["datafiles"]:
					if i['fileName'] == fileName:
						infoFile = i
						break
				# If not, we proceed with default values and raise a warning
				if infoFile == None:
					infoFile = {'descr': '-', 'status': '-', 
						'size': os.path.getsize(os.path.join(dataDir, infos['cat'], infos['abb'], fileName))}
					log.append("</li>\n</ul>\n<p><strong>No info has been for the file " + str(fileName) + 
						" in the info file of " + str(zipfileName) + "</strong></p>\n<ul>")

				# We get of create the datapatch object containing the datafile
				dataPatchObj = DataPatch.objects.get_or_create(
					name = fileName.split('.')[0],
					dataSet = datasetObj[0],
					seriesNumber = fileName.split('.')[0].split('-')[-1],
					defaults = {
						"description": infoFile['descr'],
						"modificationDate": timezone.now()})

				# We can finally create (or update) the datafile object in the database
				dataFileObj = DataFile.objects.update_or_create(
					dataPatch = dataPatchObj[0],
					fileName = fileName,
					defaults = {
						"dataType": fileName.split('.')[-1],
						"modificationType": infoFile['status'],
						"fileSize": infoFile['size'],
						"modificationDate": timezone.now()})

		# Finally, we remove the zip file from the datatoadddir since everything went well
		os.remove(os.path.join(dataToAddDir, zipfileName))