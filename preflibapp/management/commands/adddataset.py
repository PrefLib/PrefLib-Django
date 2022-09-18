from django.core.management.base import BaseCommand
from django.contrib.staticfiles import finders
from django.core import management
from django.db.models import Max

import preflibapp

from preflibapp.models import *

from preflibtools.instances.preflibinstance import OrdinalInstance, CategoricalInstance, MatchingInstance

import traceback
import zipfile
import os


def read_info_file(file_name):
    infos = {'files': {}}
    with open(file_name, 'r') as file:
        # We go line per line trying to match the beginning of the line to a known header tag
        lines = file.readlines()
        line_index = 0
        for line_index in range(len(lines)):
            line = lines[line_index]
            if len(line) > 1:
                if line.startswith('Name:'):
                    infos['name'] = line[5:].strip()
                elif line.startswith('Abbreviation:'):
                    infos['abb'] = line[13:].strip()
                elif line.startswith('Tags:'):
                    infos['tags'] = [tag.strip() for tag in line[5:].strip().split(',')]
                elif line.startswith('Series Number:'):
                    infos['series'] = line[14:].strip()
                elif line.startswith('Publication Date:'):
                    infos['publication_date'] = line[17:].strip()
                elif line.startswith('Description:'):
                    infos['description'] = line[12:].strip()
                elif line.startswith('Required Citations:'):
                    infos['citations'] = line[19:].strip() if line[19:].strip() != "None" else ""
                elif line.startswith('Selected Studies:'):
                    infos['studies'] = line[17:].strip() if line[17:].strip() != "None" else ""
                elif line.startswith('file_name, modification_type, relates_to, title, description, publication_date'):
                    break
        # We are now reading the description of the files
        for line in lines[line_index + 1:]:
            line = line.strip()
            if len(line) > 0:
                split_line = line.split(',')
                new_split_line = []
                inside_quotes = False
                tmp_split = ''
                for split in split_line:
                    split = split.strip()
                    if len(split) > 0:
                        if inside_quotes:
                            if split[-1] == "'":
                                tmp_split += split[:-1]
                                new_split_line.append(tmp_split)
                                inside_quotes = False
                            else:
                                tmp_split += split + ', '
                        else:
                            if split[0] == "'":
                                tmp_split += split[1:] + ', '
                                inside_quotes = True
                            else:
                                new_split_line.append(split)
                    else:
                        new_split_line.append('')
                infos['files'][new_split_line[0].strip()] = {
                    'file_name': new_split_line[0].strip(),
                    'modification_type': new_split_line[1].strip(),
                    'relates_to': new_split_line[2].strip(),
                    'title': new_split_line[3].strip(),
                    'description': new_split_line[4].strip(),
                    'publication_date': new_split_line[5].strip()
                }
    return infos


