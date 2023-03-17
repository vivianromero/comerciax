#-*- coding: utf-8 -*-
'''
Created on Mar 22, 2011

@author: jesusviewprod
'''
from comerciax.admincomerciax.forms import *
from comerciax.admincomerciax.models import *
from django.contrib.auth.models import User, Permission, Group
from django.shortcuts import render_to_response, HttpResponseRedirect
from django.template.context import RequestContext
from comerciax.utils import get_datatables_records, write_pdf, Estados, query_to_dicts
from uuid import uuid4
import sys
from string import find
from django.db import transaction, connection
import json
from django.http import HttpResponse
from django.core import serializers
from django.contrib.auth.forms import PasswordChangeForm
from lib2to3.pgen2.tokenize import group
from django.contrib.auth.decorators import login_required
from django.utils import simplejson
from comerciax.casco.models import Casco,DetalleRC, RecepcionCliente
from comerciax.comercial.models import Oferta, DetalleOferta, Facturas
from django.db.models import Q
import xlwt
#from xlwt import Workbook,Style
import datetime
from datetime import date,time,datetime
from decimal import Decimal
from comerciax.casco.models import DetalleDIP,DetalleDVP,DetalleTransferencia,DetalleCC,DetalleVP,DetallePT,DetallePTE,TrazabilidadCasco,Detalle_DC
import base64
import smtplib

def createexcel(request):
    
    style0 = xlwt.easyxf('font: name Times New Roman, color-index red, bold on',
        num_format_str='#,##0.00')
    style1 = xlwt.easyxf(num_format_str='D-MMM-YY')
   
    wb = xlwt.Workbook()
    ws = wb.add_sheet('A Test Sheet')
    
    ws.write(0, 0, 1234.56, style0)
    ws.write(1, 0, datetime.now(), style1)
    ws.write(2, 0, 1)
    ws.write(2, 1, 1)
    ws.write(2, 2, xlwt.Formula("A3+B3"))
    
    wb.save('example.xls')
    
    '''
    wb = Workbook()
    ws = wb.add_sheet('Type examples')
    ws.row(0).write(0,u'\xa3')
    ws.row(0).write(1,'Text')
    ws.row(1).write(0,3.1415)
    ws.row(1).write(1,15)
    ws.row(1).write(2,265L)
    ws.row(1).write(3,Decimal('3.65'))
    ws.row(2).set_cell_number(0,3.1415)
    ws.row(2).set_cell_number(1,15)
    ws.row(2).set_cell_number(2,265L)
    ws.row(2).set_cell_number(3,Decimal('3.65'))
    ws.row(3).write(0,date(2009,3,18))
    ws.row(3).write(1,datetime(2009,3,18,17,0,1))
    ws.row(3).write(2,time(17,1))
    ws.row(4).set_cell_date(0,date(2009,3,18))
    ws.row(4).set_cell_date(1,datetime(2009,3,18,17,0,1))
    ws.row(4).set_cell_date(2,time(17,1))
    ws.row(5).write(0,False)
    ws.row(5).write(1,True)
    ws.row(6).set_cell_boolean(0,False)
    ws.row(6).set_cell_boolean(1,True)
    ws.row(7).set_cell_error(0,0x17)
    ws.row(7).set_cell_error(1,'#NULL!')
    ws.row(8).write(0,'',Style.easyxf('pattern: pattern solid, fore_colour green;'))
    ws.row(8).write(1,None,Style.easyxf('pattern: pattern solid, fore_colour blue;'))
    ws.row(9).set_cell_blank(0,Style.easyxf('pattern: pattern solid, fore_colour yellow;'))
    ws.row(10).set_cell_mulblanks(5,10,Style.easyxf('pattern: pattern solid, fore_colour red;'))
    wb.save('types.xls')
    '''

def article(request):
    article = {'content':'Hola Mundo','articletitle':'Primer PDF'}
    
    return write_pdf('pdf/pdf.html',{
        'pagesize' : 'A4',
        'article' : article})

def pdfcliente(request):
    article = {'content':'Hola Mundo','articletitle':'Primer PDF'}
    
    clientes = Cliente.objects.all()
    
    return write_pdf('pdf/pdf-cliente.html',{
        'pagesize' : 'A4',
        'cliente' : clientes})

def reportcliente(request):
    clientesobj = Cliente.objects.select_related().get(pk='b5df0a69-4c24-4899-bbbd-6bc266523a07')
    lista_valores=[{"pk":"123","dir":"Calle A","codigo":"ABD111"}]
    '''
    for clienteobj in clientesobj:
        pk = clienteobj.id
        direccion = clienteobj.direccion
        codigo = clienteobj.codigo
        lista_valores=lista_valores + [{"pk":pk,"dir":direccion,"codigo":codigo}]
    ''' 
    return HttpResponse(simplejson.dumps(lista_valores),content_type = 'application/javascript; charset=utf8')

def reporte1(request):
    clientes = Cliente.objects.all()
    return render_to_response("report/oferta.html",locals(),context_instance = RequestContext(request))


@login_required
def grupo(request):
    if not request.user.has_perm('auth.add_group'):
        return render_to_response("denegado.html",locals(),context_instance = RequestContext(request))
    return render_to_response("admincomerciax/indexgrupo.html",locals(),context_instance = RequestContext(request))

def get_grupo_list(request):
    #prepare the params

    #initial querySet
    querySet = Group.objects.all()
    #columnIndexNameMap is required for correct sorting behavior
    columnIndexNameMap = {0:'id', 1:'name'}
    #model fields listed in searchableColumns will be used for filtering (Search)
    searchableColumns = ['name']
    #path to template used to generate json
    jsonTemplatePath = 'admincomerciax/json/json_grupo.txt'

    #call to generic function from utils
    return get_datatables_records(request, querySet, columnIndexNameMap, searchableColumns, jsonTemplatePath)

@login_required
def addgrupo(request):
    if not request.user.has_perm('auth.add_group'):
        return render_to_response("denegado.html",locals(),context_instance = RequestContext(request))
    c = None
    l = []
    if request.method == 'POST':
        form = FGrupo(request.POST)
        if form.is_valid():
            grupo = Group()
            try:
                grupo.name = form.cleaned_data['nombre']
                grupo.save()
                
                if request.POST.__contains__('submit1'):
                    return HttpResponseRedirect('/comerciax/admincom/grupo/view/' + grupo.pk.__str__())
                else:
                    form = FGrupo()
            except Exception, e:
                exc_info = e.__str__() # sys.exc_info()[:1]
                c = exc_info.find("DETAIL:")
                if c < 0:
                    l = l + ["Error Fatal."]
                else:
                    c = exc_info[c + 7:]
                    l=l+[c]
    else:
        form = FGrupo()
     
    uri="/comerciax/admincom/grupo/index" 
    return render_to_response("admincomerciax/form_grupoadd.html",{'form':form,'title':'Grupo', 'form_name':'Insetar Grupo','form_description':'Introducir un nuevo grupo de usuario a la base de datos','controlador':'Grupo','accion':addgrupo,
                                                    'cancelbtn':uri,'error2':l},context_instance = RequestContext(request))
@login_required
def viewgrupo(request,idgrupo,*otro):
    if not request.user.has_perm('auth.add_group'):
        return render_to_response("denegado.html",locals(),context_instance = RequestContext(request))
    l=[]
    if otro.__len__()!=0:
        l=[otro[0]]
    error2 = l
    grupoobj = Group.objects.get(pk=idgrupo)
    nombre = grupoobj.name
    pk = idgrupo   
    
    
#    todos = Permission.objects.filter(name__startswith='Realiz')  
    todos = Permission.objects.filter(Q(name__contains='Realiz')|Q(name__contains='Gestiona')|Q(name__contains='Recibir')|Q(name__contains='Pasar')|Q(name__contains='Adicionar')|Q(name__contains='Modificar')).order_by('name')
    seleccionados = grupoobj.permissions.all()
    
    return render_to_response("admincomerciax/viewgrupo.html",locals(),context_instance = RequestContext(request))

@login_required
def pgrupo(request):
    if not request.user.has_perm('auth.add_group'):
        return render_to_response("denegado.html",locals(),context_instance = RequestContext(request))
    selec = request.POST.getlist('selecc')
    idgrupo = request.POST["idgrupo"]

    grupoobj = Group.objects.get(pk=idgrupo)
    #eliminar todos los permisos del usurio
    grupoobj.permissions.clear()
    #adicionar los nuevos permisos
    if selec.__len__() > 0:
        grupoobj.permissions = selec
    grupoobj.save()
    
    return viewgrupo(request, idgrupo)

@login_required
def editgrupo(request,idgrupo):
    if not request.user.has_perm('auth.add_group'):
        return render_to_response("denegado.html",locals(),context_instance = RequestContext(request))
    c = None
    l = []
    if request.method == 'POST':
        form = FGrupo(request.POST)
        if form.is_valid():
            grupoobj = Group.objects.get(pk=idgrupo)
            grupoobj.name = form.cleaned_data['nombre']
            try:
                grupoobj.save()
                return viewgrupo(request, idgrupo)
            except Exception, e:
                exc_info = e.__str__() # sys.exc_info()[:1]
                c = exc_info.find("DETAIL:")
                if c < 0:
                    l = l + ["Error Fatal."]
                else:
                    c = exc_info[c + 7:]
                    l=l+[c]
                uri="/comerciax/admincom/grupo/view/" + idgrupo 
                edituri = "/comerciax/admincom/grupo/edit/" + idgrupo + "/"
                return render_to_response("form/form_edit.html",{'tipocliente':'2','form':form,'title':'Grupo de usuario', 'form_name':'Editar Grupo de usuario','form_description':'Editar el grupo de usuario seleccionado','controlador':'Grupo de usuario','accion':editgrupo,
                                                                  'cancelbtn':uri, 'error2':l},context_instance = RequestContext(request))
    else:
        grupoobj = Group.objects.get(pk=idgrupo)
        form = FGrupo(initial={"nombre":grupoobj.name})
        uri="/comerciax/admincom/grupo/view/" + idgrupo 
        edituri = "/comerciax/admincom/grupo/edit/" + idgrupo + "/"
        return render_to_response("form/form_edit.html",{'tipocliente':'2','form':form,'title':'Grupo de usuario', 'form_name':'Editar Grupo de usuario','form_description':'Editar el grupo de usuario seleccionado','controlador':'Grupo de usuario','accion':editgrupo,
                                                                  'cancelbtn':uri,},context_instance = RequestContext(request))
@login_required
def delgrupo(request,idgrupo):
    if not request.user.has_perm('auth.add_group'):
        return render_to_response("denegado.html",locals(),context_instance = RequestContext(request))
    
    grupoobj = Group.objects.get(pk=idgrupo)
    try:
        grupoobj.delete()
        return HttpResponseRedirect('/comerciax/admincom/grupo/index')
    except  Exception, e:
        c = "No se puede eliminar el grupo de usuario, posibles causas este siendo utilizada por algún otro registro de la BD"
        return viewgrupo(request, idgrupo, c)

@login_required
def usuario(request):
    if not request.user.has_perm('auth.add_user'):
        return render_to_response("denegado.html",locals(),context_instance = RequestContext(request))
    
    return render_to_response("admincomerciax/indexusuario.html",locals(),context_instance = RequestContext(request))
    

def get_usuario_list(request):
    #prepare the params

    #initial querySet
    querySet = User.objects.all()
    #columnIndexNameMap is required for correct sorting behavior
    columnIndexNameMap = {0:'id', 1:'first_name',2:'email',3:'username',4:'is_active'}
    #model fields listed in searchableColumns will be used for filtering (Search)
    searchableColumns = ['first_name']
    #path to template used to generate json
    jsonTemplatePath = 'admincomerciax/json/json_usuario.txt'

    #call to generic function from utils
    return get_datatables_records(request, querySet, columnIndexNameMap, searchableColumns, jsonTemplatePath)

@login_required
def adduser(request):
    if not request.user.has_perm('auth.add_user'):
        return render_to_response("denegado.html",locals(),context_instance = RequestContext(request))
    c = None
    l = []
    if request.method == 'POST':
        form = Myregister_user(request.POST)
        if form.is_valid():
            user = User()
            try:
                user.first_name = form.cleaned_data['nombre']
                user.last_name = form.cleaned_data['apellidos']
                user.email = form.cleaned_data['email']
                user.username = form.cleaned_data['username']
                user.set_password(form.cleaned_data['password'])
                #user.password = form.cleaned_data['password']
                user.is_staff = True
                user.is_active = True
                user.save()
                
                if request.POST.__contains__('submit1'):
                    return HttpResponseRedirect('/comerciax/admincom/usuario/view/' + user.pk.__str__())
                else:
                    form = Myregister_user()
            except Exception, e:
                exc_info = e.__str__() # sys.exc_info()[:1]
                c = exc_info.find("DETAIL:")
                if c < 0:
                    l = l + ["Error Fatal."]
                else:
                    c = exc_info[c + 7:]
                    l=l+[c]
    else:
        form = Myregister_user()
     
    uri="/comerciax/admincom/usuario/index" 
    return render_to_response("admincomerciax/form_useradd.html",{'form':form,'title':'Usuario', 'form_name':'Insetar Usuario','form_description':'Introducir un nuevo usuario a la base de datos','controlador':'Usuario','accion':'adduser',
                                                    'cancelbtn':uri,'error2':l},context_instance = RequestContext(request))   
@login_required   
def viewusuario(request,idusuario,*otro):
    if not request.user.has_perm('auth.add_user'):
        return render_to_response("denegado.html",locals(),context_instance = RequestContext(request))
    l=[]
    if otro.__len__()!=0:
      l=[otro[0]]
    error2 = l
    usuarioobj = User.objects.get(pk=idusuario)
    nombre = usuarioobj.first_name
    apellidos = usuarioobj.last_name
    username = usuarioobj.username
    email = usuarioobj.email
    pk = idusuario
    todos = Group.objects.all()    
    seleccionados = usuarioobj.groups.all()
    
    return render_to_response("admincomerciax/viewusuario.html",locals(),context_instance = RequestContext(request))

@login_required   
def viewperfil(request,idusuario,*otro):
#    if not request.user.has_perm('auth.perfil'):
#        return render_to_response("denegado.html",locals(),context_instance = RequestContext(request))
    l=[]
    if otro.__len__()!=0:
      l=[otro[0]]
    error2 = l
    usuarioobj = User.objects.get(pk=idusuario)
    nombre = usuarioobj.first_name
    apellidos = usuarioobj.last_name
    username = usuarioobj.username
    email = usuarioobj.email
    pk = idusuario
    return render_to_response("admincomerciax/viewperfil.html",locals(),context_instance = RequestContext(request))

@login_required
def editperfil(request,idusuario):
#    if not request.user.has_perm('auth.perfil'):
#        return render_to_response("denegado.html",locals(),context_instance = RequestContext(request))
    c = None
    l = []
    if request.method == 'POST':
        form = FEdit_user(request.POST)
        if form.is_valid():
            usuarioobj = User.objects.get(pk=idusuario)
            usuarioobj.first_name = form.cleaned_data['nombre']
            usuarioobj.last_name = form.cleaned_data['apellidos']
            usuarioobj.username = form.cleaned_data['username']
            usuarioobj.email = form.cleaned_data['email']
            
            try:
                usuarioobj.save()
                return viewperfil(request, idusuario)
            except Exception, e:
                exc_info = e.__str__() # sys.exc_info()[:1]
                c = exc_info.find("DETAIL:")
                if c < 0:
                    l = l + ["Error Fatal."]
                else:
                    c = exc_info[c + 7:]
                    l=l+[c]
                uri="/comerciax/admincom/usuario/perfil/" + idusuario 
                edituri = "/comerciax/admincom/usuario/editperfil/" + idusuario + "/"
                return render_to_response("form/form_edit.html",{'tipocliente':'2','form':form,'title':'Perfil', 'form_name':'Editar Perfil','form_description':'Editar mis datos de usuario','controlador':'Perfil','accion':editperfil,
                                                                  'cancelbtn':uri, 'error2':l},context_instance = RequestContext(request))
    else:
        usuarioobj = User.objects.get(pk=idusuario)
        form = FEdit_user(initial={"nombre":usuarioobj.first_name,"apellidos":usuarioobj.last_name,"username":usuarioobj.username,"email":usuarioobj.email})
        uri="/comerciax/admincom/usuario/viewperfil/" + idusuario 
        edituri = "/comerciax/admincom/usuario/editperfil/" + idusuario + "/"
        return render_to_response("form/form_edit.html",{'tipocliente':'2','form':form,'title':'Perfil', 'form_name':'Editar Perfil','form_description':'Editar mis datos de usuario','controlador':'Perfil','accion':editperfil,
                                                                  'cancelbtn':uri},context_instance = RequestContext(request))

@login_required
def changepassperfil(request,idusuario):
#    if not request.user.has_perm('auth.perfil'):
#        return render_to_response("denegado.html",locals(),context_instance = RequestContext(request))
    if request.method == 'POST':
        form = FChange_password(request.POST)
        if form.is_valid():
            usuarioobj = User.objects.get(pk=idusuario)
            #chequear que la contraseya anterior es la correcta
            if usuarioobj.check_password(form.cleaned_data['clave_actual']) :
                #todo ok se puede cambiar la contraseya
                usuarioobj.set_password(form.cleaned_data['clave_nueva'])
                usuarioobj.save()
                return viewperfil(request, idusuario)
            else :
                l=["La clave actual introducida no coincide con la clave del usuario, por favor vuelva a intentarlo"]
                uri="/comerciax/admincom/usuario/viewperfil/" + idusuario 
                return render_to_response("admincomerciax/form_changepass.html",{'form':form,'title':'Perfil', 'form_name':'Cambiar clave','form_description':'Cambiar la clave de usuario','controlador':'Perfil','accion':changepassperfil,
                                                    'idusuario':idusuario,'cancelbtn':uri, 'error2':l},context_instance = RequestContext(request))
    else:
        form2 = FChange_password()
        uri="/comerciax/admincom/usuario/viewperfil/" + idusuario 
        return render_to_response("admincomerciax/form_changepass.html",{'form':form2,'title':'Perfil', 'form_name':'Cambiar clave','form_description':'Cambiar la clave de usuario','controlador':'Perfil','accion':changepassperfil,
                                                    'idusuario':idusuario,'cancelbtn':uri},context_instance = RequestContext(request))


@login_required
def puser(request):
    if not request.user.has_perm('auth.add_user'):
        return render_to_response("denegado.html",locals(),context_instance = RequestContext(request))
    selec = request.POST.getlist('selecc')
    idusuario = request.POST["idusuario"]

    usuarioobj = User.objects.get(pk=idusuario)
    #eliminar todos los permisos del usurio
    #usuarioobj.user_permissions.clear()
    usuarioobj.groups.clear()
    #adicionar los nuevos permisos
    if selec.__len__() > 0:
        usuarioobj.groups = selec
        #usuarioobj.user_permissions = selec
    usuarioobj.save()
    return viewusuario(request, idusuario)

@login_required
def editusuario(request,idusuario):
    if not request.user.has_perm('auth.add_user'):
        return render_to_response("denegado.html",locals(),context_instance = RequestContext(request))
    c = None
    l = []
    if request.method == 'POST':
        form = FEdit_user(request.POST)
        if form.is_valid():
            usuarioobj = User.objects.get(pk=idusuario)
            usuarioobj.first_name = form.cleaned_data['nombre']
            usuarioobj.last_name = form.cleaned_data['apellidos']
            usuarioobj.username = form.cleaned_data['username']
            usuarioobj.email = form.cleaned_data['email']
            
            try:
                usuarioobj.save()
                return viewusuario(request, idusuario)
            except Exception, e:
                exc_info = e.__str__() # sys.exc_info()[:1]
                c = exc_info.find("DETAIL:")
                if c < 0:
                    l = l + ["Error Fatal."]
                else:
                    c = exc_info[c + 7:]
                    l=l+[c]
                uri="/comerciax/admincom/usuario/view/" + idusuario 
                edituri = "/comerciax/admincom/usuario/edit/" + idusuario + "/"
                return render_to_response("form/form_edit.html",{'tipocliente':'2','form':form,'title':'Usuario', 'form_name':'Editar Usuario','form_description':'Editar el usuario seleccionado','controlador':'Usuario','accion':editusuario,
                                                                  'cancelbtn':uri, 'error2':l},context_instance = RequestContext(request))
    else:
        usuarioobj = User.objects.get(pk=idusuario)
        form = FEdit_user(initial={"nombre":usuarioobj.first_name,"apellidos":usuarioobj.last_name,"username":usuarioobj.username,"email":usuarioobj.email})
        uri="/comerciax/admincom/usuario/view/" + idusuario 
        edituri = "/comerciax/admincom/usuario/edit/" + idusuario + "/"
        return render_to_response("form/form_edit.html",{'tipocliente':'2','form':form,'title':'Usuario', 'form_name':'Editar Usuario','form_description':'Editar el usuario seleccionado','controlador':'Usuario','accion':editusuario,
                                                                  'cancelbtn':uri},context_instance = RequestContext(request))
                
