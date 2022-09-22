import datetime

from django.contrib.auth import authenticate, login, logout
from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponseRedirect, Http404
from django.views.decorators.cache import cache_page
from django.db.models import Sum, Max, Min
from django.contrib.staticfiles import finders
from django.db.models.functions import Cast
from django.core.paginator import Paginator

from math import floor, ceil

import copy
import os

from .models import *
from .forms import *

# ========================
#   Auxiliary functions
# ========================

CACHE_TIME = 60 * 60 * 24


# Returns a nice paginator of the iterable for a give window size around the current page
def get_paginator(request, iterable, page_size=20, window_size=3, max_pages=15):
    paginator = Paginator(iterable, page_size)
    # Try to find the page number, default being 1
    try:
        page = int(request.GET.get('page'))
    except TypeError:
        page = 1

    # Get the page, automatically returning the first page if page is not a valid one
    paginated = paginator.get_page(page)
    # Compute pages before and after the current one
    if paginator.num_pages > max_pages + 1:
        pages_before = []
        if page - window_size > 1:
            pages_before.append(1)
        if page - window_size > 2:
            pages_before.append("...")
        for p in range(max(1, page - window_size), page):
            pages_before.append(p)
        pages_after = list(range(page + 1, min(page + window_size + 1, paginator.num_pages + 1)))
        if page + window_size < paginator.num_pages - 1:
            pages_after.append("...")
        if page + window_size < paginator.num_pages:
            pages_after.append(paginator.num_pages)
    else:
        # If there are few pages, we display them all
        pages_before = list(range(1, page))
        pages_after = list(range(page + 1, paginator.num_pages + 1))
    return paginator, paginated, page, pages_before, pages_after


# ============
#   Renderer  
# ============

def my_render(request, template, args=None):
    if args is None:
        args = {}
    args['loginNextUrl'] = request.get_full_path
    return render(request, template, args)


def error_render(request, template, status):
    args = dict([])
    return render(request, template, args, status=status)


def error_400_view(request, exception):
    return error_render(request, '400.html', 400)


def error_403_view(request, exception):
    return error_render(request, '403.html', 403)


def error_404_view(request, exception):
    return error_render(request, '404.html', 404)


def error_500_view(request):
    return error_render(request, '500.html', 500)


# =========
#   Views
# =========

@cache_page(CACHE_TIME)
def main(request):
    nb_dataset = DataSet.objects.count()
    nb_datafile = DataFile.objects.count()
    total_size = DataFile.objects.aggregate(Sum('file_size'))['file_size__sum']
    nb_datatype = DataFile.objects.values('data_type').distinct().count()

    (paginator, papers, page, pages_before, pages_after) = get_paginator(request, Paper.objects.all(), page_size=15)

    return my_render(request, os.path.join('preflib', 'index.html'), locals())


@cache_page(CACHE_TIME)
def data_format(request):
    all_tags = DataTag.objects.all()
    metadata_per_categories = [(c[1], Metadata.objects.filter(is_active=True, category=c[0])) for c in
                               METADATACATEGORIES]
    return my_render(request, os.path.join('preflib', 'data_format.html'), locals())


@cache_page(CACHE_TIME)
def all_datasets(request):
    tags = set()
    datasets = DataSet.objects.filter().order_by('name')
    dataset_info = []
    for ds in datasets:
        max_files_displayed = 7
        files = list(ds.files.filter(related_files__isnull=True))
        dataset_info.append({
            "ds": ds,
            "timestamp": (ds.publication_date - datetime.date(2000, 1, 1)).days,
            "files": files[:max_files_displayed],
            "num_files": len(files),
            "num_hidden_files": max(0, len(files) - max_files_displayed),
            "zip_file": ds.zip_file_path,
            "zip_file_size": ds.zip_file_size,
            "tags": ",".join(ds.tags.values_list('name', flat=True))
        })
        for tag in ds.tags.all():
            tags.add(tag)
    return my_render(request, os.path.join('preflib', 'dataset_all.html'), locals())


