from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect, Http404
from django.contrib.staticfiles import finders
from django.db.models import Sum, Max, Min, Count
from django.core.paginator import Paginator
from django.core import management

from datetime import datetime
from subprocess import Popen

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
	args['DATASETEXTENSIONS'] = DATASETEXTENSIONS
	args['DATATYPES'] = DATATYPES
	return render(request, template, args)

def error_render(request, template, status):
	return render(request, template, locals(), status = status)

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

def main(request):
	nbDataSet = DataSet.objects.count()
	nbDataFile = DataFile.objects.count()
	totalSize = DataFile.objects.aggregate(Sum('fileSize'))['fileSize__sum']
	if totalSize != None:
		totalSize = round(totalSize / 1000000000, 2)
	nbDataType = DataFile.objects.values('dataType').distinct().count()
	if DataProp.objects.exists():
		randomProp = random.choice(DataProp.objects.filter(nbAlternatives__gt = 5, image__isnull = False))
	return my_render(request, os.path.join('preflib', 'index.html'), locals())

# Data views
def data(request):
	return my_render(request, os.path.join('preflib', 'data.html'))

def dataFormat(request):
	return my_render(request, os.path.join('preflib', 'dataformat.html'))

def dataMetadata(request):
	return my_render(request, os.path.join('preflib', 'datametadata.html'))

def alldatasets(request, dataextension):
	(paginator, datasets, page, pagesBefore, pagesAfter) = getPaginator(request, DataSet.objects.filter(extension = dataextension).order_by('name'))
	title = findChoiceValue(DATASETEXTENSIONS, dataextension)
	return my_render(request, os.path.join('preflib', 'datasetall.html'), locals())

def dataset(request, dataextension, dataSetNum):
	dataset = get_object_or_404(DataSet, extension = dataextension, seriesNumber = dataSetNum)
	(paginator, patches, page, pagesBefore, pagesAfter) = getPaginator(request, DataPatch.objects.filter(dataSet = dataset).order_by("name"))
	allFiles = DataFile.objects.filter(dataPatch__dataSet = dataset)
	nbFiles = allFiles.count()
	totalSize = allFiles.aggregate(Sum('fileSize'))['fileSize__sum']
	if totalSize != None:
		totalSize = round(totalSize / 1000, 2)
	allTypes = allFiles.order_by('dataType').values('dataType').distinct()
	allDataTypes = ", ".join([t['dataType'] for t in allTypes])
	zipfilepath = os.path.join('data', dataextension, str(dataset.abbreviation), str(dataset.abbreviation) + '.zip')
	return my_render(request, os.path.join('preflib', 'dataset.html'), locals())

def datapatch(request, dataextension, dataSetNum, dataPatchNum):
	dataSet = get_object_or_404(DataSet, extension = dataextension, seriesNumber = dataSetNum)
	dataPatch = get_object_or_404(DataPatch, dataSet = dataSet, seriesNumber = dataPatchNum)
	dataFiles = DataFile.objects.filter(dataPatch = dataPatch).order_by('-modificationType')
	return my_render(request, os.path.join('preflib', 'datapatch.html'), locals())

def datatypes(request):
	return my_render(request, os.path.join('preflib', 'datatypes.html'))

