from django.urls import path, re_path

from . import views

from .choices import *

app_name = 'preflibapp'
urlpatterns = [
    path('', views.main, name='main'),
    re_path(r'^data/?$', views.data, name='data'),
    re_path(r'^data/format/?$', views.data_format, name='data-format'),
    re_path(r'^data/metadata/?$', views.data_metadata, name='data-metadata'),
    re_path(r'^data/(?P<data_category>' + '|'.join(map(lambda x: x[0], DATACATEGORY)) + ')/?$', views.all_datasets,
            name='all-datasets'),
    re_path(
        r'^data/(?P<data_category>' + '|'.join(map(lambda x: x[0], DATACATEGORY)) + ')/(?P<dataset_num>[0-9]{5})/?$',
        views.dataset, name='dataset'),
    re_path(r'^data/(?P<data_category>' + '|'.join(
        map(lambda x: x[0], DATACATEGORY)) + ')/(?P<dataset_num>[0-9]{5})/(?P<datapatch_num>[0-9]{8})/?$',
            views.datapatch, name='datapatch'),
    re_path(r'^data/types/?$', views.datatypes, name='datatypes'),
    re_path(r'^data/search/?$', views.data_search, name="data-search"),

    re_path(r'^about/?$', views.about, name='about'),

    re_path(r'^tools/ivs/?$', views.tools_IVS, name='tools-IVS'),
    re_path(r'^tools/kdg/?$', views.tools_KDG, name='tools-KDG'),
    re_path(r'^tools/cris/?$', views.tools_CRIS, name='tools-CRIS'),

    re_path(r'^login/?$', views.user_login, name='login'),
    re_path(r'^logout/?$', views.user_logout, name='logout'),

    re_path(r'^admin/?$', views.admin, name='ownadmin'),
    re_path(r'^admin/paper/?$', views.admin_paper, name='admin-paper'),
    re_path(r'^admin/zip/?$', views.admin_zip, name='admin-zip'),
    re_path(r'^admin/log/(?P<log_type>zip|dataset)/(?P<log_num>[0-9]+)/?$', views.admin_log, name='admin-log'),
    re_path(r'^admin/addDataset/?$', views.admin_add_dataset, name='admin-add-dataset'),
]
