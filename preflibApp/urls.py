from django.urls import path, re_path

from . import views

from .choices import *

app_name = 'preflibapp'
urlpatterns = [
    path('', views.main, name = 'main'),
    re_path(r'^data[/]?$', views.data, name = 'data'),
    re_path(r'^data/format[/]?$', views.dataFormat, name = 'dataFormat'),
    re_path(r'^data/metadata[/]?$', views.dataMetadata, name = 'dataMetadata'),
    re_path(r'^data/(?P<dataextension>' + '|'.join(map(lambda x: x[0], DATASETEXTENSIONS)) + ')[/]?$', views.alldatasets, name = 'alldatasets'),
    re_path(r'^data/(?P<dataextension>' + '|'.join(map(lambda x: x[0], DATASETEXTENSIONS)) + ')/(?P<dataSetNum>[0-9]{5})[/]?$', views.dataset, name = 'dataset'),
    re_path(r'^data/(?P<dataextension>' + '|'.join(map(lambda x: x[0], DATASETEXTENSIONS)) + ')/(?P<dataSetNum>[0-9]{5})/(?P<dataPatchNum>[0-9]{8})[/]?$', views.datapatch, name = 'datapatch'),
    re_path(r'^data/types[/]?$', views.datatypes, name = 'datatypes'),
    re_path(r'^data/search[/]?$', views.dataSearch, name = "dataSearch"),

    re_path(r'^about[/]?$', views.about, name = 'about'),

    re_path(r'^papers[/]?$', views.papersView, name = 'papers'),

    re_path(r'^tools[/]?$', views.tools, name = 'tools'),
    re_path(r'^tools/ivs[/]?$', views.toolsIVS, name = 'toolsIVS'),
    re_path(r'^tools/kdg[/]?$', views.toolsKDG, name = 'toolsKDG'),
    re_path(r'^tools/cris[/]?$', views.toolsCRIS, name = 'toolsCRIS'),

    re_path(r'^archive[/]?$', views.archive, name = 'archive'),

    re_path(r'^login[/]?$', views.userLogin, name = 'login'),
    re_path(r'^logout[/]?$', views.userLogout, name = 'logout'),

    re_path(r'^admin[/]?$', views.admin, name = 'ownadmin'),
    re_path(r'^admin/newuser[/]?$', views.createUser, name = 'createUser'),
    re_path(r'^admin/news[/]?$', views.adminNews, name = 'adminNews'),
    re_path(r'^admin/paper[/]?$', views.adminPaper, name = 'adminPaper'),
    re_path(r'^admin/zip[/]?$', views.adminZip, name = 'adminZip'),
    re_path(r'^admin/log/(?P<logtype>zip|dataset)/(?P<lognum>[0-9]+)[/]?$', views.adminLog, name = 'adminLog'),
    re_path(r'^admin/addDataset[/]?$', views.adminAddDataset, name = 'adminAddDataset'),
]