def dataSearch(request):
	def filterTrivaluedField(queryset, field, value):
		queryset.filter(**{field: value})

	extensions = copy.deepcopy(DATASETEXTENSIONS)
	types = copy.deepcopy(DATATYPES)
	types.remove(('dat', 'extra data file'))
	types.remove(('csv', 'comma-separated values'))
	allProps = DataProp.objects.all().exclude(dataFile__dataType__in = ['dat', 'csv'])
	nbAlt = [allProps.aggregate(Min('nbAlternatives'))['nbAlternatives__min'], 
		allProps.aggregate(Max('nbAlternatives'))['nbAlternatives__max']]
	nbAlt.append(nbAlt[1] * 0.1)
	nbBallot = [allProps.aggregate(Min('nbVoters'))['nbVoters__min'], 
		allProps.aggregate(Max('nbVoters'))['nbVoters__max']]
	nbBallot.append(nbBallot[1] * 0.1)
	nbUniqueBallot = [allProps.aggregate(Min('nbDifferentOrders'))['nbDifferentOrders__min'], 
		allProps.aggregate(Max('nbDifferentOrders'))['nbDifferentOrders__max']]
	nbUniqueBallot.append(nbUniqueBallot[1] * 0.1)

	if request.method != 'POST' and 'page' in request.GET:
		if 'searchDataFilesPOST' in request.session:
			request.POST = request.session['searchDataFilesPOST']
			request.method = 'POST'

	filterDict = dict([])
	filterDict['dataType__in'] = [t[0] for t in types]
	excludeDict = dict([])
	if request.method == 'POST':
		request.session['searchDataFilesPOST'] = request.POST
		electionTypeFilter = [ext[0] for ext in extensions]
		for ext in extensions:	
			if request.POST.get(ext[0] + 'selector') == "no":
				if ext[0] in electionTypeFilter: electionTypeFilter.remove(ext[0])
			elif request.POST.get(ext[0] + 'selector') == "yes":
				electionTypeFilter = [e for e in electionTypeFilter if e == ext[0]]
		filterDict['dataPatch__dataSet__extension__in'] = electionTypeFilter
		dataTypeFilter = [t[0] for t in types]
		for t in types:
			if request.POST.get(t[0] + 'selector') == "no":
				if t[0] in dataTypeFilter: dataTypeFilter.remove(t[0])
			elif request.POST.get(ext[0] + 'selector') == "yes":
				dataTypeFilter = [x for x in dataTypeFilter if x == t[0]]
		filterDict['dataType__in'] = dataTypeFilter
		if request.POST.get('isSPselector') == "no":
			filterDict['proptofile__isSinglePeaked'] = False
		elif request.POST.get('isSPselector') == "yes":
			filterDict['proptofile__isSinglePeaked'] = True
		if request.POST.get('isSCselector') == "no":
			filterDict['proptofile__isSingleCrossed'] = False
		elif request.POST.get('isSCselector') == "yes":
			filterDict['proptofile__isSingleCrossed'] = True
		if request.POST.get('isAppselector') == "no":
			filterDict['proptofile__isApproval'] = False
		elif request.POST.get('isAppselector') == "yes":
			filterDict['proptofile__isApproval'] = True
		if request.POST.get('isStrictselector') == "no":
			filterDict['proptofile__isStrict'] = False
		elif request.POST.get('isStrictselector') == "yes":
			filterDict['proptofile__isStrict'] = True
		if request.POST.get('isComplselector') == "no":
			filterDict['proptofile__isComplete'] = False
		elif request.POST.get('isComplselector') == "yes":
			filterDict['proptofile__hasCondorcet'] = True
		if request.POST.get('hasCondselector') == "no":
			filterDict['proptofile__isComplete'] = False
		elif request.POST.get('hasCondselector') == "yes":
			filterDict['proptofile__hasCondorcet'] = True
		excludeDict['proptofile__nbAlternatives__lt'] = request.POST.get('nbAltsSliderValueMin')
		excludeDict['proptofile__nbAlternatives__gt'] = request.POST.get('nbAltsSliderValueMax')
		excludeDict['proptofile__nbVoters__lt'] = request.POST.get('nbBallotsSliderValueMin')
		excludeDict['proptofile__nbVoters__gt'] = request.POST.get('nbBallotsSliderValueMax')
		excludeDict['proptofile__nbDifferentOrders__lt'] = request.POST.get('nbUniqBallotsSliderValueMin')
		excludeDict['proptofile__nbDifferentOrders__gt'] = request.POST.get('nbUniqBallotsSliderValueMax')
		excludeDict['proptofile__largestBallot__gt'] = request.POST.get('sizeBallotsSliderValueMax')
		excludeDict['proptofile__smallestBallot__lt'] = request.POST.get('sizeBallotsSliderValueMin')
		excludeDict['proptofile__maxNbIndif__gt'] = request.POST.get('nbIndifSliderValueMax')
		excludeDict['proptofile__minNbIndif__lt'] = request.POST.get('nbIndifSliderValueMin')
		excludeDict['proptofile__largestIndif__gt'] = request.POST.get('sizeIndifSliderValueMax')
		excludeDict['proptofile__smallestIndif__lt'] = request.POST.get('sizeIndifSliderValueMin')

	# print(filterDict)
	# print(excludeDict)
	allFiles = DataFile.objects.filter(**filterDict)
	for key, value in excludeDict.items():
		# print(key)
		# print(value)
		allFiles = allFiles.exclude(**{key: value})
		# print(allFiles)
		# print(len(allFiles))
		# print()
	allFiles = allFiles.order_by('dataType', 'fileName')	
	(paginator, dataFiles, page, pagesBefore, pagesAfter) = getPaginator(request, allFiles, pageSize = 50)
	return my_render(request, os.path.join('preflib', 'datasearch.html'), locals())

# About views
def about(request):
	return my_render(request, os.path.join('preflib', 'about.html'))

# Tools views
def tools(request):
	return my_render(request, os.path.join('preflib', 'tools.html'))

# Tools views
def toolsIVS(request):
	return my_render(request, os.path.join('preflib', 'toolsivs.html'))

# Tools views
def toolsKDG(request):
	return my_render(request, os.path.join('preflib', 'toolskdg.html'))

# Tools views
def toolsCRIS(request):
	return my_render(request, os.path.join('preflib', 'toolscris.html'))

# Paper views
def papersView(request):
	(paginator, papers, page, pagesBefore, pagesAfter) = getPaginator(request, Paper.objects.all(), pageSize = 30)
	return my_render(request, os.path.join('preflib', 'papers.html'), locals())

# Archive views
def archive(request):
	return my_render(request, os.path.join('preflib', 'archive.html'))

# User stuff
def userLogin(request):
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
	return my_render(request, os.path.join('preflib', 'login.html'), locals())

def userLogout(request):
	if not request.user.is_authenticated:
		raise Http404
	if request.user.is_authenticated:
		logout(request)
	return redirect('preflibapp:main')

def createUser(request):
	if not request.user.is_authenticated:
		raise Http404
	form = CreateUserForm(request.POST or None)
	created = False
	if form.is_valid():
		if form.cleaned_data["superuser"]:
			User.objects.create_superuser(
			form.cleaned_data["username"], 
			form.cleaned_data["email"], 
			form.cleaned_data["password2"])
		else:
			User.objects.create_user(
				form.cleaned_data["username"], 
				form.cleaned_data["email"], 
				form.cleaned_data["password2"])
		created = True
	return my_render(request, os.path.join('preflib', 'adminuser.html'), locals())

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
			now = datetime.now()
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