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
			print("ERROR: The static folder datatoadd was not found, no dataset has been added.")
			return 

		# Putting the lock on
		lock = open(os.path.join(dataToAddDir, "dataset.lock"), "w")
		lock.close()

		try:
			# Initializing the log
			newLogNum = Log.objects.filter(logType = "add_dataset").aggregate(Max('logNum'))['logNum__max']
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
				except FileExistsError as e:
					pass

			# Creating a tmp folder to extract the zip in
			tmpDir = os.path.join(dataToAddDir, "tmp")
			try:
				os.makedirs(tmpDir)
			except FileExistsError as e:
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
					print("Adding dataset " + str(fileName))
					log.append("\n\t<li>Dataset " + str(fileName) + "... ")
					try:
						# Actually adding the dataset
						self.addDataset(tmpDir, dataToAddDir, dataDir, fileName, log)
						log.append(" ... done.</li>\n")
					except Exception as e:
						# If something happened, we log it and move on
						log.append("</li>\n</ul>\n<p><strong>" + str(e) + "<br>\n" + str(traceback.format_exc()) + 
						"	</strong></p>\n<ul>")
						print(traceback.format_exc())
						print(e)
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
				logType = "add_dataset", 
				logNum = newLogNum,
				publicationDate = timezone.now())

	# Function that reads the info file in the zip file to get the details of the dataset
	def read_info_file(self, fileName, tmpDir):
		infos = {'files': {}, 'patches': {}}
		file = open(fileName, 'r')
		# We go line per line trying to match the beginning of the line to a known header
		reading_patches = False
		reading_files = False
		for line in file.readlines():
			if len(line) > 1:
				if line.startswith('Name:'):
					infos['name'] = line[5:].strip()
				elif line.startswith('Abbreviation:'):
					infos['abb'] = line[13:].strip()
				elif line.startswith('Category:'):
					infos['cat'] = line[9:].strip()
				elif line.startswith('Tags:'):
					infos['tags'] = [tag.strip() for tag in line[5:].strip().split(',')]
				elif line.startswith('Series Number:'):
					infos['series'] = line[14:].strip()
				elif line.startswith('Publication Date:'):
					infos['publication_date'] = line[17:].strip()
				elif line.startswith('Description:'):
					infos['description'] = line[12:].strip()
				elif line.startswith('Required Citations:'):
					infos['citations'] = line[19:].strip() if line[19:].strip() != "None" else ""
				elif line.startswith('Selected Studies:'):
					infos['studies'] = line[17:].strip() if line[17:].strip() != "None" else ""
				elif line.startswith('patch_name, description, series_number, publication_date, representative'):
					reading_patches = True
				elif line.startswith('patch_number, file_name, modification_type, publication_date'):
					reading_files = True
				# If it's not one the above header, it must be the lists of the patches and files contained in the
				# dataset, we parse this here
				else:
					if reading_patches and not reading_files:
						patch_dict = {}
						split_line = line.split(',')
						patch_dict['patch_name'] = split_line[0].strip()
						patch_dict['description'] = split_line[1].strip()
						patch_dict['series_number'] = split_line[2].strip()
						patch_dict['publication_date'] = split_line[3].strip()
						patch_dict['representative'] = split_line[4].strip()
						infos['patches'][patch_dict['series_number']] = patch_dict
					elif reading_files:
						file_dict = {}
						split_line = line.split(',')
						file_dict['patch_number'] = split_line[0].strip()
						file_dict['file_name'] = split_line[1].strip()
						file_dict['modification_type'] = split_line[2].strip()
						file_dict['publication_date'] = split_line[3].strip()
						try:
							file_dict['size'] = os.path.getsize(os.path.join(tmpDir, file_dict['file_name']))
						except:
							file_dict['size'] = 0
						infos['files'][file_dict['file_name']] = file_dict
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
				infos = self.read_info_file(os.path.join(tmpDir, fileName), tmpDir)
				os.remove(os.path.join(tmpDir, fileName))
				break
		if infos == None:
			raise Exception("No info.txt file has been found for " + str(zipfileName) + " ... skipping it.")
	
		# Now that we have all the infos, we can create the dataset object in the database
		datasetObj, _ = DataSet.objects.update_or_create(
			abbreviation = infos['abb'],
			defaults = {
				'name': infos['name'],
				'category': infos['cat'],
				'seriesNumber': infos['series'],
				'description': infos['description'],
				'requiredCitations': infos['citations'],
				'selectedStudies': infos['studies'],
				'publicationDate': infos['publication_date'], 
				'modificationDate': timezone.now()})

		# We add the tags, creating them in the database if needed
		for tag in infos["tags"]:
			tag_obj, _ = DataTag.objects.get_or_create(
					name = tag,
					defaults = {
						'description': 'No description provided.',
						'parent': None
					}
				)
			datasetObj.tags.add(tag_obj)
		datasetObj.save()

		# We create a folder for the dataset in the data folder
		try:
			os.makedirs(os.path.join(dataDir, infos['cat'], infos['abb']))
		except FileExistsError as e:
			pass

		# We create the 'img' folder in the previously created folder, this folder
		# will contain all the visializations of the datafiles 
		try:
			os.makedirs(os.path.join(dataDir, infos['cat'], infos['abb'], 'img'))
		except FileExistsError as e:
			pass

		# Let's now add the datafiles to the database
		for fileName in os.listdir(tmpDir):
			# We only do it if it actually is a file we're interested in
			if isAChoice(DATATYPES, os.path.splitext(fileName)[1][1:]):     # Using [1:] here to remove the dot

				# Move the file to the folder of the dataset
				os.rename(os.path.join(tmpDir, fileName), os.path.join(dataDir, infos['cat'], infos['abb'], fileName))
				
				# Looking through the infos we collected to see if the file appears there
				file_info = infos['files'].get(fileName)
				# If not, we proceed with default values and raise a warning
				if not file_info:
					file_info = {
						'patch_number': os.path.splitext(fileName)[0].split('-')[-1],
						'file_name': fileName,
						'modification_type': '-',
						'publication_date': timezone.now(),
					}

					log.append("</li>\n</ul>\n<p><strong>No info has been found for the file " + str(fileName) + 
						" in the info file of " + str(zipfileName) + "</strong></p>\n<ul>")

				# Same for the path the file belongs to
				patch_info = infos['patches'].get(file_info['patch_number'])
				if not patch_info:
					patch_info = {
						'patch_name': os.path.splitext(fileName)[0],
						'description': '-',
						'series_number': os.path.splitext(fileName)[0].split('-')[-1],
						'representative': None,
						'publication_date': timezone.now(),
					}

					log.append("</li>\n</ul>\n<p><strong>No info has been found for the patch " + 
						str(file_info['patch_number']) + " in the info file of " + str(zipfileName) + 
						"</strong></p>\n<ul>")

				# We get of create the datapatch object containing the datafile
				dataPatchObj, _ = DataPatch.objects.update_or_create(
					dataSet = datasetObj,
					seriesNumber = file_info['patch_number'],
					defaults = {
						"name": patch_info['patch_name'],
						"description": patch_info['description'],
						"publicationDate": patch_info['publication_date'],
						"modificationDate": timezone.now()})

				# We can finally create (or update) the datafile object in the database
				dataFileObj, _ = DataFile.objects.update_or_create(
					fileName = fileName,
					defaults = {
						"dataPatch": dataPatchObj,
						"dataType": os.path.splitext(fileName)[1][1:],
						"modificationType": file_info['modification_type'],
						"fileSize": file_info['size'],
						"publicationDate": file_info['publication_date'],
						"modificationDate": timezone.now()})

				# We add the representative of the datapatch if needed
				if fileName == patch_info['representative']:
					dataPatchObj.representative = dataFileObj
					dataPatchObj.save()

		# Finally, we remove the zip file from the datatoadd directory since everything went well
		os.remove(os.path.join(dataToAddDir, zipfileName))