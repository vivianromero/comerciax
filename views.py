'''
Created on Mar 4, 2011

@author: jesus
'''
from django.shortcuts import render_to_response
from django.http import HttpResponseRedirect
from django.contrib import auth
from django.template.context import RequestContext

def index(request):
    #return render_to_response('base.html',{'mensage': 'mensage'})
    if request.user.is_authenticated():
        # Do something for authenticated users.
        #return render_to_response('index.html')
        return render_to_response("index.html",locals(),context_instance = RequestContext(request))
    else:
        # Do something for anonymous users.
        return render_to_response('login.html') 

def login(request):
    if request.POST:
        username = request.POST.get('user')
        password = request.POST.get('password')
        
        user = auth.authenticate(username=username, password=password)
        if user is not None:
            if user.is_active:
                auth.login(request, user)
                return HttpResponseRedirect("/comerciax/index/")
                #return render_to_response('index.html', locals())
                # Redirect to a success page.
        else:
            # Return an 'invalid login' error message.
            return render_to_response('login.html')        
    else:
        return render_to_response('login.html')
    
def logout(request):
    auth.logout(request)
    return HttpResponseRedirect("/comerciax/index/")