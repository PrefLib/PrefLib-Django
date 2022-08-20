from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect, Http404
from django.views.decorators.cache import cache_page
from django.db.models import Sum, Max, Min, Count
from django.contrib.staticfiles import finders
from django.db.models.functions import Cast
from django.core.paginator import Paginator
from django.core import management
from django.utils import timezone

from django.conf import settings

from subprocess import Popen
from math import floor, ceil

import random
import copy
import os

from .models import *
from .forms import *
from .scripts import *
from .choices import *

# ========================
#   Auxiliary functions
# ========================

CACHE_TIME = 60 * 60 * 24

# Returns a nice paginator of the iterable for a give window size around the current page 
def getPaginator(request, iterable, pageSize = 20, windowSize = 3, maxNumberPages = 15):
	paginator = Paginator(iterable, pageSize)
	# Try to find the page number, default being 1
	try:
		page = int(request.GET.get('page'))
	except:
		page = 1
	# Check if the page is a valid one
	try:
		paginated = paginator.get_page(page)
	except PageNotAnInteger:
		paginated = paginator.page(1)
	except EmptyPage:
		paginated = paginator.page(paginator.num_pages)
	# Compute pages before and after the current one     
	if paginator.num_pages > maxNumberPages + 1:
		pagesBefore = []
		if page - windowSize > 1:
			pagesBefore.append(1)
		if page - windowSize > 2:
			pagesBefore.append("...")
		for p in range(max(1, page - windowSize), page):
			pagesBefore.append(p)
		pagesAfter = list(range(page + 1, min(page + windowSize + 1, paginator.num_pages + 1)))
		if page + windowSize < paginator.num_pages - 1:
			pagesAfter.append("...")
		if page + windowSize < paginator.num_pages:
			pagesAfter.append(paginator.num_pages)
	else:
		# If there are few pages, we display them all
		pagesBefore = list(range(1, page))
		pagesAfter = list(range(page + 1, paginator.num_pages + 1))
	return (paginator, paginated, page, pagesBefore, pagesAfter)

# ============
#   Renderer  
# ============

def my_render(request, template, args = dict([])):
	args['DATACATEGORY'] = DATACATEGORY
	args['DATATYPES'] = DATATYPES
	args['loginNextUrl'] = request.get_full_path
	return render(request, template, args)

def error_render(request, template, status):
	args = dict([])
	args['DATACATEGORY'] = DATACATEGORY
	args['DATATYPES'] = DATATYPES
	return render(request, template, args, status = status)

def error_400_view(request, exception):
	return error_render(request,'400.html', 400)

def error_403_view(request, exception):
	return error_render(request,'403.html', 403)

def error_404_view(request, exception):
	return error_render(request,'404.html', 404)

def error_500_view(request):
	return error_render(request,'500.html', 500)

# =========
#   Views
# =========

@cache_page(CACHE_TIME)
def main(request):
	nbDataSet = DataSet.objects.count()
	nbDataFile = DataFile.objects.count()
	totalSize = DataFile.objects.aggregate(Sum('fileSize'))['fileSize__sum']
	if totalSize != None:
		totalSize = round(totalSize / 1000000000, 2)
	nbDataType = DataFile.objects.values('dataType').distinct().count()
	
	filesWithImages = DataFile.objects.filter(image__isnull = False, dataType__in = ['soc', 'soi', 'toc', 'toi', 'tog', 'mjg', 'wmg', 'pwg', 'wmd'])
	if filesWithImages.exists():
		randomFileWithImage = random.choice(filesWithImages)
	
	(paginator, papers, page, pagesBefore, pagesAfter) = getPaginator(request, Paper.objects.all(), pageSize = 15)
	
	return my_render(request, os.path.join('preflib', 'index.html'), locals())

# Data views
@cache_page(CACHE_TIME)
def data(request):
	return my_render(request, os.path.join('preflib', 'data.html'))

@cache_page(CACHE_TIME)
def dataFormat(request):
	return my_render(request, os.path.join('preflib', 'dataformat.html'))

