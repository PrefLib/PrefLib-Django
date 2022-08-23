from django.core.management.base import BaseCommand
from django.contrib.staticfiles import finders
from django.utils import timezone
from django.db.models import Max

from preflibapp.models import *

import traceback
import re


class Command(BaseCommand):
    help = "Update the papers in the database according to the bib file in the static directory"

    def handle(self, *args, **options):

        log = []
        new_log_num = 0

        try:
            # Initializing a new log
            new_log_num = Log.objects.filter(log_type="papers").aggregate(Max('log_num'))['log_num__max']
            if new_log_num is None:
                new_log_num = 0
            else:
                new_log_num += 1

            # Starting the log
            log = ["<h4> Updating the list of papers #" + str(new_log_num) + " - " + str(timezone.now()) + "</h4>\n"]

            # We start by emptying the Paper table
            Paper.objects.all().delete()
            log.append("<p>All previous papers deleted.</p>\n")

            # We read the file papers.bib which contains all the papers that should appear in Preflib
            file = open(finders.find("papers.bib"), "r")
            log.append("<p>Reading bib file</p>\n<ul>\n")

            # Some regexpr that will be used to parse the bib file
            field_regex = re.compile(r'\b(?P<key>\w+)={(?P<value>[^}]+)}')
            name_regex = re.compile(r'@article{(?P<name>.+),')

            # Parsing the bib file
            reading_paper = False
            in_at = False
            paper_block = ""
            num_parenthesis = 0
            for line in file.readlines():
                for char in line:
                    if char == '@':
                        reading_paper = True
                        in_at = True
                    elif char == '{':
                        in_at = False
                        num_parenthesis += 1
                    elif char == '}':
                        num_parenthesis -= 1
                    if reading_paper:
                        paper_block += char
                        if not in_at and num_parenthesis == 0:
                            reading_paper = False

                            # We read a paper, let's add it to the database
                            paper_dict = dict(field_regex.findall(paper_block))
                            paper_dict["name"] = name_regex.findall(paper_block)[0]
                            if "url" not in paper_dict:
                                paper_dict["url"] = ""
                            print(paper_dict)
                            paper_obj, _ = Paper.objects.create(
                                name=paper_dict["name"],
                                title=paper_dict["title"],
                                authors=paper_dict["author"],
                                publisher=paper_dict["journal"],
                                year=paper_dict["year"],
                                url=paper_dict["url"])

                            log.append("\t<li>Created entry for " + paper_dict["name"] + "</li>\n")

                            paper_block = ""
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
                log=''.join(log),
                log_type="papers",
                log_num=new_log_num,
                publication_date=timezone.now())