def add_dataset(file_path, tmp_dir, data_dir, keepzip, log):
    # We start by extracting the zip file
    with zipfile.ZipFile(file_path, 'r') as archive:
        archive.extractall(tmp_dir)

    # We try to read and parse the info file, if we don't find the info.txt file, we skip the dataset
    if os.path.exists(os.path.join(tmp_dir, "info.txt")):
        infos = read_info_file(os.path.join(tmp_dir, "info.txt"))
    else:
        raise Exception("No info.txt file has been found for " + str(file_path) + " ... skipping it.")

    # Now that we have all the infos, we can create the dataset object in the database
    dataset_obj, _ = DataSet.objects.update_or_create(
        abbreviation=infos['abb'],
        defaults={
            'name': infos['name'],
            'series_number': infos['series'],
            'zip_file_path': None,
            'zip_file_size': 0,
            'description': infos['description'],
            'required_citations': infos['citations'],
            'selected_studies': infos['studies'],
            'publication_date': infos['publication_date']})

    # We add the tags, creating them in the database if needed
    for tag in infos["tags"]:
        tag_obj, _ = DataTag.objects.get_or_create(
            name=tag,
            defaults={
                'description': 'No description provided.',
                'parent': None
            }
        )
        dataset_obj.tags.add(tag_obj)
    dataset_obj.save()

    # We create a folder for the dataset in the data folder
    try:
        os.makedirs(os.path.join(data_dir, infos['abb']))
    except FileExistsError:
        pass
    if os.path.exists(os.path.join(data_dir, infos['abb'], "info.txt")):
        os.remove(os.path.join(data_dir, infos['abb'], "info.txt"))
    os.rename(os.path.join(tmp_dir, "info.txt"), os.path.join(data_dir, infos['abb'], "info.txt"))

    # Let's now add the datafiles to the database
    relates_to_dict = {}
    for file_name in os.listdir(tmp_dir):
        extension  = os.path.splitext(file_name)[1][1:] # Using [1:] here to remove the dot

        # We only do it if it actually is a file we're interested in
        if is_choice(DATATYPES, extension):
            print("\t{}".format(file_name))

            # Move the file to the folder of the dataset
            if os.path.exists(os.path.join(data_dir, infos['abb'], file_name)):
                os.remove(os.path.join(data_dir, infos['abb'], file_name))
            os.rename(os.path.join(tmp_dir, file_name), os.path.join(data_dir, infos['abb'], file_name))

            # Parsing the parsable files or looking through the infos we collected to see if the file appears there
            if extension in ["soc", "soi", "toc", "toi", "cat", "wmd"]:
                if extension == "cat":
                    instance = CategoricalInstance(os.path.join(data_dir, infos['abb'], file_name))
                elif extension == "wmd":
                    instance = MatchingInstance(os.path.join(data_dir, infos['abb'], file_name))
                else:
                    instance = OrdinalInstance(os.path.join(data_dir, infos['abb'], file_name))
                file_info = {
                    'modification_type': instance.modification_type,
                    'title': instance.title,
                    'description': instance.description,
                    'relates_to': instance.relates_to,
                    'publication_date': instance.publication_date,
                }
            else:
                file_info = infos['files'].get(file_name)
            if not file_info:
                file_info = {
                    'modification_type': '-',
                    'title': '',
                    'description': '-',
                    'relates_to': '',
                    'publication_date': timezone.now(),
                }
                print("No info found for {}".format(file_name))
                log.append("</li>\n</ul>\n<p><strong>No info has been found for the file " + str(file_name) +
                           " in the info file of " + str(file_path) + "</strong></p>\n<ul>")



            # We can finally create (or update) the datafile object in the database
            datafile_obj, _ = DataFile.objects.update_or_create(
                file_name=file_name,
                defaults={
                    "dataset": dataset_obj,
                    "data_type": os.path.splitext(file_name)[1][1:],
                    "modification_type": file_info['modification_type'],
                    "title": file_info['title'],
                    "description": file_info['description'],
                    "file_path": 'data/{}/{}'.format(infos['abb'], file_name),
                    "file_size": os.path.getsize(os.path.join(data_dir, infos['abb'], file_name)),
                    "publication_date": file_info['publication_date']})

            if file_info['relates_to']:
                relates_to_dict[datafile_obj] = file_info['relates_to']

    for datafile, relates_to_name in relates_to_dict.items():
        related_file = DataFile.objects.get(file_name=relates_to_name)
        datafile.relates_to = related_file
        datafile.save()

    # Finally, we remove the zip file from the datatoadd directory since everything went well
    if not keepzip:
        os.remove(file_path)


