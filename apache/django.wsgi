import os
import sys
sys.path.append('C:/Program Files (x86)/Apache Software Foundation/Apache2.2/htdocs/comerciax/')
sys.path.append('C:/Program Files (x86)/Apache Software Foundation/Apache2.2/htdocs/')

os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'

import django.core.handlers.wsgi
application = django.core.handlers.wsgi.WSGIHandler()