@cache_page(CACHE_TIME)
def dataset_view(request, dataset_num):
    dataset = get_object_or_404(DataSet, series_number=dataset_num)
    data_files = dataset.files.all()
    num_files = data_files.count()
    total_size = data_files.aggregate(Sum('file_size'))['file_size__sum']
    all_types = data_files.order_by('data_type').values_list('data_type').distinct()

    files_info = []
    for file in data_files:
        if file.relates_to is None:
            file_dict = {"f": file}
            # Getting the metadata value for each category
            meta_per_category = {}
            for prop in file.dataproperty_set.all():
                category_long_name = find_choice_value(METADATACATEGORIES, prop.metadata.category)
                if category_long_name in meta_per_category:
                    meta_per_category[category_long_name].append(prop)
                else:
                    meta_per_category[category_long_name] = [prop]
                if prop.metadata.short_name == "numAlt":
                    file_dict["num_alt"] = prop.typed_value()
                if prop.metadata.short_name == "numVot":
                    file_dict["num_vot"] = prop.typed_value()
            file_dict["meta_per_cat"] = meta_per_category
            # Getting the first few lines of the file
            meta_lines = []
            pref_lines = []
            global_index = 0
            meta_index = 1
            pref_index = 1
            with open(finders.find(file.file_path), "r", encoding="utf-8") as f:
                for line in f.readlines():
                    global_index += 1
                    if line.startswith('#'):
                        if meta_index is not None:
                            if meta_index <= 15:
                                meta_lines.append((global_index, line.strip()))
                                meta_index += 1
                            else:
                                meta_lines.append(("...", "..."))
                                meta_index = None
                    else:
                        if pref_index <= 10:
                            pref_lines.append((global_index, line.strip()))
                            pref_index += 1
                        else:
                            pref_lines.append(("...", "..."))
                            break
            lines = meta_lines + pref_lines
            file_dict["preview"] = lines
            files_info.append(file_dict)
    return my_render(request, os.path.join('preflib', 'dataset.html'), locals())


