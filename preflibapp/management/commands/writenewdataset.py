from django.core.management.base import BaseCommand
from django.contrib.staticfiles import finders
from django.db.models import Max

import preflibapp

from preflibapp.models import *
from preflibtools.instances.preflibinstance import OrdinalInstance, MatchingInstance

import traceback
import shutil
import os


class Command(BaseCommand):
    help = "Add datasets to database"

    def add_arguments(self, parser):
        parser.add_argument("-d", type=str, required=True)
        parser.add_argument("--abb", nargs="*", type=str)
        parser.add_argument("--all", action="store_true")

    def handle(self, *args, **options):
        if not options["d"]:
            print(
                "ERROR: you need to pass a target directory as argument (with option -d path/to/your/dic)."
            )
            return
        else:
            if not os.path.isdir(options["d"]):
                print("ERROR: {} is not a directory.".format(options["d"]))
                return

        if not options["all"] and not options["abb"]:
            print(
                "ERROR: you need to pass at least one dataset to write (with option --abb DATASET_ABBREVIATION) or "
                "the option --all."
            )
            return

        log = []
        new_log_num = 0

        try:
            # Initializing the log
            new_log_num = Log.objects.filter(log_type="write_dataset").aggregate(
                Max("log_num")
            )["log_num__max"]
            if new_log_num is None:
                new_log_num = 0
            else:
                new_log_num += 1

            # Starting the log
            log = [
                "<h4> Writing dataset #"
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
            log.append("<p>Writing datasets</p>\n<ul>\n")
            start_time = timezone.now()

            if options["all"]:
                options["abb"] = DataSet.objects.values_list("abbreviation", flat=True)

            for abbreviation in options["abb"]:

                log.append("\t<li>{}</li>\n".format(abbreviation))

                # Get the dataset
                dataset = DataSet.objects.get(abbreviation=abbreviation)

                # Creating the folder for the dataset, if it already exists, we delete the content
                ds_dir = os.path.join(
                    options["d"],
                    "{} - {}".format(dataset.series_number, dataset.abbreviation),
                )
                try:
                    os.makedirs(ds_dir)
                except FileExistsError:
                    shutil.rmtree(ds_dir)
                    os.makedirs(ds_dir)

                # Write the info file
                self.write_info_file(dataset, ds_dir)

                # Writting the file
                for datafile in dataset.files.all():
                    self.write_datafile(datafile, ds_dir)

            # Finalizing the log
            log.append(
                "</ul>\n<p>The datasets have been successfully written. It took "
            )
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
                log_type="write_dataset",
                log_num=new_log_num,
                publication_date=timezone.now(),
            )

    @staticmethod
    def write_info_file(dataset, ds_dir):
        def escape_comas(string):
            if "," in string:
                return "'" + string + "'"
            return string

        with open(os.path.join(ds_dir, "info.txt"), "w") as f:
            # File Header
            f.write("Name: {}\n\n".format(dataset.name))
            f.write("Abbreviation: {}\n\n".format(dataset.abbreviation))
            f.write(
                "Tags: {}\n\n".format(
                    ", ".join([tag.name for tag in dataset.tags.all()])
                )
            )
            f.write("Series Number: {}\n\n".format(dataset.series_number))
            f.write("Publication Date: {}\n\n".format(dataset.publication_date))
            f.write("Description: {}\n\n".format(dataset.description))
            f.write("Required Citations: {}\n\n".format(dataset.required_citations))
            f.write("Selected Studies: {}\n\n".format(dataset.selected_studies))

            f.write(
                "file_name, modification_type, relates_to, title, description, publication_date\n"
            )
            for data_file in dataset.files.all():
                f.write(
                    "{}, {}, {}, {}, {}, {}\n".format(
                        data_file,
                        data_file.modification_type,
                        "" if data_file.relates_to is None else data_file.relates_to,
                        escape_comas(data_file.title),
                        escape_comas(data_file.description),
                        data_file.publication_date,
                    )
                )
            f.close()

    @staticmethod
    def write_datafile(datafile, ds_dir):
        if datafile.data_type in ["soc", "soi", "toc", "toi"]:
            instance = OrdinalInstance(
                os.path.join(
                    os.path.dirname(preflibapp.__file__), "static", datafile.file_path
                )
            )
        elif datafile.data_type == "wmd":
            instance = MatchingInstance(
                os.path.join(
                    os.path.dirname(preflibapp.__file__), "static", datafile.file_path
                )
            )
        else:
            shutil.copy(
                os.path.join(
                    os.path.dirname(preflibapp.__file__), "static", datafile.file_path
                ),
                os.path.join(ds_dir, datafile.file_name),
            )
            return
        instance.modification_type = datafile.modification_type
        if datafile.relates_to:
            instance.relates_to = datafile.relates_to.file_name
        if datafile.related_files.all():
            instance.related_files = ",".join(
                [df.file_name for df in datafile.related_files.all()]
            )
        instance.title = datafile.title
        instance.description = datafile.description
        instance.publication_date = str(datafile.publication_date)
        instance.modification_date = str(datafile.modification_date)
        instance.write(os.path.join(ds_dir, datafile.file_name))
