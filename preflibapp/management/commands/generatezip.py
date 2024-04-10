from django.core.management.base import BaseCommand
from django.contrib.staticfiles import finders
from django.core import management
from django.db.models import Max

from preflibapp.models import *

import traceback
import zipfile
import os


def zip_dataset(dataset, data_dir):
    # First locate the dataset folder
    ds_dir = os.path.join(data_dir, dataset.abbreviation)
    # Create the zip file for the dataset
    zipf = zipfile.ZipFile(os.path.join(ds_dir, dataset.abbreviation + ".zip"), "w", zipfile.ZIP_DEFLATED)

    # Add all the files to the zip archive
    for datafile in dataset.files.all():
        zipf.write(os.path.join(ds_dir, datafile.file_name), datafile.file_name)

    # Add the info.txt file to the archive
    zipf.write(os.path.join(ds_dir, "info.txt"), "info.txt")

    # Closing the archive
    zipf.close()

    data_dir_name = os.path.basename(os.path.normpath(data_dir))
    dataset.zip_file_path = os.path.join(data_dir_name, dataset.abbreviation, dataset.abbreviation + ".zip")
    dataset.zip_file_size = os.path.getsize(os.path.join(ds_dir, dataset.abbreviation + ".zip"))
    dataset.save()


def zip_type(data_type, data_dir):
    if data_type in ('dat',):
        return
    zipf = zipfile.ZipFile(os.path.join(data_dir, "types", data_type + ".zip"), "w", zipfile.ZIP_DEFLATED)
    for datafile in DataFile.objects.filter(data_type=data_type):
        zipf.write(os.path.join(os.path.dirname(data_dir), datafile.file_path), datafile.file_name)
    zipf.close()


class Command(BaseCommand):
    help = "Generate the zip files of the data"

    log = []
    new_log_num = 0

    def handle(self, *args, **options):
        # Finding the data dir in the static folder
        data_dir = finders.find("data")

        # Creating the lock
        lock = open(os.path.join(data_dir, "zip.lock"), "w")
        lock.close()

        log = []
        new_log_num = 0

        try:
            # Initializing a new log
            new_log_num = Log.objects.filter(log_type="zip").aggregate(Max('log_num'))['log_num__max']
            if new_log_num is None:
                new_log_num = 0
            else:
                new_log_num += 1

            # Starting the log
            log = ["<h4> Zipping log #" + str(new_log_num) + " - " + str(timezone.now()) + "</h4>\n"]
            start_time = timezone.now()

            # We start by zipping the data sets
            log.append("<p>Zipping data sets...</p>\n<ul>\n")
            for ds in DataSet.objects.all():
                print("Zipping dataset " + str(ds))
                log.append("\t<li>Zipping dataset " + str(ds) + "... ")
                zip_dataset(ds, data_dir)
                log.append(" ... done.</li>\n")
            log.append("</ul>\n<p>... done.</p>\n")

            # We will now zip the files per type, starting by creating the corresponding folder
            try:
                os.makedirs(os.path.join(data_dir, "types"))
            except OSError:
                pass

            # We actually zip the types
            log.append("\n<p>Zipping data files by type</p>\n<ul>\n")
            for data_type in DataFile.objects.order_by().values_list('data_type', flat=True).distinct():
                print("Zipping type " + data_type)
                log.append("\t<li>Zipping type " + data_type + "... ")
                zip_type(data_type, data_dir)
                log.append(" ... done.</li>\n")
            log.append("</ul>\n<p>... done.</p>\n")

            # We finish the log
            log.append("\n<p>Regeneration of the zip files successfully completed in ")
            log.append(str((timezone.now() - start_time).total_seconds() / 60) + " minutes</p>\n")

            # And finally collect the statics
            print("Finished, collecting statics")
            management.call_command("collectstatic", no_input=False)

        except Exception as e:
            # If anything happened, we log it and move on
            log.append("\n<p><strong>" + str(e) + "<br>\n" + str(traceback.format_exc()) + "</strong></p>")
            print(traceback.format_exc())
            print(e)

        finally:
            # In any cases we remove the lock and save the log
            os.remove(os.path.join(data_dir, "zip.lock"))
            Log.objects.create(
                log=''.join(log),
                log_type="zip",
                log_num=new_log_num,
                publication_date=timezone.now())
