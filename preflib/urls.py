"""preflib URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import path, include
from django.conf.urls import handler400, handler403, handler404, handler500

handler400 = "preflibapp.views.error_400_view"
handler403 = "preflibapp.views.error_403_view"
handler404 = "preflibapp.views.error_404_view"
handler500 = "preflibapp.views.error_500_view"

urlpatterns = [
    path("djangoadmin/", admin.site.urls),
    path("", include("preflibapp.urls")),
]
