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
		parser.add_argument('-d', type = str, required = True)
		parser.add_argument('--abb', nargs = '*', type = str)
		parser.add_argument('--all', action = 'store_true')


	def handle(self, *args, **options):
		if not options['d']:
			print("ERROR: you need to pass a target directory as argument (with option -d path/to/your/dic).")
			return
		else:
			if not os.path.isdir(options['d']):
				print("ERROR: {} is not a directory.".format(options['d']))
				return

		if not options['all'] and not options['abb']:
			print("ERROR: you need to pass at least one dataset to write (with option --abb DATASET_ABBREVIATION) or the option --all.")
			return

		try:
			# Initializing the log
			newLogNum = Log.objects.filter(logType = "write_dataset").aggregate(Max('logNum'))['logNum__max']
			if newLogNum == None:
				newLogNum = 0
			else:
				newLogNum += 1

			# Starting the log
			log = ["<h4> Writing dataset #" + str(newLogNum) + " - " + str(timezone.now()) + "</h4>\n"]
			log.append("<ul>\n\t<li>args : " + str(args) + "</li>\n\t<li>options : " + str(options) + 
				"</li>\n</ul>\n")
			
			# Looking for the data folder
			data_dir = finders.find("data")
			if not data_dir:
				log.append("\n<p><strong>There is no data folder in the static folder, that is weird...</strong></p>")

			# Starting the real stuff
			log.append("<p>Deleting datasets</p>\n<ul>\n")
			startTime = timezone.now()

			if options['all']:
				options['abb'] = DataSet.objects.values_list('abbreviation', flat=True)
				print(options['abb'])

			for abbreviation in options['abb']:

				# Get the dataset
				dataset = DataSet.objects.get(abbreviation = abbreviation)

				# Creating the folder for the dataset, if it already exists, we delete the content
				ds_dir = os.path.join(options['d'], dataset.abbreviation)
				try:
					os.makedirs(ds_dir)
				except FileExistsError as e:
					shutil.rmtree(ds_dir)
					os.makedirs(ds_dir)

				# Write the info file
				self.write_info_file(dataset, ds_dir)

				# Copy the data files to the folder
				for data_patch in dataset.datapatch_set.all():
					for data_file in data_patch.datafile_set.all():
						shutil.copyfile(os.path.join(data_dir, dataset.category, dataset.abbreviation, 
							data_file.fileName), os.path.join(ds_dir, data_file.fileName))

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
				logType = "write_dataset", 
				logNum = newLogNum,
				publicationDate = timezone.now())

	def write_info_file(self, dataset, ds_dir):
		with open(os.path.join(ds_dir, "info.txt"), "w") as f:
			# File Header
			f.write("Name: {}\n\n".format(dataset.name))
			f.write("Abbreviation: {}\n\n".format(dataset.abbreviation))
			f.write("Category: {}\n\n".format(dataset.category))
			f.write("Tags: {}\n\n".format(dataset.get_tag_list()))
			f.write("Series Number: {}\n\n".format(dataset.seriesNumber))
			f.write("Publication Date: {}\n\n".format(dataset.publicationDate))
			f.write("Description: {}\n\n".format(dataset.description))
			f.write("Required Citations: {}\n\n".format(dataset.requiredCitations))
			f.write("Selected Studies: {}\n\n".format(dataset.selectedStudies))

			# Patch Section (Building the file section at the same time)
			f.write("patch_name, description, series_number, publication_date, representative\n")
			write_file_str = "\npatch_number, file_name, modification_type, publication_date\n"
			for data_patch in dataset.datapatch_set.all():
				f.write("{}, {}, {}, {}, {}\n".format(data_patch.name, data_patch.description, data_patch.seriesNumber, 
					data_patch.publicationDate, data_patch.representative.fileName))

				for data_file in data_patch.datafile_set.all():
					write_file_str += "{}, {}, {}, {}\n".format(data_patch.seriesNumber, data_file.fileName, 
						data_file.modificationType, data_file.publicationDate)
			
			# File Section
			f.write(write_file_str)

			f.close()