@cache_page(CACHE_TIME)
def dataMetadata(request):
	metadataPerCategories = [(c[1], Metadata.objects.filter(isActive = True, category = c[0])) for c in METADATACATEGORIES]
	return my_render(request, os.path.join('preflib', 'datametadata.html'), locals())

@cache_page(CACHE_TIME)
def alldatasets(request, datacategory):
	# (paginator, datasets, page, pagesBefore, pagesAfter) = getPaginator(request, DataSet.objects.filter(category = datacategory).order_by('name'))
	datasets = DataSet.objects.filter(category = datacategory).order_by('name')
	title = findChoiceValue(DATACATEGORY, datacategory)
	datasetInfo = []
	for dataset in datasets:
		patches = DataPatch.objects.filter(dataSet = dataset)
		zipFilePath = os.path.join('data', datacategory, str(dataset.abbreviation), str(dataset.abbreviation) + '.zip')
		staticDir = finders.find(zipFilePath)
		if staticDir != None:
			zipFileSize = os.path.getsize(staticDir)
		else:
			zipFileSize = 0
		show_how_many_patches = 7
		datasetInfo.append({
			"ds": dataset, 
			"patches": patches[:show_how_many_patches], 
			"nbPatches": patches.count(),
			"nbPatchesNotShown": max(0, patches.count() - show_how_many_patches),
			"zipFile": zipFilePath,
			"zipFileSize": zipFileSize
		})
	return my_render(request, os.path.join('preflib', 'datasetall.html'), locals())

@cache_page(CACHE_TIME)
def dataset(request, datacategory, dataSetNum):
	dataset = get_object_or_404(DataSet, category = datacategory, seriesNumber = dataSetNum)
	(paginator, patches, page, pagesBefore, pagesAfter) = getPaginator(request, DataPatch.objects.filter(dataSet = dataset).order_by("name"))
	number_alt_meta = Metadata.objects.get(shortName = "numAlt")
	number_vot_meta = Metadata.objects.get(shortName = "numVot")
	patch_num_vot_alt = {}
	for patch in patches:
		try:
			number_alt = DataProperty.objects.get(metadata = number_alt_meta, dataFile = patch.representative).getTypedValue()
			number_vot = DataProperty.objects.get(metadata = number_vot_meta, dataFile = patch.representative).getTypedValue()
			patch_num_vot_alt[patch] = (number_alt, number_vot)
		except DataProperty.DoesNotExist:
			pass
	allFiles = DataFile.objects.filter(dataPatch__dataSet = dataset)
	nbFiles = allFiles.count()
	totalSize = allFiles.aggregate(Sum('fileSize'))['fileSize__sum']
	if totalSize != None:
		totalSize = round(totalSize / 1000, 2)
	allTypes = allFiles.order_by('dataType').values_list('dataType').distinct()
	zipfilepath = os.path.join('data', datacategory, str(dataset.abbreviation), str(dataset.abbreviation) + '.zip')
	return my_render(request, os.path.join('preflib', 'dataset.html'), locals())