def data_search(request):
    print(request.POST)
    types = copy.deepcopy(DATATYPES)
    types.remove(('dat', 'extra data file'))
    types.remove(('csv', 'comma-separated values'))
    modification_types = MODIFICATIONTYPES
    metadatas = Metadata.objects.filter(is_active=True, is_displayed=True)

    metadata_slider_values = {}
    remove_metadata = []
    # We compute the max and min values of the slider for each metadata
    for m in metadatas:
        if m.search_widget == "range":
            props = DataProperty.objects.filter(metadata=m)
            if props.exists():
                props = props.annotate(float_value=Cast('value', models.FloatField()))
                max_value = ceil(props.aggregate(Max('float_value'))['float_value__max'])
                min_value = floor(props.aggregate(Min('float_value'))['float_value__min'])
                intermediate_value = floor((max_value - min_value) * 0.3) if max_value > 30 else floor(
                    (max_value - min_value) * 0.5)
                metadata_slider_values[m] = (min_value, intermediate_value, max_value)

                # If the min and max are equal, filtering on that metadata is useless so we remove it
                if max_value == min_value:
                    remove_metadata.append(m)
            else:
                remove_metadata.append(m)

    for m in remove_metadata:
        metadatas = metadatas.exclude(pk=m.pk)

    print(metadatas)

    # This is to save the POST data when we change to a different page of the results
    if request.method != 'POST' and 'page' in request.GET:
        if 'search_datafiles_POST' in request.session:
            request.POST = request.session['search_datafiles_POST']
            request.method = 'POST'

    all_files = DataFile.objects.filter(data_type__in=[t[0] for t in types])
    if request.method == 'POST':
        request.session['search_datafiles_POST'] = request.POST

        datatype_filter = [t[0] for t in types]
        for t in types:
            if request.POST.get(t[0] + 'selector') == "no":
                if t[0] in datatype_filter:
                    datatype_filter.remove(t[0])
            elif request.POST.get(t[0] + 'selector') == "yes":
                datatype_filter = [x for x in datatype_filter if x == t[0]]
        all_files = all_files.filter(data_type__in=datatype_filter)

        modiftype_filer = [mt[0] for mt in modification_types]
        for mt in modification_types:
            if request.POST.get(mt[0] + 'selector') == "no":
                if mt[0] in modiftype_filer:
                    modiftype_filer.remove(mt[0])
            elif request.POST.get(mt[0] + 'selector') == "yes":
                modiftype_filer = [x for x in modiftype_filer if x == mt[0]]
        all_files = all_files.filter(modification_type__in=modiftype_filer)

        for m in metadatas:
            if m.search_widget == "ternary":
                if request.POST.get(m.short_name + 'selector') == "no":
                    property_query = DataProperty.objects.filter(metadata=m, value=True)
                    all_files = all_files.exclude(dataproperty__in=models.Subquery(property_query.values('pk')))
                elif request.POST.get(m.short_name + 'selector') == "yes":
                    property_query = DataProperty.objects.filter(metadata=m, value=True)
                    all_files = all_files.filter(dataproperty__in=models.Subquery(property_query.values('pk')))

            elif m.search_widget == "range":
                print(m.short_name)
                property_query_min = DataProperty.objects.filter(metadata=m).annotate(
                    float_value=Cast('value', models.FloatField())).filter(
                        float_value__lt=float(request.POST.get(m.short_name + '_slider_value_min')))
                all_files = all_files.exclude(dataproperty__in=models.Subquery(property_query_min.values('pk')))
                property_query_max = DataProperty.objects.filter(metadata=m).annotate(
                    float_value=Cast('value', models.FloatField())).filter(
                        float_value__gt=float(request.POST.get(m.short_name + '_slider_value_max')))

                all_files = all_files.exclude(dataproperty__in=models.Subquery(property_query_max.values('pk')))

    all_files = all_files.order_by('file_name', 'data_type')
    (paginator, datafiles, page, pages_before, pages_after) = get_paginator(request, all_files, page_size=40)
    return my_render(request, os.path.join('preflib', 'datasearch.html'), locals())


# Tools views
@cache_page(CACHE_TIME)
def tools(request):
    return my_render(request, os.path.join('preflib', 'tools.html'))


# Tools views
@cache_page(CACHE_TIME)
def tools_IVS(request):
    return my_render(request, os.path.join('preflib', 'toolsivs.html'))


# Tools views
@cache_page(CACHE_TIME)
def tools_KDG(request):
    return my_render(request, os.path.join('preflib', 'toolskdg.html'))


# Tools views
@cache_page(CACHE_TIME)
def tools_CRIS(request):
    return my_render(request, os.path.join('preflib', 'toolscris.html'))


# Paper views
@cache_page(CACHE_TIME)
def papers(request):
    (paginator, papers, page, pages_before, pages_after) = get_paginator(request, Paper.objects.all(), page_size=30)
    return my_render(request, os.path.join('preflib', 'papers.html'), locals())


# User stuff
def user_login(request):
    print(request.POST)
    error = False
    # The variable that get the next page if there is one
    request_next = request.POST.get('next', request.GET.get('next', ''))
    if request.method == "POST":
        form = LoginForm(request.POST)
        if form.is_valid():
            # If the form is valid, try to authenticate the user
            username = form.cleaned_data["username"]
            password = form.cleaned_data["password"]
            user = authenticate(username=username, password=password)
            if user:
                # If the authentication is right, login the user and redirect to the next page if there is one
                login(request, user)
                if request_next:
                    return HttpResponseRedirect(request_next)
            else:
                # Else there have been an error during the login
                error = True
    else:
        form = LoginForm()
    return my_render(request, os.path.join('preflib', 'userlogin.html'), locals())


def user_logout(request):
    if not request.user.is_authenticated:
        raise Http404
    if request.user.is_authenticated:
        logout(request)
    return redirect('preflibapp:main')
