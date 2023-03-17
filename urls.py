from django.conf.urls.defaults import *
from comerciax.views import *
from comerciax.admincomerciax import views

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

import os
from comerciax import admincomerciax
import comerciax
media = os.path.join(os.path.dirname(__file__),  'media')


urlpatterns = patterns('',
    # Example:
    # (r'^comerciax/', include('comerciax.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    # (r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    # (r'^admin/', include(admin.site.urls)),
    
    (r'^comerciax/login/$', login),
    (r'^comerciax/logout/$', logout),
    url(r'^comerciax/logout/$', 'logout', name='logout2'),
    url(r'^comerciax/index/$', index , name='index2'),
    (r'^comerciax/index/$', index),
    (r'^comerciax/media/(?P<path>.*)$', 'django.views.static.serve',{'document_root': media}),
    
    
    (r'^comerciax/admincom/', include('comerciax.admincomerciax.urls')),
    (r'^comerciax/casco/', include('comerciax.casco.urls')),
    (r'^comerciax/comercial/', include('comerciax.comercial.urls')),
    
    
     # Example:
    # (r'^comerciax/', include('comerciax.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    # (r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    # (r'^admin/', include(admin.site.urls)),
)
