from django.core.management.base import BaseCommand
from django.contrib.staticfiles import finders
from django.core import management
from django.utils import timezone
from django.db.models import Max
from django.conf import settings
from random import shuffle

from preflibApp.preflibtools.instance import PreflibInstance
from preflibApp.models import *

import importlib
import traceback
import os


def update_dataprop(datafile, no_drawing=False):
    # Easy access to the dataset containing the datafile
    dataset = datafile.dataPatch.dataSet
    # Finding the actual file referred by the datafile and parsing it
    folder = finders.find(os.path.join("data", dataset.category, dataset.abbreviation))
    preflib_instance = PreflibInstance()
    preflib_instance.parse(os.path.join(folder, datafile.fileName))
    if not no_drawing:
        # Creating the image file for it
        try:
            os.makedirs(os.path.join(folder, 'img'))
        except OSError:
            pass
        preflib_instance.draw(os.path.join(folder, 'img', datafile.fileName.replace('.', '_') + '.png'))
        # NEXT LINE IS TERRIBLE!!!
        os.system(settings.CONVERT_PATH + " " + os.path.join(folder, 'img',
                                                             datafile.fileName.replace('.', '_') + '.png') +
                  " -trim " + os.path.join(folder, 'img', datafile.fileName.replace('.', '_') + '.png'))
        datafile.image = datafile.fileName.replace('.', '_') + '.png'
    datafile.save()
    # Selecting only the active metadata
    metadata = Metadata.objects.filter(isActive=True)
    for m in metadata:
        if datafile.dataType in m.getAppliesToList():
            # If the metadata applies to the datafile we compute its value and save it
            dataprop_obj, _ = DataProperty.objects.update_or_create(
                dataFile=datafile,
                metadata=m,
                defaults={
                    "value": getattr(importlib.import_module("preflibApp." + m.innerModule), m.innerFunction)(
                        preflib_instance)
                })
            dataprop_obj.save()


class Command(BaseCommand):
    help = "Update the metadata of the data file"

    def add_arguments(self, parser):
        parser.add_argument('--dataset', nargs='*', type=str)
        parser.add_argument('--noDrawing', action='store_true')

    def handle(self, *args, **options):
        # Check if there is directory "data" exists in the statics
        data_dir = finders.find("data")
        if not data_dir:
            print("The folder data was not found, nothing has been done.")
            return

        # Create a lock to avoid running the same procedure in parallel
        lock = open(os.path.join(data_dir, "metadata.lock"), "w")
        lock.close()

        log = []
        new_log_num = 0

        try:
            # Initialize a new log
            new_log_num = Log.objects.filter(logType="metadata").aggregate(Max('logNum'))['logNum__max']
            if new_log_num is None:
                new_log_num = 0
            else:
                new_log_num += 1

            # Either the datasets have been specified or we run through all of them
            if options["dataset"] is None:
                datafiles = list(DataFile.objects.all().order_by("fileName"))
                shuffle(datafiles)
            else:
                datafiles = DataFile.objects.filter(dataPatch__dataSet__abbreviation__in=options["dataset"]).order_by(
                    "fileName")

            # Starting the real stuff
            log = ["<h4> Updating the metadata #" + str(new_log_num) + " - " + str(timezone.now()) + "</h4>\n<p><ul>"]
            start_time = timezone.now()
            for dataFile in datafiles:
                print("\nData file " + str(dataFile.fileName) + "...")
                log.append("\n\t<li>Data file " + str(dataFile.fileName) + "... ")
                update_dataprop(dataFile, no_drawing=options['noDrawing'])
                log.append(" ... done.</li>\n")

            # Closing the log
            log.append("\n<p>Metadata updated in ")
            log.append(str((timezone.now() - start_time).total_seconds() / 60) + " minutes</p>\n")

            # Collecting statics at the end
            print("Finished, collecting statics")
            management.call_command("collectstatic", no_input=False)

        except Exception as e:
            # If an exception occured during runtime, we log it and continue
            log.append("\n</ul>\n<p><strong>" + str(e) + "<br>\n" + str(traceback.format_exc()) + "</strong></p>")
            print(traceback.format_exc())
            print("Exception " + str(e))

        finally:
            # In any cases, we remove the lock and save the log
            os.remove(os.path.join(data_dir, "metadata.lock"))
            Log.objects.create(
                log=''.join(log),
                logType="metadata",
                logNum=new_log_num,
                publicationDate=timezone.now())