@login_required
def changepassword(request,idusuario):
    if User.objects.get(pk=request.user.id).is_superuser==True:
        if request.method == 'POST':
            form = FChange_passwordadm(request.POST)
            if form.is_valid():
                usuarioobj = User.objects.get(pk=idusuario)
                #chequear que la contraseya anterior es la correcta
                    #todo ok se puede cambiar la contraseya
                usuarioobj.set_password(form.cleaned_data['clave_nueva'])
                usuarioobj.save()
                return viewusuario(request, idusuario)
        else:
            form2 = FChange_passwordadm()
            uri="/comerciax/admincom/usuario/view/" + idusuario 
            return render_to_response("admincomerciax/form_changepass.html",{'form':form2,'title':'Usuario', 'form_name':'Cambiar clave','form_description':'Cambiar el valor de la clave','controlador':'Usuario','accion':changepassword,
                                                        'idusuario':idusuario,'cancelbtn':uri},context_instance = RequestContext(request))

    
    if not request.user.has_perm('auth.add_user'):
        return render_to_response("denegado.html",locals(),context_instance = RequestContext(request))
    if request.method == 'POST':
        form = FChange_password(request.POST)
        if form.is_valid():
            usuarioobj = User.objects.get(pk=idusuario)
            #chequear que la contraseya anterior es la correcta
            if usuarioobj.check_password(form.cleaned_data['clave_actual']) :
                #todo ok se puede cambiar la contraseya
                usuarioobj.set_password(form.cleaned_data['clave_nueva'])
                usuarioobj.save()
                return viewusuario(request, idusuario)
            else :
                l=["La clave actual introducida no coincide con la clave del usuario, por favor vuelva a intentarlo"]
                uri="/comerciax/admincom/usuario/view/" + idusuario 
                return render_to_response("admincomerciax/form_changepass.html",{'form':form,'title':'Usuario', 'form_name':'Cambiar clave','form_description':'Cambiar el valor de la clave','controlador':'Usuario','accion':changepassword,
                                                    'idusuario':idusuario,'cancelbtn':uri, 'error2':l},context_instance = RequestContext(request))
    else:
        form2 = FChange_password()
        uri="/comerciax/admincom/usuario/view/" + idusuario 
        return render_to_response("admincomerciax/form_changepass.html",{'form':form2,'title':'Usuario', 'form_name':'Cambiar clave','form_description':'Cambiar el valor de la clave','controlador':'Usuario','accion':changepassword,
                                                    'idusuario':idusuario,'cancelbtn':uri},context_instance = RequestContext(request))

@login_required
def delusuario(request,idusuario):
    if not request.user.has_perm('auth.add_user'):
        return render_to_response("denegado.html",locals(),context_instance = RequestContext(request))
    usuarioobj = User.objects.get(pk=idusuario)
    try:
        usuarioobj.delete()
        #return HttpResponseRedirect('/comerciax/admincom/usuario/index')
    except  Exception, e:
        usuarioobj.is_active = False
        usuarioobj.save()
        
    return HttpResponseRedirect('/comerciax/admincom/usuario/index')
        #c = "No se puede eliminar el usuario, posibles causas este siendo utilizada por algún otro registro de la BD"
        #return viewusuario(request, idusuario, c)

@login_required
def provincia(request):
    if not request.user.has_perm('admincomerciax.provincias'):
        return render_to_response("denegado.html",locals(),context_instance = RequestContext(request))
    return render_to_response("admincomerciax/indexprovincia.html",locals(),context_instance = RequestContext(request))

def get_provincias_list(request):
    #prepare the params

    #initial querySet
    querySet = Provincias.objects.all()
    #columnIndexNameMap is required for correct sorting behavior
    columnIndexNameMap = { 0: 'codigo_provincia', 1: 'descripcion_provincia' }
    #model fields listed in searchableColumns will be used for filtering (Search)
    searchableColumns = ['descripcion_provincia']
    #path to template used to generate json
    jsonTemplatePath = 'admincomerciax/json/json_provincias.txt'

    #call to generic function from utils
    return get_datatables_records(request, querySet, columnIndexNameMap, searchableColumns, jsonTemplatePath)

@login_required    
def addprovincia(request):
    if not request.user.has_perm('admincomerciax.provincias'):
        return render_to_response("denegado.html",locals(),context_instance = RequestContext(request))
    c = None
    l = []
    if request.method == 'POST':
        form = Provincia(request.POST)
        if form.is_valid():
            provincia_name = form.cleaned_data['provincia']
            myprovincia = Provincias()
            myprovincia.codigo_provincia = uuid4() 
            myprovincia.descripcion_provincia = provincia_name
            try:
                myprovincia.save()
                if request.POST.__contains__('submit1'):
                    return HttpResponseRedirect('/comerciax/admincom/provincia/view/' + myprovincia.codigo_provincia.__str__())
                else:
                    form = Provincia()
            except Exception, e:
                exc_info = e.__str__() # sys.exc_info()[:1]
                c = exc_info.find("DETAIL:")
                if c < 0:
                    l = l + ["Error Fatal."]
                else:
                    c = exc_info[c + 7:]
                    l=l+[c]
    else:
        form = Provincia()
    uri="/comerciax/admincom/provincia/index" 
    return render_to_response("form/form_add.html",{'form':form,'title':'Provincia', 'form_name':'Insetar Provincia','form_description':'Introducir una nueva provincia a la base de datos','controlador':'Provincia','accion':'addprovincia',
                                                    'cancelbtn':uri,'error2':l},context_instance = RequestContext(request))

@login_required    
def viewprovincia(request,idprov):
    if not request.user.has_perm('admincomerciax.provincias'):
        return render_to_response("denegado.html",locals(),context_instance = RequestContext(request))
    provinciaobj = Provincias.objects.get(pk=idprov)
    provincia_name = provinciaobj.descripcion_provincia
    
    return render_to_response("admincomerciax/viewprovincia.html",{'provincia_name':provincia_name,'provincia_id':idprov},context_instance = RequestContext(request))

@login_required
def editprovincia(request,idprov):
    if not request.user.has_perm('admincomerciax.provincias'):
        return render_to_response("denegado.html",locals(),context_instance = RequestContext(request))
    c = None
    l = []
    if request.method == 'POST':
        form = Provincia(request.POST)
        if form.is_valid():
            provincia = Provincias.objects.get(pk=idprov)
            provincia.descripcion_provincia = form.cleaned_data['provincia']
            try:
                provincia.save()
                return viewprovincia(request, idprov)
            except Exception, e:
                exc_info = e.__str__() # sys.exc_info()[:1]
                c = exc_info.find("DETAIL:")
                if c < 0:
                    l = l + ["Error Fatal."]
                else:
                    c = exc_info[c + 7:]
                    l=l+[c]
                uri="/comerciax/admincom/provincia/view/" + idprov 
                edituri = "/comerciax/admincom/provincia/edit/" + idprov + "/"
                return render_to_response("form/form_edit.html",{'tipocliente':'2','form':form,'title':'Provincia', 'form_name':'Editar Provincia','form_description':'Editar la provincia seleccionada','controlador':'Provincia','accion':edituri,
                                                                  'cancelbtn':uri, 'error2':l},context_instance = RequestContext(request))
    else:
        provinciaobj = Provincias.objects.get(pk=idprov)
        form = Provincia(initial={"provincia":provinciaobj.descripcion_provincia})
        uri="/comerciax/admincom/provincia/view/" + idprov 
        edituri = "/comerciax/admincom/provincia/edit/" + idprov + "/"
        return render_to_response("form/form_edit.html",{'tipocliente':'2','form':form,'title':'Provincia', 'form_name':'Editar Provincia','form_description':'Editar la provincia seleccionada','controlador':'Provincia','accion':edituri
                                                         , 'cancelbtn':uri},context_instance = RequestContext(request))

    
@login_required
def delprovincia(request,idprov):
    if not request.user.has_perm('admincomerciax.provincias'):
        return render_to_response("denegado.html",locals(),context_instance = RequestContext(request))
    provinciaobj = Provincias.objects.get(pk=idprov)
    try:
        provinciaobj.delete()
        return HttpResponseRedirect('/comerciax/admincom/provincia/index')
        #return render_to_response("admincomerciax/indexprovincia.html")
    except  Exception, e:
        c = "No se puede eliminar la provincia, posibles causas este siendo utilizada por algún otro registro de la BD"
        provincia_name = provinciaobj.descripcion_provincia
        return render_to_response("admincomerciax/viewprovincia.html",{'provincia_name':provinciaobj.descripcion_provincia,'provincia_id':idprov, 'error2':c},context_instance = RequestContext(request))
    
#############################################################
#        ORGANISMO
#############################################################
@login_required
def organismo(request):
    if not request.user.has_perm('admincomerciax.organismo'):
        return render_to_response("denegado.html",locals(),context_instance = RequestContext(request))
    return render_to_response("admincomerciax/indexorganismo.html",locals(),context_instance = RequestContext(request))

def get_organismo_list(request):
    #initial querySet
    querySet = Organismo.objects.all()
    #columnIndexNameMap is required for correct sorting behavior
    columnIndexNameMap = {0:'codigo_organismo', 1: 'codigo_organismo', 2 : 'siglas_organismo' }
    #model fields listed in searchableColumns will be used for filtering (Search)
    searchableColumns = ['codigo_organismo','siglas_organismo']
    #path to template used to generate json
    jsonTemplatePath = 'admincomerciax/json/json_organismo.txt'
    #call to generic function from utils
    return get_datatables_records(request, querySet, columnIndexNameMap, searchableColumns, jsonTemplatePath)

@login_required    
def addorganismo(request):
    if not request.user.has_perm('admincomerciax.organismo'):
        return render_to_response("denegado.html",locals(),context_instance = RequestContext(request))
    c = None
    l = []
    if request.method == 'POST':
        form = FOrganismo(request.POST)
        if form.is_valid():
            myorg = Organismo()
            myorg.id = uuid4()
            myorg.codigo_organismo = form.cleaned_data['codigo']
            myorg.siglas_organismo = form.cleaned_data['siglas'].upper() 
            try:
                myorg.save()
                if request.POST.__contains__('submit1'):
                    return HttpResponseRedirect('/comerciax/admincom/organismo/view/' + myorg.id.__str__())
                else:
                    form = FOrganismo()
            except Exception, e:
                exc_info = e.__str__() # sys.exc_info()[:1]
                c = exc_info.find("DETAIL:")
                if c < 0:
                    l = l + ["Error Fatal."]
                else:
                    c = exc_info[c + 7:]
                    l=l+[c]
    else:
        form = FOrganismo()
    uri="/comerciax/admincom/organismo/index" 
    return render_to_response("form/form_add.html",{'form':form,'title':'Organismo', 'form_name':'Insertar Organismo','form_description':'Introducir un nuevo organismo a la base de datos','controlador':'Organismo','accion':'addorganismo',
                                                    'cancelbtn':uri,'error2':l},context_instance = RequestContext(request))

@login_required    
def vieworganismo(request,idorg):
    if not request.user.has_perm('admincomerciax.organismo'):
        return render_to_response("denegado.html",locals(),context_instance = RequestContext(request))
    organismoobj = Organismo.objects.get(pk=idorg)
    organismo_sigla = organismoobj.siglas_organismo
    organismo_code = organismoobj.codigo_organismo
    
    union = Union.objects.filter(organismo=idorg)
    return render_to_response("admincomerciax/vieworganismo.html",{'organismo_name':organismo_sigla,'organismo_code':organismo_code,'organismo_id':idorg,'uniones':union},context_instance = RequestContext(request))

@login_required
def editorganismo(request,idorg):
    if not request.user.has_perm('admincomerciax.organismo'):
        return render_to_response("denegado.html",locals(),context_instance = RequestContext(request))
    c = None
    l = []
    if request.method == 'POST':
        form = FOrganismo(request.POST)
        if form.is_valid():
            organismo = Organismo.objects.get(pk=idorg)
            organismo.codigo_organismo = form.cleaned_data['codigo']
            organismo.siglas_organismo= form.cleaned_data['siglas'].upper()
            try:
                organismo.save()
                return vieworganismo(request, idorg)
            except Exception, e:
                exc_info = e.__str__() # sys.exc_info()[:1]
                c = exc_info.find("DETAIL:")
                if c < 0:
                    l = l + ["Error Fatal."]
                else:
                    c = exc_info[c + 7:]
                    l=l+[c]
                uri="/comerciax/admincom/organismo/view/" + idorg 
                edituri = "/comerciax/admincom/organismo/edit/" + idorg + "/"
                return render_to_response("form/form_edit.html",{'tipocliente':'2','form':form,'title':'Organismo', 'form_name':'Editar Organismo','form_description':'Editar el organismo seleccionado','controlador':'Organismo','accion':edituri
                                                         , 'cancelbtn':uri, 'error2':l},context_instance = RequestContext(request))
    else:
        organismoobj = Organismo.objects.get(pk=idorg)
        form = FOrganismo(initial={"siglas":organismoobj.siglas_organismo, "codigo":organismoobj.codigo_organismo})
        uri="/comerciax/admincom/organismo/view/" + idorg 
        edituri = "/comerciax/admincom/organismo/edit/" + idorg + "/"
        return render_to_response("form/form_edit.html",{'tipocliente':'2','form':form,'title':'Organismo', 'form_name':'Editar Organismo','form_description':'Editar el organismo seleccionado','controlador':'Organismo','accion':edituri
                                                         , 'cancelbtn':uri},context_instance = RequestContext(request))

@login_required        
def unionadd(request,idorg):
    if not request.user.has_perm('admincomerciax.organismo'):
        return render_to_response("denegado.html",locals(),context_instance = RequestContext(request))
    c = None
    l = []
    if request.method == 'POST':
        form = FUnion(request.POST)
        if form.is_valid():
            myunion = Union()
            myunion.id = uuid4()
            myunion.descripcion = form.cleaned_data['union']
            myunion.organismo = Organismo.objects.get(pk=idorg)
            try:
                myunion.save()
                if request.POST.__contains__('submit1'):
                    return HttpResponseRedirect('/comerciax/admincom/organismo/view/' + idorg)
                else:
                    form = FUnion()
            
            except Exception, e:
                exc_info = e.__str__() # sys.exc_info()[:1]
                c = exc_info.find("DETAIL:")
                if c < 0:
                    l = l + ["Error Fatal."]
                else:
                    c = exc_info[c + 7:]
                    l=l+[c]
                    
               #transaction.rollback()
                
                form = FUnion(request.POST)
                uri="/comerciax/admincom/organismo/view/"  + idorg
                return render_to_response("form/form_add.html",{'form':form,'title':'Unión', 'form_name':'Insertar unión','form_description':'Introducir una nueva unión a la base de datos','controlador':'Organismo','accion':'unionadd',
                                                    'cancelbtn':uri, 'error2':l},context_instance = RequestContext(request))
            #else:
                #transaction.commit()
    else:
        form = FUnion()
    uri="/comerciax/admincom/organismo/view/"  + idorg
    return render_to_response("form/form_add.html",{'form':form,'title':'Unión', 'form_name':'Insertar unión','form_description':'Introducir una nueva unión a la base de datos','controlador':'Organismo','accion':'unionadd',
                                                    'cancelbtn':uri, 'error2':l},context_instance = RequestContext(request))

@login_required
def delunion(request,idorg,idunion):
    if not request.user.has_perm('admincomerciax.organismo'):
        return render_to_response("denegado.html",locals(),context_instance = RequestContext(request))
    try:
        unionobj = Union.objects.get(pk=idunion)
        unionobj.delete()
        union = Union.objects.filter(organismo=idorg)
        
        json_serializer = serializers.get_serializer("json")()
        response = HttpResponse()
        response["Content-type"] = "text/json"
        json_serializer.serialize(union,ensure_ascii = False, stream = response)
        return response
    
    except Exception, e:
        error2 = "No se puede eliminar la Unión, posibles causas problema de conexion con la BD" 
        return HttpResponse(json.dumps({'error':True, 'message':error2}),mimetype=u'application/json')

@login_required
def get_uniones(request,idorg):
    if not request.user.has_perm('admincomerciax.organismo'):
        return render_to_response("denegado.html",locals(),context_instance = RequestContext(request))
    try:
        union = Union.objects.filter(organismo=idorg)
        
        json_serializer = serializers.get_serializer("json")()
        response = HttpResponse()
        response["Content-type"] = "text/json"
        json_serializer.serialize(union,ensure_ascii = False, stream = response)
        return response
    
    except Exception, e:
        error2 = "No se puede eliminar la Unión, posibles causas problema de conexion con la BD" 
        return HttpResponse(json.dumps({'error':True, 'message':error2}),mimetype=u'application/json')


@login_required
def delorganismo(request,idorg):
    if not request.user.has_perm('admincomerciax.organismo'):
        return render_to_response("denegado.html",locals(),context_instance = RequestContext(request))
    organismoobj = Organismo.objects.get(pk=idorg)
    try:
        organismoobj.delete()
        return HttpResponseRedirect('/comerciax/admincom/organismo/index')
    except  Exception, e:
        c = "No se puede eliminar el organismo, posibles causas este siendo utilizado por algún otro registro de la BD"
        organismo_sigla = organismoobj.siglas_organismo
        organismo_code = organismoobj.codigo_organismo
        union = Union.objects.filter(organismo=idorg)
        return render_to_response("admincomerciax/vieworganismo.html",{'uniones':union,'organismo_name':organismo_sigla,'organismo_code':organismo_code,'organismo_id':idorg,'error2':c},context_instance = RequestContext(request))
    
#############################################################
#        SUCURSAL
#############################################################
@login_required
def sucursal(request):
    if not request.user.has_perm('admincomerciax.sucursal'):
        return render_to_response("denegado.html",locals(),context_instance = RequestContext(request))
    return render_to_response("admincomerciax/indexsucursal.html",locals(),context_instance = RequestContext(request))

def get_sucursal_list(request):
    #initial querySet
    querySet = Sucursales.objects.all()
    #columnIndexNameMap is required for correct sorting behavior
    columnIndexNameMap = { 0: 'sucursal_descripcion'}
    #model fields listed in searchableColumns will be used for filtering (Search)
    searchableColumns = ['sucursal_descripcion']
    #path to template used to generate json
    jsonTemplatePath = 'admincomerciax/json/json_sucursal.txt'
    #call to generic function from utils
    return get_datatables_records(request, querySet, columnIndexNameMap, searchableColumns, jsonTemplatePath)

@login_required    
def addsucursal(request):
    if not request.user.has_perm('admincomerciax.sucursal'):
        return render_to_response("denegado.html",locals(),context_instance = RequestContext(request))
    c = None
    l = []
    if request.method == 'POST':
        form = FSucursal(request.POST)
        if form.is_valid():
            mysucursal = Sucursales()
            mysucursal.id_sucursal = uuid4()
            mysucursal.sucursal_descripcion = form.cleaned_data['sucursal'].upper()
            try:
                mysucursal.save()
                if request.POST.__contains__('submit1'):
                    return HttpResponseRedirect('/comerciax/admincom/sucursal/view/' + mysucursal.id_sucursal.__str__())
                else:
                    form = FSucursal()
            except Exception, e:
                exc_info = e.__str__() # sys.exc_info()[:1]
                c = exc_info.find("DETAIL:")
                if c < 0:
                    l = l + ["Error Fatal."]
                else:
                    c = exc_info[c + 7:]
                    l=l+[c]
    else:
        form = FSucursal()
    uri="/comerciax/admincom/sucursal/index" 
    return render_to_response("form/form_add.html",{'form':form,'title':'Sucursal', 'form_name':'Insertar Sucursal','form_description':'Introducir una nueva sucursal a la base de datos','controlador':'Sucursal','accion':'addsucursal',
                                                    'cancelbtn':uri, 'error2':l},context_instance = RequestContext(request))

@login_required    
def viewsucursal(request,idsuc):
    if not request.user.has_perm('admincomerciax.sucursal'):
        return render_to_response("denegado.html",locals(),context_instance = RequestContext(request))
    sucursalobj = Sucursales.objects.get(pk=idsuc)
    sucursal_desc = sucursalobj.sucursal_descripcion
    return render_to_response("admincomerciax/viewsucursal.html",{'sucursal_name':sucursal_desc, 'sucursal_id':idsuc},context_instance = RequestContext(request))