@cache_page(CACHE_TIME)
def datapatch(request, datacategory, dataSetNum, dataPatchNum):
	dataSet = get_object_or_404(DataSet, category = datacategory, seriesNumber = dataSetNum)
	dataPatch = get_object_or_404(DataPatch, dataSet = dataSet, seriesNumber = dataPatchNum)
	dataFiles = DataFile.objects.filter(dataPatch = dataPatch).order_by('-modificationType')
	metadataPerCategories = [(c[1], Metadata.objects.filter(isActive = True, isDisplayed = True, category = c[0])) for c in METADATACATEGORIES]
	number_alt_meta = Metadata.objects.get(shortName = "numAlt")
	filesMetaPreview = []
	for file in dataFiles:
		metaCat = []
		for (category, metadata) in metadataPerCategories:
			metaInsideCat = []
			for m in metadata:
				if DataProperty.objects.filter(metadata = m, dataFile = file).exists():
					metaInsideCat.append((m, DataProperty.objects.get(metadata = m, dataFile = file).getTypedValue()))
			if len(metaInsideCat) > 0:
				metaCat.append((category, metaInsideCat))
		# Getting the first few lines of the file
		try:
			number_alt = DataProperty.objects.get(metadata = number_alt_meta, dataFile = file).getTypedValue()
			f = open(finders.find(os.path.join("data", dataSet.category, dataSet.abbreviation, file.fileName)), "r")
			if number_alt <= 12:
				lines = f.readlines()
				lines = lines[:min(number_alt + 2 + 10, len(lines))]
				lines = [(i + 1, lines[i]) for i in range(len(lines))]
			else:
				tmplines = f.readlines()
				lines = [(i + 1, tmplines[i]) for i in range(12)]
				lines.append(("...", ""))
				lines += [(i + 1, tmplines[i][:45] + "...") for i in range(number_alt + 1, min(number_alt + 12, len(tmplines)))]
			f.close
			filesMetaPreview.append((file, metaCat, lines))
		except DataProperty.DoesNotExist:
			pass
	return my_render(request, os.path.join('preflib', 'datapatch.html'), locals())

@cache_page(CACHE_TIME)
def datatypes(request):
	return my_render(request, os.path.join('preflib', 'datatypes.html'))

def dataSearch(request):
	categories = copy.deepcopy(DATACATEGORY)
	types = copy.deepcopy(DATATYPES)
	types.remove(('dat', 'extra data file'))
	types.remove(('csv', 'comma-separated values'))
	allMetadata = Metadata.objects.filter(isActive = True, isDisplayed = True)

	metadataSliderValues = dict()
	removeMetadata = []
	# We compute the max and min values of the slider for each metadata
	for m in allMetadata:
		if m.searchWidget == "range":
			props = DataProperty.objects.filter(metadata = m).annotate(floatValue = Cast('value', models.FloatField()))
			maxValue = ceil(props.aggregate(Max('floatValue'))['floatValue__max'])
			minValue = floor(props.aggregate(Min('floatValue'))['floatValue__min'])
			intermediateValue = floor((maxValue - minValue) * 0.3) if maxValue > 30 else floor((maxValue - minValue) * 0.5)
			metadataSliderValues[m] = (minValue, intermediateValue, maxValue)
			# If the min and max are equal, filtering on that metadata is useless so we remove it
			if maxValue == minValue:
				removeMetadata.append(m)
	for m in removeMetadata:
		allMetadata = allMetadata.exclude(pk = m.pk)

	# This is to save the POST data when we change to a different page of the results
	if request.method != 'POST' and 'page' in request.GET:
		if 'searchDataFilesPOST' in request.session:
			request.POST = request.session['searchDataFilesPOST']
			request.method = 'POST'

	allFiles = DataFile.objects.filter(dataType__in = [t[0] for t in types])
	if request.method == 'POST':
		request.session['searchDataFilesPOST'] = request.POST
	
		categoryFilter = [cat[0] for cat in categories]
		for cat in categories:	
			if request.POST.get(cat[0] + 'selector') == "no":
				if cat[0] in categoryFilter: categoryFilter.remove(cat[0])
			elif request.POST.get(cat[0] + 'selector') == "yes":
				categoryFilter = [c for c in categoryFilter if c == cat[0]]
		allFiles = allFiles.filter(dataPatch__dataSet__category__in = categoryFilter)

		dataTypeFilter = [t[0] for t in types]
		for t in types:
			if request.POST.get(t[0] + 'selector') == "no":
				if t[0] in dataTypeFilter: dataTypeFilter.remove(t[0])
			elif request.POST.get(t[0] + 'selector') == "yes":
				dataTypeFilter = [x for x in dataTypeFilter if x == t[0]]
		allFiles = allFiles.filter(dataType__in = dataTypeFilter)

		for m in allMetadata:
			if m.searchWidget == "ternary":
				if request.POST.get(m.shortName + 'selector') == "no":
					propretyQuery = DataProperty.objects.filter(metadata = m, value = True)
					allFiles = allFiles.exclude(dataproperty__in = models.Subquery(propretyQuery.values('pk')))
				elif request.POST.get(m.shortName + 'selector') == "yes":
					propretyQuery = DataProperty.objects.filter(metadata = m, value = True)
					allFiles = allFiles.filter(dataproperty__in = models.Subquery(propretyQuery.values('pk')))

			elif m.searchWidget == "range":
				propretyQueryMin = DataProperty.objects.filter(metadata = m).annotate(floatValue = Cast('value', models.FloatField())).filter(floatValue__lt = float(request.POST.get(m.shortName + 'SliderValueMin')))
				allFiles = allFiles.exclude(dataproperty__in = models.Subquery(propretyQueryMin.values('pk')))
				propretyQueryMax = DataProperty.objects.filter(metadata = m).annotate(floatValue = Cast('value', models.FloatField())).filter(floatValue__gt = float(request.POST.get(m.shortName + 'SliderValueMax')))

				allFiles = allFiles.exclude(dataproperty__in = models.Subquery(propretyQueryMax.values('pk')))

	allFiles = allFiles.order_by('fileName', 'dataType')
	(paginator, dataFiles, page, pagesBefore, pagesAfter) = getPaginator(request, allFiles, pageSize = 40)
	return my_render(request, os.path.join('preflib', 'datasearch.html'), locals())

