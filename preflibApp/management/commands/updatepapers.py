from django.core.management.base import BaseCommand
from django.contrib.staticfiles import finders
from django.core import management
from django.utils import timezone
from django.db.models import Max
from django.apps import apps
from copy import deepcopy

from preflibApp.models import *

import traceback
import os
import re

class Command(BaseCommand):
	help = "Update the papers in the database according to the bib file in the static directory"

	def handle(self, *args, **options):

		try:
			# Initializing a new log
			newLogNum = Log.objects.filter(logType = "papers").aggregate(Max('logNum'))['logNum__max']
			if newLogNum == None:
				newLogNum = 0
			else:
				newLogNum += 1

			# Starting the log
			log = ["<h4> Updating the list of papers #" + str(newLogNum) + " - " + str(timezone.now()) + "</h4>\n"]

			# We start by emptying the Paper table
			Paper.objects.all().delete()
			log.append("<p>All previous papers deleted.</p>\n")

			# We read the file papers.bib which contains all the papers that should appear in Preflib
			file = open(finders.find("papers.bib"), "r")
			log.append("<p>Reading bib file</p>\n<ul>\n")

			# Some regexpr that will be used to parse the bib file
			fieldRegex = re.compile(r'\b(?P<key>\w+)={(?P<value>[^}]+)}')
			nameRegex = re.compile(r'@article{(?P<name>.+),')
			
			# Parsing the bib file
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

							# We read a paper, let's add it to the database
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

							log.append("\t<li>Created entry for " + paperDic["name"] + "</li>\n")

							paperBlock = ""
			# We close the log
			log.append("</ul>\n")
			file.close()

		except Exception as e:
			# If something happend, we log it and move on
			log.append("<p><strong>" + str(e) + "<br>\n" + str(traceback.format_exc()) + "</strong></p>")
			print(e)
			print(traceback.format_exc())
		finally:
			# In any cases we add the log to the database
			Log.objects.create(
				log = ''.join(log),
				logType = "papers", 
				logNum = newLogNum,
				publicationDate = timezone.now())