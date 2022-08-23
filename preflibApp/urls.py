from django.urls import path, re_path

from . import views

from .choices import *

app_name = 'preflibapp'
urlpatterns = [
    path('', views.main, name='main'),
    re_path(r'^data/?$', views.data, name='data'),
    re_path(r'^data/format/?$', views.data_format, name='dataFormat'),
    re_path(r'^data/metadata/?$', views.data_metadata, name='dataMetadata'),
    re_path(r'^data/(?P<data_category>' + '|'.join(map(lambda x: x[0], DATACATEGORY)) + ')[/]?$', views.all_datasets,
            name='alldatasets'),
    re_path(
        r'^data/(?P<data_category>' + '|'.join(map(lambda x: x[0], DATACATEGORY)) + ')/(?P<dataset_num>[0-9]{5})[/]?$',
        views.dataset, name='dataset'),
    re_path(r'^data/(?P<datacategory>' + '|'.join(
        map(lambda x: x[0], DATACATEGORY)) + ')/(?P<dataSetNum>[0-9]{5})/(?P<dataPatchNum>[0-9]{8})[/]?$',
            views.datapatch, name='datapatch'),
    re_path(r'^data/types/?$', views.datatypes, name='datatypes'),
    re_path(r'^data/search/?$', views.dataSearch, name="dataSearch"),

    re_path(r'^about/?$', views.about, name='about'),

    re_path(r'^tools/ivs/?$', views.toolsIVS, name='toolsIVS'),
    re_path(r'^tools/kdg/?$', views.toolsKDG, name='toolsKDG'),
    re_path(r'^tools/cris/?$', views.toolsCRIS, name='toolsCRIS'),

    re_path(r'^login/?$', views.userLogin, name='login'),
    re_path(r'^logout/?$', views.userLogout, name='logout'),

    re_path(r'^admin/?$', views.admin, name='ownadmin'),
    re_path(r'^admin/paper/?$', views.adminPaper, name='adminPaper'),
    re_path(r'^admin/zip/?$', views.adminZip, name='adminZip'),
    re_path(r'^admin/log/(?P<logtype>zip|dataset)/(?P<lognum>[0-9]+)/?$', views.adminLog, name='adminLog'),
    re_path(r'^admin/addDataset/?$', views.adminAddDataset, name='adminAddDataset'),
]
