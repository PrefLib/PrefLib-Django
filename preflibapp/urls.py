from django.urls import re_path
from django_distill import distill_path, distill_re_path

from . import views
from .models import DataSet


def get_all_dataset_num():
    for ds in DataSet.objects.all():
        yield {'dataset_num': ds.series_number}


app_name = 'preflibapp'
urlpatterns = [
    distill_path('', views.main, name='main', distill_file='index.html'),
    distill_re_path(r'^format/?$', views.data_format, name='data-format', distill_file="format.html"),

    distill_re_path(r'^datasets/?$', views.all_datasets, name='all-datasets', distill_file="datasets.html"),
    distill_re_path(r'^dataset/(?P<dataset_num>[0-9]{5})/?$', views.dataset_view, name='dataset', distill_func=get_all_dataset_num),

    distill_re_path(r'^data/search/?$', views.data_search, name="data-search"),

    distill_re_path(r'^BoSc22/?$', views.boehmer_schaar, name="boehmer-schaar", distill_file="BoSc22.html"),

    distill_re_path(r'^tools/ivs/?$', views.tools_IVS, name='tools-IVS', distill_file="tools/ivs.html"),
    distill_re_path(r'^tools/kdg/?$', views.tools_KDG, name='tools-KDG', distill_file="tools/kdg.html"),
    distill_re_path(r'^tools/cris/?$', views.tools_CRIS, name='tools-CRIS', distill_file="tools/cris.html"),

    re_path(r'^login/?$', views.user_login, name='login'),
    re_path(r'^logout/?$', views.user_logout, name='logout'),
]
