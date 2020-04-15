from __future__ import absolute_import, unicode_literals
from celery import Celery
import os
# import locie_server.settings as settings

# set the default Django settings module for the celery program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE','locie_server.settings')

app = Celery('locie_server')


# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix

app.config_from_object('django.conf:settings',namespace='CELERY')

app.autodiscover_tasks()

@app.task(bind=True)
def debug_task(self):
    print('Request: {0!r}'.format(self.request))