@login_required
def editsucursal(request,idsuc):
    if not request.user.has_perm('admincomerciax.sucursal'):
        return render_to_response("denegado.html",locals(),context_instance = RequestContext(request))
    c = None
    l = []
    if request.method == 'POST':
        form = FSucursal(request.POST)
        if form.is_valid():
            sucursal = Sucursales.objects.get(pk=idsuc)
            sucursal.sucursal_descripcion = form.cleaned_data['sucursal'].upper()
            try:
                sucursal.save()
                return viewsucursal(request, idsuc)
            except Exception, e:
                exc_info = e.__str__() # sys.exc_info()[:1]
                c = exc_info.find("DETAIL:")
                if c < 0:
                    l = l + ["Error Fatal."]
                else:
                    c = exc_info[c + 7:]
                    l=l+[c]
                uri="/comerciax/admincom/sucursal/view/" + idsuc 
                edituri = "/comerciax/admincom/sucursal/edit/" + idsuc + "/"
                return render_to_response("form/form_edit.html",{'tipocliente':'2','form':form,'title':'Sucursal', 'form_name':'Editar Sucursal','form_description':'Editar la sucursal seleccionada','controlador':'Sucursal','accion':edituri
                                                         , 'cancelbtn':uri,'error2':l},context_instance = RequestContext(request))
    else:
        sucursalobj = Sucursales.objects.get(pk=idsuc)
        form = FSucursal(initial={"sucursal":sucursalobj.sucursal_descripcion})
        uri="/comerciax/admincom/sucursal/view/" + idsuc 
        edituri = "/comerciax/admincom/sucursal/edit/" + idsuc + "/"
        return render_to_response("form/form_edit.html",{'tipocliente':'2','form':form,'title':'Sucursal', 'form_name':'Editar Sucursal','form_description':'Editar la sucursal seleccionada','controlador':'Sucursal','accion':edituri
                                                         , 'cancelbtn':uri,'error2':l},context_instance = RequestContext(request))

@login_required
def delsucursal(request,idsuc):
    if not request.user.has_perm('admincomerciax.sucursal'):
        return render_to_response("denegado.html",locals(),context_instance = RequestContext(request))
    sucursalobj = Sucursales.objects.get(pk=idsuc)
    try:
        sucursalobj.delete()
        return HttpResponseRedirect('/comerciax/admincom/sucursal/index')
    except Exception, e:
        c = "No se puede eliminar la sucursal, posibles causas este siendo utilizada por algún otro registro de la BD"
        sucursal_desc = sucursalobj.sucursal_descripcion
        return render_to_response("admincomerciax/viewsucursal.html",{'sucursal_name':sucursal_desc, 'sucursal_id':idsuc, 'error2':c},context_instance = RequestContext(request))
    
#############################################################
#        AREA
#############################################################
@login_required
def area(request):
    if not request.user.has_perm('admincomerciax.area'):
        return render_to_response("denegado.html",locals(),context_instance = RequestContext(request))
    return render_to_response("admincomerciax/indexarea.html",locals(),context_instance = RequestContext(request))

def get_area_list(request):
    #initial querySet
    querySet = Area.objects.all()
    #columnIndexNameMap is required for correct sorting behavior
    columnIndexNameMap = { 0: 'descripcion'}
    #model fields listed in searchableColumns will be used for filtering (Search)
    searchableColumns = ['descripcion']
    #path to template used to generate json
    jsonTemplatePath = 'admincomerciax/json/json_area.txt'
    #call to generic function from utils
    return get_datatables_records(request, querySet, columnIndexNameMap, searchableColumns, jsonTemplatePath)


@login_required    
def addarea(request):
    if not request.user.has_perm('admincomerciax.area'):
        return render_to_response("denegado.html",locals(),context_instance = RequestContext(request))
    c = None
    l = []
    if request.method == 'POST':
        form = FArea(request.POST)
        if form.is_valid():
            myarea = Area()
            myarea.id = uuid4()
            myarea.descripcion = form.cleaned_data['area']
            try:
                myarea.save()
                if request.POST.__contains__('submit1'):
                    return HttpResponseRedirect('/comerciax/admincom/area/view/' + myarea.id.__str__())
                else:
                    form = FArea()
            except Exception, e:
                exc_info = e.__str__() # sys.exc_info()[:1]
                c = exc_info.find("DETAIL:")
                if c < 0:
                    l = l + ["Error Fatal."]
                else:
                    c = exc_info[c + 7:]
                    l=l+[c]
    else:
        form = FArea()
    uri="/comerciax/admincom/area/index" 
    return render_to_response("form/form_add.html",{'form':form,'title':'Área', 'form_name':'Insertar Área','form_description':'Introducir una nueva área a la base de datos','controlador':'Área','accion':'addarea',
                                                    'cancelbtn':uri, 'error2':l},context_instance = RequestContext(request))

@login_required    
def viewarea(request,idarea):
    if not request.user.has_perm('admincomerciax.area'):
        return render_to_response("denegado.html",locals(),context_instance = RequestContext(request))
    areaobj = Area.objects.get(pk=idarea)
    desc = areaobj.descripcion
    return render_to_response("admincomerciax/viewarea.html",{'area_name':desc, 'area_id':idarea},context_instance = RequestContext(request))

@login_required
def editarea(request,idarea):
    if not request.user.has_perm('admincomerciax.area'):
        return render_to_response("denegado.html",locals(),context_instance = RequestContext(request))
    c = None
    l = []
    if request.method == 'POST':
        form = FArea(request.POST)
        if form.is_valid():
            area = Area.objects.get(pk=idarea)
            area.descripcion = form.cleaned_data['area']
            try:
                area.save()
                return viewarea(request, idarea)
            except Exception, e:
                exc_info = e.__str__() # sys.exc_info()[:1]
                c = exc_info.find("DETAIL:")
                if c < 0:
                    l = l + ["Error Fatal."]
                else:
                    c = exc_info[c + 7:]
                    l=l+[c]
                uri="/comerciax/admincom/area/view/" + idarea 
                edituri = "/comerciax/admincom/area/edit/" + idarea + "/"
                return render_to_response("form/form_edit.html",{'tipocliente':'2','form':form,'title':'Área', 'form_name':'Editar Área','form_description':'Editar el área seleccionada','controlador':'Área','accion':edituri
                                                         , 'cancelbtn':uri,'error2':l},context_instance = RequestContext(request))
    else:
        areaobj = Area.objects.get(pk=idarea)
        form = FArea(initial={"area":areaobj.descripcion})
        uri="/comerciax/admincom/area/view/" + idarea 
        edituri = "/comerciax/admincom/area/edit/" + idarea + "/"
        return render_to_response("form/form_edit.html",{'tipocliente':'2','form':form,'title':'Área', 'form_name':'Editar Área','form_description':'Editar el área seleccionada','controlador':'Área','accion':edituri
                                                         , 'cancelbtn':uri,'error2':l},context_instance = RequestContext(request))

@login_required
def delarea(request,idarea):
    if not request.user.has_perm('admincomerciax.area'):
        return render_to_response("denegado.html",locals(),context_instance = RequestContext(request))
    areaobj = Area.objects.get(pk=idarea)
    try:
        areaobj.delete()
        return HttpResponseRedirect('/comerciax/admincom/area/index')
    except Exception, e:
        c = "No se puede eliminar el área, posibles causas: esté siendo utilizada por algún otro registro de la BD"
        desc = areaobj.descripcion
        return render_to_response("admincomerciax/viewarea.html",{'area_name':desc, 'area_id':idarea, 'error2':c},context_instance = RequestContext(request))
    
#############################################################
#        CAUSAS DEL RECHAZO
#############################################################
@login_required
def causar(request):
    if not request.user.has_perm('admincomerciax.causarechazo'):
        return render_to_response("denegado.html",locals(),context_instance = RequestContext(request))
    return render_to_response("admincomerciax/indexcausar.html",locals(),context_instance = RequestContext(request))

def get_causar_list(request):
    #initial querySet
    querySet = CausasRechazo.objects.all()
    #columnIndexNameMap is required for correct sorting behavior
    columnIndexNameMap = { 0: 'descripcion'}
    #model fields listed in searchableColumns will be used for filtering (Search)
    searchableColumns = ['descripcion']
    #path to template used to generate json
    jsonTemplatePath = 'admincomerciax/json/json_causar.txt'
    #call to generic function from utils
    return get_datatables_records(request, querySet, columnIndexNameMap, searchableColumns, jsonTemplatePath)

@login_required    
def addcausar(request):
    if not request.user.has_perm('admincomerciax.causarechazo'):
        return render_to_response("denegado.html",locals(),context_instance = RequestContext(request))
    c = None
    l = []
    if request.method == 'POST':
        form = FCausar(request.POST)
        if form.is_valid():
            mycausar = CausasRechazo()
            mycausar.id = uuid4()
            mycausar.descripcion = form.cleaned_data['causa']
            try:
                mycausar.save()
                if request.POST.__contains__('submit1'):
                    return HttpResponseRedirect('/comerciax/admincom/causar/view/' + mycausar.id.__str__())
                else:
                    form = FCausar()
            except Exception, e:
                exc_info = e.__str__() # sys.exc_info()[:1]
                c = exc_info.find("DETAIL:")
                if c < 0:
                    l = l + ["Error Fatal."]
                else:
                    c = exc_info[c + 7:]
                    l=l+[c]
    else:
        form = FCausar()
    uri="/comerciax/admincom/causar/index" 
    return render_to_response("form/form_add.html",{'form':form,'title':'Causas de Rechazo', 'form_name':'Insertar Causa de rechazo','form_description':'Introducir una nueva causa de rechazo a la base de datos','controlador':'Causa de Rechazo','accion':'addcausar',
                                                    'cancelbtn':uri, 'error2':l},context_instance = RequestContext(request))

@login_required    
def viewcausar(request,idcausar):
    if not request.user.has_perm('admincomerciax.causarechazo'):
        return render_to_response("denegado.html",locals(),context_instance = RequestContext(request))
    causarobj = CausasRechazo.objects.get(pk=idcausar)
    desc = causarobj.descripcion
    return render_to_response("admincomerciax/viewcausar.html",{'causar_name':desc, 'causar_id':idcausar},context_instance = RequestContext(request))

@login_required
def editcausar(request,idcausar):
    if not request.user.has_perm('admincomerciax.causarechazo'):
        return render_to_response("denegado.html",locals(),context_instance = RequestContext(request))
    c = None
    l = []
    if request.method == 'POST':
        form = FCausar(request.POST)
        if form.is_valid():
            causar = CausasRechazo.objects.get(pk=idcausar)
            causar.descripcion = form.cleaned_data['causa']
            try:
                causar.save()
                return viewcausar(request, idcausar)
            except Exception, e:
                exc_info = e.__str__() # sys.exc_info()[:1]
                c = exc_info.find("DETAIL:")
                if c < 0:
                    l = l + ["Error Fatal."]
                else:
                    c = exc_info[c + 7:]
                    l=l+[c]
                uri="/comerciax/admincom/causar/view/" + idcausar 
                edituri = "/comerciax/admincom/causar/edit/" + idcausar + "/"
                return render_to_response("form/form_edit.html",{'tipocliente':'2','form':form,'title':'Causas de Rechazo', 'form_name':'Editar Causa de rechazo','form_description':'Editar la causa de rechazo seleccionada','controlador':'Causa de rechazo','accion':edituri
                                                         , 'cancelbtn':uri,'error2':l},context_instance = RequestContext(request))
    else:
        causarobj = CausasRechazo.objects.get(pk=idcausar)
        form = FCausar(initial={"causa":causarobj.descripcion})
        uri="/comerciax/admincom/causar/view/" + idcausar 
        edituri = "/comerciax/admincom/causar/edit/" + idcausar + "/"
        return render_to_response("form/form_edit.html",{'tipocliente':'2','form':form,'title':'Causas de Rechazo', 'form_name':'Editar Causa de rechazo','form_description':'Editar la causa de rechazo seleccionada','controlador':'Causa de rechazo','accion':edituri
                                                         , 'cancelbtn':uri,'error2':l},context_instance = RequestContext(request))

@login_required
def delcausar(request,idcausar):
    if not request.user.has_perm('admincomerciax.causarechazo'):
        return render_to_response("denegado.html",locals(),context_instance = RequestContext(request))
    causarobj = CausasRechazo.objects.get(pk=idcausar)
    try:
        causarobj.delete()
        return HttpResponseRedirect('/comerciax/admincom/causar/index')
    except Exception, e:
        c = "No se puede eliminar la causa de rechazo, posibles causas este siendo utilizada por algún otro registro de la BD"
        desc = causarobj.descripcion
        return render_to_response("admincomerciax/viewcausar.html",{'causa_name':desc, 'causa_id':idcausar, 'error2':c},context_instance = RequestContext(request))

#############################################################
#        UNIDAD DE MEDIDA
#############################################################
@login_required
def unidadm(request):
    if not request.user.has_perm('admincomerciax.umedida'):
        return render_to_response("denegado.html",locals(),context_instance = RequestContext(request))
    return render_to_response("admincomerciax/indexunidadm.html",locals(),context_instance = RequestContext(request))

def get_unidadm_list(request):
    #initial querySet
    querySet = Umedida.objects.all()
    #columnIndexNameMap is required for correct sorting behavior
    columnIndexNameMap = { 0: 'descripcion'}
    #model fields listed in searchableColumns will be used for filtering (Search)
    searchableColumns = ['descripcion']
    #path to template used to generate json
    jsonTemplatePath = 'admincomerciax/json/json_unidadm.txt'
    #call to generic function from utils
    return get_datatables_records(request, querySet, columnIndexNameMap, searchableColumns, jsonTemplatePath)

@login_required    
def addunidadm(request):
    if not request.user.has_perm('admincomerciax.umedida'):
        return render_to_response("denegado.html",locals(),context_instance = RequestContext(request))
    c = None
    l = []
    if request.method == 'POST':
        form = FUnidadm(request.POST)
        if form.is_valid():
            myunidadm = Umedida()
            myunidadm.id = uuid4()
            myunidadm.descripcion = form.cleaned_data['unidad']
            try:
                myunidadm.save()
                if request.POST.__contains__('submit1'):
                    return HttpResponseRedirect('/comerciax/admincom/unidadm/view/' + myunidadm.id.__str__())
                else:
                    form = FUnidadm()
            except Exception, e:
                exc_info = e.__str__() # sys.exc_info()[:1]
                c = exc_info.find("DETAIL:")
                if c < 0:
                    l = l + ["Error Fatal."]
                else:
                    c = exc_info[c + 7:]
                    l=l+[c]
    else:
        form = FUnidadm()
    uri="/comerciax/admincom/unidadm/index" 
    return render_to_response("form/form_add.html",{'form':form,'title':'Unidad de medida', 'form_name':'Insertar Unidad de medida','form_description':'Introducir una nueva unidad de medida a la base de datos','controlador':'Unidad de medida','accion':'addunidadm',
                                                    'cancelbtn':uri, 'error2':l},context_instance = RequestContext(request))

@login_required    
def viewunidadm(request,idunidadm):
    if not request.user.has_perm('admincomerciax.umedida'):
        return render_to_response("denegado.html",locals(),context_instance = RequestContext(request))
    unidadmobj = Umedida.objects.get(pk=idunidadm)
    desc = unidadmobj.descripcion
    return render_to_response("admincomerciax/viewunidadm.html",{'unidadm_name':desc, 'unidadm_id':idunidadm},context_instance = RequestContext(request))

@login_required
def editunidadm(request,idunidadm):
    if not request.user.has_perm('admincomerciax.umedida'):
        return render_to_response("denegado.html",locals(),context_instance = RequestContext(request))
    c = None
    l = []
    if request.method == 'POST':
        form = FUnidadm(request.POST)
        if form.is_valid():
            unidadm = Umedida.objects.get(pk=idunidadm)
            unidadm.descripcion = form.cleaned_data['unidad']
            try:
                unidadm.save()
                return viewunidadm(request, idunidadm)
            except Exception, e:
                exc_info = e.__str__() # sys.exc_info()[:1]
                c = exc_info.find("DETAIL:")
                if c < 0:
                    l = l + ["Error Fatal."]
                else:
                    c = exc_info[c + 7:]
                    l=l+[c]
                uri="/comerciax/admincom/unidadm/view/" + idunidadm 
                edituri = "/comerciax/admincom/unidadm/edit/" + idunidadm + "/"
                return render_to_response("form/form_edit.html",{'tipocliente':'2','form':form,'title':'Causas de Rechazo', 'form_name':'Editar Causa de rechazo','form_description':'Editar la causa de rechazo seleccionada','controlador':'Causa de rechazo','accion':edituri
                                                         , 'cancelbtn':uri,'error2':l},context_instance = RequestContext(request))
    else:
        unidadmobj = Umedida.objects.get(pk=idunidadm)
        form = FUnidadm(initial={"unidad":unidadmobj.descripcion})
        uri="/comerciax/admincom/unidadm/view/" + idunidadm 
        edituri = "/comerciax/admincom/unidadm/edit/" + idunidadm + "/"
        return render_to_response("form/form_edit.html",{'tipocliente':'2','form':form,'title':'Causas de Rechazo', 'form_name':'Editar Causa de rechazo','form_description':'Editar la causa de rechazo seleccionada','controlador':'Causa de rechazo','accion':edituri
                                                         , 'cancelbtn':uri,'error2':l},context_instance = RequestContext(request))

@login_required
def delunidadm(request,idunidadm):
    if not request.user.has_perm('admincomerciax.umedida'):
        return render_to_response("denegado.html",locals(),context_instance = RequestContext(request))
    unidadmobj = Umedida.objects.get(pk=idunidadm)
    try:
        unidadmobj.delete()
        return HttpResponseRedirect('/comerciax/admincom/unidadm/index')
    except Exception, e:
        c = "No se puede eliminar la unidad de medida, posibles causas este siendo utilizada por algún otro registro de la BD"
        desc = unidadmobj.descripcion
        return render_to_response("admincomerciax/viewunidadm.html",{'causa_name':desc, 'causa_id':idunidadm, 'error2':c},context_instance = RequestContext(request))
    
#############################################################
#        FORMA DE PAGO
#############################################################
@login_required
def formap(request):
    if not request.user.has_perm('admincomerciax.formapago'):
        return render_to_response("denegado.html",locals(),context_instance = RequestContext(request))
    return render_to_response("admincomerciax/indexformap.html",locals(),context_instance = RequestContext(request))

def get_formap_list(request):
    #initial querySet
    querySet = FormasPago.objects.all()
    #columnIndexNameMap is required for correct sorting behavior
    columnIndexNameMap = { 0: 'descripcion'}
    #model fields listed in searchableColumns will be used for filtering (Search)
    searchableColumns = ['descripcion']
    #path to template used to generate json
    jsonTemplatePath = 'admincomerciax/json/json_formap.txt'
    #call to generic function from utils
    return get_datatables_records(request, querySet, columnIndexNameMap, searchableColumns, jsonTemplatePath)

@login_required    
def addformap(request):
    if not request.user.has_perm('admincomerciax.formapago'):
        return render_to_response("denegado.html",locals(),context_instance = RequestContext(request))
    c = None
    l = []
    if request.method == 'POST':
        form = FFormasp(request.POST)
        if form.is_valid():
            myformap = FormasPago()
            myformap.id = uuid4()
            myformap.descripcion = form.cleaned_data['forma']
            try:
                myformap.save()
                if request.POST.__contains__('submit1'):
                    return HttpResponseRedirect('/comerciax/admincom/formap/view/' + myformap.id.__str__())
                else:
                    form = FFormasp()
            except Exception, e:
                exc_info = e.__str__() # sys.exc_info()[:1]
                c = exc_info.find("DETAIL:")
                if c < 0:
                    l = l + ["Error Fatal."]
                else:
                    c = exc_info[c + 7:]
                    l=l+[c]
    else:
        form = FFormasp()
    uri="/comerciax/admincom/formap/index" 
    return render_to_response("form/form_add.html",{'form':form,'title':'Formas de pago', 'form_name':'Insertar Formas de pago','form_description':'Introducir una nueva forma de pago a la base de datos','controlador':'Formas de pago','accion':'addformap',
                                                    'cancelbtn':uri, 'error2':l},context_instance = RequestContext(request))

