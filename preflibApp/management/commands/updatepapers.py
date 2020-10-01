from django.core.management.base import BaseCommand
from django.contrib.staticfiles import finders
from django.db.models import Max
from django.core import management
from django.apps import apps
from datetime import datetime
from copy import deepcopy

import os
import re
import time
import traceback

class Command(BaseCommand):
	help = "Update the papers in the database according to the bib file in the static directory"

	def handle(self, *args, **options):

		try:
			Log = apps.get_model("preflibApp", "Log")
			newLogNum = Log.objects.filter(logType = "papers").aggregate(Max('logNum'))['logNum__max']
			if newLogNum == None:
				newLogNum = 0
			else:
				newLogNum += 1

			Paper = apps.get_model("preflibApp", "Paper")

			log = ["<h4> Updating the list of papers #" + str(newLogNum) + " - " + str(datetime.now()) + "</h4>\n"]

			Paper.objects.all().delete()
			log.append("<p>All previous papers deleted.</p>\n")

			file = open(finders.find("papers.bib"), "r")
			log.append("<p>Reading bib file</p>\n<ul>\n")

			fieldRegex = re.compile(r'\b(?P<key>\w+)={(?P<value>[^}]+)}')
			nameRegex = re.compile(r'@article{(?P<name>.+),')
			
			readingPaper = False
			inAt = False
			paperBlock = ""
			numPar = 0
			for line in file.readlines():
				for char in line:
					if char == '@':
						readingPaper = True
						inAt = True
					elif char == '{':
						inAt = False
						numPar += 1
					elif char == '}':
						numPar -= 1
					if readingPaper:
						paperBlock += char
						if not inAt and numPar == 0:
							readingPaper = False

							paperDic = dict(fieldRegex.findall(paperBlock))
							paperDic["name"] = nameRegex.findall(paperBlock)[0]
							if "url" not in paperDic:
								paperDic["url"] = ""
							print(paperDic)
							paperObj = Paper.objects.create(
								name = paperDic["name"],
								title = paperDic["title"],
								authors = paperDic["author"],
								publisher = paperDic["journal"],
								year = paperDic["year"],
								url = paperDic["url"])
							paperObj.save()

							log.append("\t<li>Created entry for " + paperDic["name"] + "</li>\n")

							paperBlock = ""
			log.append("</ul>\n")
			file.close()
		except Exception as e:
			log.append("<p><strong>" + str(e) + "<br>\n" + str(traceback.format_exc()) + "</strong></p>")
			print(e)
			print(traceback.format_exc())
		finally:
			Log.objects.create(
				log = ''.join(log),
				logType = "papers", 
				logNum = newLogNum,
				publicationDate = datetime.now())