class Command(BaseCommand):
    help = "Add datasets to database"

    def add_arguments(self, parser):
        parser.add_argument('-d', nargs='*', type=str)
        parser.add_argument('-f', nargs='*', type=str)
        parser.add_argument('--all', action='store_true')
        parser.add_argument('--keepzip', action='store_true')

    def handle(self, *args, **options):
        if not options['d'] and not options['f']:
            print("ERROR: you need to pass an input argument: either -d for a directory of -f for a single file.")
            return
        if options['f']:
            for file_path in options['f']:
                if os.path.splitext(file_path)[1] != ".zip":
                    print("ERROR: the argument -f should point to a zip file, and {} does not look like one.".format(
                        file_path))
                    return
        if options['d']:
            for dir_path in options['d']:
                if not os.path.isdir(dir_path):
                    print("ERROR: the argument -d should point to a directory, and {} does not look like one.".format(
                        dir_path))
                    return

        log = []
        new_log_num = 0

        try:
            # Initializing the log
            new_log_num = Log.objects.filter(log_type="add_dataset").aggregate(Max('log_num'))['log_num__max']
            if new_log_num is None:
                new_log_num = 0
            else:
                new_log_num += 1

            # Looking for the data folder, creating it if it's not there
            data_dir = finders.find("data")
            if not data_dir:
                try:
                    data_dir = os.path.join(os.path.dirname(preflibapp.__file__), "static", "data")
                    os.makedirs(data_dir)
                except FileExistsError:
                    pass

            # Creating a tmp folder to extract the zip in
            tmp_dir = "adddataset_tmp"
            try:
                os.makedirs(tmp_dir)
            except FileExistsError:
                pass

            # Starting the log
            log = ["<h4> Adding dataset #" + str(new_log_num) + " - " + str(timezone.now()) + "</h4>\n",
                   "<ul>\n\t<li>args : " + str(args) + "</li>\n\t<li>options : " + str(options) +
                   "</li>\n</ul>\n"]

            # If the option 'all' has been passed, we add all the datasets in the datatoadd folder
            # to the 'file' option
            if options['d']:
                if not options['f']:
                    options['f'] = []
                for dir_path in options['d']:
                    for filename in os.listdir(dir_path):
                        if filename.endswith(".zip"):
                            options['f'].append(os.path.join(dir_path, filename))

            # Starting the real stuff
            log.append("<p>Adding datasets</p>\n<ul>\n")
            start_time = timezone.now()
            for file_path in options['f']:
                # We only consider zip files
                if os.path.splitext(file_path)[1] == '.zip':
                    # Let's work on the dataset
                    file_name = os.path.basename(file_path)
                    print("Adding dataset " + str(file_name))
                    log.append("\n\t<li>Dataset " + str(file_name) + "... ")
                    try:
                        # Actually adding the dataset
                        add_dataset(file_path, tmp_dir, data_dir, options['keepzip'], log)
                        log.append(" ... done.</li>\n")
                    except Exception as e:
                        # If something happened, we log it and move on
                        log.append("</li>\n</ul>\n<p><strong>" + str(e) + "<br>\n" + str(traceback.format_exc()) +
                                   "	</strong></p>\n<ul>")
                        print(traceback.format_exc())
                        print(e)
                    finally:
                        # In any cases, we delete all the temporary stuff we have created
                        for file in os.listdir(tmp_dir):
                            os.remove(os.path.join(tmp_dir, file))

            # Removing the tmp folder
            os.rmdir(tmp_dir)

            # Finalizing the log
            log.append("</ul>\n<p>The datasets have been successfully added in ")
            log.append(str((timezone.now() - start_time).total_seconds() / 60))
            log.append(" minutes.</p>")

            # Collecting the statics once everything has been done
            print("Finished, collecting statics")
            management.call_command("collectstatic", no_input=False)
        except Exception as e:
            # If anything happened during the execution, we log it and move on
            log.append("\n<p><strong>" + str(e) + "<br>\n" + str(traceback.format_exc()) + "</strong></p>")
            print(traceback.format_exc())
            print(e)
        finally:
            # In any cases, we save the log
            Log.objects.create(
                log=''.join(log),
                log_type="add_dataset",
                log_num=new_log_num,
                publication_date=timezone.now())
