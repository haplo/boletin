from django.conf.urls.defaults import *
from django.http import HttpResponse

from boletin.urls import urlpatterns as boletin_urls


urlpatterns = patterns('',
    # Mock profile urls
    url(r'^contactform/$', lambda r: HttpResponse("foo"), name='contact_form'),
)

urlpatterns += boletin_urls
