from django.db import models
from django.contrib.auth.models import User

from pydoc import locate

from .choices import *


# ================================
#    Models related to the data  
# ================================

class DataTag(models.Model):
    name = models.CharField(max_length=30,
                            unique=True)
    description = models.TextField()
    parent = models.ForeignKey('DataTag',
                               on_delete=models.CASCADE,
                               null=True,
                               blank=True,
                               related_name="children")

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class DataSet(models.Model):
    name = models.CharField(max_length=1000)
    abbreviation = models.CharField(max_length=100,
                                    unique=True)
    category = models.CharField(choices=DATACATEGORY,
                                max_length=5)
    series_number = models.SlugField()
    description = models.TextField()
    tags = models.ManyToManyField(DataTag,
                                  blank=True)
    required_citations = models.TextField(blank=True,
                                          null=True)
    selected_studies = models.TextField()
    publication_date = models.DateField()
    modification_date = models.DateField(auto_now=True)

    def get_tag_list(self):
        return ', '.join([str(tag) for tag in self.tags.all()])

    class Meta:
        ordering = ('category', 'series_number')
        unique_together = ('category', 'series_number')

    def __str__(self):
        return self.category + "-" + self.series_number + " - " + self.name


class DataPatch(models.Model):
    dataset = models.ForeignKey(DataSet,
                                on_delete=models.CASCADE)
    series_number = models.SlugField()
    name = models.CharField(max_length=1000)
    description = models.CharField(max_length=1000)
    representative = models.ForeignKey("DataFile",
                                       on_delete=models.CASCADE,
                                       related_name="represents",
                                       blank=True,
                                       null=True)
    publication_date = models.DateField()
    modification_date = models.DateField(auto_now=True)

    class Meta:
        unique_together = ('dataset', 'series_number')
        ordering = ['name']

    def __str__(self):
        return self.name


class Metadata(models.Model):
    name = models.CharField(max_length=100,
                            unique=True)
    short_name = models.CharField(max_length=100,
                                  unique=True)
    category = models.CharField(choices=METADATACATEGORIES,
                                max_length=100)
    description = models.TextField()
    is_active = models.BooleanField()
    is_displayed = models.BooleanField()
    applies_to = models.CharField(max_length=1000)
    upper_bounds = models.ManyToManyField('self',
                                          symmetrical=False,
                                          related_name="upperBoundedBy",
                                          blank=True)
    inner_module = models.CharField(max_length=100)
    inner_function = models.CharField(max_length=100)
    inner_type = models.CharField(max_length=100)
    search_widget = models.CharField(choices=SEARCHWIDGETS,
                                     max_length=100)
    search_question = models.CharField(max_length=1000)
    search_res_name = models.CharField(max_length=100)
    order_priority = models.IntegerField()

    class Meta:
        ordering = ["order_priority", "name"]

    def applies_to_list(self):
        return self.applies_to.split(',')

    def __str__(self):
        return self.name


class DataFile(models.Model):
    datapatch = models.ForeignKey(DataPatch,
                                  on_delete=models.CASCADE)
    file_name = models.CharField(max_length=255,
                                 unique=True)
    data_type = models.CharField(choices=DATATYPES,
                                 max_length=5)
    metadatas = models.ManyToManyField(Metadata,
                                       through="DataProperty")
    modification_type = models.CharField(choices=MODIFICATIONTYPES,
                                         max_length=20)
    file_size = models.FloatField(default=0)
    image = models.CharField(max_length=1000, null=True)
    publication_date = models.DateField()
    modification_date = models.DateField(auto_now=True)

    class Meta:
        ordering = ['file_name']

    def short_name(self):
        return self.file_name.split('.')[0][3:]

    def __str__(self):
        return self.file_name


class DataProperty(models.Model):
    datafile = models.ForeignKey(DataFile,
                                 on_delete=models.CASCADE)
    metadata = models.ForeignKey(Metadata,
                                 on_delete=models.CASCADE)
    value = models.CharField(max_length=1000)

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
    name = models.CharField(max_length=50,
                            unique=True)
    title = models.CharField(max_length=1000)
    authors = models.CharField(max_length=1000)
    publisher = models.CharField(max_length=1000)
    year = models.IntegerField(default=0)
    url = models.URLField(max_length=1000)

    class Meta:
        ordering = ['-year', 'title']

    def __str__(self):
        return self.authors.split(' ')[1] + "_" + str(self.year)


# ==============================
#    Logs for the admin tasks   
# ==============================

class Log(models.Model):
    log = models.TextField()
    log_type = models.CharField(max_length=200)
    log_num = models.IntegerField(default=0)
    publication_date = models.DateTimeField()

    class Meta:
        ordering = ['-publication_date']
        unique_together = ('log_type', 'log_num')

    def __str__(self):
        return self.log_type + " #" + str(self.log_num) + " - " + str(self.publication_date)