# About views
@cache_page(CACHE_TIME)
def about(request):
	return my_render(request, os.path.join('preflib', 'about.html'))

# Tools views
@cache_page(CACHE_TIME)
def tools(request):
	return my_render(request, os.path.join('preflib', 'tools.html'))

# Tools views
@cache_page(CACHE_TIME)
def toolsIVS(request):
	return my_render(request, os.path.join('preflib', 'toolsivs.html'))

# Tools views
@cache_page(CACHE_TIME)
def toolsKDG(request):
	return my_render(request, os.path.join('preflib', 'toolskdg.html'))

# Tools views
@cache_page(CACHE_TIME)
def toolsCRIS(request):
	return my_render(request, os.path.join('preflib', 'toolscris.html'))

# Paper views
@cache_page(CACHE_TIME)
def papersView(request):
	(paginator, papers, page, pagesBefore, pagesAfter) = getPaginator(request, Paper.objects.all(), pageSize = 30)
	return my_render(request, os.path.join('preflib', 'papers.html'), locals())

# Archive views
@cache_page(CACHE_TIME)
def archive(request):
	return my_render(request, os.path.join('preflib', 'archive.html'))

# User stuff
def userLogin(request):
	print(request.POST)
	error = False
	# The variable that get the next page if there is one
	next = request.POST.get('next', request.GET.get('next', ''))
	if request.method == "POST":
		form = LoginForm(request.POST)
		if form.is_valid():
			# If the form is valid, try to authenticate the user
			username = form.cleaned_data["username"]
			password = form.cleaned_data["password"]
			user = authenticate(username = username, password = password) 
			if user:
				# If the authentication is right, login the user and redirect to the next page if there is one
				login(request, user)
				if next:
					return HttpResponseRedirect(next)
			else: 
				# Else there have been an error during the login
				error = True
	else:
		form = LoginForm()
	return my_render(request, os.path.join('preflib', 'userlogin.html'), locals())

def userLogout(request):
	if not request.user.is_authenticated:
		raise Http404
	if request.user.is_authenticated:
		logout(request)
	return redirect('preflibapp:main')

def userProfile(request):
	if not request.user.is_authenticated:
		raise Http404
	return my_render(request, os.path.join('preflib', 'userprofile.html'), locals())

def newAccount(request):
	form = CreateUserForm(request.POST or None)
	created = False
	if form.is_valid():
		User.objects.create_user(
			form.cleaned_data["username"], 
			form.cleaned_data["email"], 
			form.cleaned_data["password2"])
		created = True
	return my_render(request, os.path.join('preflib', 'usernewaccount.html'), locals())

