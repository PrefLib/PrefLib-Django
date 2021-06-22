from django.contrib import admin

from .models import *

admin.site.register(DataSet)
admin.site.register(DataPatch)
admin.site.register(DataFile)
admin.site.register(Metadata)
admin.site.register(DataProperty)
admin.site.register(Paper)
admin.site.register(Log)