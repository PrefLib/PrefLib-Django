from django.urls import path, re_path

from . import views


app_name = 'preflibapp'
urlpatterns = [
    path('', views.main, name='main'),
    re_path(r'^format/?$', views.data_format, name='data-format'),

    re_path(r'^datasets/?$', views.all_datasets, name='all-datasets'),
    re_path(r'^dataset/(?P<dataset_num>[0-9]{5})/?$', views.dataset, name='dataset'),

    re_path(r'^data/search/?$', views.data_search, name="data-search"),

    re_path(r'^about/?$', views.about, name='about'),

    re_path(r'^tools/ivs/?$', views.tools_IVS, name='tools-IVS'),
    re_path(r'^tools/kdg/?$', views.tools_KDG, name='tools-KDG'),
    re_path(r'^tools/cris/?$', views.tools_CRIS, name='tools-CRIS'),

    re_path(r'^login/?$', views.user_login, name='login'),
    re_path(r'^logout/?$', views.user_logout, name='logout'),
]
