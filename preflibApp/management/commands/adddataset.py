from itertools import permutations, combinations, combinations_with_replacement
from django.core.management.base import BaseCommand
from django.contrib.staticfiles import finders
from django.core import management
from django.conf import settings
from django.db.models import Max
from datetime import datetime
from django.apps import apps

from preflibApp.choices import *

import os
import zipfile
import time
import traceback

class Command(BaseCommand):
	help = "Add datasets to database"

	def add_arguments(self, parser):
		parser.add_argument('--file', nargs = '*', type = str)
		parser.add_argument('--all', action='store_true')

	def handle(self, *args, **options):
		dataToAddDir = finders.find("datatoadd")
		if not dataToAddDir:
			print("The folder datatoadd was not found, no dataset has been added.")
			return 
		lock = open(os.path.join(dataToAddDir, "dataset.lock"), "w")
		lock.close()

		try:
			Log = apps.get_model("preflibApp", "Log")
			newLogNum = Log.objects.filter(logType = "dataset").aggregate(Max('logNum'))['logNum__max']
			if newLogNum == None:
				newLogNum = 0
			else:
				newLogNum += 1

			dataDir = finders.find("data")
			if not dataDir:
				try:
					os.makedirs(dataToAddDir[0:-9] + "data")
					dataDir = dataToAddDir[0:-9] + "data"
				except Exception as e:
					pass
			tmpDir = os.path.join(dataToAddDir, "tmp")
			DataSet = apps.get_model("preflibApp", "Dataset")
			DataPatch = apps.get_model("preflibApp", "DataPatch")
			DataFile = apps.get_model("preflibApp", "DataFile")

			try:
				os.makedirs(tmpDir)
			except Exception as e:
				pass

			log = ["<h4> Adding dataset #" + str(newLogNum) + " - " + str(datetime.now()) + "</h4>\n"]
			log.append("<ul>\n\t<li>args : " + str(args) + "</li>\n\t<li>options : " + str(options) + 
				"</li>\n</ul>\n")

			if options['all']:
				options['file'] = []
				for filename in os.listdir(dataToAddDir):
					if filename.endswith(".zip"):
						options['file'].append(str(filename))

			log.append("<p>Adding datasets</p>\n<ul>\n")
			startTime = time.time()
			for fileName in options['file']:
				if fileName.endswith('.zip'):
					fileName = fileName.split(os.path.sep)[-1]
					print("Dataset " + str(fileName))
					log.append("\n\t<li>Dataset " + str(fileName) + "... ")
					try:
						self.addDataset(tmpDir, dataToAddDir, dataDir, fileName, DataSet, DataPatch, DataFile, log)
						log.append(" ... done.</li>\n")
					except Exception as e:
						log.append("</li>\n</ul>\n<p><strong>" + str(e) + "<br>\n" + str(traceback.format_exc()) + 
						"	</strong></p>\n<ul>")
					finally:
						for fileName in os.listdir(tmpDir):
							os.remove(os.path.join(tmpDir, fileName))
			os.rmdir(tmpDir)
			log.append("</ul>\n<p>The datasets have been successfully added in " + str(time.time() - startTime))
			log.append(" seconds.</p>")
			
			print("Finished, collecting statics")
			management.call_command("collectstatic", no_input = False)
		except Exception as e:
			log.append("\n<p><strong>" + str(e) + "<br>\n" + str(traceback.format_exc()) + "</strong></p>")
			print(traceback.format_exc())
			print(e)
		finally:
			os.remove(os.path.join(dataToAddDir, "dataset.lock"))
			Log.objects.create(
				log = ''.join(log),
				logType = "dataset", 
				logNum = newLogNum,
				publicationDate = datetime.now())

	def readInfoFile(self, fileName, tmpDir, Dataset):
		infos = {"datafiles": []}
		file = open(fileName, 'r')
		for line in file.readlines():
			if len(line) > 1:
				if line.startswith('Name:'):
					infos['name'] = line[5:].strip()
				elif line.startswith('Abbreviation:'):
					infos['abb'] = line[13:].strip()
				elif line.startswith('Extension:'):
					infos['ext'] = line[10:].strip()
				elif line.startswith('Series Number:'):
					infos['series'] = line[14:].strip()
				elif line.startswith('Description:'):
					infos['descr'] = line[12:].strip()
				elif line.startswith('Required Citations:'):
					infos['cite'] = line[19:].strip()
				elif line.startswith('Selected Studies:'):
					infos['studies'] = line[17:].strip()
				elif line.startswith('description,status,file_name') or line.startswith('Path:'):
					pass
				else:
					tmp = {}
					tmpline = line.split(',')
					tmp['descr'] = tmpline[0].strip()
					tmp['status'] = tmpline[1].strip()
					tmp['fileName'] = tmpline[2].strip()
					try:
						tmp['size'] = os.path.getsize(os.path.join(tmpDir, tmpline[2].strip()))
					except:
						tmp['size'] = 0
					infos["datafiles"].append(tmp)
		file.close()
		return infos

	def addDataset(self, tmpDir, dataToAddDir, dataDir, zipfileName, Dataset, DataPatch, DataFile, log):
		with zipfile.ZipFile(os.path.join(dataToAddDir, zipfileName), 'r') as archive:
			archive.extractall(tmpDir)

		infos = None
		for fileName in os.listdir(tmpDir):
			if fileName == "info.txt":
				infos = self.readInfoFile(os.path.join(tmpDir, fileName), tmpDir, Dataset)
				os.remove(os.path.join(tmpDir, fileName))
				break
		if infos == None:
			raise Exception("No info.txt file has been found for " + str(zipfileName) + " ... skipping it.")
		
		datasetObj = Dataset.objects.update_or_create(
			extension = infos['ext'],
			seriesNumber = infos['series'],
			defaults = {
				'name': infos['name'],
				'abbreviation': infos['abb'],
				'description': infos['descr'],
				'requiredCitations': infos['cite'],
				'selectedStudies': infos['studies'], 
				'modificationDate': datetime.now()})
		try:
			os.makedirs(os.path.join(dataDir, infos['ext'], infos['abb'], 'img'))
		except Exception as e:
			pass
		try:
			os.makedirs(os.path.join(dataDir, infos['ext'], infos['abb']))
		except Exception as e:
			pass
		for fileName in os.listdir(tmpDir):
			if fileName.split('.')[-1] in ['toi', 'toc', 'soi', 'soc', 'tog', 'mjg', 'wmg', 
				'pwg', 'wmd', 'dat', 'csv']:
				os.rename(os.path.join(tmpDir, fileName), os.path.join(dataDir, infos['ext'], infos['abb'], fileName))
				infoFile = None
				for i in infos["datafiles"]:
					if i['fileName'] == fileName:
						infoFile = i
						break
				if infoFile == None:
					infoFile = {'descr': '-', 'status': '-', 
						'size': os.path.getsize(os.path.join(dataDir, infos['ext'], infos['abb'], fileName))}
					log.append("</li>\n</ul>\n<p><strong>No info has been for the file " + str(fileName) + 
						" in the info file of " + str(zipfileName) + "</strong></p>\n<ul>")

				dataPatchObj = DataPatch.objects.get_or_create(
					name = fileName.split('.')[0],
					dataSet = datasetObj[0],
					seriesNumber = fileName.split('.')[0].split('-')[-1],
					defaults = {
						"description": infoFile['descr'],
						"modificationDate": datetime.now()})
				dataFileObj = DataFile.objects.update_or_create(
					dataPatch = dataPatchObj[0],
					fileName = fileName,
					defaults = {
						"dataType": fileName.split('.')[-1],
						"modificationType": infoFile['status'],
						"fileSize": infoFile['size'],
						"modificationDate": datetime.now()})

		os.remove(os.path.join(dataToAddDir, zipfileName))