@login_required    
def viewformap(request,idformap):
    if not request.user.has_perm('admincomerciax.formapago'):
        return render_to_response("denegado.html",locals(),context_instance = RequestContext(request))
    formapobj = FormasPago.objects.get(pk=idformap)
    desc = formapobj.descripcion
    return render_to_response("admincomerciax/viewformap.html",{'formap_name':desc, 'formap_id':idformap},context_instance = RequestContext(request))

@login_required
def editformap(request,idformap):
    if not request.user.has_perm('admincomerciax.formapago'):
        return render_to_response("denegado.html",locals(),context_instance = RequestContext(request))
    c = None
    l = []
    if request.method == 'POST':
        form = FFormasp(request.POST)
        if form.is_valid():
            formap = FormasPago.objects.get(pk=idformap)
            formap.descripcion = form.cleaned_data['forma']
            try:
                formap.save()
                return viewformap(request, idformap)
            except Exception, e:
                exc_info = e.__str__() # sys.exc_info()[:1]
                c = exc_info.find("DETAIL:")
                if c < 0:
                    l = l + ["Error Fatal."]
                else:
                    c = exc_info[c + 7:]
                    l=l+[c]
                uri="/comerciax/admincom/formap/view/" + idformap 
                edituri = "/comerciax/admincom/formap/edit/" + idformap + "/"
                return render_to_response("form/form_edit.html",{'tipocliente':'2','form':form,'title':'Formas de pago', 'form_name':'Editar Forma de pago','form_description':'Editar la forma de pago seleccionada','controlador':'Formas de pago','accion':edituri
                                                         , 'cancelbtn':uri,'error2':l},context_instance = RequestContext(request))
    else:
        formapobj = FormasPago.objects.get(pk=idformap)
        form = FFormasp(initial={"forma":formapobj.descripcion})
        uri="/comerciax/admincom/formap/view/" + idformap 
        edituri = "/comerciax/admincom/formap/edit/" + idformap + "/"
        return render_to_response("form/form_edit.html",{'tipocliente':'2','form':form,'title':'Formas de pago', 'form_name':'Editar Forma de pago','form_description':'Editar la forma de pago seleccionada','controlador':'Formas de pago','accion':edituri
                                                         , 'cancelbtn':uri,'error2':l},context_instance = RequestContext(request))

@login_required
def delformap(request,idformap):
    if not request.user.has_perm('admincomerciax.formapago'):
        return render_to_response("denegado.html",locals(),context_instance = RequestContext(request))
    formapobj = FormasPago.objects.get(pk=idformap)
    try:
        formapobj.delete()
        return HttpResponseRedirect('/comerciax/admincom/formap/index')
    except Exception, e:
        c = "No se puede eliminar la forma de pago, posibles causas este siendo utilizada por algún otro registro de la BD"
        desc = formapobj.descripcion
        return render_to_response("admincomerciax/viewformap.html",{'causa_name':desc, 'causa_id':idformap, 'error2':c},context_instance = RequestContext(request))
    
#############################################################
#        Moneda
#############################################################
@login_required
def moneda(request):
    if not request.user.has_perm('admincomerciax.monedas'):
        return render_to_response("denegado.html",locals(),context_instance = RequestContext(request))
    return render_to_response("admincomerciax/indexmoneda.html",locals(),context_instance = RequestContext(request))

def get_moneda_list(request):
    #initial querySet
    querySet = Monedas.objects.all()
    #columnIndexNameMap is required for correct sorting behavior
    columnIndexNameMap = { 0: 'descripcion'}
    #model fields listed in searchableColumns will be used for filtering (Search)
    searchableColumns = ['descripcion']
    #path to template used to generate json
    jsonTemplatePath = 'admincomerciax/json/json_moneda.txt'
    #call to generic function from utils
    return get_datatables_records(request, querySet, columnIndexNameMap, searchableColumns, jsonTemplatePath)

@login_required    
def addmoneda(request):
    if not request.user.has_perm('admincomerciax.monedas'):
        return render_to_response("denegado.html",locals(),context_instance = RequestContext(request))
    c = None
    l = []
    if request.method == 'POST':
        form = FMoneda(request.POST)
        if form.is_valid():
            mymoneda = Monedas()
            mymoneda.id = uuid4()
            mymoneda.descripcion = form.cleaned_data['moneda'].upper()
            try:
                mymoneda.save()
                if request.POST.__contains__('submit1'):
                    return HttpResponseRedirect('/comerciax/admincom/moneda/view/' + mymoneda.id.__str__())
                else:
                    form = FMoneda()
            except Exception, e:
                exc_info = e.__str__() # sys.exc_info()[:1]
                c = exc_info.find("DETAIL:")
                if c < 0:
                    l = l + ["Error Fatal."]
                else:
                    c = exc_info[c + 7:]
                    l=l+[c]
    else:
        form = FMoneda()
    uri="/comerciax/admincom/moneda/index" 
    return render_to_response("form/form_add.html",{'form':form,'title':'Monedas', 'form_name':'Insertar Monedas','form_description':'Introducir una nueva moneda a la base de datos','controlador':'Monedas','accion':'addmoneda',
                                                    'cancelbtn':uri, 'error2':l},context_instance = RequestContext(request))

@login_required    
def viewmoneda(request,idmoneda):
    if not request.user.has_perm('admincomerciax.monedas'):
        return render_to_response("denegado.html",locals(),context_instance = RequestContext(request))
    monedaobj = Monedas.objects.get(pk=idmoneda)
    desc = monedaobj.descripcion
    return render_to_response("admincomerciax/viewmoneda.html",{'moneda_name':desc, 'moneda_id':idmoneda},context_instance = RequestContext(request))

@login_required
def editmoneda(request,idmoneda):
    if not request.user.has_perm('admincomerciax.monedas'):
        return render_to_response("denegado.html",locals(),context_instance = RequestContext(request))
    c = None
    l = []
    if request.method == 'POST':
        form = FMoneda(request.POST)
        if form.is_valid():
            moneda = Monedas.objects.get(pk=idmoneda)
            moneda.descripcion = form.cleaned_data['moneda'].upper()
            try:
                moneda.save()
                return viewmoneda(request, idmoneda)
            except Exception, e:
                exc_info = e.__str__() # sys.exc_info()[:1]
                c = exc_info.find("DETAIL:")
                if c < 0:
                    l = l + ["Error Fatal."]
                else:
                    c = exc_info[c + 7:]
                    l=l+[c]
                uri="/comerciax/admincom/moneda/view/" + idmoneda 
                edituri = "/comerciax/admincom/moneda/edit/" + idmoneda + "/"
                return render_to_response("form/form_edit.html",{'tipocliente':'2','form':form,'title':'Monedas', 'form_name':'Editar Moneda','form_description':'Editar la moneda seleccionada','controlador':'Monedas','accion':edituri
                                                         , 'cancelbtn':uri,'error2':l},context_instance = RequestContext(request))
    else:
        monedaobj = Monedas.objects.get(pk=idmoneda)
        form = FMoneda(initial={"moneda":monedaobj.descripcion})
        uri="/comerciax/admincom/moneda/view/" + idmoneda 
        edituri = "/comerciax/admincom/moneda/edit/" + idmoneda + "/"
        return render_to_response("form/form_edit.html",{'tipocliente':'2','form':form,'title':'Monedas', 'form_name':'Editar Moneda','form_description':'Editar la moneda seleccionada','controlador':'Monedas','accion':edituri
                                                         , 'cancelbtn':uri,'error2':l},context_instance = RequestContext(request))

@login_required
def delmoneda(request,idmoneda):
    if not request.user.has_perm('admincomerciax.monedas'):
        return render_to_response("denegado.html",locals(),context_instance = RequestContext(request))
    monedaobj = Monedas.objects.get(pk=idmoneda)
    try:
        monedaobj.delete()
        return HttpResponseRedirect('/comerciax/admincom/moneda/index')
    except Exception, e:
        c = "No se puede eliminar la moneda, posibles causas este siendo utilizada por algún otro registro de la BD"
        desc = monedaobj.descripcion
        return render_to_response("admincomerciax/viewmoneda.html",{'causa_name':desc, 'causa_id':idmoneda, 'error2':c},context_instance = RequestContext(request))
    
#############################################################
#        PRODUCTO
#############################################################
@login_required
def producto(request):
    if not request.user.has_perm('admincomerciax.producto'):
        return render_to_response("denegado.html",locals(),context_instance = RequestContext(request))
    return render_to_response("admincomerciax/indexproducto.html",locals(),context_instance = RequestContext(request))

def get_producto_list(request):
    #initial querySet
    querySet = Producto.objects.all().select_related()
    #columnIndexNameMap is required for correct sorting behavior
    columnIndexNameMap = { 0:'id', 1:'descripcion', 2:'codigo',3:'admincomerciax_umedida.descripcion', 4:'precio_mn', 5:'precio_cuc', 6:'precio_costo_mn', 
                          7:'precio_costo_cuc',9:'precio_externo_cup',10:'precio_particular',11:'precio_casco', 12:'otro_precio_casco',13:'precio_vulca'}
    #model fields listed in searchableColumns will be used for filtering (Search)
    searchableColumns = ['descripcion','codigo','precio_externo_cup']
    #path to template used to generate json
    jsonTemplatePath = 'admincomerciax/json/json_producto.txt'
    #call to generic function from utils
    return get_datatables_records(request, querySet, columnIndexNameMap, searchableColumns, jsonTemplatePath)

@login_required    
def addproducto(request):
    if not request.user.has_perm('admincomerciax.producto'):
        return render_to_response("denegado.html",locals(),context_instance = RequestContext(request))
    c = None
    l = []
    if request.method == 'POST':
        form = FProducto(request.POST)
        if form.is_valid():
            myproducto = Producto()
            myproducto.id = uuid4()
            myproducto.descripcion = form.cleaned_data['producto']
            myproducto.codigo = form.cleaned_data['codigo']
            myproducto.precio_mn = form.cleaned_data['precio_mn']
            myproducto.precio_cuc = form.cleaned_data['precio_cuc']
            myproducto.precio_costo_cuc = form.cleaned_data['precio_costo_cuc']
            myproducto.precio_costo_mn = form.cleaned_data['precio_costo_mn']
            myproducto.um = Umedida.objects.get(pk = form.data['unidad_medida'])
            myproducto.precio_particular = form.cleaned_data['precio_particular']
            myproducto.precio_casco = form.cleaned_data['precio_casco']
            myproducto.otro_precio_casco = form.cleaned_data['otro_precio_casco']
            myproducto.precio_externo_cup = form.cleaned_data['precio_externo']
            myproducto.precio_vulca = form.cleaned_data['precio_vulca']
            
            try:
                myproducto.save()
                if request.POST.__contains__('submit1'):
                    return HttpResponseRedirect('/comerciax/admincom/producto/view/' + myproducto.id.__str__())
                else:
                    form = FProducto()
            
            except Exception, e:
                exc_info = e.__str__() # sys.exc_info()[:1]
                c = exc_info.find("DETAIL:")
                if c < 0:
                    l = l + ["Error Fatal."]
                else:
                    c = exc_info[c + 7:]
                    l=l+[c]
                    
                transaction.rollback()
                
                form = FProducto(request.POST)
                uri="/comerciax/admincom/producto/index" 
                return render_to_response("form/form_add.html",{'form':form,'title':'Productos', 'form_name':'Insertar Producto','form_description':'Introducir un nuevo producto a la base de datos','controlador':'Productos','accion':'addproducto',
                                                    'cancelbtn':uri, 'error2':l},context_instance = RequestContext(request))
            #else:
                #transaction.commit()
    else:
        form = FProducto()
    uri="/comerciax/admincom/producto/index" 
    return render_to_response("form/form_add.html",{'form':form,'title':'Productos', 'form_name':'Insertar Producto','form_description':'Introducir un nuevo producto a la base de datos','controlador':'Productos','accion':'addproducto',
                                                'cancelbtn':uri, 'error2':l},context_instance = RequestContext(request))

@login_required    
def viewproducto(request,idproducto):
    if not request.user.has_perm('admincomerciax.producto'):
        return render_to_response("denegado.html",locals(),context_instance = RequestContext(request))
    productoobj = Producto.objects.get(pk=idproducto)
    desc = productoobj.descripcion
    return render_to_response("admincomerciax/viewproducto.html",{'producto_name':desc, 'producto_id':idproducto,"preciomn":productoobj.precio_mn,
                                  "preciocuc":productoobj.precio_cuc,
                                  "codigo":productoobj.codigo,
                                  "preciocostocuc":productoobj.precio_costo_cuc,
                                  "preciocostomn":productoobj.precio_costo_mn,
                                  "precioparticular":productoobj.precio_particular,
                                  "preciocasco":productoobj.precio_casco,
                                  "otro_preciocasco":productoobj.otro_precio_casco,
                                  "precioexternocup":productoobj.precio_externo_cup,
                                  "preciovulca":productoobj.precio_vulca,
                                  "um":productoobj.um.descripcion,},context_instance = RequestContext(request))

@login_required
def editproducto(request,idproducto):
    if not request.user.has_perm('admincomerciax.producto'):
        return render_to_response("denegado.html",locals(),context_instance = RequestContext(request))
    c = None
    l = []
    if request.method == 'POST':
        form = FProducto(request.POST)
        if form.is_valid():
            producto = Producto.objects.get(pk=idproducto)
            producto.descripcion = form.cleaned_data['producto']
            producto.codigo = form.cleaned_data['codigo']
            producto.precio_mn = form.cleaned_data['precio_mn']
            producto.precio_cuc = form.cleaned_data['precio_cuc']
            producto.precio_costo_mn = form.cleaned_data['precio_costo_mn']
            producto.precio_costo_cuc = form.cleaned_data['precio_costo_cuc']
            producto.precio_particular = form.cleaned_data['precio_particular']
            producto.precio_casco = form.cleaned_data['precio_casco']
            producto.otro_precio_casco = form.cleaned_data['otro_precio_casco']
            producto.precio_externo_cup = form.cleaned_data['precio_externo']
            producto.um = Umedida.objects.get(pk = form.data['unidad_medida'])
            producto.precio_vulca = form.cleaned_data['precio_vulca']
            try:
                producto.save()
                return viewproducto(request, idproducto)
            except Exception, e:
                exc_info = e.__str__() # sys.exc_info()[:1]
                c = exc_info.find("DETAIL:")
                if c < 0:
                    l = l + ["Error Fatal."]
                else:
                    c = exc_info[c + 7:]
                    l=l+[c]
                transaction.rollback()
                    
                form = FProducto(request.POST)
                uri="/comerciax/admincom/producto/view/" + idproducto 
                edituri = "/comerciax/admincom/producto/edit/" + idproducto + "/"
                return render_to_response("form/form_edit.html",{'tipocliente':'2','form':form,'title':'Productos', 
                                                                 'form_name':'Editar producto','form_description':'Editar el producto seleccionado',
                                                                 'controlador':'Productos','accion':edituri,
                                                                 'cancelbtn':uri,'error2':l},context_instance = RequestContext(request))
            else:
                transaction.commit()
    else:
        productoobj = Producto.objects.get(pk=idproducto)
        form = FProducto(initial={"producto":productoobj.descripcion,
                                  "codigo":productoobj.codigo,
                                  "precio_mn":productoobj.precio_mn,
                                  "precio_cuc":productoobj.precio_cuc,
                                  "precio_costo_mn":productoobj.precio_costo_mn,
                                  "precio_costo_cuc":productoobj.precio_costo_cuc,
                                  "precio_particular":productoobj.precio_particular,
                                  "precio_externo":productoobj.precio_externo_cup,
                                  "otro_precio_casco":productoobj.otro_precio_casco, 
                                  "precio_casco":productoobj.precio_casco, 
                                  "precio_vulca":productoobj.precio_vulca,                                 
                                  "unidad_medida":productoobj.um.id,})
        uri="/comerciax/admincom/producto/view/" + idproducto 
        edituri = "/comerciax/admincom/producto/edit/" + idproducto + "/"
        return render_to_response("form/form_edit.html",{'tipocliente':'2','form':form,'title':'Productos', 'form_name':'Editar producto','form_description':'Editar el producto seleccionado','controlador':'Productos','accion':edituri
                                                         , 'cancelbtn':uri,'error2':l},context_instance = RequestContext(request))

@login_required
def delproducto(request,idproducto):
    if not request.user.has_perm('admincomerciax.producto'):
        return render_to_response("denegado.html",locals(),context_instance = RequestContext(request))
    productoobj = Producto.objects.get(pk=idproducto)
    try:
        productoobj.delete()
        return HttpResponseRedirect('/comerciax/admincom/producto/index')
    except Exception, e:
        c = "No se puede eliminar la producto, posibles causas este siendo utilizada por algún otro registro de la BD"
        desc = productoobj.descripcion
        return render_to_response("admincomerciax/viewproducto.html",{'producto_name':desc, 'producto_id':idproducto, 'error2':c},context_instance = RequestContext(request))
    
#############################################################
#        EMPRESA
#############################################################
@login_required
def empresa(request):
    if not request.user.has_perm('admincomerciax.empresa'):
        return render_to_response("denegado.html",locals(),context_instance = RequestContext(request))
    return render_to_response("admincomerciax/indexempresa.html",locals(),context_instance = RequestContext(request))

def get_empresa_list(request):
    #initial querySet
    querySet = Empresa.objects.all().select_related()
    #columnIndexNameMap is required for correct sorting behavior
    columnIndexNameMap = { 0:'codigo', 1:'codigo', 2:'nombre', 3:'direccion', 4:'telefono', 5:'fax'}
    #model fields listed in searchableColumns will be used for filtering (Search)
    searchableColumns = ['nombre']
    #path to template used to generate json
    jsonTemplatePath = 'admincomerciax/json/json_empresa.txt'
    #call to generic function from utils
    return get_datatables_records(request, querySet, columnIndexNameMap, searchableColumns, jsonTemplatePath)

@login_required    
def addempresa(request):
    if not request.user.has_perm('admincomerciax.empresa'):
        return render_to_response("denegado.html",locals(),context_instance = RequestContext(request))
    c = None
    l = []
    if request.method == 'POST':
        form = FEmpresa(request.POST)
        if form.is_valid():
            myempresa = Empresa()
            myempresa.id = uuid4()
            myempresa.codigo = form.cleaned_data['codigo']
            myempresa.nombre = form.cleaned_data['nombre']
            myempresa.direccion = form.cleaned_data['direccion']
            myempresa.telefono = form.cleaned_data['telefono']
            myempresa.fax = form.cleaned_data['fax']
            myempresa.email = form.cleaned_data['email']
            myempresa.titular_mn = form.cleaned_data['titular_mn']
            myempresa.titular_usd = form.cleaned_data['titular_usd']
            myempresa.cuenta_mn = form.cleaned_data['cuenta_mn']
            myempresa.cuenta_usd = form.cleaned_data['cuenta_usd']
            
            myempresa.provincia = Provincias.objects.get(pk = form.data['provincia'])
            myempresa.sucursal_mn = Sucursales.objects.get(pk = form.data['sucursal_mn'])
            myempresa.sucursal_usd = Sucursales.objects.get(pk = form.data['sucursal_usd'])
            
            try:
                myempresa.save()
                if request.POST.__contains__('submit1'):
                    return HttpResponseRedirect('/comerciax/admincom/empresa/view/' + myempresa.id.__str__())
                else:
                    form = FEmpresa()
            
            except Exception, e:
                exc_info = e.__str__() # sys.exc_info()[:1]
                c = exc_info.find("DETAIL:")
                if c < 0:
                    l = l + ["Error Fatal."]
                else:
                    c = exc_info[c + 7:]
                    l=l+[c]
                    
                transaction.rollback()
                
                form = FEmpresa(request.POST)
                uri="/comerciax/admincom/empresa/index" 
                return render_to_response("admincomerciax/form_empresaadd.html",{'form':form,'title':'Empresa', 'form_name':'Insertar Empresa','form_description':'Introducir una nueva empresa a la base de datos','controlador':'Empresas','accion':'addempresa',
                                                    'cancelbtn':uri, 'error2':l},context_instance = RequestContext(request))
            else:
                transaction.commit()
    else:
        form = FEmpresa()
    uri="/comerciax/admincom/empresa/index" 
    return render_to_response("admincomerciax/form_empresaadd.html",{'form':form,'title':'Empresa', 'form_name':'Insertar Empresa','form_description':'Introducir una nueva empresa a la base de datos','controlador':'Empresas','accion':'addempresa',
                                                'cancelbtn':uri, 'error2':l},context_instance = RequestContext(request))

