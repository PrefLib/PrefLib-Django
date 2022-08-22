from django.core.management.base import BaseCommand
from django.contrib.staticfiles import finders
from django.utils import timezone
from django.db.models import Max

from preflibApp.choices import *
from preflibApp.models import *

import traceback
import shutil
import os

class Command(BaseCommand):
	help = "Add datasets to database"

	def add_arguments(self, parser):
		parser.add_argument('--abb', nargs = '*', type = str)
		parser.add_argument('--all', action = 'store_true')


	def handle(self, *args, **options):

		try:
			# Initializing the log
			newLogNum = Log.objects.filter(logType = "del_dataset").aggregate(Max('logNum'))['logNum__max']
			if newLogNum == None:
				newLogNum = 0
			else:
				newLogNum += 1

			# Starting the log
			log = ["<h4> Deleting dataset #" + str(newLogNum) + " - " + str(timezone.now()) + "</h4>\n"]
			log.append("<ul>\n\t<li>args : " + str(args) + "</li>\n\t<li>options : " + str(options) + 
				"</li>\n</ul>\n")

			# Looking for the data folder
			dataDir = finders.find("data")
			if not dataDir:
				log.append("\n<p><strong>There is no data folder in the static folder, that is weird...</strong></p>")

			# Starting the real stuff
			log.append("<p>Deleting datasets</p>\n<ul>\n")
			startTime = timezone.now()

			if options['all']:
				options['abb'] = DataSet.objects.values_list('abbreviation', flat=True)

			for abbreviation in options['abb']:
				# Get the dataset
				dataset = DataSet.objects.get(abbreviation = abbreviation)

				# Delete the static files
				shutil.rmtree(os.path.join(dataDir, dataset.category, dataset.abbreviation))

				# Delete the DB entry
				dataset.delete()

			# Finalizing the log
			log.append("</ul>\n<p>The datasets have been successfully deleted in ")
			log.append(str((timezone.now() - startTime).total_seconds() / 60))
			log.append(" minutes.</p>")

		except Exception as e:
			# If anything happened during the execution, we log it and move on
			log.append("\n<p><strong>" + str(e) + "<br>\n" + str(traceback.format_exc()) + "</strong></p>")
			print(traceback.format_exc())
			print(e)
		finally:
			Log.objects.create(
				log = ''.join(log),
				logType = "del_dataset", 
				logNum = newLogNum,
				publicationDate = timezone.now())