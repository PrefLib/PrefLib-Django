from django.core.management import BaseCommand

from preflibapp.models import DataSet
import yaml


class Command(BaseCommand):
    help = "Add datasets to database"

    def add_arguments(self, parser):
        parser.add_argument("--abb", nargs="*", type=str)
        parser.add_argument("-f", type=str)
        parser.add_argument("--all", action="store_true")

    def handle(self, *args, **options):
        if options["all"]:
            options["abb"] = DataSet.objects.values_list("abbreviation", flat=True)

        yml_data = []
        for abbreviation in options["abb"]:
            dataset = DataSet.objects.get(abbreviation=abbreviation)
            yml_data.append({
                "name": dataset.name,
                "abbreviation": dataset.abbreviation,
                "series_number": dataset.series_number,
                "description": dataset.description,
                "required_citations": dataset.required_citations,
                "selected_studies": dataset.selected_studies,
                "publication_date": dataset.publication_date,
                "modification_date": dataset.modification_date,
                "tags": [t.name for t in dataset.tags]
            })

        if not options["f"]:
            options["f"] = "dataset.yml"

        with open(options["f"], "w") as f:
            yaml.dump(yml_data, f, default_flow_style=False, sort_keys=False)
