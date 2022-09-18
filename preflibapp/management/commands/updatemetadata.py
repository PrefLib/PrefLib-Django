from django.core.management.base import BaseCommand
from django.contrib.staticfiles import finders
from django.core import management
from django.db.models import Max, Count

import django

from preflibtools.instances.preflibinstance import get_parsed_instance
from preflibapp.models import *

from concurrent.futures import ProcessPoolExecutor

import importlib
import traceback


def update_dataprop(pk_log_meta):
    django.setup()
    datafile_pk, log, metadata = pk_log_meta
    datafile = DataFile.objects.get(pk=datafile_pk)
    log.append("\n\t<li>Data file " + str(datafile.file_name) + "... ")
    # Finding the actual file referred by the datafile and parsing it
    preflib_instance = get_parsed_instance(finders.find(datafile.file_path))
    if preflib_instance is not None:
        print("\nData file " + str(datafile.file_name) + "...")
        for m in metadata:
            if datafile.data_type in m.applies_to_list():
                # If the metadata applies to the datafile we compute its value and save it
                dataprop_obj, _ = DataProperty.objects.update_or_create(
                    datafile=datafile,
                    metadata=m,
                    defaults={
                        "value": getattr(importlib.import_module(m.inner_module), m.inner_function)(
                            preflib_instance)
                    })
                dataprop_obj.save()
    log.append(" ... done.</li>\n")


class Command(BaseCommand):
    help = "Update the metadata of the data file"

    def add_arguments(self, parser):
        parser.add_argument('--abb', nargs='*', type=str)
        parser.add_argument('--all', action='store_true')
        parser.add_argument('--meta', nargs='*', type=str)

    def handle(self, *args, **options):
        if not options['all'] and not options['abb']:
            print(
                "ERROR: you need to pass at least one dataset to write (with option --abb DATASET_ABBREVIATION) or "
                "the option --all.")
            return

        # Check if there is directory "data" exists in the statics
        data_dir = finders.find("data")
        if not data_dir:
            print("The folder data was not found, nothing has been done.")
            return

        log = []
        new_log_num = 0

        try:
            # Initialize a new log
            new_log_num = Log.objects.filter(log_type="metadata").aggregate(Max('log_num'))['log_num__max']
            if new_log_num is None:
                new_log_num = 0
            else:
                new_log_num += 1

            # Either the datasets have been specified or we run through all of them
            if options['all']:
                options['abb'] = DataSet.objects.values_list('abbreviation', flat=True)

            datafiles = DataFile.objects.filter(dataset__abbreviation__in=options["abb"]).annotate(num_props=Count('metadata')).order_by('num_props')

            metadata = Metadata.objects.filter(is_active=True)
            if options['meta']:
                metadata = metadata.filter(short_name__in=options['meta'])
                print("Only considering {}".format(options['meta']))

            # Starting the real stuff
            log = ["<h4> Updating the metadata #" + str(new_log_num) + " - " + str(timezone.now()) + "</h4>\n<p><ul>"]
            multiproc = False
            start_time = timezone.now()
            if multiproc:
                print("Starting the pool")
                pks_log_meta = [(df.pk, log, metadata) for df in datafiles]
                with ProcessPoolExecutor(initializer=django.setup) as executor:
                    futures = {executor.map(update_dataprop, pks_log_meta)}
                for f in futures:
                    pass
                print("Done with the pool")
            else:
                for datafile in datafiles:
                    update_dataprop((datafile.pk, log, metadata))

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
            # In any cases, we save the log
            Log.objects.create(
                log=''.join(log),
                log_type="metadata",
                log_num=new_log_num,
                publication_date=timezone.now())