@login_required    
def viewempresa(request,idempresa):
    if not request.user.has_perm('admincomerciax.empresa'):
        return render_to_response("denegado.html",locals(),context_instance = RequestContext(request))
    empresaobj = Empresa.objects.select_related().get(pk=idempresa)
    empresa_id = empresaobj.id
    empresa_nombre = empresaobj.nombre
    direccion = empresaobj.direccion
    codigo = empresaobj.codigo
    email = empresaobj.email
    telefono = empresaobj.telefono
    fax = empresaobj.fax
    cuenta_mn = empresaobj.cuenta_mn
    cuenta_usd = empresaobj.cuenta_usd
    titular_mn = empresaobj.titular_mn
    titular_usd = empresaobj.titular_usd
    sucursal_mn = empresaobj.sucursal_mn
    sucursal_usd = empresaobj.sucursal_usd
    provincia = empresaobj.provincia    
    return render_to_response("admincomerciax/viewempresa.html",locals(),context_instance = RequestContext(request))

@login_required
def editempresa(request,idempresa):
    if not request.user.has_perm('admincomerciax.empresa'):
        return render_to_response("denegado.html",locals(),context_instance = RequestContext(request))
    c = None
    l = []
    if request.method == 'POST':
        form = FEmpresa(request.POST)
        if form.is_valid():
            empresa = Empresa.objects.get(pk=idempresa)
            empresa.nombre = form.cleaned_data['nombre']
            empresa.direccion = form.cleaned_data['direccion']
            empresa.codigo = form.cleaned_data['codigo']
            empresa.email = form.cleaned_data['email']
            empresa.telefono = form.cleaned_data['telefono']
            empresa.fax = form.cleaned_data['fax']
            empresa.cuenta_mn = form.cleaned_data['cuenta_mn']
            empresa.cuenta_usd = form.cleaned_data['cuenta_usd']
            empresa.titular_mn = form.cleaned_data['titular_mn']
            empresa.titular_usd = form.cleaned_data['titular_usd']
            empresa.sucursal_mn = Sucursales.objects.get(pk = form.data['sucursal_mn'])
            empresa.sucursal_usd = Sucursales.objects.get(pk = form.data['sucursal_usd'])
            empresa.provincia = Provincias.objects.get(pk = form.data['provincia'])
            try:
                empresa.save()
                return viewempresa(request, idempresa)
            except Exception, e:
                exc_info = e.__str__() # sys.exc_info()[:1]
                c = exc_info.find("DETAIL:")
                if c < 0:
                    l = l + ["Error Fatal."]
                else:
                    c = exc_info[c + 7:]
                    l=l+[c]
                    
                transaction.rollback()
                    
                form = FEmpresa(request.POST)
                uri="/comerciax/admincom/empresa/view/" + idempresa 
                edituri = "/comerciax/admincom/empresa/edit/" + idempresa + "/"
                return render_to_response("admincomerciax/form_empresaadd.html",{'form':form,'title':'Empresa', 'form_name':'Editar empresa','form_description':'Editar la empresa seleccionada','controlador':'Empresas','accion':edituri
                                                         , 'cancelbtn':uri,'error2':l},context_instance = RequestContext(request))
            else:
                transaction.commit()
    else:
        empresaobj = Empresa.objects.select_related().get(pk=idempresa)
        form = FEmpresa(initial={"nombre" : empresaobj.nombre,
        "direccion" : empresaobj.direccion,
        "codigo" : empresaobj.codigo,
        "email" : empresaobj.email,
        "telefono" : empresaobj.telefono,
        "fax" : empresaobj.fax,
        "cuenta_mn" : empresaobj.cuenta_mn,
        "cuenta_usd" : empresaobj.cuenta_usd,
        "titular_mn" : empresaobj.titular_mn,
        "titular_usd" : empresaobj.titular_usd,
        "sucursal_mn" : empresaobj.sucursal_mn,
        "sucursal_usd" : empresaobj.sucursal_usd,
        "provincia" : empresaobj.provincia})
            
        uri="/comerciax/admincom/empresa/view/" + idempresa 
        edituri = "/comerciax/admincom/empresa/edit/" + idempresa + "/"
        return render_to_response("admincomerciax/form_empresaadd.html",{'form':form,'title':'empresas', 'form_name':'Editar empresa','form_description':'Editar el empresa seleccionado','controlador':'empresas','accion':edituri
                                                         , 'cancelbtn':uri,'error2':l},context_instance = RequestContext(request))

@login_required
def delempresa(request,idempresa):
    if not request.user.has_perm('admincomerciax.empresa'):
        return render_to_response("denegado.html",locals(),context_instance = RequestContext(request))
    empresaobj = Empresa.objects.get(pk=idempresa)
    try:
        empresaobj.delete()
        return HttpResponseRedirect('/comerciax/admincom/empresa/index')
    except Exception, e:
        c = "No se puede eliminar la empresa, posibles causas este siendo utilizada por algún otro registro de la BD"
        desc = empresaobj.descripcion
        return render_to_response("admincomerciax/viewempresa.html",{'causa_name':desc, 'causa_id':idempresa, 'error2':c},context_instance = RequestContext(request))
    
#############################################################
#        CLIENTE
#############################################################
@login_required
def cliente(request):
    if not request.user.has_perm('admincomerciax.cliente'):
        return render_to_response("denegado.html",locals(),context_instance = RequestContext(request))
    return render_to_response("admincomerciax/indexcliente.html",locals(),context_instance = RequestContext(request))

def get_cliente_list(request):
#    #initial querySet
#    querySet = ClienteContrato.objects.select_related().filter(cerrado=False).order_by('nombre')
#    columnIndexNameMap = { 0:'cliente__codigo', 1:'cliente__codigo', 2:'cliente__nombre', 3:'cliente__organismo__siglas_organismo',4:'cliente__provincia__descripcion_provincia',5:'contrato__contrato_nro',6:'cliente__direccion', 7:'cliente__telefono', 8:'fax', 9:'contrato__id_contrato'}
#    #model fields listed in searchableColumns will be used for filtering (Search)
#    searchableColumns = ['cliente__codigo','cliente__nombre','cliente__organismo__siglas_organismo','cliente__provincia__descripcion_provincia','contrato__contrato_nro']
#    #path to template used to generate json
#    jsonTemplatePath = 'admincomerciax/json/json_cliente.txt'
#    #call to generic function from utils
#    return get_datatables_records(request, querySet , columnIndexNameMap, searchableColumns, jsonTemplatePath)
    #initial querySet
    
    querySet = Cliente.objects.filter(eliminado=False).distinct().order_by('nombre')
    columnIndexNameMap = { 0:'codigo', 1:'codigo', 2:'nombre', 3:'organismo__siglas_organismo',4:'provincia__descripcion_provincia',5:'clientcontrato__contrato__contrato_nro',6:'direccion', 7:'telefono', 8:'fax', 9:'clientecontrato__contrato__id_contrato'}
    #model fields listed in searchableColumns will be used for filtering (Search)
    searchableColumns = ['codigo','nombre','organismo__siglas_organismo','provincia__descripcion_provincia','clientecontrato__contrato__contrato_nro']
    #path to template used to generate json
    jsonTemplatePath = 'admincomerciax/json/json_cliente.txt'
    #call to generic function from utils
    return get_datatables_records(request, querySet , columnIndexNameMap, searchableColumns, jsonTemplatePath)

@login_required    
def addcliente(request):
    if not request.user.has_perm('admincomerciax.add_cliente'):
        return render_to_response("denegado.html",locals(),context_instance = RequestContext(request))
    c = None
    l = []
    if request.method == 'POST':
        form = FCliente(request.POST)
        if form.is_valid():
            mycliente = Cliente()
            mycliente.id = uuid4()
            codigo = form.cleaned_data['codigo']
            mycliente.codigo = codigo
            mycliente.nombre = form.cleaned_data['nombre']
            mycliente.direccion = form.cleaned_data['direccion']
            mycliente.telefono = form.cleaned_data['telefono']
            mycliente.fax = form.cleaned_data['fax']
            mycliente.email = form.cleaned_data['email']
            mycliente.eliminado = False
            mycliente.externo = form.cleaned_data['externo']
            mycliente.comercializadora = form.cleaned_data['comercializadora']
            mycliente.provincia = Provincias.objects.get(pk = form.data['provincia'])
            organismo = Organismo.objects.get(pk = form.data['organismo'])
            mycliente.organismo = organismo
            
            if form.data.has_key('union'):
                union = Union.objects.get(pk = form.data['union'])
                mycliente.union = union
            else:
                mycliente.union = None 
            
            codorg = organismo.codigo_organismo
            '''
            existe =  codigo.find(codorg)
            try:
                if existe == 0:
                    mycliente.save()
                    if request.POST.__contains__('submit1'):
                        return HttpResponseRedirect('/comerciax/admincom/cliente/view/' + mycliente.id.__str__())
                    else:
                        form = FCliente()
                else:
                    raise Exception("Error, no coinciden el organismo con el que introdujo en el codigo del cliente")
            '''
            try:
                mycliente.save()
                return HttpResponseRedirect('/comerciax/admincom/cliente/view/' + mycliente.id.__str__())
            except Exception, e:
                exc_info = e.__str__() # sys.exc_info()[:1]
                c = exc_info.find("DETAIL:")
                if c < 0:
                    #l = l + ["Error Fatal."]
                    l = l + [exc_info]
                else:
                    c = exc_info[c + 7:]
                    l=l+[c]
                #transaction.rollback()
                form = FCliente(request.POST)
                uri="/comerciax/admincom/cliente/index" 
                return render_to_response("admincomerciax/form_clienteadd.html",{'form':form,'title':'Cliente', 'form_name':'Insertar cliente','form_description':'Introducir una nueva cliente a la base de datos','controlador':'Clientes','accion':'addcliente',
                                                    'cancelbtn':uri, 'error2':l},context_instance = RequestContext(request))
            #else:
                #transaction.commit()
    else:
        form = FCliente()
    uri="/comerciax/admincom/cliente/index" 
    return render_to_response("admincomerciax/form_clienteadd.html",{'form':form,'title':'Cliente', 'form_name':'Insertar cliente','form_description':'Introducir una nueva cliente a la base de datos','controlador':'Clientes','accion':'addcliente',
                                                'cancelbtn':uri, 'error2':l},context_instance = RequestContext(request))

@login_required 
@transaction.commit_on_success()
def viewcliente(request,idcliente):
    if not request.user.has_perm('admincomerciax.cliente'):
        return render_to_response("denegado.html",locals(),context_instance = RequestContext(request))

        
    clienteobj = Cliente.objects.select_related().get(pk=idcliente)
    cliente_id = clienteobj.id
    cliente_nombre = clienteobj.nombre
    direccion = clienteobj.direccion
    codigo = clienteobj.codigo
    email = clienteobj.email
    telefono = clienteobj.telefono
    fax = clienteobj.fax
    provincia = clienteobj.provincia
    organismo = clienteobj.organismo
    a = 0
    if clienteobj.union:
        union = clienteobj.union
    else:
        union = "--------"
    
    if clienteobj.externo:
        externo = 'Sí'
    else:
        externo = 'No'
        
    #obtener todos los contratos del cliente
#    contratos = Contrato.objects.select_related().filter(cliente=idcliente)
    contratos = ClienteContrato.objects.select_related().filter(cliente=idcliente)
        
    return render_to_response("admincomerciax/viewcliente.html",locals(),context_instance = RequestContext(request))

@login_required
def editcliente(request,idcliente):
    if not request.user.has_perm('admincomerciax.cliente'):
        return render_to_response("denegado.html",locals(),context_instance = RequestContext(request))
    c = None
    l = []
    if request.method == 'POST':
        form = FCliente(request.POST)
        if form.is_valid():
            cliente = Cliente.objects.get(pk=idcliente)
            cliente.nombre = form.cleaned_data['nombre']
            cliente.direccion = form.cleaned_data['direccion']
            cliente.codigo = form.cleaned_data['codigo']
            cliente.email = form.cleaned_data['email']
            cliente.telefono = form.cleaned_data['telefono']
            cliente.fax = form.cleaned_data['fax']
            cliente.externo = form.cleaned_data['externo']
            cliente.comercializadora = form.cleaned_data['comercializadora']
            cliente.organismo = Organismo.objects.get(pk = form.data['organismo'])
            cliente.provincia = Provincias.objects.get(pk = form.data['provincia'])
            
            if form.data.has_key('union'):
                union = Union.objects.get(pk = form.data['union'])
                cliente.union = union
            else:
                cliente.union = None
            
            try:
                cliente.save()
                return viewcliente(request, idcliente)
            except Exception, e:
                exc_info = e.__str__() # sys.exc_info()[:1]
                c = exc_info.find("DETAIL:")
                if c < 0:
                    l = l + ["Error Fatal."]
                else:
                    c = exc_info[c + 7:]
                    l=l+[c]
                    
                transaction.rollback()
                    
                form = FCliente(request.POST)
                uri="/comerciax/admincom/cliente/view/" + idcliente 
                edituri = "/comerciax/admincom/cliente/edit/" + idcliente + "/"
                return render_to_response("admincomerciax/form_clienteedit.html",{'form':form,'title':'Cliente', 'form_name':'Editar cliente','form_description':'Editar la cliente seleccionada','controlador':'Clientes','accion':edituri
                                                         , 'cancelbtn':uri,'error2':l},context_instance = RequestContext(request))
            else:
                transaction.commit()
    else:

        clienteobj = Cliente.objects.select_related().get(pk=idcliente)
        form = FCliente(initial={"nombre" : clienteobj.nombre,
        "direccion" : clienteobj.direccion,
        "codigo" : clienteobj.codigo,
        "email" : clienteobj.email,
        "telefono" : clienteobj.telefono,
        "fax" : clienteobj.fax,
        "externo" : clienteobj.externo,
        "comercializadora" : clienteobj.comercializadora,
        "organismo" : clienteobj.organismo,
        "provincia" : clienteobj.provincia,
        "union":clienteobj.union})
            
        uri="/comerciax/admincom/cliente/view/" + idcliente 
        edituri = "/comerciax/admincom/cliente/edit/" + idcliente + "/"
        return render_to_response("admincomerciax/form_clienteedit.html",{'form':form,'title':'Clientes', 'form_name':'Editar cliente','form_description':'Editar el cliente seleccionado','controlador':'Clientes','accion':edituri
                                                         , 'cancelbtn':uri,'error2':l},context_instance = RequestContext(request))

@login_required    
@transaction.commit_on_success()    
def contratoexiste(request,idcliente):
    if not request.user.has_perm('admincomerciax.change_contrato'):
        return render_to_response("denegado.html",locals(),context_instance = RequestContext(request))
    l=[]
    titulo_form='Seleccionar Contrato' 
    controlador_form='Seleccionar Contrato'
    descripcion_form='Seleccionar Contrato'
    
    accion_form='contratoadd'
    cancelbtn_form='/comerciax/admincom/cliente/view/'+idcliente
    estado="Casco" 
    if request.method == 'POST':
        seleccion=request.POST.keys()
        
        k=0
            
        while True:
            if seleccion.__len__()==1:
                break
            contrato=Contrato.objects.filter(pk=request.POST['radiosel'])

            if contrato.count()!=0:
                '''
                Los selecionados los cambio de estado, agregar a detalle del documento y actualizar trazabilidad
                '''
                objcc=ClienteContrato.objects.filter(contrato=request.POST['radiosel'],cliente=idcliente)
                if objcc.count()!=0:
                    objcc.update(cerrado=False)
                else:
                    contratocliente=ClienteContrato()
                    contratocliente.id_contratocliente=uuid4()
                    contratocliente.cliente=Cliente.objects.get(pk=idcliente)
                    contratocliente.contrato=Contrato.objects.get(pk=request.POST['radiosel'])
                    nro=contratocliente.contrato.contrato_nro
                    try:
                        contratocliente.save()
                        
                    except Exception, e:
                        exc_info = e.__str__() # sys.exc_info()[:1]
                        c = exc_info.find("DETAIL:")
                        
                        if c < 0:
                            l=l+["Error Fatal."]
                        else:
                            l=['El contrato ' + str(nro) +' ya existe para este cliente']
                            c = exc_info[c + 7:]
                            transaction.rollback()
        
            return HttpResponseRedirect('/comerciax/admincom/cliente/view/' + idcliente)
    contratos=ClienteContrato.objects.select_related().filter(cerrado=False,cliente__organismo=Organismo.objects.get(pk=Cliente.objects.get(pk=idcliente).organismo.id)).order_by('contrato__contrato_nro')
#    contratos=Contrato.objects.select_related().filter(cerrado=False,clientecontrato__clienteorganismo=Organismo.objects.get(pk=Cliente.objects.get(pk=idcliente).organismo.id)).order_by('contrato_nro')
    l=l+["No Existen Contratos para Seleccionar"]
    for a1 in contratos:
        l=[]
        break
    return render_to_response('admincomerciax/form_seleccontrato.html', {'error2':l,'title':titulo_form,'controlador':controlador_form,'accion':accion_form,
                                                      'cancelbtn':cancelbtn_form,'form_description':descripcion_form,
                                                      'cliente_id':idcliente,'contratos':contratos},context_instance = RequestContext(request))    

@login_required    
@transaction.commit_on_success()    
def contratoadd(request,idcliente):
    if not request.user.has_perm('admincomerciax.change_contrato'):
        return render_to_response("denegado.html",locals(),context_instance = RequestContext(request))
    c = None
    l = []
    if request.method == 'POST':
        form = FContrato(request.POST)
        if form.is_valid():
            mycontrato = Contrato()
            myclientecontrato=ClienteContrato()
            mycontrato.id_contrato = uuid4()
            mycontrato.contrato_nro = form.cleaned_data['contrato_nro']
#            mycontrato.cliente = Cliente.objects.get(pk = idcliente)
            mycontrato.fecha_vigencia = form.cleaned_data['fecha_vigencia']
            mycontrato.tiempo_vigencia = form.cleaned_data['tiempo_vigencia']
            mycontrato.fecha_vencimiento = form.cleaned_data['fecha_vencimiento']
#            mycontrato.plan_contratado = form.cleaned_data['plan_contratado']
            mycontrato.sucursal_mn = Sucursales.objects.get(pk = form.data['sucursal_mn'])            
            susc_usd = form.data['sucursal_usd'] 
            if (susc_usd.__len__() > 0):
                mycontrato.sucursal_usd = Sucursales.objects.get(pk = form.data['sucursal_usd'])
            mycontrato.titular_mn = form.data['titular_mn']
            mycontrato.titular_usd = form.data['titular_usd'] 
            mycontrato.cuenta_mn = form.data['cuenta_mn']
            mycontrato.cuenta_usd = form.data['cuenta_usd']
            mycontrato.cerrado = False
            
            para_la_venta = form.cleaned_data['para_la_venta']
            if para_la_venta == 'N':
                mycontrato.para_la_venta = False
            else:
                mycontrato.para_la_venta = True
            
            seleccionado = 0
            
            if form.data.has_key('venta_costo_mn'):
                ventacostomn = form.data['venta_costo_mn']
                if ventacostomn == 'costomn':
                    mycontrato.preciocostomn = True 
                    mycontrato.preciomn = False
                    mycontrato.precioextcup = False
                if ventacostomn == 'ventamn':
                    mycontrato.preciocostomn = False 
                    mycontrato.preciomn = True
                    mycontrato.precioextcup = False
                if ventacostomn == 'ventaext':
                    mycontrato.preciocostomn = False 
                    mycontrato.preciomn = False
                    mycontrato.precioextcup = True
                if ventacostomn == 'noexistmn':
                    mycontrato.preciocostomn = False 
                    mycontrato.preciomn = False
                    mycontrato.precioextcup = False
                    seleccionado += 1
            else:
                mycontrato.preciocostomn = False 
                mycontrato.preciomn = False
                    
            if form.data.has_key('venta_costo_cuc'):
                ventacostocuc = form.data['venta_costo_cuc']
                if ventacostocuc == 'costocuc':
                    mycontrato.preciocostocuc = True 
                    mycontrato.preciocuc = False
                if ventacostocuc == 'ventacuc':
                    mycontrato.preciocostocuc = False 
                    mycontrato.preciocuc = True
                if ventacostocuc == 'noexistcuc':
                    mycontrato.preciocostocuc = False 
                    mycontrato.preciocuc = False
                    seleccionado += 1
            else:
                mycontrato.preciocostocuc = False 
                mycontrato.preciocuc = False
                
            otropreciocasco = False   
            if form.data.has_key('otro_precio_casco'):
                otropreciocasco = True
            
            mycontrato.otro_precio_casco = otropreciocasco 
                    
            try:
                if seleccionado == 2:
                    raise Exception('DETAIL:Debe seleccionar al menos un precio') 
 
                mycontrato.save()
                myclientecontrato.id_contratocliente=uuid4()
                myclientecontrato.contrato=Contrato.objects.get(pk = mycontrato.id_contrato)
                myclientecontrato.cliente=Cliente.objects.get(pk = idcliente)
                myclientecontrato.save()
                
                
                if request.POST.__contains__('submit1'):
                    return HttpResponseRedirect('/comerciax/admincom/cliente/view/' + idcliente)
                else:
                    form = FContrato()
            
            except Exception, e:
                exc_info = e.__str__() # sys.exc_info()[:1]
                c = exc_info.find("DETAIL:")
                if c < 0:
                    l = l + ["Error Fatal."]
                else:
                    c = exc_info[c + 7:]
                    l=l+[c]
                    
                transaction.rollback()
                
                form = FContrato(request.POST)
                uri='/comerciax/admincom/cliente/view/' + idcliente
                return render_to_response("admincomerciax/form_contratoadd.html",{'form':form,'title':'Cliente', 'form_name':'Insertar cliente','form_description':'Introducir una nueva cliente a la base de datos','controlador':'Clientes','accion':'addcliente',
                                                    'cancelbtn':uri, 'error2':l},context_instance = RequestContext(request))
            else:
                transaction.commit()
    else:
        form = FContrato()
    uri='/comerciax/admincom/cliente/view/' + idcliente        
    return render_to_response("admincomerciax/form_contratoadd.html",{'form':form,'title':'Contrato', 'form_name':'Insertar contrato','form_description':'Introducir un nuevo contrato a la base de datos','controlador':'Contrato','accion':'addcontrato',
                                                'cancelbtn':uri, 'error2':l},context_instance = RequestContext(request))

