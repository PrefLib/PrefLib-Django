from django.core.management.base import BaseCommand
from django.contrib.staticfiles import finders
from django.utils import timezone
from django.db.models import Max

from preflibapp.models import *

import traceback
import shutil
import os


class Command(BaseCommand):
    help = "Add datasets to database"

    def add_arguments(self, parser):
        parser.add_argument("--abb", nargs="*", type=str)
        parser.add_argument("--all", action="store_true")

    def handle(self, *args, **options):

        log = []
        new_log_num = 0

        try:
            # Initializing the log
            new_log_num = Log.objects.filter(log_type="del_dataset").aggregate(
                Max("log_num")
            )["log_num__max"]
            if new_log_num is None:
                new_log_num = 0
            else:
                new_log_num += 1

            # Starting the log
            log = [
                "<h4> Deleting dataset #"
                + str(new_log_num)
                + " - "
                + str(timezone.now())
                + "</h4>\n",
                "<ul>\n\t<li>args : "
                + str(args)
                + "</li>\n\t<li>options : "
                + str(options)
                + "</li>\n</ul>\n",
            ]

            # Looking for the data folder
            data_dir = finders.find("data")
            if not data_dir:
                log.append(
                    "\n<p><strong>There is no data folder in the static folder, that is weird...</strong></p>"
                )

            # Starting the real stuff
            log.append("<p>Deleting datasets</p>\n<ul>\n")
            start_time = timezone.now()

            if options["all"]:
                options["abb"] = DataSet.objects.values_list("abbreviation", flat=True)

            for abbreviation in options["abb"]:
                # Get the dataset
                dataset = DataSet.objects.get(abbreviation=abbreviation)

                # Delete the static files
                shutil.rmtree(os.path.join(data_dir, dataset.abbreviation))

                # Delete the DB entry
                dataset.delete()

                print("Dataset {} has been deleted".format(abbreviation))

            # Finalizing the log
            log.append("</ul>\n<p>The datasets have been successfully deleted in ")
            log.append(str((timezone.now() - start_time).total_seconds() / 60))
            log.append(" minutes.</p>")

        except Exception as e:
            # If anything happened during the execution, we log it and move on
            log.append(
                "\n<p><strong>"
                + str(e)
                + "<br>\n"
                + str(traceback.format_exc())
                + "</strong></p>"
            )
            print(traceback.format_exc())
            print(e)
        finally:
            Log.objects.create(
                log="".join(log),
                log_type="del_dataset",
                log_num=new_log_num,
                publication_date=timezone.now(),
            )
