from django.contrib.auth.models import User
from django.utils import timezone
from django.db import models

from pydoc import locate

from .choices import *


# ================================
#    Models related to the data
# ================================


class DataTag(models.Model):
    name = models.CharField(max_length=30, unique=True, verbose_name="name")
    description = models.TextField(verbose_name="Description of the tag")

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class DataSet(models.Model):
    name = models.CharField(max_length=50, unique=True, verbose_name="name")
    abbreviation = models.SlugField(
        max_length=30, unique=True, verbose_name="abbreviation of the dataset"
    )
    series_number = models.SlugField(
        unique=True, verbose_name="series number of the dataset"
    )
    zip_file_path = models.CharField(max_length=255, blank=True, null=True, unique=True)
    zip_file_size = models.FloatField(default=0)
    description = models.TextField(
        blank=True, verbose_name="description of the dataset"
    )
    tags = models.ManyToManyField(
        DataTag, blank=True, verbose_name="tags applying to the dataset"
    )
    required_citations = models.TextField(
        blank=True, verbose_name="HTML code describing the required citations"
    )
    selected_studies = models.TextField(blank=True)
    publication_date = models.DateField()
    modification_date = models.DateField()

    def save(self, *args, **kwargs):
        self.modification_date = timezone.now()
        return super(DataSet, self).save(*args, **kwargs)

    class Meta:
        ordering = ("series_number",)

    def __str__(self):
        return self.series_number + " - " + self.abbreviation


class Metadata(models.Model):
    name = models.CharField(max_length=100, unique=True)
    short_name = models.CharField(max_length=100, unique=True)
    category = models.CharField(choices=METADATACATEGORIES, max_length=100)
    description = models.TextField()
    is_active = models.BooleanField()
    is_displayed = models.BooleanField()
    applies_to = models.CharField(max_length=100)
    upper_bounds = models.ManyToManyField(
        "self", symmetrical=False, related_name="upperBoundedBy", blank=True
    )
    inner_module = models.CharField(max_length=100)
    inner_function = models.CharField(max_length=100)
    inner_type = models.CharField(max_length=100)
    search_widget = models.CharField(choices=SEARCHWIDGETS, max_length=100)
    search_question = models.TextField()
    search_res_name = models.CharField(max_length=100)
    order_priority = models.IntegerField()

    class Meta:
        ordering = ["order_priority", "name"]

    def applies_to_list(self):
        return self.applies_to.split(",")

    def __str__(self):
        return self.name


class DataFile(models.Model):
    dataset = models.ForeignKey(DataSet, on_delete=models.CASCADE, related_name="files")
    file_name = models.CharField(max_length=100, unique=True)
    data_type = models.CharField(choices=DATATYPES, max_length=5)
    metadata = models.ManyToManyField(
        Metadata, through="DataProperty", related_name="files"
    )
    modification_type = models.CharField(choices=MODIFICATIONTYPES, max_length=20)
    title = models.CharField(max_length=100, blank=True)
    description = models.TextField(blank=True)
    file_path = models.CharField(max_length=255, blank=True, unique=True)
    file_size = models.FloatField(default=0)
    relates_to = models.ForeignKey(
        "DataFile", on_delete=models.CASCADE, related_name="related_files", null=True
    )
    publication_date = models.DateField()
    modification_date = models.DateField()

    def save(self, *args, **kwargs):
        self.modification_date = timezone.now()
        return super(DataFile, self).save(*args, **kwargs)

    class Meta:
        ordering = ["file_name"]

    def short_name(self):
        return self.file_name.split(".")[0]

    def __str__(self):
        return self.file_name


class DataProperty(models.Model):
    datafile = models.ForeignKey(DataFile, on_delete=models.CASCADE)
    metadata = models.ForeignKey(Metadata, on_delete=models.CASCADE)
    value = models.CharField(max_length=100)

    def typed_value(self):
        if self.metadata.inner_type == "bool":
            return self.value == "True"
        return locate(self.metadata.inner_type)(self.value)

    class Meta:
        unique_together = ("datafile", "metadata")
        ordering = ("datafile", "metadata")

    def __str__(self):
        return self.datafile.__str__() + " - " + self.metadata.name


# ===================================
#    Papers that are using PrefLib
# ===================================


class Paper(models.Model):
    name = models.CharField(max_length=50, unique=True)
    title = models.TextField()
    authors = models.TextField()
    publisher = models.TextField()
    year = models.IntegerField(default=0)
    url = models.URLField(max_length=100)

    class Meta:
        ordering = ["-year", "title"]

    def __str__(self):
        return self.authors.split(" ")[1] + "_" + str(self.year)


# ==============================
#    Logs for the admin tasks
# ==============================


class Log(models.Model):
    log = models.TextField()
    log_type = models.CharField(max_length=50)
    log_num = models.IntegerField(default=0)
    publication_date = models.DateTimeField()

    class Meta:
        ordering = ["-publication_date"]
        unique_together = ("log_type", "log_num")

    def __str__(self):
        return (
            self.log_type
            + " #"
            + str(self.log_num)
            + " - "
            + str(self.publication_date)
        )