@login_required
def delcliente(request,idcliente):
    if not request.user.has_perm('admincomerciax.cliente'):
        return render_to_response("denegado.html",locals(),context_instance = RequestContext(request))
    clienteobj = Cliente.objects.get(pk=idcliente)
    cliente_id = clienteobj.id
    cliente_nombre = clienteobj.nombre
    direccion = clienteobj.direccion
    codigo = clienteobj.codigo
    email = clienteobj.email
    telefono = clienteobj.telefono
    fax = clienteobj.fax
    provincia = clienteobj.provincia
    organismo = clienteobj.organismo
    try:
        cantidad=DetalleRC.objects.select_related().filter(rc__cliente__id=idcliente).exclude(casco__estado_actual="Factura").count()
        if cantidad == 0:
            Cliente.objects.get(id = idcliente).eliminar()
#            idcontrato=ClienteContrato.objects.get(cliente = idcliente,cerrado=False).contrato
#            ClienteContrato.objects.get(cliente = idcliente,cerrado=False).delete()
#            otros = ClienteContrato.objects.filter(contrato=idcontrato).count()
#            if otros==0:
#                contratoobj = Contrato.objects.get(pk=idcontrato)
#                contratoobj.delete()
            return HttpResponseRedirect('/comerciax/admincom/cliente/index')
        else:
            c = "No se puede eliminar el cliente"
            l=[]
            l+=[c]
            error2=l
            cliente_id=idcliente
            contratos = ClienteContrato.objects.select_related().filter(cliente=idcliente)
            return render_to_response("admincomerciax/viewcliente.html",locals(),context_instance = RequestContext(request))
        
    except Exception, e:
        c = "No se puede eliminar el cliente"
        return render_to_response("admincomerciax/viewcliente.html",locals(),context_instance = RequestContext(request))


@login_required    
def viewcontratoselecc(request,idcliente,idcontrato):
    if not request.user.has_perm('admincomerciax.cliente'):
        return render_to_response("denegado.html",locals(),context_instance = RequestContext(request))
    l=[]
    error2 = l
      
    contratoobj = Contrato.objects.select_related().get(pk=idcontrato)
    contrato_id = contratoobj.id_contrato
    cliente_id=idcliente
    contrato_nro = contratoobj.contrato_nro
    fecha_vigencia = contratoobj.fecha_vigencia
    fecha_vencimiento = contratoobj.fecha_vencimiento
    tiempo_vigencia = contratoobj.tiempo_vigencia
    titular_mn = contratoobj.titular_mn
    titular_usd = contratoobj.titular_usd 
    sucursal_mn = contratoobj.sucursal_mn
    sucursal_usd = contratoobj.sucursal_usd 
    cuenta_mn = contratoobj.cuenta_mn
    cuenta_usd = contratoobj.cuenta_usd
    idcontcli=ClienteContrato.objects.get(cliente=idcliente,contrato=idcontrato)
#    cerrado = contratoobj.cerrado
#    plan_contratado = contratoobj.plan_contratado 
    '''
    if contratoobj.cerrado:
        cerrado = 'Sí'
    else:
        cerrado = 'No'
    ''' 
    
    if contratoobj.para_la_venta:
        para_la_venta = 'Normal'
    else:
        para_la_venta = 'Para la venta'
            
    
    if contratoobj.preciocostomn:
        preciocostomn = 'Sí'
    else:
        preciocostomn = 'No'
    if contratoobj.preciomn:
        preciomn = 'Sí'
    else:
        preciomn = 'No'
    if contratoobj.preciocostocuc:
        preciocostocuc = 'Sí'
    else:
        preciocostocuc = 'No'
    if contratoobj.preciocuc:
        preciocuc = 'Sí'
    else:
        preciocuc = 'No'
    if contratoobj.precioextcup:
        precioextcup = 'Sí'
    else:
        precioextcup = 'No'
        
    #obtener todos los representantes del contrato
    representantes = Representante.objects.select_related().filter(contrato=idcontrato)
    
    #obtener todos los transportadores del contrato
#    transportadores = Transpotador.objects.select_related().filter(contrato=idcontrato,activo=True)
    transportadores = Transpotador.objects.select_related().filter(contrato=idcontrato).order_by('-activo','nombre')
    selecc=True
        
    return render_to_response("admincomerciax/viewcontrato.html",locals(),context_instance = RequestContext(request))
@login_required    
def viewcontrato(request,idcliente,idcontrato,*otro):
    if not request.user.has_perm('admincomerciax.cliente'):
        return render_to_response("denegado.html",locals(),context_instance = RequestContext(request))
    l=[]
    if otro.__len__()!=0:
        l=[otro[0]]
    error2 = l
    selecc=False
    contratoobj = Contrato.objects.select_related().get(pk=idcontrato)
    contrato_id = contratoobj.id_contrato
    cliente_id = idcliente
    contrato_nro = contratoobj.contrato_nro
    cliente = Cliente.objects.select_related().get(pk=idcliente)
    fecha_vigencia = contratoobj.fecha_vigencia
    fecha_vencimiento = contratoobj.fecha_vencimiento
    tiempo_vigencia = contratoobj.tiempo_vigencia
    titular_mn = contratoobj.titular_mn
    titular_usd = contratoobj.titular_usd 
    sucursal_mn = contratoobj.sucursal_mn
    sucursal_usd = contratoobj.sucursal_usd 
    cuenta_mn = contratoobj.cuenta_mn
    cuenta_usd = contratoobj.cuenta_usd
#    cerrado = contratoobj.cerrado
#    cerrado=ClienteContrato.objects.select_related().get(contrato=idcontrato,cliente=idcliente).cerrado
    idcontcli_=ClienteContrato.objects.select_related().get(contrato=idcontrato,cliente=idcliente)
    cerrado=idcontcli_.cerrado
    idcontcliente=idcontcli_.id_contratocliente
#    plan_contratado = contratoobj.plan_contratado 
    '''
    if contratoobj.cerrado:
        cerrado = 'Sí'
    else:
        cerrado = 'No'
    ''' 
    
    if contratoobj.para_la_venta==False:
        para_la_venta = 'Normal'
    else:
        para_la_venta = 'Para la venta'
            
    
    if contratoobj.preciocostomn:
        preciocostomn = 'Sí'
    else:
        preciocostomn = 'No'
    if contratoobj.preciomn:
        preciomn = 'Sí'
    else:
        preciomn = 'No'
    if contratoobj.preciocostocuc:
        preciocostocuc = 'Sí'
    else:
        preciocostocuc = 'No'
    if contratoobj.preciocuc:
        preciocuc = 'Sí'
    else:
        preciocuc = 'No'
    
    if contratoobj.precioextcup:
        precioextcup = 'Sí'
    else:
        precioextcup = 'No'
        
    #obtener todos los representantes del contrato
    representantes = Representante.objects.select_related().filter(contrato=idcontrato)
    
    #obtener todos los transportadores del contrato
#    transportadores = Transpotador.objects.select_related().filter(contrato=idcontrato,activo=True)
    transportadores = Transpotador.objects.select_related().filter(contrato=idcontrato).order_by('-activo','nombre')
    
    planescont = Planes.objects.select_related().filter(contrato=idcontrato).order_by('plan_ano')
        
    return render_to_response("admincomerciax/viewcontrato.html",locals(),context_instance = RequestContext(request))

@login_required
def contratodel(request,idcontrato, idcliente):
    if not request.user.has_perm('admincomerciax.cliente'):
        return render_to_response("denegado.html",locals(),context_instance = RequestContext(request))
    try:
        exist=Facturas.objects.select_related().filter(cliente__id=idcliente,transportador__contrato__id_contrato=idcontrato).count()
        if exist!=0:
            error2 = "No se puede eliminar el contrato, existen facturas asociadas al mismo"
            return viewcontrato(request, idcliente, idcontrato, error2) 
        clientecontratoobj = ClienteContrato.objects.get(contrato=idcontrato,cliente=idcliente)
        clientecontratoobj.delete()
        otros = ClienteContrato.objects.filter(contrato=idcontrato).count()
        if otros==0:
            contratoobj = Contrato.objects.get(pk=idcontrato)
            contratoobj.delete()
        return viewcliente(request, idcliente)
    except Exception, e:
        error2 = "No se puede eliminar el contrato, posibles causas este siendo utilizada por algún otro registro de la BD"
        return viewcontrato(request, idcliente, idcontrato, error2)


@login_required
def contratoedit(request,idcon,idcliente):
    if not request.user.has_perm('admincomerciax.cliente'):
        return render_to_response("denegado.html",locals(),context_instance = RequestContext(request))
    c = None
    l = []
    if request.method == 'POST':
        form = FContrato(request.POST)
        if form.is_valid():
            mycontrato = Contrato.objects.get(pk=idcon)
            mycontrato.contrato_nro = form.cleaned_data['contrato_nro']
#            mycontrato.cliente = Cliente.objects.get(pk = idcliente)
            mycontrato.fecha_vigencia = form.cleaned_data['fecha_vigencia']
            mycontrato.tiempo_vigencia = form.cleaned_data['tiempo_vigencia']
            mycontrato.fecha_vencimiento = form.cleaned_data['fecha_vencimiento']
            mycontrato.sucursal_mn = Sucursales.objects.get(pk = form.data['sucursal_mn'])            
            susc_usd = form.data['sucursal_usd'] 
            if (susc_usd.__len__() > 0):
                mycontrato.sucursal_usd = Sucursales.objects.get(pk = form.data['sucursal_usd'])
            mycontrato.titular_mn = form.data['titular_mn']
            mycontrato.titular_usd = form.data['titular_usd']            
            #mycontrato.sucursal_mn = Sucursales.objects.get(pk = form.data['sucursal_mn'])
            #mycontrato.sucursal_usd = Sucursales.objects.get(pk = form.data['sucursal_usd'])
            mycontrato.cuenta_mn = form.data['cuenta_mn']
            mycontrato.cuenta_usd = form.data['cuenta_usd']
            mycontrato.cerrado = False
#            mycontrato.plan_contratado = form.cleaned_data['plan_contratado']
            
            para_la_venta = form.cleaned_data['para_la_venta']
            if para_la_venta == 'N':
                mycontrato.para_la_venta = False
            else:
                mycontrato.para_la_venta = True
                
            seleccionado = 0
            
            if form.data.has_key('venta_costo_mn'):
                ventacostomn = form.data['venta_costo_mn']
                if ventacostomn == 'costomn':
                    mycontrato.preciocostomn = True 
                    mycontrato.preciomn = False
                    mycontrato.precioextcup = False
                if ventacostomn == 'ventamn':
                    mycontrato.preciocostomn = False 
                    mycontrato.preciomn = True
                    mycontrato.precioextcup = False
                if ventacostomn == 'ventaext':
                    mycontrato.preciocostomn = False 
                    mycontrato.preciomn = False
                    mycontrato.precioextcup = True
                if ventacostomn == 'noexistmn':
                    mycontrato.preciocostomn = False 
                    mycontrato.preciomn = False
                    mycontrato.precioextcup = False
                    seleccionado += 1
            else:
                mycontrato.preciocostomn = False 
                mycontrato.preciomn = False
                
            if form.data.has_key('venta_costo_cuc'):
                ventacostocuc = form.data['venta_costo_cuc']
                if ventacostocuc == 'costocuc':
                    mycontrato.preciocostocuc = True 
                    mycontrato.preciocuc = False
                if ventacostocuc == 'ventacuc':
                    mycontrato.preciocostocuc = False 
                    mycontrato.preciocuc = True
                if ventacostocuc == 'noexistcuc':
                    mycontrato.preciocostocuc = False 
                    mycontrato.preciocuc = False
                    seleccionado += 1
            else:
                mycontrato.preciocostocuc = False 
                mycontrato.preciocuc = False
                
            otropreciocasco = False   
            if form.data.has_key('otro_precio_casco'):
                otropreciocasco = True
            
            mycontrato.otro_precio_casco = otropreciocasco 
            
            try:
                if seleccionado == 2:
                    raise Exception('DETAIL:Debe seleccionar al menos un precio')
            
                mycontrato.save()
                return viewcontrato(request, idcliente, idcon)
            except Exception, e:
                exc_info = e.__str__() # sys.exc_info()[:1]
                c = exc_info.find("DETAIL:")
                if c < 0:
                    l = l + ["Error Fatal."]
                else:
                    c = exc_info[c + 7:]
                    l=l+[c]
                    
                form = FContrato(request.POST)
                uri="/comerciax/admincom/cliente/viewcontrato/" + idcliente + "/" + idcon + "/" 
                edituri = "/comerciax/admincom/cliente/contratoedit/" + idcon + "/" + idcliente + "/"
                #form/form_edit.html
                return render_to_response("admincomerciax/form_contratoedit.html",{'form':form,'title':'Contrato', 'form_name':'Editar contrato','form_description':'Editar el contrato seleccionado','controlador':'Contrato','accion':edituri
                                                         , 'cancelbtn':uri,'error2':l},context_instance = RequestContext(request))
    else:
        contratoobj = Contrato.objects.select_related().get(pk=idcon)
        
        
        if contratoobj.para_la_venta:
            para_la_venta = 'V'
        else:
            para_la_venta = 'N'
        
        mn = 'noexistmn'
        cuc = 'noexistcuc'
        otropreciocasco = False
        if contratoobj.preciocostomn:
            mn = 'costomn'
        if contratoobj.preciomn:
            mn = 'ventamn'
        if contratoobj.precioextcup:
            mn='ventaext'
        if contratoobj.preciocostocuc:
            cuc = 'costocuc'
        if contratoobj.preciocuc:
            cuc = 'ventacuc'
        if contratoobj.otro_precio_casco:
            otropreciocasco = True
        
        form = FContrato(initial={"contrato_nro" : contratoobj.contrato_nro,
        "cliente" : Cliente.objects.get(pk = idcliente),
        "fecha_vigencia" : contratoobj.fecha_vigencia,
        "tiempo_vigencia" : contratoobj.tiempo_vigencia,
        "fecha_vencimiento" : contratoobj.fecha_vencimiento,
        "sucursal_mn" : contratoobj.sucursal_mn,
        "sucursal_usd" : contratoobj.sucursal_usd,
#        "plan_contratado": contratoobj.plan_contratado,
        "titular_mn" : contratoobj.titular_mn,
        "titular_usd" : contratoobj.titular_usd,
        "cuenta_mn" : contratoobj.cuenta_mn,
        "cuenta_usd" : contratoobj.cuenta_usd,
        "venta_costo_mn" : mn,
        "venta_costo_cuc" : cuc,
        "para_la_venta" : para_la_venta,
        "otro_precio_casco":otropreciocasco})
            
        uri="/comerciax/admincom/cliente/viewcontrato/" + idcliente + "/" + idcon + "/" 
        edituri = "/comerciax/admincom/cliente/contratoedit/" + idcon + "/" + idcliente + "/"
        #form/form_edit.html
        return render_to_response("admincomerciax/form_contratoedit.html",{'form':form,'title':'Contrato', 'form_name':'Editar contrato','form_description':'Editar el contrato seleccionado','controlador':'Contrato','accion':edituri
                                                         , 'cancelbtn':uri,'error2':l},context_instance = RequestContext(request))

@login_required
def contratocancel(request,idcontrato, idcliente):
    if not request.user.has_perm('admincomerciax.cliente'):
        return render_to_response("denegado.html",locals(),context_instance = RequestContext(request))
    try:
        clientecontratoobj=ClienteContrato.objects.get(contrato=idcontrato,cliente=idcliente)
        clientecontratoobj.cerrado = True
        clientecontratoobj.save()
#        otros=ClienteContrato.objects.filter(contrato=idcontrato,cerrado=False).count()
#        if otros==0:
        contratoobj = Contrato.objects.get(pk=idcontrato)
        contratoobj.cerrado = True
        contratoobj.save()
        
        return viewcliente(request, idcliente)
    except Exception, e:
        error2 = "Error fatal"
        return viewcontrato(request, idcliente, idcontrato, error2)


#############################################################
#        PLANES CONTRATADOS
#############################################################
@login_required
def planes(request):
    if not request.user.has_perm('admincomerciax.planes'):
        return render_to_response("denegado.html",locals(),context_instance = RequestContext(request))
    from comerciax.casco.models import Fechacierre
    year_actual=str(Fechacierre.objects.get(almacen='cm').year)
    
    return render_to_response("admincomerciax/indexplanes.html",locals(),context_instance = RequestContext(request))

def get_planes_list(request):
    #initial querySet
    querySet = ClienteContrato.objects.select_related().filter(contrato__cerrado=False).order_by('cliente__nombre')
    
    #columnIndexNameMap is required for correct sorting behavior
#    columnIndexNameMap = { 0:'codigo', 1:'codigo', 2:'nombre', 3:'contrato__contrato_nro',4:'direccion', 5:'telefono', 6:'fax'}
    columnIndexNameMap = { 0:'cliente__codigo', 1:'cliente__codigo', 2:'cliente__nombre', 3:'cliente__organismo__siglas_organismo',4:'cliente__provincia__descripcion_provincia',5:'contrato__contrato_nro', 6:'contrato__id_contrato'}
    #model fields listed in searchableColumns will be used for filtering (Search)
    searchableColumns = ['cliente__codigo','cliente__nombre','cliente__organismo__siglas_organismo','cliente__provincia__descripcion_provincia','contrato__contrato_nro']
    #path to template used to generate json
    jsonTemplatePath = 'admincomerciax/json/json_planes.txt'
    
    #call to generic function from utils
    return get_datatables_records(request, querySet , columnIndexNameMap, searchableColumns, jsonTemplatePath)


@login_required
def viewplan(request,idcont):
    if not request.user.has_perm('admincomerciax.planes'):
        return render_to_response("denegado.html",locals(),context_instance = RequestContext(request))
    c = None
    l = []
    
    if request.method == 'POST':
        form = FPlan(request.POST)
        if form.is_valid():
            contrato_ = Contrato.objects.get(pk=idcont)
            plan=Planes.objects.filter(contrato=contrato_,plan_ano=int(form.cleaned_data['anoplan']))
            if plan.__len__()==0:
#            contrato.plan_contratado = form.cleaned_data['plan_contratado']
                plan=Planes()
                plan.id = uuid4()
                plan.contrato=contrato_
            else:
                plan=Planes.objects.get(contrato=contrato_,plan_ano=int(form.cleaned_data['anoplan']))
            plan.plan_contratado=form.cleaned_data['plan_contratado']
            plan.plan_ano=int(form.cleaned_data['anoplan'])
            
            plan.plan_enero=int(form.cleaned_data['plan_enero'])
            plan.plan_febrero=int(form.cleaned_data['plan_febrero'])
            plan.plan_marzo=int(form.cleaned_data['plan_marzo'])
            plan.plan_abril=int(form.cleaned_data['plan_abril'])
            plan.plan_mayo=int(form.cleaned_data['plan_mayo'])
            plan.plan_junio=int(form.cleaned_data['plan_junio'])
            plan.plan_julio=int(form.cleaned_data['plan_julio'])
            plan.plan_agosto=int(form.cleaned_data['plan_agosto'])
            plan.plan_septiembre=int(form.cleaned_data['plan_septiembre'])
            plan.plan_octubre=int(form.cleaned_data['plan_octubre'])
            plan.plan_noviembre=int(form.cleaned_data['plan_noviembre'])
            plan.plan_diciembre=int(form.cleaned_data['plan_diciembre'])
            try:
