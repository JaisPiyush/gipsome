from django.urls import path,include
from django.conf import settings
from django_hosts import patterns,host


host_patterns = patterns('',
  host(r'gipsome',settings.ROOT_URLCONF,name='locie_server'),
  host(r'\w+','locie.lociestores_url',name='lociestore'),
)