# Admin views
def admin(request):
	if not request.user.is_authenticated:
		raise Http404
	return my_render(request, os.path.join('preflib', 'admin.html'))

def adminNews(request):
	if not request.user.is_authenticated:
		raise Http404
	created = False
	# The variable that get the next page if there is one
	if request.method == "POST":
		form = NewsForm(request.POST)
		if form.is_valid():
			now = timezone.now()
			News.objects.create(
				title = form.cleaned_data['title'],
				text = form.cleaned_data['text'],
				publicationDate = str(now.year) + '-' + str(now.month) + '-' + str(now.day),
				author = request.user)
			created = True
	else:
		form = NewsForm()
	return my_render(request, os.path.join('preflib', 'adminnews.html'), locals())

def adminPaper(request):
	if not request.user.is_authenticated:
		raise Http404
	created = False
	# The variable that get the next page if there is one
	if request.method == "POST":
		form = PaperForm(request.POST)
		if form.is_valid():
			Paper.objects.create(
				title = form.cleaned_data['title'],
				authors = form.cleaned_data['authors'],
				publisher = form.cleaned_data['publisher'],
				year = form.cleaned_data['year'],
				url = form.cleaned_data['url'])
			created = True
	else:
		form = PaperForm()
	return my_render(request, os.path.join('preflib', 'adminpaper.html'), locals())

def adminZip(request):
	if not request.user.is_authenticated:
		raise Http404

	logs = Log.objects.filter(logType = "zip")
	if len(logs) > 0:
		log = logs.latest("publicationDate")
	else:
		log = None

	if request.method == "POST":
		if "zip" in request.POST and request.POST['zip'] == "True":
			if finders.find(os.path.join("data", "zip.lock")) == None:
				threaded_management_command("generateZipFiles")
				launchedText = """The script regenerating the zip files has been launched, it will take several 
				minutes to complete, come here to see the log once it will be available. You will be redirected 
				in 5 seconds to the admin panel."""
			else:
				launchedText = """The script regenerating the zip files <strong>has not been launched</strong>, another is already 
				running. You will be redirected in 5 seconds to the admin panel."""

	return my_render(request, os.path.join('preflib', 'adminzip.html'), locals())

def adminAddDataset(request):
	if not request.user.is_authenticated:
		raise Http404

	logs = Log.objects.filter(logType = "dataset")
	if len(logs) > 0:
		log = logs.latest("publicationDate")
	else:
		log = None

	if request.method == "POST":
		if finders.find(os.path.join("datatoadd", "dataset.lock")) == None:
			args = []
			if "all" in request.POST:
				dataDir = finders.find("datatoadd/")
				for filename in os.listdir(dataDir):
					if filename.endswith(".zip"):
						args.append(str(filename))
			else:
				for zipFile in request.POST.getlist('dataset'):
					args.append(str(zipFile))
			if len(args) == 0:
				launchedText = """The script adding datasets <strong>has not been launched</strong>, you have not selected any 
				dataset to be added. Please select at least one."""
				noArgs = True
			else:
				threaded_management_command("addDataset", {"file": args})
				launchedText = """The script adding datasets has been launched, it could take some time to proceed, come here 
				to see the log once it will be available. You will be redirected in 5 seconds to the admin panel."""
		else:
			launchedText = """The script adding datasets <strong>has not been launched</strong>, another is already 
			running. You will be redirected in 5 seconds to the admin panel."""
	else:
		dataDir = finders.find("datatoadd")
		files = []
		for filename in os.listdir(dataDir):
			if filename.endswith(".zip"):
				files.append((filename, os.path.getsize(os.path.join(dataDir, filename)) / 1000))
		files.sort()

	return my_render(request, os.path.join('preflib', 'adminadddataset.html'), locals())

def adminLog(request, logtype, lognum):
	if not request.user.is_authenticated:
		raise Http404
	log = get_object_or_404(Log, logType = logtype, logNum = lognum)
	title = logtype.capitalize()
	return my_render(request, os.path.join('preflib', 'adminlog.html'), locals())