#                contrato.save()
                plan.save()
                return planes(request)
            except Exception, e:
                exc_info = e.__str__() # sys.exc_info()[:1]
                c = exc_info.find("DETAIL:")
                if c < 0:
                    l = l + ["Error Fatal."]
                else:
                    c = exc_info[c + 7:]
                    l=l+[c]
                    
                transaction.rollback()
                    
                form = FPlan(request.POST)
                
                uri="/comerciax/admincom/planes/index/" 
                uri2="/comerciax/admincom/planes/view/" +idcont+"/"
                #form/form_edit.html
                return render_to_response("admincomerciax/form_contratoedit.html",{'form':form,'title':'Plan Contratado', 'form_name':'Plan Contratado','form_description':'Plan Contratado','controlador':'Contrato','accion':uri2
                                                         , 'cancelbtn':uri,'error2':l},context_instance = RequestContext(request))
            else:
                transaction.commit()
    else:

#        clienteobj = Contrato.objects.select_related().get(pk=idcont)
        form = FPlan()
            
        uri="/comerciax/admincom/planes/index/"  
        uri2="/comerciax/admincom/planes/view/" +idcont+"/"
        return render_to_response("admincomerciax/form_clienteedit.html",{'form':form,'title':'Plan Contratado', 'form_name':'Plan Contratado','form_description':'Plan Contratado','controlador':'Plan Contratado','accion':uri2
                                                         , 'cancelbtn':uri,'error2':l},context_instance = RequestContext(request))

@login_required
def planesadd(request,idcontcli):
    if not request.user.has_perm('admincomerciax.planes'):
        return render_to_response("denegado.html",locals(),context_instance = RequestContext(request))
    c = None
    l = []
    clienteobj=ClienteContrato.objects.select_related().get(pk=idcontcli)
    idcont=clienteobj.contrato.id_contrato
    if request.method == 'POST':
        form = FPlan(request.POST)
        if form.is_valid():
            contrato = Contrato.objects.get(pk=idcont)
            sumameses=form.cleaned_data['plan_enero']+form.cleaned_data['plan_febrero']+form.cleaned_data['plan_marzo']+form.cleaned_data['plan_abril']+\
               form.cleaned_data['plan_mayo']+form.cleaned_data['plan_junio']+form.cleaned_data['plan_julio']+form.cleaned_data['plan_agosto']+\
               form.cleaned_data['plan_septiembre']+form.cleaned_data['plan_octubre']+form.cleaned_data['plan_noviembre']+form.cleaned_data['plan_diciembre']
            if sumameses!=0 and  sumameses!=form.cleaned_data['plan_contratado']:
                form = FPlan(request.POST)
                l=l+["El plan por meses no coincide con el total contratado"]
                uri="/comerciax/admincom/cliente/viewcontrato/" + clienteobj.cliente.id + "/" + idcont 
                return render_to_response("form/form_add.html",{'form':form,'title':'Planes', 'form_name':'Adicionar Planes','form_description':'Introducir planes contratados','controlador':'Contrato','accion':'addplanes',
                                                'cancelbtn':uri, 'error2':l},context_instance = RequestContext(request))      
#            contrato.plan_contratado = form.cleaned_data['plan_contratado']
            planes=Planes()
            planes.id = uuid4()
            planes.plan_contratado=form.cleaned_data['plan_contratado']
            planes.plan_ano=int(form.cleaned_data['anoplan'])
            planes.contrato=contrato
            planes.plan_enero=int(form.cleaned_data['plan_enero'])
            planes.plan_febrero=int(form.cleaned_data['plan_febrero'])
            planes.plan_marzo=int(form.cleaned_data['plan_marzo'])
            planes.plan_abril=int(form.cleaned_data['plan_abril'])
            planes.plan_mayo=int(form.cleaned_data['plan_mayo'])
            planes.plan_junio=int(form.cleaned_data['plan_junio'])
            planes.plan_julio=int(form.cleaned_data['plan_julio'])
            planes.plan_agosto=int(form.cleaned_data['plan_agosto'])
            planes.plan_septiembre=int(form.cleaned_data['plan_septiembre'])
            planes.plan_octubre=int(form.cleaned_data['plan_octubre'])
            planes.plan_noviembre=int(form.cleaned_data['plan_noviembre'])
            planes.plan_diciembre=int(form.cleaned_data['plan_diciembre'])
            try:
                planes.save()
                
                if request.POST.__contains__('submit1'):
                    return HttpResponseRedirect('/comerciax/admincom/cliente/viewcontrato/' + clienteobj.cliente.id + '/' + idcont)
                else:
                    form = FPlan()
                    
            except Exception, e:
                exc_info = e.__str__() # sys.exc_info()[:1]
                c = exc_info.find("DETAIL:")
                if c < 0:
                    l = l + ["Error Fatal."]
                else:
                    c = exc_info[c + 7:]
                    l=l+[c]
                    
                form = FPlan(request.POST)
                uri="/comerciax/admincom/cliente/viewcontrato/" + clienteobj.cliente.id + "/" + idcont 
                return render_to_response("form/form_add.html",{'form':form,'title':'Planes', 'form_name':'Adicionar Planes','form_description':'Introducir planes contratados','controlador':'Contrato','accion':'addplanes',
                                                'cancelbtn':uri, 'error2':l},context_instance = RequestContext(request))
    else:
        
        form = FPlan()
    uri="/comerciax/admincom/cliente/viewcontrato/" + clienteobj.cliente.id + "/" + idcont
    return render_to_response("form/form_add.html",{'form':form,'title':'Planes', 'form_name':'Adicionar Planes','form_description':'Introducir planes contratados','controlador':'Contrato','accion':'addplanes',
                                                'cancelbtn':uri, 'error2':l},context_instance = RequestContext(request))
    

def obteneranos_list(request,idcont,tipo):
    if ClienteContrato.objects.filter(pk=idcont).all().__len__()!=0:
        idcont=ClienteContrato.objects.get(pk=idcont).contrato.id_contrato
    elementos=Contrato.objects.get(pk=idcont)
    ano=elementos.fecha_vigencia.year
    anos=elementos.tiempo_vigencia
    lista=[]
    aplan=[]
    for a1 in range(anos+1):
        if tipo=='0':
            aplan=Planes.objects.filter(contrato=idcont,plan_ano=ano+a1)
        if aplan.__len__()==0:
            lista.append((str(ano+a1),str(ano+a1)))
    return HttpResponse(simplejson.dumps(lista),content_type = 'application/javascript; charset=utf8')

def get_datosplan(request,idcont,idano):
    idano=0 if len(idano)==0 else int(idano)
    plan = Planes.objects.filter(contrato=idcont,plan_ano=idano)
    json_serializer = serializers.get_serializer("json")()
    response = HttpResponse()
    response["Content-type"] = "text/json"
    json_serializer.serialize(plan,ensure_ascii = False, stream = response)
    return response


@login_required
def plandel(request,idplan,idcont):
    if not request.user.has_perm('admincomerciax.planes'):
        return render_to_response("denegado.html",locals(),context_instance = RequestContext(request))
    planes = Planes.objects.get(pk=idplan)
    try:
        planes.delete()
        
        planescont = Planes.objects.select_related().filter(contrato=idcont).order_by('plan_ano')
        
        json_serializer = serializers.get_serializer("json")()
        response = HttpResponse()
        response["Content-type"] = "text/json"
        json_serializer.serialize(planescont,ensure_ascii = False, stream = response)
        return response
    
    except Exception, e:
        error2 = "No se puede eliminar, posibles causas problema de conexion con la BD" 
        return HttpResponse(json.dumps({'error':True, 'message':error2}),mimetype=u'application/json')
    
@login_required
def planedit(request,idplan,idcliente):
    if not request.user.has_perm('admincomerciax.planes'):
        return render_to_response("denegado.html",locals(),context_instance = RequestContext(request))
    c = None
    l = []
    repobj = Planes.objects.select_related().get(pk=idplan)
    idcont= repobj.contrato.id_contrato 
#    idcliente = repobj.cliente.id
    if request.method == 'POST':
        form = FPlanEdit(request.POST)
        a1=form.is_valid()
        if form.is_valid():
            planes = Planes.objects.get(pk=idplan)
            planes.plan_contratado=form.cleaned_data['plan_contratado']
            planes.plan_enero=int(form.cleaned_data['plan_enero'])
            valor_validar=form.cleaned_data['plan_contratado']
            try:
                planes.save()
                return viewcontrato(request, idcliente, idcont)
            except Exception, e:
                exc_info = e.__str__() # sys.exc_info()[:1]
                c = exc_info.find("DETAIL:")
                if c < 0:
                    l = l + ["Error Fatal."]
                else:
                    c = exc_info[c + 7:]
                    l=l+[c]
                    
                form = FPlanEdit(request.POST)
                uri="/comerciax/admincom/cliente/viewcontrato/" + idcliente + "/" +  idcont
                edituri = "/comerciax/admincom/cliente/viewcontrato/" + idcliente + "/" +  idcont
                return render_to_response("form/form_edit.html",{'valor_validar':valor_validar,'tipocliente':'2','form':form,'title':'Planes Contratados', 'form_name':'Editar Planes Contratados','form_description':'Editar Plan contratdo','controlador':'Planes','accion':uri
                                                 , 'cancelbtn':edituri,'error2':l},context_instance = RequestContext(request))
    else:
        
        form = FPlanEdit(initial={"anoplan" : str(repobj.plan_ano),"plan_contratado" : repobj.plan_contratado,
                                  "plan_enero":repobj.plan_enero,
                                  "plan_febrero":repobj.plan_febrero,
                                  "plan_marzo":repobj.plan_marzo,
                                  "plan_abril":repobj.plan_abril,
                                  "plan_mayo":repobj.plan_mayo,
                                  "plan_junio":repobj.plan_junio,
                                  "plan_julio":repobj.plan_julio,
                                  "plan_agosto":repobj.plan_agosto,
                                  "plan_septiembre":repobj.plan_septiembre,
                                  "plan_octubre":repobj.plan_octubre,
                                  "plan_noviembre":repobj.plan_noviembre,
                                  "plan_diciembre":repobj.plan_diciembre
                                  })
        
        valor_validar = repobj.plan_contratado
        edituri="/comerciax/admincom/planes/planedit/" + idplan + "/" +idcliente+"/" 
        uri = "/comerciax/admincom/cliente/viewcontrato/" + idcliente + "/" +  idcont
        return render_to_response("form/form_edit.html",{'valor_validar':valor_validar,'tipocliente':'2','form':form,'title':'Planes Contratados', 'form_name':'Editar Planes Contratados','form_description':'Editar Plan contratdo','controlador':'Planes','accion':edituri,
                                                  'cancelbtn':uri,'error2':l},context_instance = RequestContext(request))
    
@login_required      
def repadd(request,idcont,idcliente):
    if not request.user.has_perm('admincomerciax.cliente'):
        return render_to_response("denegado.html",locals(),context_instance = RequestContext(request))
    c = None
    l = []
    if request.method == 'POST':
        form = FRepresentante(request.POST)
        if form.is_valid():
            myrepresentante = Representante()
            myrepresentante.id = uuid4()
            myrepresentante.nombre = form.cleaned_data['nombre']
            myrepresentante.cargo = form.cleaned_data['cargo']
            myrepresentante.ci = form.cleaned_data['ci']
            myrepresentante.nombramiento = form.cleaned_data['nombramiento']
            myrepresentante.contrato = Contrato.objects.get(pk = idcont)
            try:
                myrepresentante.save()
                if request.POST.__contains__('submit1'):
                    return HttpResponseRedirect('/comerciax/admincom/cliente/viewcontrato/' + idcliente + '/' + idcont)
                else:
                    form = FRepresentante()
                    
            except Exception, e:
                exc_info = e.__str__() # sys.exc_info()[:1]
                c = exc_info.find("DETAIL:")
                if c < 0:
                    l = l + ["Error Fatal."]
                else:
                    c = exc_info[c + 7:]
                    l=l+[c]
                    
                form = FRepresentante(request.POST)
                uri="/comerciax/admincom/cliente/viewcontrato/" + idcliente + "/" + idcont 
                return render_to_response("form/form_add.html",{'form':form,'title':'Representante', 'form_name':'Insertar representante','form_description':'Introducir un nuevo representante al contrato','controlador':'Contrato','accion':'addrep',
                                                    'cancelbtn':uri, 'error2':l},context_instance = RequestContext(request))
    else:
        form = FRepresentante()
    uri="/comerciax/admincom/cliente/viewcontrato/" + idcliente + "/" + idcont
    return render_to_response("form/form_add.html",{'form':form,'title':'Representante', 'form_name':'Insertar representante','form_description':'Introducir un nuevo representante al contrato','controlador':'Contrato','accion':'addrep',
                                                'cancelbtn':uri, 'error2':l},context_instance = RequestContext(request))

@login_required
def repedit(request,idcont,idcliente,idrep):
    if not request.user.has_perm('admincomerciax.cliente'):
        return render_to_response("denegado.html",locals(),context_instance = RequestContext(request))
    c = None
    l = []
    if request.method == 'POST':
        form = FRepresentante(request.POST)
        if form.is_valid():
            myrepresentante = Representante.objects.get(pk=idrep)
            myrepresentante.nombre = form.cleaned_data['nombre']
            myrepresentante.cargo = form.cleaned_data['cargo']
            myrepresentante.ci = form.cleaned_data['ci']
            myrepresentante.nombramiento = form.cleaned_data['nombramiento']
            try:
                myrepresentante.save()
                return viewcontrato(request, idcliente, idcont)
            except Exception, e:
                exc_info = e.__str__() # sys.exc_info()[:1]
                c = exc_info.find("DETAIL:")
                if c < 0:
                    l = l + ["Error Fatal."]
                else:
                    c = exc_info[c + 7:]
                    l=l+[c]
                    
                form = FRepresentante(request.POST)
                uri="/comerciax/admincom/cliente/viewcontrato/" + idcliente + "/" + idcont 
                edituri = "/comerciax/admincom/cliente/repedit/" + idcont + "/" + idcliente + "/" + idrep
                return render_to_response("form/form_edit.html",{'tipocliente':'2','form':form,'title':'Representante', 'form_name':'Editar representante','form_description':'Editar el representante seleccionado','controlador':'Contrato','accion':edituri
                                                         , 'cancelbtn':uri,'error2':l},context_instance = RequestContext(request))
    else:
        repobj = Representante.objects.select_related().get(pk=idrep)
        form = FRepresentante(initial={"nombre" : repobj.nombre,"cargo" : repobj.cargo,"nombramiento":repobj.nombramiento,"ci" : repobj.ci})
            
        uri="/comerciax/admincom/cliente/viewcontrato/" + idcliente + "/" + idcont 
        edituri = "/comerciax/admincom/cliente/repedit/" + idcont + "/" + idcliente + "/" + idrep + "/"
        return render_to_response("form/form_edit.html",{'tipocliente':'2','form':form,'title':'Representante', 'form_name':'Editar representante','form_description':'Editar el representante seleccionado','controlador':'Contrato','accion':edituri
                                                 , 'cancelbtn':uri,'error2':l},context_instance = RequestContext(request))

@login_required
def repdel(request,idcont,idcliente,idrep):
    if not request.user.has_perm('admincomerciax.cliente'):
        return render_to_response("denegado.html",locals(),context_instance = RequestContext(request))
    myrepresentante = Representante.objects.get(pk=idrep)
    try:
        myrepresentante.delete()
        #uri="/comerciax/admincom/cliente/viewcontrato/" + idcliente + "/" + idcont 
        #return HttpResponseRedirect(uri)
    
        representantes = Representante.objects.select_related().filter(contrato=idcont)
        
        json_serializer = serializers.get_serializer("json")()
        response = HttpResponse()
        response["Content-type"] = "text/json"
        json_serializer.serialize(representantes,ensure_ascii = False, stream = response)
        return response
    
    except Exception, e:
        error2 = "No se puede eliminar el representante, posibles causas problema de conexion con la BD" 
        #return render_to_response(uri,locals())
        return HttpResponse(json.dumps({'error':True, 'message':error2}),mimetype=u'application/json')

@login_required    
def transadd(request,idcont,idcliente):
    if not request.user.has_perm('admincomerciax.cliente'):
        return render_to_response("denegado.html",locals(),context_instance = RequestContext(request))
    c = None
    l = []
    if request.method == 'POST':
        form = FTransportador(request.POST)
        if form.is_valid():
            mytransportador = Transpotador()
            mytransportador.id = uuid4()
            mytransportador.nombre = form.cleaned_data['nombre']
            mytransportador.activo = True
            #mytransportador.licencia = form.cleaned_data['licencia']
            mytransportador.ci = form.cleaned_data['ci']
            mytransportador.contrato = Contrato.objects.get(pk = idcont)
            try:
                mytransportador.save()
                if request.POST.__contains__('submit1'):
                    return HttpResponseRedirect('/comerciax/admincom/cliente/viewcontrato/' + idcliente + '/' + idcont)
                else:
                    form = FTransportador(initial={"activo":True})
                    
            except Exception, e:
                exc_info = e.__str__() # sys.exc_info()[:1]
                c = exc_info.find("DETAIL:")
                if c < 0:
                    l = l + ["Error Fatal."]
                else:
                    c = exc_info[c + 7:]
                    l=l+[c]
                    
                form = FTransportador(request.POST)
                uri="/comerciax/admincom/cliente/viewcontrato/" + idcliente + "/" + idcont 
                return render_to_response("form/form_add.html",{'form':form,'title':'Autorizados', 'form_name':'Insertar autorizados','form_description':'Introducir una nueva persona autorizada al contrato','controlador':'Contrato','accion':'addtrans',
                                                    'cancelbtn':uri, 'error2':l},context_instance = RequestContext(request))
    else:
        form = FTransportador(initial={"activo":True})
    uri="/comerciax/admincom/cliente/viewcontrato/" + idcliente + "/" + idcont
    return render_to_response("form/form_add.html",{'form':form,'title':'Autorizados', 'form_name':'Insertar autorizados','form_description':'Introducir una nueva persona autorizada al contrato','controlador':'Contrato','accion':'addtrans',
                                                'cancelbtn':uri, 'error2':l},context_instance = RequestContext(request))

@login_required
def transedit(request,idcont,idcliente,idtrans):
    if not request.user.has_perm('admincomerciax.cliente'):
        return render_to_response("denegado.html",locals(),context_instance = RequestContext(request))
    c = None
    l = []
    if request.method == 'POST':
        form = FTransportador(request.POST)
        if form.is_valid():
            mytransportador = Transpotador.objects.get(pk=idtrans)
            mytransportador.nombre = form.cleaned_data['nombre']
            mytransportador.activo = form.cleaned_data['activo']
            #mytransportador.licencia = form.cleaned_data['licencia']
            mytransportador.ci = form.cleaned_data['ci']
            try:
                mytransportador.save()
                return viewcontrato(request, idcliente, idcont)
            except Exception, e:
                exc_info = e.__str__() # sys.exc_info()[:1]
                c = exc_info.find("DETAIL:")
                if c < 0:
                    l = l + ["Error Fatal."]
                else:
                    c = exc_info[c + 7:]
                    l=l+[c]
                    
                form = FTransportador(request.POST)
                uri="/comerciax/admincom/cliente/viewcontrato/" + idcliente + "/" + idcont 
                edituri = "/comerciax/admincom/cliente/transedit/" + idcont + "/" + idcliente + "/" + idtrans
                return render_to_response("form/form_edit.html",{'tipocliente':'2','form':form,'title':'Autorizados', 'form_name':'Editar autorizados','form_description':'Editar persona autorizada seleccionada','controlador':'Contrato','accion':edituri
                                                         , 'cancelbtn':uri,'error2':l},context_instance = RequestContext(request))
    else:
        repobj = Transpotador.objects.select_related().get(pk=idtrans)
        form = FTransportador(initial={"nombre" : repobj.nombre,"ci" : repobj.ci,"activo":repobj.activo})
            
        uri="/comerciax/admincom/cliente/viewcontrato/" + idcliente + "/" + idcont 
        edituri = "/comerciax/admincom/cliente/transedit/" + idcont + "/" + idcliente + "/" + idtrans + "/"
        return render_to_response("form/form_edit.html",{'tipocliente':'2','form':form,'title':'Autorizados', 'form_name':'Editar autorizados','form_description':'Editar persona autorizada seleccionada','controlador':'Contrato','accion':edituri
                                                 , 'cancelbtn':uri,'error2':l},context_instance = RequestContext(request))

@login_required
def transdel(request,idcont,idcliente,idtrans):
    if not request.user.has_perm('admincomerciax.cliente'):
        return render_to_response("denegado.html",locals(),context_instance = RequestContext(request))
    mytransportador = Transpotador.objects.get(pk=idtrans)
    try:
        mytransportador.delete()
    except Exception, e:
        mytransportador.activo=False
        mytransportador.save()
        
#    transportadores = Transpotador.objects.select_related().filter(contrato=idcont,activo=True)
    transportadores = Transpotador.objects.select_related().filter(contrato=idcont).order_by('-activo','nombre')
    
    json_serializer = serializers.get_serializer("json")()
    response = HttpResponse()
    response["Content-type"] = "text/json"
    json_serializer.serialize(transportadores,ensure_ascii = False, stream = response)
    return response
    
#    except Exception, e:
#        mytransportador.activo=False
#        
#        error2 = "No se puede eliminar, posibles causas problema de conexion con la BD" 
#        return HttpResponse(json.dumps({'error':True, 'message':error2}),mimetype=u'application/json')
    
    
def get_cnroc_list(request):
    #prepare the params

    
    querySet = ConsOrg.objects.all().select_related()
    #querySet = querySet.filter(doc__fecha_doc__year=2010)
    
    columnIndexNameMap = {0: 'admincomerciax_organismo.codigo_organismo',1: 'admincomerciax_organismo.codigo_organismo',2:'admincomerciax_organismo.siglas_organismo'}
    #searchableColumns = ['cliente__nombre','recepcioncliente_nro']
    searchableColumns = ['organismo__organismo_nombre']
    #path to template used to generate json
    jsonTemplatePath = 'admincomerciax/json/json_cnroc.txt'


    #call to generic function from utils
    return get_datatables_records(request, querySet, columnIndexNameMap, searchableColumns, jsonTemplatePath)


    
#@login_required
def confignrocasco_index(request):
    if not request.user.has_perm('admincomerciax.consorg'):
        return render_to_response("denegado.html",locals(),context_instance = RequestContext(request))
    return render_to_response('admincomerciax/confignrocascoindex.html',locals(),context_instance = RequestContext(request))

#@login_required
@transaction.commit_on_success()
def confignrocasco_add(request):
    if not request.user.has_perm('admincomerciax.consorg'):
        return render_to_response("denegado.html",locals(),context_instance = RequestContext(request))
    nombre_form='Configuración'
    descripcion_form='Configurar número de cascos para organismos'
    titulo_form='Configuración' 
    controlador_form='Configuración'
    accion_form='/comerciax/admincom/confignrocasco/add'
    cancelbtn_form='/comerciax/admincom/confignrocasco/index'
    cons=ConsOrg.objects.all()
    lorg=[]
    l=[]
    for consec in cons:
        lorg=lorg+[consec.org.id]
    conforg=Organismo.objects.all().exclude(pk__in=lorg).order_by('codigo_organismo')
    if request.method == 'POST':
        seleccion=request.POST.keys()
        k=0

        while True:
            if k==seleccion.__len__():
                break
            org=Organismo.objects.filter(codigo_organismo=seleccion[k])

            if org.count()!=0:
                '''
                Los selecionados se adicionan
                '''
                detalle=ConsOrg()
                detalle.id=uuid4()
                detalle.org=Organismo.objects.get(codigo_organismo=seleccion[k])
                try:
                    detalle.save()
                except Exception, e:
                    exc_info = e.__str__() # sys.exc_info()[:1]
                    c = exc_info.find("DETAIL:")
                    
                    if c < 0:
                        l=l+["Error Fatal."]
                    else:
                        #l=['El casco ' + str(nro) +' ya existe en este documento']
                        c = exc_info[c + 7:]
                        transaction.rollback()
                        return render_to_response('admincomerciax/confignrocasco.html', {'title':'Configuración','elementos_detalle':conforg,'error2':l,'title':titulo_form,'controlador':controlador_form,'accion':accion_form,
                                                     'cancelbtn':cancelbtn_form,'form_name':'Configurar', 'form_description':descripcion_form},context_instance = RequestContext(request))
    
            k=k+1
        if request.POST.__contains__('submit1'):
            cons=ConsOrg.objects.all()
            lorg=[]
            for consec in cons:
                lorg=lorg+[consec.org.id]
            conforg=Organismo.objects.all().exclude(pk__in=lorg).order_by('codigo_organismo')
            return render_to_response('admincomerciax/confignrocasco.html', {'title':'Configuración','elementos_detalle':conforg,'error2':l,'title':titulo_form,'controlador':controlador_form,'accion':accion_form,
                                                     'cancelbtn':cancelbtn_form,'form_name':'Configurar',  'form_description':descripcion_form},context_instance = RequestContext(request))
    
        else:
            return HttpResponseRedirect('/comerciax/admincom/confignrocasco/index/')
    
    return render_to_response('admincomerciax/confignrocasco.html', {'title':'Configuración','elementos_detalle':conforg,'error2':l,'title':titulo_form,'controlador':controlador_form,'accion':accion_form,
                                                     'cancelbtn':cancelbtn_form,'form_name':'Configurar',  'form_description':descripcion_form},context_instance = RequestContext(request))
 
 
def editar_confignrocasco(request, codigo):
    if not request.user.has_perm('admincomerciax.consorg'):
        return render_to_response("denegado.html",locals(),context_instance = RequestContext(request))
    cade='-'+codigo+'-'
    casco=Casco.objects.all()
    for codi in casco:
        if (cade in codi.id_casco):
            return 2
    return 1
               
#@login_required
def confignrocasco_view(request,idconf):
    if not request.user.has_perm('admincomerciax.consorg'):
        return render_to_response("denegado.html",locals(),context_instance = RequestContext(request)) 
    
    l=[]
    cp = ConsOrg.objects.get(pk=idconf)
    codigo=cp.org.codigo_organismo
    name=cp.org.siglas_organismo
    
   
    '''
    FALTA HACER EL PROCEDIMEINTO PARA VERIFICAR SI SE PUEDE ELIMINAR ESA CONFIGURACION.
    SE PUEDE ELIMINAR SI NO HAY NRO DE CASCOS IMPLICADOS
    '''
    editar=editar_confignrocasco(request,codigo)
    return render_to_response('admincomerciax/viewconfnrocasco.html',{'organismo_name':codigo,'organismo_siglas':name,'rc_id':idconf,'edito':editar,'error2':l},context_instance = RequestContext(request))

#@login_required
@transaction.commit_on_success()
def confignrocasco_del(request,idconf):
    if not request.user.has_perm('admincomerciax.consorg'):
        return render_to_response("denegado.html",locals(),context_instance = RequestContext(request))    
    
    try:
        ConsOrg.objects.get(pk=idconf).delete()
        return HttpResponseRedirect('/comerciax/admincom/confignrocasco/index')
    except Exception :
        transaction.rollback()
        l = ['Error al eliminar la configuración']
        cp = ConsOrg.objects.get(pk=idconf)
        
        orga=Organismo.objects.get(organismo_codigo=cp.codigo_organismo)
        name=orga.sigla_organismo
        codigo=orga.codigo_organismo
        
        editar=1

        return render_to_response('admincomerciax/viewconfnrocasco.html',{'organismo_name':codigo,'organismo_siglas':name,'rc_id':idconf,'edito':editar,'error2':l},context_instance = RequestContext(request))

    else:
        transaction.commit()

@login_required
@transaction.commit_on_success()
def eliminar_casco(request):
    nombre_form='Eliminar Casco'
    descripcion_form='Eliminar Casco'
    titulo_form='Eliminar Casco' 
    controlador_form='Eliminar Casco'
    accion_form='eliminar_casco'
    cancelbtn='/comerciax/index/'
    mesg=[]
    arrorganismo=Organismo.objects.all()
    arrprovincia=Provincias.objects.all()
    if request.method == 'POST':
        filtro=[]
        idcasco=''
        
        if request.POST.__contains__('submit'):
            seleccion=request.POST.keys()
            k=0
            while True:
                if k==seleccion.__len__():
                    break
                if seleccion[k]!='provincia' and seleccion[k]!='submit' and seleccion[k]!='organismo' and seleccion[k]!='cliente':
                    obj_casco=Casco.objects.get(pk=seleccion[k])
                    DetalleRC.objects.select_related().filter(casco=obj_casco).delete() 
                    DetalleDIP.objects.select_related().filter(casco=obj_casco).delete()
                    DetalleDVP.objects.select_related().filter(casco=obj_casco).delete()
                    DetalleTransferencia.objects.select_related().filter(casco=obj_casco).delete()
                    DetalleCC.objects.select_related().filter(casco=obj_casco).delete()
                    DetalleVP.objects.select_related().filter(casco=obj_casco).delete()
                    DetallePT.objects.select_related().filter(casco=obj_casco).delete()
                    DetallePTE.objects.select_related().filter(casco=obj_casco).delete()
                    TrazabilidadCasco.objects.select_related().filter(casco=obj_casco).delete()
                    Detalle_DC.objects.select_related().filter(casco=obj_casco).delete()
                    Casco.objects.select_related().filter(id_casco=obj_casco.id_casco).delete()
                k+=1
    
    return render_to_response("admincomerciax/eliminar_casco.html",{'tipo':"PT",'arrorganismo':arrorganismo,'arrprovincia':arrprovincia,'cancelbtn':cancelbtn,'title':titulo_form, 'form_name':nombre_form,'form_description':descripcion_form,
                                                                'controlador':controlador_form,'accion':accion_form,'error2':mesg},context_instance = RequestContext(request))

@login_required
@transaction.commit_on_success()
def config_smtp(request):
    nombre_form = 'Configurar Correo SMTP'
    descripcion_form = 'Configurar Correo SMTP'
    titulo_form = 'Configurar Correo SMTP' 
    controlador_form = 'Configurar Correo SMTP'
    accion_form = ''
    
    cancelbtn_form = '/comerciax/index'
    l = []
    nuevo=False
    try:
        querySet = Config_SMTPEmail.objects.get()
    except Exception, e:
        nuevo=True
        form=Config_SMTP()
            
    if request.method == 'POST':
        form = Config_SMTP(request.POST)
        if form.is_valid():
            confi=Config_SMTPEmail() if nuevo else Config_SMTPEmail.objects.get()
            confi.servidor = form.cleaned_data['servidor']
            confi.puerto = form.cleaned_data['puerto']
            confi.ssl = form.cleaned_data['ssl']
            confi.correo = form.cleaned_data['email']
            if form.cleaned_data['password']!='********************':
                passw=form.cleaned_data['password']
                confi.set_password(form.cleaned_data['password'])
            else: passw=base64.b64decode(confi.contrasena)
            
            try:
                if form.cleaned_data['ssl']==True:
                    smtp = smtplib.SMTP_SSL(host=form.cleaned_data['servidor'],port=form.cleaned_data['puerto'])
                else:
                    smtp = smtplib.SMTP(host=form.cleaned_data['servidor'],port=form.cleaned_data['puerto'])
                smtp.ehlo()
                smtp.login(form.cleaned_data['email'],passw)
            except Exception, e:
                form = Config_SMTP(initial={"servidor" : confi.servidor,
                                  "puerto":confi.puerto,
                                  "ssl":confi.ssl,
                                  "email":confi.correo,
                                  "password":"********************"
                                  })
                l=["Error de conexión. "+e.__str__()]       
                return render_to_response("form/form_add.html", {'acepto':"1",'form':form,'title':titulo_form, 'form_name':nombre_form,'form_description':descripcion_form,                    
                                          'controlador':controlador_form,'cancelbtn':cancelbtn_form,'accion':accion_form,'error2':l,'continua':1},context_instance = RequestContext(request))
                
            
            confi.save()
            
            form = Config_SMTP(initial={"servidor" : confi.servidor,
                                  "puerto":confi.puerto,
                                  "ssl":confi.ssl,
                                  "email":confi.correo,
                                  "password":"********************"
                                  })
            return render_to_response("form/form_add.html", {'acepto':"1",'form':form,'title':titulo_form, 'form_name':nombre_form,'form_description':descripcion_form,                    
                                          'controlador':controlador_form,'cancelbtn':cancelbtn_form,'accion':accion_form,'error2':l,'continua':1},context_instance = RequestContext(request))
    else:
        try:
            querySet = Config_SMTPEmail.objects.get()
        except Exception, e:
            form=Config_SMTP()
            l=[]       
            return render_to_response("form/form_add.html", {'acepto':"1",'form':form,'title':titulo_form, 'form_name':nombre_form,'form_description':descripcion_form,                    
                                          'controlador':controlador_form,'cancelbtn':cancelbtn_form,'accion':accion_form,'error2':l,'continua':1},context_instance = RequestContext(request))
            
        form = Config_SMTP(initial={"servidor" : querySet.servidor,
                                  "puerto":querySet.puerto,
                                  "ssl":querySet.ssl,
                                  "email":querySet.correo,
                                  "password":"********************"
                                  }) 
        l=[]       
        return render_to_response("form/form_add.html", {'acepto':"1",'form':form,'title':titulo_form, 'form_name':nombre_form,'form_description':descripcion_form,                    
                                          'controlador':controlador_form,'cancelbtn':cancelbtn_form,'accion':accion_form,'error2':l,'continua':1},context_instance = RequestContext(request)) 
    return
        
            
@login_required
@transaction.commit_on_success()
def detalleeliminar_list(request,idcli,tipo):
    if tipo=="PT":
        cascos=Casco.objects.select_related().filter(estado_actual="PT",detallerc__rc__cliente__id=idcli).order_by('casco_nro')
    else:
        cascos=Casco.objects.select_related().filter(estado_actual="Casco",ocioso=True,detallerc__rc__cliente__id=idcli).order_by('casco_nro')
    
    lista_valores=[]
    for detalles in cascos:
        lista_valores=lista_valores+[{"casco_nro":detalles.casco_nro,"pk":detalles.id_casco,"medida":detalles.producto.descripcion,"dias":detalles.get_dias()}]
    
    return HttpResponse(simplejson.dumps(lista_valores),content_type = 'application/javascript; charset=utf8') 

@login_required
def ver_fecha(request):
    if not request.user.has_perm('admincomerciax.fecha_ver'):
        return render_to_response("denegado.html",locals(),context_instance = RequestContext(request))
    nombre_form='Ver Documentos'
    descripcion_form='Ver Documentos'
    titulo_form='Ver Documentos' 
    controlador_form='Ver Documentos'
    accion_form=uri2="/comerciax/admincom/ver_fecha/"
    cancelbtn='/comerciax/index/'
    l=[]
    uri="/comerciax/index/"
    
    if request.method == 'POST':
        form = VerFecha(request.POST)
        if form.is_valid():
            
            datos=Fecha_Ver()
            if Fecha_Ver.objects.all().count()==0:
                datos=Fecha_Ver()
                datos.id=uuid4()
            else:
                datos=Fecha_Ver.objects.get()
            datos.fecha=form.cleaned_data['desde']
            try:
                datos.save()
                form = VerFecha()
                return HttpResponseRedirect('/comerciax/admincom/ver_fecha/')
            except Exception, e:
                exc_info = e.__str__() # sys.exc_info()[:1]
                c = exc_info.find("DETAIL:")
                if c < 0:
                    l = l + ["Error Fatal."]
                else:
                    c = exc_info[c + 7:]
                    l=l+[c]
                    
                form = VerFecha(request.POST)
                 
                return render_to_response("form/form_add.html",{'form':form,'title':nombre_form, 'form_name':nombre_form,'form_description':controlador_form,'controlador':controlador_form,'accion':accion_form,
                                                    'cancelbtn':uri, 'error2':l,'continua':1},context_instance = RequestContext(request))
    else:
        form = VerFecha()
        if Fecha_Ver.objects.all().count()!=0:            
            form = VerFecha(initial={"desde" : Fecha_Ver.objects.get().fecha})
        return render_to_response("form/form_add.html",{'form':form,'title':nombre_form, 'form_name':nombre_form,'form_description':controlador_form,'controlador':controlador_form,'accion':accion_form,
                                                    'cancelbtn':uri, 'error2':l,'continua':1},context_instance = RequestContext(request))

@login_required
@transaction.commit_on_success()
def ocioso_casco(request):
    nombre_form='Pasar Casco a Ocisos'
    descripcion_form='Pasar Casco a Ocisos'
    titulo_form='Pasar Casco a Ocisos' 
    controlador_form='Pasar Casco a Ocisos'
    accion_form='ocioso_casco'
    cancelbtn='/comerciax/index/'
    mesg=[]
    arrorganismo=Organismo.objects.all()
    arrprovincia=Provincias.objects.all()
    if request.method == 'POST':
        filtro=[]
        idcasco=''
        
        if request.POST.__contains__('submit'):
            seleccion=request.POST.keys()
            k=0
            while True:
                if k==seleccion.__len__():
                    break
                if seleccion[k]!='provincia' and seleccion[k]!='submit' and seleccion[k]!='organismo' and seleccion[k]!='cliente':
                    obj_casco=Casco.objects.get(pk=seleccion[k])
                    obj_casco.ocioso = True
                    obj_casco.save()
                k+=1
    
    return render_to_response("admincomerciax/ocioso_casco.html",{'arrorganismo':arrorganismo,'arrprovincia':arrprovincia,'cancelbtn':cancelbtn,'title':titulo_form, 'form_name':nombre_form,'form_description':descripcion_form,
                                                                'controlador':controlador_form,'accion':accion_form,'error2':mesg},context_instance = RequestContext(request))
            
            
@login_required
@transaction.commit_on_success()
def detalleocioso_list(request,idcli):
    
    cascos=Casco.objects.select_related().filter(estado_actual="Casco",ocioso = False,detallerc__rc__cliente__id=idcli).order_by('fecha','casco_nro')
    
    lista_valores=[]
    for detalles in cascos:
        lista_valores=lista_valores+[{"casco_nro":detalles.casco_nro,"pk":detalles.id_casco,"medida":detalles.producto.descripcion,"dias":detalles.get_dias()}]
    
    return HttpResponse(simplejson.dumps(lista_valores),content_type = 'application/javascript; charset=utf8')  

@login_required
@transaction.commit_on_success()
def eliminar_ocioso(request):
    nombre_form='Eliminar Casco Ocioso'
    descripcion_form='Eliminar Casco Ocioso'
    titulo_form='Eliminar Casco Ocioso' 
    controlador_form='Eliminar Casco Ocioso'
    accion_form='eliminar_ocioso'
    cancelbtn='/comerciax/index/'
    mesg=[]
    arrorganismo=Organismo.objects.all()
    arrprovincia=Provincias.objects.all()
    if request.method == 'POST':
        filtro=[]
        idcasco=''
        
        if request.POST.__contains__('submit'):
            seleccion=request.POST.keys()
            k=0
            while True:
                if k==seleccion.__len__():
                    break
                if seleccion[k]!='provincia' and seleccion[k]!='submit' and seleccion[k]!='organismo' and seleccion[k]!='cliente':
                    obj_casco=Casco.objects.get(pk=seleccion[k])
#                    DetalleRC.objects.select_related().filter(casco=obj_casco).delete() 
#                    DetalleDIP.objects.select_related().filter(casco=obj_casco).delete()
#                    DetalleDVP.objects.select_related().filter(casco=obj_casco).delete()
#                    DetalleTransferencia.objects.select_related().filter(casco=obj_casco).delete()
#                    DetalleCC.objects.select_related().filter(casco=obj_casco).delete()
#                    DetalleVP.objects.select_related().filter(casco=obj_casco).delete()
#                    DetallePT.objects.select_related().filter(casco=obj_casco).delete()
#                    DetallePTE.objects.select_related().filter(casco=obj_casco).delete()
#                    TrazabilidadCasco.objects.select_related().filter(casco=obj_casco).delete()
#                    Detalle_DC.objects.select_related().filter(casco=obj_casco).delete()
                    Casco.objects.select_related().filter(id_casco=obj_casco.id_casco).delete()
                k+=1
    
    return render_to_response("admincomerciax/eliminar_casco.html",{'tipo':"O",'arrorganismo':arrorganismo,'arrprovincia':arrprovincia,'cancelbtn':cancelbtn,'title':titulo_form, 'form_name':nombre_form,'form_description':descripcion_form,
                                                                'controlador':controlador_form,'accion':accion_form,'error2':mesg},context_instance = RequestContext(request))