#-*- coding: utf-8 -*-
from decimal import Decimal

from django.contrib.auth.decorators import login_required
from django.shortcuts import render_to_response
from django.template.context import RequestContext
from django.template import Template, Context
from django import template


from comerciax.casco.forms import *
from comerciax.casco.models import *
from comerciax.admincomerciax.models import *
from comerciax.admincomerciax.forms import *
import datetime
from uuid import uuid4
from django.http import HttpResponseRedirect, HttpRequest
from django.db import transaction
from django.utils import simplejson
from comerciax.comercial.models import *
from comerciax.comercial.forms import *
from comerciax.casco.views import actualiza_traza,add_trazabilidad
import hashlib
from django.db.models import Count,Max
from comerciax import utils
from django.db import connection
from collections import OrderedDict
from django.db.models import Q


from pyPdf import PdfFileReader, PdfFileWriter

import os
import comerciax.settings
import random
import base64




#===============================================================================
# Imports para pdfs
#===============================================================================
from comerciax.reportes import report_class

from comercial.models import FacturasProdAlter, DetalleFacturaProdAlter, \
    FacturasProdAlterPart, DetalleFacturaProdAlterPart

tipo_entrada = {'O':'Otro', 'A':'Ajuste', 'K':'Vulca', 'V':'Venta', 'R':'Regrabable'}

#############################################################
#                              REPORTES                     #
#############################################################
@login_required
def formconcixorgprov(request):
    if not request.user.has_perm('comercial.oferta'):
        return render_to_response("denegado.html",locals(),context_instance = RequestContext(request))
    mesg = []
    queryset=[]
    filtro = []
    
    if request.method == 'POST':
        form = Fformconcixorgprov(request.POST)
        
        
        if form.is_valid():
            desde  = form.cleaned_data['desde']
            hasta  = form.cleaned_data['hasta']
            org = form.cleaned_data['organismo']
            orga = org.siglas_organismo
            filtro.append({'desde':desde,'hasta':hasta,'empresa':orga})
            '''
                - si no se pasa la provincia como parametro se deben recorrer todas las provincias
            '''
            org2 = org.id
            data1, total = concixorgprov(request, desde, hasta, org2)
            
            data = OrderedDict(sorted(data1.items(), key=lambda t: t[0]))
            fechahoy = fecha_hoy()
            for index, values in data1.iteritems():
                for filas in values:
                    queryset.append({'provincia':index,'cierre':filas['cierre'],'almc_semana':filas['almc_semana'],'almc_mes':filas['almc_mes'],'almc_year':filas['almc_year'],
                                     'inserv_semana':filas['inserv_semana'],'inserv_mes':filas['inserv_mes'],'inserv_year':filas['inserv_year'],
                                     'factu_semana':filas['factu_semana'],'factu_mes':filas['factu_mes'],'factu_year':filas['factu_year'],
                                     'total_recog':filas['total_recog'],'por_recog_terminados':filas['por_recog_terminados'],
                                     'por_recog_inservible':filas['por_recog_inservible'],'total_por_recog':filas['total_por_recog'],'decom_year':filas['decom_year'],
                                     'pend_total':filas['pend_total'],'casco_x_prod':filas['casco_x_prod']})
            if not request.POST.__contains__('submit2'):
                return render_to_response("report/conciliacionxorgxprov.html",locals(),context_instance = RequestContext(request))
            else:
                if queryset.__len__():    
                        pdf_file_name=os.path.join(comerciax.settings.ADMIN_MEDIA_PDF,"Conciliacion con los Clientes.pdf")
                        if report_class.Reportes.GenerarRep(report_class.Reportes() , queryset, "concil_recap",pdf_file_name,filtro)==0:
                            form = Fformconcixcliente()
                            return render_to_response("report/formconciliacionxcliente.html",{'form':form,'title':'Conciliación con las Entidades', 'form_name':'Reportes',
                                                                                              'form_description':'Conciliación con los clientes', 'controlador':'Reportes',
                                                                                              'accion':formbalacvsrecap,"error2":mesg,},context_instance = RequestContext(request))               
                        else:
                            input = PdfFileReader(file(pdf_file_name,"rb"))
                            output = PdfFileWriter()
                            for page in input.pages:
                                output.addPage(page)
                            buffer = StringIO.StringIO()
                            output.write(buffer)
                            response = HttpResponse(mimetype='application/pdf')
                            response['Content-Disposition'] = 'attachment; filename=%s'%(pdf_file_name)
                            response.write(buffer.getvalue())
                            return response
         
        
    else:
        form = Fformconcixorgprov()
        return render_to_response("report/formconciliacionxcliente.html",{'form':form,'title':'Conciliación con las Entidades', 'form_name':'Reportes','form_description':'Conciliación con los clientes','controlador':'Reportes','accion':formbalacvsrecap
                                ,"error2":mesg,},context_instance = RequestContext(request))

@login_required
@transaction.commit_on_success
def concixorgprov(request,desde,hasta,org):
    if not request.user.has_perm('comercial.oferta'):
        return render_to_response("denegado.html",locals(),context_instance = RequestContext(request))
    
    semanainicio = desde
    semanafin = hasta
    mes = desde.month
    year = desde.year
    inicioyear = datetime.date(year,1,1)
    lastdaymes = Meses.meses_name[mes]
    iniciomes = datetime.date(year,mes,1)
    
    data=[]
    dataprov={}
    nuevodata={}
    
    
    totales = {'cierre':0,
            'almc_semana':0,
            'almc_mes':0,
            'almc_year':0,
            'inserv_semana':0,
            'inserv_mes':0,
            'inserv_year':0,
            'factu_semana':0,
            'factu_mes':0,
            'factu_year':0,
            'decom_semana':0,
            'decom_mes':0,
            'decom_year':0,
            'total_recog':0,
            'por_recog_terminados':0,
            'por_recog_inservible':0,
            'total_por_recog':0,
            'pend_total':0,
            'casco_x_prod':0,
            }
    
    provincias = Provincias.objects.all()
    for provitem  in provincias:
        listtemp=[]
        dataitem = {'cierre':0,
            'almc_semana':0,
            'almc_mes':0,
            'almc_year':0,
            'inserv_semana':0,
            'inserv_mes':0,
            'inserv_year':0,
            'factu_semana':0,
            'factu_mes':0,
            'factu_year':0,
            'decom_semana':0,
            'decom_mes':0,
            'decom_year':0,
            'total_recog':0,
            'por_recog_terminados':0,
            'por_recog_inservible':0,
            'total_por_recog':0,
            'pend_total':0,
            'casco_x_prod':0,
            }
        ''' Cierre year ''' 
        
        ''' semana '''
        resul_semana = get_conci_x_org_prov(desde, hasta, provitem.codigo_provincia,org)
        for item1 in resul_semana:
            aa = item1[0][1]
            if aa == 'Casco':
                dataitem['almc_semana'] = item1[0][0]
                totales['almc_semana'] += item1[0][0]
            if aa == 'DIP' or aa=='ER' or aa=='REE':
                dataitem['inserv_semana'] += item1[0][0]
                totales['inserv_semana'] += item1[0][0]
            if aa == 'Factura':
                dataitem['factu_semana'] = item1[0][0]
                totales['factu_semana'] += item1[0][0]
                
        deco=query_to_dicts("""
                      SELECT 
                          
                          count(casco_casco.estado_actual) as canti
                          
                        FROM
                          casco_casco
                          FULL OUTER JOIN casco_detallerc ON (casco_casco.id_casco = casco_detallerc.casco_id)
                          LEFT OUTER JOIN casco_recepcioncliente ON (casco_detallerc.rc_id = casco_recepcioncliente.doc_recepcioncliente_id)
                          LEFT OUTER JOIN admincomerciax_cliente ON (casco_recepcioncliente.cliente_id = admincomerciax_cliente.id)
                          LEFT OUTER JOIN admincomerciax_organismo ON (admincomerciax_cliente.organismo_id = admincomerciax_organismo.id)
              LEFT OUTER JOIN admincomerciax_provincias ON (admincomerciax_cliente.provincia_id = admincomerciax_provincias.codigo_provincia)
                          LEFT OUTER JOIN casco_doc ON (casco_recepcioncliente.doc_recepcioncliente_id = casco_doc.id_doc)
                        where   decomisado=True and admincomerciax_provincias.codigo_provincia=%s and admincomerciax_organismo.id=%s and 
                         casco_doc.fecha_doc >=%s AND
                                casco_doc.fecha_doc <= %s
                        """,provitem.codigo_provincia,org,desde,hasta) 
        for a1 in deco:
            decom=a1['canti']
        dataitem['almc_semana']+= decom
        totales['almc_semana'] += decom
        dataitem['decom_semana'] = decom
        totales['decom_semana'] += decom
        
        ''' mes '''
        resul_mes = get_conci_x_org_prov(iniciomes, hasta, provitem.codigo_provincia,org)
        for item2 in resul_mes:
            aa = item2[0][1]
            if aa == 'Casco':
                dataitem['almc_mes'] = item2[0][0]
                totales['almc_mes'] += item2[0][0]
            if aa == 'DIP' or aa=='ER' or aa=='REE':
                dataitem['inserv_mes'] += item2[0][0]
                totales['inserv_mes'] += item2[0][0]
            if aa == 'Factura':
                dataitem['factu_mes'] = item2[0][0]
                totales['factu_mes'] += item2[0][0]
        deco=query_to_dicts("""
                      SELECT 
                          
                          count(casco_casco.estado_actual) as canti
                          
                        FROM
                          casco_casco
                          FULL OUTER JOIN casco_detallerc ON (casco_casco.id_casco = casco_detallerc.casco_id)
                          LEFT OUTER JOIN casco_recepcioncliente ON (casco_detallerc.rc_id = casco_recepcioncliente.doc_recepcioncliente_id)
                          LEFT OUTER JOIN admincomerciax_cliente ON (casco_recepcioncliente.cliente_id = admincomerciax_cliente.id)
                          LEFT OUTER JOIN admincomerciax_organismo ON (admincomerciax_cliente.organismo_id = admincomerciax_organismo.id)
              LEFT OUTER JOIN admincomerciax_provincias ON (admincomerciax_cliente.provincia_id = admincomerciax_provincias.codigo_provincia)
                          LEFT OUTER JOIN casco_doc ON (casco_recepcioncliente.doc_recepcioncliente_id = casco_doc.id_doc)
                        where   decomisado=True and admincomerciax_provincias.codigo_provincia=%s and admincomerciax_organismo.id=%s and 
                         casco_doc.fecha_doc >=%s AND
                                casco_doc.fecha_doc <= %s
                        """,provitem.codigo_provincia,org,iniciomes,hasta)                
        for a1 in deco:
            decom=a1['canti']
        dataitem['almc_mes']+=decom
        totales['almc_mes']+=decom
        
        dataitem['decom_mes']+=decom
        totales['decom_mes']+=decom
                
        '''  year  '''
        resul_year = get_conci_x_org_prov(inicioyear, hasta, provitem.codigo_provincia,org)
        for item3 in resul_year:
            aa = item3[0][1]
            if aa == 'Casco':
                dataitem['almc_year'] = item3[0][0]
                totales['almc_year'] += item3[0][0]
            if aa == 'DIP' or aa=='ER' or aa=='REE':
                dataitem['inserv_year'] += item3[0][0]
                totales['inserv_year'] += item3[0][0]
            if aa == 'Factura':
                dataitem['factu_year'] = item3[0][0]
                totales['factu_year'] += item3[0][0]
        deco=query_to_dicts("""
                      SELECT 
                          
                          count(casco_casco.estado_actual) as canti
                          
                        FROM
                          casco_casco
                          FULL OUTER JOIN casco_detallerc ON (casco_casco.id_casco = casco_detallerc.casco_id)
                          LEFT OUTER JOIN casco_recepcioncliente ON (casco_detallerc.rc_id = casco_recepcioncliente.doc_recepcioncliente_id)
                          LEFT OUTER JOIN admincomerciax_cliente ON (casco_recepcioncliente.cliente_id = admincomerciax_cliente.id)
                          LEFT OUTER JOIN admincomerciax_organismo ON (admincomerciax_cliente.organismo_id = admincomerciax_organismo.id)
              LEFT OUTER JOIN admincomerciax_provincias ON (admincomerciax_cliente.provincia_id = admincomerciax_provincias.codigo_provincia)
                          LEFT OUTER JOIN casco_doc ON (casco_recepcioncliente.doc_recepcioncliente_id = casco_doc.id_doc)
                        where   decomisado=True and admincomerciax_provincias.codigo_provincia=%s and admincomerciax_organismo.id=%s and 
                         casco_doc.fecha_doc >=%s AND
                                casco_doc.fecha_doc <= %s
                        """,provitem.codigo_provincia,org,inicioyear,hasta)                
        for a1 in deco:
            decom=a1['canti']
        dataitem['almc_year']+=decom
        totales['almc_year']+= decom
        
        dataitem['decom_year']+=decom
        totales['decom_year']+= decom
        
        
        ''' por recoger terminado '''
        if provitem.codigo_provincia=='12454edc-a53c-43fc-8115-5b07e970680d':
            a1=2
        dataitem['por_recog_terminados'] = RecepcionCliente.objects.select_related().filter(cliente__provincia = provitem.codigo_provincia,
                                                                                            cliente__organismo = org,
                                                                                            detallerc__casco__estado_actual='PT', detallerc__casco__venta=False).count()
        totales['por_recog_terminados'] += dataitem['por_recog_terminados']
        ''' por recoger inservible '''
        dataitem['por_recog_inservible'] = RecepcionCliente.objects.select_related().filter((Q(detallerc__casco__estado_actual='DIP')|
                                                                                            Q(detallerc__casco__estado_actual='ER')|
                                                                                            Q(detallerc__casco__estado_actual='REE')),
                                                                                            cliente__provincia = provitem.codigo_provincia,
                                                                                            cliente__organismo = org).count()
        totales['por_recog_inservible'] += dataitem['por_recog_inservible']
        
        
        ''' total recogido '''
        dataitem['total_recog'] = dataitem['factu_year'] + dataitem['inserv_year'] - dataitem['por_recog_inservible']
        totales['total_recog'] += dataitem['total_recog'] 
        
        ''' por recoger '''
        dataitem['total_por_recog'] =  dataitem['por_recog_terminados'] + dataitem['por_recog_inservible']
        totales['total_por_recog'] += dataitem['total_por_recog']
        ''' pendiente total '''
        dataitem['pend_total'] = dataitem['cierre'] + dataitem['almc_year'] - dataitem['total_recog'] - dataitem['decom_year']
        totales['pend_total'] += dataitem['pend_total']
        ''' casco por produccion '''
        dataitem['casco_x_prod'] = dataitem['pend_total'] - dataitem['total_por_recog']
        totales['casco_x_prod'] += dataitem['casco_x_prod']
        
        listtemp.append(dataitem)
        dataprov[provitem.descripcion_provincia] = listtemp
        
    aux =[]
    aux.append(totales) 
    nuevodata['Total'] = aux
    return dataprov,nuevodata        


def get_conci_x_org_prov(desde,hasta,prov,org):
    curs = connection.cursor()
    callproc_params = [desde, hasta, prov, org]
    curs.callproc('conciliacion_x_prov', callproc_params)
    while True:
        
        result = curs.fetchmany()
        if not result:
            break
        yield result 
       
@login_required
def formconcixcliente(request):
    if not request.user.has_perm('comercial.oferta'):
        return render_to_response("denegado.html",locals(),context_instance = RequestContext(request))
    mesg = []
    queryset=[]
    filtro=[]
    a=1
    if request.method == 'POST':
        form = Fformconcixcliente(request.POST)
        if form.is_valid():
            envia=False
            if request.POST.__contains__('submit3'):
                envia=True
                cliente=form.cleaned_data['cliente']
                correo=cliente.email
                if correo.__len__()==0:
                    mesg=mesg+['Este cliente no tiene correo']
                    return render_to_response("report/formconciliacionxcliente.html",{'form':form,'title':'Conciliación con las Entidades', 'form_name':'Reportes',
                                                                                              'form_description':'Conciliación con los clientes', 'controlador':'Reportes',
                                                                                              'accion':formbalacvsrecap,"error2":mesg,'email':1},context_instance = RequestContext(request))
                try:
                    querySet = Config_SMTPEmail.objects.get()
                except Exception, e:
                    mesg=mesg+['No está configurado el correo SMTP']
                    return render_to_response("report/formconciliacionxcliente.html",{'form':form,'title':'Conciliación con las Entidades', 'form_name':'Reportes',
                                                                                              'form_description':'Conciliación con los clientes', 'controlador':'Reportes',
                                                                                              'accion':formbalacvsrecap,"error2":mesg,'email':1},context_instance = RequestContext(request))
                servidor=querySet.servidor
                correo_envia=querySet.correo
                puerto = querySet.puerto
                ssl = querySet.ssl
                try:
                    contrasena = base64.b64decode(querySet.contrasena)
                except Exception, e:
                    mesg=mesg+['Revise la contraseña en la configuración del Correo SMTP']
                    return render_to_response("report/formconciliacionxcliente.html",{'form':form,'title':'Conciliación con las Entidades', 'form_name':'Reportes',
                                                                                              'form_description':'Conciliación con los clientes', 'controlador':'Reportes',
                                                                                              'accion':formbalacvsrecap,"error2":mesg,'email':1},context_instance = RequestContext(request))
            desde  = form.cleaned_data['desde']
            hasta  = form.cleaned_data['hasta']
            client = form.cleaned_data['cliente']
            client2 = client.id
            empresa = client.nombre
            contrato = client.clientecontrato_set.filter(cerrado = False)
            filtro.append({'desde':desde,'hasta':hasta,'empresa':empresa})
            plan=0
            for cont in contrato:
                plan = cont.contrato.get_plan_contratado(desde.year)
             
            resul = concixcliente(request, desde, hasta, client2)
            deuda = resul['almc'] - resul['facturado'] - resul['inservible'] - resul['decomisado']
            queryset.append({'plan':plan,'inv_ini':a,'entregados':resul['almc'],'deuda':deuda,'inservible':resul['inservible'],'facturado':resul['facturado'],
                             'decomisado':resul['decomisado'],'terminados':resul['almpt']})
            if not request.POST.__contains__('submit2') and not request.POST.__contains__('submit3'):
                return render_to_response("report/conciliacionxcliente.html",locals(),context_instance = RequestContext(request))
            else:
                if queryset.__len__():    
                    pdf_file_name=os.path.join(comerciax.settings.ADMIN_MEDIA_PDF,"Conciliacion con la Entidad.pdf")
                    if report_class.Reportes.GenerarRep(report_class.Reportes() , queryset, "concil_client",pdf_file_name,filtro)==0:
                        form = Fformconcixcliente()
                        return render_to_response("report/formconciliacionxcliente.html",{'form':form,'title':'Conciliación con las Entidades', 'form_name':'Reportes',
                                                                                          'form_description':'Conciliación con los clientes', 'controlador':'Reportes',
                                                                                          'accion':formbalacvsrecap,"error2":mesg,'email':1},context_instance = RequestContext(request))               
                    else:
                        input = PdfFileReader(file(pdf_file_name,"rb"))
                        output = PdfFileWriter()
                        for page in input.pages:
                            output.addPage(page)
                        buffer = StringIO.StringIO()
                        output.write(buffer)
                        response = HttpResponse(mimetype='application/pdf')
                        file_namesitio='%s'%(pdf_file_name)
                        response['Content-Disposition'] = 'attachment; filename=%s'%(pdf_file_name)
                        response.write(buffer.getvalue())
                        if envia:
                            import smtplib
                            from email.mime.application import MIMEApplication
                            from django.core.mail.message import EmailMessage
                            try:
                                message = EmailMessage(subject='Conciliacion con la Entidad',body='Enviado por '+request.user.first_name+' '+request.user.last_name, from_email=correo_envia, to=[correo])
                                part = MIMEApplication(open(file_namesitio,"rb").read())
                                part.add_header('Content-Disposition', 'attachment', filename="Conciliacion con la Entidad.pdf")
                                message.attach(part)
                                if ssl==True:
                                    smtp = smtplib.SMTP_SSL(host=servidor,port=puerto)
                                else:
                                    smtp = smtplib.SMTP(servidor)
                                smtp.ehlo()
                                smtp.login(correo_envia,contrasena)
                                smtp.sendmail(correo_envia,[correo],message.message().as_string())
                                smtp.close()
                                return response        
                            except Exception, e:
                                mesg=mesg+['Error de conexión. Revise la configuración del Correo SMTP']
                                return render_to_response("report/formconciliacionxcliente.html",{'form':form,'title':'Conciliación con las Entidades', 'form_name':'Reportes',
                                                                                          'form_description':'Conciliación con los clientes', 'controlador':'Reportes',
                                                                                          'accion':formbalacvsrecap,"error2":mesg,'email':1},context_instance = RequestContext(request))
                        return response
    else:
        form = Fformconcixcliente()
        return render_to_response("report/formconciliacionxcliente.html",{'form':form,'title':'Conciliación con las Entidades', 'form_name':'Reportes','form_description':'Conciliación con los clientes','controlador':'Reportes','accion':formbalacvsrecap
                                ,"error2":mesg,'email':1},context_instance = RequestContext(request))

@login_required
@transaction.commit_on_success
def concixcliente(request,desde,hasta,client):
    if not request.user.has_perm('comercial.oferta'):
        return render_to_response("denegado.html",locals(),context_instance = RequestContext(request))
    
    val = get_conciliacion_x_cliente(desde, hasta, client)
    data = {'almc':0,
            'inservible':0,
            'produccion':0,
            'almpt':0,
            'facturado':0,
            'decomisado':0,}
    
    for ase in val:
        if ase[0][1] == 'Casco':
            data['almc'] = ase[0][0]
        if ase[0][1] == 'DIP':
            data['inservible'] = ase[0][0]
        if ase[0][1] == 'Produccion':
            data['produccion'] = ase[0][0]
        if ase[0][1] == 'PT':
            data['almpt'] = ase[0][0]
        if ase[0][1] == 'DC':
            data['decomisado'] = ase[0][0]
    factu=query_to_dicts("""
                      SELECT 
                          
                          count(casco_casco.estado_actual) as canti
                          
                        FROM
                          casco_casco
                          FULL OUTER JOIN casco_detallerc ON (casco_casco.id_casco = casco_detallerc.casco_id)
                          LEFT OUTER JOIN casco_recepcioncliente ON (casco_detallerc.rc_id = casco_recepcioncliente.doc_recepcioncliente_id)
                          LEFT OUTER JOIN admincomerciax_cliente ON (casco_recepcioncliente.cliente_id = admincomerciax_cliente.id)
                          LEFT OUTER JOIN casco_doc ON (casco_recepcioncliente.doc_recepcioncliente_id = casco_doc.id_doc)
                        where   estado_actual='Factura' and venta=False and id=%s and casco_doc.fecha_doc >=%s AND
                                casco_doc.fecha_doc <= %s
                        """,client,desde,hasta)
    fac=0
    for a1 in factu:
    	fac=a1['canti']
    data['facturado'] = fac
    data['almpt']= data['almpt']-data['decomisado']
    return data        


def get_conciliacion_x_cliente(desde,hasta,client):
    curs = connection.cursor()
    callproc_params = [desde, hasta, client]
    curs.callproc('consiliacion', callproc_params)
    while True:
        
        result = curs.fetchmany()
        if not result:
            break
        yield result 
    
@login_required
@transaction.commit_on_success
def invptxorgedad(request):
    if not request.user.has_perm('comercial.oferta'):
        return render_to_response("denegado.html",locals(),context_instance = RequestContext(request))
    
    data = query_to_dicts("""
    SELECT
        *
    FROM
        invprodtxorg
    """)
    
    totalmayor = 0
    totalmenor = 0
    
    datos=[]
    for item in data:
        dicc={'org':item['siglas_organismo'],
           'mayor':item['mayor'],
           'menor':item['menor']}
        datos.append(dicc)
        totalmayor += item['mayor']
        totalmenor += item['menor']
    
    return render_to_response("report/invprodt_x_orgedad.html",locals(),context_instance = RequestContext(request))  

@login_required
def formorgfarmin(request):
    if not request.user.has_perm('comercial.oferta'):
        return render_to_response("denegado.html",locals(),context_instance = RequestContext(request))
    mesg = []
    if request.method == 'POST':
        form = Fformorgfarmin(request.POST)
        if form.is_valid():
            mess  = form.cleaned_data['mes']
            mes = utils.Meses.meses_name[int(mess)]
            years = form.cleaned_data['year']
            org = form.cleaned_data['organismo']
            orgs = []
            for item in org:
                orgs.append(item.__str__())
            resul = recapfarmin(request, mess, years, orgs)
            cantorg = orgs.__len__()
            
         
            if request.POST.__contains__('submit2'): 
                dic=[]
                a=[]  
                keys = resul.keys()
                k1=0
                for item in keys:
                    a=resul[item]                
                    for v in range(len(a)): 
                        if a[v].has_key('totalcup')==False:                                     
                            a[v]['organismo']=keys[k1]
                            dic.append(a[v])
                    k1+=1
                
                if dic.__len__():  
                    pdf_file_name=os.path.join(comerciax.settings.ADMIN_MEDIA_PDF,"Servicio de Recape a Organismos.pdf")
                    filtro=['Del mes de '+mes+ ' del '+str(years)]
                    if report_class.Reportes.GenerarRep(report_class.Reportes() , dic, "rec_organismos",pdf_file_name,filtro)==0:
                        mesg.append('Debe cerrar el fichero Servicio de Recape a Organismos.pdf')
                        return render_to_response("report/formrecapxorgindex.html",{'form':form,'title':'Servicios de Recape', 'form_name':'Reportes','form_description':'Serivicios de recape a Organismos','controlador':'Reportes','accion':formbalacvsrecap
                            ,"error2":mesg,},context_instance = RequestContext(request))
                    else:
                        input = PdfFileReader(file(pdf_file_name,"rb"))
                        output = PdfFileWriter()
                        for page in input.pages:
                            output.addPage(page)
                        buffer = StringIO.StringIO()
                        output.write(buffer)
                        response = HttpResponse(mimetype='application/pdf')
                        response['Content-Disposition'] = 'attachment; filename=%s'%(pdf_file_name)
                        response.write(buffer.getvalue())
                        return response                        
                    form = Fformorgfarmin()
                    return render_to_response("report/formrecapxorgindex.html",{'form':form,'title':'Servicios de Recape', 'form_name':'Reportes','form_description':'Serivicios de recape a Organismos','controlador':'Reportes','accion':formbalacvsrecap
                                        ,"error2":mesg,},context_instance = RequestContext(request))   
                else:
                    mesg.append('No existen Datos')
                    return render_to_response("report/formrecapxorgindex.html",{'form':form,'title':'Servicios de Recape', 'form_name':'Reportes','form_description':'Serivicios de recape a Organismos','controlador':'Reportes','accion':formbalacvsrecap
                            ,"error2":mesg,},context_instance = RequestContext(request))
            
            else:
                keys = resul.keys()
                for item in keys:
                    a = resul[item]
                return render_to_response("report/servicio_recape_org.html",locals(),context_instance = RequestContext(request))
        
    else:
        form = Fformorgfarmin()
        return render_to_response("report/formrecapxorgindex.html",{'form':form,'title':'Servicios de Recape', 'form_name':'Reportes','form_description':'Serivicios de recape a Organismos','controlador':'Reportes','accion':formbalacvsrecap
                                ,"error2":mesg,},context_instance = RequestContext(request))

@login_required
@transaction.commit_on_success
def recapfarmin(request,mes,year,orgs):
    if not request.user.has_perm('comercial.oferta'):
        return render_to_response("denegado.html",locals(),context_instance = RequestContext(request))
    
    mesaux = mes #9
    yearaux = year #2011
    data = {}
    l = []
    for orgitem in orgs:
        name = orgitem.__str__() 
        data[name] = l
         
    list_Organismo = orgs #['SIME','MINFAR','MININT']
    '''
    - todas las facturas de ese mes y ese year
    - no esten canceladas
    - esten confirmadas
    '''
    misfact = Facturas.objects.filter(doc_factura__fecha_doc__month = mesaux,
                                      doc_factura__fecha_doc__year = yearaux,
                                      cancelada=False,
                                      cliente__organismo__siglas_organismo__in = list_Organismo).order_by('admincomerciax_organismo.siglas_organismo')
    org_guia = ""
    list_data = []
    totalcuc = 0
    totalcup = 0
    incluir = True
    for fact in misfact:
        '''
        DICCIONARIO resultante
        {
         'Org1' : [ {cod,nro,cliente},[cod,nro,cliente],[cod,nro,cliente] ]',
         'Org2' : [ {cod,nro,cliente},[cod,nro,cliente],[cod,nro,cliente] ]',
         'Org3' : [ {cod,nro,cliente},[cod,nro,cliente],[cod,nro,cliente] ]',
        }
        - chequear que la factura este confirmada
        - agrupar las facturas segun cliente
        - agrupar segun organismo
        - sumar todas las facturas para cada organismo
        '''
        
        #comprobar si la factura esta confirmada
        
        if fact.get_confirmada() == 'S':
            #crear lista
            list_aux = {'codigo':fact.cliente.codigo,
                        'nro':fact.factura_nro,
                        'cliente':fact.cliente.nombre,
                        'cantidad':fact.cantidad_casco(),
                        'cuc':fact.get_importecuc(1),
                        'cup':fact.get_importecup(1)}
            
            if org_guia == fact.cliente.organismo:
                totalcuc += list_aux['cuc']
                totalcup += list_aux['cup'] 
                list_data.append(list_aux)
                incluir = True
            elif org_guia.__str__().__len__() == 0:
                totalcuc += list_aux['cuc']
                totalcup += list_aux['cup']
                org_guia = fact.cliente.organismo
                list_data.append(list_aux)
            else:
                incluir = False
                #creo el diccionario
                list_total = {'totalcuc':totalcuc,'totalcup':totalcup}
                list_data.append(list_total)
                
                data[org_guia.__str__()] = list_data
                org_guia = fact.cliente.organismo
                list_data = []
                list_data.append(list_aux)
                #inicializar totales
                totalcuc = 0
                totalcup = 0
                
        a = "asas"
    #fin del ciclo
    if incluir:
        list_total = {'totalcuc':totalcuc,'totalcup':totalcup}
        list_data.append(list_total)
        
    data[org_guia.__str__()] = list_data    
    return data        

@login_required
@transaction.commit_on_success
def cerrarmescomerc(request,mes,year):
    year1=int(year)
    mes1=Meses.meses_no[mes]
    
#    resultado1=query_to_dicts("""INSERT INTO comercial_invcliente
#                                 (year,mes,cliente_id,cantidad)
#                                 (SELECT 
#                                  %s as year, %s as mes,
#                                  casco_recepcioncliente.cliente_id,
#                                  count(casco_recepcioncliente.cliente_id) as cantidad
#                               FROM 
#                                  casco_casco
#                               INNER JOIN public.casco_detallerc ON casco_detallerc.casco_id = casco_casco.id_casco
#                               INNER JOIN   public.casco_recepcioncliente ON casco_detallerc.rc_id = casco_recepcioncliente.doc_recepcioncliente_id
#                              WHERE casco_casco.decomisado = False AND 
#                              casco_casco.estado_actual in ('Casco','Produccion','PT','Transferencia','DIP','DVP','ER','REE')
#                              group by casco_recepcioncliente.cliente_id
#                              order by casco_recepcioncliente.cliente_id)""",year1,mes1)
    resultado1=query_to_dicts("""
                                 SELECT 
                                  casco_recepcioncliente.cliente_id,
                                  count(casco_recepcioncliente.cliente_id) as cantidad
                               FROM 
                                  casco_casco
                               INNER JOIN public.casco_detallerc ON casco_detallerc.casco_id = casco_casco.id_casco
                               INNER JOIN   public.casco_recepcioncliente ON casco_detallerc.rc_id = casco_recepcioncliente.doc_recepcioncliente_id
                              WHERE casco_casco.estado_actual in ('Casco','Produccion','PT','Transferencia','DIP','DVP','ER','REE')
                              group by casco_recepcioncliente.cliente_id
                              order by casco_recepcioncliente.cliente_id""")
    for datos in resultado1:
        try:
            invcli=InvCliente()
            invcli.year=year1
            invcli.mes=mes1
            invcli.cliente=Cliente.objects.get(pk=datos['cliente_id'])
            invcli.cantidad=datos['cantidad']
            invcli.save()
            Fechacierre.objects.filter(almacen='cm').update(mes=mes1,year=year1)
            
        except Exception, e:
            transaction.rollback()
        else:
            transaction.commit() 
        
        
    try:
        if mes1==12:
            nume=NumeroDoc.objects.get()
            nume.nro_factura=0
            nume.nro_oferta=0
            nume.nro_facturapart=0
            nume.nro_facturaext=0
            nume.save()
    except Exception, e:
        transaction.rollback()
    else:
        transaction.commit()
    return HttpResponseRedirect('/comerciax/index')
        
@login_required
@transaction.commit_on_success
def cerrarmes(request):
    
    if not request.user.has_perm('comercial.invcliente'):
        return render_to_response("denegado.html",locals(),context_instance = RequestContext(request))
    
    fechacierre = Fechacierre.objects.filter(almacen='cm').all()
    ultimo_mes_anyo = fechacierre[0]
    messes = ultimo_mes_anyo.mes
    years = ultimo_mes_anyo.year
    if messes == 12:
        newmes_=1
        newmes =  Meses.meses_name[1]
        newyear =  ultimo_mes_anyo.year + 1 
    else:
        newmes_=messes+1
        newmes =  Meses.meses_name[ultimo_mes_anyo.mes + 1]
        newyear =  ultimo_mes_anyo.year
    
    cerrado = True
    mensage=""
    mesage=0
    cierre = Fechacierre.objects.all()
    for cie in cierre:
        if cie.mes != Meses.meses_no[newmes] and cie.almacen != 'cm':
            mesage = 1
            mensage += "El " + Estados.siglas_alm[cie.almacen] + " no ha cerrado el mes."+ "\n"
    
    canti_no=Facturas.objects.select_related().filter(confirmar=False,doc_factura__fecha_doc__month = newmes_,
                                      doc_factura__fecha_doc__year = years).count()
    if canti_no!=0:
        mesage = 1
        mensage += "Existen facturas a Clientes sin Confirmar. \n"
    
    canti_no=FacturasParticular.objects.select_related().filter(confirmar=False,doc_factura__fecha_doc__month = newmes_,
                                      doc_factura__fecha_doc__year = newyear).count()
    if canti_no!=0:
        mesage = 1
        mensage += "Existen facturas a Particulares sin Confirmar. \n"

    canti_no = FacturasServicios.objects.select_related().filter(confirmar=False, doc_factura__fecha_doc__month=newmes_,
                                                        doc_factura__fecha_doc__year=years).count()

    if canti_no!=0:
        mesage = 1
        mensage += "Existen servicios a clientes sin Confirmar. \n"
    
    if mesage==1:
        mensage +="\n\n No se puede realizar el cierre en Comercial."
    
    return render_to_response("comercial/cerrarmes.html",locals(),context_instance = RequestContext(request))

@login_required
@transaction.commit_on_success
#Este el cierre de mes de comercial primero que se hizo
def cerrarmes1(request):
    
    if not request.user.has_perm('comercial.invcliente'):
        return render_to_response("denegado.html",locals(),context_instance = RequestContext(request))
    
    fechacierre = Fechacierre.objects.filter(almacen='cm').all()
    ultimo_mes_anyo = fechacierre[0]
    messes = ultimo_mes_anyo.mes
    years = ultimo_mes_anyo.year
    if messes == 12:
        newmes_=1
        newmes =  Meses.meses_name[1]
        newyear =  ultimo_mes_anyo.year + 1 
    else:
        newmes_=messes+1
        newmes =  Meses.meses_name[ultimo_mes_anyo.mes + 1]
        newyear =  ultimo_mes_anyo.year
    
    cerrado = True
    mesg = []
    cierre = Fechacierre.objects.all()
    for cie in cierre:
        if cie.mes != Meses.meses_no[newmes] and cie.almacen != 'cm':
            cerrado = False
            mensaje = "El " + Estados.siglas_alm[cie.almacen] + " no ha cerrado el mes"
            mesg.append(mensaje)
    
    
    canti_no=Facturas.objects.select_related().filter(confirmar=False,doc_factura__fecha_doc__month = newmes_,
                                      doc_factura__fecha_doc__year = years).count()
    if canti_no!=0:
        cerrado = False
        mensaje = "Existen facturas a Clientes sin Confirmar2 "
        mesg.append(mensaje)
        
    
    canti_no=FacturasParticular.objects.select_related().filter(confirmar=False,doc_factura__fecha_doc__month = newmes_,
                                      doc_factura__fecha_doc__year = newyear).count()
    if canti_no!=0:
        cerrado = False
        mensaje = "Existen facturas a Particulares sin Confirmar " 
        mesg.append(mensaje)

    canti_no = FacturasServicios.objects.select_related().filter(confirmar=False, doc_factura__fecha_doc__month=newmes_,
                                                                 doc_factura__fecha_doc__year=years).count()

    if canti_no != 0:
        mesage = 1
        mensage += "Existen servicios a clientes sin Confirmar. \n"
    
    '''
    cierre = Fechacierre.objects.filter(mes=Meses.meses_no[newmes], year=newyear).all()
    if cierre.__len__() <= 1 :
        cerrado = False
        mensaje = "Los almacenes de Casco, Producción y Producción terminada no se han cerrado"
        mesg.append(mensaje)
    else:    
        for cie in cierre:
            if cie.mes != Meses.meses_no[newmes] and cie.almacen != 'cm':
                cerrado = False
                mensaje = "El almacen " + Estados.siglas_alm[cie.almacen] + " no ha cerrado el mes"
                mesg.append(mensaje) 
    '''
            
    if request.method == 'POST':
        form = FCerrarmes(request.POST)
        if form.is_valid():
            mesf = form.cleaned_data['mes']
            cerrarf = form.data['cerrar']
            yearf = form.cleaned_data['year']
            
            '''
                tengo que comprobar que esten cerrado los almacenes en el mes que se paso por parametro
                 1 - Balance Casco vs Recape 
            ''' 
            if cerrarf == "True":
                mes_inicio=12 if Meses.meses_no[mesf]==1 else Meses.meses_no[mesf]-1
                year_inicio = int(yearf)-1 if Meses.meses_no[mesf]==1 else int(yearf)
                bal_casco_vs_recap = gen_balacvsrecap(request,mes_inicio,year_inicio)
                if bal_casco_vs_recap.__len__() > 0:
                    try: 
                        mesadd = Meses.meses_no[mesf]
                        totales = { "Total":"Total",
                                    "tinvinicial":0,
                                    "tcasco":0,
                                    "ter":0,
                                    "tree":0,
                                    "tdip":0,
                                    "tecr":0,
                                    "tfact":0,
                                    "ttranf":0,
                                    "tbalance":0,
                                    "tinvfinal":0,
                                    "tdif":0}
                        for bal in bal_casco_vs_recap:
                            balance = Balancecascovsrecap()
                            balance.year = yearf
                            balance.mes = mesadd
                            balance.medida = bal['medida']
                            balance.invini = bal['invinicial']
                            balance.casco = bal['casco']
                            balance.er = bal['er']
                            balance.ree = bal['ree']
                            balance.dip = bal['dip']
                            balance.ecr = bal['ecr']
                            balance.fact = bal['fact']
                            balance.tranf = bal['tranf']
                            balance.balance = bal['balance']
                            balance.invf = bal['invfinal']
                            balance.dif = bal['dif']
                            
                            balance.save()
                            totales['tinvinicial'] = totales['tinvinicial'] + bal['invinicial']
                            totales['tcasco'] = totales['tcasco'] + bal['casco']
                            totales['ter'] = totales['ter'] + bal['er']
                            totales['tree'] = totales['tree'] + bal['ree']
                            totales['tdip'] = totales['tdip'] + bal['dip']
                            totales['tecr'] = totales['tecr'] + bal['ecr']
                            totales['ttranf'] = totales['ttranf'] + bal['tranf']
                            totales['tfact'] = totales['tfact'] + bal['fact']
                            totales['tbalance'] = totales['tbalance'] + bal['balance']
                            totales['tinvfinal'] = totales['tinvfinal'] + bal['invfinal']
                            totales['tdif'] = totales['tdif'] + bal['dif']
                            
                        Fechacierre.objects.filter(almacen='cm').update(year=yearf,mes=newmes_)
                              
                    except Exception, e:
                        transaction.rollback()
                        exc_info = e.__str__()
                        mesg.append("Error Fatal")
                        
                        form2 = FCerrarmes(initial={"mes":newmes,"year":newyear})
                        return render_to_response("comercial/cerrarmes.html",{'form':form2,'title':'Cierre de mes', 'form_name':'Cerrar mes','form_description':'Cerrar el mes','controlador':'Cierre de mes','accion':cerrarmes1,                                                              
                                   "error2":mesg,"cerrar":cerrado},context_instance = RequestContext(request))
                    
                return HttpResponseRedirect('/comerciax/index')
            else:
                form2 = FCerrarmes(initial={"mes":newmes,"year":newyear})
                return render_to_response("comercial/cerrarmes.html",{'form':form2,'title':'Cierre de mes', 'form_name':'Cerrar mes','form_description':'Cerrar el mes','controlador':'Cierre de mes','accion':cerrarmes1,                                                              
                                   "error2":mesg,"cerrar":cerrado},context_instance = RequestContext(request))
    else:
        form2 = FCerrarmes(initial={"mes":newmes,"year":newyear})
        return render_to_response("comercial/cerrarmes.html",{'form':form2,'title':'Cierre de mes', 'form_name':'Cerrar mes','form_description':'Cerrar el mes','controlador':'Cierre de mes','accion':cerrarmes1,                                                              
                                   "error2":mesg,"cerrar":cerrado},context_instance = RequestContext(request))

def gen_balacvsrecap(request,mescierre,yearcierre):
       
    #inventario inicial se coge de la Vista "invinicial" pasandole el mes y año como parametro
    invinicial = query_to_dicts("""
    SELECT
        *
    FROM
        invinicial
    Where mes = %s and year = %s
    """,mescierre,yearcierre)#ultimo_mes_anyo.mes,ultimo_mes_anyo.year)
    
    #obtener todos los cascos que estan en los estados 
    #Casco, ER, REE, DIP, ECR, Factura, Transferencia
    in_out = query_to_dicts("""
    SELECT
        *
    FROM
        balcascovsrecapaux
    """)
    resulfinal = [] 
    lista = []
    for el in in_out:
            lista.append(el)
    resultado = []
    totales = { "tinvinicial":0,
                "tcasco":0,
                "ter":0,
                "tree":0,
                "tdip":0,
                "tecr":0,
                "tfact":0,
                "ttranf":0,
                "tbalance":0,
                "tinvfinal":0,
                "tdif":0}
    for elemento in invinicial:
        registro = {"medida":"",
                "invinicial":0,
                "casco":0,
                "er":0,
                "ree":0,
                "dip":0,
                "ecr":0,
                "fact":0,
                "tranf":0,
                "balance":0,
                "invfinal":0,
                "dif":0}
        
        registro['invinicial'] = elemento['inicialcasco']
        mimedida = Producto.objects.get(pk = elemento['medida_id'])
        registro['medida'] = mimedida.descripcion
        registro['balance'] = elemento['inicialcasco']
        registro['invfinal'] = elemento['inicialcasco']        
        totales['tinvinicial'] = totales['tinvinicial'] + elemento['inicialcasco']  
        
        for inout in lista:
            if inout['medida'] == mimedida.descripcion:
                #elemento['medida_id']:
                registro['casco'] = inout['Casco']
                registro['er'] = inout['ER']
                registro['ree'] = inout['REE']
                registro['dip'] = inout['DIP']
                registro['ecr'] = inout['ECR']
                registro['tranf'] = inout['Transferencia']
                registro['fact'] = inout['Facturado']
                registro['balance'] = elemento['inicialcasco'] + inout['Casco'] + inout['ER'] + inout['REE'] + inout['DIP'] - inout['Facturado'] - inout['Transferencia'] - inout['ECR']
                
                totales['tcasco'] = totales['tcasco'] + registro['casco']
                totales['ter'] = totales['ter'] + registro['er']
                totales['tree'] = totales['tree'] + registro['ree']
                totales['tdip'] = totales['tdip'] + registro['dip']
                totales['tecr'] = totales['tecr'] + registro['ecr']
                totales['ttranf'] = totales['ttranf'] + registro['tranf']
                totales['tfact'] = totales['tfact'] + registro['fact']
                totales['tbalance'] = totales['tbalance'] + registro['balance']
                break
            
                
        resultado.append(registro)
    #resulfinal.append(resultado)
    #tengo que comprobar ahora que no se me queden medidas de las entradas-salidas sin analizar
    for inout2 in lista:
        encontrado = False
        
        for subitem in resultado:
            if subitem['medida'] == inout2['medida']:
                encontrado = True
                break
                
        if not encontrado:                
            registro = {"medida":"",
            "invinicial":0,
            "casco":0,
            "er":0,
            "ree":0,
            "dip":0,
            "ecr":0,
            "fact":0,
            "tranf":0,
            "balance":0,
            "invfinal":0,
            "dif":0}                
            registro['medida'] = inout2['medida']
            registro['casco'] = inout2['Casco']
            registro['er'] = inout2['ER']
            registro['ree'] = inout2['REE']
            registro['dip'] = inout2['DIP']
            registro['ecr'] = inout2['ECR']
            registro['tranf'] = inout2['Transferencia']
            registro['fact'] = inout2['Facturado']
            registro['balance'] = inout2['Casco'] + inout2['ER'] + inout2['REE'] + inout2['DIP'] - inout2['Facturado'] - inout2['Transferencia'] - inout2['ECR']
            
            totales['tcasco'] = totales['tcasco'] + registro['casco']
            totales['ter'] = totales['ter'] + registro['er']
            totales['tree'] = totales['tree'] + registro['ree']
            totales['tdip'] = totales['tdip'] + registro['dip']
            totales['tecr'] = totales['tecr'] + registro['ecr']
            totales['ttranf'] = totales['ttranf'] + registro['tranf']
            totales['tfact'] = totales['tfact'] + registro['fact']
            totales['tbalance'] = totales['tbalance'] + registro['balance']
            
            resultado.append(registro)
                  
    return resultado

'''
    Este es el reporte que se muestra cuando se da clic en el enlace que aparece en el formulario de
    cierre de mes del area comercial.
    cuando se presiona el boton del formulario, se guardan los dtos en la  BD para poder acceder a ellos desde el enlace que parace en el menu
    
'''

def formbalacvsrecap(request):
    if not request.user.has_perm('casco.cierremes'):
        return render_to_response("denegado.html",locals(),context_instance = RequestContext(request))
    mesg = []
    queryset=[]
    if request.method == 'POST':
        form = FindexBalanceCasco(request.POST)
        if form.is_valid():
            mess  = form.cleaned_data['mes']
            years = form.cleaned_data['year']
            mes=Meses.meses_name[int(mess)]
            anno=years
            resultado = Balancecascovsrecap.objects.filter(mes=mess, year=years ).all()
            totales_=query_to_dicts("""
            SELECT Sum(casco_balancecascovsrecap.invini) AS tinvinicial,    
                   Sum(casco_balancecascovsrecap.casco) AS tcasco, 
                   Sum(casco_balancecascovsrecap.er) AS ter, 
                   Sum(casco_balancecascovsrecap.ree) AS tree, 
                   Sum(casco_balancecascovsrecap.ecr) AS tecr, 
                   Sum(casco_balancecascovsrecap.dip) AS tdip, 
                   Sum(casco_balancecascovsrecap.fact) AS tfact, 
                   Sum(casco_balancecascovsrecap.tranf) AS ttranf, 
                   Sum(casco_balancecascovsrecap.balance) AS tbalance, 
                   Sum(casco_balancecascovsrecap.invf) AS tinvfinal, 
                   Sum(casco_balancecascovsrecap.dif) AS tdif, 
                   casco_balancecascovsrecap.year, casco_balancecascovsrecap.mes
                FROM casco_balancecascovsrecap
                GROUP BY casco_balancecascovsrecap.year, casco_balancecascovsrecap.mes
                HAVING ((((casco_balancecascovsrecap.mes)=%s) and (casco_balancecascovsrecap.year)=%s));

            """,mess,years)
            totales = {
                        "tinvinicial":0,
                        "tcasco":0,
                        "ter":0,
                        "tree":0,
                        "tdip":0,
                        "tecr":0,
                        "tfact":0,
                        "ttranf":0,
                        "tbalance":0,
                        "tinvfinal":0,
                        "tdif":0}
            for total in totales_:
                totales['tinvinicial']=total['tinvinicial']
                totales['tcasco']=total['tcasco']
                totales['ter']=total['ter']
                totales['tree']=total['tree']
                totales['tdip']=total['tdip']
                totales['tecr']=total['tecr']
                totales['tfact']=total['tfact']
                totales['ttranf']=total['ttranf']
                totales['tbalance']=total['tbalance']
                totales['tinvfinal']=total['tinvfinal']
                totales['tdif']=total['tdif']
                
            if resultado.__len__() == 0:
                uno = int(mess)
                cadena = "no se ha cerrado el mes " + Meses.meses_name[uno] + " del " + years
                mesg = [cadena]
                form = FindexBalanceCasco()
                return render_to_response("form/form_add.html",{'form':form,'title':'Balance Casco vs Recape', 'form_name':'Reportes','form_description':'Balance de casco vs recape','controlador':'Reportes','accion':formbalacvsrecap
                                ,"error2":mesg,"reporte":1},context_instance = RequestContext(request))
            else:
                if not request.POST.__contains__('submit2'):
                    return render_to_response("report/balancecasco_vs_recape.html",locals(),context_instance = RequestContext(request))
                else:
                    for fila in resultado:
                        queryset.append({'medida':fila.medida,'invinicial':fila.invini,'casco':fila.casco,
                                         'dip':fila.dip,'er':fila.er,'ree':fila.ree,'ecr':fila.ecr,'fact':fila.fact,
                                         'tranf':fila.tranf,'balance':fila.balance,'invfinal':fila.invf,
                                         'dif':fila.dif})
                    pdf_file_name=os.path.join(comerciax.settings.ADMIN_MEDIA_PDF,"Conciliacion con los Clientes.pdf")
                    if report_class.Reportes.GenerarRep(report_class.Reportes() , queryset, "balanc_casc_recap",pdf_file_name,[])==0:
                        form = Fformconcixcliente()
                        return render_to_response("report/formconciliacionxcliente.html",{'form':form,'title':'Conciliación con las Entidades', 'form_name':'Reportes',
                                                                                          'form_description':'Conciliación con los clientes', 'controlador':'Reportes',
                                                                                          'accion':formbalacvsrecap,"error2":mesg,},context_instance = RequestContext(request))               
                    else:
                        input = PdfFileReader(file(pdf_file_name,"rb"))
                        output = PdfFileWriter()
                        for page in input.pages:
                            output.addPage(page)
                        buffer = StringIO.StringIO()
                        output.write(buffer)
                        response = HttpResponse(mimetype='application/pdf')
                        response['Content-Disposition'] = 'attachment; filename=%s'%(pdf_file_name)
                        response.write(buffer.getvalue())
                        return response
              
    else:
        form = FindexBalanceCasco()
        
        return render_to_response("form/form_add.html",{'es_add':'0','form':form,'title':'Balance Casco vs Recape', 'form_name':'Reportes','form_description':'Balance de casco vs recape','controlador':'Reportes','accion':formbalacvsrecap
                                ,"error2":mesg,"reporte":1},context_instance = RequestContext(request))
        

def balacvsrecap_sincierre(request, *error):
    if not request.user.has_perm('casco.invalmcasco'):
        return render_to_response("denegado.html",locals(),context_instance = RequestContext(request))
    l=[]
    if error.__len__() > 0:
        l=error[0]
    error2 = l
    
    fechacierre = Fechacierre.objects.filter(almacen='c').all()
    ultimo_mes_anyo = fechacierre[0]
    if ultimo_mes_anyo.mes == 1 :
        mmes = 12 
        anno = ultimo_mes_anyo.year - 1
    else :
        mmes = ultimo_mes_anyo.mes - 1
        anno = ultimo_mes_anyo.year
       
    #inventario inicial se coge de la Vista "invinicial" pasandole el mes y año como parametro
    invinicial = query_to_dicts("""
    SELECT
        *
    FROM
        invinicial
    Where mes = %s and year = %s
    """,mmes,anno)
    
    #obtener todos los cascos que estan en los estados 
    #Casco, ER, REE, DIP, ECR, Factura, Transferencia
    in_out = query_to_dicts("""
    SELECT
        *
    FROM
        balcascovsrecapaux
    """)
    resulfinal = [] 
    lista = []
    for el in in_out:
            lista.append(el)
    resultado = []
    totales = { "tinvinicial":0,
                "tcasco":0,
                "ter":0,
                "tree":0,
                "tdip":0,
                "tecr":0,
                "tfact":0,
                "ttranf":0,
                "tbalance":0,
                "tinvfinal":0,
                "tdif":0}
    for elemento in invinicial:
        registro = {"medida":"",
                "invinicial":0,
                "casco":0,
                "er":0,
                "ree":0,
                "dip":0,
                "ecr":0,
                "fact":0,
                "tranf":0,
                "balance":0,
                "invfinal":0,
                "dif":0}
        
        registro['invinicial'] = elemento['inicialcasco']
        mimedida = Producto.objects.get(pk = elemento['medida_id'])
        registro['medida'] = mimedida.descripcion
        registro['balance'] = elemento['inicialcasco']
        registro['invfinal'] = elemento['inicialcasco']
        
        totales['tinvinicial'] = totales['tinvinicial'] + elemento['inicialcasco']  
        
        for inout in lista:
            if inout['medida'] == mimedida.descripcion:
                #elemento['medida_id']:
                registro['casco'] = inout['Casco']
                registro['er'] = inout['ER']
                registro['ree'] = inout['REE']
                registro['dip'] = inout['DIP']
                registro['ecr'] = inout['ECR']
                registro['tranf'] = inout['Transferencia']
                registro['fact'] = inout['Facturado']
                registro['balance'] = elemento['inicialcasco'] + inout['Casco'] + inout['ER'] + inout['REE'] + inout['DIP'] - inout['Facturado'] - inout['Transferencia'] - inout['ECR']
                
                totales['tcasco'] = totales['tcasco'] + registro['casco']
                totales['ter'] = totales['ter'] + registro['er']
                totales['tree'] = totales['tree'] + registro['ree']
                totales['tdip'] = totales['tdip'] + registro['dip']
                totales['tecr'] = totales['tecr'] + registro['ecr']
                totales['ttranf'] = totales['ttranf'] + registro['tranf']
                totales['tfact'] = totales['tfact'] + registro['fact']
                totales['tbalance'] = totales['tbalance'] + registro['balance']
                break
            
                
        resultado.append(registro)
    #resulfinal.append(resultado)
    #tengo que comprobar ahora que no se me queden medidas de las entradas-salidas sin analizar
    for inout2 in lista:
        encontrado = False
        
        for subitem in resultado:
            if subitem['medida'] == inout2['medida']:
                encontrado = True
                break
                
        if not encontrado:                
            registro = {"medida":"",
            "invinicial":0,
            "casco":0,
            "er":0,
            "ree":0,
            "dip":0,
            "ecr":0,
            "fact":0,
            "tranf":0,
            "balance":0,
            "invfinal":0,
            "dif":0}                
            registro['medida'] = inout2['medida']
            registro['casco'] = inout2['Casco']
            registro['er'] = inout2['ER']
            registro['ree'] = inout2['REE']
            registro['dip'] = inout2['DIP']
            registro['ecr'] = inout2['ECR']
            registro['tranf'] = inout2['Transferencia']
            registro['fact'] = inout2['Facturado']
            registro['balance'] = inout2['Casco'] + inout2['ER'] + inout2['REE'] + inout2['DIP'] - inout2['Facturado'] - inout2['Transferencia'] - inout2['ECR']
            
            totales['tcasco'] = totales['tcasco'] + registro['casco']
            totales['ter'] = totales['ter'] + registro['er']
            totales['tree'] = totales['tree'] + registro['ree']
            totales['tdip'] = totales['tdip'] + registro['dip']
            totales['tecr'] = totales['tecr'] + registro['ecr']
            totales['ttranf'] = totales['ttranf'] + registro['tranf']
            totales['tfact'] = totales['tfact'] + registro['fact']
            totales['tbalance'] = totales['tbalance'] + registro['balance']
            
            resultado.append(registro)
                  
    mes=Meses.meses_name[mmes+1]
    return render_to_response("report/balancecasco_vs_recape.html",locals(),context_instance = RequestContext(request))


def rpt1(request):
    if not request.user.has_perm('comercial.oferta'):
        return render_to_response("denegado.html",locals(),context_instance = RequestContext(request))
    
    
    c = None
    l = []
    if request.method == 'POST':
        form = FRpt1(request.POST)
        if form.is_valid():
            org = Provincias.objects.get(pk = form.data['organismo'])
            desde = form.cleaned_data['desde']
            hasta = form.cleaned_data['hasta']
            
            return verRpt1(locals())
            #return HttpResponseRedirect('/comerciax/admincom/provincia/view/' + myprovincia.codigo_provincia.__str__())
    else:
        a ='s'
        #form = Provincia()
    uri="/comerciax/index" 
    return render_to_response("form/form_edit.html",{'tipocliente':'2','form':form,'title':'Rpt1', 'form_name':'Rpt1','form_description':'Criterio para mostra el reporte Rpt1','controlador':'Reportes Rpt1','accion':'rpt1',
                                                    'cancelbtn':uri},context_instance = RequestContext(request))

def verRpt1(request,org,desde,hasta):
    
    return 


#############################################################
#                              OFERTAS   AQUIIIIIII                   #
#############################################################
def veroferta(request,idoferta,haycup,haycuc,espdf):
    
    encabezados = []
    empresaobj1 = Empresa.objects.all()#filter(pk="8e7e4231-872f-4bff-8762-0810eeace12c")
    hay_cup=int(haycup)
    hay_cuc=int(haycuc)
    idoferta=idoferta
    espdf = int(espdf)
    for empresaobj in empresaobj1: 
        titular_name = empresaobj.nombre
        titular_dir = empresaobj.direccion
        titular_codigo = empresaobj.codigo
        titular_email = empresaobj.email
        titular_phone = empresaobj.telefono
        titular_fax = empresaobj.fax
        titular_cuenta_mn = empresaobj.cuenta_mn
        titular_cuenta_cuc = empresaobj.cuenta_usd
        titular_sucursal_mn = empresaobj.sucursal_mn.sucursal_descripcion
        titular_sucursal_cuc = empresaobj.sucursal_usd.sucursal_descripcion
    
    oferta = Oferta.objects.select_related().get(doc_oferta=idoferta)
    importecup=oferta.get_importecup
    importecuc=oferta.get_importecuc 
    importetotalcup=oferta.get_importetotalcup
    importecup_venta=oferta.get_importe_venta
    fecha_confeccionado=oferta.doc_oferta.fecha_operacion
    pk_user=User.objects.get(pk=request.user.id)
    vendedor=pk_user.first_name+" "+pk_user.last_name
    
    detallesOf = DetalleOferta.objects.select_related().filter(oferta=idoferta).values('oferta','precio_mn','precio_cuc','casco__producto_salida',\
                                                                            'casco__producto_salida__codigo','casco__producto_salida__descripcion',\
                                                                            'casco__producto_salida__um__descripcion')\
                                                                            .annotate(cantidad=Count('casco__producto_salida'))
                                                                            
    detallesOfVenta = DetalleOferta.objects.select_related().filter(oferta=idoferta,casco__venta=True,casco__decomisado=False).values('oferta','precio_casco','casco__producto_salida',\
                                                                            'casco__producto_salida__codigo','casco__producto_salida__descripcion',\
                                                                            'casco__producto_salida__um__descripcion')\
                                                                            .annotate(cantidad=Count('casco__producto_salida'))                                                                            
    hay_venta=0
    for a1 in range(detallesOf.__len__()):
        detallesOf[a1]['importecup']=detallesOf[a1]['precio_mn']*detallesOf[a1]['cantidad']
        detallesOf[a1]['importecup']=str(detallesOf[a1]['importecup'])
        detallesOf[a1]['precio_mn']=str(detallesOf[a1]['precio_mn'])
        detallesOf[a1]['importecuc']=detallesOf[a1]['precio_cuc']*detallesOf[a1]['cantidad']
        detallesOf[a1]['importecuc']=str(detallesOf[a1]['importecuc'])
        detallesOf[a1]['precio_cuc']=str(detallesOf[a1]['precio_cuc'])
        
    for a1 in range(detallesOfVenta.__len__()):
        hay_venta=1
        detallesOfVenta[a1]['importecup']=detallesOfVenta[a1]['precio_casco']*detallesOfVenta[a1]['cantidad']
        detallesOfVenta[a1]['importecup']=str(detallesOfVenta[a1]['importecup'])
        detallesOfVenta[a1]['precio_casco']=str(detallesOfVenta[a1]['precio_casco'])
   
    cliente = oferta.cliente
    cliente_codigo = cliente.codigo
    cliente_nombre = cliente.nombre
    cliente_dir = cliente.direccion
    cliente_phone = cliente.telefono
    cliente_email = cliente.email
    cliente_fax = cliente.fax
    
    contrato = ClienteContrato.objects.select_related().get(cliente=cliente.id, cerrado=False)
    
    contrato_sucursal_mn = contrato.contrato.sucursal_mn
    mn = ""
    cuc = ""
    if contrato_sucursal_mn:
        mn = contrato.contrato.sucursal_mn.sucursal_descripcion
    contrato_sucursal_cuc = contrato.contrato.sucursal_usd
    if contrato_sucursal_cuc:
        cuc= contrato.contrato.sucursal_usd.sucursal_descripcion
    
    contrato_cuenta_mn = contrato.contrato.cuenta_mn
    contrato_cuenta_cuc = contrato.contrato.cuenta_usd
    utils.backup()
    
    queryset = prepare_data_veroferta(detallesOf, detallesOfVenta)
    
    encabezados.append({'titular_name': titular_name, 'titular_dir':titular_dir, 'titular_codigo':titular_codigo,
                        'titular_email':titular_email, 'titular_phone':titular_phone, 'titular_fax':titular_fax, 
                        'titular_cuenta_mn':titular_cuenta_mn, 'titular_cuenta_cuc':titular_cuenta_cuc,
                         'titular_sucursal_mn':titular_sucursal_mn, 'titular_sucursal_cuc':titular_sucursal_cuc,
                          'fecha_confeccionado':fecha_confeccionado, 'pk_user':pk_user.get_full_name(), 'vendedor':vendedor,
                           'cliente':cliente ,'cliente_codigo':cliente_codigo, 'cliente_nombre':cliente_nombre,'cliente_dir':cliente_dir,
                            'cliente_phone': cliente_phone, 'cliente_email': cliente_email, 'cliente_fax':cliente_fax ,
                              'contrato' :contrato,'contrato_sucursal_mn' :mn ,
                               'contrato_sucursal_cuc' :cuc,'contrato_cuenta_mn' :contrato_cuenta_mn,
                                  'contrato_cuenta_cuc' :contrato_cuenta_cuc, 'hay_cup':hay_cup, 'hay_cuc': hay_cuc, 'no_oferta': oferta.oferta_nro})
    
    if espdf==1:
        error=[]
        if queryset.__len__():  
            envia=True
            #La validacion de la conf smtp ya se hace en verificaemail a traves de una url, o sea que aqui llega si no hay error en la configuracion
            querySet = Config_SMTPEmail.objects.get()
            servidor=querySet.servidor
            correo_envia=querySet.correo
            correo=cliente.email
            puerto = querySet.puerto
            ssl = querySet.ssl
            contrasena = base64.b64decode(querySet.contrasena)
            
            pdf_file_name=os.path.join(comerciax.settings.ADMIN_MEDIA_PDF,"Oferta.pdf") 
            if report_class.Reportes.Oferta(report_class.Reportes() , queryset, encabezados ,pdf_file_name)!=0:
                input = PdfFileReader(file(pdf_file_name,"rb"))
                output = PdfFileWriter()
                for page in input.pages:
                    output.addPage(page)
                buffer = StringIO.StringIO()
                output.write(buffer)
                response = HttpResponse(mimetype='application/pdf')
                response['Content-Disposition'] = 'attachment; filename=%s'%(pdf_file_name)
                response.write(buffer.getvalue())
                import smtplib
                from email.mime.application import MIMEApplication
                from django.core.mail.message import EmailMessage

                message = EmailMessage(subject='Oferta',body='Enviado por '+request.user.first_name+' '+request.user.last_name, from_email=correo_envia, to=[correo])
                file_namesitio='%s'%(pdf_file_name)
                part = MIMEApplication(open(file_namesitio,"rb").read())
                part.add_header('Content-Disposition', 'attachment', filename="Oferta.pdf")
                message.attach(part)
                if ssl==True:
                    smtp = smtplib.SMTP_SSL(host=servidor,port=puerto)
                else:
                    smtp = smtplib.SMTP(servidor)
                smtp.ehlo()
                smtp.login(correo_envia,contrasena)
                smtp.sendmail(correo_envia,[correo],message.message().as_string())
                smtp.close()
                return response         

    return render_to_response("report/oferta.html",locals(),context_instance = RequestContext(request))

def prepare_data_veroferta(detallesOf, detallesOfVenta):
    
    queryset = []
    subqueryset = []
    
    for a1 in range(detallesOf.__len__()):
        queryset.append({ 'oferta' : detallesOf[a1]['oferta'],'precio_mn': float(detallesOf[a1]['precio_mn']),'precio_cuc': float(detallesOf[a1]['precio_cuc']),\
                         'casco__producto_salida': detallesOf[a1]['casco__producto_salida'],\
                        'casco__producto_salida__codigo': detallesOf[a1]['casco__producto_salida__codigo'],'casco__producto_salida__descripcion': detallesOf[a1]['casco__producto_salida__descripcion'],\
                        'casco__producto_salida__um__descripcion': detallesOf[a1]['casco__producto_salida__um__descripcion'],\
                        'importecup' : float(detallesOf[a1]['importecup']), 'cantidad' : float(detallesOf[a1]['cantidad']),\
                        'importecuc' : float(detallesOf[a1]['importecuc']),\
                         'ofertaventa' : "",'preciocasco': "",\
                         'casco__producto_salidaventa': "",\
                        'casco__producto_salida__codigoventa': "",'casco__producto_salida__descripcionventa': "",\
                        'casco__producto_salida__um__descripcionventa': "",\
                        'importecupventa' : "", 'cantidadventa' : "", 'venta': ""})
        
    for a1 in range(detallesOfVenta.__len__()):
        queryset.append({ 'oferta' : detallesOfVenta[a1]['oferta'],'precio_mn': float(detallesOfVenta[a1]['precio_casco']),'precio_cuc': "",\
                         'casco__producto_salida': detallesOfVenta[a1]['casco__producto_salida'],\
                        'casco__producto_salida__codigo': detallesOfVenta[a1]['casco__producto_salida__codigo'],'casco__producto_salida__descripcion': detallesOfVenta[a1]['casco__producto_salida__descripcion'],\
                        'casco__producto_salida__um__descripcion': detallesOfVenta[a1]['casco__producto_salida__um__descripcion'],\
                        'importecup' : float(detallesOfVenta[a1]['importecup']), 'cantidad' : float(detallesOfVenta[a1]['cantidad']),\
                        'importecuc' : "",\
                         'ofertaventa' : detallesOfVenta[a1]['oferta'],'precio_casco': float(detallesOfVenta[a1]['precio_casco']),\
                         'casco__producto_salidaventa':detallesOfVenta[a1]['casco__producto_salida'],\
                        'casco__producto_salida__codigoventa':detallesOfVenta[a1]['casco__producto_salida__codigo'],'casco__producto_salida__descripcionventa':detallesOfVenta[a1]['casco__producto_salida__descripcion'],\
                        'casco__producto_salida__um__descripcionventa':detallesOfVenta[a1]['casco__producto_salida__um__descripcion'],\
                        'importecupventa' :float(detallesOfVenta[a1]['importecup']), 'cantidadventa' :float(detallesOfVenta[a1]['cantidad']), 'venta': "Venta de Cascos."})
        
    return queryset


@login_required
def get_ofer_list(request):
    #prepare the params
    try:
        fecha_desde=Fecha_Ver.objects.get()
    except Exception, e:
        fecha_desde=None
    if  fecha_desde == None:  
        querySet = Oferta.objects.select_related().all()
    else:
        querySet = Oferta.objects.select_related().filter(doc_oferta__fecha_doc__gte=fecha_desde.fecha)
    
    #querySet = querySet.filter(doc__fecha_doc__year=2010)
 
    columnIndexNameMap = {0: '-doc_oferta__fecha_doc',1: 'oferta_nro',2:'admincomerciax_cliente.nombre',3:'doc_oferta__fecha_doc',4:'oferta_tipo'}

    searchableColumns = ['oferta_nro','cliente__nombre','doc_oferta__fecha_doc']
    #path to template used to generate json
    jsonTemplatePath = 'comercial/json/json_oferta.txt'

    #call to generic function from utils
    return get_datatables_records(request, querySet, columnIndexNameMap, searchableColumns, jsonTemplatePath)
    

@login_required
def oferta_index(request):
    if not request.user.has_perm('comercial.oferta'):
        return render_to_response("denegado.html",locals(),context_instance = RequestContext(request))
    
    return render_to_response('comercial/ofertaindex.html',locals(),context_instance = RequestContext(request))

@login_required
@transaction.commit_on_success()
def oferta_add(request):
    if not request.user.has_perm('comercial.oferta'):
        return render_to_response("denegado.html",locals(),context_instance = RequestContext(request))
    
    nombre_form='Ofertas'
    descripcion_form='Realizar Oferta'
    titulo_form='Ofertas' 
    controlador_form='Ofertas'
    accion_form='/comerciax/comercial/oferta/add'
    cancelbtn_form='/comerciax/comercial/oferta/index'
    fecha_cierre=datetime.date.today().strftime("%d/%m/%Y")
    fecham=Cierre.objects.all()
    c=None
    l=[]
    for a in fecham:
        fecha_cierre=a.fechacierre.strftime("%d/%m/%Y")
    if request.method == 'POST':
        form = OfertaForm(request.POST)

        if form.is_valid():
            tipo=form.cleaned_data['tipo']
            obj_cliente = Cliente.objects.get(pk = form.data['cliente']) 
            try:
                tipoc=obj_cliente.get_contrato_tipo()
            except Exception, e:
                tipoc=None
            
            if tipoc==None:
                l=['Este cliente no tiene contrato por lo que no se puede realizar la oferta']
                return render_to_response('form/form_adddetalle.html',  {'tipocliente':'2','form': form, 'form_name':nombre_form,
                                                                         'form_description':descripcion_form,'accion':accion_form,
                                                                         'titulo':titulo_form,'controlador':controlador_form,
                                                                         'cancelbtn':cancelbtn_form,'fecha_minima':fecha_cierre,
                                                                         'error2':l},context_instance = RequestContext(request))
               
            if (tipoc==True) and (tipo=='A' or tipo=='O'):
                l=['Este cliente tiene contrato para venta el tipo de oferta seleccionada es incorrecto']
                return render_to_response('form/form_adddetalle.html',  {'tipocliente':'2','form': form, 'form_name':nombre_form,
                                                                         'form_description':descripcion_form,'accion':accion_form,
                                                                         'titulo':titulo_form,'controlador':controlador_form,
                                                                         'cancelbtn':cancelbtn_form,'fecha_minima':fecha_cierre,
                                                                         'error2':l},context_instance = RequestContext(request))
                  
            pk_user=User.objects.get(pk=request.user.id)
            
            ofer=Oferta()
            
            pk_doc=uuid4()
            obj_doc=Doc()
            
            obj_doc.id_doc=pk_doc
            obj_doc.tipo_doc='13'
            obj_doc.fecha_doc=form.cleaned_data['fecha']
            obj_doc.operador=pk_user
            obj_doc.fecha_operacion=datetime.date.today()
            obj_doc.observaciones=form.cleaned_data['observaciones']
            
            
            ofer.doc_oferta = obj_doc
            ofer.oferta_nro=form.cleaned_data['nro'] 
            ofer.cliente=Cliente.objects.get(pk = form.data['cliente'])
            ofer.oferta_tipo=tipo
            
            nume=NumeroDoc()
            if NumeroDoc.objects.count()==0:
                nume.id_numerodoc=uuid4()
            else:
                nume=NumeroDoc.objects.get()
            nume.nro_oferta=form.cleaned_data['nro']
         
            try:
                obj_doc.save()
                ofer.save()
                nume.save() 
                return HttpResponseRedirect('/comerciax/comercial/oferta/view/'+pk_doc.__str__())  
            except Exception, e:
                exc_info = e.__str__() # sys.exc_info()[:1]
                c = exc_info.find("DETAIL:")
                
                if c < 0:
                    l=l+["Error Fatal."]
                else:
                    c = exc_info[c + 7:]
                    l=l+[c] 
                                     
                transaction.rollback()
                form = OfertaForm(request.POST)
                return render_to_response('form/form_adddetalle.html',  {'tipocliente':'2','form': form, 'form_name':nombre_form,'form_description':descripcion_form,
                                                                         'accion':accion_form,'titulo':titulo_form,'controlador':controlador_form,
                                                                         'cancelbtn':cancelbtn_form,'fecha_minima':fecha_cierre,'error2':l},context_instance = RequestContext(request))
            else:
                transaction.commit()
    else:
        nrodoc=1
        
        if NumeroDoc.objects.count()!=0:
            nrodoc=NumeroDoc.objects.get().nro_oferta+1
        form = OfertaForm(initial={'nro':nrodoc}) 
    
    return render_to_response('form/form_adddetalle.html',  {'tipocliente':'2','form': form, 'form_name':nombre_form,'form_description':descripcion_form,
                                                             'accion':accion_form,'titulo':titulo_form,'controlador':controlador_form,
                                                             'cancelbtn':cancelbtn_form,'fecha_minima':fecha_cierre,'error2':c},context_instance = RequestContext(request))


@login_required
@transaction.commit_on_success()
def oferta_edit(request,idof):
    if not request.user.has_perm('comercial.oferta'):
        return render_to_response("denegado.html",locals(),context_instance = RequestContext(request))
    
    nombre_form='Ofertas'
    descripcion_form='Realizar Oferta a Clientes'
    titulo_form='Ofertas' 
    controlador_form='Ofertas'
    accion_form='/comerciax/comercial/oferta/edit/'+ idof +'/'
    cancelbtn_form='/comerciax/comercial/oferta/view/'+ idof +'/'
    fecha_cierre=datetime.date.today().strftime("%d/%m/%Y")
    fecham=Cierre.objects.all()
    c=None
    l=[]
    for a in fecham:
        fecha_cierre=a.fechacierre.strftime("%d/%m/%Y")
        
    detalles=DetalleOferta.objects.filter(oferta=idof).count()   
    if request.method == 'POST':
        ofer = Oferta.objects.select_related().get(pk=idof)
        tipo=ofer.oferta_tipo
        if detalles==0:
            form = OfertaForm(request.POST)
        elif tipo=='V':
            form = OfertaForm1(request.POST)
        else:
            form = OfertaForm2(request.POST)
        #rajuste = form.cleaned_data['ajuste']
        if form.is_valid():
            cc=form.data['cliente']
            if (cc.find("|") < 0):
                obj_cliente = Cliente.objects.get(pk = form.data['cliente'])
            else:
                obj_cliente= Cliente.objects.get(pk = ofer.cliente.id)
            try:
                tipoc=obj_cliente.get_contrato_tipo()
            except Exception, e:
                tipoc=None
            
            if tipoc==None:
                l=['Este cliente no tiene contrato por lo que no se puede realizar la oferta']
                return render_to_response('form/form_adddetalle.html',  {'tipocliente':'2','form': form, 'form_name':nombre_form,
                                                                         'form_description':descripcion_form,'accion':accion_form,
                                                                         'titulo':titulo_form,'controlador':controlador_form,
                                                                         'cancelbtn':cancelbtn_form,'fecha_minima':fecha_cierre,
                                                                         'error2':l},context_instance = RequestContext(request))
            tipo=form.cleaned_data['tipo']  
            if  form.cleaned_data['tipo']=='De Venta':
                tipo='V'
            elif form.cleaned_data['tipo']=='De Ajuste':
                tipo='A'
            elif form.cleaned_data['tipo']=='Otra':
                tipo='O'
                
            if (tipoc==True) and (tipo=='A' or tipo=='O'):
                l=['Este cliente tiene contrato para venta el tipo de oferta seleccionada es incorrecto']
                return render_to_response('form/form_adddetalle.html',  {'tipocliente':'2','form': form, 'form_name':nombre_form,
                                                                         'form_description':descripcion_form,'accion':accion_form,
                                                                         'titulo':titulo_form,'controlador':controlador_form,
                                                                         'cancelbtn':cancelbtn_form,'fecha_minima':fecha_cierre,
                                                                         'error2':l},context_instance = RequestContext(request))
            pk_user=User.objects.get(pk=request.user.id)
            
            ofer=Oferta.objects.get(pk=idof)
            doc=Doc.objects.get(pk=idof)
            
            ofer.oferta_nro=form.cleaned_data['nro'] 
            doc.fecha_doc=form.cleaned_data['fecha']
            doc.operador=pk_user
            doc.doc_operacion=datetime.date.today()
            doc.observaciones=form.cleaned_data['observaciones']         
            ofer.cliente=obj_cliente
            ofer.oferta_tipo=tipo
            try:
                doc.save()
                ofer.save() 
 
                return HttpResponseRedirect('/comerciax/comercial/oferta/view/'+idof)  

            except Exception, e:
                exc_info = e.__str__() # sys.exc_info()[:1]
                c = exc_info.find("DETAIL:")
                
                if c < 0:
                    l=l+["Error Fatal."]
                else:
                    c = exc_info[c + 7:]
                    l=l+[c]
                    
                transaction.rollback()
                
                form = OfertaForm(request.POST)
                return render_to_response('form/form_adddetalle.html',  {'tipocliente':'2','form': form, 'form_name':nombre_form,'form_description':descripcion_form,
                                                                         'accion':accion_form,'titulo':titulo_form,'controlador':controlador_form,
                                                                         'cancelbtn':cancelbtn_form,'fecha_minima':fecha_cierre,'error2':l},context_instance = RequestContext(request))
            else:
                transaction.commit()     
    else:
        ofer = Oferta.objects.select_related().get(pk=idof)
        tipo=ofer.oferta_tipo
        if detalles==0:
            form = OfertaForm(initial={'tipo':ofer.oferta_tipo,'nro':ofer.oferta_nro,'fecha':ofer.doc_oferta.fecha_doc,
                                            'cliente':ofer.cliente,'observaciones':ofer.doc_oferta.observaciones})
        elif tipo=='V':
            form = OfertaForm1(initial={'tipo':'De Venta','nro':ofer.oferta_nro,'fecha':ofer.doc_oferta.fecha_doc,
                                            'cliente':ofer.cliente,'observaciones':ofer.doc_oferta.observaciones})
        else:
            rc_tipo='De Ajuste'
            if ofer.oferta_tipo == 'O':
                rc_tipo='Otra'
            form = OfertaForm2(initial={'tipo':rc_tipo,'nro':ofer.oferta_nro,'fecha':ofer.doc_oferta.fecha_doc,
                                            'cliente':ofer.cliente,'observaciones':ofer.doc_oferta.observaciones})
        
    return render_to_response('form/form_edit.html',  {'tipocliente':'2','form': form, 'form_name':nombre_form,'form_description':descripcion_form,
                                                       'accion':accion_form,'titulo':titulo_form,'controlador':controlador_form,
                                                       'cancelbtn':cancelbtn_form,'fecha_minima':fecha_cierre},context_instance = RequestContext(request))

@login_required
def oferta_view(request,idof):
    if not request.user.has_perm('comercial.oferta'):
        return render_to_response("denegado.html",locals(),context_instance = RequestContext(request))
    
    l=[]
    hay_cup=0
    hay_cuc=0
    ofer = Oferta.objects.select_related().get(pk=idof)

    rc_fecha=ofer.doc_oferta.fecha_doc.strftime("%d/%m/%Y")
    rc_cliente=ofer.cliente.nombre
    rc_nro=ofer.oferta_nro
    tiene_email=1 if ofer.cliente.email.__len__()!=0 else 0

    #asaa=Cliente.objects.get(pk=ofer.cliente.id).get_cascos()
    importecuc=ofer.get_importecuc()
    importecup=ofer.get_importecup()
    importetotalcup=ofer.get_importetotalcup()
    importetotalcasco=ofer.get_importe_venta()
    
    pmn=ClienteContrato.objects.select_related().get(cliente=ofer.cliente.id,cerrado=False)
    mncosto=pmn.contrato.preciocostomn
    cuccosto=pmn.contrato.preciocostocuc
    
    precio_CUP="Precio CUP"
    if(mncosto==True):
        precio_CUP=precio_CUP+"(Costo)"
                
    precio_CUC="Precio MLC"
    if (cuccosto==True):
        precio_CUC=precio_CUC+"(Costo)"
    
    rc_observaciones=ofer.doc_oferta.observaciones
    filas = DetalleOferta.objects.select_related().filter(oferta=idof).order_by('casco__producto_salida__descripcion','casco_casco.casco_nro')
    
    rc_tipo='De Venta'
    if ofer.oferta_tipo == 'O':
        rc_tipo='Otra'
    elif ofer.oferta_tipo == 'A':
        rc_tipo='Ajuste'
    elif ofer.oferta_tipo == 'K':
        rc_tipo='Vulca'

    
    elementos_detalle=[]
    id1=''
    k=0
    k2=0
    t_preciocuc=0.0
    t_preciocup=0.0  
    t_preciocasco=0.0  
    
    for a1 in filas:
        if k!=0:
            if id1!=a1.casco.producto_salida.id:
                elementos_detalle[k-1]['cantidad'] = k2
                elementos_detalle[k-1]['t_preciocuc'] = t_preciocuc
                elementos_detalle[k-1]['t_preciocup'] = t_preciocup
                elementos_detalle[k-1]['t_preciocasco'] = t_preciocasco
                t_preciocuc=0.0
                t_preciocup=0.0 
                t_preciocasco=0.0
                k2=0
        elementos_detalle+=[{'casco_id':a1.casco.id_casco,
                             'casco_nro':a1.casco.casco_nro,'productosalida':a1.casco.producto_salida.descripcion,
                             'productoid':a1.casco.producto.id,'precio_cup':a1.format_precio_mn(),
                             'precio_cuc':a1.format_precio_cuc(),'precio_casco':a1.format_precio_casco()}]
        k+=1
        k2+=1
        t_preciocup+=float(a1.precio_mn)
        t_preciocuc+=float(a1.precio_cuc)
        t_preciocasco+=float(a1.precio_casco)
        id1=a1.casco.producto_salida.id  
    if k!=0:
        elementos_detalle[k-1]['cantidad'] = k2    
        elementos_detalle[k-1]['t_preciocuc'] = t_preciocuc
        elementos_detalle[k-1]['t_preciocup'] = t_preciocup
        elementos_detalle[k-1]['t_preciocasco'] = t_preciocasco
    # Verificar si se puede editar. Se puede editar si todos los cascos relacionados con el estado es Casco
    #editar=editar_documento(filas,idof)
    return render_to_response('comercial/viewoferta.html',{'total_casco':k,'precio_CUC':precio_CUC,'precio_CUP':precio_CUP,
                                                           'importecuc':importecuc,'importecup':importecup,
                                                           'importetotalcup':importetotalcup,
                                                           'tipo':rc_tipo,'rc_nro':rc_nro,'fecha':rc_fecha,
                                                           'cliente':rc_cliente,'observaciones':rc_observaciones,
                                                           'rc_id':idof,'elementos_detalle':elementos_detalle, 
                                                           'haycup':hay_cup,'haycuc':hay_cuc,'error2':l,'tiene_email':tiene_email,
                                                           'importetotalcasco':importetotalcasco},context_instance = RequestContext(request))


@login_required
@transaction.commit_on_success()
def oferta_del(request,idof):
    if not request.user.has_perm('comercial.oferta'):
        return render_to_response("denegado.html",locals(),context_instance = RequestContext(request))
    
    l=[]
    try:
        
        filas = DetalleOferta.objects.filter(oferta=idof)
        #for canti in filas:
        #    actualiza_traza(canti.casco.id_casco,idof)
        
        Doc.objects.select_related().get(pk=idof).delete()
        return HttpResponseRedirect('/comerciax/comercial/oferta/index')
        #return render_to_response("casco/recepcionclienteindex.html",locals(),context_instance = RequestContext(request))
    except Exception :
        transaction.rollback()
        l = ['Error al eliminar el documento']
        ofer = Oferta.objects.select_related().get(pk=idof)
        rc_fecha=ofer.doc_oferta.fecha_doc.strftime("%d/%m/%Y")
        rc_cliente=ofer.cliente.nombre
        rc_nro=ofer.oferta_nro
        rc_observaciones=ofer.observaciones
        filas = DetalleOferta.objects.select_related().filter(oferta=idof).order_by('casco__producto_salida__descripcion','casco_casco.casco_nro')
        hay_cup=0
        hay_cuc=0
        return render_to_response('casco/viewoferta.html',{'rc_nro':rc_nro,'fecha':rc_fecha,
                                                           'cliente':rc_cliente,'haycup':hay_cup,
                                                           'haycuc':hay_cuc,'observaciones':rc_observaciones,
                                                           'rc_id':idof,'elementos_detalle':filas, 
                                                           'error2':l},context_instance = RequestContext(request))
    else:
        transaction.commit()
 
      
#############################################################
#        DETALLE OFERTA
#############################################################
@login_required
def detalleOferCliente_list(request,idprod,idof):
    ofer=Oferta.objects.get(pk=idof)
    filas1=None
    filas=DetalleRC.objects.select_related().filter(rc__cliente=ofer.cliente,rc__recepcioncliente_tipo=ofer.oferta_tipo,casco__estado_actual="PT",casco__producto_salida_id=idprod).order_by('casco_casco.casco_nro')
    
    if ofer.cliente.comercializadora==True:
        filas1=DetalleRC.objects.select_related().filter(rc__cliente__provincia=ofer.cliente.provincia,rc__cliente__organismo=ofer.cliente.organismo,rc__recepcioncliente_tipo=ofer.oferta_tipo,casco__estado_actual="PT",casco__producto_salida_id=idprod).\
               exclude(rc__cliente=ofer.cliente).order_by('casco_casco.casco_nro')
              
    cascos=Casco.objects.select_related().filter(estado_actual="DC",producto_salida_id=idprod).order_by('admincomerciax_producto.descripcion','casco_nro')
    cascos_ventas=Casco.objects.select_related().filter(estado_actual="PT",producto_salida_id=idprod,venta=True).order_by('admincomerciax_producto.descripcion','casco_nro')
    
    lista_valores=[]
    for detalles in filas:
        lista_valores=lista_valores+[{"casco_nro":detalles.casco.casco_nro,"pk":detalles.casco.id_casco,
                                      "medida":detalles.casco.producto_salida.descripcion,"cliente":detalles.casco.get_cliente(),
                                      "medida_entrada":detalles.casco.producto.descripcion}]
    if filas1!=None:
        for detalles in filas1:
            lista_valores=lista_valores+[{"casco_nro":detalles.casco.casco_nro,"pk":detalles.casco.id_casco,
                                      "medida":detalles.casco.producto_salida.descripcion,"cliente":detalles.casco.get_cliente(),
                                      "medida_entrada":detalles.casco.producto.descripcion}]
    for detalles in cascos:
        lista_valores=lista_valores+[{"casco_nro":detalles.casco_nro,"pk":detalles.id_casco,
                                      "medida":detalles.producto_salida.descripcion,"cliente":detalles.get_cliente(),
                                      "medida_entrada":detalles.producto.descripcion}]
    for detalles in cascos_ventas:
        lista_valores=lista_valores+[{"casco_nro":detalles.casco_nro,"pk":detalles.id_casco,
                                      "medida":detalles.producto_salida.descripcion,"cliente":detalles.get_cliente(),
                                      "medida_entrada":detalles.producto.descripcion}]
    
    return HttpResponse(simplejson.dumps(lista_valores),content_type = 'application/javascript; charset=utf8')

@login_required
#@transaction.commit_on_success()
def detalleOfer_add(request,idof):
    if not request.user.has_perm('comercial.oferta'):
        return render_to_response("denegado.html",locals(),context_instance = RequestContext(request))
    
    titulo_form='Ofertas' 
    controlador_form='Ofertas'
    descripcion_form='Seleccionar cascos para la oferta'
    
    accion_form='detalleOferta_add'
    cancelbtn_form='/comerciax/comercial/oferta/view/'+idof
    
     
    ofer=Oferta.objects.get(pk=idof)
    medidas=Producto.objects.all()

    if request.method == 'POST':
        pmn=ClienteContrato.objects.select_related().get(cliente=ofer.cliente.id,cerrado=False)
        mn=pmn.contrato.preciomn
        mnext = pmn.contrato.precioextcup
        mncosto=pmn.contrato.preciocostomn
        cuc=pmn.contrato.preciocuc
        cuccosto=pmn.contrato.preciocostocuc
        seleccion=request.POST.keys()
        k=0

        while True:
            if k==seleccion.__len__():
                break
            casco=Casco.objects.filter(pk=seleccion[k])

            if casco.count()!=0:
                '''
                Los selecionados los cambio de estado, agregar a detalle del documento y actualizar trazabilidad
                
                Casco.objects.filter(pk=seleccion[k]).update(estado_actual=Estados.estados["Oferta"])
                '''
                
                detalle=DetalleOferta()
                if DetalleOferta.objects.filter(oferta=idof, casco=Casco.objects.get(pk=seleccion[k])).count()!=0:
                    detalle=DetalleOferta.objects.get(oferta=idof, casco=Casco.objects.get(pk=seleccion[k]))
                else:
                    detalle.id_detalleofertafactura=uuid4()
                    
                detalle.oferta=Oferta.objects.get(pk=idof)
                detalle.casco=Casco.objects.get(pk=seleccion[k])
                detalle.precio_mn=0
                detalle.precio_casco=0
                
                if (mn==True):
                    detalle.precio_mn=detalle.casco.producto_salida.precio_mn
                    if detalle.casco.venta==True and detalle.casco.decomisado==False:
                        if not detalle.casco.id_cliente.get_precio_casco():
                            detalle.precio_casco=detalle.casco.producto_salida.precio_casco
                        else:
                            detalle.precio_casco=detalle.casco.producto_salida.otro_precio_casco
                elif (mnext==True):
                    detalle.precio_mn=detalle.casco.producto_salida.precio_externo_cup
                    if detalle.casco.venta==True and detalle.casco.decomisado==False:
                        if not detalle.casco.id_cliente.get_precio_casco():
                            detalle.precio_casco=detalle.casco.producto_salida.precio_casco
                        else:
                            detalle.precio_casco=detalle.casco.producto_salida.otro_precio_casco
                elif(mncosto==True):
                    detalle.precio_mn=detalle.casco.producto_salida.precio_costo_mn
                detalle.precio_cuc=0
                if (cuc==True):
                    detalle.precio_cuc=detalle.casco.producto_salida.precio_cuc
                elif (cuccosto==True):
                    detalle.precio_cuc=detalle.casco.producto_salida.precio_costo_cuc
                    
                detalle.save()
            k=k+1
        if request.POST.__contains__('submit1'):
            return render_to_response('comercial/seleccionar_casco_oferta.html', {'title':titulo_form,'controlador':controlador_form,'accion':accion_form,
                                                     'cancelbtn':cancelbtn_form, 'nro':ofer.oferta_nro,'form_description':descripcion_form,
                                                     'fecha':ofer.doc_oferta.fecha_doc.strftime("%d/%m/%Y"),'observaciones':ofer.doc_oferta.observaciones,
                                                     'rc_id':idof,'medidas':medidas},context_instance = RequestContext(request))
        else:
            return HttpResponseRedirect('/comerciax/comercial/oferta/view/' + idof)
#    if ofer.oferta_tipo=='V':
    return render_to_response('comercial/seleccionar_casco_oferta.html', {'title':titulo_form,'controlador':controlador_form,'accion':accion_form,
                                                      'cancelbtn':cancelbtn_form, 'nro':ofer.oferta_nro,'form_description':descripcion_form,
                                                      'fecha':ofer.doc_oferta.fecha_doc.strftime("%d/%m/%Y"),'observaciones':ofer.doc_oferta.observaciones,
                                                      'rc_id':idof,'dettransfe':True,'medidas':medidas},context_instance = RequestContext(request)) 

@login_required
def detalleOfer_delete(request,idof,idcasco):
    if not request.user.has_perm('comercial.oferta'):
        return render_to_response("denegado.html",locals(),context_instance = RequestContext(request))
    
    DetalleOferta.objects.get(casco=idcasco,oferta=idof).delete()
        
    filas = DetalleOferta.objects.select_related().filter(oferta=idof).order_by('casco__producto_salida__descripcion','casco__casco_nro')
    
    elementos_detalle=[]
    id1=''
    k=0
    k2=0
    t_preciocuc=0.0
    t_preciocup=0.0  
    t_preciocasco=0.0  
    
    for a1 in filas:
        if k!=0:
            if id1!=a1.casco.producto_salida.id:
                elementos_detalle[k-1]['cantidad'] = k2
                elementos_detalle[k-1]['t_preciocuc'] = t_preciocuc
                elementos_detalle[k-1]['t_preciocup'] = t_preciocup
                elementos_detalle[k-1]['t_preciocasco'] = t_preciocasco
                t_preciocuc=0.0
                t_preciocup=0.0 
                t_preciocasco=0.0
                k2=0
        if k==0: 
            importetotalcup=a1.oferta.get_importetotalcup()
            importetotalcuc=a1.oferta.get_importecuc()
            importetotalcasco=a1.oferta.get_importe_venta()
            elementos_detalle+=[{'id_doc':a1.oferta.doc_oferta.id_doc,'importetotalcup':importetotalcup,'importetotalcuc':importetotalcuc,'casco_id':a1.casco.id_casco,
                             'casco_nro':a1.casco.casco_nro,'productosalida':a1.casco.producto_salida.descripcion,
                             'productoid':a1.casco.producto.id,'precio_cup':a1.format_precio_mn(),'importetotalcasco':importetotalcasco,
                             'precio_cuc':a1.format_precio_cuc(),'precio_casco':a1.format_precio_casco()}]
        else:
            elementos_detalle+=[{'id_doc':a1.oferta.doc_oferta.id_doc,'casco_id':a1.casco.id_casco,
                             'casco_nro':a1.casco.casco_nro,'productosalida':a1.casco.producto_salida.descripcion,
                             'productoid':a1.casco.producto.id,'precio_cup':a1.format_precio_mn(),
                             'precio_cuc':a1.format_precio_cuc(),'precio_casco':a1.format_precio_casco()}]
        k+=1
        k2+=1
        t_preciocup+=float(a1.precio_mn)
        t_preciocuc+=float(a1.precio_cuc)
        t_preciocasco+=float(a1.precio_casco)
        id1=a1.casco.producto_salida.id  
    if k!=0:
        elementos_detalle[k-1]['cantidad'] = k2    
        elementos_detalle[k-1]['t_preciocuc'] = '{:20,.2f}'.format(t_preciocuc)
        elementos_detalle[k-1]['t_preciocup'] = '{:20,.2f}'.format(t_preciocup)
        elementos_detalle[k-1]['t_preciocasco'] = '{:20,.2f}'.format(t_preciocasco)
    return HttpResponse(simplejson.dumps(elementos_detalle),content_type = 'application/javascript; charset=utf8')

#############################################################
#                              FACTURAS                     #
#############################################################

def verfactura(request,idfactura,haycup,haycuc,cantcascos):
    empresaobj1 = Empresa.objects.all()
    hay_cup=int(haycup)
    hay_cuc=int(haycuc)
    for empresaobj in empresaobj1: 
        titular_name = empresaobj.nombre
        titular_dir = empresaobj.direccion
        titular_codigo = empresaobj.codigo
        titular_email = empresaobj.email
        titular_phone = empresaobj.telefono
        titular_fax = empresaobj.fax
        titular_cuenta_mn = empresaobj.cuenta_mn
        titular_cuenta_cuc = empresaobj.cuenta_usd
        titular_sucursal_mn = empresaobj.sucursal_mn
        titular_sucursal_cuc = empresaobj.sucursal_usd
    
    factura = Facturas.objects.select_related().get(doc_factura=idfactura)
    pk_user=User.objects.get(pk=request.user.id)
    vendedor=pk_user.first_name+" "+pk_user.last_name
    
#    doc_fac=Facturas.objects.get(pk=idfactura).doc_factura
    user_doc=Doc.objects.get(id_doc=factura.doc_factura.id_doc).operador
    operador_=User.objects.get(pk=user_doc.id)
#    operador_=User.objects.get(pk=Doc.objects.get(pk=Facturas.objects.get(pk=idfactura).doc_factura).operador)
    confeccionado=operador_.first_name+" "+operador_.last_name
        
#    detallesFact4 = DetalleFactura.objects.select_related().filter(factura=idfactura,casco__producto_salida__codigo='"625.9.01.2205"')
    #Todos los cascos el servicio de recape
    detallesFact = DetalleFactura.objects.select_related().filter(factura=idfactura).values('factura','precio_mn','precio_cuc','casco__producto_salida',\
                                                                            'casco__producto_salida__codigo','casco__producto_salida__descripcion',\
                                                                            'casco__producto_salida__um__descripcion')\
                                                                            .annotate(cantidad=Count('casco__producto_salida'))
    for a1 in range(detallesFact.__len__()):
        detallesFact[a1]['importecup']=detallesFact[a1]['precio_mn']*detallesFact[a1]['cantidad']
        detallesFact[a1]['importecup']=str(detallesFact[a1]['importecup'])
        detallesFact[a1]['precio_mn']=str(detallesFact[a1]['precio_mn'])
        detallesFact[a1]['importecuc']=detallesFact[a1]['precio_cuc']*detallesFact[a1]['cantidad']
        detallesFact[a1]['importecuc']=str(detallesFact[a1]['importecuc'])
        detallesFact[a1]['precio_cuc']=str(detallesFact[a1]['precio_cuc'])
        
    #Los de venta, el valor del casco
    detallesFact_venta = DetalleFactura.objects.select_related().filter(factura=idfactura,casco__venta=True,casco__decomisado=False).values('factura','precio_casco','casco__producto_salida',\
                                                                            'casco__producto_salida__codigo','casco__producto_salida__descripcion',\
                                                                            'casco__producto_salida__um__descripcion')\
                                                                            .annotate(cantidad=Count('casco__producto_salida'))
    hay_venta=0
    for a1 in range(detallesFact_venta.__len__()):
        hay_venta=1
        detallesFact_venta[a1]['importecup']=detallesFact_venta[a1]['precio_casco']*detallesFact_venta[a1]['cantidad']
        detallesFact_venta[a1]['importecup']=str(detallesFact_venta[a1]['importecup'])
        detallesFact_venta[a1]['precio_casco']=str(detallesFact_venta[a1]['precio_casco'])
    
    cliente = factura.cliente
    fecha_confeccionado = factura.doc_factura.fecha_doc
    
    cliente_codigo = cliente.codigo
    cliente_nombre = cliente.nombre
    cliente_dir = cliente.direccion
    cliente_phone = cliente.telefono
    cliente_email = cliente.email
    cliente_fax = cliente.fax
    
    contrato = ClienteContrato.objects.select_related().get(cliente=cliente.id, cerrado=False)
    contrato_sucursal_mn = contrato.contrato.sucursal_mn
    contrato_sucursal_cuc = contrato.contrato.sucursal_usd
    contrato_cuenta_mn = contrato.contrato.cuenta_mn
    contrato_cuenta_cuc = contrato.contrato.cuenta_usd
    contrato_nro = contrato.contrato.contrato_nro
    
    transportador = factura.transportador
    transportador_nombre = transportador.nombre
    transportador_ci = transportador.ci
    #transportador_licencia = transportador.licencia
    transportador_chapa = factura.chapa 
    transportador_licencia = factura.licencia
    vulca = False
    regrabable = False
    if factura.cancelada==True:
        cancelada=True
    else:
        regrabable = factura.tipo=='R'
        if factura.tipo=='A':
            ajuste=True
        elif factura.tipo == 'K':
            vulca = True
    
    importetotalcup=factura.get_importetotalcup()
    importetotalcuc=factura.get_importecuc()
    importecup=factura.get_importecup()
    importecup_venta=factura.get_importe_venta()
    
    importeventa=factura.get_importe_venta()
    
    
    observaciones=factura.doc_factura.observaciones
    declaracion = True
    
    
         
    #return render_to_response("report/reporte1.html",locals(),context_instance = RequestContext(request))
    return render_to_response("report/factura.html",locals(),context_instance = RequestContext(request))


    
def obtener_transp(request, idcl):
    data=[]
    vencido=3
    numero="Sin Contrato"
    por_pagar=0
    fecha1 = datetime.date.today().timetuple()[:3]
    fecha2=datetime.datetime.strptime(str(fecha1[0])+"/"+str(fecha1[1])+"/"+str(fecha1[2]), '%Y/%m/%d').date()
    if idcl.__len__()!=0:
        elementos=Cliente.objects.get(id=idcl)
        if elementos.get_facturas_porpagar():
            por_pagar=1
        numero=elementos.get_contrato_nro()
#        cc=ClienteContrato.objects.filter(cliente_id=idcl,cerrado=False,contrato__fecha_vencimiento__lte=fecha2)
        cc=ClienteContrato.objects.filter(cliente__id=idcl,cerrado=False)
        vencido=3
        for ax in cc:
            if ax.contrato.fecha_vencimiento<=fecha2:
#            if ClienteContrato.objects.get(cliente_id=idcl,cerrado=False,contrato__fecha_vencimiento__lte=fecha2)!=None:
                vencido=1
            else:
                vencido=0
            
        trans=Transpotador.objects.select_related().filter(activo=True,contrato__clientecontrato__cerrado=False,contrato__clientecontrato__cliente=Cliente.objects.get(id = idcl).id).all()
    else:        
        trans=Transpotador.objects.select_related().filter(id='0').all()
        
    for a1 in trans:
        data+=[{'pk':a1.id,'nombre':a1.nombre,'vencido':str(vencido),'nro':numero,'por_pagar':str(por_pagar)}]
    if data.__len__()==0:
        data+=[{'pk':"",'nombre':"",'vencido':str(vencido),'nro':"",'por_pagar':""}]
        
    return HttpResponse(simplejson.dumps(data),content_type = 'application/javascript; charset=utf8') 
   
#    data = serializers.serialize("json", trans, fields=('id','nombre'))
#    return HttpResponse(data, mimetype="application/javascript")
 
 
#===============================================================================
# FACTURA ENTIDADES EXTERNAS
#===============================================================================
@login_required
def get_factext_list(request):
    #prepare the params
    try:
        fecha_desde=Fecha_Ver.objects.get()
    except Exception, e:
        fecha_desde=None
    if  fecha_desde == None:  
        querySet = Facturas.objects.select_related().filter(cliente__externo=True)
    else:
        querySet = Facturas.objects.select_related().filter(cliente__externo=True,doc_factura__fecha_doc__gte=fecha_desde.fecha)
    #querySet = querySet.filter(doc__fecha_doc__year=2010)
 
    columnIndexNameMap = {0:'-doc_factura__fecha_doc',1:'factura_nro',2:'admincomerciax_cliente.nombre',3:'doc_factura__fecha_doc',4:'tipo',5:'cancelada',6:'confirmar'}
    #{0: 'oferta_nro',1: 'oferta_nro',2:'admincomerciax_cliente.nombre',3:'doc_oferta__fecha_oferta',4:'oferta_tipo'}

    searchableColumns = ['confirmar','factura_nro','cliente__nombre','doc_factura__fecha_doc']
    #path to template used to generate json
    jsonTemplatePath = 'comercial/json/json_factura.txt'

    #call to generic function from utils
    return get_datatables_records(request, querySet, columnIndexNameMap, searchableColumns, jsonTemplatePath)

    

@login_required
def facturaext_index(request):
    if not request.user.has_perm('comercial.factura'):
        return render_to_response("denegado.html",locals(),context_instance = RequestContext(request))
    return render_to_response('comercial/facturaextindex.html',locals(),context_instance = RequestContext(request))
    
@login_required
@transaction.commit_on_success()
def facturaext_add(request):
    if not request.user.has_perm('comercial.factura'):
        return render_to_response("denegado.html",locals(),context_instance = RequestContext(request))
    nombre_form='Facturas'
    descripcion_form='Realizar Factura'
    titulo_form='Facturas' 
    controlador_form='Facturas'
    accion_form='/comerciax/comercial/facturaext/add'
    cancelbtn_form='/comerciax/comercial/facturaext/index'
    fecha_cierre=Fechacierre.objects.get(almacen='cm').fechaminima()
    fecha_maxima=Fechacierre.objects.get(almacen='cm').fechamaxima()
    c=None
    l=[]
#    for a in fecham:
#        fecha_cierre=a.fechacierre.strftime("%d/%m/%Y")
    if request.method == 'POST':
        form = FacturaExtForm(request.POST)

        if form.is_valid():
            tipo=form.cleaned_data['tipo']
            obj_cliente = Cliente.objects.get(pk = form.data['cliente1'])
            #cliente = Cliente.objects.get(id = cliente_id)
             
            try:
                tipoc=obj_cliente.get_contrato_tipo()
            except Exception, e:
                tipoc=None
            
            if tipoc==None:
                l=['Este cliente no tiene contrato por lo que no se puede realizar la factura']
                return render_to_response('comercial/facturaextadd.html',  {'form': form, 'form_name':nombre_form,
                                                                         'form_description':descripcion_form,'accion':accion_form,
                                                                         'titulo':titulo_form,'controlador':controlador_form,
                                                                         'cancelbtn':cancelbtn_form,'fecha_minima':fecha_cierre,'fecha_maxima':fecha_maxima,
                                                                         'error2':l},context_instance = RequestContext(request))
               
            if (tipoc==True) and (tipo=='A' or tipo=='O'):
                l=['Este cliente tiene contrato para venta el tipo de factura seleccionada es incorrecto']
                return render_to_response('comercial/facturaextadd.html',  {'form': form, 'form_name':nombre_form,
                                                                         'form_description':descripcion_form,'accion':accion_form,
                                                                         'titulo':titulo_form,'controlador':controlador_form,
                                                                         'cancelbtn':cancelbtn_form,'fecha_minima':fecha_cierre,'fecha_maxima':fecha_maxima,
                                                                         'error2':l},context_instance = RequestContext(request))
                  
            pk_user=User.objects.get(pk=request.user.id)
            
            fact=Facturas()
            
            pk_doc=uuid4()
            obj_doc=Doc()
            
            obj_doc.id_doc=pk_doc
            obj_doc.tipo_doc='14'
            obj_doc.fecha_doc=form.cleaned_data['fecha']
            obj_doc.operador=pk_user
            obj_doc.fecha_operacion=datetime.date.today()
            obj_doc.observaciones=form.cleaned_data['observaciones']
            
            fact.doc_factura = obj_doc
            fact.factura_nro=random.randint(1,100000)  
            fact.cliente=Cliente.objects.get(pk = form.data['cliente1'])
            fact.tipo=tipo
            fact.confirmada=hashlib.sha1(pk_doc.__str__()+'NO').hexdigest()

            fact.chapa=form.cleaned_data['chapa']
            fact.licencia=form.cleaned_data['licencia']
            fact.transportador=Transpotador.objects.get(pk = form.data['transportador']) 
         
            try:
                obj_doc.save()
                fact.save()
#                nume.save() 
                return HttpResponseRedirect('/comerciax/comercial/facturaext/view/'+pk_doc.__str__())  
            except Exception, e:
                exc_info = e.__str__() # sys.exc_info()[:1]
                c = exc_info.find("DETAIL:")
                
                if c < 0:
                    l=l+["Error Fatal."]
                else:
                    c = exc_info[c + 7:]
                    l=l+[c] 
                                     
                transaction.rollback()
                form = FacturaExtForm(request.POST)
                return render_to_response('comercial/facturaextadd.html',  {'form': form, 'form_name':nombre_form,'form_description':descripcion_form,
                                                                         'accion':accion_form,'titulo':titulo_form,'controlador':controlador_form,
                                                                         'cancelbtn':cancelbtn_form,'fecha_minima':fecha_cierre,'fecha_maxima':fecha_maxima,'error2':l},context_instance = RequestContext(request))
            else:
                transaction.commit()
    else:

        form =FacturaExtForm(initial={'fecha':fecha_cierre}) 
    
    return render_to_response('comercial/facturaextadd.html',  {'form': form, 'form_name':nombre_form,'form_description':descripcion_form,
                                                             'accion':accion_form,'titulo':titulo_form,'controlador':controlador_form,
                                                             'cancelbtn':cancelbtn_form,'fecha_minima':fecha_cierre,'fecha_maxima':fecha_maxima,'error2':c},context_instance = RequestContext(request))


@login_required
@transaction.commit_on_success()
def facturaext_edit(request,idfa):
    if not request.user.has_perm('comercial.factura'):
        return render_to_response("denegado.html",locals(),context_instance = RequestContext(request))
    
    fact=Facturas.objects.select_related().get(pk=idfa)
    noedit=0
    if fact.confirmada == hashlib.sha1(fact.pk.__str__()+'YES').hexdigest():
        mensa="No se puede editar la factura Nro. "+fact.factura_nro+" porque ya está confirmada"
        noedit=1
    elif fact.confirmada != hashlib.sha1(fact.pk.__str__()+'NO').hexdigest():
        mensa="No se puede editar la factura Nro. "+fact.factura_nro+" porque está corrupta"
        noedit=1
        #return HttpResponseRedirect('/comerciax/comercial/facturaext/view/'+idfa) 
    if noedit==1:
        l=[mensa]
        rc_fecha=fact.doc_factura.fecha_doc.strftime("%d/%m/%Y")
        rc_cliente=fact.cliente.nombre
        rc_nro=fact.factura_nro

        importecup=Facturas.objects.get(pk=idfa).get_importecup()
        importecuc=Facturas.objects.get(pk=idfa).get_importecuc()
        
        
        pmn=ClienteContrato.objects.select_related().get(cliente=fact.cliente.id,cerrado=False)
        mncosto=pmn.contrato.preciocostomn
        cuccosto=pmn.contrato.preciocostocuc
    
        precio_CUP="Precio CUP"
        if(mncosto==True):
            precio_CUP=precio_CUP+"(Costo)"
                
        precio_CUC="Precio MLC"
        if (cuccosto==True):
            precio_CUC=precio_CUC+"(Costo)"
                    
        rc_observaciones=fact.doc_factura.observaciones
        filas = DetalleFactura.objects.select_related().filter(factura=idfa).order_by('casco_casco.casco_nro')
        rc_tipo='De Venta'
        if fact.tipo == 'O':
            rc_tipo='Otra'
        elif fact.tipo == 'A':
            rc_tipo='Ajuste'
        elif fact.tipo == 'K':
            rc_tipo='Vulca'
        rc_transportador=fact.transportador.nombre
        rc_chapa=fact.chapa
        rc_licencia=fact.licencia
        hay_cup=0
        hay_cuc=0
        
    # Verificar si se puede editar. Se puede editar si todos los cascos relacionados con el estado es Casco
    #editar=editar_documento(filas,idfa)
    
        return render_to_response('comercial/viewfacturaext.html',{'hay_cup':hay_cup,'hay_cuc':hay_cuc,'eliminar':0,'editar':1,'cancelar':0,'confirmar':0,'transportador':rc_transportador,'chapa':rc_chapa,
                                                            'transportador':rc_transportador,'licencia':rc_licencia,'precio_CUC':precio_CUC,
                                                            'precio_CUP':precio_CUP,'importecuc':importecuc,'importecup':importecup,
                                                            'tipo':rc_tipo,'rc_nro':rc_nro,'fecha':rc_fecha,'cliente':rc_cliente,
                                                            'observaciones':rc_observaciones,'rc_id':idfa,'elementos_detalle':filas, 
                                                            'error2':l},context_instance = RequestContext(request))

    nombre_form='Facturas'
    descripcion_form='Realizar Factura a Clientes'
    titulo_form='Facturas' 
    controlador_form='Facturas'
    accion_form='/comerciax/comercial/facturaext/edit/'+ idfa +'/'
    cancelbtn_form='/comerciax/comercial/facturaext/view/'+ idfa +'/'
    fecha_cierre=Fechacierre.objects.get(almacen='cm').fechaminima()
    fecha_maxima=Fechacierre.objects.get(almacen='cm').fechamaxima() 
    c=None
    
#    fact = Facturas.objects.select_related().get(pk=idfa)
    l=[]
#    for a in fecham:
#        fecha_cierre=a.fechacierre.strftime("%d/%m/%Y")
        
    detalles=DetalleFactura.objects.filter(factura=idfa).count() 
      
    if request.method == 'POST':
        tipo=fact.tipo
        if detalles==0:
            form = FacturaExtForm(request.POST)
        elif tipo=='V':
            form = FacturaExtForm1(request.POST)
        else:
            form = FacturaExtForm2(request.POST)
        #rajuste = form.cleaned_data['ajuste']
        if form.is_valid():
            cc=form.data['cliente1']
            if (cc.find("|") < 0):
                obj_cliente = Cliente.objects.get(pk = form.data['cliente1'])
            else:
                obj_cliente= Cliente.objects.get(pk = fact.cliente.id)
            try:
                tipoc=obj_cliente.get_contrato_tipo()
            except Exception, e:
                tipoc=None
            
            if tipoc==None:
                l=['Este cliente no tiene contrato por lo que no se puede realizar la factura']
                return render_to_response('form/form_adddetalle.html',  {'tipocliente':'1','form': form, 'form_name':nombre_form,
                                                                         'form_description':descripcion_form,'accion':accion_form,
                                                                         'titulo':titulo_form,'controlador':controlador_form,
                                                                         'cancelbtn':cancelbtn_form,'fecha_minima':fecha_cierre,'fecha_maxima':fecha_maxima,
                                                                         'error2':l},context_instance = RequestContext(request))
            tipo=form.cleaned_data['tipo']  
            if  form.cleaned_data['tipo']=='De Venta':
                tipo='V'
            elif form.cleaned_data['tipo']=='De Ajuste':
                tipo='A'
            elif form.cleaned_data['tipo']=='Otra':
                tipo='O'
                
            if (tipoc==True) and (tipo=='A' or tipo=='O'):
                l=['Este cliente tiene contrato para venta el tipo de factura seleccionada es incorrecto']
                return render_to_response('form/form_adddetalle.html',  {'tipocliente':'1','form': form, 'form_name':nombre_form,
                                                                         'form_description':descripcion_form,'accion':accion_form,
                                                                         'titulo':titulo_form,'controlador':controlador_form,
                                                                         'cancelbtn':cancelbtn_form,'fecha_minima':fecha_cierre,'fecha_maxima':fecha_maxima,
                                                                         'error2':l},context_instance = RequestContext(request))
                  
            
            pk_user=User.objects.get(pk=request.user.id)
            
            fact=Facturas.objects.get(pk=idfa)
            doc=Doc.objects.get(pk=idfa)
            
#            fact.factura_nro=form.cleaned_data['nro'] 
            doc.fecha_doc=form.cleaned_data['fecha']
            doc.operador=pk_user
            doc.doc_operacion=datetime.date.today()
            doc.observaciones=form.cleaned_data['observaciones']         
            fact.cliente=obj_cliente
            fact.transportador=Transpotador.objects.get(pk=form.data['transportador'])
            fact.tipo=tipo
            fact.chapa=form.cleaned_data['chapa']
            fact.licencia=form.cleaned_data['licencia']
         
            try:
                doc.save()
                fact.save() 
 
                return HttpResponseRedirect('/comerciax/comercial/facturaext/view/'+idfa)  

            except Exception, e:
                exc_info = e.__str__() # sys.exc_info()[:1]
                c = exc_info.find("DETAIL:")
                
                if c < 0:
                    l=l+["Error Fatal."]
                else:
                    c = exc_info[c + 7:]
                    l=l+[c]
                    
                transaction.rollback()
                
                form = FacturaExtForm(request.POST)
                return render_to_response('form/form_adddetalle.html',  {'tipocliente':'1','form': form, 'form_name':nombre_form,'form_description':descripcion_form,
                                                                         'accion':accion_form,'titulo':titulo_form,'controlador':controlador_form,
                                                                         'cancelbtn':cancelbtn_form,'fecha_minima':fecha_cierre,'fecha_maxima':fecha_maxima,'error2':l},context_instance = RequestContext(request))
            else:
                transaction.commit()     
    else:
#        fact = Facturas.objects.select_related().get(pk=idfa)
        tipo=fact.tipo
        if detalles==0:
            form = FacturaExtForm(initial={'transportador':fact.transportador,'chapa':fact.chapa,'licencia':fact.licencia,'tipo':fact.tipo,'nro':fact.factura_nro,'fecha':fact.doc_factura.fecha_doc,
                                            'cliente1':fact.cliente,'observaciones':fact.doc_factura.observaciones})
        elif tipo=='V':
            a1=fact.cliente
            form = FacturaExtForm1(initial={'transportador':fact.transportador,
                                         'chapa':fact.chapa,
                                         'licencia':fact.licencia,
                                         'tipo':'De Venta',
                                         'nro':fact.factura_nro,
                                         'fecha':fact.doc_factura.fecha_doc,
                                         'cliente1':fact.cliente,
                                         'observaciones':fact.doc_factura.observaciones})
        else:
            rc_tipo='De Ajuste'
            if fact.tipo == 'O':
                rc_tipo='Otra'
            form = FacturaExtForm2(initial={'transportador':fact.transportador,'licencia':fact.licencia,'chapa':fact.chapa,'tipo':rc_tipo,'nro':fact.factura_nro,'fecha':fact.doc_factura.fecha_doc,
                                            'cliente1':fact.cliente,'transportador':fact.transportador,'observaciones':fact.doc_factura.observaciones})
        
    return render_to_response('comercial/facturaextedit.html',  {'form': form, 'form_name':nombre_form,'form_description':descripcion_form,
                                                       'accion':accion_form,'titulo':titulo_form,'controlador':controlador_form,
                                                       'cancelbtn':cancelbtn_form,'fecha_minima':fecha_cierre,'fecha_maxima':fecha_maxima},context_instance = RequestContext(request))

@login_required
def facturaext_view(request,idfa):
    if not request.user.has_perm('comercial.factura'):
        return render_to_response("denegado.html",locals(),context_instance = RequestContext(request))
    
    l=[]
    cancelar=0
    fact = Facturas.objects.select_related().get(pk=idfa)
    if fact.cancelada==True:
        cancelar=1
    confir=fact.get_confirmada()
    confirmar=2
    if confir=='N':
        confirmar=0
    elif confir=='S':
        confirmar=1

    eliminar=1
    editar=1
    if confirmar==2 or confirmar==1:
        eliminar=0  
        editar=0
     
    rc_fecha=fact.doc_factura.fecha_doc.strftime("%d/%m/%Y")
    rc_cliente=fact.cliente.nombre
    rc_nro=fact.factura_nro
    importecup=Facturas.objects.get(pk=idfa).get_importetotalcup()
    importecuc=Facturas.objects.get(pk=idfa).get_importecuc()   
    cant_cascos=Facturas.objects.get(pk=idfa).cantidad_casco() 
    importecasco=Facturas.objects.get(pk=idfa).get_importe_venta()
    cant_renglones=Facturas.objects.get(pk=idfa).get_renglones() 
    pmn=ClienteContrato.objects.select_related().get(cliente=fact.cliente.id,cerrado=False)
    mncosto=pmn.contrato.preciocostomn
    cuccosto=pmn.contrato.preciocostocuc
    
    precio_CUP="Precio CUP"
    if(mncosto==True):
        precio_CUP=precio_CUP+"(Costo)"
                
    precio_CUC="Precio MLC"
    if (cuccosto==True):
        precio_CUC=precio_CUC+"(Costo)"
                    
    rc_observaciones=fact.doc_factura.observaciones
    filas = DetalleFactura.objects.select_related().filter(factura=idfa).order_by('casco__producto_salida__descripcion','casco__casco_nro')
    rc_tipo='De Venta'
    if fact.tipo == 'O':
        rc_tipo='Otra'
    elif fact.tipo == 'A':
        rc_tipo='Ajuste'
    elif fact.tipo == 'K':
        rc_tipo='Vulca'
    rc_transportador=fact.transportador.nombre
    rc_chapa=fact.chapa
    rc_licencia=fact.licencia
    hay_cup=1
    hay_cuc=1
    
    
    elementos_detalle=[]
    id1=''
    k=0
    k2=0
    t_preciocuc=0.0
    t_preciocup=0.0  
    t_preciocasco=0.0  
    
    for a1 in filas:
        if k!=0:
            if id1!=a1.casco.producto_salida.id:
                elementos_detalle[k-1]['cantidad'] = k2
                elementos_detalle[k-1]['t_preciocuc'] = t_preciocuc
                elementos_detalle[k-1]['t_preciocup'] = t_preciocup
                elementos_detalle[k-1]['t_preciocasco'] = t_preciocasco
                t_preciocuc=0.0
                t_preciocup=0.0 
                t_preciocasco=0.0
                k2=0
        elementos_detalle+=[{'casco_id':a1.casco.id_casco,
                             'casco_nro':a1.casco.casco_nro,'productosalida':a1.casco.producto_salida.descripcion,
                             'productoid':a1.casco.producto.id,'precio_cup':a1.format_precio_mn(),
                             'precio_cuc':a1.format_precio_cuc(),'precio_casco':a1.format_precio_casco()}]
        k+=1
        k2+=1
        t_preciocup+=float(a1.precio_mn)
        t_preciocuc+=float(a1.precio_cuc)
        t_preciocasco+=float(a1.precio_casco)
        id1=a1.casco.producto_salida.id  
    if k!=0:
        elementos_detalle[k-1]['cantidad'] = k2    
        elementos_detalle[k-1]['t_preciocuc'] = t_preciocuc
        elementos_detalle[k-1]['t_preciocup'] = t_preciocup
        elementos_detalle[k-1]['t_preciocasco'] = t_preciocasco
    return render_to_response('comercial/viewfacturaext.html',{'total_casco':k,'hay_cup':hay_cup,'hay_cuc':hay_cuc,
                                                            'eliminar':eliminar,'editar':editar,'cancelar':cancelar,
                                                            'confirmar':confirmar,'transportador':rc_transportador,
                                                            'chapa':rc_chapa,'precio_CUC':precio_CUC,'importecasco':importecasco,
                                                            'transportador':rc_transportador,'licencia':rc_licencia,
                                                            'precio_CUP':precio_CUP,'importecuc':importecuc,'importecup':importecup,
                                                            'tipo':rc_tipo,'rc_nro':rc_nro,'fecha':rc_fecha,'cliente':rc_cliente,
                                                            'observaciones':rc_observaciones,'rc_id':idfa,'elementos_detalle':elementos_detalle, 
                                                            'error2':l,'cant_cascos':cant_cascos,'cant_renglones':cant_renglones},context_instance = RequestContext(request))

@login_required
@transaction.commit_on_success()
def facturaext_del(request,idfa):
    if not request.user.has_perm('comercial.factura'):
        return render_to_response("denegado.html",locals(),context_instance = RequestContext(request))
    
    l=[]
    fact=Facturas.objects.get(pk=idfa)
    noelim=0
    if fact.confirmada == hashlib.sha1(fact.pk.__str__()+'YES').hexdigest():
        mensa="No se puede eliminar la factura Nro. "+fact.factura_nro+" porque ya está confirmada"
        noelim=1
    elif fact.confirmada != hashlib.sha1(fact.pk.__str__()+'NO').hexdigest():
        mensa="No se puede eliminar la factura Nro. "+fact.factura_nro+" porque está corrupta"
        noelim=1
        #return HttpResponseRedirect('/comerciax/comercial/facturaext/view/'+idfa) 
    if noelim==1:
        l=[mensa]
        rc_fecha=fact.doc_factura.fecha_doc.strftime("%d/%m/%Y")
        rc_cliente=fact.cliente.nombre
        rc_nro=fact.factura_nro
        importecup=Facturas.objects.get(pk=idfa).get_importecup()  
        importecuc=Facturas.objects.get(pk=idfa).get_importecuc() 
    
        pmn=ClienteContrato.objects.select_related().get(cliente=fact.cliente.id,cerrado=False)
        mncosto=pmn.contrato.preciocostomn
        cuccosto=pmn.contrato.preciocostocuc
    
        precio_CUP="Precio CUP"
        if(mncosto==True):
            precio_CUP=precio_CUP+"(Costo)"
                
        precio_CUC="Precio MLC"
        if (cuccosto==True):
            precio_CUC=precio_CUC+"(Costo)"
                    
        rc_observaciones=fact.doc_factura.observaciones
        filas = DetalleFactura.objects.select_related().filter(factura=idfa).order_by('casco_casco.casco_nro')
        rc_tipo='De Venta'
        if fact.tipo == 'O':
            rc_tipo='Otra'
        elif fact.tipo == 'A':
            rc_tipo='Ajuste'
        elif fact.tipo == 'K':
            rc_tipo='Vulca'
        rc_transportador=fact.transportador.nombre
        rc_chapa=fact.chapa
        rc_licencia=fact.licencia
        hay_cup=1
        hay_cuc=1
    # Verificar si se puede editar. Se puede editar si todos los cascos relacionados con el estado es Casco
    #editar=editar_documento(filas,idfa)
    
        return render_to_response('comercial/viewfacturaext.html',{'hay_cup':hay_cup,'hay_cuc':hay_cuc,'eliminar':0,'editar':1,'cancelar':0,'confirmar':0,'transportador':rc_transportador,'chapa':rc_chapa,
                                                            'licencia':fact.licencia,'transportador':rc_transportador,'chapa':rc_chapa,'precio_CUC':precio_CUC,
                                                            'precio_CUP':precio_CUP,'importecuc':importecuc,'importecup':importecup,
                                                            'tipo':rc_tipo,'rc_nro':rc_nro,'fecha':rc_fecha,'cliente':rc_cliente,
                                                            'observaciones':rc_observaciones,'rc_id':idfa,'elementos_detalle':filas, 
                                                            'error2':l},context_instance = RequestContext(request))
    try:
        filas = DetalleFactura.objects.filter(factura=idfa)
        for canti in filas:
            actualiza_traza(canti.casco.id_casco,idfa)
        
        Doc.objects.select_related().get(pk=idfa).delete()
        
        return HttpResponseRedirect('/comerciax/comercial/facturaext/index')
        #return render_to_response("casco/recepcionclienteindex.html",locals(),context_instance = RequestContext(request))
    except Exception,e:
        transaction.rollback()
        l = ['Error al eliminar el documento']
        fact = Facturas.objects.select_related().get(pk=idfa)
        rc_fecha=fact.doc_factura.fecha_doc.strftime("%d/%m/%Y")
        rc_cliente=fact.cliente.nombre
        rc_nro=fact.factura_nro
        rc_observaciones=fact.doc_factura.observaciones
        filas = DetalleFactura.objects.select_related().filter(factura=idfa).order_by('casco_casco.casco_nro')
       
        return render_to_response('comercial/viewfacturaext.html',{'hay_cup':hay_cup,'hay_cuc':hay_cuc,'rc_nro':rc_nro,'fecha':rc_fecha,'cliente':rc_cliente,'observaciones':rc_observaciones,'rc_id':idfa,'elementos_detalle':filas, 'error2':l},context_instance = RequestContext(request))
    else:
        transaction.commit()
 
    return 0


@login_required
@transaction.commit_on_success()
def facturaext_confirmar(request,idfa):
    if not request.user.has_perm('comercial.factura'):
        return render_to_response("denegado.html",locals(),context_instance = RequestContext(request))
#    Facturas.objects.filter(pk=idfa).update(confirmada=hashlib.sha1(idfa.__str__()+'YES').hexdigest())
    pk_user=User.objects.get(pk=request.user.id)
    
    nrodoc=1
    if NumeroDoc.objects.count()!=0:
        nrodoc=NumeroDoc.objects.get().nro_facturaext+1
    nume=NumeroDoc()
    if NumeroDoc.objects.count()==0:
        nume.id_numerodoc=uuid4()
    else:
        nume=NumeroDoc.objects.get()
    nume.nro_facturaext=nrodoc
    nume.save()
    Doc.objects.filter(pk=Facturas.objects.get(pk=idfa).doc_factura).update(operador=pk_user)
    Facturas.objects.filter(pk=idfa).update(confirmada=hashlib.sha1(idfa.__str__()+'YES').hexdigest(),factura_nro=nrodoc,confirmar=True)
    
    
    
#    Doc.objects.filter(pk=Facturas.objects.get(pk=idfa).doc_factura).update(operador=pk_user)
        
    #fact.confirmada=hashlib.sha1(pk_doc.__str__()+'NO').hexdigest()
    #return HttpResponseRedirect('/comerciax/comercial/facturaext/index') 
    return HttpResponseRedirect('/comerciax/comercial/facturaext/view/' + idfa)

@login_required
@transaction.commit_on_success()
def facturaext_imprimir(request,idfa):
    
    if not request.user.has_perm('comercial.factura'):
        return render_to_response("denegado.html",locals(),context_instance = RequestContext(request))
    
    l=[]
    fact=Facturas.objects.get(pk=idfa)
    if fact.confirmada != hashlib.sha1(fact.pk.__str__()+'YES').hexdigest():
        mensa="No se puede imprimir la factura Nro. "+fact.factura_nro+" porque no está confirmada"
        l=[mensa]
        rc_fecha=fact.doc_factura.fecha_doc.strftime("%d/%m/%Y")
        rc_cliente=fact.cliente.nombre
        rc_nro=fact.factura_nro
        importecup=Facturas.objects.get(pk=idfa).get_importecup()  
        importecuc=Facturas.objects.get(pk=idfa).get_importecuc() 
    
        pmn=ClienteContrato.objects.select_related().get(cliente=fact.cliente.id,cerrado=False)
        mncosto=pmn.contrato.preciocostomn
        cuccosto=pmn.contrato.preciocostocuc
    
        precio_CUP="Precio CUP"
        if(mncosto==True):
            precio_CUP=precio_CUP+"(Costo)"
                
        precio_CUC="Precio MLC"
        if (cuccosto==True):
            precio_CUC=precio_CUC+"(Costo)"
                    
        rc_observaciones=fact.doc_factura.observaciones
        filas = DetalleFactura.objects.select_related().filter(factura=idfa).order_by('casco_casco.casco_nro')
        rc_tipo='De Venta'
        if fact.tipo == 'O':
            rc_tipo='Otra'
        elif fact.tipo == 'A':
            rc_tipo='Ajuste'
        elif fact.tipo == 'K':
            rc_tipo='Vulca'
        rc_transportador=fact.transportador.nombre
        rc_chapa=fact.chapa
        rc_licencia=fact.licencia
    # Verificar si se puede editar. Se puede editar si todos los cascos relacionados con el estado es Casco
    #editar=editar_documento(filas,idfa)
        hay_cup=0
        hay_cuc=0
        return render_to_response('comercial/viewfacturaext.html',{'hay_cup':hay_cup,'hay_cuc':hay_cuc,'eliminar':0,'editar':1,'cancelar':0,'confirmar':0,'transportador':rc_transportador,'chapa':rc_chapa,
                                                            'transportador':rc_transportador,'chapa':rc_chapa,'licencia':rc_licencia,'precio_CUC':precio_CUC,
                                                            'precio_CUP':precio_CUP,'importecuc':importecuc,'importecup':importecup,
                                                            'tipo':rc_tipo,'rc_nro':rc_nro,'fecha':rc_fecha,'cliente':rc_cliente,
                                                            'observaciones':rc_observaciones,'rc_id':idfa,'elementos_detalle':filas, 
                                                            'error2':l},context_instance = RequestContext(request))

    return 0

@login_required
@transaction.commit_on_success()
def facturaext_cancelar(request,idfa):
    if not request.user.has_perm('comercial.factura'):
        return render_to_response("denegado.html",locals(),context_instance = RequestContext(request))
    
    l=[]
    fact=Facturas.objects.get(pk=idfa)
    
    pagosfact=PagosFacturas.objects.filter(facturas=fact).count()
    
    if fact.confirmada != hashlib.sha1(fact.pk.__str__()+'YES').hexdigest() or pagosfact!=0:
        mensa="No se puede cancelar la factura Nro. "+fact.factura_nro+" porque no está confirmada"
        if pagosfact>0:
            mensa="No se puede cancelar la factura Nro. "+fact.factura_nro+" porque se han realizado pagos"
        l=[mensa]
        rc_fecha=fact.doc_factura.fecha_doc.strftime("%d/%m/%Y")
        rc_cliente=fact.cliente.nombre
        rc_nro=fact.factura_nro
        importecup=Facturas.objects.get(pk=idfa).get_importecup()  
        importecuc=Facturas.objects.get(pk=idfa).get_importecuc()
    
        pmn=ClienteContrato.objects.select_related().get(cliente=fact.cliente.id,cerrado=False)
        mncosto=pmn.contrato.preciocostomn
        cuccosto=pmn.contrato.preciocostocuc
    
        precio_CUP="Precio CUP"
        if(mncosto==True):
            precio_CUP=precio_CUP+"(Costo)"
                
        precio_CUC="Precio MLC"
        if (cuccosto==True):
            precio_CUC=precio_CUC+"(Costo)"
                    
        rc_observaciones=fact.doc_factura.observaciones
        filas = DetalleFactura.objects.select_related().filter(factura=idfa).order_by('casco_casco.casco_nro')
        rc_tipo='De Venta'
        if fact.tipo == 'O':
            rc_tipo='Otra'
        elif fact.tipo == 'A':
            rc_tipo='Ajuste'
        elif fact.tipo == 'K':
            rc_tipo='Vulca'
        rc_transportador=fact.transportador.nombre
        rc_chapa=fact.chapa
        rc_licencia=fact.licencia
    # Verificar si se puede editar. Se puede editar si todos los cascos relacionados con el estado es Casco
    #editar=editar_documento(filas,idfa)
        hay_cup=1
        hay_cuc=1
        return render_to_response('comercial/viewfacturaext.html',{'hay_cup':hay_cup,'hay_cuc':hay_cuc,'eliminar':0,'editar':1,'cancelar':0,'confirmar':0,'transportador':rc_transportador,'chapa':rc_chapa,
                                                            'licencia':rc_licencia,'transportador':rc_transportador,'precio_CUC':precio_CUC,
                                                            'precio_CUP':precio_CUP,'importecuc':importecuc,'importecup':importecup,
                                                            'tipo':rc_tipo,'rc_nro':rc_nro,'fecha':rc_fecha,'cliente':rc_cliente,
                                                            'observaciones':rc_observaciones,'rc_id':idfa,'elementos_detalle':filas, 
                                                            'error2':l},context_instance = RequestContext(request))

    try:
        
        filas = DetalleFactura.objects.filter(factura=idfa)
        for canti in filas:
            actualiza_traza(canti.casco.id_casco,idfa)
        Facturas.objects.filter(pk=idfa).update(cancelada=True)
        pk_user=User.objects.get(pk=request.user.id)
        Doc.objects.filter(pk=Facturas.objects.get(pk=idfa).doc_factura).update(operador=pk_user)
            
        #Doc.objects.select_related().get(pk=idfa).delete()
        return HttpResponseRedirect('/comerciax/comercial/facturaext/index')
        #return render_to_response("casco/recepcionclienteindex.html",locals(),context_instance = RequestContext(request))
    except Exception,e :
        transaction.rollback()
        l = ['Error al cancelar factura']
        fact = Facturas.objects.select_related().get(pk=idfa)
        importecup=Facturas.objects.get(pk=idfa).get_importecup()  
        importecuc=Facturas.objects.get(pk=idfa).get_importecuc()
    
        rc_fecha=fact.doc_factura.fecha_doc.strftime("%d/%m/%Y")
        rc_cliente=fact.cliente.nombre
        rc_transportador=fact.transportador.nombre
        rc_nro=fact.factura_nro
        rc_observaciones=fact.doc_factura.observaciones
        rc_chapa=fact.chapa
        rc_licencia=fact.licencia
        rc_tipo='De Venta'
        if fact.tipo == 'O':
            rc_tipo='Otra'
        elif fact.tipo == 'A':
            rc_tipo='Ajuste'
        elif fact.tipo == 'K':
            rc_tipo='Vulca'
        
        filas = DetalleFactura.objects.select_related().filter(factura=idfa).order_by('casco_casco.casco_nro')
        pmn=ClienteContrato.objects.select_related().get(cliente=fact.cliente.id,cerrado=False)
        mncosto=pmn.contrato.preciocostomn
        cuccosto=pmn.contrato.preciocostocuc
    
        precio_CUP="Precio CUP"
        if(mncosto==True):
            precio_CUP=precio_CUP+"(Costo)"
                
        precio_CUC="Precio MLC"
        if (cuccosto==True):
            precio_CUC=precio_CUC+"(Costo)"
  
        return render_to_response('comercial/viewfacturaext.html',{'hay_cup':hay_cup,'hay_cuc':hay_cuc,'transportador':rc_transportador,'chapa':rc_chapa,'licencia':rc_licencia,'transportador':rc_transportador,'precio_CUC':precio_CUC,
                                                            'precio_CUP':precio_CUP,'importecuc':importecuc,'importecup':importecup,
                                                            'tipo':rc_tipo,'rc_nro':rc_nro,'fecha':rc_fecha,'cliente':rc_cliente,
                                                            'observaciones':rc_observaciones,'rc_id':idfa,'elementos_detalle':filas, 
                                                            'error2':l},context_instance = RequestContext(request))
    else:
        transaction.commit()
 
#===============================================================================
# FACTURA ENTIDADES
#===============================================================================
@login_required
def get_fact_list(request):
    #prepare the params
    try:
        fecha_desde=Fecha_Ver.objects.get()
    except Exception, e:
        fecha_desde=None
    if  fecha_desde == None:  
        querySet = Facturas.objects.select_related().filter(cliente__externo=False)
    else:
        querySet = Facturas.objects.select_related().filter(cliente__externo=False,doc_factura__fecha_doc__gte=fecha_desde.fecha)
    #querySet = querySet.filter(doc__fecha_doc__year=2010)

    columnIndexNameMap = {0:'-doc_factura__fecha_doc',1:'factura_nro',2:'admincomerciax_cliente.nombre',
                          3:'doc_factura__fecha_doc',
                          4:'tipo',5:'cancelada',6:'confirmar'}

    # columnIndexNameMap = {}
    #{0: 'oferta_nro',1: 'oferta_nro',2:'admincomerciax_cliente.nombre',3:'doc_oferta__fecha_oferta',4:'oferta_tipo'}

    searchableColumns = ['confirmar', 'cancelada', 'factura_nro','cliente__nombre','doc_factura__fecha_doc']
    #path to template used to generate json
    jsonTemplatePath = 'comercial/json/json_factura.txt'

    #call to generic function from utils
    return get_datatables_records(request, querySet, columnIndexNameMap, searchableColumns, jsonTemplatePath)

    

@login_required
def factura_index(request):
    if not request.user.has_perm('comercial.factura'):
        return render_to_response("denegado.html",locals(),context_instance = RequestContext(request))
    return render_to_response('comercial/facturaindex.html',locals(),context_instance = RequestContext(request))
    
@login_required
@transaction.commit_on_success()
def factura_add(request):
    if not request.user.has_perm('comercial.factura'):
        return render_to_response("denegado.html",locals(),context_instance = RequestContext(request))
    
    nombre_form='Facturas'
    descripcion_form='Realizar Factura'
    titulo_form='Facturas' 
    controlador_form='Facturas'
    accion_form='/comerciax/comercial/factura/add'
    cancelbtn_form='/comerciax/comercial/factura/index'
    fecha_hoy=datetime.date.today().strftime("%d/%m/%Y")
    fecha_cierre=Fechacierre.objects.get(almacen='cm').fechaminima()
    fecha_maxima=Fechacierre.objects.get(almacen='cm').fechamaxima()
    c=None
    l=[]
    if request.method == 'POST':
        form = FacturaForm(request.POST)
        if form.is_valid():
            tipo=form.cleaned_data['tipo']
            obj_cliente = Cliente.objects.get(pk = form.data['cliente1'])
            #cliente = Cliente.objects.get(id = cliente_id)
             
            try:
                tipoc=obj_cliente.get_contrato_tipo()
            except Exception, e:
                tipoc=None
            
            if tipoc==None:
                l=['Este cliente no tiene contrato por lo que no se puede realizar la factura']
                return render_to_response('comercial/facturaadd.html',  {'form': form, 'form_name':nombre_form,
                                                                         'form_description':descripcion_form,'accion':accion_form,
                                                                         'titulo':titulo_form,'controlador':controlador_form,
                                                                         'cancelbtn':cancelbtn_form,'fecha_minima':fecha_cierre,'fecha_maxima':fecha_maxima,
                                                                         'error2':l},context_instance = RequestContext(request))
               
            if (tipoc==True) and (tipo=='A' or tipo=='O'):
                l=['Este cliente tiene contrato para venta el tipo de factura seleccionada es incorrecto']
                return render_to_response('comercial/facturaadd.html',  {'form': form, 'form_name':nombre_form,
                                                                         'form_description':descripcion_form,'accion':accion_form,
                                                                         'titulo':titulo_form,'controlador':controlador_form,
                                                                         'cancelbtn':cancelbtn_form,'fecha_minima':fecha_cierre,'fecha_maxima':fecha_maxima,
                                                                         'error2':l},context_instance = RequestContext(request))
                  
            pk_user=User.objects.get(pk=request.user.id)
            
            fact=Facturas()
            
            pk_doc=uuid4()
            obj_doc=Doc()
            
            obj_doc.id_doc=pk_doc
            obj_doc.tipo_doc='14'
            obj_doc.fecha_doc=form.cleaned_data['fecha']
            obj_doc.operador=pk_user
            obj_doc.fecha_operacion=datetime.date.today()
            obj_doc.observaciones=form.cleaned_data['observaciones']
            
            fact.doc_factura = obj_doc
            fact.factura_nro=str(random.randint(1,100000))+"S/C"
            fact.cliente=Cliente.objects.get(pk = form.data['cliente1'])
            fact.tipo=tipo
            fact.confirmada=hashlib.sha1(pk_doc.__str__()+'NO').hexdigest()

            fact.chapa=form.cleaned_data['chapa']
            fact.licencia=form.cleaned_data['licencia']
            fact.transportador=Transpotador.objects.get(pk = form.data['transportador']) 
         
            try:
                obj_doc.save()
                fact.save()
#                nume.save() 
                return HttpResponseRedirect('/comerciax/comercial/factura/view/'+pk_doc.__str__())  
            except Exception, e:
                exc_info = e.__str__() # sys.exc_info()[:1]
                c = exc_info.find("DETAIL:")
                
                if c < 0:
                    l=l+["Error Fatal."]
                else:
                    c = exc_info[c + 7:]
                    l=l+[c] 
                                     
                transaction.rollback()
                form = FacturaForm(request.POST)
                return render_to_response('comercial/facturaadd.html',  {'form': form, 'form_name':nombre_form,'form_description':descripcion_form,
                                                                         'accion':accion_form,'titulo':titulo_form,'controlador':controlador_form,
                                                                         'cancelbtn':cancelbtn_form,'fecha_minima':fecha_cierre,'fecha_maxima':fecha_maxima,'error2':l},context_instance = RequestContext(request))
            else:
                transaction.commit()
    else:
#        nrodoc=random.randint(1,100000)
#        if NumeroDoc.objects.count()!=0:
#            nrodoc=NumeroDoc.objects.get().nro_factura+1
        meshoy=int(fecha_hoy.split('/')[1])
        mescierre=int(fecha_cierre.split('/')[1])
        
        if meshoy==mescierre:
            fecha_cierre=fecha_hoy
        form =FacturaForm(initial={'fecha':fecha_cierre}) 
    
    return render_to_response('comercial/facturaadd.html',  {'form': form, 'form_name':nombre_form,'form_description':descripcion_form,
                                                             'accion':accion_form,'titulo':titulo_form,'controlador':controlador_form,
                                                             'cancelbtn':cancelbtn_form,'fecha_minima':fecha_cierre,'fecha_maxima':fecha_maxima,'error2':c},context_instance = RequestContext(request))


@login_required
@transaction.commit_on_success()
def factura_edit(request,idfa):
    if not request.user.has_perm('comercial.factura'):
        return render_to_response("denegado.html",locals(),context_instance = RequestContext(request))
    
    fact=Facturas.objects.select_related().get(pk=idfa)
    noedit=0
    if fact.confirmada == hashlib.sha1(fact.pk.__str__()+'YES').hexdigest():
        mensa="No se puede editar la factura Nro. "+fact.factura_nro+" porque ya está confirmada"
        noedit=1
    elif fact.confirmada != hashlib.sha1(fact.pk.__str__()+'NO').hexdigest():
        mensa="No se puede editar la factura Nro. "+fact.factura_nro+" porque está corrupta"
        noedit=1
        #return HttpResponseRedirect('/comerciax/comercial/factura/view/'+idfa) 
    if noedit==1:
        l=[mensa]
        rc_fecha=fact.doc_factura.fecha_doc.strftime("%d/%m/%Y")
        rc_cliente=fact.cliente.nombre
        rc_nro=fact.factura_nro

        importecup=Facturas.objects.get(pk=idfa).get_importecup()
        importecuc=Facturas.objects.get(pk=idfa).get_importecuc()
        
        
        pmn=ClienteContrato.objects.select_related().get(cliente=fact.cliente.id,cerrado=False)
        mncosto=pmn.contrato.preciocostomn
        cuccosto=pmn.contrato.preciocostocuc
    
        precio_CUP="Precio CUP"
        if(mncosto==True):
            precio_CUP=precio_CUP+"(Costo)"
                
        precio_CUC="Precio MLC"
        if (cuccosto==True):
            precio_CUC=precio_CUC+"(Costo)"
                    
        rc_observaciones=fact.doc_factura.observaciones
        filas = DetalleFactura.objects.select_related().filter(factura=idfa).order_by('casco_casco.casco_nro')
        rc_tipo='De Venta'
        if fact.tipo == 'O':
            rc_tipo='Otra'
        elif fact.tipo == 'A':
            rc_tipo='Ajuste'
        elif fact.tipo == 'K':
            rc_tipo='Vulca'
        elif fact.tipo == 'R':
            rc_tipo='Regrabable'
        rc_transportador=fact.transportador.nombre
        rc_chapa=fact.chapa
        rc_licencia=fact.licencia
        hay_cup=0
        hay_cuc=0
        
    # Verificar si se puede editar. Se puede editar si todos los cascos relacionados con el estado es Casco
    #editar=editar_documento(filas,idfa)
    
        return render_to_response('comercial/viewfactura.html',{'hay_cup':hay_cup,'hay_cuc':hay_cuc,'eliminar':0,'editar':1,'cancelar':0,'confirmar':0,'transportador':rc_transportador,'chapa':rc_chapa,
                                                            'transportador':rc_transportador,'licencia':rc_licencia,'precio_CUC':precio_CUC,
                                                            'precio_CUP':precio_CUP,'importecuc':importecuc,'importecup':importecup,
                                                            'tipo':rc_tipo,'rc_nro':rc_nro,'fecha':rc_fecha,'cliente':rc_cliente,
                                                            'observaciones':rc_observaciones,'rc_id':idfa,'elementos_detalle':filas, 
                                                            'error2':l},context_instance = RequestContext(request))

    nombre_form='Facturas'
    descripcion_form='Realizar Factura a Clientes'
    titulo_form='Facturas' 
    controlador_form='Facturas'
    accion_form='/comerciax/comercial/factura/edit/'+ idfa +'/'
    cancelbtn_form='/comerciax/comercial/factura/view/'+ idfa +'/'
    fecha_cierre=Fechacierre.objects.get(almacen='cm').fechaminima()
    fecha_maxima=Fechacierre.objects.get(almacen='cm').fechamaxima()
    c=None
    
#    fact = Facturas.objects.select_related().get(pk=idfa)
    l=[]
#    for a in fecham:
#        fecha_cierre=a.fechacierre.strftime("%d/%m/%Y")
        
    detalles=DetalleFactura.objects.filter(factura=idfa).count() 
      
    if request.method == 'POST':
        tipo=fact.tipo
        if detalles==0:
            form = FacturaForm(request.POST)
#        elif tipo=='V':
#            form = FacturaForm1(request.POST)
        else:
            form = FacturaForm2(request.POST)
        #rajuste = form.cleaned_data['ajuste']
        if form.is_valid():
            if detalles==0:
                cc=form.data['cliente1']
            else:
                cc=form.data['cliente']
            if (cc.find("|") < 0):
                obj_cliente = Cliente.objects.get(pk = cc)
            else:
                obj_cliente= Cliente.objects.get(pk = fact.cliente.id)
            try:
                tipoc=obj_cliente.get_contrato_tipo()
            except Exception, e:
                tipoc=None
            
            if tipoc==None:
                l=['Este cliente no tiene contrato por lo que no se puede realizar la factura']
                return render_to_response('form/form_adddetalle.html',  {'tipocliente':'0','form': form, 'form_name':nombre_form,
                                                                         'form_description':descripcion_form,'accion':accion_form,
                                                                         'titulo':titulo_form,'controlador':controlador_form,
                                                                         'cancelbtn':cancelbtn_form,'fecha_minima':fecha_cierre,'fecha_maxima':fecha_maxima,
                                                                         'error2':l},context_instance = RequestContext(request))
            tipo=form.cleaned_data['tipo']  
            if  form.cleaned_data['tipo']=='De Venta':
                tipo='V'
            elif form.cleaned_data['tipo']=='De Ajuste':
                tipo='A'
            elif form.cleaned_data['tipo']=='Otra':
                tipo='O'
                
            if (tipoc==True) and (tipo=='A' or tipo=='O'):
                l=['Este cliente tiene contrato para venta el tipo de factura seleccionada es incorrecto']
                return render_to_response('form/form_adddetalle.html',  {'tipocliente':'0','form': form, 'form_name':nombre_form,
                                                                         'form_description':descripcion_form,'accion':accion_form,
                                                                         'titulo':titulo_form,'controlador':controlador_form,
                                                                         'cancelbtn':cancelbtn_form,'fecha_minima':fecha_cierre,'fecha_maxima':fecha_maxima,
                                                                         'error2':l},context_instance = RequestContext(request))
                  
            
            pk_user=User.objects.get(pk=request.user.id)
            
            fact=Facturas.objects.get(pk=idfa)
            doc=Doc.objects.get(pk=idfa)
            
#            fact.factura_nro=form.cleaned_data['nro'] 
            doc.fecha_doc=form.cleaned_data['fecha']
            doc.operador=pk_user
            doc.doc_operacion=datetime.date.today()
            doc.observaciones=form.cleaned_data['observaciones']         
            fact.cliente=obj_cliente
            fact.transportador=Transpotador.objects.get(pk=form.data['transportador'])
            fact.tipo=tipo
            fact.chapa=form.cleaned_data['chapa']
            fact.licencia=form.cleaned_data['licencia']
         
            try:
                doc.save()
                fact.save() 
 
                return HttpResponseRedirect('/comerciax/comercial/factura/view/'+idfa)  

            except Exception, e:
                exc_info = e.__str__() # sys.exc_info()[:1]
                c = exc_info.find("DETAIL:")
                
                if c < 0:
                    l=l+["Error Fatal."]
                else:
                    c = exc_info[c + 7:]
                    l=l+[c]
                    
                transaction.rollback()
                
                form = FacturaForm(request.POST)
                return render_to_response('form/form_adddetalle.html',  {'tipocliente':'0','form': form, 'form_name':nombre_form,'form_description':descripcion_form,
                                                                         'accion':accion_form,'titulo':titulo_form,'controlador':controlador_form,
                                                                         'cancelbtn':cancelbtn_form,'fecha_minima':fecha_cierre,'fecha_maxima':fecha_maxima,'error2':l},context_instance = RequestContext(request))
            else:
                transaction.commit()     
    else:
#        fact = Facturas.objects.select_related().get(pk=idfa)
        tipo=fact.tipo
        if detalles==0:
            form = FacturaForm(initial={'transportador':fact.transportador,'chapa':fact.chapa,'licencia':fact.licencia,'tipo':fact.tipo,'nro':fact.factura_nro,'fecha':fact.doc_factura.fecha_doc,
                                            'cliente1':fact.cliente,'observaciones':fact.doc_factura.observaciones})
        else:
            rc_tipo='De Ajuste'
            if fact.tipo == 'O':
                rc_tipo='Otra'
            form = FacturaForm2(initial={'transportador':fact.transportador,
                                         'licencia':fact.licencia,
                                         'chapa':fact.chapa,'tipo':rc_tipo,'nro':fact.factura_nro,'fecha':fact.doc_factura.fecha_doc,
                                         'cliente':fact.cliente,
                                         'transportador':fact.transportador,
                                         'observaciones':fact.doc_factura.observaciones})
        
    return render_to_response('comercial/facturaedit.html',  {'form': form, 'form_name':nombre_form,'form_description':descripcion_form,
                                                       'accion':accion_form,'titulo':titulo_form,'controlador':controlador_form,
                                                       'cancelbtn':cancelbtn_form,'fecha_minima':fecha_cierre,'fecha_maxima':fecha_maxima},context_instance = RequestContext(request))

@login_required
def factura_view(request,idfa):
    if not request.user.has_perm('comercial.factura'):
        return render_to_response("denegado.html",locals(),context_instance = RequestContext(request))
    
    l=[]
    cancelar=0
    fact = Facturas.objects.select_related().get(pk=idfa)
    if fact.cancelada==True:
        cancelar=1
    confir=fact.get_confirmada()
    confirmar=2
    if confir=='N':
        confirmar=0
    elif confir=='S':
        confirmar=1

    eliminar=1
    editar=1
    if confirmar==2 or confirmar==1:
        eliminar=0  
        editar=0
     
    rc_fecha=fact.doc_factura.fecha_doc.strftime("%d/%m/%Y")
    rc_cliente=fact.cliente.nombre
    rc_nro=fact.factura_nro
    importecup=Facturas.objects.get(pk=idfa).get_importetotalcup()
    importecuc=Facturas.objects.get(pk=idfa).get_importecuc()   
    cant_cascos=Facturas.objects.get(pk=idfa).cantidad_casco() 
    importecasco=Facturas.objects.get(pk=idfa).get_importe_venta()
    cant_renglones=Facturas.objects.get(pk=idfa).get_renglones() 
    pmn=ClienteContrato.objects.select_related().get(cliente=fact.cliente.id,cerrado=False)
    mncosto=pmn.contrato.preciocostomn
    cuccosto=pmn.contrato.preciocostocuc
    
    precio_CUP="Precio CUP"
    if(mncosto==True):
        precio_CUP=precio_CUP+"(Costo)"
                
    precio_CUC="Precio MLC"
    if (cuccosto==True):
        precio_CUC=precio_CUC+"(Costo)"
                    
    rc_observaciones=fact.doc_factura.observaciones
    filas = DetalleFactura.objects.select_related().filter(factura=idfa).order_by('casco__producto_salida__descripcion','casco__casco_nro')
    rc_tipo='De Venta'
    if fact.tipo == 'O':
        rc_tipo='Otra'
    elif fact.tipo == 'A':
        rc_tipo='Ajuste'
    elif fact.tipo == 'K':
        rc_tipo='Vulca'
    elif fact.tipo == 'R':
        rc_tipo = 'Regrabable'
    rc_transportador=fact.transportador.nombre
    rc_chapa=fact.chapa
    rc_licencia=fact.licencia
    hay_cup=1
    hay_cuc=1
    
    
    elementos_detalle=[]
    id1=''
    k=0
    k2=0
    t_preciocuc=0.0
    t_preciocup=0.0  
    t_preciocasco=0.0  
    
    for a1 in filas:
        if k!=0:
            if id1!=a1.casco.producto_salida.id:
                elementos_detalle[k-1]['cantidad'] = k2
                elementos_detalle[k-1]['t_preciocuc'] = t_preciocuc
                elementos_detalle[k-1]['t_preciocup'] = t_preciocup
                elementos_detalle[k-1]['t_preciocasco'] = t_preciocasco
                t_preciocuc=0.0
                t_preciocup=0.0 
                t_preciocasco=0.0
                k2=0
        elementos_detalle+=[{'casco_id':a1.casco.id_casco,
                             'casco_nro':a1.casco.casco_nro,'productosalida':a1.casco.producto_salida.descripcion,
                             'productoid':a1.casco.producto.id,'precio_cup':a1.format_precio_mn(),
                             'precio_cuc':a1.format_precio_cuc(),'precio_casco':a1.format_precio_casco()}]
        k+=1
        k2+=1
        t_preciocup+=float(a1.precio_mn)
        t_preciocuc+=float(a1.precio_cuc)
        t_preciocasco+=float(a1.precio_casco)
        id1=a1.casco.producto_salida.id  
    if k!=0:
        elementos_detalle[k-1]['cantidad'] = k2    
        elementos_detalle[k-1]['t_preciocuc'] = t_preciocuc
        elementos_detalle[k-1]['t_preciocup'] = t_preciocup
        elementos_detalle[k-1]['t_preciocasco'] = t_preciocasco
    return render_to_response('comercial/viewfactura.html',{'total_casco':k,'hay_cup':hay_cup,'hay_cuc':hay_cuc,
                                                            'eliminar':eliminar,'editar':editar,'cancelar':cancelar,
                                                            'confirmar':confirmar,'transportador':rc_transportador,
                                                            'chapa':rc_chapa,'precio_CUC':precio_CUC,'importecasco':importecasco,
                                                            'transportador':rc_transportador,'licencia':rc_licencia,
                                                            'precio_CUP':precio_CUP,'importecuc':importecuc,'importecup':importecup,
                                                            'tipo':rc_tipo,'rc_nro':rc_nro,'fecha':rc_fecha,'cliente':rc_cliente,
                                                            'observaciones':rc_observaciones,'rc_id':idfa,'elementos_detalle':elementos_detalle, 
                                                            'error2':l,'cant_cascos':cant_cascos,'cant_renglones':cant_renglones},context_instance = RequestContext(request))

@login_required
@transaction.commit_on_success()
def factura_del(request,idfa):
    if not request.user.has_perm('comercial.factura'):
        return render_to_response("denegado.html",locals(),context_instance = RequestContext(request))
    
    l=[]
    fact=Facturas.objects.get(pk=idfa)
    noelim=0
    if fact.confirmada == hashlib.sha1(fact.pk.__str__()+'YES').hexdigest():
        mensa="No se puede eliminar la factura Nro. "+fact.factura_nro+" porque ya está confirmada"
        noelim=1
    elif fact.confirmada != hashlib.sha1(fact.pk.__str__()+'NO').hexdigest():
        mensa="No se puede eliminar la factura Nro. "+fact.factura_nro+" porque está corrupta"
        noelim=1
        #return HttpResponseRedirect('/comerciax/comercial/factura/view/'+idfa) 
    if noelim==1:
        l=[mensa]
        rc_fecha=fact.doc_factura.fecha_doc.strftime("%d/%m/%Y")
        rc_cliente=fact.cliente.nombre
        rc_nro=fact.factura_nro
        importecup=Facturas.objects.get(pk=idfa).get_importetotalcup()  
        importecuc=Facturas.objects.get(pk=idfa).get_importecuc() 
    
        pmn=ClienteContrato.objects.select_related().get(cliente=fact.cliente.id,cerrado=False)
        mncosto=pmn.contrato.preciocostomn
        cuccosto=pmn.contrato.preciocostocuc
    
        precio_CUP="Precio CUP"
        if(mncosto==True):
            precio_CUP=precio_CUP+"(Costo)"
                
        precio_CUC="Precio MLC"
        if (cuccosto==True):
            precio_CUC=precio_CUC+"(Costo)"
                    
        rc_observaciones=fact.doc_factura.observaciones
        filas = DetalleFactura.objects.select_related().filter(factura=idfa).order_by('casco_casco.casco_nro')
        rc_tipo='De Venta'
        if fact.tipo == 'O':
            rc_tipo='Otra'
        elif fact.tipo == 'A':
            rc_tipo='Ajuste'
        elif fact.tipo == 'K':
            rc_tipo='Vulca'
        elif fact.tipo == 'R':
            rc_tipo='Regrabable'
        rc_transportador=fact.transportador.nombre
        rc_chapa=fact.chapa
        rc_licencia=fact.licencia
        hay_cup=1
        hay_cuc=1
    # Verificar si se puede editar. Se puede editar si todos los cascos relacionados con el estado es Casco
    #editar=editar_documento(filas,idfa)
    
        return render_to_response('comercial/viewfactura.html',{'hay_cup':hay_cup,'hay_cuc':hay_cuc,'eliminar':0,'editar':1,'cancelar':0,'confirmar':0,'transportador':rc_transportador,'chapa':rc_chapa,
                                                            'licencia':fact.licencia,'transportador':rc_transportador,'chapa':rc_chapa,'precio_CUC':precio_CUC,
                                                            'precio_CUP':precio_CUP,'importecuc':importecuc,'importecup':importecup,
                                                            'tipo':rc_tipo,'rc_nro':rc_nro,'fecha':rc_fecha,'cliente':rc_cliente,
                                                            'observaciones':rc_observaciones,'rc_id':idfa,'elementos_detalle':filas, 
                                                            'error2':l},context_instance = RequestContext(request))
    try:
        filas = DetalleFactura.objects.filter(factura=idfa)
        for canti in filas:
            actualiza_traza(canti.casco.id_casco,idfa)
        
        Doc.objects.select_related().get(pk=idfa).delete()
        
        return HttpResponseRedirect('/comerciax/comercial/factura/index')
        #return render_to_response("casco/recepcionclienteindex.html",locals(),context_instance = RequestContext(request))
    except Exception,e:
        transaction.rollback()
        l = ['Error al eliminar el documento']
        fact = Facturas.objects.select_related().get(pk=idfa)
        rc_fecha=fact.doc_factura.fecha_doc.strftime("%d/%m/%Y")
        rc_cliente=fact.cliente.nombre
        rc_nro=fact.factura_nro
        rc_observaciones=fact.doc_factura.observaciones
        filas = DetalleFactura.objects.select_related().filter(factura=idfa).order_by('casco_casco.casco_nro')
       
        return render_to_response('comercial/viewfactura.html',{'hay_cup':hay_cup,'hay_cuc':hay_cuc,'rc_nro':rc_nro,'fecha':rc_fecha,'cliente':rc_cliente,'observaciones':rc_observaciones,'rc_id':idfa,'elementos_detalle':filas, 'error2':l},context_instance = RequestContext(request))
    else:
        transaction.commit()
 
    return 0


@login_required
@transaction.commit_on_success()
def factura_confirmar(request,idfa):
    if not request.user.has_perm('comercial.factura'):
        return render_to_response("denegado.html",locals(),context_instance = RequestContext(request))
    
    l=[]
    fact=Facturas.objects.get(pk=idfa)
    if fact.get_renglones()>30:
        l=[]
        cancelar=0
        fact = Facturas.objects.select_related().get(pk=idfa)
        if fact.cancelada==True:
            cancelar=1
        confir=fact.get_confirmada()
        confirmar=2
        if confir=='N':
            confirmar=0
        elif confir=='S':
            confirmar=1
    
        eliminar=1
        editar=1
        if confirmar==2 or confirmar==1:
            eliminar=0  
            editar=0
         
        rc_fecha=fact.doc_factura.fecha_doc.strftime("%d/%m/%Y")
        rc_cliente=fact.cliente.nombre
        rc_nro=fact.factura_nro
        importecup=Facturas.objects.get(pk=idfa).get_importetotalcup()
        importecuc=Facturas.objects.get(pk=idfa).get_importecuc()   
        cant_cascos=Facturas.objects.get(pk=idfa).cantidad_casco() 
        cant_renglones=Facturas.objects.get(pk=idfa).get_renglones()
        pmn=ClienteContrato.objects.select_related().get(cliente=fact.cliente.id,cerrado=False)
        mncosto=pmn.contrato.preciocostomn
        cuccosto=pmn.contrato.preciocostocuc
        
        precio_CUP="Precio CUP"
        if(mncosto==True):
            precio_CUP=precio_CUP+"(Costo)"
                    
        precio_CUC="Precio MLC"
        if (cuccosto==True):
            precio_CUC=precio_CUC+"(Costo)"
                        
        rc_observaciones=fact.doc_factura.observaciones
        filas = DetalleFactura.objects.select_related().filter(factura=idfa).order_by('casco__producto_salida__descripcion','casco_casco.casco_nro')
        rc_tipo='De Venta'
        if fact.tipo == 'O':
            rc_tipo='Otra'
        elif fact.tipo == 'A':
            rc_tipo='Ajuste'
        elif fact.tipo == 'K':
            rc_tipo='Vulca'
        elif fact.tipo == 'R':
            rc_tipo='Regrabable'
        rc_transportador=fact.transportador.nombre
        rc_chapa=fact.chapa
        rc_licencia=fact.licencia
        hay_cup=1
        hay_cuc=1
        l=["La factura excede los 30 renglones, no se puede confirmar"]
        return render_to_response('comercial/viewfactura.html',{'hay_cup':hay_cup,'hay_cuc':hay_cuc,'eliminar':eliminar,'editar':editar,'cancelar':cancelar,'confirmar':confirmar,'transportador':rc_transportador,'chapa':rc_chapa,
                                                            'transportador':rc_transportador,'chapa':rc_chapa,'licencia':rc_licencia,'precio_CUC':precio_CUC,
                                                            'precio_CUP':precio_CUP,'importecuc':importecuc,'importecup':importecup,
                                                            'tipo':rc_tipo,'rc_nro':rc_nro,'fecha':rc_fecha,'cliente':rc_cliente,
                                                            'observaciones':rc_observaciones,'rc_id':idfa,'elementos_detalle':filas, 
                                                            'error2':l,'cant_cascos':cant_cascos,'cant_renglones':cant_renglones},context_instance = RequestContext(request))

    else:
        
        pk_user=User.objects.get(pk=request.user.id)
        nrodoc=1
        if NumeroDoc.objects.count()!=0:
            nrodoc=NumeroDoc.objects.get().nro_factura+1
        nume=NumeroDoc()
        if NumeroDoc.objects.count()==0:
            nume.id_numerodoc=uuid4()
        else:
            nume=NumeroDoc.objects.get()
        nume.nro_factura=nrodoc
        nume.save()
        Doc.objects.filter(pk=Facturas.objects.get(pk=idfa).doc_factura).update(operador=pk_user)
        Facturas.objects.filter(pk=idfa).update(confirmada=hashlib.sha1(idfa.__str__()+'YES').hexdigest(),factura_nro=nrodoc,confirmar=True)  
        #fact.confirmada=hashlib.sha1(pk_doc.__str__()+'NO').hexdigest()
        #return HttpResponseRedirect('/comerciax/comercial/factura/index') 
        return HttpResponseRedirect('/comerciax/comercial/factura/view/' + idfa)

@login_required
@transaction.commit_on_success()
def factura_imprimir(request,idfa):
    
    if not request.user.has_perm('comercial.factura'):
        return render_to_response("denegado.html",locals(),context_instance = RequestContext(request))
    
    l=[]
    fact=Facturas.objects.get(pk=idfa)
    if fact.confirmada != hashlib.sha1(fact.pk.__str__()+'YES').hexdigest():
        mensa="No se puede imprimir la factura Nro. "+fact.factura_nro+" porque no está confirmada"
        l=[mensa]
        rc_fecha=fact.doc_factura.fecha_doc.strftime("%d/%m/%Y")
        rc_cliente=fact.cliente.nombre
        rc_nro=fact.factura_nro
        importetotalcup=Facturas.objects.get(pk=idfa).get_importetotalcup()  
        importecuc=Facturas.objects.get(pk=idfa).get_importecuc()
        importecup=Facturas.objects.get(pk=idfa).get_importecup()
        importe_venta=Facturas.objects.get(pk=idfa).get_importe_venta()
    
        pmn=ClienteContrato.objects.select_related().get(cliente=fact.cliente.id,cerrado=False)
        mncosto=pmn.contrato.preciocostomn
        cuccosto=pmn.contrato.preciocostocuc
    
        precio_CUP="Precio CUP"
        if(mncosto==True):
            precio_CUP=precio_CUP+"(Costo)"
                
        precio_CUC="Precio MLC"
        if (cuccosto==True):
            precio_CUC=precio_CUC+"(Costo)"
                    
        rc_observaciones=fact.doc_factura.observaciones
        filas = DetalleFactura.objects.select_related().filter(factura=idfa).order_by('casco_casco.casco_nro')
        filas.__len__()
        filas2 = DetalleFactura.objects.select_related().filter(factura=idfa,casco__venta=True,casco__decomisado=False).order_by('casco_casco.casco_nro')
        hay_venta=True
        if filas.__len__()==0:
            hay_venta=False
        rc_tipo='De Venta'
        if fact.tipo == 'O':
            rc_tipo='Otra'
        elif fact.tipo == 'A':
            rc_tipo='Ajuste'
        elif fact.tipo == 'K':
            rc_tipo='Vulca'
        elif fact.tipo == 'R':
            rc_tipo='Regrabable'
        rc_transportador=fact.transportador.nombre
        rc_chapa=fact.chapa
        rc_licencia=fact.licencia
    # Verificar si se puede editar. Se puede editar si todos los cascos relacionados con el estado es Casco
    #editar=editar_documento(filas,idfa)
        hay_cup=0
        hay_cuc=0
        return render_to_response('comercial/viewfactura.html',{'hay_cup':hay_cup,'hay_cuc':hay_cuc,'eliminar':0,'editar':1,'cancelar':0,'confirmar':0,'transportador':rc_transportador,'chapa':rc_chapa,
                                                            'transportador':rc_transportador,'chapa':rc_chapa,'licencia':rc_licencia,'precio_CUC':precio_CUC,'hay_venta':hay_venta,
                                                            'precio_CUP':precio_CUP,'importecuc':importecuc,'importecup':importecup,'importetotalcup':importetotalcup,
                                                            'importe_venta':importe_venta,'tipo':rc_tipo,'rc_nro':rc_nro,'fecha':rc_fecha,'cliente':rc_cliente,
                                                            'observaciones':rc_observaciones,'rc_id':idfa,'elementos_detalle':filas,'elementos_detalleventa':filas2,
                                                            'error2':l},context_instance = RequestContext(request))
    return 0

@login_required
@transaction.commit_on_success()
def factura_cancelar(request,idfa):
    if not request.user.has_perm('comercial.factura'):
        return render_to_response("denegado.html",locals(),context_instance = RequestContext(request))
    
    l=[]
    fact=Facturas.objects.get(pk=idfa)
    pagosfact=PagosFacturas.objects.filter(facturas=fact).count()
    if fact.confirmada != hashlib.sha1(fact.pk.__str__()+'YES').hexdigest() or pagosfact!=0:
        mensa="No se puede cancelar la factura Nro. "+fact.factura_nro+" porque no está confirmada"
        if pagosfact>0:
            mensa="No se puede cancelar la factura Nro. "+fact.factura_nro+" porque se han realizado pagos"
        l=[mensa]
        rc_fecha=fact.doc_factura.fecha_doc.strftime("%d/%m/%Y")
        rc_cliente=fact.cliente.nombre
        rc_nro=fact.factura_nro
        importecup=Facturas.objects.get(pk=idfa).get_importetotalcup()  
        importecuc=Facturas.objects.get(pk=idfa).get_importecuc()
    
        pmn=ClienteContrato.objects.select_related().get(cliente=fact.cliente.id,cerrado=False)
        mncosto=pmn.contrato.preciocostomn
        cuccosto=pmn.contrato.preciocostocuc
    
        precio_CUP="Precio CUP"
        if(mncosto==True):
            precio_CUP=precio_CUP+"(Costo)"
                
        precio_CUC="Precio MLC"
        if (cuccosto==True):
            precio_CUC=precio_CUC+"(Costo)"
                    
        rc_observaciones=fact.doc_factura.observaciones
        filas = DetalleFactura.objects.select_related().filter(factura=idfa).order_by('casco_casco.casco_nro')
        rc_tipo='De Venta'
        if fact.tipo == 'O':
            rc_tipo='Otra'
        elif fact.tipo == 'A':
            rc_tipo='Ajuste'
        elif fact.tipo == 'K':
            rc_tipo='Vulca'
        elif fact.tipo == 'R':
            rc_tipo='Regrabable'
        rc_transportador=fact.transportador.nombre
        rc_chapa=fact.chapa
        rc_licencia=fact.licencia
    # Verificar si se puede editar. Se puede editar si todos los cascos relacionados con el estado es Casco
    #editar=editar_documento(filas,idfa)
        hay_cup=1
        hay_cuc=1
        return render_to_response('comercial/viewfactura.html',{'hay_cup':hay_cup,'hay_cuc':hay_cuc,'eliminar':0,'editar':1,'cancelar':0,'confirmar':0,'transportador':rc_transportador,'chapa':rc_chapa,
                                                            'licencia':rc_licencia,'transportador':rc_transportador,'precio_CUC':precio_CUC,
                                                            'precio_CUP':precio_CUP,'importecuc':importecuc,'importecup':importecup,
                                                            'tipo':rc_tipo,'rc_nro':rc_nro,'fecha':rc_fecha,'cliente':rc_cliente,
                                                            'observaciones':rc_observaciones,'rc_id':idfa,'elementos_detalle':filas, 
                                                            'error2':l},context_instance = RequestContext(request))

    try:
        hay_cup=1
        hay_cuc=1
        filas = DetalleFactura.objects.filter(factura=idfa)
        for canti in filas:
            actualiza_traza(canti.casco.id_casco,idfa)
        Facturas.objects.filter(pk=idfa).update(cancelada=True)
        pk_user=User.objects.get(pk=request.user.id)
        Doc.objects.filter(pk=Facturas.objects.get(pk=idfa).doc_factura).update(operador=pk_user)
            
        #Doc.objects.select_related().get(pk=idfa).delete()
        return HttpResponseRedirect('/comerciax/comercial/factura/index')
        #return render_to_response("casco/recepcionclienteindex.html",locals(),context_instance = RequestContext(request))
    except Exception,e :
        transaction.rollback()
        l = ['Error al cancelar factura']
        fact = Facturas.objects.select_related().get(pk=idfa)
        importecup=Facturas.objects.get(pk=idfa).get_importetotalcup()  
        importecuc=Facturas.objects.get(pk=idfa).get_importecuc()
    
        rc_fecha=fact.doc_factura.fecha_doc.strftime("%d/%m/%Y")
        rc_cliente=fact.cliente.nombre
        rc_transportador=fact.transportador.nombre
        rc_nro=fact.factura_nro
        rc_observaciones=fact.doc_factura.observaciones
        rc_chapa=fact.chapa
        rc_licencia=fact.licencia
        rc_tipo='De Venta'
        if fact.tipo == 'O':
            rc_tipo='Otra'
        elif fact.tipo == 'A':
            rc_tipo='Ajuste'
        elif fact.tipo == 'K':
            rc_tipo='Vulca'
        elif fact.tipo == 'R':
            rc_tipo='Regrabable'
        
        filas = DetalleFactura.objects.select_related().filter(factura=idfa).order_by('casco_casco.casco_nro')
        pmn=ClienteContrato.objects.select_related().get(cliente=fact.cliente.id,cerrado=False)
        mncosto=pmn.contrato.preciocostomn
        cuccosto=pmn.contrato.preciocostocuc
    
        precio_CUP="Precio CUP"
        if(mncosto==True):
            precio_CUP=precio_CUP+"(Costo)"
                
        precio_CUC="Precio MLC"
        if (cuccosto==True):
            precio_CUC=precio_CUC+"(Costo)"
			
        return render_to_response('comercial/viewfactura.html',{'hay_cup':hay_cup,'hay_cuc':hay_cuc,'transportador':rc_transportador,'chapa':rc_chapa,'licencia':rc_licencia,'transportador':rc_transportador,'precio_CUC':precio_CUC,
                                                            'precio_CUP':precio_CUP,'importecuc':importecuc,'importecup':importecup,
                                                            'tipo':rc_tipo,'rc_nro':rc_nro,'fecha':rc_fecha,'cliente':rc_cliente,
                                                            'observaciones':rc_observaciones,'rc_id':idfa,'elementos_detalle':filas, 
                                                            'error2':l, 'cantcascos':'4'},context_instance = RequestContext(request))
    else:
        transaction.commit()
 
      
#############################################################
#        DETALLE FACTURA
#############################################################
@login_required
def detalle_factura_list(request,idfa,medida):
    cascos = DetalleFactura.objects.select_related().filter(factura=idfa,).order_by('casco_casco.casco_nro')    
#    cascos=Casco.objects.select_related().filter(estado_actual__in=filtro,producto__id=idprod).order_by('admincomerciax_producto.descripcion','casco_nro')
    
    lista_valores=[]
    for detalles in cascos:
        lista_valores=lista_valores+[{"casco_nro":detalles.casco_nro,"pk":detalles.id_casco,"medida":detalles.producto.descripcion,"cliente":detalles.get_cliente()}]
    
    return HttpResponse(simplejson.dumps(lista_valores),content_type = 'application/javascript; charset=utf8')

@login_required
def detalleFactCliente_list(request,idprod,idfa):
   
    fact=Facturas.objects.get(pk=idfa)
    filas1=None
    filas=DetalleRC.objects.select_related().filter(rc__cliente=fact.cliente,rc__recepcioncliente_tipo=fact.tipo,casco__estado_actual__in=["PT"],casco__producto_salida_id=idprod).order_by('casco_casco.casco_nro')
    if fact.cliente.comercializadora==True:
        filas1=DetalleRC.objects.select_related().\
              filter(rc__cliente__provincia=fact.cliente.provincia,rc__cliente__organismo=fact.cliente.organismo,
                     rc__recepcioncliente_tipo=fact.tipo,casco__estado_actual="PT",casco__producto_salida_id=idprod).\
              exclude(rc__cliente=fact.cliente).order_by('casco_casco.casco_nro')

    cascos = Casco.objects.select_related().filter(estado_actual="DC", producto_salida_id=idprod).order_by(
        'admincomerciax_producto.descripcion', 'casco_nro')
    cascos_ventas = Casco.objects.select_related().filter(estado_actual="PT", producto_salida_id=idprod,
                                                          venta=True).order_by('admincomerciax_producto.descripcion',
                                                                               'casco_nro')
    lista_valores=[]
    for detalles in filas:
        lista_valores=lista_valores+[{"casco_nro":detalles.casco.casco_nro,"pk":detalles.casco.id_casco,
                                      "medida":detalles.casco.producto_salida.descripcion,"cliente":detalles.casco.get_cliente(),
                                      "medida_entrada":detalles.casco.producto.descripcion}]
    if filas1!=None:
        for detalles in filas1:
            lista_valores=lista_valores+[{"casco_nro":detalles.casco.casco_nro,"pk":detalles.casco.id_casco,
                                      "medida":detalles.casco.producto_salida.descripcion,"cliente":detalles.casco.get_cliente(),
                                      "medida_entrada":detalles.casco.producto.descripcion}]
        
    for detalles in cascos:
        lista_valores=lista_valores+[{"casco_nro":detalles.casco_nro,"pk":detalles.id_casco,
                                      "medida":detalles.producto_salida.descripcion,"cliente":detalles.get_cliente(),
                                      "medida_entrada":detalles.producto.descripcion}]
    for detalles in cascos_ventas:
        lista_valores=lista_valores+[{"casco_nro":str(detalles.casco_nro)+'(V)',"pk":detalles.id_casco,
                                      "medida":detalles.producto_salida.descripcion,"cliente":detalles.get_cliente(),
                                      "medida_entrada":detalles.producto.descripcion}]

    return HttpResponse(simplejson.dumps(lista_valores),content_type = 'application/javascript; charset=utf8')

@login_required
def detalleFactPart_list(request,idprod,idfa):
   
    fact=FacturasParticular.objects.get(pk=idfa)
    nombre_fact=fact.nombre
    ci_fact=fact.ci

    filas = DetalleRP.objects.select_related(). \
        filter(rp__nombre=nombre_fact, rp__ci=ci_fact, casco__estado_actual="PT", casco__producto_salida_id=idprod). \
        order_by('casco_casco.casco_nro')

    cascos = Casco.objects.select_related().filter(estado_actual="DC", producto_salida_id=idprod).order_by(
        'admincomerciax_producto.descripcion', 'casco_nro')
    cascos_ventas = Casco.objects.select_related().filter(estado_actual="PT", producto_salida_id=idprod,
                                                          venta=True).order_by('admincomerciax_producto.descripcion',
                                                                               'casco_nro')
    lista_valores = []

    for detalles in filas:
        lista_valores = lista_valores + [{"casco_nro": detalles.casco.casco_nro, "pk": detalles.casco.id_casco,
                                          "medida": detalles.casco.producto_salida.descripcion,
                                          "cliente": detalles.casco.get_cliente(),
                                          "medida_entrada": detalles.casco.producto.descripcion}]
    for detalles in cascos:
        lista_valores = lista_valores + [{"casco_nro": detalles.casco_nro, "pk": detalles.id_casco,
                                          "medida": detalles.producto_salida.descripcion,
                                          "cliente": detalles.get_cliente(),
                                          "medida_entrada": detalles.producto.descripcion}]
    for detalles in cascos_ventas:
        lista_valores = lista_valores + [{"casco_nro": str(detalles.casco_nro)+'(V)', "pk": detalles.id_casco,
                                          "medida": detalles.producto_salida.descripcion,
                                          "cliente": detalles.get_cliente(),
                                          "medida_entrada": detalles.producto.descripcion}]

    return HttpResponse(simplejson.dumps(lista_valores),content_type = 'application/javascript; charset=utf8')

@login_required
#@transaction.commit_on_success()
def detalleFactura_add(request,idfa):
    if not request.user.has_perm('comercial.factura'):
        return render_to_response("denegado.html",locals(),context_instance = RequestContext(request))
    
    l=[]
    fact=Facturas.objects.get(pk=idfa)
    medidas=Producto.objects.all()
    noelim=0
    if fact.confirmada == hashlib.sha1(fact.pk.__str__()+'YES').hexdigest():
        mensa="No se puede adicionar cascos a la factura Nro. "+fact.factura_nro+" porque ya está confirmada"
        noelim=1
    elif fact.confirmada != hashlib.sha1(fact.pk.__str__()+'NO').hexdigest():
        mensa="No se puede adcionar cascos a la factura Nro. "+fact.factura_nro+" porque está corrupta"
        noelim=1
        #return HttpResponseRedirect('/comerciax/comercial/factura/view/'+idfa) 
    if noelim==1:
        l=[mensa]
        rc_fecha=fact.doc_factura.fecha_doc.strftime("%d/%m/%Y")
        rc_cliente=fact.cliente.nombre
        rc_clientecomercializador=fact.cliente.comercializadora
        rc_nro=fact.factura_nro
        importecup=Facturas.objects.get(pk=idfa).get_importe_totalcup() 
        importecuc=Facturas.objects.get(pk=idfa).get_importecuc()
    
        pmn=ClienteContrato.objects.select_related().get(cliente=fact.cliente.id,cerrado=False)
        mncosto=pmn.contrato.preciocostomn
        cuccosto=pmn.contrato.preciocostocuc
    
        precio_CUP="Precio CUP"
        if(mncosto==True):
            precio_CUP=precio_CUP+"(Costo)"
                
        precio_CUC="Precio MLC"
        if (cuccosto==True):
            precio_CUC=precio_CUC+"(Costo)"
                    
        rc_observaciones=fact.doc_factura.observaciones
        filas = DetalleFactura.objects.select_related().filter(factura=idfa).order_by('casco_casco.casco_nro')
#        rc_tipo='De Venta'
        if fact.tipo == 'O':
            rc_tipo='Otra'
        elif fact.tipo == 'A':
            rc_tipo='Ajuste'
        elif fact.tipo == 'K':
            rc_tipo='Vulca'
        elif fact.tipo == 'R':
            rc_tipo='Regrabable'
        rc_transportador=fact.transportador.nombre
        rc_chapa=fact.chapa
        rc_licencia=fact.licencia
    # Verificar si se puede editar. Se puede editar si todos los cascos relacionados con el estado es Casco
    #editar=editar_documento(filas,idfa)
        hay_cup=1
        hay_cuc=1
        return render_to_response('comercial/viewfactura.html',{'hay_cup':hay_cup,'hay_cuc':hay_cuc,'eliminar':0,'editar':1,'cancelar':0,'confirmar':0,'transportador':rc_transportador,'chapa':rc_chapa,
                                                            'transportador':rc_transportador,'licencia':rc_licencia,'precio_CUC':precio_CUC,
                                                            'precio_CUP':precio_CUP,'importecuc':importecuc,'importecup':importecup,
                                                            'tipo':rc_tipo,'rc_nro':rc_nro,'fecha':rc_fecha,'cliente':rc_cliente,
                                                            'observaciones':rc_observaciones,'rc_id':idfa,'elementos_detalle':filas, 
                                                            'error2':l},context_instance = RequestContext(request))

    titulo_form='Facturas' 
    controlador_form='Facturas'
    descripcion_form='Seleccionar cascos para la factura'
    
    accion_form='detalleFactura_add'
    cancelbtn_form='/comerciax/comercial/factura/view/'+idfa
    
    if request.method == 'POST':
        
        pmn=ClienteContrato.objects.select_related().get(cliente=fact.cliente.id,cerrado=False)
        mn=pmn.contrato.preciomn
        mnext=pmn.contrato.precioextcup
        mncosto=pmn.contrato.preciocostomn
        cuc=pmn.contrato.preciocuc
        cuccosto=pmn.contrato.preciocostocuc
        seleccion=request.POST.keys()
        k=0

        while True:
            if k==seleccion.__len__():
                break
            casco=Casco.objects.filter(pk=seleccion[k])

            if casco.count()!=0:
                '''
                Los selecionados los cambio de estado, agregar a detalle del documento y actualizar trazabilidad
                
                Casco.objects.filter(pk=seleccion[k]).update(estado_actual=Estados.estados["Factura"])
                '''
                
                detalle=DetalleFactura()
                if DetalleFactura.objects.filter(factura=idfa, casco=Casco.objects.get(pk=seleccion[k])).count()!=0:
                    detalle=DetalleFactura.objects.get(factura=idfa, casco=Casco.objects.get(pk=seleccion[k]))
                else:
                    detalle.id_detalle=uuid4()
                    
                detalle.factura=Facturas.objects.get(pk=idfa)
                detalle.casco=Casco.objects.get(pk=seleccion[k])
                detalle.precio_mn=0
                detalle.precio_casco=0
                detalle.precio_casco=0
                if detalle.casco.venta==True and detalle.casco.decomisado==False:
                    if not detalle.casco.id_cliente.get_precio_casco():
                        detalle.precio_casco=detalle.casco.producto_salida.precio_casco
                    else:
                        detalle.precio_casco=detalle.casco.producto_salida.otro_precio_casco
                
                if (mn==True):
                    if fact.tipo=='K':
                        detalle.precio_mn=detalle.casco.producto_salida.precio_vulca
                    elif fact.tipo=='R':
                        detalle.precio_mn = detalle.casco.producto_salida.precio_regrabable
                    else:
                        detalle.precio_mn=detalle.casco.producto_salida.precio_mn
                elif (mnext==True):
                    detalle.precio_mn=detalle.casco.producto_salida.precio_externo_cup
                elif(mncosto==True):
                    detalle.precio_mn=detalle.casco.producto_salida.precio_costo_mn
                detalle.precio_cuc=0
                if fact.tipo!='K': 
                    if (cuc==True):
                        detalle.precio_cuc=detalle.casco.producto_salida.precio_cuc
                    elif (cuccosto==True):
                        detalle.precio_cuc=detalle.casco.producto_salida.precio_costo_cuc
                    
                detalle.save()
                
                Casco.objects.filter(pk=seleccion[k]).update(estado_actual="Factura",fecha=fact.doc_factura.fecha_doc,id_cliente=fact.cliente)
                
                add_trazabilidad(seleccion[k], idfa, "Factura")
                
            k=k+1
        if request.POST.__contains__('submit1'):
#            if fact.tipo=='V':
            #filas=DetalleRC.objects.filter(rc__in=lista_doc, casco__estado_actual=Estados.estados["PT"]).order_by('casco_casco.casco_nro')
            return render_to_response('comercial/seleccionar_casco.html', {'medidas':medidas,'title':titulo_form,'controlador':controlador_form,'accion':accion_form,
                                                      'cancelbtn':cancelbtn_form,'nro':fact.factura_nro,'form_description':descripcion_form,
                                                      'fecha':fact.doc_factura.fecha_doc.strftime("%d/%m/%Y"),'observaciones':fact.doc_factura.observaciones,
                                                      'rc_id':idfa,'dettransfe':True},context_instance = RequestContext(request)) 
#            return render_to_response('comercial/seleccionar_casco.html', {'cant_elem':cant_elem,'title':titulo_form,'controlador':controlador_form,'accion':accion_form,
#                                                     'cancelbtn':cancelbtn_form,'elementos_detalle1':filas_result, 'nro':fact.factura_nro,'form_description':descripcion_form,
#                                                     'fecha':fact.doc_factura.fecha_doc.strftime("%d/%m/%Y"),'observaciones':fact.doc_factura.observaciones,
#                                                     'rc_id':idfa},context_instance = RequestContext(request))
        else:
            return HttpResponseRedirect('/comerciax/comercial/factura/view/' + idfa)
#    if fact.tipo=='V':
        
    return render_to_response('comercial/seleccionar_casco.html', {'medidas':medidas,'title':titulo_form,'controlador':controlador_form,'accion':accion_form,
                                                      'cancelbtn':cancelbtn_form,'nro':fact.factura_nro,'form_description':descripcion_form,
                                                      'fecha':fact.doc_factura.fecha_doc.strftime("%d/%m/%Y"),'observaciones':fact.doc_factura.observaciones,
                                                      'rc_id':idfa,'dettransfe':True},context_instance = RequestContext(request)) 
#===============================================================================
# FACTURA A PARTICULARES
#===============================================================================
@login_required
def get_factpart_list(request):
    #prepare the params
    try:
        fecha_desde=Fecha_Ver.objects.get()
    except Exception, e:
        fecha_desde=None
    if  fecha_desde == None:  
        querySet = FacturasParticular.objects.select_related().all()
    else:
        querySet = FacturasParticular.objects.select_related().filter(doc_factura__fecha_doc__gte=fecha_desde.fecha)
    #querySet = querySet.filter(doc__fecha_doc__year=2010)
 
    columnIndexNameMap = {0:'-doc_factura__fecha_doc',1:'factura_nro',2:'doc_factura__fecha_doc',3:'nombre',4:'ci',5:'cancelada',6:'confirmar'}
    
    #{0: 'oferta_nro',1: 'oferta_nro',2:'admincomerciax_cliente.nombre',3:'doc_oferta__fecha_oferta',4:'oferta_tipo'}

    searchableColumns = ['factura_nro','nombre','ci','confirmar','doc_factura__fecha_doc']
    #path to template used to generate json
    jsonTemplatePath = 'comercial/json/json_facturapart.txt'

    #call to generic function from utils
    return get_datatables_records(request, querySet, columnIndexNameMap, searchableColumns, jsonTemplatePath)

def verfacturapart(request,idfactura,haycup,haycuc,cantcascos):
    empresaobj1 = Empresa.objects.all()
    hay_cup=int(haycup)
    hay_cuc=int(haycuc)
    for empresaobj in empresaobj1: 
        titular_name = empresaobj.nombre
        titular_dir = empresaobj.direccion
        titular_codigo = empresaobj.codigo
        titular_email = empresaobj.email
        titular_phone = empresaobj.telefono
        titular_fax = empresaobj.fax
        titular_cuenta_mn = empresaobj.cuenta_mn
        titular_cuenta_cuc = empresaobj.cuenta_usd
        titular_sucursal_mn = empresaobj.sucursal_mn
        titular_sucursal_cuc = empresaobj.sucursal_usd
    
    factura = FacturasParticular.objects.select_related().get(doc_factura=idfactura)
    pk_user=User.objects.get(pk=request.user.id)
    vendedor=pk_user.first_name+" "+pk_user.last_name
    
#    doc_fac=Facturas.objects.get(pk=idfactura).doc_factura
    user_doc=Doc.objects.get(id_doc=factura.doc_factura.id_doc).operador
    operador_=User.objects.get(pk=user_doc.id)
#    operador_=User.objects.get(pk=Doc.objects.get(pk=Facturas.objects.get(pk=idfactura).doc_factura).operador)
    confeccionado=operador_.first_name+" "+operador_.last_name
    declaracion = True
        
#    detallesFact4 = DetalleFactura.objects.select_related().filter(factura=idfactura,casco__producto_salida__codigo='"625.9.01.2205"')
    detallesFact = DetalleFacturaPart.objects.select_related().filter(factura=idfactura).values('factura','precio_particular','casco__producto_salida',\
                                                                            'casco__producto_salida__codigo','casco__producto_salida__descripcion',\
                                                                            'casco__producto_salida__um__descripcion')\
                                                                            .annotate(cantidad=Count('casco__producto_salida'))
    for a1 in range(detallesFact.__len__()):
        detallesFact[a1]['importecup']=detallesFact[a1]['precio_particular']*detallesFact[a1]['cantidad']
        detallesFact[a1]['precio_mn']=str(detallesFact[a1]['precio_particular'])

    cliente = factura.nombre
    cliente_codigo = factura.ci
    cliente_nombre = factura.nombre
    fecha_confeccionado = factura.doc_factura.fecha_doc
    importecup = factura.get_importetotalcup()
    observaciones=factura.doc_factura.observaciones

    transportador_nombre = factura.nombre
    transportador_ci = factura.ci

    cancelada=factura.cancelada
    importetotalcup=factura.get_importe()

    if factura.recargo > 0.0:
        recargo = float(factura.recargo)
        importe_ = float(importetotalcup.replace(' ', '').replace(',', '').replace('$', ''))
        val = utils.redondeo((importe_ * recargo)/100, 2)
        importetotalcup_ = utils.redondeo(importe_ + val,2)
        importetotalcup_ = '$' + '{:20,.2f}'.format(importetotalcup_)


    return render_to_response("report/factura.html",locals(),context_instance = RequestContext(request))

def obtener_particular(request, idcl):
    
    data=[]
    por_pagar=0
    if idcl.__len__()!=0:
        trans=RecepcionParticular.objects.filter(ci = idcl).distinct('nombre').order_by('nombre')
        elementos=FacturasParticular.objects.filter(ci = idcl,confirmar=True,cancelada=False).all()
        for a1 in elementos:
            if a1.get_porpagar(2)>0.0:
                por_pagar=1
    else:        
        trans=RecepcionParticular.objects.select_related().filter(ci='0')
        
    for a1 in trans:
        data+=[{'pk':a1.doc_recepcionparticular.id_doc,'nombre':a1.nombre,'por_pagar':str(por_pagar)}]
    if data.__len__()==0:
        data+=[{'pk':"",'nombre':"",'por_pagar':str(por_pagar)}]
        
        
    return HttpResponse(simplejson.dumps(data),content_type = 'application/javascript; charset=utf8')

@login_required
def facturapart_index(request):
    if not request.user.has_perm('comercial.factura'):
        return render_to_response("denegado.html",locals(),context_instance = RequestContext(request))
    return render_to_response('comercial/facturapartindex.html',locals(),context_instance = RequestContext(request))
    
@login_required
@transaction.commit_on_success()
def facturapart_add(request):
    if not request.user.has_perm('comercial.factura'):
        return render_to_response("denegado.html",locals(),context_instance = RequestContext(request))
    
    nombre_form='Facturas'
    descripcion_form='Realizar Factura'
    titulo_form='Facturas' 
    controlador_form='Facturas'
    accion_form='/comerciax/comercial/facturapart/add'
    cancelbtn_form='/comerciax/comercial/facturapart/index'
    fecha_cierre=Fechacierre.objects.get(almacen='cm').fechaminima()
    fecha_maxima=Fechacierre.objects.get(almacen='cm').fechamaxima() 
    c=None
    l=[]
#    for a in fecham:
#        fecha_cierre=a.fechacierre.strftime("%d/%m/%Y")
    if request.method == 'POST':
        form = FacturaPartForm(request.POST)

        if form.is_valid():
            tipo=form.cleaned_data['tipo']
            ci=form.cleaned_data['ci']
            pk_user=User.objects.get(pk=request.user.id)
            
            fact=FacturasParticular()
            
            pk_doc=uuid4()
            obj_doc=Doc()
            
            obj_doc.id_doc=pk_doc
            obj_doc.tipo_doc='17'
            obj_doc.fecha_doc=form.cleaned_data['fecha']
            obj_doc.operador=pk_user
            obj_doc.fecha_operacion=datetime.date.today()
            obj_doc.observaciones=form.cleaned_data['observaciones']
            
            fact.doc_factura = obj_doc
            fact.factura_nro=random.randint(1,1000) 
            fact.ci=form.data['ci']
            fact.tipo=tipo
            fact.recargo=form.cleaned_data['recargo']
            fact.nombre=RecepcionParticular.objects.get(pk=form.cleaned_data['nombre']).nombre
            fact.confirmada=hashlib.sha1(pk_doc.__str__()+'NO').hexdigest()
#         
            try:
                obj_doc.save()
                fact.save()
#                nume.save() 
                return HttpResponseRedirect('/comerciax/comercial/facturapart/view/'+pk_doc.__str__())  
            except Exception, e:
                exc_info = e.__str__() # sys.exc_info()[:1]
                c = exc_info.find("DETAIL:")
                
                if c < 0:
                    l=l+["Error Fatal."]
                else:
                    c = exc_info[c + 7:]
                    l=l+[c] 
                                     
                transaction.rollback()
                form = FacturaPartForm(request.POST)
                return render_to_response('comercial/facturaadd.html',  {'form': form, 'form_name':nombre_form,'form_description':descripcion_form,
                                                                         'accion':accion_form,'titulo':titulo_form,'controlador':controlador_form,
                                                                         'cancelbtn':cancelbtn_form,'fecha_minima':fecha_cierre,'fecha_maxima':fecha_maxima,'error2':l},context_instance = RequestContext(request))
            else:
                transaction.commit()
    else:
        form =FacturaPartForm(initial={'fecha':fecha_cierre}) 
    
    return render_to_response('comercial/facturaadd.html',  {'form': form, 'form_name':nombre_form,'form_description':descripcion_form,
                                                             'accion':accion_form,'titulo':titulo_form,'controlador':controlador_form,
                                                             'cancelbtn':cancelbtn_form,'fecha_minima':fecha_cierre,'fecha_maxima':fecha_maxima,'error2':c},context_instance = RequestContext(request))


@login_required
@transaction.commit_on_success()
def facturapart_edit(request,idfa):
    
    if not request.user.has_perm('comercial.factura'):
        return render_to_response("denegado.html",locals(),context_instance = RequestContext(request))
    
    fact=FacturasParticular.objects.select_related().get(pk=idfa)
    noedit=0
    if fact.confirmada == hashlib.sha1(fact.pk.__str__()+'YES').hexdigest():
        mensa="No se puede editar la factura Nro. "+fact.factura_nro+" porque ya está confirmada"
        noedit=1
    elif fact.confirmada != hashlib.sha1(fact.pk.__str__()+'NO').hexdigest():
        mensa="No se puede editar la factura Nro. "+fact.factura_nro+" porque está corrupta"
        noedit=1
        #return HttpResponseRedirect('/comerciax/comercial/factura/view/'+idfa) 
    if noedit==1:
        l=[mensa]
        rc_fecha=fact.doc_factura.fecha_doc.strftime("%d/%m/%Y")
        rc_cliente=fact.nombre
        rc_ci=fact.ci
        rc_nro=fact.factura_nro
        rc_recarga=fact.format_recargo()

        # importecup=FacturasParticular.objects.get(pk=idfa).get_importetotalcup()
        importecup=fact.get_importetotalcup()

        rc_observaciones=fact.doc_factura.observaciones
        filas = DetalleFacturaPart.objects.select_related().filter(factura=idfa).order_by('casco_casco.casco_nro')
        rc_tipo='De Venta'
        if fact.tipo == 'O':
            rc_tipo='Otra'
        elif fact.tipo == 'A':
            rc_tipo='Ajuste'
        elif fact.tipo == 'K':
            rc_tipo='Vulca'
        elif fact.tipo == 'R':
            rc_tipo='Regrabable'
        
    # Verificar si se puede editar. Se puede editar si todos los cascos relacionados con el estado es Casco
    #editar=editar_documento(filas,idfa)
    
        return render_to_response('comercial/viewfactura.html',{'ci':rc_ci,'eliminar':0,'editar':1,'cancelar':0,'confirmar':0,
                                                            'importecup':importecup,
                                                            'tipo':rc_tipo,'rc_nro':rc_nro,'fecha':rc_fecha,'cliente':rc_cliente,
                                                            'observaciones':rc_observaciones,'rc_id':idfa,'elementos_detalle':filas, 
                                                            'error2':l},context_instance = RequestContext(request))

    nombre_form='Facturas'
    descripcion_form='Realizar Factura a Particulares'
    titulo_form='Facturas' 
    controlador_form='Facturas'
    accion_form='/comerciax/comercial/facturapart/edit/'+ idfa +'/'
    cancelbtn_form='/comerciax/comercial/facturapart/view/'+ idfa +'/'
    fecha_cierre=Fechacierre.objects.get(almacen='cm').fechaminima()
    fecha_maxima=Fechacierre.objects.get(almacen='cm').fechamaxima() 
    c=None
    
#    fact = Facturas.objects.select_related().get(pk=idfa)
    l=[]
#    for a in fecham:
#        fecha_cierre=a.fechacierre.strftime("%d/%m/%Y")
        
    detalles=DetalleFacturaPart.objects.filter(factura=idfa).count() 
      
    if request.method == 'POST':
        tipo=fact.tipo
        if detalles==0:
            form = FacturaPartForm(request.POST)
        elif tipo=='V':
            form = FacturaPartForm1(request.POST)
        else:
            form = FacturaPartForm1(request.POST)
        #rajuste = form.cleaned_data['ajuste']
        if form.is_valid():
            ci=form.data['ci']
            nombre=RecepcionParticular.objects.get(pk=form.cleaned_data['nombre']).nombre
            tipo=form.cleaned_data['tipo']  
            recarga=form.cleaned_data['recargo']
            recarga = 0.0 if str(recarga).__len__() == 0 else recarga
            if  form.cleaned_data['tipo']=='De Venta':
                tipo='V'
            elif form.cleaned_data['tipo']=='De Ajuste':
                tipo='A'
            elif form.cleaned_data['tipo']=='Otra':
                tipo='O'
            elif form.cleaned_data['tipo']=='Vulka':
                tipo='K'
                
            pk_user=User.objects.get(pk=request.user.id)
            
            # fact=FacturasParticular.objects.get(pk=idfa)
            doc=Doc.objects.get(pk=idfa)
            
            fact.factura_nro=random.randint(1,100000) 
            doc.fecha_doc=form.cleaned_data['fecha']
            doc.operador=pk_user
            doc.operador=pk_user
            doc.doc_operacion=datetime.date.today()
            doc.observaciones=form.cleaned_data['observaciones']         
            fact.ci=ci
            fact.tipo=tipo
            fact.recargo=recarga
            fact.nombre=nombre
         
            try:
                doc.save()
                fact.save() 
 
                return HttpResponseRedirect('/comerciax/comercial/facturapart/view/'+idfa)  

            except Exception, e:
                exc_info = e.__str__() # sys.exc_info()[:1]
                c = exc_info.find("DETAIL:")
                
                if c < 0:
                    l=l+["Error Fatal."]
                else:
                    c = exc_info[c + 7:]
                    l=l+[c]
                    
                transaction.rollback()
                
                form = FacturaForm(request.POST)
                return render_to_response('form/form_adddetalle.html',  {'tipocliente':'0','form': form, 'form_name':nombre_form,'form_description':descripcion_form,
                                                                         'accion':accion_form,'titulo':titulo_form,'controlador':controlador_form,
                                                                         'cancelbtn':cancelbtn_form,'fecha_minima':fecha_cierre,'fecha_maxima':fecha_maxima,'error2':l},context_instance = RequestContext(request))
            else:
                transaction.commit()     
    else:
#        fact = Facturas.objects.select_related().get(pk=idfa)
        tipo=fact.tipo
        if detalles==0:
            form = FacturaPartForm(initial={'tipo':fact.tipo,'nro':fact.factura_nro,'fecha':fact.doc_factura.fecha_doc,
                                            'ci':fact.ci,'nombre':fact.nombre,'observaciones':fact.doc_factura.observaciones,
                                            'recargo':fact.recargo})
        elif tipo=='V':
            a1=fact.nombre
            form = FacturaPartForm1(initial={'ci':fact.ci,
                                         'tipo':'De Venta',
                                         'nro':fact.factura_nro,
                                         'fecha':fact.doc_factura.fecha_doc,
                                         'nombre':fact.cliente,
                                         'observaciones':fact.doc_factura.observaciones})
        else:
            rc_tipo='De Ajuste'
            if fact.tipo == 'O':
                rc_tipo='Otra'
            form = FacturaPartForm1(initial={'ci':fact.ci,'tipo':rc_tipo,'nro':fact.factura_nro,'fecha':fact.doc_factura.fecha_doc,
                                            'nombre':fact.nombre,'observaciones':fact.doc_factura.observaciones,
                                             'recargo':fact.recargo})
        
    return render_to_response('comercial/facturaedit.html',  {'form': form, 'form_name':nombre_form,'form_description':descripcion_form,
                                                       'accion':accion_form,'titulo':titulo_form,'controlador':controlador_form,
                                                       'cancelbtn':cancelbtn_form,'fecha_minima':fecha_cierre,'fecha_maxima':fecha_maxima},context_instance = RequestContext(request))

@login_required
def facturapart_view(request,idfa):
    if not request.user.has_perm('comercial.factura'):
        return render_to_response("denegado.html",locals(),context_instance = RequestContext(request))
    
    l=[]
    cancelar=0
    fact = FacturasParticular.objects.select_related().get(pk=idfa)
    if fact.cancelada==True:
        cancelar=1
    confir=fact.get_confirmada()
    confirmar=2
    if confir=='N':
        confirmar=0
    elif confir=='S':
        confirmar=1

    eliminar=1
    editar=1
    if confirmar==2 or confirmar==1:
        eliminar=0  
        editar=0
     
    rc_fecha=fact.doc_factura.fecha_doc.strftime("%d/%m/%Y")
    rc_cliente=fact.nombre
    rc_ci=fact.ci
    rc_nro=fact.factura_nro
    importecup=fact.get_importe()
    cant_cascos=fact.cantidad_casco()
    crenglones=fact.get_renglones()
    importecasco=fact.get_importe_venta()
    rc_observaciones=fact.doc_factura.observaciones
    filas = DetalleFacturaPart.objects.select_related().filter(factura=idfa).order_by('casco__producto_salida__descripcion','casco_casco.casco_nro')
    rc_tipo='De Venta'
    if fact.tipo == 'O':
        rc_tipo='Otra'
    elif fact.tipo == 'A':
        rc_tipo='Ajuste'
    elif fact.tipo == 'K':
        rc_tipo='Vulca'
    elif fact.tipo == 'R':
        rc_tipo = 'Regrabable'
    for a in filas:
        z=a.format_precio_particular()
        
    elementos_detalle=[]
    id1=''
    k=0
    k2=0
    t_preciocuc=0.0
    t_preciocup=0.0  
    t_preciocasco=0.0  
    recargo = fact.format_recargo()
    totalpagar = fact.get_importe_total(recargo)
    for a1 in filas:
        if k!=0:
            if id1!=a1.casco.producto_salida.id:
                elementos_detalle[k-1]['cantidad'] = k2
                elementos_detalle[k-1]['t_preciocup'] = t_preciocup
                elementos_detalle[k-1]['t_preciocasco'] = t_preciocasco
                t_preciocuc=0.0
                t_preciocup=0.0 
                t_preciocasco=0.0
                k2=0
        elementos_detalle+=[{'casco_id':a1.casco.id_casco,
                             'casco_nro':a1.casco.casco_nro,'productosalida':a1.casco.producto_salida.descripcion,
                             'productoid':a1.casco.producto.id,'precio_cup':a1.format_precio_particular(),
                             'precio_casco':a1.format_precio_casco()}]
        k+=1
        k2+=1
        t_preciocup+=float(a1.precio_particular)
        t_preciocasco+=float(a1.precio_casco)
        id1=a1.casco.producto_salida.id  
    if k!=0:
        elementos_detalle[k-1]['cantidad'] = k2    
        elementos_detalle[k-1]['t_preciocup'] = t_preciocup
        elementos_detalle[k-1]['t_preciocasco'] = t_preciocasco
    return render_to_response('comercial/viewfacturapart.html',{'crenglones':crenglones,'total_casco':k,'eliminar':eliminar,
                                                                'editar':editar,'cancelar':cancelar,'confirmar':confirmar,
                                                            'ci':rc_ci,'importecup':importecup,
                                                            'tipo':rc_tipo,'rc_nro':rc_nro,'fecha':rc_fecha,'cliente':rc_cliente,
                                                            'observaciones':rc_observaciones,'rc_id':idfa,'elementos_detalle':elementos_detalle,
                                                            'cant_cascos':cant_cascos, 'importecasco':importecasco,
                                                            'error2':l, 'recargo': fact.format_recargo(), 'totalpagar': totalpagar},context_instance = RequestContext(request))

@login_required
@transaction.commit_on_success()
def facturapart_del(request,idfa):
    if not request.user.has_perm('comercial.factura'):
        return render_to_response("denegado.html",locals(),context_instance = RequestContext(request))
    
    l=[]
    fact=FacturasParticular.objects.get(pk=idfa)
    noelim=0
    if fact.confirmada == hashlib.sha1(fact.pk.__str__()+'YES').hexdigest():
        mensa="No se puede eliminar la factura Nro. "+fact.factura_nro+" porque ya está confirmada"
        noelim=1
    elif fact.confirmada != hashlib.sha1(fact.pk.__str__()+'NO').hexdigest():
        mensa="No se puede eliminar la factura Nro. "+fact.factura_nro+" porque está corrupta"
        noelim=1
        #return HttpResponseRedirect('/comerciax/comercial/factura/view/'+idfa) 
    if noelim==1:
        l=[mensa]
        rc_fecha=fact.doc_factura.fecha_doc.strftime("%d/%m/%Y")
        rc_cliente=fact.nombre
        rc_ci=fact.ci
        rc_nro=fact.factura_nro
        importecup=FacturasParticular.objects.get(pk=idfa).get_importetotalcup()  
    
        rc_observaciones=fact.doc_factura.observaciones
        filas = DetalleFacturaPart.objects.select_related().filter(factura=idfa).order_by('casco_casco.casco_nro')
        rc_tipo='De Venta'
        if fact.tipo == 'O':
            rc_tipo='Otra'
        elif fact.tipo == 'A':
            rc_tipo='Ajuste'
        elif fact.tipo == 'K':
            rc_tipo='Vulca'
        elif fact.tipo == 'R':
            rc_tipo='Regrabable'
    # Verificar si se puede editar. Se puede editar si todos los cascos relacionados con el estado es Casco
    #editar=editar_documento(filas,idfa)
    
        return render_to_response('comercial/viewfacturapart.html',{'eliminar':0,'editar':1,'cancelar':0,'confirmar':0,
                                                            'importecup':importecup,'ci':rc_ci,
                                                            'tipo':rc_tipo,'rc_nro':rc_nro,'fecha':rc_fecha,'cliente':rc_cliente,
                                                            'observaciones':rc_observaciones,'rc_id':idfa,'elementos_detalle':filas, 
                                                            'error2':l},context_instance = RequestContext(request))
    try:
        filas = DetalleFacturaPart.objects.filter(factura=idfa)
        for canti in filas:
            actualiza_traza(canti.casco.id_casco,idfa)
        
        Doc.objects.select_related().get(pk=idfa).delete()
        
        return HttpResponseRedirect('/comerciax/comercial/facturapart/index')
        #return render_to_response("casco/recepcionclienteindex.html",locals(),context_instance = RequestContext(request))
    except Exception,e:
        transaction.rollback()
        l = ['Error al eliminar el documento']
        fact = FacturasParticular.objects.select_related().get(pk=idfa)
        rc_fecha=fact.doc_factura.fecha_doc.strftime("%d/%m/%Y")
        rc_cliente=fact.nombre
        rc_ci=fact.ci
        rc_nro=fact.factura_nro
        rc_observaciones=fact.doc_factura.observaciones
        filas = DetalleFacturaPart.objects.select_related().filter(factura=idfa).order_by('casco_casco.casco_nro')
       
        return render_to_response('comercial/viewfacturapart.html',{'ci':rc_ci,'rc_nro':rc_nro,'fecha':rc_fecha,'cliente':rc_cliente,'observaciones':rc_observaciones,'rc_id':idfa,'elementos_detalle':filas, 'error2':l},context_instance = RequestContext(request))
    else:
        transaction.commit()
 
    return 0


@login_required
@transaction.commit_on_success()
def facturapart_confirmar(request,idfa):
    if not request.user.has_perm('comercial.factura'):
        return render_to_response("denegado.html",locals(),context_instance = RequestContext(request))
#    FacturasParticular.objects.filter(pk=idfa).update(confirmada=hashlib.sha1(idfa.__str__()+'YES').hexdigest())
    l=[]
    fact=FacturasParticular.objects.get(pk=idfa)
    if fact.get_renglones()>30:
        l=["La factura excede los 30 renglones, no se puede confirmar"]
        cancelar=0
        fact = FacturasParticular.objects.select_related().get(pk=idfa)
        if fact.cancelada==True:
            cancelar=1
        confir=fact.get_confirmada()
        confirmar=2
        if confir=='N':
            confirmar=0
        elif confir=='S':
            confirmar=1
    
        eliminar=1
        editar=1
        if confirmar==2 or confirmar==1:
            eliminar=0  
            editar=0
         
        rc_fecha=fact.doc_factura.fecha_doc.strftime("%d/%m/%Y")
        rc_cliente=fact.nombre
        rc_ci=fact.ci
        rc_nro=fact.factura_nro
        importecup=FacturasParticular.objects.get(pk=idfa).get_importe()
        cant_cascos=FacturasParticular.objects.get(pk=idfa).cantidad_casco() 
        crenglones=FacturasParticular.objects.get(pk=idfa).get_renglones()
        importecasco=FacturasParticular.objects.get(pk=idfa).get_importe_venta()         
        rc_observaciones=fact.doc_factura.observaciones
        filas = DetalleFacturaPart.objects.select_related().filter(factura=idfa).order_by('casco__producto_salida__descripcion','casco_casco.casco_nro')
        rc_tipo='De Venta'
        if fact.tipo == 'O':
            rc_tipo='Otra'
        elif fact.tipo == 'A':
            rc_tipo='Ajuste'
        elif fact.tipo == 'K':
            rc_tipo='Vulca'
        elif fact.tipo == 'R':
            rc_tipo='Regrabable'
        for a in filas:
            z=a.format_precio_particular()
            
        elementos_detalle=[]
        id1=''
        k=0
        k2=0
        t_preciocuc=0.0
        t_preciocup=0.0  
        t_preciocasco=0.0  
        
        for a1 in filas:
            if k!=0:
                if id1!=a1.casco.producto_salida.id:
                    elementos_detalle[k-1]['cantidad'] = k2
                    elementos_detalle[k-1]['t_preciocup'] = t_preciocup
                    elementos_detalle[k-1]['t_preciocasco'] = t_preciocasco
                    t_preciocuc=0.0
                    t_preciocup=0.0 
                    t_preciocasco=0.0
                    k2=0
            elementos_detalle+=[{'casco_id':a1.casco.id_casco,
                                 'casco_nro':a1.casco.casco_nro,'productosalida':a1.casco.producto_salida.descripcion,
                                 'productoid':a1.casco.producto.id,'precio_cup':a1.format_precio_particular(),
                                 'precio_casco':a1.format_precio_casco()}]
            k+=1
            k2+=1
            t_preciocup+=float(a1.precio_particular)
            t_preciocasco+=float(a1.precio_casco)
            id1=a1.casco.producto_salida.id  
        if k!=0:
            elementos_detalle[k-1]['cantidad'] = k2    
            elementos_detalle[k-1]['t_preciocup'] = t_preciocup
            elementos_detalle[k-1]['t_preciocasco'] = t_preciocasco
        return render_to_response('comercial/viewfacturapart.html',{'crenglones':crenglones,'total_casco':k,'eliminar':eliminar,'editar':editar,'cancelar':cancelar,'confirmar':confirmar,
                                                                'ci':rc_ci,'importecup':importecup,
                                                                'tipo':rc_tipo,'rc_nro':rc_nro,'fecha':rc_fecha,'cliente':rc_cliente,
                                                                'observaciones':rc_observaciones,'rc_id':idfa,'elementos_detalle':elementos_detalle,
                                                                'cant_cascos':cant_cascos, 'importecasco':importecasco,
                                                                'error2':l},context_instance = RequestContext(request))
    
    pk_user=User.objects.get(pk=request.user.id)
    
    nrodoc=1
    if NumeroDoc.objects.count()!=0:
        nrodoc=NumeroDoc.objects.get().nro_facturapart+1
    nume=NumeroDoc()
    if NumeroDoc.objects.count()==0:
        nume.id_numerodoc=uuid4()
    else:
        nume=NumeroDoc.objects.get()
    nume.nro_facturapart=nrodoc
    nume.save()
    Doc.objects.filter(pk=FacturasParticular.objects.get(pk=idfa).doc_factura).update(operador=pk_user)
    FacturasParticular.objects.filter(pk=idfa).update(confirmada=hashlib.sha1(idfa.__str__()+'YES').hexdigest(),factura_nro=nrodoc,confirmar=True)
#    Doc.objects.filter(pk=FacturasParticular.objects.get(pk=idfa).doc_factura).update(operador=pk_user)
        
    #fact.confirmada=hashlib.sha1(pk_doc.__str__()+'NO').hexdigest()
    #return HttpResponseRedirect('/comerciax/comercial/factura/index') 
    return HttpResponseRedirect('/comerciax/comercial/facturapart/view/' + idfa)

@login_required
@transaction.commit_on_success()
def facturapart_imprimir(request,idfa):
    
    if not request.user.has_perm('comercial.factura'):
        return render_to_response("denegado.html",locals(),context_instance = RequestContext(request))
    
    l=[]
    fact=FacturasParticular.objects.get(pk=idfa)
    if fact.confirmada != hashlib.sha1(fact.pk.__str__()+'YES').hexdigest():
        mensa="No se puede imprimir la factura Nro. "+fact.factura_nro+" porque no está confirmada"
        l=[mensa]
        rc_fecha=fact.doc_factura.fecha_doc.strftime("%d/%m/%Y")
        rc_cliente=fact.cliente.nombre
        rc_nro=fact.factura_nro
        importecup=FacturasParticular.objects.get(pk=idfa).get_importetotalcup()  
        importecuc=FacturasParticular.objects.get(pk=idfa).get_importecuc() 
    
        pmn=ClienteContrato.objects.select_related().get(cliente=fact.cliente.id,cerrado=False)
        mncosto=pmn.contrato.preciocostomn
        cuccosto=pmn.contrato.preciocostocuc
    
        precio_CUP="Precio CUP"
        if(mncosto==True):
            precio_CUP=precio_CUP+"(Costo)"
                
        precio_CUC="Precio MLC"
        if (cuccosto==True):
            precio_CUC=precio_CUC+"(Costo)"
                    
        rc_observaciones=fact.doc_factura.observaciones
        filas = DetalleFacturaPart.objects.select_related().filter(factura=idfa).order_by('casco_casco.casco_nro')
        rc_tipo='De Venta'
        if fact.tipo == 'O':
            rc_tipo='Otra'
        elif fact.tipo == 'A':
            rc_tipo='Ajuste'
        elif fact.tipo == 'K':
            rc_tipo='Vulca'
        elif fact.tipo == 'R':
            rc_tipo='Regrabable'
        rc_transportador=fact.transportador.nombre
        rc_chapa=fact.chapa
        rc_licencia=fact.licencia
    # Verificar si se puede editar. Se puede editar si todos los cascos relacionados con el estado es Casco
    #editar=editar_documento(filas,idfa)
        hay_cup=0
        hay_cuc=0
        return render_to_response('comercial/viewfactura.html',{'hay_cup':hay_cup,'hay_cuc':hay_cuc,'eliminar':0,'editar':1,'cancelar':0,'confirmar':0,'transportador':rc_transportador,'chapa':rc_chapa,
                                                            'transportador':rc_transportador,'chapa':rc_chapa,'licencia':rc_licencia,'precio_CUC':precio_CUC,
                                                            'precio_CUP':precio_CUP,'importecuc':importecuc,'importecup':importecup,
                                                            'tipo':rc_tipo,'rc_nro':rc_nro,'fecha':rc_fecha,'cliente':rc_cliente,
                                                            'observaciones':rc_observaciones,'rc_id':idfa,'elementos_detalle':filas, 
                                                            'error2':l},context_instance = RequestContext(request))

    return 0

@login_required
@transaction.commit_on_success()
def facturapart_cancelar(request,idfa):
    if not request.user.has_perm('comercial.factura'):
        return render_to_response("denegado.html",locals(),context_instance = RequestContext(request))
    
    l=[]
    fact=FacturasParticular.objects.get(pk=idfa)
    pagosfact=PagosFacturasPart.objects.filter(facturas=fact).count()
    
    if fact.confirmada != hashlib.sha1(fact.pk.__str__()+'YES').hexdigest() or pagosfact!=0:
        mensa="No se puede cancelar la factura Nro. "+fact.factura_nro+" porque no está confirmada"
        if pagosfact>0:
            mensa="No se puede cancelar la factura Nro. "+fact.factura_nro+" porque se han realizado pagos"
        l=[mensa]
        rc_fecha=fact.doc_factura.fecha_doc.strftime("%d/%m/%Y")
        rc_cliente=fact.nombre
        rc_ci=fact.ci
        rc_nro=fact.factura_nro
        importecup=FacturasParticular.objects.get(pk=idfa).get_importe()  
                    
        rc_observaciones=fact.doc_factura.observaciones
        filas = DetalleFacturaPart.objects.select_related().filter(factura=idfa).order_by('casco_casco.casco_nro')
        rc_tipo='De Venta'
        if fact.tipo == 'O':
            rc_tipo='Otra'
        elif fact.tipo == 'A':
            rc_tipo='Ajuste'
        elif fact.tipo == 'K':
            rc_tipo='Vulca'
        elif fact.tipo == 'R':
            rc_tipo='Regrabable'
    # Verificar si se puede editar. Se puede editar si todos los cascos relacionados con el estado es Casco
    #editar=editar_documento(filas,idfa)
        return render_to_response('comercial/viewfacturapart.html',{'ci':rc_ci,'eliminar':0,'editar':1,'cancelar':0,'confirmar':0,
                                                            'importecup':importecup,
                                                            'tipo':rc_tipo,'rc_nro':rc_nro,'fecha':rc_fecha,'cliente':rc_cliente,
                                                            'observaciones':rc_observaciones,'rc_id':idfa,'elementos_detalle':filas, 
                                                            'error2':l},context_instance = RequestContext(request))

    try:
        
        filas = DetalleFacturaPart.objects.filter(factura=idfa)
        for canti in filas:
            actualiza_traza(canti.casco.id_casco,idfa)
        FacturasParticular.objects.filter(pk=idfa).update(cancelada=True)
        pk_user=User.objects.get(pk=request.user.id)
        Doc.objects.filter(pk=FacturasParticular.objects.get(pk=idfa).doc_factura).update(operador=pk_user)
            
        #Doc.objects.select_related().get(pk=idfa).delete()
        return HttpResponseRedirect('/comerciax/comercial/facturapart/index')
        #return render_to_response("casco/recepcionclienteindex.html",locals(),context_instance = RequestContext(request))
    except Exception,e :
        transaction.rollback()
        l = ['Error al cancelar factura']
        fact = FacturasParticular.objects.select_related().get(pk=idfa)
        importecup=FacturasParticular.objects.get(pk=idfa).get_importetotalcup()  
    
        rc_fecha=fact.doc_factura.fecha_doc.strftime("%d/%m/%Y")
        rc_cliente=fact.nombre
        rc_ci=fact.ci
        rc_nro=fact.factura_nro
        rc_observaciones=fact.doc_factura.observaciones
        rc_tipo='De Venta'
        if fact.tipo == 'O':
            rc_tipo='Otra'
        elif fact.tipo == 'A':
            rc_tipo='Ajuste'
        elif fact.tipo == 'K':
            rc_tipo='Vulca'
        elif fact.tipo == 'R':
            rc_tipo='Regrabable'
        
        filas = DetalleFacturaPart.objects.select_related().filter(factura=idfa).order_by('casco_casco.casco_nro')
  
        return render_to_response('comercial/viewfacturapart.html',{'ci':rc_ci,
                                                            'importecup':importecup,
                                                            'tipo':rc_tipo,'rc_nro':rc_nro,'fecha':rc_fecha,'cliente':rc_cliente,
                                                            'observaciones':rc_observaciones,'rc_id':idfa,'elementos_detalle':filas, 
                                                            'error2':l},context_instance = RequestContext(request))
    else:
        transaction.commit()
 
      
#############################################################
#        DETALLE FACTURA
#############################################################
@login_required
def detalle_facturapart_list(request,idfa,medida):
    cascos = DetalleFacturaPart.objects.select_related().filter(factura=idfa,).order_by('casco_casco.casco_nro')    
#    cascos=Casco.objects.select_related().filter(estado_actual__in=filtro,producto__id=idprod).order_by('admincomerciax_producto.descripcion','casco_nro')
    
    lista_valores=[]
    for detalles in cascos:
        lista_valores=lista_valores+[{"casco_nro":detalles.casco_nro,"pk":detalles.id_casco,"medida":detalles.producto.descripcion,"cliente":detalles.get_cliente()}]
    
    return HttpResponse(simplejson.dumps(lista_valores),content_type = 'application/javascript; charset=utf8')

@login_required
#@transaction.commit_on_success()
def detalleFacturapart_add(request,idfa):
    
    if not request.user.has_perm('comercial.factura'):
        return render_to_response("denegado.html",locals(),context_instance = RequestContext(request))
    
    l=[]
    fact=FacturasParticular.objects.get(pk=idfa)
    medidas=Producto.objects.all()
    noelim=0
    if fact.confirmada == hashlib.sha1(fact.pk.__str__()+'YES').hexdigest():
        mensa="No se puede adicionar cascos a la factura Nro. "+fact.factura_nro+" porque ya está confirmada"
        noelim=1
    elif fact.confirmada != hashlib.sha1(fact.pk.__str__()+'NO').hexdigest():
        mensa="No se puede adcionar cascos a la factura Nro. "+fact.factura_nro+" porque está corrupta"
        noelim=1
        #return HttpResponseRedirect('/comerciax/comercial/factura/view/'+idfa) 
    if noelim==1:
        l=[mensa]
        rc_fecha=fact.doc_factura.fecha_doc.strftime("%d/%m/%Y")
        rc_cliente=fact.cliente.nombre
        rc_nro=fact.factura_nro
        importecup=FacturasParticular.objects.get(pk=idfa).get_importetotalcup() 
                    
        rc_observaciones=fact.doc_factura.observaciones
        filas = DetalleFacturaPart.objects.select_related().filter(factura=idfa).order_by('casco_casco.casco_nro')
        rc_tipo='De Venta'
        if fact.tipo == 'O':
            rc_tipo='Otra'
        elif fact.tipo == 'A':
            rc_tipo='Ajuste'
        elif fact.tipo == 'K':
            rc_tipo='Vulca'
        elif fact.tipo == 'R':
            rc_tipo='Regrabable'
        return render_to_response('comercial/viewfacturapart.html',{'eliminar':0,'editar':1,'cancelar':0,'confirmar':0,
                                                            'importecup':importecup,
                                                            'tipo':rc_tipo,'rc_nro':rc_nro,'fecha':rc_fecha,'cliente':rc_cliente,
                                                            'observaciones':rc_observaciones,'rc_id':idfa,'elementos_detalle':filas, 
                                                            'error2':l},context_instance = RequestContext(request))

    titulo_form='Facturas' 
    controlador_form='Facturas'
    descripcion_form='Seleccionar cascos para la factura2'
    
    accion_form='detalleFacturapart_add'
    cancelbtn_form='/comerciax/comercial/facturapart/view/'+idfa
    
     
    fact=FacturasParticular.objects.get(pk=idfa)
      
    if request.method == 'POST':
        seleccion=request.POST.keys()
        k=0

        while True:
            if k==seleccion.__len__():
                break
            casco=Casco.objects.filter(pk=seleccion[k])

            if casco.count()!=0:
                '''
                Los selecionados los cambio de estado, agregar a detalle del documento y actualizar trazabilidad
                
                Casco.objects.filter(pk=seleccion[k]).update(estado_actual=Estados.estados["Factura"])
                '''
                
                detalle=DetalleFacturaPart()
                if DetalleFacturaPart.objects.filter(factura=idfa, casco=Casco.objects.get(pk=seleccion[k])).count()!=0:
                    detalle=DetalleFacturaPart.objects.get(factura=idfa, casco=Casco.objects.get(pk=seleccion[k]))
                else:
                    detalle.id_detalle=uuid4()
                    
                detalle.factura=FacturasParticular.objects.get(pk=idfa)
                detalle.casco=Casco.objects.get(pk=seleccion[k])
                if detalle.factura.tipo=='K':
                    detalle.precio_particular=detalle.casco.producto_salida.precio_vulca
                else:   
                    detalle.precio_particular=detalle.casco.producto_salida.precio_particular
                
                if detalle.casco.venta==True and detalle.casco.decomisado==False:
                    if not detalle.casco.id_cliente.get_precio_casco():
                        detalle.precio_casco=detalle.casco.producto_salida.precio_casco
                    else:
                        detalle.precio_casco=detalle.casco.producto_salida.otro_precio_casco
                    
                detalle.save()
                
                Casco.objects.filter(pk=seleccion[k]).update(estado_actual="Factura")
                add_trazabilidad(seleccion[k], idfa, "Factura")
                
            k=k+1
            
            
        if request.POST.__contains__('submit1'):
            if fact.tipo=='V':
#                return render_to_response('comercial/seleccionar_casco.html', {'cant_elem':cant_elem,'title':titulo_form,'controlador':controlador_form,'accion':accion_form,
#                                                     'cancelbtn':cancelbtn_form,'elementos_detalle1':filas_result, 'nro':fact.factura_nro,'form_description':descripcion_form,
#                                                     'fecha':fact.doc_factura.fecha_doc.strftime("%d/%m/%Y"),'observaciones':fact.doc_factura.observaciones,
#                                                     'rc_id':idfa},context_instance = RequestContext(request))
                return render_to_response('comercial/seleccionar_casco_particular.html', {'medidas':medidas,'title':titulo_form,'controlador':controlador_form,'accion':accion_form,
                                                      'cancelbtn':cancelbtn_form,'nro':fact.factura_nro,'form_description':descripcion_form,
                                                      'fecha':fact.doc_factura.fecha_doc.strftime("%d/%m/%Y"),'observaciones':fact.doc_factura.observaciones,
                                                      'rc_id':idfa,'dettransfe':True, 'es_part':1},context_instance = RequestContext(request))
#            return render_to_response('comercial/seleccionar_casco.html', {'cant_elem':cant_elem,'title':titulo_form,'controlador':controlador_form,'accion':accion_form,
#                                                     'cancelbtn':cancelbtn_form,'elementos_detalle1':filas_result, 'nro':fact.factura_nro,'form_description':descripcion_form,
#                                                     'fecha':fact.doc_factura.fecha_doc.strftime("%d/%m/%Y"),'observaciones':fact.doc_factura.observaciones,
#                                                     'rc_id':idfa},context_instance = RequestContext(request))
        else:
            return HttpResponseRedirect('/comerciax/comercial/facturapart/view/' + idfa)
    if fact.tipo=='V':
#        return render_to_response('comercial/seleccionar_casco.html', {'medidas':medidas,'title':titulo_form,'controlador':controlador_form,'accion':accion_form,
#                                                      'cancelbtn':cancelbtn_form,'nro':fact.factura_nro,'form_description':descripcion_form,
#                                                      'fecha':fact.doc_factura.fecha_doc.strftime("%d/%m/%Y"),'observaciones':fact.doc_factura.observaciones,
#                                                      'rc_id':idfa,'dettransfe':True},context_instance = RequestContext(request))
        return render_to_response('comercial/seleccionar_casco_particular.html', {'medidas':medidas,'title':titulo_form,'controlador':controlador_form,'accion':accion_form,
                                                      'cancelbtn':cancelbtn_form,'nro':fact.factura_nro,'form_description':descripcion_form,
                                                      'fecha':fact.doc_factura.fecha_doc.strftime("%d/%m/%Y"),'observaciones':fact.doc_factura.observaciones,
                                                      'rc_id':idfa,'dettransfe':True, 'es_part':1},context_instance = RequestContext(request)) 
        
#        return render_to_response('comercial/seleccionar_casco.html', {'cant_elem':cant_elem,'title':titulo_form,'controlador':controlador_form,'accion':accion_form,
#                                                      'cancelbtn':cancelbtn_form,'elementos_detalle1':filas_result,'nro':fact.factura_nro,'form_description':descripcion_form,
#                                                      'fecha':fact.doc_factura.fecha_doc.strftime("%d/%m/%Y"),'observaciones':fact.doc_factura.observaciones,
#                                                      'rc_id':idfa,'dettransfe':True},context_instance = RequestContext(request)) 
#    return render_to_response('comercial/seleccionar_casco.html', {'cant_elem':cant_elem,'title':titulo_form,'controlador':controlador_form,'accion':accion_form,
#                                                      'cancelbtn':cancelbtn_form,'elementos_detalle1':filas_result, 'nro':fact.factura_nro,'form_description':descripcion_form,
#                                                      'fecha':fact.doc_factura.fecha_doc.strftime("%d/%m/%Y"),'observaciones':fact.doc_factura.observaciones,
#                                                      'rc_id':idfa,'dettransfe':True},context_instance = RequestContext(request)) 
    return render_to_response('comercial/seleccionar_casco_particular.html', {'medidas':medidas,'title':titulo_form,'controlador':controlador_form,'accion':accion_form,
                                                      'cancelbtn':cancelbtn_form,'nro':fact.factura_nro,'form_description':descripcion_form,
                                                      'fecha':fact.doc_factura.fecha_doc.strftime("%d/%m/%Y"),'observaciones':fact.doc_factura.observaciones,
                                                      'rc_id':idfa,'dettransfe':True,'es_part':1},context_instance = RequestContext(request))  

@login_required
def detalleFacturapart_delete(request,idfa,idcasco):
    if not request.user.has_perm('comercial.factura'):
        return render_to_response("denegado.html",locals(),context_instance = RequestContext(request))
    
    
    fact=FacturasParticular.objects.get(pk=idfa)
    noelim=0
    if fact.confirmada == hashlib.sha1(fact.pk.__str__()+'YES').hexdigest():
        mensa="No se puede eliminar cascos a la factura Nro. "+fact.factura_nro+" porque ya está confirmada"
        noelim=1
    elif fact.confirmada != hashlib.sha1(fact.pk.__str__()+'NO').hexdigest():
        mensa="No se puede eliminar cascos a la factura Nro. "+fact.factura_nro+" porque está corrupta"
        noelim=1
        #return HttpResponseRedirect('/comerciax/comercial/factura/view/'+idfa) 
    if noelim==1:
        l=[mensa]
        rc_fecha=fact.doc_factura.fecha_doc.strftime("%d/%m/%Y")
        rc_cliente=fact.nombre
        rc_ci=fact.ci
        rc_nro=fact.factura_nro
        importecup=FacturasParticular.objects.get(pk=idfa).get_importe() 
    
        rc_observaciones=fact.doc_factura.observaciones
        filas = DetalleFacturaPart.objects.select_related().filter(factura=idfa).order_by('casco_casco.casco_nro')
        rc_tipo='De Venta'
        if fact.tipo == 'O':
            rc_tipo='Otra'
        elif fact.tipo == 'A':
            rc_tipo='Ajuste'
        elif fact.tipo == 'K':
            rc_tipo='Vulca'
        elif fact.tipo == 'R':
            rc_tipo='Regrabable'
    # Verificar si se puede editar. Se puede editar si todos los cascos relacionados con el estado es Casco
    #editar=editar_documento(filas,idfa)
        return render_to_response('comercial/viewfacturapart.html',{'editar':1,'cancelar':0,'confirmar':0,
                                                            'importecup':importecup,
                                                            'tipo':rc_tipo,'rc_nro':rc_nro,'fecha':rc_fecha,'cliente':rc_cliente,'ci':rc_ci,
                                                            'observaciones':rc_observaciones,'rc_id':idfa,'elementos_detalle':filas, 
                                                            'error2':l},context_instance = RequestContext(request))

    l=[]
    casco=Casco.objects.select_related().get(pk=idcasco)
    
    DetalleFacturaPart.objects.get(casco=idcasco,factura=idfa).delete()
    actualiza_traza(idcasco,idfa)
        
    cant_renglones = str(FacturasParticular.objects.get(doc_factura=idfa).get_renglones())
    data=[]   
    filas = DetalleFacturaPart.objects.select_related().filter(factura=idfa).order_by('casco__producto_salida__descripcion','casco__casco_nro')
    total_casco=str(filas.count())
    elementos_detalle=[]
    id1=''
    k=0
    k2=0
    t_preciocup=0.0  
    t_preciocasco=0.0  
    
    for a1 in filas:
        if k!=0:
            if id1!=a1.casco.producto_salida.id:
                elementos_detalle[k-1]['cantidad'] = k2
                elementos_detalle[k-1]['t_preciocup'] = t_preciocup
                elementos_detalle[k-1]['t_preciocasco'] = t_preciocasco
                elementos_detalle[k-1]['crenglones'] = cant_renglones
                t_preciocup=0.0 
                t_preciocasco=0.0
                k2=0
        if k==0:
            importetotalcup=a1.factura.get_importe_venta()
            importetotalcasco=a1.factura.get_importe()
            recargo = a1.factura.recargo
            total_pagar = a1.factura.get_importe_total(recargo)
            elementos_detalle+=[{'total_casco':total_casco,'cant_renglones':cant_renglones,'id_doc':a1.factura.doc_factura.id_doc,
                                 'importetotalcup':importetotalcup,'casco_id':a1.casco.id_casco,
                                 'recargo': str(a1.factura.format_recargo()), 'total_pagar': total_pagar,
                             'casco_nro':a1.casco.casco_nro,'productosalida':a1.casco.producto_salida.descripcion,
                             'productoid':a1.casco.producto.id,'precio_cup':a1.format_precio_particular(),
                             'importetotalcasco':importetotalcasco,
                             'precio_casco':a1.format_precio_casco()
                                 }]
        else:
            elementos_detalle+=[{'id_doc':a1.factura.doc_factura.id_doc,'casco_id':a1.casco.id_casco,
                             'casco_nro':a1.casco.casco_nro,'productosalida':a1.casco.producto_salida.descripcion,
                             'productoid':a1.casco.producto.id,'precio_cup':a1.format_precio_particular(),
                             'precio_casco':a1.format_precio_casco()}]
        k+=1
        k2+=1
        t_preciocup+=float(a1.precio_particular)
        t_preciocasco+=float(a1.precio_casco)
        id1=a1.casco.producto_salida.id  
    if k!=0:
        elementos_detalle[k-1]['cantidad'] = k2
        elementos_detalle[k-1]['t_preciocup'] = '{:20,.2f}'.format(t_preciocup)
        elementos_detalle[k-1]['t_preciocasco'] = '{:20,.2f}'.format(t_preciocasco)

    return HttpResponse(simplejson.dumps(elementos_detalle),content_type = 'application/javascript; charset=utf8')
#        
#    json_serializer = serializers.get_serializer("json")()
#    response = HttpResponse()
#    response["Content-type"] = "text/json"
#
#    json_serializer.serialize(detalleofe,ensure_ascii = False, stream = response, use_natural_keys=True)
#        #json_serializer.serialize(detallerc,ensure_ascii = False, stream = response)
#    return response


@login_required
@transaction.commit_on_success()
def detalleFacturaPart_edit(request,idfa,idcasco):
    if not request.user.has_perm('comercial.factura'):
        return render_to_response("denegado.html",locals(),context_instance = RequestContext(request))
    
    c=None
    l=[]
    
    nombre_form='Editar Casco Facturado'
    descripcion_form='Editar Casco Facturado'
    titulo_form='Editar Casco Facturado' 
    controlador_form='Editar Casco Facturado'
    accion_form='detalleFacturaPart_edit/' + idfa +'/' +idcasco
    cancelbtn_form='/comerciax/comercial/facturapart/view/' + idfa +'/'
    
    
    if request.method == 'POST':
        form = DetalleFacturaForm(request.POST)
        
        if form.is_valid():
            fact=FacturasParticular.objects.select_related().get(pk=idfa)
            #form = DetalleRCForm(request.POST)
            casco_medida=form.data['medida_salida']
            cascosave=Casco.objects.get(pk=idcasco)
            detalle=DetalleFacturaPart.objects.get(casco=cascosave,factura=fact)
            producto=Producto.objects.get(pk=casco_medida)
#            DetalleFactura.objects.filter(casco=cascosave).update(precio_mn=Producto.objects.get(pk = casco_medida).)

            try:
                cascosave.producto_salida=Producto.objects.get(pk = casco_medida)
                if detalle.casco.venta==True and detalle.casco.decomisado==False:
                    if not detalle.casco.id_cliente.get_precio_casco():
                        detalle.precio_casco=detalle.casco.producto_salida.precio_casco
                    else:
                        detalle.precio_casco=detalle.casco.producto_salida.otro_precio_casco
                detalle.precio_particular=producto.precio_particular
                
                cascosave.save()
                detalle.save()
                importecup=FacturasParticular.objects.get(pk=idfa).get_importetotalcup()
                return facturapart_view(request, idfa)
            except Exception, e:
                exc_info = e.__str__() # sys.exc_info()[:1]
                c = exc_info.find("DETAIL:")
                if c < 0:
                    l = l + ["Error Fatal."]
                else:
                    c = exc_info[c + 7:]
                    #l=l+[c]
                    l=['Error al cambiar la medida de salida del casco']
                transaction.rollback()
                form = DetalleFacturaForm(request.POST)
                return render_to_response("form/form_edit.html",{'tipocliente':'0','form':form,'title':titulo_form, 'form_name': nombre_form,'form_description':descripcion_form,'controlador':controlador_form,'accion':accion_form
                                                         , 'cancelbtn':cancelbtn_form,'error2':l},context_instance = RequestContext(request))
            else:
                transaction.commit()
    else:   
        rc =Casco.objects.select_related().get(id_casco=idcasco)
        form = DetalleFacturaForm(initial={'medida_salida':rc.producto_salida})
        return render_to_response('form/form_edit.html',  {'tipocliente':'0','form': form, 'form_name':nombre_form,'form_description':descripcion_form,'accion':accion_form,'titulo':titulo_form,'controlador':controlador_form,'cancelbtn':cancelbtn_form},context_instance = RequestContext(request))
    return facturapart_view(request, idfa)  

#===============================================================================
# 
#===============================================================================
def ofertadetalle_view(request,idof):
    #return render_to_response("comercial/viewdetalleoferta.html",locals(),context_instance = RequestContext(request))
    ofer=Oferta.objects.get(pk=idof)
    
    filas=DetalleOferta.objects.select_related().filter(oferta=idof).order_by('admincomerciax_producto.descripcion','casco_casco.casco_nro')
    return render_to_response('comercial/viewdetalleoferta.html', {'elementos_detalle':filas},context_instance = RequestContext(request))   


@login_required
#@transaction.commit_on_success()
def detalleFactura_addofer(request,idfa):
    if not request.user.has_perm('comercial.factura'):
        return render_to_response("denegado.html",locals(),context_instance = RequestContext(request))
    
    l=[]
    fact=Facturas.objects.get(pk=idfa)
    noelim=0
    if fact.confirmada == hashlib.sha1(fact.pk.__str__()+'YES').hexdigest():
        mensa="No se puede adicionar cascos a la factura Nro. "+fact.factura_nro+" porque ya está confirmada"
        noelim=1
    elif fact.confirmada != hashlib.sha1(fact.pk.__str__()+'NO').hexdigest():
        mensa="No se puede adcionar cascos a la factura Nro. "+fact.factura_nro+" porque está corrupta"
        noelim=1
        #return HttpResponseRedirect('/comerciax/comercial/factura/view/'+idfa) 
    if noelim==1:
        l=[mensa]
        rc_fecha=fact.doc_factura.fecha_doc.strftime("%d/%m/%Y")
        rc_cliente=fact.cliente.nombre
        rc_nro=fact.factura_nro
        importecup=Facturas.objects.get(pk=idfa).get_importetotalcup()
        importecuc=Facturas.objects.get(pk=idfa).get_importecuc() 
    
        pmn=ClienteContrato.objects.select_related().get(cliente=fact.cliente.id,cerrado=False)
        mncosto=pmn.contrato.preciocostomn
        cuccosto=pmn.contrato.preciocostocuc
    
        precio_CUP="Precio CUP"
        if(mncosto==True):
            precio_CUP=precio_CUP+"(Costo)"
                
        precio_CUC="Precio CUC"
        if (cuccosto==True):
            precio_CUC=precio_CUC+"(Costo)"
                    
        rc_observaciones=fact.doc_factura.observaciones
        filas = DetalleFactura.objects.select_related().filter(factura=idfa).order_by('casco_casco.casco_nro')
        for ss in filas:
            aa=ss.oferta.doc_oferta.id_doc
        rc_tipo='De Venta'
        if fact.tipo == 'O':
            rc_tipo='Otra'
        elif fact.tipo == 'A':
            rc_tipo='Ajuste'
        elif fact.tipo == 'K':
            rc_tipo='Vulca'
        elif fact.tipo == 'R':
            rc_tipo='Regrabable'
        rc_transportador=fact.transportador.nombre
        rc_chapa=fact.chapa
        rc_licencia=fact.licencia
    # Verificar si se puede editar. Se puede editar si todos los cascos relacionados con el estado es Casco
    #editar=editar_documento(filas,idfa)
        hay_cup=0
        hay_cuc=0
        return render_to_response('comercial/viewfactura.html',{'hay_cup':hay_cup,'hay_cuc':hay_cuc,'eliminar':0,'editar':1,'cancelar':0,'confirmar':0,'transportador':rc_transportador,'chapa':rc_chapa,
                                                            'transportador':rc_transportador,'licencia':rc_licencia,'precio_CUC':precio_CUC,
                                                            'precio_CUP':precio_CUP,'importecuc':importecuc,'importecup':importecup,
                                                            'tipo':rc_tipo,'rc_nro':rc_nro,'fecha':rc_fecha,'cliente':rc_cliente,
                                                            'observaciones':rc_observaciones,'rc_id':idfa,'elementos_detalle':filas, 
                                                            'error2':l},context_instance = RequestContext(request))

    titulo_form='Facturas' 
    controlador_form='Facturas'
    descripcion_form='Seleccionar oferta para la factura'
    
    accion_form='detalleFactura_addofer'
    cancelbtn_form='/comerciax/comercial/factura/view/'+idfa
    
     
    #fact=Facturas.objects.get(pk=idfa)
    idcliente=fact.cliente
    #recep=RecepcionCliente.objects.filter(cliente=Cliente.objects.get(pk=fact.cliente.id))
    
    #lista_doc={}
    #for rec in recep:
        #lista_doc=lista_doc+[RecepcionCliente.objects.get(pk=rec.doc_recepcioncliente)]

    #filas=DetalleRC.objects.filter(rc__in=lista_doc, casco__estado_actual=Estados.estados["PT"]).order_by('casco_casco.casco_nro')
    filas=Oferta.objects.select_related().filter(oferta_tipo=fact.tipo,cliente=idcliente).order_by('oferta_nro')
    if request.method == 'POST':
        pmn=ClienteContrato.objects.select_related().get(cliente=fact.cliente.id,cerrado=False)
        mn=pmn.contrato.preciomn
        mncosto=pmn.contrato.preciocostomn
        cuc=pmn.contrato.preciocuc
        cuccosto=pmn.contrato.preciocostocuc
        seleccion=request.POST.keys()
        k=0

        while True:
            if k==seleccion.__len__():
                break
            cascos=DetalleOferta.objects.filter(oferta=seleccion[k])

            #if casco.count()!=0:
            for casco in cascos:                
                detalle=DetalleFactura()
                deta=DetalleFactura.objects.filter(casco=casco.casco.id_casco, factura=idfa)
                if deta.count()!=0:
                    detalle=DetalleFactura.objects.get(casco=casco.casco.id_casco, factura=idfa)
                else:
                    detalle.id_detalle=uuid4()
                
                    detalle.factura=Facturas.objects.get(pk=idfa)
                    detalle.casco=Casco.objects.get(pk=casco.casco.id_casco)
                    detalle.precio_mn=0
                    if (mn==True):
                        detalle.precio_mn=detalle.casco.producto_salida.precio_mn
                    elif(mncosto==True):
                        detalle.precio_mn=detalle.casco.producto_salida.precio_costo_mn
                    detalle.precio_cuc=0
                    if (cuc==True):
                        detalle.precio_cuc=detalle.casco.producto_salida.precio_cuc
                    elif (cuccosto==True):
                        detalle.precio_cuc=detalle.casco.producto_salida.precio_costo_cuc
                    if detalle.casco.venta and detalle.casco.decomisado==False:
                        if not detalle.casco.id_cliente.get_precio_casco():
                            detalle.precio_casco=detalle.casco.producto_salida.precio_casco
                        else:
                            detalle.precio_casco=detalle.casco.producto_salida.otro_precio_casco
                        
                    detalle.save()
                    if casco.casco.estado_actual!="Factura":
                        add_trazabilidad(casco.casco.id_casco, idfa, "Factura")
                    Casco.objects.filter(pk=casco.casco.id_casco).update(estado_actual="Factura")
            k=k+1
        if request.POST.__contains__('submit1'):
            if fact.tipo=='V':
            #filas=DetalleRC.objects.filter(rc__in=lista_doc, casco__estado_actual=Estados.estados["PT"]).order_by('casco_casco.casco_nro')
                return render_to_response('comercial/seleccionar_oferta.html', {'title':titulo_form,'controlador':controlador_form,'accion':accion_form,
                                                     'cancelbtn':cancelbtn_form,'elementos_detalle':filas,'elementos_detalle':filas, 'nro':fact.factura_nro,'form_description':descripcion_form,
                                                     'fecha':fact.doc_factura.fecha_doc.strftime("%d/%m/%Y"),'observaciones':fact.doc_factura.observaciones,
                                                     'rc_id':idfa},context_instance = RequestContext(request))
            return render_to_response('comercial/seleccionar_oferta.html', {'title':titulo_form,'controlador':controlador_form,'accion':accion_form,
                                                     'cancelbtn':cancelbtn_form,'elementos_detalle':filas, 'nro':fact.factura_nro,'form_description':descripcion_form,
                                                     'fecha':fact.doc_factura.fecha_doc.strftime("%d/%m/%Y"),'observaciones':fact.doc_factura.observaciones,
                                                     'rc_id':idfa},context_instance = RequestContext(request))
        else:
            return HttpResponseRedirect('/comerciax/comercial/factura/view/' + idfa)
    if fact.tipo=='V':
        return render_to_response('comercial/seleccionar_oferta.html', {'title':titulo_form,'controlador':controlador_form,'accion':accion_form,
                                                      'cancelbtn':cancelbtn_form,'elementos_detalle':filas,'elementos_detalle':filas, 'nro':fact.factura_nro,'form_description':descripcion_form,
                                                      'fecha':fact.doc_factura.fecha_doc.strftime("%d/%m/%Y"),'observaciones':fact.doc_factura.observaciones,
                                                      'rc_id':idfa,'dettransfe':True},context_instance = RequestContext(request)) 
    return render_to_response('comercial/seleccionar_oferta.html', {'title':titulo_form,'controlador':controlador_form,'accion':accion_form,
                                                      'cancelbtn':cancelbtn_form,'elementos_detalle':filas, 'nro':fact.factura_nro,'form_description':descripcion_form,
                                                      'fecha':fact.doc_factura.fecha_doc.strftime("%d/%m/%Y"),'observaciones':fact.doc_factura.observaciones,
                                                      'rc_id':idfa,'dettransfe':True},context_instance = RequestContext(request))    

@login_required
@transaction.commit_on_success()
def detalleFactura_edit(request,idfa,idcasco):
    if not request.user.has_perm('comercial.factura'):
        return render_to_response("denegado.html",locals(),context_instance = RequestContext(request))
    
    
    c=None
    l=[]
    
    nombre_form='Editar Casco Facturado'
    descripcion_form='Editar Casco Facturado'
    titulo_form='Editar Casco Facturado' 
    controlador_form='Editar Casco Facturado'
    accion_form='detalleFactura_edit/' + idfa +'/' +idcasco
    cancelbtn_form='/comerciax/comercial/factura/view/' + idfa +'/'
    
    
    if request.method == 'POST':
        form = DetalleFacturaForm(request.POST)
        
        if form.is_valid():
            fact=Facturas.objects.select_related().get(pk=idfa)
            pmn=ClienteContrato.objects.select_related().get(cliente=fact.cliente.id,cerrado=False)
            mn=pmn.contrato.preciomn
            mncosto=pmn.contrato.preciocostomn
            cuc=pmn.contrato.preciocuc
            cuccosto=pmn.contrato.preciocostocuc
            #form = DetalleRCForm(request.POST)
            casco_medida=form.data['medida_salida']
            cascosave=Casco.objects.get(pk=idcasco)
            detalle=DetalleFactura.objects.get(casco=cascosave,factura=fact)
            producto=Producto.objects.get(pk=casco_medida)
#            DetalleFactura.objects.filter(casco=cascosave).update(precio_mn=Producto.objects.get(pk = casco_medida).)

            try:
                cascosave.producto_salida=Producto.objects.get(pk = casco_medida)
                if detalle.casco.venta==True and detalle.casco.decomisado==False:
                    if not detalle.casco.id_cliente.get_precio_casco():
                        detalle.precio_casco=detalle.casco.producto_salida.precio_casco
                    else:
                        detalle.precio_casco=detalle.casco.producto_salida.otro_precio_casco
                if (mn==True):
                    detalle.precio_mn=producto.precio_mn
                elif(mncosto==True):
                    detalle.precio_mn=producto.precio_costo_mn
                detalle.precio_cuc=0
                if (cuc==True):
                    detalle.precio_cuc=producto.precio_cuc
                elif (cuccosto==True):
                    detalle.precio_cuc=producto.precio_costo_cuc
                cascosave.save()
                detalle.save()
                importecup=Facturas.objects.get(pk=idfa).get_importetotalcup()
                importecuc=Facturas.objects.get(pk=idfa).get_importecuc()
                return factura_view(request, idfa)
            except Exception, e:
                exc_info = e.__str__() # sys.exc_info()[:1]
                c = exc_info.find("DETAIL:")
                if c < 0:
                    l = l + ["Error Fatal."]
                else:
                    c = exc_info[c + 7:]
                    #l=l+[c]
                    l=['Error al cambiar la medida de salida del casco']
                transaction.rollback()
                form = DetalleFacturaForm(request.POST)
                return render_to_response("form/form_edit.html",{'tipocliente':'0','form':form,'title':titulo_form, 'form_name': nombre_form,'form_description':descripcion_form,'controlador':controlador_form,'accion':accion_form
                                                         , 'cancelbtn':cancelbtn_form,'error2':l},context_instance = RequestContext(request))
            else:
                transaction.commit()
    else:   
        rc =Casco.objects.select_related().get(id_casco=idcasco)
        form = DetalleFacturaForm(initial={'medida_salida':rc.producto_salida})
        return render_to_response('form/form_edit.html',  {'tipocliente':'0','form': form, 'form_name':nombre_form,'form_description':descripcion_form,'accion':accion_form,'titulo':titulo_form,'controlador':controlador_form,'cancelbtn':cancelbtn_form},context_instance = RequestContext(request))
    return factura_view(request, idfa)  


@login_required
def detalleFactura_delete(request,idfa,idcasco):
    if not request.user.has_perm('comercial.factura'):
        return render_to_response("denegado.html",locals(),context_instance = RequestContext(request))
    
    
    fact=Facturas.objects.get(pk=idfa)

    l=[]
    casco=Casco.objects.select_related().get(pk=idcasco)
    
    DetalleFactura.objects.get(casco=idcasco,factura=idfa).delete()
    actualiza_traza(idcasco,idfa)
    cant_renglones = str(Facturas.objects.get(doc_factura=idfa).get_renglones())
    data=[]   
    filas = DetalleFactura.objects.select_related().filter(factura=idfa).order_by('casco__producto_salida__descripcion','casco__casco_nro')
    total_casco=str(filas.count())
    elementos_detalle=[]
    id1=''
    k=0
    k2=0
    t_preciocuc=0.0
    t_preciocup=0.0  
    t_preciocasco=0.0  
    
    for a1 in filas:
        if k!=0:
            if id1!=a1.casco.producto_salida.id:
                elementos_detalle[k-1]['cantidad'] = k2
                elementos_detalle[k-1]['t_preciocuc'] = t_preciocuc
                elementos_detalle[k-1]['t_preciocup'] = t_preciocup
                elementos_detalle[k-1]['t_preciocasco'] = t_preciocasco
                t_preciocuc=0.0
                t_preciocup=0.0 
                t_preciocasco=0.0
                k2=0
        if k==0: 
            importetotalcup=a1.factura.get_importetotalcup()
            importetotalcuc=a1.factura.get_importecuc()
            importetotalcasco=a1.factura.get_importe_venta()
            
            elementos_detalle+=[{'total_casco':total_casco,'cant_renglones':cant_renglones,'id_doc':a1.factura.doc_factura.id_doc,
                                 'importetotalcup':importetotalcup,'importetotalcuc':importetotalcuc,'casco_id':a1.casco.id_casco,
                             'casco_nro':a1.casco.casco_nro,'productosalida':a1.casco.producto_salida.descripcion,
                             'productoid':a1.casco.producto.id,'precio_cup':a1.format_precio_mn(),'importetotalcasco':importetotalcasco,
                             'precio_cuc':a1.format_precio_cuc(),'precio_casco':a1.format_precio_casco()}]
        else:
            elementos_detalle+=[{'id_doc':a1.factura.doc_factura.id_doc,'casco_id':a1.casco.id_casco,
                             'casco_nro':a1.casco.casco_nro,'productosalida':a1.casco.producto_salida.descripcion,
                             'productoid':a1.casco.producto.id,'precio_cup':a1.format_precio_mn(),
                             'precio_cuc':a1.format_precio_cuc(),'precio_casco':a1.format_precio_casco()}]
        k+=1
        k2+=1
        t_preciocup+=float(a1.precio_mn)
        t_preciocuc+=float(a1.precio_cuc)
        t_preciocasco+=float(a1.precio_casco)
        id1=a1.casco.producto_salida.id  
    if k!=0:
        elementos_detalle[k-1]['cantidad'] = k2    
        elementos_detalle[k-1]['t_preciocuc'] = '{:20,.2f}'.format(t_preciocuc)
        elementos_detalle[k-1]['t_preciocup'] = '{:20,.2f}'.format(t_preciocup)
        elementos_detalle[k-1]['t_preciocasco'] = '{:20,.2f}'.format(t_preciocasco)
    return HttpResponse(simplejson.dumps(elementos_detalle),content_type = 'application/javascript; charset=utf8')


#############################################################
#                  PAGOS EN EFECTIVO PARTICULARES           #
#############################################################
@login_required
def get_pagoefectpart_list(request):
    #prepare the params
    try:
        fecha_desde=Fecha_Ver.objects.get()
    except Exception, e:
        fecha_desde=None
    if  fecha_desde == None:  
        querySet = Pagos.objects.select_related().filter(particulares=True)
    else:
        querySet = Pagos.objects.select_related().filter(particulares=True,fecha_pago__gte=fecha_desde.fecha)
        
    #querySet = querySet.filter(doc__fecha_doc__year=2010)
 
    columnIndexNameMap = {0:'id_pago', 1:'pagosefectivo__nombre', 2:'ci',3:'fecha_pago',4:'tipo_moneda',6:'importe',7:'deposito_adelantado'}

    searchableColumns = ['pagosefectivo__nombre','pagosefectivo__ci','tipo_moneda','importe','deposito_adelantado']
    #path to template used to generate json
    jsonTemplatePath = 'comercial/json/json_pagoefect.txt'

    #call to generic function from utils
    return get_datatables_records(request, querySet, columnIndexNameMap, searchableColumns, jsonTemplatePath)
    

@login_required
def pagoefectpart_index(request):
    if not request.user.has_perm('comercial.pagos'):
        return render_to_response("denegado.html",locals(),context_instance = RequestContext(request))
    return render_to_response('comercial/pagoefectpartindex.html',locals(),context_instance = RequestContext(request))

@login_required
@transaction.commit_on_success()
def pagoefectpart_add(request):
    if not request.user.has_perm('comercial.pagos'):
        return render_to_response("denegado.html",locals(),context_instance = RequestContext(request))
    
    nombre_form='Pagos en efectivo'
    descripcion_form='Realizar Pago en Efectivo'
    titulo_form='Pagos en Efectivo' 
    controlador_form='Pagos en Efectivo'
    accion_form='/comerciax/comercial/pagoefectpart/add'
    cancelbtn_form='/comerciax/comercial/pagoefectpart/index'
    fecha_cierre=datetime.date.today().strftime("%d/%m/%Y")
    fecham=Cierre.objects.all()
    c=None
    l=[]
    for a in fecham:
        fecha_cierre=a.fechacierre.strftime("%d/%m/%Y")
    if request.method == 'POST':
        form = PagoEfectPartForm(request.POST)

        if form.is_valid():
            
            pago=PagosEfectivo()
            
            pk_doc=uuid4()
            obj_pago=Pagos()
            
            obj_pago.id_pago=pk_doc
            obj_pago.fecha_pago=form.cleaned_data['fecha']
            obj_pago.importe=form.cleaned_data['importe']
            obj_pago.efectivo=True
            obj_pago.operador=User.objects.get(pk=request.user.id)
            obj_pago.fecha_operacion=datetime.date.today()
            obj_pago.observaciones=form.cleaned_data['observaciones']
            obj_pago.particulares=True
            
            obj_pago.tipo_moneda=Monedas.objects.get(pk = form.data['moneda'])
            obj_pago.deposito_adelantado=form.cleaned_data['importe']
            
            pago.pagos=obj_pago
            pago.nombre=form.cleaned_data['nombre'] 
            pago.ci=form.cleaned_data['ci']
#            obj_pagocliente=PagosClientes()
            
#            obj_pagocliente.id_pagocliente=uuid4()
#            obj_pagocliente.pagos=obj_pago
            
#            obj_pagocliente.cliente=Cliente.objects.get(pk = form.data['cliente'])
            
         
            try:
                obj_pago.save()
#                obj_pagocliente.save()
                pago.save()
                return HttpResponseRedirect('/comerciax/comercial/pagoefectpart/view/'+pk_doc.__str__())  
            except Exception, e:
                exc_info = e.__str__() # sys.exc_info()[:1]
                c = exc_info.find("DETAIL:")
                
                if c < 0:
                    l=l+["Error Fatal."]
                else:
                    c = exc_info[c + 7:]
                    l=l+[c] 
                                     
                transaction.rollback()
                form = PagoEfectForm(request.POST)
                return render_to_response('form/form_adddetalle.html',  {'tipocliente':'2','form': form, 'form_name':nombre_form,'form_description':descripcion_form,
                                                                         'accion':accion_form,'titulo':titulo_form,'controlador':controlador_form,
                                                                         'cancelbtn':cancelbtn_form,'fecha_minima':fecha_cierre,'error2':l},context_instance = RequestContext(request))
            else:
                transaction.commit()
    else:
        form = PagoEfectPartForm() 
    return render_to_response('form/form_adddetalle.html',  {'tipocliente':'2','form': form, 'form_name':nombre_form,'form_description':descripcion_form,
                                                             'accion':accion_form,'titulo':titulo_form,'controlador':controlador_form,
                                                             'cancelbtn':cancelbtn_form,'fecha_minima':fecha_cierre,'error2':c},context_instance = RequestContext(request))


@login_required
@transaction.commit_on_success()
def pagoefectpart_edit(request,idpa):

    if not request.user.has_perm('comercial.pagos'):
        return render_to_response("denegado.html",locals(),context_instance = RequestContext(request))
        
    nombre_form='Pagos en efectivo'
    descripcion_form='Realizar Pago en Efectivo'
    titulo_form='Pagos en Efectivo' 
    controlador_form='Pagos en Efectivo'
    accion_form='/comerciax/comercial/pagoefectpart/edit/'+ idpa +'/'
    cancelbtn_form='/comerciax/comercial/pagoefectpart/view/'+ idpa +'/'
    fecha_cierre=datetime.date.today().strftime("%d/%m/%Y")
    fecham=Cierre.objects.all()
    c=None
    l=[]
    for a in fecham:
        fecha_cierre=a.fechacierre.strftime("%d/%m/%Y")
    
    pagosfact=PagosFacturas.objects.filter(pagos=idpa).count()    
    if request.method == 'POST':
        
        form = PagoEfectPartForm1(request.POST) if pagosfact!=0 else PagoEfectPartForm(request.POST)
        
        if form.is_valid():
            
            
            pagoefect=PagosEfectivo.objects.select_related().get(pk=idpa)
            pago=Pagos.objects.select_related().get(pk=idpa)
            importe_old=pago.importe
            if form.cleaned_data['importe']!=importe_old:
                if form.cleaned_data['importe']<pago.importe-pago.deposito_adelantado:
                    l=l+['Error al cambiar el importe']
                    form = PagoEfectPartForm1(initial={'nombre':form.cleaned_data['nombre'],'ci':form.cleaned_data['ci'],
                                      'fecha':form.cleaned_data['fecha'],
                                      'moneda':pago.tipo_moneda,'forma_de_pago':pago.efectivo,'importe':form.cleaned_data['importe'],
                                      'observaciones':form.cleaned_data['observaciones'],'error2':l})
                    return render_to_response('form/form_edit.html',  {'tipocliente':'2','form': form, 'form_name':nombre_form,'form_description':descripcion_form,
                                                             'accion':accion_form,'titulo':titulo_form,'controlador':controlador_form,
                                                             'cancelbtn':cancelbtn_form,'fecha_minima':fecha_cierre,'error2':l},context_instance = RequestContext(request))
                   
            
            #pk_doc=uuid4()
            
            #obj_pago.id_pago=pk_doc
            pago.fecha_pago=form.cleaned_data['fecha']
            pago.importe=form.cleaned_data['importe']
            pago.efectivo=True
            pago.operador=User.objects.get(pk=request.user.id)
            pago.fecha_operacion=datetime.date.today()
            pago.observaciones=form.cleaned_data['observaciones']
            if pagosfact==0:
#                pago.pagosclientes.cliente=Cliente.objects.get(pk = form.data['cliente'])
                pago.tipo_moneda=Monedas.objects.get(pk = form.data['moneda'])
                pago.deposito_adelantado=form.cleaned_data['importe']
            else:
                pago.deposito_adelantado=abs(importe_old-form.cleaned_data['importe']-pago.deposito_adelantado)
            
            #pago.pago=obj_pago
            #pago.pago = obj_pago
            pagoefect.nombre=form.cleaned_data['nombre'] 
            pagoefect.ci=form.cleaned_data['ci']
            
            try:
                pago.save()
                pagoefect.save()
            
                return HttpResponseRedirect('/comerciax/comercial/pagoefectpart/view/'+idpa)  
            except Exception, e:
                exc_info = e.__str__() # sys.exc_info()[:1]
                c = exc_info.find("DETAIL:")
                
                if c < 0:
                    l=l+["Error Fatal."]
                else:
                    c = exc_info[c + 7:]
                    l=l+[c] 
                                     
                transaction.rollback()
                form = PagoEfectForm(request.POST)
                return render_to_response('form/form_edit.html',  {'tipocliente':'2','form': form, 'form_name':nombre_form,'form_description':descripcion_form,
                                                                         'accion':accion_form,'titulo':titulo_form,'controlador':controlador_form,
                                                                         'cancelbtn':cancelbtn_form,'fecha_minima':fecha_cierre,'error2':l},context_instance = RequestContext(request))
            else:
                transaction.commit()
    else:
        pago=PagosEfectivo.objects.get(pk=idpa)
        if pagosfact==0:
            form = PagoEfectPartForm(initial={'nombre':pago.nombre,'ci':pago.ci,'fecha':pago.pagos.fecha_pago,
                                      'moneda':pago.pagos.tipo_moneda,'forma_de_pago':pago.pagos.efectivo,'importe':pago.pagos.importe,
                                      'observaciones':pago.pagos.observaciones})
        else:
            form = PagoEfectPartForm1(initial={'nombre':pago.nombre,'ci':pago.ci,'fecha':pago.pagos.fecha_pago,
                                      'moneda':pago.pagos.tipo_moneda,'forma_de_pago':pago.pagos.efectivo,'importe':pago.pagos.importe,
                                      'observaciones':pago.pagos.observaciones})

             
    return render_to_response('form/form_edit.html',  {'tipocliente':'2','form': form, 'form_name':nombre_form,'form_description':descripcion_form,
                                                             'accion':accion_form,'titulo':titulo_form,'controlador':controlador_form,
                                                             'cancelbtn':cancelbtn_form,'fecha_minima':fecha_cierre,'error2':c},context_instance = RequestContext(request))
@login_required
def pagoefectpart_view(request,idpa):
    if not request.user.has_perm('comercial.pagos'):
        return render_to_response("denegado.html",locals(),context_instance = RequestContext(request))
    l=[]
    
    pago = PagosEfectivo.objects.select_related().get(pagos=idpa)

    rc_fecha=pago.pagos.fecha_pago.strftime("%d/%m/%Y")
#    rc_cliente=pago.pagos.pagosclientes.cliente.nombre
    rc_nombre=pago.nombre
    rc_ci=pago.ci
    rc_importe='$'+'{:20,.2f}'.format(pago.pagos.importe)
    rc_observaciones=pago.pagos.observaciones
    rc_fpago='Si' if (pago.pagos.efectivo==True) else 'No'
    rc_tmoneda=pago.pagos.tipo_moneda.descripcion
    rc_pagoadelantado='$'+'{:20,.2f}'.format(pago.pagos.deposito_adelantado) 
    
    
    filas = PagosFacturasPart.objects.select_related().filter(pagos=idpa).order_by('comercial_facturasparticular.factura_nro')
    #.order_by('comercial_facturas.factura_nro')

    # Verificar si se puede editar. Se puede editar si todos los cascos relacionados con el estado es Casco
    #editar=editar_documento(filas,idpa)
    return render_to_response('comercial/viewpagoefectpart.html',{'nombre':rc_nombre,'ci':rc_ci,'importe':rc_importe,'fecha':rc_fecha,'observaciones':rc_observaciones,
                                                              'rc_id':idpa,'fpago':rc_fpago,'tmoneda':rc_tmoneda,'pagoadelantado':rc_pagoadelantado,'elementos_detalle':filas, 'error2':l},context_instance = RequestContext(request))


@login_required
@transaction.commit_on_success()
def pagoefectpart_del(request,idpa):
    if not request.user.has_perm('comercial.pagos'):
        return render_to_response("denegado.html",locals(),context_instance = RequestContext(request))
    
    l=[]
    try:
        
        filas = PagosFacturasPart.objects.filter(pagos=idpa)
        #for canti in filas:
        #    actualiza_traza(canti.casco.id_casco,idpa)
        
        Pagos.objects.select_related().get(pk=idpa).delete()
        return HttpResponseRedirect('/comerciax/comercial/pagoefectpart/index')
        #return render_to_response("casco/recepcionclienteindex.html",locals(),context_instance = RequestContext(request))
    except Exception, e :
        transaction.rollback()
        l = ['Error al eliminar el documento']
        pagos = PagosEfectivo.objects.select_related().get(pk=idpa)
        rc_fecha=pagos.doc_factura.fecha_doc.strftime("%d/%m/%Y")
#        rc_cliente=pagos.cliente.nombre
        rc_nro=pagos.pagoefect_nro
        rc_observaciones=pagos.observaciones
        filas = PagosFacturasPart.objects.select_related().filter(pagos=idpa)
       
        return render_to_response('comercial/viewpagoefectpart.html',{'rc_nro':rc_nro,'fecha':rc_fecha,'observaciones':rc_observaciones,'rc_id':idpa,'elementos_detalle':filas, 'error2':l},context_instance = RequestContext(request))
    else:
        transaction.commit()

@login_required
def detallePagopart_delete(request,idpa,idpag):
    if not request.user.has_perm('comercial.pagos'):
        return render_to_response("denegado.html",locals(),context_instance = RequestContext(request))
    
    pagosfact=PagosFacturasPart.objects.get(pk=idpa)
    importe=pagosfact.importe_pagado
    pagosfact.delete()
        
    detallepago = PagosFacturasPart.objects.select_related().filter(pagos=idpag).order_by('comercial_facturasparticular.factura_nro')
   
    pago=Pagos.objects.get(pk=idpag)
    deposito=pago.deposito_adelantado
    pago.deposito_adelantado=deposito+importe
    pago.save()
    lista_valores=[]
    for detalles in detallepago:
        importe=str(detalles.importe_pagado)
        lista_valores=lista_valores+[{"id":detalles.id,"pago":detalles.pagos.id_pago,"factura_nro":detalles.facturas.factura_nro,"importe_pagado":importe}]
    return HttpResponse(simplejson.dumps(lista_valores),content_type = 'application/javascript; charset=utf8')

@login_required
@transaction.commit_on_success()    
def detallePagopart_add(request,idpa):
    if not request.user.has_perm('comercial.pagos'):
        return render_to_response("denegado.html",locals(),context_instance = RequestContext(request))
    l=[]
    titulo='Pagos' 
    controlador='Pagos'
    descripcion='Pagar factura'
    
    accion='detallePagopart_add'
    cancelbtn='/comerciax/comercial/pagoefectpart/view/'+idpa
    
    moneda=Pagos.objects.get(pk=idpa).tipo_moneda.id
    imp_pago=Pagos.objects.get(pk=idpa).deposito_adelantado
    if int(moneda) == 1:
        encab='Por pagar CUP'
#        elementos_detalle=Cliente.objects.get(id=PagosClientes.objects.get(pagos=idpa).cliente.id).get_porpagar()
        elementos_detalle=FacturasParticular.objects.select_related().filter(cancelada=False,ci=PagosEfectivo.objects.get(pagos=Pagos.objects.get(pk=idpa)).ci)
        
    
    if request.method == 'POST':
        seleccion=request.POST.keys()
        k=0
        importetotal=0
        pago=Pagos.objects.get(pk=idpa)
        while True:
            if k==seleccion.__len__():
                break
            fact=FacturasParticular.objects.filter(pk=seleccion[k])
            if fact.count()!=0:
                try:
                    importe=float(request.POST[seleccion[k]])
                    
                    if importe!=0:
                        
                        importetotal=importetotal+importe
                        if importe>pago.deposito_adelantado:
                            transaction.rollback()
                            error=["Error, el importe a pagar excede el pago"]
                            return render_to_response('comercial/pagarfactura.html', {'rc_id':idpa,'accion':accion,'elementos_detalle':elementos_detalle,
                                                              'cancelbtn':cancelbtn,'imp_pago':str(imp_pago),'controlador':controlador,'encab':encab,
                                                              'title':titulo,'form_description':descripcion,'error2':error},context_instance = RequestContext(request))
                    
                    
                        if PagosFacturasPart.objects.filter(facturas=FacturasParticular.objects.get(pk=seleccion[k]), pagos=idpa).count()==0:
                            pagosfact=PagosFacturasPart()
                            pagosfact.id=uuid4()
                            pagosfact.pagos=pago
                            pagosfact.importe_pagado=importe
                            pagosfact.facturas=FacturasParticular.objects.get(pk=seleccion[k])
                        else:
                            pagosfact=PagosFacturasPart.objects.get(facturas=FacturasParticular.objects.get(pk=seleccion[k]), pagos=idpa)
                            pagosfact.importe_pagado=float(pagosfact.importe_pagado)+importe
                    
                    
                        pago.deposito_adelantado=float(pago.deposito_adelantado)-importe
                    
                        pago.save()
                        pagosfact.save()
                except Exception, e:
                    exc_info = e.__str__() # sys.exc_info()[:1]
                    c = exc_info.find("DETAIL:")
                
                    if c < 0:
                        l=l+["Error Fatal."]
                    else:
                        c = exc_info[c + 7:]
                        l=l+[c] 
                        transaction.rollback()
                        return render_to_response('comercial/pagarfactura.html', {'rc_id':idpa,'imp_pago':str(imp_pago),'accion':accion,'elementos_detalle':elementos_detalle,
                                                              'cancelbtn':cancelbtn,'controlador':controlador,'encab':encab,
                                                              'title':titulo,'form_description':descripcion},context_instance = RequestContext(request))   

                
                    
            k=k+1
        transaction.commit()
        return HttpResponseRedirect('/comerciax/comercial/pagoefectpart/view/' + idpa)
    elementos_detalle1=[]
    for a1 in elementos_detalle:
        if a1.get_porpagar(1)>0 and a1.get_confirmada()=='S':
            elementos_detalle1+=[{'nro':a1.factura_nro,'importe':str(a1.get_porpagar(1)),'imp_num':str(a1.get_porpagar(1)),'pk':a1.doc_factura.id_doc}]
            
            
    return render_to_response('comercial/pagarfactura.html', {'rc_id':idpa,'accion':accion,'elementos_detalle':elementos_detalle1,'imp_pago':str(imp_pago),
                                                              'cancelbtn':cancelbtn,'controlador':controlador,'encab':encab,
                                                              'title':titulo,'form_description':descripcion},context_instance = RequestContext(request))   

#############################################################
#                     PAGOS EN EFECTIVO  ENTIDADES          #
#############################################################
@login_required
def get_pagoefect_list(request):
    #prepare the params
    try:
        fecha_desde=Fecha_Ver.objects.get()
    except Exception, e:
        fecha_desde=None
    if  fecha_desde == None:  
        querySet = Pagos.objects.select_related().filter(particulares=False)
    else:
        querySet = Pagos.objects.select_related().filter(particulares=False,fecha_pago__gte=fecha_desde.fecha)
        
    #querySet = querySet.filter(doc__fecha_doc__year=2010)
 
    columnIndexNameMap = {0: 'pagosclientes__cliente__nombre',1:'pagosclientes__cliente__nombre',2:'fecha_pago',3:'tipo_moneda',4:'efectivo',5:'importe',6:'deposito_adelantado'}

    searchableColumns = ['pagosclientes__cliente__nombre','tipo_moneda','efectivo','importe','deposito_adelantado']
    #path to template used to generate json
    jsonTemplatePath = 'comercial/json/json_pagos.txt'

    #call to generic function from utils
    return get_datatables_records(request, querySet, columnIndexNameMap, searchableColumns, jsonTemplatePath)
    

@login_required
def pagoefect_index(request):
    if not request.user.has_perm('comercial.pagos'):
        return render_to_response("denegado.html",locals(),context_instance = RequestContext(request))
    return render_to_response('comercial/pagoefectindex.html',locals(),context_instance = RequestContext(request))

@login_required
@transaction.commit_on_success()
def pagoefect_add(request):
    if not request.user.has_perm('comercial.pagos'):
        return render_to_response("denegado.html",locals(),context_instance = RequestContext(request))
    
    nombre_form='Pagos en efectivo'
    descripcion_form='Realizar Pago en Efectivo'
    titulo_form='Pagos en Efectivo' 
    controlador_form='Pagos en Efectivo'
    accion_form='/comerciax/comercial/pagoefect/add'
    cancelbtn_form='/comerciax/comercial/pagoefect/index'
    fecha_cierre=datetime.date.today().strftime("%d/%m/%Y")
    fecham=Cierre.objects.all()
    c=None
    l=[]
    for a in fecham:
        fecha_cierre=a.fechacierre.strftime("%d/%m/%Y")
    if request.method == 'POST':
        form = PagoEfectForm(request.POST)

        if form.is_valid():
            
            
            pago=PagosEfectivo()
            
            pk_doc=uuid4()
            obj_pago=Pagos()
            
            obj_pago.id_pago=pk_doc
            obj_pago.fecha_pago=form.cleaned_data['fecha']
            obj_pago.importe=form.cleaned_data['importe']
            obj_pago.efectivo=True
            obj_pago.operador=User.objects.get(pk=request.user.id)
            obj_pago.fecha_operacion=datetime.date.today()
            obj_pago.observaciones=form.cleaned_data['observaciones']
            
            obj_pago.tipo_moneda=Monedas.objects.get(pk = form.data['moneda'])
            obj_pago.deposito_adelantado=form.cleaned_data['importe']
            
            pago.pagos=obj_pago
            pago.nombre=form.cleaned_data['nombre'] 
            pago.ci=form.cleaned_data['ci']
            obj_pagocliente=PagosClientes()
            
            obj_pagocliente.id_pagocliente=uuid4()
            obj_pagocliente.pagos=obj_pago
            
            obj_pagocliente.cliente=Cliente.objects.get(pk = form.data['cliente'])
            
         
            try:
                obj_pago.save()
                obj_pagocliente.save()
                pago.save()
                return HttpResponseRedirect('/comerciax/comercial/pagoefect/view/'+pk_doc.__str__())  
            except Exception, e:
                exc_info = e.__str__() # sys.exc_info()[:1]
                c = exc_info.find("DETAIL:")
                
                if c < 0:
                    l=l+["Error Fatal."]
                else:
                    c = exc_info[c + 7:]
                    l=l+[c] 
                                     
                transaction.rollback()
                form = PagoEfectForm(request.POST)
                return render_to_response('form/form_adddetalle.html',  {'tipocliente':'2','form': form, 'form_name':nombre_form,'form_description':descripcion_form,
                                                                         'accion':accion_form,'titulo':titulo_form,'controlador':controlador_form,
                                                                         'cancelbtn':cancelbtn_form,'fecha_minima':fecha_cierre,'error2':l},context_instance = RequestContext(request))
            else:
                transaction.commit()
    else:
        form = PagoEfectForm() 
    return render_to_response('form/form_adddetalle.html',  {'tipocliente':'2','form': form, 'form_name':nombre_form,'form_description':descripcion_form,
                                                             'accion':accion_form,'titulo':titulo_form,'controlador':controlador_form,
                                                             'cancelbtn':cancelbtn_form,'fecha_minima':fecha_cierre,'error2':c},context_instance = RequestContext(request))


@login_required
@transaction.commit_on_success()
def pagoefect_edit(request,idpa):

    if not request.user.has_perm('comercial.pagos'):
        return render_to_response("denegado.html",locals(),context_instance = RequestContext(request))
        
    nombre_form='Pagos en efectivo'
    descripcion_form='Realizar Pago en Efectivo'
    titulo_form='Pagos en Efectivo' 
    controlador_form='Pagos en Efectivo'
    accion_form='/comerciax/comercial/pagoefect/edit/'+ idpa +'/'
    cancelbtn_form='/comerciax/comercial/pagoefect/view/'+ idpa +'/'
    fecha_cierre=datetime.date.today().strftime("%d/%m/%Y")
    fecham=Cierre.objects.all()
    c=None
    l=[]
    for a in fecham:
        fecha_cierre=a.fechacierre.strftime("%d/%m/%Y")
    
    pagosfact=PagosFacturas.objects.filter(pagos=idpa).count()    
    if request.method == 'POST':
        
        form = PagoEfectForm1(request.POST) if pagosfact!=0 else PagoEfectForm(request.POST)
        
        if form.is_valid():
            
            
            pagoefect=PagosEfectivo.objects.select_related().get(pk=idpa)
            pago=Pagos.objects.select_related().get(pk=idpa)
            importe_old=pago.importe
            if form.cleaned_data['importe']!=importe_old:
                if form.cleaned_data['importe']<pago.importe-pago.deposito_adelantado:
                    l=l+['Error al cambiar el importe']
                    form = PagoEfectForm1(initial={'nombre':form.cleaned_data['nombre'],'ci':form.cleaned_data['ci'],
                                      'fecha':form.cleaned_data['fecha'],'cliente':pago.pagosclientes.cliente,
                                      'moneda':pago.tipo_moneda,'forma_de_pago':pago.efectivo,'importe':form.cleaned_data['importe'],
                                      'observaciones':form.cleaned_data['observaciones'],'error2':l})
                    return render_to_response('form/form_edit.html',  {'tipocliente':'2','form': form, 'form_name':nombre_form,'form_description':descripcion_form,
                                                             'accion':accion_form,'titulo':titulo_form,'controlador':controlador_form,
                                                             'cancelbtn':cancelbtn_form,'fecha_minima':fecha_cierre,'error2':l},context_instance = RequestContext(request))
                   
            
            #pk_doc=uuid4()
            
            #obj_pago.id_pago=pk_doc
            pago.fecha_pago=form.cleaned_data['fecha']
            pago.importe=form.cleaned_data['importe']
            pago.efectivo=True
            pago.operador=User.objects.get(pk=request.user.id)
            pago.fecha_operacion=datetime.date.today()
            pago.observaciones=form.cleaned_data['observaciones']
            if pagosfact==0:
                pago.pagosclientes.cliente=Cliente.objects.get(pk = form.data['cliente'])
                pago.tipo_moneda=Monedas.objects.get(pk = form.data['moneda'])
                pago.deposito_adelantado=form.cleaned_data['importe']
            else:
                pago.deposito_adelantado=abs(importe_old-form.cleaned_data['importe']-pago.deposito_adelantado)
            
            #pago.pago=obj_pago
            #pago.pago = obj_pago
            pagoefect.nombre=form.cleaned_data['nombre'] 
            pagoefect.ci=form.cleaned_data['ci']
            
            try:
                pago.save()
                pagoefect.save()
            
                return HttpResponseRedirect('/comerciax/comercial/pagoefect/view/'+idpa)  
            except Exception, e:
                exc_info = e.__str__() # sys.exc_info()[:1]
                c = exc_info.find("DETAIL:")
                
                if c < 0:
                    l=l+["Error Fatal."]
                else:
                    c = exc_info[c + 7:]
                    l=l+[c] 
                                     
                transaction.rollback()
                form = PagoEfectForm(request.POST)
                return render_to_response('form/form_edit.html',  {'tipocliente':'2','form': form, 'form_name':nombre_form,'form_description':descripcion_form,
                                                                         'accion':accion_form,'titulo':titulo_form,'controlador':controlador_form,
                                                                         'cancelbtn':cancelbtn_form,'fecha_minima':fecha_cierre,'error2':l},context_instance = RequestContext(request))
            else:
                transaction.commit()
    else:
        pago=PagosEfectivo.objects.get(pk=idpa)
        if pagosfact==0:
            form = PagoEfectForm(initial={'nombre':pago.nombre,'ci':pago.ci,'fecha':pago.pagos.fecha_pago,'cliente':pago.pagos.pagosclientes.cliente,
                                      'moneda':pago.pagos.tipo_moneda,'forma_de_pago':pago.pagos.efectivo,'importe':pago.pagos.importe,
                                      'observaciones':pago.pagos.observaciones})
        else:
            form = PagoEfectForm1(initial={'nombre':pago.nombre,'ci':pago.ci,'fecha':pago.pagos.fecha_pago,'cliente':pago.pagos.pagosclientes.cliente,
                                      'moneda':pago.pagos.tipo_moneda,'forma_de_pago':pago.pagos.efectivo,'importe':pago.pagos.importe,
                                      'observaciones':pago.pagos.observaciones})

             
    return render_to_response('form/form_edit.html',  {'tipocliente':'2','form': form, 'form_name':nombre_form,'form_description':descripcion_form,
                                                             'accion':accion_form,'titulo':titulo_form,'controlador':controlador_form,
                                                             'cancelbtn':cancelbtn_form,'fecha_minima':fecha_cierre,'error2':c},context_instance = RequestContext(request))
@login_required
def pagoefect_view(request,idpa):
    if not request.user.has_perm('comercial.pagos'):
        return render_to_response("denegado.html",locals(),context_instance = RequestContext(request))
    l=[]
    
    pago = PagosEfectivo.objects.select_related().get(pagos=idpa)

    rc_fecha=pago.pagos.fecha_pago.strftime("%d/%m/%Y")
    rc_cliente=pago.pagos.pagosclientes.cliente.nombre
    rc_importe='$'+'{:20,.2f}'.format(pago.pagos.importe)
    rc_observaciones=pago.pagos.observaciones
    rc_fpago='Si' if (pago.pagos.efectivo==True) else 'No'
    rc_tmoneda=pago.pagos.tipo_moneda.descripcion
    rc_pagoadelantado='$'+'{:20,.2f}'.format(pago.pagos.deposito_adelantado) 
    
    
    filas = PagosFacturas.objects.select_related().filter(pagos=idpa).order_by('comercial_facturas.factura_nro')
    #.order_by('comercial_facturas.factura_nro')

    # Verificar si se puede editar. Se puede editar si todos los cascos relacionados con el estado es Casco
    #editar=editar_documento(filas,idpa)
    return render_to_response('comercial/viewpagoefect.html',{'importe':rc_importe,'fecha':rc_fecha,'cliente':rc_cliente,'observaciones':rc_observaciones,
                                                              'rc_id':idpa,'fpago':rc_fpago,'tmoneda':rc_tmoneda,'pagoadelantado':rc_pagoadelantado,'elementos_detalle':filas, 'error2':l},context_instance = RequestContext(request))


@login_required
@transaction.commit_on_success()
def pagoefect_del(request,idpa):
    if not request.user.has_perm('comercial.pagos'):
        return render_to_response("denegado.html",locals(),context_instance = RequestContext(request))
    
    l=[]
    try:
        
#        filas = PagosFacturas.objects.filter(pagos=idpa)
        #for canti in filas:
        #    actualiza_traza(canti.casco.id_casco,idpa)
        
        Pagos.objects.select_related().get(pk=idpa).delete()
#        PagosClientes.objects.filter(pagos=pago).delete()
#        PagosFacturas.objects.filter(pagos=pago).delete()
#        PagosEfectivo.objects.filter(pagos=pago).delete()
#        Pagos.objects.filter(pk=idpa).delete()
        return HttpResponseRedirect('/comerciax/comercial/pagoefect/index')
        #return render_to_response("casco/recepcionclienteindex.html",locals(),context_instance = RequestContext(request))
    except Exception, e :
        transaction.rollback()
        l = ['Error al eliminar el documento']
        pagos = PagosEfectivo.objects.select_related().get(pk=idpa)
        rc_fecha=pagos.pagos.fecha_pago.strftime("%d/%m/%Y")
        rc_cliente=pagos.pagos.pagosclientes.cliente.nombre
#        rc_nro=pagos.pagos.pagoefect_nro
        rc_observaciones=pagos.pagos.observaciones
        filas = PagosFacturas.objects.select_related().filter(pagos=idpa)
       
        return render_to_response('comercial/viewpagoefect.html',{'fecha':rc_fecha,'cliente':rc_cliente,'observaciones':rc_observaciones,'rc_id':idpa,'elementos_detalle':filas, 'error2':l},context_instance = RequestContext(request))
    else:
        transaction.commit()
 

@login_required
def detallePago_delete(request,idpa,idpag):
    if not request.user.has_perm('comercial.pagos'):
        return render_to_response("denegado.html",locals(),context_instance = RequestContext(request))
    
    pagosfact=PagosFacturas.objects.get(pk=idpa)
    importe=pagosfact.importe_pagado
    pagosfact.delete()
        
    detallepago = PagosFacturas.objects.select_related().filter(pagos=idpag).order_by('comercial_facturas.factura_nro')
   
    pago=Pagos.objects.get(pk=idpag)
    deposito=pago.deposito_adelantado
    pago.deposito_adelantado=deposito+importe
    pago.save()
    lista_valores=[]
    for detalles in detallepago:
        importe=str(detalles.importe_pagado)
        lista_valores=lista_valores+[{"id":detalles.id,"pago":detalles.pagos.id_pago,"factura_nro":detalles.facturas.factura_nro,"importe_pagado":importe}]
    return HttpResponse(simplejson.dumps(lista_valores),content_type = 'application/javascript; charset=utf8')
    
@login_required
@transaction.commit_on_success()    
def detallePago_add(request,idpa):
    if not request.user.has_perm('comercial.pagos'):
        return render_to_response("denegado.html",locals(),context_instance = RequestContext(request))
    l=[]
    titulo='Pagos' 
    controlador='Pagos'
    descripcion='Pagar factura'
    
    accion='detallePago_add'
    cancelbtn='/comerciax/comercial/pagoefect/view/'+idpa
    
    moneda=Pagos.objects.get(pk=idpa).tipo_moneda.id
    imp_pago=Pagos.objects.get(pk=idpa).deposito_adelantado
    if int(moneda) == 1:
        encab='Por pagar CUP'
        elementos_detalle=Cliente.objects.get(id=PagosClientes.objects.get(pagos=idpa).cliente.id).get_facturas_porpagarcup()
    else:
        encab='Por pagar CUC'
        elementos_detalle=Cliente.objects.get(id=PagosClientes.objects.get(pagos=idpa).cliente.id).get_facturas_porpagarcuc()
        
    
    if request.method == 'POST':
        seleccion=request.POST.keys()
        k=0
        importetotal=0
        pago=Pagos.objects.get(pk=idpa)
        while True:
            if k==seleccion.__len__():
                break
            fact=Facturas.objects.filter(pk=seleccion[k])
            if fact.count()!=0:
                try:
                    importe=float(request.POST[seleccion[k]])
                    
                    if importe!=0:
                        
                        importetotal=importetotal+importe
                        if importe>pago.deposito_adelantado:
                            transaction.rollback()
                            error=["Error, el importe a pagar excede el pago"]
                            return render_to_response('comercial/pagarfactura.html', {'rc_id':idpa,'accion':accion,'elementos_detalle':elementos_detalle,
                                                              'cancelbtn':cancelbtn,'imp_pago':str(imp_pago),'controlador':controlador,'encab':encab,
                                                              'title':titulo,'form_description':descripcion,'error2':error},context_instance = RequestContext(request))
                    
                    
                        if PagosFacturas.objects.filter(facturas=Facturas.objects.get(pk=seleccion[k]), pagos=idpa).count()==0:
                            pagosfact=PagosFacturas()
                            pagosfact.id=uuid4()
                            pagosfact.pagos=pago
                            pagosfact.importe_pagado=importe
                            pagosfact.facturas=Facturas.objects.get(pk=seleccion[k])
                        else:
                            pagosfact=PagosFacturas.objects.get(facturas=Facturas.objects.get(pk=seleccion[k]), pagos=idpa)
                            pagosfact.importe_pagado=float(pagosfact.importe_pagado)+importe
                    
                    
                        pago.deposito_adelantado=float(pago.deposito_adelantado)-importe
                    
                        pago.save()
                        pagosfact.save()
                except Exception, e:
                    exc_info = e.__str__() # sys.exc_info()[:1]
                    c = exc_info.find("DETAIL:")
                
                    if c < 0:
                        l=l+["Error Fatal."]
                    else:
                        c = exc_info[c + 7:]
                        l=l+[c] 
                        transaction.rollback()
                        return render_to_response('comercial/pagarfactura.html', {'rc_id':idpa,'imp_pago':str(imp_pago),'accion':accion,'elementos_detalle':elementos_detalle,
                                                              'cancelbtn':cancelbtn,'controlador':controlador,'encab':encab,
                                                              'title':titulo,'form_description':descripcion},context_instance = RequestContext(request))   

                
                    
            k=k+1
        transaction.commit()
        return HttpResponseRedirect('/comerciax/comercial/pagoefect/view/' + idpa)
    return render_to_response('comercial/pagarfactura.html', {'rc_id':idpa,'accion':accion,'elementos_detalle':elementos_detalle,'imp_pago':str(imp_pago),
                                                              'cancelbtn':cancelbtn,'controlador':controlador,'encab':encab,
                                                              'title':titulo,'form_description':descripcion},context_instance = RequestContext(request))   


#############################################################
#                              PAGOS OTROS                  #
#############################################################

@login_required
@transaction.commit_on_success()
def pagootros_add(request):
    if not request.user.has_perm('comercial.pagos'):
        return render_to_response("denegado.html",locals(),context_instance = RequestContext(request))
    
    nombre_form='Otros Pagos'
    descripcion_form='Realizar Pago'
    titulo_form='Otros Pagos' 
    controlador_form='Otros Pagos'
    accion_form='/comerciax/comercial/pagootros/add'
    cancelbtn_form='/comerciax/comercial/pagoefect/index'
    fecha_cierre=datetime.date.today().strftime("%d/%m/%Y")
    fecham=Cierre.objects.all()
    c=None
    l=[]
    for a in fecham:
        fecha_cierre=a.fechacierre.strftime("%d/%m/%Y")
    if request.method == 'POST':
        form = PagosForm(request.POST)

        if form.is_valid():
            
            
            pago=PagosOtros()
            
            pk_doc=uuid4()
            obj_pago=Pagos()
            
            obj_pago.id_pago=pk_doc
            obj_pago.fecha_pago=form.cleaned_data['fecha']
            obj_pago.importe=form.cleaned_data['importe']
            obj_pago.efectivo=False
            obj_pago.operador=User.objects.get(pk=request.user.id)
            obj_pago.fecha_operacion=datetime.date.today()
            obj_pago.observaciones=form.cleaned_data['observaciones']
            obj_pagocliente=PagosClientes()
            obj_pagocliente.id_pagocliente=uuid4()
            obj_pagocliente.cliente=Cliente.objects.get(pk = form.data['cliente'])
            obj_pagocliente.pagos=obj_pago
            obj_pago.tipo_moneda=Monedas.objects.get(pk = form.data['moneda'])
            obj_pago.deposito_adelantado=form.cleaned_data['importe']
            
            pago.pagos=obj_pago
            pago.nro=form.cleaned_data['nro'] 
            pago.forma_pago=FormasPago.objects.get(pk = form.data['tipo'])
            
         
            try:
                obj_pago.save()
                obj_pagocliente.save()
                pago.save()
                return HttpResponseRedirect('/comerciax/comercial/pagootros/view/'+pk_doc.__str__())  
            except Exception, e:
                exc_info = e.__str__() # sys.exc_info()[:1]
                c = exc_info.find("DETAIL:")
                
                if c < 0:
                    l=l+["Error Fatal."]
                else:
                    c = exc_info[c + 7:]
                    l=l+[c] 
                                     
                transaction.rollback()
                form = PagoEfectForm(request.POST)
                return render_to_response('form/form_adddetalle.html',  {'tipocliente':'2','form': form, 'form_name':nombre_form,'form_description':descripcion_form,
                                                                         'accion':accion_form,'titulo':titulo_form,'controlador':controlador_form,
                                                                         'cancelbtn':cancelbtn_form,'fecha_minima':fecha_cierre,'error2':l},context_instance = RequestContext(request))
            else:
                transaction.commit()
    else:
        form = PagosForm() 
    return render_to_response('form/form_adddetalle.html',  {'tipocliente':'2','form': form, 'form_name':nombre_form,'form_description':descripcion_form,
                                                             'accion':accion_form,'titulo':titulo_form,'controlador':controlador_form,
                                                             'cancelbtn':cancelbtn_form,'fecha_minima':fecha_cierre,'error2':c},context_instance = RequestContext(request))

@login_required
def pagootros_view(request,idpa):
    if not request.user.has_perm('comercial.pagos'):
        return render_to_response("denegado.html",locals(),context_instance = RequestContext(request))
    l=[]
    
    pago = PagosOtros.objects.select_related().get(pagos=idpa)

    rc_fecha=pago.pagos.fecha_pago.strftime("%d/%m/%Y")
    rc_cliente=pago.pagos.pagosclientes.cliente.nombre
    rc_importe='$'+'{:20,.2f}'.format(pago.pagos.importe) 
    rc_observaciones=pago.pagos.observaciones
    rc_fpago=pago.forma_pago.descripcion
    rc_tmoneda=pago.pagos.tipo_moneda.descripcion
    rc_pagoadelantado='$'+'{:20,.2f}'.format(pago.pagos.deposito_adelantado) 
    
    
    filas = PagosFacturas.objects.select_related().filter(pagos=idpa).order_by('comercial_facturas.factura_nro')
    #.order_by('comercial_facturas.factura_nro')

    # Verificar si se puede editar. Se puede editar si todos los cascos relacionados con el estado es Casco
    #editar=editar_documento(filas,idpa)
    return render_to_response('comercial/viewpagootros.html',{'importe':rc_importe,'fecha':rc_fecha,'cliente':rc_cliente,'observaciones':rc_observaciones,
                                                              'rc_id':idpa,'fpago':rc_fpago,'tmoneda':rc_tmoneda,'pagoadelantado':rc_pagoadelantado,'elementos_detalle':filas, 'error2':l},context_instance = RequestContext(request))


@login_required
@transaction.commit_on_success()
def pagootros_edit(request,idpa):
    
    if not request.user.has_perm('comercial.pagos'):
        return render_to_response("denegado.html",locals(),context_instance = RequestContext(request))
        
    nombre_form='Otros Pagos'
    descripcion_form='Realizar Pago'
    titulo_form='Otros Pagos' 
    controlador_form='Otros Pagos'
    accion_form='/comerciax/comercial/pagootros/edit/'+ idpa +'/'
    cancelbtn_form='/comerciax/comercial/pagootros/view/'+ idpa +'/'
    fecha_cierre=datetime.date.today().strftime("%d/%m/%Y")
    fecham=Cierre.objects.all()
    c=None
    l=[]
    for a in fecham:
        fecha_cierre=a.fechacierre.strftime("%d/%m/%Y")
    
    pagosfact=PagosFacturas.objects.filter(pagos=idpa).count()    
    if request.method == 'POST':
        
        form = PagosForm1(request.POST) if pagosfact!=0 else PagosForm(request.POST)
        
        if form.is_valid():
            
            pagootros=PagosOtros.objects.select_related().get(pk=idpa)
            pago=Pagos.objects.select_related().get(pk=idpa)
            pagoscliente=PagosClientes.objects.select_related().get(pagos=pago)
            importe_old=pago.importe
            if form.cleaned_data['importe']!=importe_old:
                if form.cleaned_data['importe']<pago.importe-pago.deposito_adelantado:
                    l=l+['Error al cambiar el importe']
                    form = PagosForm1(initial={'nombre':form.cleaned_data['nombre'],'ci':form.cleaned_data['ci'],
                                      'fecha':form.cleaned_data['fecha'],'cliente':pago.pagoscliente.cliente,
                                      'moneda':pago.tipo_moneda,'tipo':pago.forma_pago,'importe':form.cleaned_data['importe'],
                                      'observaciones':form.cleaned_data['observaciones'],'error2':l})
                    return render_to_response('form/form_edit.html',  {'tipocliente':'2','form': form, 'form_name':nombre_form,'form_description':descripcion_form,
                                                             'accion':accion_form,'titulo':titulo_form,'controlador':controlador_form,
                                                             'cancelbtn':cancelbtn_form,'fecha_minima':fecha_cierre,'error2':l},context_instance = RequestContext(request))
                   
            
            #pk_doc=uuid4()
            
            #obj_pago.id_pago=pk_doc
            pago.fecha_pago=form.cleaned_data['fecha']
            pago.importe=form.cleaned_data['importe']
            pago.efectivo=False
            pago.operador=User.objects.get(pk=request.user.id)
            pago.fecha_operacion=datetime.date.today()
            pago.observaciones=form.cleaned_data['observaciones']
            if pagosfact==0:
                pagoscliente.cliente=Cliente.objects.get(pk = form.data['cliente'])
                pago.tipo_moneda=Monedas.objects.get(pk = form.data['moneda'])
                pago.deposito_adelantado=form.cleaned_data['importe']
            else:
                pago.deposito_adelantado=abs(importe_old-form.cleaned_data['importe']-pago.deposito_adelantado)

            #pago.pago=obj_pago
            #pago.pago = obj_pago
            pagootros.nro=form.cleaned_data['nro'] 
            pagootros.forma_pago=FormasPago.objects.get(pk = form.data['tipo'])
            
            try:
                pago.save()
                pagootros.save()
                pagoscliente.save()
                return HttpResponseRedirect('/comerciax/comercial/pagootros/view/'+idpa)  
            except Exception, e:
                exc_info = e.__str__() # sys.exc_info()[:1]
                c = exc_info.find("DETAIL:")
                
                if c < 0:
                    l=l+["Error Fatal."]
                else:
                    c = exc_info[c + 7:]
                    l=l+[c] 
                                     
                transaction.rollback()
                form = PagoEfectForm(request.POST)
                return render_to_response('form/form_edit.html',  {'tipocliente':'2','form': form, 'form_name':nombre_form,'form_description':descripcion_form,
                                                                         'accion':accion_form,'titulo':titulo_form,'controlador':controlador_form,
                                                                         'cancelbtn':cancelbtn_form,'fecha_minima':fecha_cierre,'error2':l},context_instance = RequestContext(request))
            else:
                transaction.commit()
    else:
        pago=PagosOtros.objects.get(pk=idpa)
        ax=pago.forma_pago
        if pagosfact==0:
            form = PagosForm(initial={'nro':pago.nro,'tipo':pago.forma_pago,'fecha':pago.pagos.fecha_pago,'cliente':pago.pagos.pagosclientes.cliente,
                                      'moneda':pago.pagos.tipo_moneda,'importe':pago.pagos.importe,
                                      'observaciones':pago.pagos.observaciones})
        else:
            form = PagosForm1(initial={'nro':pago.nro,'tipo':pago.forma_pago,'fecha':pago.pagos.fecha_pago,'cliente':pago.pagos.pagosclientes.cliente,
                                      'moneda':pago.pagos.tipo_moneda,'importe':pago.pagos.importe,
                                      'observaciones':pago.pagos.observaciones})

             
    return render_to_response('form/form_edit.html',  {'tipocliente':'2','form': form, 'form_name':nombre_form,'form_description':descripcion_form,
                                                             'accion':accion_form,'titulo':titulo_form,'controlador':controlador_form,
                                                             'cancelbtn':cancelbtn_form,'fecha_minima':fecha_cierre,'error2':c},context_instance = RequestContext(request))

@login_required
@transaction.commit_on_success()
def detallePagootro_add(request,idpa):
    if not request.user.has_perm('comercial.pagos'):
        return render_to_response("denegado.html",locals(),context_instance = RequestContext(request))
    
    titulo='Pagos' 
    controlador='Pagos'
    descripcion='Pagar factura'
    
    accion='detallePagootro_add'
    cancelbtn='/comerciax/comercial/pagootros/view/'+idpa
    
    moneda=Pagos.objects.get(pk=idpa).tipo_moneda.id
    imp_pago=Pagos.objects.get(pk=idpa).deposito_adelantado
    if moneda == '1':
        encab='Por pagar CUP'
        elementos_detalle=Cliente.objects.get(id=Pagos.objects.get(pk=idpa).pagosclientes.cliente.id).get_facturas_porpagarcup()
    else:
        encab='Por pagar CUC'
        elementos_detalle=Cliente.objects.get(id=Pagos.objects.get(pk=idpa).pagosclientes.cliente.id).get_facturas_porpagarcuc()
        
    l=[]
    if request.method == 'POST':
        seleccion=request.POST.keys()
        k=0
        importetotal=0
        pago=Pagos.objects.get(pk=idpa)
        while True:
            if k==seleccion.__len__():
                break
            
            
            fact=Facturas.objects.filter(pk=seleccion[k])
            
                
            if fact.count()!=0:
                try:
                    importe=float(request.POST[seleccion[k]])
                    
                    if importe!=0:
                        
                        importetotal=importetotal+importe
                        if importe>pago.deposito_adelantado:
                            transaction.rollback()
                            error=["Error, el importe a pagar excede el pago"]
                            return render_to_response('comercial/pagarfactura.html', {'rc_id':idpa,'accion':accion,'elementos_detalle':elementos_detalle,
                                                              'cancelbtn':cancelbtn,'imp_pago':str(imp_pago),'controlador':controlador,'encab':encab,
                                                              'title':titulo,'form_description':descripcion,'error2':error},context_instance = RequestContext(request))
                    
                    
                        if PagosFacturas.objects.filter(facturas=Facturas.objects.get(pk=seleccion[k]), pagos=idpa).count()==0:
                            pagosfact=PagosFacturas()
                            pagosfact.id=uuid4()
                            pagosfact.pagos=pago
                            pagosfact.importe_pagado=importe
                            pagosfact.facturas=Facturas.objects.get(pk=seleccion[k])
                        else:
                            pagosfact=PagosFacturas.objects.get(facturas=Facturas.objects.get(pk=seleccion[k]), pagos=idpa)
                            pagosfact.importe_pagado=float(pagosfact.importe_pagado)+importe
                    
                    
                        pago.deposito_adelantado=float(pago.deposito_adelantado)-importe
                    
                        pago.save()
                        pagosfact.save()
                except Exception, e:
                    exc_info = e.__str__() # sys.exc_info()[:1]
                    c = exc_info.find("DETAIL:")
                
                    if c < 0:
                        l=l+["Error Fatal."]
                    else:
                        c = exc_info[c + 7:]
                        l=l+[c] 
                        transaction.rollback()
                        return render_to_response('comercial/pagarfactura.html', {'rc_id':idpa,'imp_pago':str(imp_pago),'accion':accion,'elementos_detalle':elementos_detalle,
                                                              'cancelbtn':cancelbtn,'controlador':controlador,'encab':encab,
                                                              'title':titulo,'form_description':descripcion},context_instance = RequestContext(request))   

                
                    
            k=k+1
        transaction.commit()
        return HttpResponseRedirect('/comerciax/comercial/pagootros/view/' + idpa)
    
    return render_to_response('comercial/pagarfactura.html', {'rc_id':idpa,'accion':accion,'elementos_detalle':elementos_detalle,'imp_pago':str(imp_pago),
                                                              'cancelbtn':cancelbtn,'controlador':controlador,'encab':encab,
                                                              'title':titulo,'form_description':descripcion},context_instance = RequestContext(request))   

#############################################################
#              CONTRATOS POR FECHA DE VENCIMIENTO           #
#############################################################
@login_required
def contratosvencimiento(request):
    
    nombre_form='Reportes'
    descripcion_form='Contratos por Fecha de Vencimiento'
    titulo_form='Contratos por Fecha de Vencimiento' 
    controlador_form='Reportes'
    accion_form='/comerciax/comercial/contratosvencimiento/reporte'
    cancelbtn_form='/comerciax/comercial/contratosvencimiento/'
    mesg=[]
    
    if request.method == 'POST':
        form = Rep_ContratosFechaVenc(request.POST)
        if form.is_valid():
            orden=form.cleaned_data['orden']
            mes = form.cleaned_data['mes']
            ano = form.cleaned_data['year']
            
            filtro=[]
            filtro.append('Fecha de Vencimiento: '+Meses.meses_name[int(mes)]+"/"+str(ano))
            queryset=[]
            condic=[]
            if orden=='fecha':
                resultado=ClienteContrato.objects.select_related().filter(contrato__fecha_vencimiento__month=int(mes),contrato__fecha_vencimiento__year=int(ano),contrato__cerrado=False).order_by('contrato__fecha_vencimiento')
            else:
                resultado=ClienteContrato.objects.select_related().filter(contrato__fecha_vencimiento__month=int(mes),contrato__fecha_vencimiento__year=int(ano),contrato__cerrado=False).order_by('cliente__nombre') 
            
            if request.POST.__contains__('submit'):
                return render_to_response("report/registro_contratosfecha.html",{'filtro':filtro,'fecha_hoy':fecha_hoy(),'resultado':resultado,'error2':mesg},context_instance = RequestContext(request))
            
            if request.POST.__contains__('submit1'):  
                for a in resultado:                                       
                    queryset.append({'codigo':a.cliente.codigo,'nombre':a.cliente.nombre,'contrato_nro':a.contrato.contrato_nro,'fecha_vigencia':a.contrato.fecha_vigencia,
                              'fecha_vencimiento':a.contrato.fecha_vencimiento,'cerrado':'No' if not a.contrato.cerrado else 'Si','tipo':a.cliente.get_contrato_tipoDesc(),
                              'preciomn':a.cliente.get_contrato_preciocup(),'preciocuc':a.cliente.get_contrato_preciocuc(),'dias':a.cliente.get_contrato_dias()})
                if queryset.__len__():  #22 
                    pdf_file_name=os.path.join(comerciax.settings.ADMIN_MEDIA_PDF,"Registro Contratos.pdf") 
                    if report_class.Reportes.GenerarRep(report_class.Reportes() , queryset, "reg_contrat",pdf_file_name,filtro)==0:
                        mesg=mesg+['Debe cerrar el documento Registro Contratos.pdf']
                        return render_to_response("comercial/reporteindex.html",{'filtro':filtro,'resultado':resultado,'form':form,'title':titulo_form, 'form_name':nombre_form,'form_description':descripcion_form,
                                                        'controlador':controlador_form,'accion':accion_form,'error2':mesg},context_instance = RequestContext(request))
                    else:
                        input = PdfFileReader(file(pdf_file_name,"rb"))
                        output = PdfFileWriter()
                        for page in input.pages:
                            output.addPage(page)
                        buffer = StringIO.StringIO()
                        output.write(buffer)
                        response = HttpResponse(mimetype='application/pdf')
                        response['Content-Disposition'] = 'attachment; filename=%s'%(pdf_file_name)
                        response.write(buffer.getvalue())
                        return response
                else:
                    mesg=mesg+['No existe información para mostrar']
                    return render_to_response("comercial/reporteindex.html",{'filtro':filtro,'resultado':resultado,'form':form,'title':titulo_form, 'form_name':nombre_form,'form_description':descripcion_form,
                                                        'controlador':controlador_form,'accion':accion_form,'error2':mesg},context_instance = RequestContext(request))

    else:
        form = Rep_ContratosFechaVenc() 
    #    
        return render_to_response("comercial/reporteindex.html",{'form':form,'title':titulo_form, 'form_name':nombre_form,'form_description':descripcion_form,
                                                                'controlador':controlador_form,'accion':accion_form,'error2':mesg},context_instance = RequestContext(request))
    
#############################################################
#              REGISTRO DE CONTRATOS                        #
#############################################################
@login_required
def regcontratos(request):
    
    nombre_form='Reportes'
    descripcion_form='Registro de Contratos.'
    titulo_form='Registro de Contratos' 
    controlador_form='Reportes'
    accion_form='/comerciax/comercial/regcontratos/reporte'
    cancelbtn_form='/comerciax/comercial/regcontratos/'
    mesg=[]
    
    if request.method == 'POST':
        form = Rep_RegContratos(request.POST)
        if form.is_valid():
            orden=form.cleaned_data['orden']
            cliente  = form.cleaned_data['cliente']
            nro = form.cleaned_data['nro']
            tipo = form.cleaned_data['tipo']
            cerrado = form.cleaned_data['cerrado']
            preciocup = form.cleaned_data['preciocup']
            preciocuc = form.cleaned_data['preciocuc']
            dias = form.cleaned_data['dias']
            if dias==None:
                dias=0
            filtro=[]
            queryset=[]
            condic=[]
            if cliente!=None:
                filtro.append('Cliente: '+cliente.nombre)
                condic+=["admincomerciax_cliente.id = '"+cliente.id+"'"]
            if nro.__len__()!=0:
                filtro.append('Nro. contrato contine: '+nro)
                condic+=["admincomerciax_contrato.contrato_nro LIKE '%"+nro+"%'"]
            if tipo!='G' and tipo.__len__()!=0:
                vtipo = True if (tipo == 'V') else False
                ctipo = 'Normal' if (tipo == 'N') else 'Para la Venta'
                filtro.append('Tipo contrato: '+ctipo)
                condic+=["admincomerciax_contrato.para_la_venta ="+str(vtipo)]
            if cerrado!='G' and cerrado.__len__()!=0:
                vcerrado=True if (cerrado == 'S') else False
                ccerrado='Si' if (cerrado == 'S') else 'No'
                filtro.append('Cerrado: '+ccerrado)
                condic+=['admincomerciax_contrato.cerrado='+str(vcerrado)]
            if preciocup!='G' and preciocup.__len__()!=0:
                if preciocup == 'N':
                    precventa=False
                    preccosto=False
                    cprecio='No Existe'
                elif preciocup == 'C':
                    precventa=False
                    preccosto=True
                    cprecio='De Costo'
                else:
                    precventa=True
                    preccosto=False
                    cprecio='De Venta'
                filtro.append('Precio CUP: '+cprecio)
                condic+=[' admincomerciax_contrato.preciomn = '+str(precventa) + ' and admincomerciax_contrato.preciocostomn ='+str(preccosto)]
            if preciocuc!='G' and preciocuc.__len__()!=0:
                if preciocuc == 'N':
                    precventa=False
                    preccosto=False
                    cprecio='No Existe'
                elif preciocuc == 'C':
                    precventa=False
                    preccosto=True
                    cprecio='De Costo'
                else:
                    precventa=True
                    preccosto=False
                    cprecio='De Venta'
                filtro.append('Precio CUP: '+str(cprecio))
                condic+=['admincomerciax_contrato.preciocuc = '+str(precventa)+' and admincomerciax_contrato.preciocostocuc = '+str(preccosto)]
            if dias>0:
                filtro.append('Máx. de días para caducar: '+str(dias))
                condic+=["cast(date_part('day', admincomerciax_contrato.fecha_vencimiento-now()) as integer) <= "+str(dias)]
            cade_where=""
            if condic.__len__()!=0:
                for i in range(condic.__len__()):
                    if i!=0 and i!=condic.__len__():
                        cade_where+=' AND '
                    cade_where+=condic[i]
                cade_where="Where "+cade_where 
            cade_order="Order By "
            if form.cleaned_data['orden']=='cliente':
                cade_order += 'admincomerciax_cliente.nombre' 
            else:
                cade_order += 'admincomerciax_contrato.contrato_nro' 
                
            resultado_sql= """
                            SELECT 
                               admincomerciax_contrato.contrato_nro, 
                               admincomerciax_cliente.id, 
                               admincomerciax_cliente.codigo, 
                               admincomerciax_cliente.nombre, 
                               admincomerciax_contrato.fecha_vigencia, 
                               admincomerciax_contrato.para_la_venta, 
                               admincomerciax_contrato.fecha_vencimiento, 
                               admincomerciax_contrato.cerrado, 
                               admincomerciax_contrato.preciomn, 
                               admincomerciax_contrato.preciocostomn, 
                               admincomerciax_contrato.preciocuc, 
                               admincomerciax_contrato.preciocostocuc, 
                               admincomerciax_contrato.para_la_venta, 
                               date_part('day'::text, admincomerciax_contrato.fecha_vencimiento::timestamp with time zone - now())::integer AS dias
                            FROM admincomerciax_clientecontrato
                               inner join admincomerciax_cliente on admincomerciax_cliente.id::text = admincomerciax_clientecontrato.cliente_id::text
                               inner join admincomerciax_contrato on admincomerciax_contrato.id_contrato::text = admincomerciax_clientecontrato.contrato_id::text
                            """+ cade_where + """  """+cade_order 
            resultado = query_to_dicts(resultado_sql)
            if request.POST.__contains__('submit'):
                return render_to_response("report/registro_contratos.html",{'filtro':filtro,'fecha_hoy':fecha_hoy(),'resultado':resultado,'error2':mesg},context_instance = RequestContext(request))

            
            if request.POST.__contains__('submit1'):  
                for a in resultado:                                       
                    queryset.append({'codigo':a['codigo'],'nombre':a['nombre'],'contrato_nro':a['contrato_nro'],'fecha_vigencia':a['fecha_vigencia'],
                              'fecha_vencimiento':a['fecha_vencimiento'],'cerrado':'No' if not a['cerrado'] else 'Si','tipo':'Normal' if not a['para_la_venta'] else 'Para la Venta',
                              'preciomn':'De Venta' if a['preciocostomn'] else 'No Existe','preciocuc':'De Venta' if a['preciocuc'] else 'No Existe','dias':a['dias']})
                if queryset.__len__():  #22 
                    pdf_file_name=os.path.join(comerciax.settings.ADMIN_MEDIA_PDF,"Registro Contratos.pdf") 
                    if report_class.Reportes.GenerarRep(report_class.Reportes() , queryset, "reg_contrat",pdf_file_name,filtro)==0:
                        mesg=mesg+['Debe cerrar el documento Registro Contratos.pdf']
                        return render_to_response("comercial/reporteindex.html",{'filtro':filtro,'resultado':resultado,'form':form,'title':titulo_form, 'form_name':nombre_form,'form_description':descripcion_form,
                                                        'controlador':controlador_form,'accion':accion_form,'error2':mesg},context_instance = RequestContext(request))
                    else:
                        input = PdfFileReader(file(pdf_file_name,"rb"))
                        output = PdfFileWriter()
                        for page in input.pages:
                            output.addPage(page)
                        buffer = StringIO.StringIO()
                        output.write(buffer)
                        response = HttpResponse(mimetype='application/pdf')
                        response['Content-Disposition'] = 'attachment; filename=%s'%(pdf_file_name)
                        response.write(buffer.getvalue())
                        return response
                else:
                    mesg=mesg+['No existe información para mostrar']
                    return render_to_response("comercial/reporteindex.html",{'filtro':filtro,'resultado':resultado,'form':form,'title':titulo_form, 'form_name':nombre_form,'form_description':descripcion_form,
                                                        'controlador':controlador_form,'accion':accion_form,'error2':mesg},context_instance = RequestContext(request))

    else:
        form = Rep_RegContratos() 
    
    return render_to_response("comercial/reporteindex.html",{'form':form,'title':titulo_form, 'form_name':nombre_form,'form_description':descripcion_form,
                                                                'controlador':controlador_form,'accion':accion_form,'error2':mesg},context_instance = RequestContext(request))
    
#############################################################
#              REPORTE CASCOS X CLIENTES                    #
#############################################################
@login_required
def cascosxcliente(request):
    
    nombre_form='Reportes'
    descripcion_form='Cascos x cliente'
    titulo_form='Cascos x cliente' 
    controlador_form='Reportes'
    accion_form='/comerciax/comercial/cascosxcliente/reporte'
    cancelbtn_form='/comerciax/comercial/cascostraza'
    mesg=[]
    queryset=[]
    
    if request.method == 'POST':
        form = Rep_CascosCliente(request.POST)
        if form.is_valid():
            envia=False
            if request.POST.__contains__('submit2'):
                envia=True
                cliente=form.cleaned_data['ccliente']
                if cliente==None:
                    mesg=mesg+['Debe seleccionar un cliente']
                    return render_to_response("comercial/reporteindex.html",{'form':form,'title':titulo_form, 'form_name':nombre_form,'form_description':descripcion_form,
                                                                    'controlador':controlador_form,'accion':accion_form,'error2':mesg,'email':1},context_instance = RequestContext(request))
                correo=cliente.email
                if correo.__len__()==0:
                    mesg=mesg+['Este cliente no tiene correo']
                    return render_to_response("comercial/reporteindex.html",{'form':form,'title':titulo_form, 'form_name':nombre_form,'form_description':descripcion_form,
                                                                   'controlador':controlador_form,'accion':accion_form,'error2':mesg,'email':1},context_instance = RequestContext(request))
                try:
                    querySet = Config_SMTPEmail.objects.get()
                except Exception, e:
                    mesg=mesg+['No está configurado el correo SMTP']
                    return render_to_response("comercial/reporteindex.html",{'form':form,'title':titulo_form, 'form_name':nombre_form,'form_description':descripcion_form,
                                                                   'controlador':controlador_form,'accion':accion_form,'error2':mesg,'email':1},context_instance = RequestContext(request))
                servidor=querySet.servidor
                correo_envia=querySet.correo
                puerto = querySet.puerto
                ssl = querySet.ssl
                try:
                    contrasena = base64.b64decode(querySet.contrasena)
                except Exception, e:
                    mesg=mesg+['Revise la contraseña en la configuración del Correo SMTP']
                    return render_to_response("comercial/reporteindex.html",{'form':form,'title':titulo_form, 'form_name':nombre_form,'form_description':descripcion_form,
                                                                   'controlador':controlador_form,'accion':accion_form,'error2':mesg,'email':1},context_instance = RequestContext(request))

            particular= form.cleaned_data['particular']
            ocioso= form.cleaned_data['ocioso']
            cliente  = form.cleaned_data['ccliente']
            provincia  = form.cleaned_data['provincia']
            organismo  = form.cleaned_data['organismo']
            nro = form.cleaned_data['cnro']
            fecha=form.cleaned_data['cfecha']
            fechahasta=form.cleaned_data['cfechahasta']
            orden=form.cleaned_data['orden']
            estado=form.cleaned_data['estado']
            filtro=[]
            
            where_="date(fecha_doc) between '"+fecha.strftime("%Y-%m-%d")+"' and '"+fechahasta.strftime("%Y-%m-%d")+"'"
            filtro.append('Entrada desde: '+fecha.strftime("%d/%m/%Y")+" hasta "+fechahasta.strftime("%d/%m/%Y"))
            if organismo!=None:
                filtro.append('Organismo: '+organismo.siglas_organismo)
                where_+=" AND organismo_id='"+organismo.id+"'"
            if provincia!=None:
                filtro.append('Provincia: '+provincia.descripcion_provincia)
                where_+=" AND admincomerciax_provincias.codigo_provincia='"+provincia.codigo_provincia+"'"
            if cliente!=None:
                filtro.append('Cliente: '+cliente.nombre)
                where_+=" AND admincomerciax_cliente.id='"+cliente.id+"'"
            if nro!=None:
                filtro.append('Nro. casco: '+str(nro))
                where_+=" AND casco_casco.casco_nro="+str(nro)
            if estado!='G':
                filtro.append('Estado: '+unicode(Estados.estados[estado],'utf-8'))
                where_+=" AND casco_casco.estado_actual='"+estado+"'"
            if ocioso:
                where_+=" AND casco_casco.ocioso=True"
            else:
                where_+=" AND casco_casco.ocioso=False"
           
            orderby="order by casco_nro"    
            if form.cleaned_data['orden']=='cliente':                
                orderby="order by siglas_organismo,descripcion_provincia,nombre,casco_nro"
            
            if particular==False:
                where_+=" AND casco_casco.particular=False"
                resultado_sql= """
                            SELECT 
                              '' as ci,
                              casco_casco.casco_nro,
                              casco_casco.venta,
                              case when casco_casco.estado_actual = 'PT' and casco_casco.venta = True then
                                 'Para la Venta'
                              else casco_casco.estado_actual end as estado_actual,
                              admincomerciax_producto.descripcion AS producto_descripcion,
                              admincomerciax_producto.codigo AS producto_codigo,
                              admincomerciax_umedida.descripcion AS um,
                              casco_casco.producto_salida_id,
                              admincomerciax_cliente.nombre AS cliente_nombre,
                              admincomerciax_cliente.codigo AS cliente_codigo,
                              admincomerciax_organismo.siglas_organismo,
                              admincomerciax_provincias.descripcion_provincia,
                              casco_recepcionparticular.nombre,
                              casco_recepcionparticular.ci,
                              admincomerciax_provincias.codigo_provincia,
                              admincomerciax_organismo.id AS organismo_id,
                              admincomerciax_cliente.id,
                              casco_doc.fecha_doc,
                              casco_recepcioncliente.recepcioncliente_nro,
                              casco_recepcioncliente.recepcioncliente_tipo as tipo
                            FROM
                              casco_casco
                              INNER JOIN admincomerciax_producto ON (casco_casco.producto_salida_id = admincomerciax_producto.id)
                              INNER JOIN admincomerciax_umedida ON (admincomerciax_producto.um_id = admincomerciax_umedida.id)
                              FULL OUTER JOIN casco_detallerc ON (casco_casco.id_casco = casco_detallerc.casco_id)
                              FULL OUTER JOIN casco_detallerp ON (casco_casco.id_casco = casco_detallerp.casco_id)
                              LEFT OUTER JOIN casco_recepcioncliente ON (casco_detallerc.rc_id = casco_recepcioncliente.doc_recepcioncliente_id)
                              LEFT OUTER JOIN admincomerciax_cliente ON (casco_recepcioncliente.cliente_id = admincomerciax_cliente.id)
                              LEFT OUTER JOIN admincomerciax_organismo ON (admincomerciax_cliente.organismo_id = admincomerciax_organismo.id)
                              LEFT OUTER JOIN admincomerciax_provincias ON (admincomerciax_cliente.provincia_id = admincomerciax_provincias.codigo_provincia)
                              LEFT OUTER JOIN casco_recepcionparticular ON (casco_detallerp.rp_id = casco_recepcionparticular.doc_recepcionparticular_id)
                              LEFT OUTER JOIN casco_doc ON (casco_recepcioncliente.doc_recepcioncliente_id = casco_doc.id_doc)
                              OR (casco_doc.id_doc = casco_recepcionparticular.doc_recepcionparticular_id)
                            WHERE """+ where_ + """  """+orderby 
            else:
                orderby=" order by nombre"
                where_+=" AND casco_casco.particular=True"
                resultado_sql="""                
                    SELECT 
                          '' as siglas_organismo,
                          '' as descripcion_provincia,
                          casco_casco.casco_nro,
                          casco_casco.venta,
                          case when casco_casco.estado_actual = 'PT' and casco_casco.venta = True then
                            'Para la Venta'
                          else casco_casco.estado_actual end as estado_actual,
                          admincomerciax_producto.descripcion AS producto_descripcion,
                          admincomerciax_producto.codigo AS producto_codigo,
                          admincomerciax_umedida.descripcion AS um,
                          casco_casco.producto_salida_id,
                          concat('**',casco_recepcionparticular.nombre) as cliente_nombre,
                          casco_recepcionparticular.ci as cliente_codigo,
                          casco_doc.fecha_doc,
                          casco_recepcionparticular.recepcionparticular_nro as recepcioncliente_nro,
                          casco_recepcionparticular.recepcionparticular_tipo as tipo
                        FROM
                          casco_casco
                          INNER JOIN admincomerciax_producto ON (casco_casco.producto_salida_id = admincomerciax_producto.id)
                          INNER JOIN admincomerciax_umedida ON (admincomerciax_producto.um_id = admincomerciax_umedida.id)
                          INNER JOIN casco_detallerp ON (casco_casco.id_casco = casco_detallerp.casco_id)
                          RIGHT OUTER JOIN casco_recepcionparticular ON (casco_detallerp.rp_id = casco_recepcionparticular.doc_recepcionparticular_id)
                          INNER JOIN casco_doc ON (casco_doc.id_doc = casco_recepcionparticular.doc_recepcionparticular_id)
                          WHERE """+ where_ + """  """+orderby
                        
                            
            resultado1 = query_to_dicts(resultado_sql)
            resultado=[]
            nombre=""
            provincia=""
            organismo=""
            for a in resultado1:
                sorg=a['siglas_organismo'] 
                prov=a['descripcion_provincia'] 
                cnom=a['cliente_nombre']
                ccod=a['cliente_codigo']
                cnro=a['recepcioncliente_nro'] 
                
                estado=a["estado_actual"]
                resultado=resultado+[{"fecha_doc":a["fecha_doc"].strftime("%d/%m/%Y"),"ministerio":sorg,
                                      "provincia":prov,"nombre":cnom,"codigo":ccod,"recepcioncliente_nro":cnro,
                                      "casco_nro":a["casco_nro"] if a["tipo"] == 'O' else str(a["casco_nro"])+"("+a["tipo"]+")",
                                      "descripcion":a["producto_descripcion"],
                                      "estado_actual":unicode(Estados.estados[estado],'utf-8') if Estados.estados.has_key(estado) else estado}]

            if resultado.__len__()==0:
                form = Rep_CascosCliente()
                mesg=mesg+['No existe información para mostrar']
                return render_to_response("comercial/reporteindex.html",{'filtro':filtro,'resultado':resultado,'form':form,'title':titulo_form, 'form_name':nombre_form,'form_description':descripcion_form,
                                                                'controlador':controlador_form,'accion':accion_form,'error2':mesg,'email':1},context_instance = RequestContext(request))
            if request.POST.__contains__('submit1') or request.POST.__contains__('submit2'): 
                pdf_file_name=os.path.join(comerciax.settings.ADMIN_MEDIA_PDF,"Cascos por Cliente.pdf")
                if report_class.Reportes.GenerarRep(report_class.Reportes() , resultado, "cascos_client",pdf_file_name,filtro)==0:
                    mesg=mesg+['Debe cerrar el documento Cascos por Cliente.pdf']
                    return render_to_response("comercial/reporteindex.html",{'filtro':filtro,'resultado':resultado,'form':form,'title':titulo_form, 'form_name':nombre_form,'form_description':descripcion_form,
                                                'controlador':controlador_form,'accion':accion_form,'error2':mesg,'email':1},context_instance = RequestContext(request))                
                else:
                    input = PdfFileReader(file(pdf_file_name,"rb"))
                    file_namesitio='%s'%(pdf_file_name)
                    output = PdfFileWriter()
                    for page in input.pages:
                        output.addPage(page)
                    buffer = StringIO.StringIO()
                    output.write(buffer)
                    response = HttpResponse(mimetype='application/pdf')
                    response['Content-Disposition'] = 'attachment; filename=%s'%(pdf_file_name)
                    response.write(buffer.getvalue())
                    if envia:
                        import smtplib
                        from email.mime.application import MIMEApplication
                        from django.core.mail.message import EmailMessage
                        try:
                            message = EmailMessage(subject='Cascos por Cliente',body='Enviado por '+request.user.first_name+' '+request.user.last_name, from_email=correo_envia, to=[correo])
                            part = MIMEApplication(open(file_namesitio,"rb").read())
                            part.add_header('Content-Disposition', 'attachment', filename="Cascos por Cliente.pdf")
                            message.attach(part)
                            if ssl==True:
                                smtp = smtplib.SMTP_SSL(host=servidor,port=puerto)
                            else:
                                smtp = smtplib.SMTP(servidor)
                            smtp.ehlo()
                            smtp.login(correo_envia,contrasena)
                            smtp.sendmail(correo_envia,[correo],message.message().as_string())
                            smtp.close()
                            return response         
                        except Exception, e:
                            mesg=mesg+['Error de conexión. Revise la configuración del Correo SMTP']
                            return render_to_response("comercial/reporteindex.html",{'filtro':filtro,'resultado':resultado,'form':form,'title':titulo_form, 'form_name':nombre_form,'form_description':descripcion_form,
                                                    'controlador':controlador_form,'accion':accion_form,'error2':mesg},context_instance = RequestContext(request))
                    return response
                

                
            return render_to_response("report/cascos_clientes.html",{'form':form,'filtro':filtro,'fecha_hoy':fecha_hoy(),'resultado':resultado,'error2':mesg,'particular':particular},context_instance = RequestContext(request))
    else:
        form = Rep_CascosCliente() 
    return render_to_response("comercial/reporteindex.html",{'form':form,'title':titulo_form, 'form_name':nombre_form,'form_description':descripcion_form,
                                                                'cancelbtn':cancelbtn_form,'controlador':controlador_form,'accion':accion_form,'error2':mesg,'email':1},context_instance = RequestContext(request))
    
############################################################
#              REPORTE TRAZABILIDAD DEL CASCO              #
############################################################
@login_required
def cascostraza(request):
    nombre_form='Reportes'
    descripcion_form='Trazabilidad de Cascos'
    titulo_form='Trazabilidad de Cascos' 
    controlador_form='Reportes'
    accion_form='/comerciax/comercial/cascostraza/reporte'
    cancelbtn_form='/comerciax/comercial/cascostraza/'
    mesg=[]
    
    if request.method == 'POST':
        form = Rep_CascosTraza(request.POST)
        if form.is_valid():
            cliente  = form.cleaned_data['ccliente']
            organismo = form.cleaned_data['organismo']
            provincia = form.cleaned_data['provincia']
            nro = form.cleaned_data['cnro']
            fecha=form.cleaned_data['cfecha']
            particular=form.cleaned_data['particular']
            filtro=[]
            filtro.append('Trazabilidad desde: '+fecha.strftime("%d/%m/%Y"))
            resultado1= TrazabilidadCasco.objects.select_related().filter(doc__fecha_doc__gte=fecha)
            if organismo!=None:
                resultado1 = resultado1.filter(casco__detallerc__rc__cliente__organismo__id=organismo.id)
                filtro.append('Organismo: '+organismo.siglas_organismo)
            if provincia!=None:
                resultado1 = resultado1.filter(casco__detallerc__rc__cliente__provincia__codigo_provincia=provincia.codigo_provincia)
                filtro.append('Provincia: '+provincia.descripcion_provincia)
            if cliente!=None: 
                resultado1 = resultado1.filter(casco__detallerc__rc__cliente__id=cliente.id) 
                filtro.append('Cliente: '+cliente.nombre) 
            resultado1=resultado1.order_by('casco','nro')
            if particular==True:
                resultado1=resultado1.filter(casco__particular=True)
            if nro!=None:
                resultado1=resultado1.filter(casco__casco_nro=nro)
            
            nombre=""
            ci=""
            nombrep=""
            nombrec=""
            codigoc=""
            resultado=[]
            for a in resultado1:
                estado=a.estado
                ocioso = ""
                descripcion=a.casco.producto.descripcion
                if estado=='PT' or estado=='DC' or estado=='Factura':
                    descripcion=a.casco.producto_salida.descripcion
                if estado=='Casco':
                    ocioso = " (Ocioso)" if a.casco.ocioso else ""
                
                nombredos=a.casco.get_cliente() 
                codi=a.casco.get_cliente_organismo()
                
                if nombre == nombredos:
                    nombre=nombredos
                    nombrec=""
                    codigoc=""
                else:
                    nombre=nombredos
                    nombrec=nombredos
                    codigoc=codi
                    
                nrodoc="-"
                tipodoc=a.doc.tipo_doc
                iddoc=a.doc.id_doc
#                tipodoc=a["tipo_doc"]
                if tipodoc=='1' or tipodoc=='3': # Recepcion cliente y recep. cliente ext.
                    obj=RecepcionCliente.objects.get(doc_recepcioncliente=iddoc)
                    nrodoc= str(obj.recepcioncliente_nro) + ' (' + tipo_entrada[str(obj.recepcioncliente_tipo)]+')' if str(obj.recepcioncliente_tipo) != 'O' else str(obj.recepcioncliente_nro)
                elif tipodoc=='2':
                    nrodoc=CC.objects.get(doc_cc=iddoc).cc_nro
                elif tipodoc=='4':
                    nrodoc=DIP.objects.get(doc_dip=iddoc).nro_dip
                elif tipodoc=='5':
                    nrodoc=DVP.objects.get(doc_dvp=iddoc).nro_dvp
                elif tipodoc=='6':
                    nrodoc=Transferencia.objects.get(doc_transferencia=iddoc).transferencia_nro
                elif tipodoc=='8':
                    nrodoc=EntregaRechazado.objects.get(doc_entregarechazado=iddoc).entregarechazado_nro
                elif tipodoc=='9':
                    nrodoc=ProduccionTerminada.objects.get(doc_pt=iddoc).produccionterminada_nro
                elif tipodoc=='10':
                    nrodoc=PTExternos.objects.get(doc_ptexternos=iddoc).ptexternos_nro
                elif tipodoc=='11':
                    nrodoc=RecepRechaExt.objects.get(doc_receprechaext=iddoc).receprechaext_nro
                elif tipodoc=='12':
                    nrodoc=VulcaProduccion.objects.get(doc_vulcaproduccion=iddoc).vulcaproduccion_nro
                elif tipodoc=='14':
                    nrodoc=Facturas.objects.get(doc_factura=iddoc).factura_nro
                elif tipodoc=='15':
                    nrodoc=""
                elif tipodoc=='16':
                    obj=RecepcionParticular.objects.get(doc_recepcionparticular=iddoc)
                    # nrodoc=str(obj.recepcionparticular_nro) + ' (' + tipo_entrada[str(obj.recepcioncliente_tipo)]+')'
                    nrodoc = str(obj.recepcionparticular_nro) + ' (' + tipo_entrada[
                        str(obj.recepcionparticular_tipo)] + ')' if str(obj.recepcionparticular_tipo) != 'O' else str(
                        obj.recepcionparticular_nro)
                elif tipodoc=='17':
                    nrodoc=FacturasParticular.objects.get(doc_factura=iddoc).factura_nro
                elif tipodoc=='18':
                    nrodoc=RecepCascoExt.objects.get(doc_recepcascoext=iddoc).recepcascoext_nro
                    
                resultado=resultado+[{"fecha_doc":a.doc.fecha_doc,"nombre":nombrec,"codigo":codigoc,
                                      "casco_nro":a.casco.get_nro_tipo(),
                                      "estado":unicode(Estados.estados[estado],'utf-8')+ocioso,"nrodoc":nrodoc,"descripcion":descripcion}]
            if request.POST.__contains__('submit1'):
                if resultado.__len__():    
                        pdf_file_name=os.path.join(comerciax.settings.ADMIN_MEDIA_PDF,"Trazabilidad de Cascos.pdf")
                        if report_class.Reportes.GenerarRep(report_class.Reportes() , resultado, "cascos_traza",pdf_file_name,filtro)==0:
                            mesg=mesg+['Debe cerrar el documento Trazabilidad de Cascos.pdf']
                            return render_to_response("comercial/reporteindex.html",{'filtro':filtro,'resultado':resultado,'form':form,'title':titulo_form, 'form_name':nombre_form,'form_description':descripcion_form,
                                                        'controlador':controlador_form,'accion':accion_form,'error2':mesg},context_instance = RequestContext(request))                        
                        else:
                            input = PdfFileReader(file(pdf_file_name,"rb"))
                            output = PdfFileWriter()
                            for page in input.pages:
                                output.addPage(page)
                            buffer = StringIO.StringIO()
                            output.write(buffer)
                            response = HttpResponse(mimetype='application/pdf')
                            response['Content-Disposition'] = 'attachment; filename=%s'%(pdf_file_name)
                            response.write(buffer.getvalue())
                            return response    
                else:
                    mesg=mesg+['No existe información para mostrar']
                    return render_to_response("comercial/reporteindex.html",{'filtro':filtro,'resultado':resultado,'form':form,'title':titulo_form, 'form_name':nombre_form,'form_description':descripcion_form,
                                                        'controlador':controlador_form,'accion':accion_form,'error2':mesg},context_instance = RequestContext(request))
            else: 
                if resultado.__len__()==0:
                    mesg=mesg+['No existe información para mostrar']
                    return render_to_response("comercial/reporteindex.html",{'form':form,'title':titulo_form, 'form_name':nombre_form,'form_description':descripcion_form,
                                                            'controlador':controlador_form,'accion':accion_form,'error2':mesg},context_instance = RequestContext(request))
                return render_to_response("report/cascos_traza.html",{'filtro':filtro,'fecha_hoy':fecha_hoy(),'resultado':resultado,'error2':mesg},context_instance = RequestContext(request))

    else:
        
        form = Rep_CascosTraza() 
    
    return render_to_response("comercial/reporteindex.html",{'form':form,'title':titulo_form, 'form_name':nombre_form,'form_description':descripcion_form,
                                                                'controlador':controlador_form,'accion':accion_form,'error2':mesg},context_instance = RequestContext(request))
    
@login_required
def cascosventa(request):
    
    nombre_form='Reportes'
    descripcion_form='Cascos para la venta en PT'
    titulo_form='Cascos para la venta en PT' 
    controlador_form='Reportes'
    accion_form='/comerciax/comercial/cascosventa/reporte'
    cancelbtn_form='/comerciax/comercial/cascosventa/'
    mesg=[]
    queryset=[]
    if request.method == 'POST':
        form = Rep_CascosVenta(request.POST)
        if form.is_valid():
            if form.cleaned_data['orden']=='medida':
                resultado=DetalleRC.objects.select_related().filter(casco__venta=True, casco__estado_actual="PT").order_by('admincomerciax_producto.descripcion','admincomerciax_cliente.nombre')
            else:
                resultado=DetalleRC.objects.select_related().filter(casco__venta=True, casco__estado_actual="PT").order_by('admincomerciax_cliente.nombre','admincomerciax_producto.descripcion')
            if request.POST.__contains__('submit1'):
                if resultado.__len__():    
                    for a in resultado:
                        queryset.append({'producto':a.casco.producto.descripcion,
                                         'casco_nro':a.casco.casco_nro if a.rc.recepcioncliente_tipo=='O' else str(a.casco.casco_nro)+'('+a.rc.recepcioncliente_tipo+')',
                                         'nombre':a.rc.cliente.nombre})
                    pdf_file_name=os.path.join(comerciax.settings.ADMIN_MEDIA_PDF,"Cascos para la Venta en PT.pdf")
                    if report_class.Reportes.GenerarRep(report_class.Reportes() , queryset, "cascos_venta",pdf_file_name,[])==0:
                        mesg=mesg+['Debe cerrar el documento Cascos para la Venta en PT.pdf']
                        return render_to_response("report/cascos_venta.html",{'fecha_hoy':fecha_hoy(),'resultado':resultado,'error2':mesg},context_instance = RequestContext(request))
                    else:
                        input = PdfFileReader(file(pdf_file_name,"rb"))
                        output = PdfFileWriter()
                        for page in input.pages:
                            output.addPage(page)
                        buffer = StringIO.StringIO()
                        output.write(buffer)
                        response = HttpResponse(mimetype='application/pdf')
                        response['Content-Disposition'] = 'attachment; filename=%s'%(pdf_file_name)
                        response.write(buffer.getvalue())
                        return response                     
                        
                else:
                    mesg=mesg+['No existe información para mostrar']
                    return render_to_response("report/cascos_venta.html",{'fecha_hoy':fecha_hoy(),'resultado':resultado,'error2':mesg},context_instance = RequestContext(request))
            else: 
                if resultado.__len__()==0:
                    mesg=mesg+['No existe información para mostrar']
                    return render_to_response("comercial/reporteindex.html",{'form':form,'title':titulo_form, 'form_name':nombre_form,'form_description':descripcion_form,
                                                                    'controlador':controlador_form,'accion':accion_form,'error2':mesg},context_instance = RequestContext(request))
                return render_to_response("report/cascos_venta.html",{'fecha_hoy':fecha_hoy(),'resultado':resultado,'error2':mesg},context_instance = RequestContext(request))
            
    form = Rep_CascosVenta() 
    
    return render_to_response("comercial/reporteindex.html",{'form':form,'title':titulo_form, 'form_name':nombre_form,'form_description':descripcion_form,
                                                                'controlador':controlador_form,'accion':accion_form,'error2':mesg},context_instance = RequestContext(request))


@login_required
def cascosptedad(request):

    resultado1 = query_to_dicts("""
                select uno.descripcion, count(uno.s1) as s1, count(uno.s2) as s2, count(uno.s3) as s3, count(uno.s1)+count(uno.s2)+count(uno.s3) as total_prod
                    from (SELECT 
                      admincomerciax_producto.descripcion,
                      case 
                         when (cast(date_part('day', now()-casco_doc.fecha_doc) as integer)<=30) then (cast(date_part('day', now()-casco_doc.fecha_doc) as integer))
                      end as s1,
                      case 
                         when (cast(date_part('day', now()-casco_doc.fecha_doc) as integer)>30 and cast(date_part('day', now()-casco_doc.fecha_doc) as integer)<=45) then (cast(date_part('day', now()-casco_doc.fecha_doc) as integer))
                      end as s2,
                      case 
                         when (cast(date_part('day', now()-casco_doc.fecha_doc) as integer)>45) then (cast(date_part('day', now()-casco_doc.fecha_doc) as integer))
                      end as s3
                    FROM 
                      public.casco_casco
                      join admincomerciax_producto on casco_casco.producto_salida_id = admincomerciax_producto.id
                      join casco_detallept on casco_detallept.casco_id = casco_casco.id_casco
                      join casco_produccionterminada on casco_detallept.pt_id = casco_produccionterminada.doc_pt_id
                      join casco_doc on casco_produccionterminada.doc_pt_id = casco_doc.id_doc
                     where casco_casco.estado_actual = 'PT'
                    union all
                    SELECT 
                      admincomerciax_producto.descripcion,
                      case 
                         when (cast(date_part('day', now()-casco_doc.fecha_doc) as integer)<=30) then (cast(date_part('day', now()-casco_doc.fecha_doc) as integer))
                      end as s1,
                      case 
                         when (cast(date_part('day', now()-casco_doc.fecha_doc) as integer)>30 and cast(date_part('day', now()-casco_doc.fecha_doc) as integer)<=45) then (cast(date_part('day', now()-casco_doc.fecha_doc) as integer))
                      end as s2,
                      case 
                         when (cast(date_part('day', now()-casco_doc.fecha_doc) as integer)>45) then (cast(date_part('day', now()-casco_doc.fecha_doc) as integer))
                      end as s3
                    FROM 
                      public.casco_casco
                      join admincomerciax_producto on casco_casco.producto_salida_id = admincomerciax_producto.id
                      join casco_detallepte on casco_detallepte.casco_id = casco_casco.id_casco
                      join casco_ptexternos on casco_detallepte.doc_pte_id = casco_ptexternos.doc_ptexternos_id
                      join casco_doc on casco_ptexternos.doc_ptexternos_id = casco_doc.id_doc
                     where casco_casco.estado_actual = 'PT'
                    order by descripcion) as uno
                    group by uno.descripcion
                  """)
    resultado=[]
    total_s1=0
    total_s2=0
    total_s3=0
    for datos in resultado1:
        resultado=resultado+[{'medida':datos['descripcion'], 
                              's1': str(datos['s1']), 
                              's2': str(datos['s2']), 
                              's3': str(datos['s3']), 
                              'total_prod': str(datos['total_prod'])}]
        total_s1+=datos['s1']
        total_s2+=datos['s2']
        total_s3+=datos['s3']
    resultado=resultado+[{'medida':'T O T A L', 
                              's1': str(total_s1), 
                              's2': str(total_s2), 
                              's3': str(total_s3), 
                              'total_prod': str(total_s1+total_s2+total_s3)}]
    if resultado.__len__():                        
        pdf_file_name=os.path.join(comerciax.settings.ADMIN_MEDIA_PDF,"Cascos en PT por Edad.pdf")
        if report_class.Reportes.GenerarRep(report_class.Reportes() , resultado, "cascos_pt_edad",pdf_file_name,[])!=0:
            input = PdfFileReader(file(pdf_file_name,"rb"))
            output = PdfFileWriter()
            for page in input.pages:
                output.addPage(page)
            buffer = StringIO.StringIO()
            output.write(buffer)
            response = HttpResponse(mimetype='application/pdf')
            file_namesitio='%s'%(pdf_file_name)
            response['Content-Disposition'] = 'attachment; filename=%s'%(pdf_file_name)
            response.write(buffer.getvalue())
            return response

@login_required
def cascosestado(request):
    
    nombre_form='Reportes'
    descripcion_form='Cascos x Estado'
    titulo_form='Cascos x Estado' 
    controlador_form='Reportes'
    accion_form='/comerciax/comercial/cascosestado/reporte'
    mesg=[]
    
    if request.method == 'POST':
        form = Rep_CascosEstado(request.POST)
        
        if form.is_valid():
            envia=False
            
            if request.POST.__contains__('submit2'):
                envia=True
                cliente=form.cleaned_data['ccliente']
                if cliente==None:
                    mesg=mesg+['Debe seleccionar un cliente']
                    return render_to_response("comercial/reporteindex.html",{'form':form,'title':titulo_form, 'form_name':nombre_form,'form_description':descripcion_form,
                                                                    'controlador':controlador_form,'accion':accion_form,'error2':mesg,'email':1},context_instance = RequestContext(request))
                correo=cliente.email
                if correo.__len__()==0:
                    mesg=mesg+['Este cliente no tiene correo']
                    return render_to_response("comercial/reporteindex.html",{'form':form,'title':titulo_form, 'form_name':nombre_form,'form_description':descripcion_form,
                                                                   'controlador':controlador_form,'accion':accion_form,'error2':mesg,'email':1},context_instance = RequestContext(request))
                try:
                    querySet = Config_SMTPEmail.objects.get()
                except Exception, e:
                    mesg=mesg+['No está configurado el correo SMTP']
                    return render_to_response("comercial/reporteindex.html",{'form':form,'title':titulo_form, 'form_name':nombre_form,'form_description':descripcion_form,
                                                                   'controlador':controlador_form,'accion':accion_form,'error2':mesg,'email':1},context_instance = RequestContext(request))
                servidor=querySet.servidor
                correo_envia=querySet.correo
                puerto = querySet.puerto
                ssl = querySet.ssl
                try:
                    contrasena = base64.b64decode(querySet.contrasena)
                except Exception, e:
                    mesg=mesg+['Revise la contraseña en la configuración del Correo SMTP']
                    return render_to_response("comercial/reporteindex.html",{'form':form,'title':titulo_form, 'form_name':nombre_form,'form_description':descripcion_form,
                                                                   'controlador':controlador_form,'accion':accion_form,'error2':mesg,'email':1},context_instance = RequestContext(request))
                
                
            medida=form.cleaned_data['estado']
            particular=form.cleaned_data['particular']
            ocioso=form.cleaned_data['ocioso']
            venta=form.cleaned_data['venta']
            medidaprod=form.cleaned_data['medida']
            cliente=form.cleaned_data['ccliente']
            organismo=form.cleaned_data['organismo']
            provincia=form.cleaned_data['provincia']
            dias=form.cleaned_data['dias']
            diasmax=form.cleaned_data['diasmax']
            orden = form.cleaned_data['orden'].capitalize()
            
            diascap = 0 if dias == None else dias
            diasmaxi = 0 if diasmax == None else diasmax
            
            if diasmaxi != 0 and diasmaxi < diascap:
                mesg=mesg+['El máximo de días puede ser menor que el mínimo de días']
                return render_to_response("comercial/reporteindex.html",{'form':form,'title':titulo_form, 'form_name':nombre_form,'form_description':descripcion_form,
                                                                'controlador':controlador_form,'accion':accion_form,'error2':mesg,'email':1},context_instance = RequestContext(request))
            diasmin = diascap
            filtro=[]
            where=[]
            
            if cliente!=None:
                where.append("cliente_id='"+cliente.id+"'")
                filtro.append('Cliente: '+cliente.nombre)
            else:
                if organismo!=None:
                    where.append("siglas_organismo='"+organismo.siglas_organismo+"'")
                    filtro.append('Organismo: '+organismo.siglas_organismo)
                if provincia!=None:
                    where.append("codigo_provincia='"+provincia.codigo_provincia+"'")
                    filtro.append('Provincia: '+provincia.descripcion_provincia)
            estado=False                    
            if medida!='G':
                filtro.append('Estado: '+unicode(Estados.estados[medida],'utf-8'))
                where.append("estado_actual= '"+medida+"'")

            if medidaprod!=None:
                filtro.append('Medida: '+medidaprod.descripcion)
                where.append("producto_salida_id='"+medidaprod.id+"'")   
                
            if venta==True:
                filtro.append('Casco que entraron para la venta ')
                
            if ocioso==True:
                filtro.append('Casco Ociosos ')
                
            if particular==True:
                filtro.append('Casco de entidades no estatal ')
            
            where.append(" ocioso = False" if not ocioso else " ocioso = True") 
            estadoocioso = "" if not ocioso else " (Ocioso)"          
                
            
            optwhere=" where " if len(where)>0 else ""               
            for a1 in range(len(where)):
                optwhere+= where[a1]+ " AND "
            long=len(optwhere)
            optwhere=optwhere[0:long-4]
            opt=str(optwhere)
            order = ""
            if particular==False:
                opt = opt + " and casco_casco.particular = False "
                if venta:
                    opt = opt+" and casco_casco.venta = True and casco_casco.decomisado=False "
                order = """ ORDER BY estado_actual, producto_descripcion, cliente_nombre, casco_nro """ if orden == 'Medida' else """ ORDER BY estado_actual, cliente_nombre, producto_descripcion"""

                resultado1 = query_to_dicts("""
                           SELECT 
                              casco_casco.venta,
                              casco_casco.decomisado,
                              casco_casco.casco_nro,
                              casco_casco.id_casco,
                              casco_casco.estado_actual,
                              casco_casco.decomisado,
                              admincomerciax_producto.descripcion AS producto_descripcion,
                              admincomerciax_producto.codigo AS producto_codigo,
                              admincomerciax_umedida.descripcion AS um,
                              casco_casco.producto_salida_id,
                              admincomerciax_cliente.nombre AS cliente_nombre,
                              admincomerciax_cliente.codigo AS cliente_codigo,
                              admincomerciax_organismo.siglas_organismo,
                              admincomerciax_provincias.descripcion_provincia,
                              casco_recepcionparticular.nombre,
                              casco_recepcionparticular.ci,
                              admincomerciax_provincias.codigo_provincia,
                              admincomerciax_organismo.id AS organismo_id,
                              admincomerciax_cliente.id as cliente_id,
                              coalesce(dest.nombre,'') as destino,
                              case when casco_casco.estado_actual = 'Casco' then
                                 (select DATE_PART('day', now()- casco_doc.fecha_doc) from casco_detallerc 
                                 inner join casco_recepcioncliente on casco_recepcioncliente.doc_recepcioncliente_id = casco_detallerc.rc_id
                                 inner join casco_doc on casco_recepcioncliente.doc_recepcioncliente_id = casco_doc.id_doc
                                 where casco_detallerc.casco_id = casco_casco.id_casco)
                              when casco_casco.estado_actual = 'Produccion' then
                                (select DATE_PART('day', now()-max(dat1.fecha_doc)) as dias
                                from
                                (select casco_doc.fecha_doc 
                                from casco_detallevp 
                                inner join casco_vulcaproduccion on casco_vulcaproduccion.doc_vulcaproduccion_id = casco_detallevp.vp_id
                                inner join casco_doc on casco_vulcaproduccion.doc_vulcaproduccion_id = casco_doc.id_doc
                                where casco_detallevp.casco_id = casco_casco.id_casco
                                union all 
                                select casco_doc.fecha_doc
                                from casco_detallecc
                                inner join casco_cc on casco_cc.doc_cc_id = casco_detallecc.cc_id
                                inner join casco_doc on casco_cc.doc_cc_id = casco_doc.id_doc
                                where casco_detallecc.casco_id = casco_casco.id_casco
                                ) as dat1)
                             when casco_casco.estado_actual = 'PT' then
                                (select DATE_PART('day', now()-max(dat1.fecha_doc)) as dias
                                from
                                (select casco_doc.fecha_doc 
                                from casco_detallept 
                                inner join casco_produccionterminada on casco_produccionterminada.doc_pt_id = casco_detallept.pt_id
                                inner join casco_doc on casco_produccionterminada.doc_pt_id = casco_doc.id_doc
                                where casco_detallept.casco_id = casco_casco.id_casco
                                union all 
                                select casco_doc.fecha_doc 
                                from casco_detallepte 
                                inner join casco_ptexternos on casco_ptexternos.doc_ptexternos_id = casco_detallepte.doc_pte_id
                                inner join casco_doc on casco_ptexternos.doc_ptexternos_id = casco_doc.id_doc
                                where casco_detallepte.casco_id = casco_casco.id_casco
                                ) as dat1)
                             when casco_casco.estado_actual = 'Transferencia' then
                                (select DATE_PART('day', now()-max(casco_doc.fecha_doc))
                                from casco_detalletransferencia 
                                inner join casco_transferencia on casco_transferencia.doc_transferencia_id = casco_detalletransferencia.transf_id
                                inner join casco_doc on casco_transferencia.doc_transferencia_id = casco_doc.id_doc
                                where casco_detalletransferencia.casco_id = casco_casco.id_casco)
                             when casco_casco.estado_actual = 'DIP' then
                                (select DATE_PART('day', now()-max(casco_doc.fecha_doc))
                                from casco_detalledip 
                                inner join casco_dip on casco_dip.doc_dip_id = casco_detalledip.dip_id
                                inner join casco_doc on casco_dip.doc_dip_id = casco_doc.id_doc
                                where casco_detalledip.casco_id = casco_casco.id_casco)
                             when casco_casco.estado_actual = 'DVP' then
                                (select DATE_PART('day', now()-max(casco_doc.fecha_doc))
                                from casco_detalledvp 
                                inner join casco_dvp on casco_dvp.doc_dvp_id = casco_detalledvp.dvp_id
                                inner join casco_doc on casco_dvp.doc_dvp_id = casco_doc.id_doc
                                where casco_detalledvp.casco_id = casco_casco.id_casco)
                             when casco_casco.estado_actual = 'ER' then
                                (select DATE_PART('day', now()-max(casco_doc.fecha_doc))
                                from casco_detalle_er 
                                inner join casco_errorrecepcion on casco_errorrecepcion.doc_errorrecepcion_id = casco_detalle_er.errro_revision_id
                                inner join casco_doc on casco_errorrecepcion.doc_errorrecepcion_id = casco_doc.id_doc
                                where casco_detalle_er.casco_id = casco_casco.id_casco)
                             when casco_casco.estado_actual = 'ECR' then
                                (select DATE_PART('day', now()-max(casco_doc.fecha_doc))
                                from casco_detalleentregarechazado
                                inner join casco_entregarechazado on casco_entregarechazado.doc_entregarechazado_id = casco_detalleentregarechazado.erechazado_id
                                inner join casco_doc on casco_entregarechazado.doc_entregarechazado_id = casco_doc.id_doc
                                where casco_detalleentregarechazado.casco_id = casco_casco.id_casco)
                            when casco_casco.estado_actual = 'REE' then
                                (select DATE_PART('day', now()-max(casco_doc.fecha_doc))
                                from casco_detallerre
                                inner join casco_receprechaext on casco_receprechaext.doc_receprechaext_id = casco_detallerre.receprechaext_id
                                inner join casco_doc on casco_receprechaext.doc_receprechaext_id = casco_doc.id_doc
                                where casco_detallerre.casco_id = casco_casco.id_casco)
                            when casco_casco.estado_actual = 'DCC' then
                                (select DATE_PART('day', now()-max(casco_doc.fecha_doc))
                                from casco_detalledcc
                                inner join casco_devolucioncasco on casco_devolucioncasco.doc_devolucion_id = casco_detalledcc.devolucion_id
                                inner join casco_doc on casco_devolucioncasco.doc_devolucion_id = casco_doc.id_doc
                                where casco_detalledcc.casco_id = casco_casco.id_casco)
                               when casco_casco.estado_actual = 'DC' then
                                (select DATE_PART('day', now()-max(casco_doc.fecha_doc))
                                from casco_detalle_dc
                                inner join casco_cascodecomiso on casco_cascodecomiso.doc_decomiso_id = casco_detalle_dc.doc_decomiso_id
                                inner join casco_doc on casco_cascodecomiso.doc_decomiso_id = casco_doc.id_doc
                                where casco_detalle_dc.casco_id = casco_casco.id_casco)
                             else 0 end as dias,
                             casco_recepcioncliente.recepcioncliente_tipo as tipo
                            FROM
                              casco_casco
                              INNER JOIN admincomerciax_producto ON (casco_casco.producto_salida_id = admincomerciax_producto.id)
                              INNER JOIN admincomerciax_umedida ON (admincomerciax_producto.um_id = admincomerciax_umedida.id)
                              FULL OUTER JOIN casco_detallerc ON (casco_casco.id_casco = casco_detallerc.casco_id)
                              FULL OUTER JOIN casco_detallerp ON (casco_casco.id_casco = casco_detallerp.casco_id)
                              FULL OUTER JOIN casco_detalletransferencia ON (casco_casco.id_casco = casco_detalletransferencia.casco_id)
                              LEFT OUTER JOIN casco_recepcioncliente ON (casco_detallerc.rc_id = casco_recepcioncliente.doc_recepcioncliente_id)
                              LEFT OUTER JOIN admincomerciax_cliente ON (casco_recepcioncliente.cliente_id = admincomerciax_cliente.id)
                              LEFT OUTER JOIN admincomerciax_organismo ON (admincomerciax_cliente.organismo_id = admincomerciax_organismo.id)
                              LEFT OUTER JOIN admincomerciax_provincias ON (admincomerciax_cliente.provincia_id = admincomerciax_provincias.codigo_provincia)
                              LEFT OUTER JOIN casco_recepcionparticular ON (casco_detallerp.rp_id = casco_recepcionparticular.doc_recepcionparticular_id)
                              left join casco_transferencia on (casco_detalletransferencia.transf_id = casco_transferencia.doc_transferencia_id) 
                              LEFT JOIN admincomerciax_cliente dest ON (casco_transferencia.destino_id = dest.id)"""+opt+ order)
            else:
                opt = opt +" and casco_casco.particular = True "
                if venta:
                    opt = opt+" and casco_casco.venta = True and casco_casco.decomisado=False "
                order = """ ORDER BY estado_actual, producto_descripcion, nombre, casco_nro """ if orden == 'Medida' else """ ORDER BY estado_actual, nombre, producto_descripcion"""
                resultado1 = query_to_dicts("""
                SELECT 
                      casco_casco.venta,
                      casco_casco.decomisado,
                      casco_casco.casco_nro,
                      casco_casco.id_casco,
                      casco_casco.estado_actual,
                      admincomerciax_producto.descripcion AS producto_descripcion,
                      admincomerciax_producto.codigo AS producto_codigo,
                      admincomerciax_umedida.descripcion AS um,
                      casco_casco.producto_salida_id,
                      casco_recepcionparticular.nombre,
                      casco_recepcionparticular.ci,
                      case when casco_casco.estado_actual = 'Casco' and casco_casco.particular = True then
                         (select DATE_PART('day', now()- casco_doc.fecha_doc) from casco_detallerp
                         inner join casco_recepcionparticular on casco_recepcionparticular.doc_recepcionparticular_id = casco_detallerp.rp_id
                         inner join casco_doc on casco_recepcionparticular.doc_recepcionparticular_id = casco_doc.id_doc
                         where casco_detallerp.casco_id = casco_casco.id_casco)
                      when casco_casco.estado_actual = 'Produccion' then
                        (select DATE_PART('day', now()-max(dat1.fecha_doc)) as dias
                        from
                        (select casco_doc.fecha_doc 
                        from casco_detallevp 
                        inner join casco_vulcaproduccion on casco_vulcaproduccion.doc_vulcaproduccion_id = casco_detallevp.vp_id
                        inner join casco_doc on casco_vulcaproduccion.doc_vulcaproduccion_id = casco_doc.id_doc
                        where casco_detallevp.casco_id = casco_casco.id_casco
                        union all 
                        select casco_doc.fecha_doc
                        from casco_detallecc
                        inner join casco_cc on casco_cc.doc_cc_id = casco_detallecc.cc_id
                        inner join casco_doc on casco_cc.doc_cc_id = casco_doc.id_doc
                        where casco_detallecc.casco_id = casco_casco.id_casco
                        ) as dat1)
                     when casco_casco.estado_actual = 'PT' then
                        (select DATE_PART('day', now()-max(dat1.fecha_doc)) as dias
                        from
                        (select casco_doc.fecha_doc 
                        from casco_detallept 
                        inner join casco_produccionterminada on casco_produccionterminada.doc_pt_id = casco_detallept.pt_id
                        inner join casco_doc on casco_produccionterminada.doc_pt_id = casco_doc.id_doc
                        where casco_detallept.casco_id = casco_casco.id_casco
                        union all 
                        select casco_doc.fecha_doc 
                        from casco_detallepte 
                        inner join casco_ptexternos on casco_ptexternos.doc_ptexternos_id = casco_detallepte.doc_pte_id
                        inner join casco_doc on casco_ptexternos.doc_ptexternos_id = casco_doc.id_doc
                        where casco_detallepte.casco_id = casco_casco.id_casco
                        ) as dat1)
                     when casco_casco.estado_actual = 'Transferencia' then
                        (select DATE_PART('day', now()-max(casco_doc.fecha_doc))
                        from casco_detalletransferencia 
                        inner join casco_transferencia on casco_transferencia.doc_transferencia_id = casco_detalletransferencia.transf_id
                        inner join casco_doc on casco_transferencia.doc_transferencia_id = casco_doc.id_doc
                        where casco_detalletransferencia.casco_id = casco_casco.id_casco)
                     when casco_casco.estado_actual = 'DIP' then
                        (select DATE_PART('day', now()-max(casco_doc.fecha_doc))
                        from casco_detalledip 
                        inner join casco_dip on casco_dip.doc_dip_id = casco_detalledip.dip_id
                        inner join casco_doc on casco_dip.doc_dip_id = casco_doc.id_doc
                        where casco_detalledip.casco_id = casco_casco.id_casco)
                     when casco_casco.estado_actual = 'DVP' then
                        (select DATE_PART('day', now()-max(casco_doc.fecha_doc))
                        from casco_detalledvp 
                        inner join casco_dvp on casco_dvp.doc_dvp_id = casco_detalledvp.dvp_id
                        inner join casco_doc on casco_dvp.doc_dvp_id = casco_doc.id_doc
                        where casco_detalledvp.casco_id = casco_casco.id_casco)
                     when casco_casco.estado_actual = 'ER' then
                        (select DATE_PART('day', now()-max(casco_doc.fecha_doc))
                        from casco_detalle_er 
                        inner join casco_errorrecepcion on casco_errorrecepcion.doc_errorrecepcion_id = casco_detalle_er.errro_revision_id
                        inner join casco_doc on casco_errorrecepcion.doc_errorrecepcion_id = casco_doc.id_doc
                        where casco_detalle_er.casco_id = casco_casco.id_casco)
                     when casco_casco.estado_actual = 'ECR' then
                        (select DATE_PART('day', now()-max(casco_doc.fecha_doc))
                        from casco_detalleentregarechazado
                        inner join casco_entregarechazado on casco_entregarechazado.doc_entregarechazado_id = casco_detalleentregarechazado.erechazado_id
                        inner join casco_doc on casco_entregarechazado.doc_entregarechazado_id = casco_doc.id_doc
                        where casco_detalleentregarechazado.casco_id = casco_casco.id_casco)
                    when casco_casco.estado_actual = 'REE' then
                        (select DATE_PART('day', now()-max(casco_doc.fecha_doc))
                        from casco_detallerre
                        inner join casco_receprechaext on casco_receprechaext.doc_receprechaext_id = casco_detallerre.receprechaext_id
                        inner join casco_doc on casco_receprechaext.doc_receprechaext_id = casco_doc.id_doc
                        where casco_detallerre.casco_id = casco_casco.id_casco)
                    when casco_casco.estado_actual = 'REE' then
                        (select DATE_PART('day', now()-max(casco_doc.fecha_doc))
                        from casco_detallerre
                        inner join casco_receprechaext on casco_receprechaext.doc_receprechaext_id = casco_detallerre.receprechaext_id
                        inner join casco_doc on casco_receprechaext.doc_receprechaext_id = casco_doc.id_doc
                        where casco_detallerre.casco_id = casco_casco.id_casco)
                    when casco_casco.estado_actual = 'DC' then
                        (select DATE_PART('day', now()-max(casco_doc.fecha_doc))
                        from casco_detalle_dc
                        inner join casco_cascodecomiso on casco_cascodecomiso.doc_decomiso_id = casco_detalle_dc.doc_decomiso_id
                        inner join casco_doc on casco_cascodecomiso.doc_decomiso_id = casco_doc.id_doc
                        where casco_detalle_dc.casco_id = casco_casco.id_casco)
                     else 0 end as dias,
                     casco_recepcionparticular.recepcionparticular_tipo as tipo
                    FROM
                      casco_casco
                      INNER JOIN admincomerciax_producto ON (casco_casco.producto_salida_id = admincomerciax_producto.id)
                      INNER JOIN admincomerciax_umedida ON (admincomerciax_producto.um_id = admincomerciax_umedida.id)
                      RIGHT OUTER JOIN casco_detallerp ON (casco_casco.id_casco = casco_detallerp.casco_id)
                      LEFT OUTER JOIN casco_recepcionparticular ON (casco_detallerp.rp_id = casco_recepcionparticular.doc_recepcionparticular_id)"""+opt+order)
            resultado=[]
            estado=""
            ccliente=""
            canti_estado=-1
            canti_cliente = -1
            medidagoma=""
            cant_medida=-1
            for datos in resultado1:
                
                if (diasmaxi != 0 and diasmin<=datos['dias']<=diasmaxi) or (diasmaxi == 0 and diasmin<=datos['dias']):
                    cnombre_datos=datos['cliente_nombre'] if datos.has_key('cliente_nombre') else ""
                    cnombre="" if cnombre_datos==None else cnombre_datos
                    pnombre="" if datos['nombre']==None else '**'+datos['nombre']
                    nombre=cnombre+" "+pnombre
                    if datos['producto_descripcion']!=medidagoma:
                        if cant_medida!=-1:
                            resultado=resultado+[{'estado_actual':"", 
                                               'medida': "", 
                                               'casco_nro':"---------------", 
                                               'cliente':"",
                                               'dias': "",
                                               'destino':""}]
                            resultado=resultado+[{'estado_actual':"", 
                                               'medida': "", 
                                               'casco_nro':cant_medida+1, 
                                               'cliente':"",
                                               'dias': "",
                                               'destino':""}]
                        medidagoma=datos['producto_descripcion']
                        cant_medida=0
                    else:
                        cant_medida+=1       
                    if estado!=datos['estado_actual']:
                        puse_cliente = False
                        if canti_estado!=-1:
                            resultado=resultado+[{'estado_actual':"", 
                                               'medida': "", 
                                               'casco_nro':"---------------", 
                                               'cliente':"",
                                               'dias': "",
                                               'destino':""}]
                            if orden != 'Medida':
                                resultado=resultado+[{'estado_actual':"= T O T A L - C L I E N T E =", 
                                               'medida': "", 
                                               'casco_nro':canti_cliente+1, 
                                               'cliente':"",
                                               'dias': "",
                                               'destino':""}]
                                puse_cliente = True
                            resultado=resultado+[{'estado_actual':"= T O T A L - E S T A D O =", 
                                               'medida': "", 
                                               'casco_nro':canti_estado+1, 
                                               'cliente':"",
                                               'dias': "",
                                               'destino':""}]
                        estado1=datos['estado_actual']
                        estado=datos['estado_actual']
                        canti_estado=0
                    else:
                        estado1=""
                        canti_estado+=1
                    if ccliente!=nombre:
                        if canti_cliente!=-1:
                            
                            if not puse_cliente and orden != 'Medida':
                                resultado=resultado+[{'estado_actual':"", 
                                               'medida': "", 
                                               'casco_nro':"---------------", 
                                               'cliente':"",
                                               'dias': "",
                                               'destino':""}]
                                resultado=resultado+[{'estado_actual':"= T O T A L - C L I E N T E =", 
                                                   'medida': "", 
                                                   'casco_nro':canti_cliente+1, 
                                                   'cliente':"",
                                                   'dias': "",
                                                   'destino':""}]
                            puse_cliente = False
                        ccliente1=cnombre+" "+pnombre
                        ccliente=cnombre+" "+pnombre
                        canti_cliente=0
                        
                    else:
                        ccliente1=""   
                        canti_cliente += 1
                    casco_nro_ = str(datos['casco_nro']) if datos['tipo'] == 'O' else str(datos['casco_nro'])+'('+datos['tipo']+')'
                    resultado=resultado+[{'estado_actual':unicode(Estados.estados[estado1],'utf-8')+estadoocioso if Estados.estados.has_key(estado1) else "", 
                                           'medida': datos['producto_descripcion'], 
                                           'casco_nro': casco_nro_+"**" if datos['venta']==True and datos['decomisado']==False else casco_nro_,
                                           'cliente':ccliente1,
                                           'dias': str(int(datos['dias'])) if datos['dias'] != 0 else "", 
                                           'destino':"" if not datos.has_key('destino') else datos['destino']
                                        }]
            
            resultado=resultado+[{'estado_actual':"", 
                                           'medida': "", 
                                           'casco_nro':"---------------", 
                                           'cliente':"",
                                           'dias': "",
                                           'destino':""}]
            resultado=resultado+[{'estado_actual':"", 
                                           'medida':"",
                                           'casco_nro':cant_medida+1, 
                                           'cliente':"",
                                           'dias': "",
                                           'destino':""}]
            
            if orden != 'Medida':
                resultado=resultado+[{'estado_actual':"", 
                                           'medida': "", 
                                           'casco_nro':"---------------", 
                                           'cliente':"",
                                           'dias': "",
                                           'destino':""}]
                resultado=resultado+[{'estado_actual':"= T O T A L - C L I E N T E =", 
                               'medida': "", 
                               'casco_nro':canti_cliente+1, 
                               'cliente':"",
                               'dias': "",
                               'destino':""}]
                
            resultado=resultado+[{'estado_actual':"= T O T A L - E S T A D O =", 
                               'medida': "", 
                               'casco_nro':canti_estado+1, 
                               'cliente':"",
                               'dias': "",
                               'destino':""}]
            if request.POST.__contains__('submit1') or request.POST.__contains__('submit2'):  
                    
                if resultado.__len__():                        
                    pdf_file_name=os.path.join(comerciax.settings.ADMIN_MEDIA_PDF,"Cascos por Estado.pdf")
                    tipo="cascos_est"
                    if medida in ['Transferencia','G']:
                        tipo="cascos_estTransf"
                    if report_class.Reportes.GenerarRep(report_class.Reportes() , resultado, tipo,pdf_file_name,filtro)==0:
                        mesg.append('Debe cerrar el fichero Cascos por Estado.pdf')
                        return render_to_response("comercial/reporteindex.html",{'filtro':filtro,'resultado':resultado,'form':form,'title':titulo_form, 'form_name':nombre_form,'form_description':descripcion_form,
                                                        'controlador':controlador_form,'accion':accion_form,'error2':mesg},context_instance = RequestContext(request))
                    else:
                        input = PdfFileReader(file(pdf_file_name,"rb"))
                        output = PdfFileWriter()
                        for page in input.pages:
                            output.addPage(page)
                        buffer = StringIO.StringIO()
                        output.write(buffer)
                        response = HttpResponse(mimetype='application/pdf')
                        file_namesitio='%s'%(pdf_file_name)
                        response['Content-Disposition'] = 'attachment; filename=%s'%(pdf_file_name)
                        response.write(buffer.getvalue())
                        #AQUIIIII EMAIL
                        if envia:
                            import smtplib
                            from email.mime.application import MIMEApplication
                            from django.core.mail.message import EmailMessage
                            try:
                                message = EmailMessage(subject='Cascos por Estado',body='Enviado por '+request.user.first_name+' '+request.user.last_name, from_email=correo_envia, to=[correo])
                                part = MIMEApplication(open(file_namesitio,"rb").read())
                                part.add_header('Content-Disposition', 'attachment', filename="Cascos por Estado.pdf")
                                message.attach(part)
                                if ssl==True:
                                    smtp = smtplib.SMTP_SSL(host=servidor,port=puerto)
                                else:
                                    smtp = smtplib.SMTP(servidor)
                                smtp.ehlo()
                                smtp.login(correo_envia,contrasena)
                                smtp.sendmail(correo_envia,[correo],message.message().as_string())
                                smtp.close()
                                return response
                            except Exception, e:
                                mesg=mesg+['Error de conexión. Revise la configuración del Correo SMTP']
                                return render_to_response("comercial/reporteindex.html",{'filtro':filtro,'resultado':resultado,
                                                                                         'form':form,'title':titulo_form, 
                                                                                         'form_name':nombre_form,'form_description':descripcion_form,
                                                        'controlador':controlador_form,'accion':accion_form,'error2':mesg},context_instance = RequestContext(request))
                                
                    return response
                else:
                    mesg=mesg+['No existe información para mostrar']
                    return render_to_response("comercial/reporteindex.html",{'filtro':filtro,'resultado':resultado,'form':form,'title':titulo_form, 'form_name':nombre_form,'form_description':descripcion_form,
                                                        'controlador':controlador_form,'accion':accion_form,'error2':mesg},context_instance = RequestContext(request))
                           
            else:
                if resultado.__len__()==0:
                    mesg=mesg+['No existe información para mostrar']
                    return render_to_response("comercial/reporteindex.html",{'form':form,'title':titulo_form, 'form_name':nombre_form,'form_description':descripcion_form,
                                                                    'controlador':controlador_form,'accion':accion_form,'error2':mesg},context_instance = RequestContext(request))
                
                destino=0
                if medida in ['Transferencia','G']: 
                    destino = 1
                return render_to_response("report/cascos_estado.html",{'destino':destino,'filtro':filtro,
                                                                       'hayfiltro':filtro.__len__(),
                                                                       'order': orden,
                                                                       'fecha_hoy':fecha_hoy(),
                                                                       'resultado':resultado,'error2':mesg},context_instance = RequestContext(request))
        
    form = Rep_CascosEstado() 
    
    return render_to_response("comercial/reporteindex.html",{'form':form,'title':titulo_form, 'form_name':nombre_form,'form_description':descripcion_form,
                                                                'controlador':controlador_form,'accion':accion_form,'error2':mesg,'email':1},context_instance = RequestContext(request))
      

@login_required
def transfenviadas(request):
    
    nombre_form='Reportes'
    descripcion_form='Transferencias Enviadas'
    titulo_form='Transferencias Enviadas' 
    controlador_form='Reportes'
    accion_form='/comerciax/comercial/transfenviadas/reporte'
    mesg=[]
    
    if request.method == 'POST':
        form = TransfEnviadas(request.POST)
        
        if form.is_valid():
            pdf=False
            if request.POST.__contains__('submit1') or request.POST.__contains__('submit2'):
                pdf=True
            envia=False
            clientetransf=form.cleaned_data['clientetransf']
            if request.POST.__contains__('submit2'):
                envia=True
                
                if clientetransf==None:
                    mesg=mesg+['Debe seleccionar un cliente']
                    return render_to_response("comercial/reporteindex.html",{'form':form,'title':titulo_form, 'form_name':nombre_form,'form_description':descripcion_form,
                                                                    'controlador':controlador_form,'accion':accion_form,'error2':mesg,'email':1},context_instance = RequestContext(request))
                correo=clientetransf.email
                if correo.__len__()==0:
                    mesg=mesg+['Este cliente no tiene correo']
                    return render_to_response("comercial/reporteindex.html",{'form':form,'title':titulo_form, 'form_name':nombre_form,'form_description':descripcion_form,
                                                                   'controlador':controlador_form,'accion':accion_form,'error2':mesg,'email':1},context_instance = RequestContext(request))
                try:
                    querySet = Config_SMTPEmail.objects.get()
                except Exception, e:
                    mesg=mesg+['No está configurado el correo SMTP']
                    return render_to_response("comercial/reporteindex.html",{'form':form,'title':titulo_form, 'form_name':nombre_form,'form_description':descripcion_form,
                                                                   'controlador':controlador_form,'accion':accion_form,'error2':mesg,'email':1},context_instance = RequestContext(request))
                servidor=querySet.servidor
                correo_envia=querySet.correo
                puerto = querySet.puerto
                ssl = querySet.ssl
                try:
                    contrasena = base64.b64decode(querySet.contrasena)
                except Exception, e:
                    mesg=mesg+['Revise la contraseña en la configuración del Correo SMTP']
                    return render_to_response("comercial/reporteindex.html",{'form':form,'title':titulo_form, 'form_name':nombre_form,'form_description':descripcion_form,
                                                                   'controlador':controlador_form,'accion':accion_form,'error2':mesg,'email':1},context_instance = RequestContext(request))
            filtro=[]
            where=[]
            where.append("casco_doc.tipo_doc='6'")
            
            desde  = form.cleaned_data['desde']
            hasta  = form.cleaned_data['hasta']
            where.append("casco_doc.fecha_doc >='"+desde.strftime("%d/%m/%Y")+"'")
            where.append("casco_doc.fecha_doc <='"+hasta.strftime("%d/%m/%Y")+"'")
            medida=form.data['medida']
            
#            resultado=Casco.objects.select_related().all().order_by('estado_actual','admincomerciax_producto.descripcion')
            if clientetransf!=None:
                where.append("admincomerciax_cliente.id='"+clientetransf.id+"'")
                filtro.append('Transferencias hacia : '+clientetransf.nombre)
            filtro.append('Desde:'+desde.strftime("%d/%m/%Y")+"  Hasta:"+hasta.strftime("%d/%m/%Y"))
            
            if medida.__len__()!=0:
                filtro.append('Medida: '+Producto.objects.get(pk=medida).descripcion)
                where.append("admincomerciax_producto.id='"+medida+"'")
                    
            optwhere=" where " if len(where)>0 else ""               
            for a1 in range(len(where)):
                optwhere+= where[a1]+ " AND "
            opt=str(optwhere[0:len(optwhere)-4])
            
            resultado1 = query_to_dicts("""
                            select uno_1.nombre, uno_1.descripcion, cast(sum(uno_1.tota)as integer) as total, 
                                cast(sum(uno_1.transf) as integer) as transferencia,
                                cast(sum(uno_1.transfrechaz) as integer) as transfrechaz,
                                cast(sum(uno_1.transfproce) as integer) as transfproce,uno_1.medida_id
                                from
                                    (select uno.nombre, uno.descripcion, sum(uno.canti) as tota,
                                      case 
                                          when (uno.estado='Transferencia') then (sum(uno.canti)) else 0
                                      end as transf,
                                      case 
                                          when (uno.estado='REE') then (sum(uno.canti)) else 0
                                      end as transfrechaz,
                                      case 
                                          when (uno.estado='PT') then (sum(uno.canti)) else 0
                                      end as transfproce,
                                      uno.medida_id
                                      
                                     from 
                                    (SELECT 
                                      admincomerciax_cliente.nombre, 
                                      admincomerciax_producto.descripcion,
                                      admincomerciax_producto.id as medida_id,
                                      case 
                                          when (casco_casco.estado_actual='Transferencia') then ('Transferencia') 
                                          when (casco_casco.estado_actual='REE') then ('REE')
                                          when (casco_casco.estado_actual='PT') then ('PT') 
                                          else ('Otro')
                                      end as estado,
                                      count(casco_casco.estado_actual) as canti
                                    FROM 
                                      public.casco_doc
                                    inner join public.casco_transferencia on casco_transferencia.doc_transferencia_id = casco_doc.id_doc 
                                    inner join public.admincomerciax_cliente on casco_transferencia.destino_id = admincomerciax_cliente.id 
                                    inner join public.casco_detalletransferencia on casco_detalletransferencia.transf_id = casco_transferencia.doc_transferencia_id
                                    inner join casco_casco on casco_detalletransferencia.casco_id = casco_casco.id_casco
                                    inner join admincomerciax_producto on casco_casco.producto_id = admincomerciax_producto.id
                                    """+opt+""" 
                                    group by admincomerciax_cliente.nombre,admincomerciax_producto.descripcion, casco_casco.estado_actual,
                                    estado,admincomerciax_producto.id
                                    order by admincomerciax_cliente.nombre,admincomerciax_producto.descripcion) as uno
                                    group by uno.nombre,uno.descripcion, uno.estado,uno.medida_id
                                    order by uno.nombre,uno.descripcion) as uno_1
                                    group by uno_1.nombre,uno_1.descripcion,uno_1.medida_id
                                    order by uno_1.nombre,uno_1.descripcion
                        """)

            resultado=[]
            ccliente=""
            canti_transf=0
            canti_dev=0
            canti_pend=0
            canti_proc=0
            canti_inserv=0
            totalcanti_transf=0
            totalcanti_dev=0
            totalcanti_pend=0
            totalcanti_proc=0
            totalcanti_inserv=0
            for datos in resultado1:
                cnombre_datos=datos['nombre'] if datos.has_key('nombre') else ""
                nombre="" if cnombre_datos==None else cnombre_datos
                if ccliente!=nombre:
                    if ccliente!="":
                        if not pdf:
                            resultado=resultado+[{'cliente':"= T O T A L =", 
                                               'medida': "", 
                                               'transferidas':canti_transf, 
                                               'procesadas':canti_proc,
                                               'noprocesadas':canti_dev,
                                               'inservibles':canti_inserv,
                                               'pendientes':canti_pend}]
                        ccliente=datos['nombre']
                        totalcanti_transf+=canti_transf
                        totalcanti_dev+=canti_dev
                        totalcanti_pend+=canti_pend
                        totalcanti_proc+=canti_proc
                        totalcanti_inserv+=canti_inserv
                        canti_transf=0
                        canti_dev=0
                        canti_pend=0
                        canti_proc=0
                        canti_inserv=0
                    resultado=resultado+[{'cliente':datos['nombre'], 
                                           'medida': datos['descripcion'], 
                                           'transferidas':datos['total'], 
                                           'procesadas':datos['transfproce'],
                                           'noprocesadas':datos['total']-(datos['transfproce']+datos['transfrechaz']+datos['transferencia']),
                                           'inservibles':datos['transfrechaz'],
                                           'pendientes':datos['transferencia']}]
                    canti_transf+=datos['total']
                    canti_dev+=datos['total']-(datos['transfproce']+datos['transfrechaz']+datos['transferencia'])
                    canti_pend+=datos['transferencia']
                    canti_proc+=datos['transfproce']
                    canti_inserv+=datos['transfrechaz']
                else:
                    resultado=resultado+[{'cliente':"" if not pdf else datos['nombre'], 
                                           'medida': datos['descripcion'], 
                                           'transferidas':datos['total'], 
                                           'procesadas':datos['transfproce'],''
                                           'noprocesadas':datos['total']-(datos['transfproce']+datos['transfrechaz']+datos['transferencia']),
                                           'inservibles':datos['transfrechaz'],
                                           'pendientes':datos['transferencia']}]
                    canti_transf+=datos['total']
                    canti_dev+=datos['total']-(datos['transfproce']+datos['transfrechaz']+datos['transferencia'])
                    canti_pend+=datos['transferencia']
                    canti_proc+=datos['transfproce']
                    canti_inserv+=datos['transfrechaz']
                if ccliente!=nombre:
                    ccliente=nombre
            if not pdf:
                resultado=resultado+[{'cliente':"= T O T A L =", 
                                               'medida': "", 
                                               'transferidas':canti_transf, 
                                               'procesadas':canti_proc,
                                               'noprocesadas':canti_transf-(canti_proc+canti_inserv+canti_pend),
                                               'inservibles':canti_inserv,
                                               'pendientes':canti_pend}]
                resultado=resultado+[{'cliente':"= T O T A L =", 
                                               'medida': "", 
                                               'transferidas':totalcanti_transf+canti_transf, 
                                               'procesadas':totalcanti_proc+canti_proc,
                                               'noprocesadas':(totalcanti_transf-(totalcanti_proc+totalcanti_inserv+totalcanti_pend))+canti_dev,
                                               'inservibles':totalcanti_inserv+canti_inserv,
                                               'pendientes':totalcanti_pend+canti_pend
                                               }]
            if pdf:  
                if resultado.__len__():                        
                    pdf_file_name=os.path.join(comerciax.settings.ADMIN_MEDIA_PDF,"TransfEnviadas.pdf")
                    if report_class.Reportes.GenerarRep(report_class.Reportes() , resultado, "transf_env",pdf_file_name,filtro)==0:
                        mesg.append('Debe cerrar el fichero TransfEnviadas.pdf')
                        return render_to_response("comercial/reporteindex.html",{'filtro':filtro,'resultado':resultado,'form':form,'title':titulo_form, 'form_name':nombre_form,'form_description':descripcion_form,
                                                        'controlador':controlador_form,'accion':accion_form,'error2':mesg,'email':1},context_instance = RequestContext(request))
                    else:
                        input = PdfFileReader(file(pdf_file_name,"rb"))
                        output = PdfFileWriter()
                        for page in input.pages:
                            output.addPage(page)
                        buffer = StringIO.StringIO()
                        output.write(buffer)
                        response = HttpResponse(mimetype='application/pdf')
                        file_namesitio='%s'%(pdf_file_name)
                        response['Content-Disposition'] = 'attachment; filename=%s'%(pdf_file_name)
                        response.write(buffer.getvalue())
                        #AQUIIIII EMAIL
                        if envia:
                            import smtplib
                            from email.mime.application import MIMEApplication
                            from django.core.mail.message import EmailMessage
                            try:
                                message = EmailMessage(subject='Transferencias Enviadas',body='Enviado por '+request.user.first_name+' '+request.user.last_name, from_email=correo_envia, to=[correo])
                                part = MIMEApplication(open(file_namesitio,"rb").read())
                                part.add_header('Content-Disposition', 'attachment', filename="TransfEnviadas.pdf")
                                message.attach(part)
                                if ssl==True:
                                    smtp = smtplib.SMTP_SSL(host=servidor,port=puerto)
                                else:
                                    smtp = smtplib.SMTP(servidor)
                                smtp.ehlo()
                                smtp.login(correo_envia,contrasena)
                                smtp.sendmail(correo_envia,[correo],message.message().as_string())
                                smtp.close()
                                return response
                            except Exception, e:
                                mesg=mesg+['Error de conexión. Revise la configuración del Correo SMTP']
                                return render_to_response("comercial/reporteindex.html",{'filtro':filtro,'resultado':resultado,'form':form,'title':titulo_form, 'form_name':nombre_form,'form_description':descripcion_form,
                                                        'controlador':controlador_form,'accion':accion_form,'error2':mesg,'email':1},context_instance = RequestContext(request))
                    return response
                else:
                    mesg=mesg+['No existe información para mostrar']
                    return render_to_response("comercial/reporteindex.html",{'filtro':filtro,'resultado':resultado,'form':form,'title':titulo_form, 'form_name':nombre_form,'form_description':descripcion_form,
                                                        'controlador':controlador_form,'accion':accion_form,'error2':mesg,'email':1},context_instance = RequestContext(request))
                       
            else:
                if resultado.__len__()==0:
                    mesg=mesg+['No existe información para mostrar']
                    return render_to_response("comercial/reporteindex.html",{'form':form,'title':titulo_form, 'form_name':nombre_form,'form_description':descripcion_form,
                                                                    'controlador':controlador_form,'accion':accion_form,'error2':mesg,'email':1},context_instance = RequestContext(request))
                
                    
                return render_to_response("report/transfenviadas.html",{'filtro':filtro,'fecha_hoy':fecha_hoy(),'resultado':resultado,'error2':mesg},context_instance = RequestContext(request))
        
    form = TransfEnviadas() 
    return render_to_response("comercial/reporteindex.html",{'form':form,'title':titulo_form, 'form_name':nombre_form,'form_description':descripcion_form,
                                                                'controlador':controlador_form,'accion':accion_form,'error2':mesg,'email':1},context_instance = RequestContext(request))
      

@login_required
def factcliente(request):
    nombre_form='Reportes'
    descripcion_form='Facturas x Clientes'
    titulo_form='Facturas x Clientes' 
    controlador_form='Reportes'
    accion_form='/comerciax/comercial/factcliente/reporte'
    mesg=[]
    
    if request.method == 'POST':
        form = Rep_FacturaCliente(request.POST)
        
        if form.is_valid():
            
            envia=False
            if request.POST.__contains__('submit2'):
                envia=True
                cliente=form.cleaned_data['ccliente']
                if cliente==None:
                    mesg=mesg+['Debe seleccionar un cliente']
                    return render_to_response("comercial/reporteindex.html",{'form':form,'title':titulo_form, 'form_name':nombre_form,'form_description':descripcion_form,
                                                                    'controlador':controlador_form,'accion':accion_form,'error2':mesg,'email':1},context_instance = RequestContext(request))
                correo=cliente.email
                if correo.__len__()==0:
                    mesg=mesg+['Este cliente no tiene correo']
                    return render_to_response("comercial/reporteindex.html",{'form':form,'title':titulo_form, 'form_name':nombre_form,'form_description':descripcion_form,
                                                                   'controlador':controlador_form,'accion':accion_form,'error2':mesg,'email':1},context_instance = RequestContext(request))
                try:
                    querySet = Config_SMTPEmail.objects.get()
                except Exception, e:
                    mesg=mesg+['No está configurado el correo SMTP']
                    return render_to_response("comercial/reporteindex.html",{'form':form,'title':titulo_form, 'form_name':nombre_form,'form_description':descripcion_form,
                                                                   'controlador':controlador_form,'accion':accion_form,'error2':mesg,'email':1},context_instance = RequestContext(request))
                servidor=querySet.servidor
                correo_envia=querySet.correo
                puerto = querySet.puerto
                ssl = querySet.ssl
                try:
                    contrasena = base64.b64decode(querySet.contrasena)
                except Exception, e:
                    mesg=mesg+['Revise la contraseña en la configuración del Correo SMTP']
                    return render_to_response("comercial/reporteindex.html",{'form':form,'title':titulo_form, 'form_name':nombre_form,'form_description':descripcion_form,
                                                                   'controlador':controlador_form,'accion':accion_form,'error2':mesg,'email':1},context_instance = RequestContext(request))
                    
            organismo=form.cleaned_data['organismo']
            provincia=form.cleaned_data['provincia']
            cliente=form.cleaned_data['ccliente']
            desde=form.cleaned_data['fecha_desde']
            hasta=form.cleaned_data['fecha_hasta']
            filtro=[]
            queryset=[]
            resultado=Facturas.objects.select_related().filter(doc_factura__fecha_doc__gte=desde,doc_factura__fecha_doc__lte=hasta,confirmar=True).order_by('cancelada', 'cliente__nombre')
            filtro.append('Facturas emitidas entre el '+desde.strftime("%d/%m/%Y")+' y el '+hasta.strftime("%d/%m/%Y"))
            if organismo!=None and resultado.__len__()!=0:
                filtro.append('Organimso: '+organismo.siglas_organismo)
#                filtro.append('Facturas emitidas entre el '+desde.strftime("%d/%m/%Y")+' y el '+hasta.strftime("%d/%m/%Y"))
#                resultado=Facturas.objects.select_related().filter(cliente=cliente,doc_factura__fecha_doc__gte=desde,doc_factura__fecha_doc__lte=hasta).order_by('factura_nro')
                resultado=resultado.filter(cliente__organismo=organismo)
            if provincia!=None and resultado.__len__()!=0:
                filtro.append('Provincia: '+provincia.descripcion_provincia)
#                filtro.append('Facturas emitidas entre el '+desde.strftime("%d/%m/%Y")+' y el '+hasta.strftime("%d/%m/%Y"))
#                resultado=Facturas.objects.select_related().filter(cliente=cliente,doc_factura__fecha_doc__gte=desde,doc_factura__fecha_doc__lte=hasta).order_by('factura_nro')
                resultado=resultado.filter(cliente__provincia=provincia)    
            if cliente!=None and resultado.__len__()!=0:
#                filtro.append('Facturas emitidas entre el '+desde.strftime("%d/%m/%Y")+' y el '+hasta.strftime("%d/%m/%Y"))
#                resultado=Facturas.objects.select_related().filter(doc_factura__fecha_doc__gte=desde,doc_factura__fecha_doc__lte=hasta,confirmar=True).order_by('admincomerciax_cliente.nombre','factura_nro')
#            else:
                filtro.append('Cliente: '+cliente.nombre)
#                filtro.append('Facturas emitidas entre el '+desde.strftime("%d/%m/%Y")+' y el '+hasta.strftime("%d/%m/%Y"))
#                resultado=Facturas.objects.select_related().filter(cliente=cliente,doc_factura__fecha_doc__gte=desde,doc_factura__fecha_doc__lte=hasta).order_by('factura_nro')
                resultado=resultado.filter(cliente=cliente)
            
            if resultado.__len__()==0:                              
                mesg=mesg+['No existe información para mostrar']
                return render_to_response("comercial/reporteindex.html",{'form':form,'title':titulo_form, 'form_name':nombre_form,'form_description':descripcion_form,
                                                                'controlador':controlador_form,'accion':accion_form,'error2':mesg,'email':1},context_instance = RequestContext(request))
            else:
                sumas = DetalleFactura.objects.filter(factura__confirmar=True, factura__doc_factura__fecha_doc__gte=desde,
                                              factura__doc_factura__fecha_doc__lte=hasta,
                                              factura__cancelada=False).aggregate(Sum('precio_mn'), Sum('precio_cuc'), Sum('precio_casco'))
                total_cuc = '$'+'{:20,.2f}'.format(sumas['precio_cuc__sum'])
                total_mn = '$'+'{:20,.2f}'.format(sumas['precio_mn__sum']+sumas['precio_casco__sum'])

                resultado=resultado.order_by('cancelada','admincomerciax_cliente.nombre','factura_nro')
                if not request.POST.__contains__('submit1') and not request.POST.__contains__('submit2'):
                    return render_to_response("report/facturas_clientes.html",{'filtro':filtro,'fecha_hoy':fecha_hoy(),
                                                                               'resultado':resultado,'error2':mesg,'email':1,
                                                                               'total_mn':total_mn,
                                                                               'total_cuc':total_cuc},context_instance = RequestContext(request))
                else:
                    esta=0
                    if cliente!=None:
                        esta=1
                    for fila in resultado:
                        queryset.append({'nombre':fila.cliente.nombre,'codigo':fila.cliente.codigo ,'factura_nro':str(fila.factura_nro),
                                      'fecha_doc':fila.doc_factura.fecha_doc,
                                      'importetotalcup':fila.get_importetotalcup(1) if not fila.cancelada else 0.00,
                                      'importecuc':fila.get_importecuc(1) if not fila.cancelada else 0.00,
                                         'cancelada':'No' if fila.cancelada==False else 'Si'
                                      })  
                    pdf_file_name=os.path.join(comerciax.settings.ADMIN_MEDIA_PDF,"Facturas por Cliente.pdf")
                    if esta==0:
                        repo = report_class.Reportes.GenerarRep(report_class.Reportes() , queryset, "fac_cliente",pdf_file_name,filtro)
                    else:
                        repo=report_class.Reportes.GenerarRep(report_class.Reportes() , queryset, "fac_uncliente",pdf_file_name,filtro)
                        
                    if repo == 0:
                        mesg=mesg+['Debe cerrar el documento Facturas por Cliente.pdf']
                        return render_to_response("comercial/reporteindex.html",{'filtro':filtro,'resultado':resultado,'form':form,'title':titulo_form, 'form_name':nombre_form,'form_description':descripcion_form,
                                                        'controlador':controlador_form,'accion':accion_form,'error2':mesg,'email':1},context_instance = RequestContext(request))
                    else:
                        if request.POST.__contains__('submit2'):
                            envia=True
                            
                        input = PdfFileReader(file(pdf_file_name,"rb"))
                        output = PdfFileWriter()
                        for page in input.pages:
                            output.addPage(page)
                        buffer = StringIO.StringIO()
                        output.write(buffer)
                        response = HttpResponse(mimetype='application/pdf')
                        file_namesitio='%s'%(pdf_file_name)
                        response['Content-Disposition'] = 'attachment; filename=%s'%(pdf_file_name)
                        response.write(buffer.getvalue())
                        if envia:
                            import smtplib
                            from email.mime.application import MIMEApplication
                            from django.core.mail.message import EmailMessage
                            try:
                                message = EmailMessage(subject='Facturas por Cliente',body='Enviado por '+request.user.first_name+' '+request.user.last_name, from_email=correo_envia, to=[correo])
                                part = MIMEApplication(open(file_namesitio,"rb").read())
                                part.add_header('Content-Disposition', 'attachment', filename="Facturas por Cliente.pdf")
                                message.attach(part)
                                if ssl==True:
                                    smtp = smtplib.SMTP_SSL(host=servidor,port=puerto)
                                else:
                                    smtp = smtplib.SMTP(servidor)
                                smtp.ehlo()
                                smtp.login(correo_envia,contrasena)
                                smtp.sendmail(correo_envia,[correo],message.message().as_string())
                                smtp.close()
                                return response     
                            except Exception, e:
                                mesg=mesg+['Error de conexión. Revise la configuración del Correo SMTP']
                                return render_to_response("comercial/reporteindex.html",{'filtro':filtro,'resultado':resultado,'form':form,'title':titulo_form, 'form_name':nombre_form,'form_description':descripcion_form,
                                                        'controlador':controlador_form,'accion':accion_form,'error2':mesg},context_instance = RequestContext(request))
                        return response         
            
    form = Rep_FacturaCliente() 
    
    return render_to_response("comercial/reporteindex.html",{'form':form,'title':titulo_form, 'form_name':nombre_form,'form_description':descripcion_form,
                                                                'controlador':controlador_form,'accion':accion_form,'error2':mesg,'email':1},context_instance = RequestContext(request))

@login_required
def regfacturas(request):
     
    nombre_form='Reportes'
    descripcion_form='Registro de Facturas'
    titulo_form='Registro de Facturas' 
    controlador_form='Reportes'
    accion_form='/comerciax/comercial/regfacturas/reporte'
    mesg=[]
    
    if request.method == 'POST':
        form = Rep_RegFacturas(request.POST)
        
        if form.is_valid():
            desde=form.cleaned_data['fecha_desde']
            hasta=form.cleaned_data['fecha_hasta']
            filtro=[]
            queryset=[]
            filtro.append('Facturas emitidas entre el '+desde.strftime("%d/%m/%Y")+' y el '+hasta.strftime("%d/%m/%Y"))
            resultado=Facturas.objects.select_related().filter(doc_factura__fecha_doc__gte=desde,doc_factura__fecha_doc__lte=hasta,confirmar=True).order_by('factura_nro')
#            resultado_externo=Facturas.objects.select_related().filter(doc_factura__fecha_doc__gte=desde,doc_factura__fecha_doc__lte=hasta,cliente__externo=True,confirmar=True).order_by('factura_nro')
            resultado_particulares=FacturasParticular.objects.select_related().filter(doc_factura__fecha_doc__gte=desde,doc_factura__fecha_doc__lte=hasta,confirmar=True).order_by('factura_nro')
            resultado = resultado.order_by('factura_nro')
            if resultado.__len__()==0 and resultado_particulares==0:                              
                mesg=mesg+['No existe información para mostrar']
                return render_to_response("comercial/reporteindex.html",{'form':form,'title':titulo_form, 'form_name':nombre_form,'form_description':descripcion_form,
                                                                'controlador':controlador_form,'accion':accion_form,'error2':mesg},context_instance = RequestContext(request))
            else:
                total_importecuc1=0
                total_importecup1=0
                total_cascocliente=0
                for k in range(resultado.__len__()):
                    if resultado[k].get_confirmada() == 'S':
                        val_cup = Decimal('0.00') if resultado[k].cancelada==True or resultado[k].tipo=='A' else resultado[k].get_importetotalcup(1)
                        val_cuc = Decimal('0.00') if resultado[k].cancelada==True or resultado[k].tipo=='A' else resultado[k].get_importecuc(1)
                        queryset.append({'nombre':resultado[k].cliente.nombre,
                                         'tipo':'Clientes',
                                         'codigo':resultado[k].cliente.codigo ,
                                         'factura_nro':str(resultado[k].factura_nro),
                                      'fecha_doc':resultado[k].get_fecha(),
                                      'cascos': resultado[k].cantidad_casco() if not resultado[k].cancelada and resultado[k].tipo!='A' else 0,
                                      'importetotalcup':val_cup, #if resultado[k].tipo!='A' else '0.00',
                                      'importecuc':val_cuc, #if not resultado[k].cancelada and resultado[k].tipo!='A' else '0.00',
                                      'cancelada':'Cancelada' if resultado[k].cancelada==True else 'Ajuste' if resultado[k].tipo=='A' else ''
                                      })
                    if resultado[k].cancelada == False and resultado[k].tipo!='A':
                        total_cascocliente+=resultado[k].cantidad_casco()
                        total_importecup1+=resultado[k].get_importetotalcup(1)
                        total_importecuc1+=resultado[k].get_importecuc(1)
                        
                valor_cliente=total_importecup1+total_importecuc1
                total_importecup3=0
                total_importecuc3=0
                total_cascopart=0
                resultado_particulares = resultado_particulares.order_by('cancelada', 'factura_nro')
                for k in range(resultado_particulares.__len__()):
                    if resultado_particulares[k].get_confirmada() == 'S':
                        val_cup = Decimal('0.00') if resultado_particulares[k].cancelada == True or resultado_particulares[k].tipo == 'A' else \
                        resultado_particulares[k].get_importe_total_value(1)

                        queryset.append({'nombre':resultado_particulares[k].nombre,
                                         'tipo':'Particulares',
                                         'codigo':resultado_particulares[k].ci,
                                         'factura_nro':str(resultado_particulares[k].factura_nro),
                                      'fecha_doc':resultado_particulares[k].get_fecha(),
                                      'cascos': 0 if resultado_particulares[k].cancelada == True or resultado_particulares[k].tipo == 'A' else resultado_particulares[k].cantidad_casco(),
                                      'importetotalcup':val_cup,
                                      'importecuc':Decimal('0.00'),
                                      'cancelada':'Cancelada' if resultado_particulares[k].cancelada==True else 'Ajuste' if resultado_particulares[k].tipo=='A' else ''
                                      })

                    if resultado_particulares[k].cancelada == False and resultado_particulares[k].tipo!='A':
                        total_cascopart+=resultado_particulares[k].cantidad_casco()
                        total_importecup3+=float(resultado_particulares[k].get_importe_total().replace(' ','').replace('$','').replace(',',''))

                total_cup= float(total_importecup1)+float(total_importecup3)
                total_cuc= total_importecuc1+total_importecuc3 
                total_cascototal=total_cascopart+total_cascocliente
                
                total_cascototal='{:20,.0f}'.format(total_cascototal)
                total_cascopart='{:20,.0f}'.format(total_cascopart)
                total_cascocliente='{:20,.0f}'.format(total_cascocliente)
                
                total_importecup1=0 if total_importecup1==0 else'{:20,.2f}'.format(total_importecup1)
                total_importecup3=0 if total_importecup3==0 else'{:20,.2f}'.format(total_importecup3)
                
                total_importecuc1=0 if total_importecuc1==0 else'{:20,.2f}'.format(total_importecuc1)
                total_importecuc3=0 if total_importecuc3==0 else'{:20,.2f}'.format(total_importecuc3)                   
                if not request.POST.__contains__('submit1'):
                    return render_to_response("report/registro_facturas.html",{'filtro':filtro,'fecha_hoy':fecha_hoy(),\
                                                                               'resultado':resultado,'resultado_particulares':resultado_particulares,\
                                                                               'total_importecup1':total_importecup1,'total_importecup3':total_importecup3,\
                                                                               'total_importecuc1':total_importecuc1,'total_importecuc3':total_importecuc3,\
                                                                               'total_cup':'{:20,.2f}'.format(total_cup),'total_cuc':'{:20,.2f}'.format(total_cuc),\
                                                                               'valor_cliente':valor_cliente,\
                                                                               'total_cascototal':total_cascototal,\
                                                                               'total_cascopart':total_cascopart,\
                                                                               'total_cascocliente':total_cascocliente,\
                                                                               'error2':mesg},context_instance = RequestContext(request))
        
                else:
                    pdf_file_name=os.path.join(comerciax.settings.ADMIN_MEDIA_PDF,"Registro de Facturas.pdf")
                    if report_class.Reportes.GenerarRep(report_class.Reportes(), queryset, "registro_fac",pdf_file_name,filtro)==0:
                        mesg=mesg+['Debe cerrar el documento Registro de Facturas.pdf']
                        return render_to_response("comercial/reporteindex.html",{'filtro':filtro,'resultado':resultado_particulares,'form':form,'title':titulo_form, 'form_name':nombre_form,'form_description':descripcion_form,
                                                        'controlador':controlador_form,'accion':accion_form,'error2':mesg},context_instance = RequestContext(request))
                    else:
                        input = PdfFileReader(file(pdf_file_name,"rb"))
                        output = PdfFileWriter()
                        for page in input.pages:
                            output.addPage(page)
                        buffer = StringIO.StringIO()
                        output.write(buffer)
                        response = HttpResponse(mimetype='application/pdf')
                        response['Content-Disposition'] = 'attachment; filename=%s'%(pdf_file_name)
                        response.write(buffer.getvalue())
                        return response         
            
    form = Rep_RegFacturas() 
    
    return render_to_response("comercial/reporteindex.html",{'form':form,'title':titulo_form, 'form_name':nombre_form,'form_description':descripcion_form,
                                                                'controlador':controlador_form,'accion':accion_form,'error2':mesg},context_instance = RequestContext(request))


@login_required
def factcobrar(request):
    
    nombre_form='Reportes'
    descripcion_form='Facturas x Cobrar'
    titulo_form='Facturas x Cobrar' 
    controlador_form='Reportes'
    accion_form=''
    mesg=[]
    
    mesg=[]
    if request.method == 'POST':
        form = Rep_FacturaCobrar(request.POST)
        
        if form.is_valid():
            
            envia=False
            if request.POST.__contains__('submit2'):
                envia=True
                cliente=form.cleaned_data['ccliente']
                if cliente==None:
                    mesg=mesg+['Debe seleccionar un cliente']
                    return render_to_response("comercial/reporteindex.html",{'form':form,'title':titulo_form, 'form_name':nombre_form,'form_description':descripcion_form,
                                                                    'controlador':controlador_form,'accion':accion_form,'error2':mesg,'email':1},context_instance = RequestContext(request))
                correo=cliente.email
                if correo.__len__()==0:
                    mesg=mesg+['Este cliente no tiene correo']
                    return render_to_response("comercial/reporteindex.html",{'form':form,'title':titulo_form, 'form_name':nombre_form,'form_description':descripcion_form,
                                                                   'controlador':controlador_form,'accion':accion_form,'error2':mesg,'email':1},context_instance = RequestContext(request))
                try:
                    querySet = Config_SMTPEmail.objects.get()
                except Exception, e:
                    mesg=mesg+['No está configurado el correo SMTP']
                    return render_to_response("comercial/reporteindex.html",{'form':form,'title':titulo_form, 'form_name':nombre_form,'form_description':descripcion_form,
                                                                   'controlador':controlador_form,'accion':accion_form,'error2':mesg,'email':1},context_instance = RequestContext(request))
                servidor=querySet.servidor
                correo_envia=querySet.correo
                puerto = querySet.puerto
                ssl = querySet.ssl
                try:
                    contrasena = base64.b64decode(querySet.contrasena)
                except Exception, e:
                    mesg=mesg+['Revise la contraseña en la configuración del Correo SMTP']
                    return render_to_response("comercial/reporteindex.html",{'form':form,'title':titulo_form, 'form_name':nombre_form,'form_description':descripcion_form,
                                                                   'controlador':controlador_form,'accion':accion_form,'error2':mesg,'email':1},context_instance = RequestContext(request))
                
            
            cliente=form.cleaned_data['ccliente']
            organismo=form.cleaned_data['organismo']
            provincia=form.cleaned_data['provincia']
            edad=0 if form.cleaned_data['edad'] is None else int(form.cleaned_data['edad'])
            orden=form.cleaned_data['orden']
            
            filtro=[]
            
            resultado1=Facturas.objects.select_related().filter(cancelada=False,confirmar=True).all()
            if edad!=0:
                filtro.append('Edad mín. de la Factura: '+str(edad))
            if organismo!=None:
                filtro.append('Organismo: '+organismo.siglas_organismo)
                resultado1=resultado1.filter(cliente__organismo__id=organismo.id)
            
            if provincia!=None:
                filtro.append('Provincia: '+provincia.descripcion_provincia)
                resultado1=resultado1.filter(cliente__provincia__codigo_provincia=provincia.codigo_provincia)
                
            if cliente!=None:
                filtro.append('Cliente: '+cliente.nombre)
                resultado1=resultado1.filter(cliente__nombre=cliente.nombre)
                
            if orden=='cliente':
                filtro.append('Ordenado por Cliente')
                resultado1=resultado1.order_by('cliente','cliente__organismo','cliente__provincia') 
            else:
                filtro.append('Ordenado por la Edad de la Factura')
                resultado1=resultado1.order_by('doc_factura__fecha_doc','cliente','cliente__organismo','cliente__provincia')
                
                   
                             
            resultado=[]
            resultado_pdf=[]
            nombrec=''
            
            if request.POST.__contains__('submit1') or request.POST.__contains__('submit2'):
                for fila in resultado1:
                    
                    precio_mn=fila.detallefactura_set.aggregate(Sum('precio_cuc'))['precio_cuc__sum']
                    precio_mn = 0.0 if precio_mn==None else precio_mn
#                    precio_mn=fila.get_importetotalcup(1)
                    precio_cuc=fila.detallefactura_set.aggregate(Sum('precio_mn'))['precio_mn__sum']
                    precio_cuc = 0.0 if precio_cuc==None else precio_cuc
#                    precio_cuc=fila.get_importecuc(1)
                    porpagar_cuc=fila.pagosfacturas_set.filter(pagos__tipo_moneda='1').aggregate(Sum('importe_pagado'))['importe_pagado__sum']
                    porpagar_cuc = 0.0 if porpagar_cuc==None else porpagar_cuc
                    importe_pagado_cuc=float(precio_cuc)-float(porpagar_cuc)
                    porpagar_cup=fila.pagosfacturas_set.filter(pagos__tipo_moneda='2').aggregate(Sum('importe_pagado'))['importe_pagado__sum']
                    porpagar_cup = 0.0 if porpagar_cup==None else porpagar_cup
                    importe_pagado_cup=float(precio_mn)-float(porpagar_cup)
                    
                    resultado_pdf=resultado_pdf+[{'cliente':fila.cliente.nombre,'nro':fila.factura_nro,'fecha':fila.get_fecha(),'edad':fila.edad_factura(),
                            'importecup':precio_mn,'importecuc':precio_cuc,
                            'cobradocup':importe_pagado_cup,
                            'cobradocuc':importe_pagado_cuc,
                            'pendientecup':float(precio_mn)-float(importe_pagado_cup),
                            'pendientecuc':float(precio_cuc)-float(importe_pagado_cuc)}]
                if resultado_pdf.__len__()==0:                              
                    mesg=mesg+['No existe información para mostrar']
                    return render_to_response("comercial/reporteindex.html",{'form':form,'title':titulo_form, 'form_name':nombre_form,'form_description':descripcion_form,
                                                                    'controlador':controlador_form,'accion':accion_form,'error2':mesg,'email':1},context_instance = RequestContext(request))
           
            
                pdf_file_name=os.path.join(comerciax.settings.ADMIN_MEDIA_PDF,"Facturas por Cobrar.pdf")
                if form.cleaned_data['orden'] == "edad":
                    edad = True
                else:
                    edad = False
                if report_class.Reportes.GenerarRep(report_class.Reportes() , resultado_pdf, "fac_cobrar",pdf_file_name,filtro,edad)==0:
                    mesg=mesg+['Debe cerrar el documento Facturas por Cobrar.pdf']
                    return render_to_response("comercial/reporteindex.html",{'filtro':filtro,'resultado':resultado,'form':form,'title':titulo_form, 'form_name':nombre_form,'form_description':descripcion_form,
                                                        'controlador':controlador_form,'accion':accion_form,'error2':mesg,'email':1},context_instance = RequestContext(request))
                else:
                    input = PdfFileReader(file(pdf_file_name,"rb"))
                    output = PdfFileWriter()
                    for page in input.pages:
                        output.addPage(page)
                    buffer = StringIO.StringIO()
                    output.write(buffer)
                    response = HttpResponse(mimetype='application/pdf')
                    file_namesitio='%s'%(pdf_file_name)
                    response['Content-Disposition'] = 'attachment; filename=%s'%(pdf_file_name)
                    response.write(buffer.getvalue())
                    if envia:
                        import smtplib
                        from email.mime.application import MIMEApplication
                        from django.core.mail.message import EmailMessage
                        try:
                            message = EmailMessage(subject='Facturas por Cobrar',body='Enviado por '+request.user.first_name+' '+request.user.last_name, from_email=correo_envia, to=[correo])
                            part = MIMEApplication(open(file_namesitio,"rb").read())
                            part.add_header('Content-Disposition', 'attachment', filename="Facturas por Cobrar.pdf")
                            message.attach(part)
                            if ssl==True:
                                smtp = smtplib.SMTP_SSL(host=servidor,port=puerto)
                            else:
                                smtp = smtplib.SMTP(servidor)
                            smtp.ehlo()
                            smtp.login(correo_envia,contrasena)
                            smtp.sendmail(correo_envia,[correo],message.message().as_string())
                            smtp.close()
                            return response         
                        except Exception, e:
                            mesg=mesg+['Error de conexión. Revise la configuración del Correo SMTP']
                            return render_to_response("comercial/reporteindex.html",{'filtro':filtro,'resultado':resultado,'form':form,'title':titulo_form, 'form_name':nombre_form,'form_description':descripcion_form,
                                                    'controlador':controlador_form,'accion':accion_form,'error2':mesg},context_instance = RequestContext(request))
                    return response
            else: 
                nombre1=''
                nombrec=''
                
                totalimportecup=0
                totalimportecuc=0
                totalcobradocup=0
                totalcobradocuc=0
                totalpendientecup=0
                totalpendientecuc=0
                      
                for fila in resultado1:
                    precio_mn=fila.get_importetotalcup(1)
                    precio_cuc=fila.get_importecuc(1)
                    importe_pagado_cuc=fila.get_importecuc(1)-fila.get_porpagar_cuc(1)
                    importe_pagado_cup=fila.get_importetotalcup(1)-fila.get_porpagar_cup(1)
                    if (((precio_mn-importe_pagado_cup)+(precio_cuc-importe_pagado_cuc))>0):
                        
                        
                        totalimportecup+=precio_mn
                        totalimportecuc+=precio_cuc
                        totalcobradocup+=importe_pagado_cup
                        totalcobradocuc+=importe_pagado_cuc
                        totalpendientecup+=precio_mn-importe_pagado_cup
                        totalpendientecuc+=precio_cuc-importe_pagado_cuc
    
                        if nombrec == fila.cliente.nombre:
                            
                            resultado=resultado+[{'cliente':"",'nro':fila.factura_nro,'fecha':fila.doc_factura.fecha_doc,'edad':fila.edad_factura(),
                                'importecup':'{:20,.2f}'.format(precio_mn),'importecuc':'{:20,.2f}'.format(precio_cuc),
                                'cobradocup':'{:20,.2f}'.format(importe_pagado_cup),
                                'cobradocuc':'{:20,.2f}'.format(importe_pagado_cuc),
                                'pendientecup':'{:20,.2f}'.format(precio_mn-importe_pagado_cup),
                                'pendientecuc':'{:20,.2f}'.format(precio_cuc-importe_pagado_cuc)}]
                        else:
                            resultado=resultado+[{'cliente':fila.cliente.nombre,'nro':fila.factura_nro,'fecha':fila.doc_factura.fecha_doc,'edad':fila.edad_factura(),
                                'importecup':'{:20,.2f}'.format(precio_mn),'importecuc':'{:20,.2f}'.format(precio_cuc),
                                'cobradocup':'{:20,.2f}'.format(importe_pagado_cup),
                                'cobradocuc':'{:20,.2f}'.format(importe_pagado_cuc),
                                'pendientecup':'{:20,.2f}'.format(precio_mn-importe_pagado_cup),
                                'pendientecuc':'{:20,.2f}'.format(precio_cuc-importe_pagado_cuc)}]
                                                  
                        nombrec=fila.cliente.nombre
                        
                        nombre1=fila.cliente.nombre
                        
                resultado=resultado+[{'totalimportecup':'{:20,.2f}'.format(totalimportecup),'totalimportecuc':'{:20,.2f}'.format(totalimportecuc),
                                      'totalcobradocup':'{:20,.2f}'.format(totalcobradocup),'totalcobradocuc':'{:20,.2f}'.format(totalcobradocuc),
                                      'totalpendientecup':'{:20,.2f}'.format(totalpendientecup),'totalpendientecuc':'{:20,.2f}'.format(totalpendientecuc)}]
                if resultado.__len__()<=1:                              
                        mesg=mesg+['No existe información para mostrar']
                        return render_to_response("comercial/reporteindex.html",{'form':form,'title':titulo_form, 'form_name':nombre_form,'form_description':descripcion_form,
                                                                        'controlador':controlador_form,'accion':accion_form,'error2':mesg,'email':1},context_instance = RequestContext(request))
               
                else:
                    return render_to_response("report/facturas_cobrar.html",{'filtro':filtro,'fecha_hoy':fecha_hoy(),'resultado':resultado,'error2':mesg},context_instance = RequestContext(request))            
                
            
        
    form = Rep_FacturaCobrar() 
    
    return render_to_response("comercial/reporteindex.html",{'form':form,'title':titulo_form, 'form_name':nombre_form,'form_description':descripcion_form,
                                                                'controlador':controlador_form,'accion':accion_form,'error2':mesg,'email':1},context_instance = RequestContext(request))

@login_required
def regcobros(request):
    
    nombre_form='Reportes'
    descripcion_form='Registro de Cobros'
    titulo_form='Registro de Cobros Efectuados' 
    controlador_form='Reportes'
    accion_form='/comerciax/comercial/regcobros/reporte'
    mesg=[]
    
    if request.method == 'POST':
    
        form = Rep_RegCobros(request.POST)
        
        if form.is_valid():
            sorganismo=form.cleaned_data['organismo']
            sprovincia=form.cleaned_data['provincia']
            scliente=form.cleaned_data['ccliente']
            fecha=form.cleaned_data['cfecha']
            mmoneda=form.cleaned_data['cmoneda']
            filtro=[]
            filtro.append('Pagos efectuados a partir del '+fecha.strftime("%d/%m/%Y"))
            pagos=Pagos.objects.select_related().filter(fecha_pago__gte=fecha).order_by('pagosclientes__cliente','fecha_pago')
            if mmoneda!=None:
                filtro.append('Moneda:'+mmoneda.descripcion)
                pagos=pagos.filter(tipo_moneda=mmoneda)
            if sorganismo!=None:
                filtro.append('Organismo:'+sorganismo.siglas_organismo)
                pagos=pagos.filter(pagosclientes__cliente__organismo=sorganismo)
            if sprovincia!=None:
                filtro.append('Provincia:'+sprovincia.descripcion_provincia)
                pagos=pagos.filter(pagosclientes__cliente__provincia=sprovincia) 
            if scliente!= None and mmoneda is None:
                filtro.append('Cliente:'+scliente.nombre)
                pagos=pagos.filter(pagosclientes__cliente=scliente)
            if pagos.__len__()==0:
                mesg=mesg+['No existe información para mostrar']
                return render_to_response("comercial/reporteindex.html",{'form':form,'title':titulo_form, 'form_name':nombre_form,'form_description':descripcion_form,
                                                                'controlador':controlador_form,'accion':accion_form,'error2':mesg},context_instance = RequestContext(request))
            resultado=[]
            resultado_pdf=[]
            resultado_pdf_d=[]
            ccliente=''
            if request.POST.__contains__('submit1'):
                Clientepago.objects.all().delete()
                objt = Clientepago()
                for a in pagos:
                    if a.particulares==True:
                        rcliente=a.pagosefectivo.nombre+'-'+a.pagosefectivo.ci
                    else:
                        rcliente = a.pagosclientes.cliente.nombre+'-'+a.pagosclientes.cliente.codigo
                    id=uuid4()
                    objt.id=id
                    objt.cliente = rcliente
                    objt.fecha_pagos = a.fecha_pago
                    objt.moneda = a.tipo_moneda.descripcion
                    objt.importe_pagado = a.importe
                    objt.deposito_adelantado = '{:20,.2f}'.format(a.deposito_adelantado)
                    objt.id_pago=a.id_pago
                    if a.efectivo == True:
                        objt.forma_pago  = 'Efectivo'
                        objt.clientep = a.pagosefectivo.nombre+' '+a.pagosefectivo.ci
                    else:                                                
                        objt.forma_pago  = a.pagosotros.forma_pago.descripcion
                        objt.clientep = a.pagosotros.nro
                    objt.save()
                cc=Clientepago.objects.all()
                facpago=Factpago()
                for a in cc: 
                    pagofact=PagosFacturas.objects.filter(pagos=Pagos.objects.get(id_pago=a.id_pago))
                    pagofactpart=PagosFacturasPart.objects.filter(pagos=Pagos.objects.get(id_pago=a.id_pago))
                    for ax in pagofact:
                        facpago.id=uuid4()
                        facpago.nro = ax.facturas.factura_nro
                        facpago.fecha = ax.facturas.doc_factura.fecha_doc
                        facpago.idcliente=a
                        facpago.imp_pagado=ax.importe_pagado
                        facpago.save()
                    for ax in pagofactpart:
                        facpago.id=uuid4()
                        facpago.nro = ax.facturas.factura_nro
                        facpago.fecha = ax.facturas.doc_factura.fecha_doc
                        facpago.idcliente=a
                        facpago.imp_pagado=ax.importe_pagado
                        facpago.save()
                    
            for a in pagos:
                a.id_pago
                if a.particulares==True:
                    xnombre=a.pagosefectivo.nombre
                else:
                    if a.efectivo==False:
                        xnombre=a.pagosclientes.cliente.nombre 
                    else:
                        xnombre=a.pagosefectivo.nombre                  
                if ccliente == xnombre:
                        
                    rcliente = 0
                    
                    if a.efectivo == True:
                        resultado=resultado+[{'fecha':a.fecha_pago,'pago_nro':a.pagosefectivo.nombre+' '+a.pagosefectivo.ci,'moneda':a.tipo_moneda.descripcion,
                                          'forma_pago':'Efectivo','importe_pagado':'{:20,.2f}'.format(a.importe),'deposito_adelantado':'{:20,.2f}'.format(a.deposito_adelantado)}]
                    else:
                        resultado=resultado+[{'fecha':a.fecha_pago,'pago_nro':a.pagosotros.nro,'moneda':a.tipo_moneda.descripcion,
                                          'forma_pago':a.pagosotros.forma_pago.descripcion,'importe_pagado':'{:20,.2f}'.format(a.importe),'deposito_adelantado':'{:20,.2f}'.format(a.deposito_adelantado)}]
                    
                else:
                    if a.particulares==True:
                        rcliente=a.pagosefectivo.nombre+'-'+a.pagosefectivo.ci
                        ccliente = a.pagosefectivo.nombre
                    else:
                        rcliente = a.pagosclientes.cliente.nombre+'-'+a.pagosclientes.cliente.codigo
                        ccliente = a.pagosclientes.cliente.nombre
                    resultado=resultado+[{'fecha':'','cliente':rcliente,'pago_nro':'','moneda':'','forma_pago':'','importe_pagado':'','deposito_adelantado':''}]
                    if a.efectivo == True:
                        resultado=resultado+[{'fecha':a.fecha_pago,'pago_nro':a.pagosefectivo.nombre+' '+a.pagosefectivo.ci,'moneda':a.tipo_moneda.descripcion,
                                          'forma_pago':'Efectivo','importe_pagado':'{:20,.2f}'.format(a.importe),'deposito_adelantado':'{:20,.2f}'.format(a.deposito_adelantado)}]
                    else:
                        resultado=resultado+[{'fecha':a.fecha_pago,'pago_nro':a.pagosotros.nro,'moneda':a.tipo_moneda.descripcion,
                                          'forma_pago':a.pagosotros.forma_pago.descripcion,'importe_pagado':'{:20,.2f}'.format(a.importe),'deposito_adelantado':'{:20,.2f}'.format(a.deposito_adelantado)}]
                if form.cleaned_data['seleccion']=='Si':
                        
                        a2=0
                        if a.particulares==False:
                            factu=a.pagosfacturas_set.all().order_by('facturas__factura_nro')
                        else:
                            factu=a.pagosfacturaspart_set.all().order_by('facturas__factura_nro')
                        for ax in factu:
                            if a2==0:
                                resultado=resultado+[{'encab_fact':'1'}]
                            a2+=1
                            resultado=resultado+[{'fechafact':ax.facturas.doc_factura.fecha_doc,'factura_nro':ax.facturas.factura_nro,'pagado':'{:20,.2f}'.format(ax.importe_pagado)}]
            if not request.POST.__contains__('submit1'):
                return render_to_response("report/registro_cobros.html",{'filtro':filtro,'fecha_hoy':fecha_hoy(),'resultado':resultado,'error2':mesg},context_instance = RequestContext(request))
            else:
                pdf_file_name=os.path.join(comerciax.settings.ADMIN_MEDIA_PDF,"Registro de Cobros.pdf")
                if report_class.Reportes.GenerarRep(report_class.Reportes() ,[], "reg_cobros", pdf_file_name,filtro)==0:
                    mesg=mesg+['Debe cerrar el documento Registro de Cobros.pdf']
                    return render_to_response("comercial/reporteindex.html",{'filtro':filtro,'resultado':resultado,'form':form,'title':titulo_form, 'form_name':nombre_form,'form_description':descripcion_form,
                                                    'controlador':controlador_form,'accion':accion_form,'error2':mesg},context_instance = RequestContext(request))
                else:
                    input = PdfFileReader(file(pdf_file_name,"rb"))
                    output = PdfFileWriter()
                    for page in input.pages:
                        output.addPage(page)
                    buffer = StringIO.StringIO()
                    output.write(buffer)
                    response = HttpResponse(mimetype='application/pdf')
                    response['Content-Disposition'] = 'attachment; filename=%s'%(pdf_file_name)
                    response.write(buffer.getvalue())
                    return response
            
    form = Rep_RegCobros() 
    
    return render_to_response("comercial/reporteindex.html",{'form':form,'title':titulo_form, 'form_name':nombre_form,'form_description':descripcion_form,
                                                                'controlador':controlador_form,'accion':accion_form,'error2':mesg},context_instance = RequestContext(request))
@login_required
def ventas_decomiso(request):
   
    nombre_form='Reportes'
    descripcion_form='Decomisos Vendidos'
    titulo_form='Decomisos Vendidos' 
    controlador_form='Reportes'
    accion_form='/comerciax/comercial/ventas_decomiso/reporte'
    mesg=[]
    
    if request.method == 'POST':
    
        form = Rep_VentasDecomiso(request.POST)
        
        if form.is_valid():
            sorganismo=form.cleaned_data['organismo']
            sprovincia=form.cleaned_data['provincia']
            scliente=form.cleaned_data['ccliente']
            fecha_desde=form.cleaned_data['cfecha']
            fecha_hasta=form.cleaned_data['dfecha']
            desglose=form.cleaned_data['desglosado']
            filtro=[]
            filtro.append('Ventas de Decomiso desde '+fecha_desde.strftime("%d/%m/%Y")+' hasta '+fecha_hasta.strftime("%d/%m/%Y"))
            if desglose:
                pagos=DetalleFactura.objects.select_related().filter(casco__decomisado=True,factura__cancelada=False,factura__doc_factura__fecha_doc__gte=fecha_desde,factura__doc_factura__fecha_doc__lte=fecha_hasta).order_by('casco__detallerc__rc__cliente__organismo__siglas_organismo')
                
                if scliente!=None:
                    pagos=pagos.filter(casco__detallerc__rc__cliente=scliente)
                else:
                    if sorganismo!=None:
                        pagos=pagos.filter(casco__detallerc__rc__cliente__organismo=sorganismo)
                    if sprovincia!=None:
                        pagos=pagos.filter(casco__detallerc__rc__cliente__provincia=sprovincia) 
                
                resultado=[]
                for a in pagos:
                    if a.factura.get_confirmada()=='S':
                        resultado+=[{'organismod':a.casco.get_cliente_organismo()[:13],'cliented':a.casco.get_cliente()[:40],
                                    'medida':a.casco.producto_salida.descripcion,'casconro':a.casco.casco_nro,
                                    'organismov':a.factura.cliente.organismo.siglas_organismo[:13],'clientev':a.factura.cliente.nombre[:40],
                                    'nrofact':a.factura.factura_nro}]
                #Buscar si hay casco decomisados vendidos a particulares
                pagos1=DetalleFacturaPart.objects.select_related().filter(casco__decomisado=True,factura__cancelada=False,factura__doc_factura__fecha_doc__gte=fecha_desde,factura__doc_factura__fecha_doc__lte=fecha_hasta).order_by('casco__detallerp__rp__nombre')
                if scliente!=None:
                    pagos1=pagos1.filter(casco__particular=False,casco__detallerc__rc__cliente=scliente)
                else:
                    if sorganismo!=None:
                        pagos1=pagos1.filter(casco__particular=False,casco__detallerc__rc__cliente__organismo=sorganismo)
                    if sprovincia!=None:
                        pagos1=pagos1.filter(casco__particular=False,casco__detallerc__rc__cliente__provincia=sprovincia) 
                for a in pagos1:
                    if a.factura.get_confirmada()=='S':
                        resultado+=[{'organismod':a.casco.get_cliente_organismo()[:10],'cliented':a.casco.get_cliente()[:40],
                                        'medida':a.casco.producto_salida.descripcion,'casconro':a.casco.casco_nro,
                                        'organismov':'** No Estatal','clientev':a.factura.nombre[:40],
                                        'nrofact':a.factura.factura_nro}]
                    
            #===================================================================
            # 
            #===================================================================
          
                if pagos.__len__()+pagos1.__len__()==0:
                    mesg = mesg+['No existe información para mostrar']
                    return render_to_response("comercial/reporteindex.html",{'form':form,'title':titulo_form, 'form_name':nombre_form,'form_description':descripcion_form,
                                                                    'controlador':controlador_form,'accion':accion_form,'error2':mesg},context_instance = RequestContext(request))
                else:
                    if not request.POST.__contains__('submit1'):
                        return render_to_response("report/ventas_decomiso.html",{'desglosado':True,'filtro':filtro,'fecha_hoy':fecha_hoy(),'resultado':resultado,'error2':mesg},context_instance = RequestContext(request))
                    else:
                        
                        pdf_file_name=os.path.join(comerciax.settings.ADMIN_MEDIA_PDF,"Facturas por Cobrar.pdf")
                        if report_class.Reportes.GenerarRep(report_class.Reportes() , resultado, "vent_decomiso",pdf_file_name,filtro)==0:
                            mesg=mesg+['Debe cerrar el documento Facturas por Cobrar.pdf']
                            return render_to_response("comercial/reporteindex.html",{'filtro':filtro,'resultado':resultado,'form':form,'title':titulo_form, 'form_name':nombre_form,'form_description':descripcion_form,
                                                            'controlador':controlador_form,'accion':accion_form,'error2':mesg},context_instance = RequestContext(request))
                        else:
                            input = PdfFileReader(file(pdf_file_name,"rb"))
                            output = PdfFileWriter()
                            for page in input.pages:
                                output.addPage(page)
                            buffer = StringIO.StringIO()
                            output.write(buffer)
                            response = HttpResponse(mimetype='application/pdf')
                            response['Content-Disposition'] = 'attachment; filename=%s'%(pdf_file_name)
                            response.write(buffer.getvalue())
                            return response
            else:
                resultado_sql="""
                select admincomerciax_organismo.siglas_organismo as decomisado,vendidos.vendido  from
                    (SELECT  
                           casco_casco.id_casco,
                           admincomerciax_organismo.siglas_organismo as vendido
                       FROM casco_casco
                       JOIN comercial_detallefactura ON casco_casco.id_casco = comercial_detallefactura.casco_id
                       JOIN comercial_facturas ON comercial_detallefactura.factura_id = comercial_facturas.doc_factura_id
                       JOIN admincomerciax_cliente ON comercial_facturas.cliente_id = admincomerciax_cliente.id
                       JOIN admincomerciax_organismo on admincomerciax_cliente.organismo_id=admincomerciax_organismo.id
                       JOIN casco_doc ON comercial_facturas.doc_factura_id = casco_doc.id_doc 
                      WHERE casco_casco.estado_actual = 'Factura' AND casco_casco.particular = False and casco_casco.decomisado = True AND
                      date(casco_doc.fecha_doc)>='"""+fecha_desde.strftime("%d/%m/%Y")+"""' AND date(casco_doc.fecha_doc)<='"""+fecha_hasta.strftime("%d/%m/%Y")+"""' AND 
                      comercial_facturas.confirmar = true order by admincomerciax_organismo.siglas_organismo) as vendidos
                      JOIN casco_detallerc ON vendidos.id_casco = casco_detallerc.casco_id
                      JOIN casco_recepcioncliente ON casco_detallerc.rc_id = casco_recepcioncliente.doc_recepcioncliente_id
                      JOIN admincomerciax_cliente ON casco_recepcioncliente.cliente_id = admincomerciax_cliente.id
                      JOIN admincomerciax_organismo on admincomerciax_cliente.organismo_id=admincomerciax_organismo.id
                      order by admincomerciax_organismo.siglas_organismo
                """
                resultado = query_to_dicts(resultado_sql)
                dicc_decom={}
                list_vendido=[]
                list_decomiso=[]
                dicc_vendido={}
                for res in resultado:
                    if dicc_decom.has_key(res['decomisado']):
                        if dicc_decom[res['decomisado']].has_key(res['vendido']):
                            dicc_decom[res['decomisado']][res['vendido']]=dicc_decom[res['decomisado']][res['vendido']]+1
                        else:
                            dicc_decom[res['decomisado']][res['vendido']]=1
                            if not (res['vendido'] in list_vendido):
                                list_vendido.append(res['vendido'])
                                
                    else:
                        dicc_decom[res['decomisado']]={}
                        
                        list_decomiso.append(res['decomisado'])
                        if not (res['vendido'] in list_vendido):
                            list_vendido.append(res['vendido'])
                        dicc_decom[res['decomisado']][res['vendido']]=1

                list_vendido.sort() 
                list_decomiso.sort() 
                resu=[]
                list_vendido.insert(0,'Decomiso/Vendido')
                list_vendido.insert(list_vendido.__len__(),'Total')
                resu.append(list_vendido)
                a1=2
                ultimo=list_vendido.__len__()-1
                canti=0
                total=0
                for a1 in range(list_decomiso.__len__()):
                    dec=dicc_decom[list_decomiso[a1]].keys()
                    resu1=[]
                    for j in range(list_vendido.__len__()):
                        resu1.append("0")
                    resu1[0]=list_decomiso[a1]
                    cant=0
                    for k in range(dec.__len__()):
                        posi=list_vendido.index(dec[k])
                        vend=list_decomiso[a1]
                        resu1[posi]=dicc_decom[vend][dec[k]]
                        cant+=dicc_decom[vend][dec[k]]
                        if dicc_vendido.has_key(dec[k]):
                            dicc_vendido[dec[k]]=dicc_vendido[dec[k]]+dicc_decom[vend][dec[k]]
                        else:
                            dicc_vendido[dec[k]]=dicc_decom[vend][dec[k]]
                            
                    resu1[ultimo]=cant
                    resu.append(resu1)
                resu_total=[]
                for j in range(list_vendido.__len__()):
                    resu_total.append("0")
                for k in range(list_vendido.__len__()):
                    posi=list_vendido.index(list_vendido[k]) 
                    if dicc_vendido.has_key(list_vendido[k]):
                        resu_total[posi]=dicc_vendido[list_vendido[k]]
                        total=total+dicc_vendido[list_vendido[k]]
                resu_total[0]='T O T A L'
                resu_total[ultimo]=total
                resu.append(resu_total)
                if not request.POST.__contains__('submit1'):
                    resu[0:1]=[]
                    return render_to_response("report/ventas_decomiso.html",{'resu_total':resu_total,'column':list_vendido,'filtro':filtro,'fecha_hoy':fecha_hoy(),'resultado':resu,'error2':mesg},context_instance = RequestContext(request))
#                else:
                    
#                    resu_dicc={}
#                    for a2 in range(resu.__len__()):
#                        resu_dicc[str(a2+1)]=resu[a2]
#                    pdf_file_name=os.path.join(comerciax.settings.ADMIN_MEDIA_PDF,"Ventas Decomiso.pdf")
#                    if report_class.Reportes.GenerarRep(report_class.Reportes() , resu_dicc, "vent_decomiso_sindesglose",pdf_file_name,filtro)==0:
#                        mesg=mesg+['Debe cerrar el documento Ventas Decomiso.pdf']
#                        return render_to_response("comercial/reporteindex.html",{'filtro':filtro,'resultado':resu,'form':form,'title':titulo_form, 'form_name':nombre_form,'form_description':descripcion_form,
#                                                        'controlador':controlador_form,'accion':accion_form,'error2':mesg},context_instance = RequestContext(request))
#                    else:
#                        input = PdfFileReader(file(pdf_file_name,"rb"))
#                        output = PdfFileWriter()
#                        for page in input.pages:
#                            output.addPage(page)
#                        buffer = StringIO.StringIO()
#                        output.write(buffer)
#                        response = HttpResponse(mimetype='application/pdf')
#                        response['Content-Disposition'] = 'attachment; filename=%s'%(pdf_file_name)
#                        response.write(buffer.getvalue())
#                        return response
#                Cascos.objects.select_related().filter(decomisado=True,estado_actual='Factura',set_factura__doc_factura__fecha_doc__gte=fecha_desde,set_factura__doc_factura__fecha_doc__lte=fecha_hasta)
                

            
    form = Rep_VentasDecomiso() 
    return render_to_response("comercial/reporteindex.html",{'form':form,'title':titulo_form, 'form_name':nombre_form,'form_description':descripcion_form,
                                                                'controlador':controlador_form,'accion':accion_form,'error2':mesg},context_instance = RequestContext(request))
  
def invfisicoall_pdf(request):
    if not request.user.has_perm('casco.invalmcasco'):
        return render_to_response("denegado.html",locals(),context_instance = RequestContext(request))
    elementos = query_to_dicts("""
    SELECT
        *
    FROM
        allalminvf
    order by medida
    """)
    
    fechacierre = Fechacierre.objects.filter(almacen='c').all()
    ultimo_mes_anyo = fechacierre[0]
    messes = ultimo_mes_anyo.mes + 1 
    pdf_file_name=os.path.join(comerciax.settings.ADMIN_MEDIA_PDF,"Inventario Fisico Mensual.pdf")
    filtro=[]
#    filtro=['Del mes de '+mes+ ' del '+str(year)]
    mesg=[]
    if report_class.Reportes.GenerarRep(report_class.Reportes() , elementos, "inv_fismen",pdf_file_name,filtro)==0:
        mesg.append('Debe cerrar el fichero Inventario Fisico Mensual.pdf')
    else:
        input = PdfFileReader(file(pdf_file_name,"rb"))
        output = PdfFileWriter()
        for page in input.pages:
            output.addPage(page)
        buffer = StringIO.StringIO()
        output.write(buffer)
        response = HttpResponse(mimetype='application/pdf')
        response['Content-Disposition'] = 'attachment; filename=%s'%(pdf_file_name)
        response.write(buffer.getvalue())
        return response    


def verificaemail(request):
    import smtplib
    try:
        error=0
        querySet = Config_SMTPEmail.objects.get()
        servidor=querySet.servidor
        correo_envia=querySet.correo
        puerto = querySet.puerto
        ssl = querySet.ssl
        contrasena = querySet.contrasena
        
        if ssl:
            smtp = smtplib.SMTP_SSL(host=servidor,port=puerto)
        smtp.ehlo()
        smtp.login(correo_envia,base64.b64decode(contrasena))
    except Exception, e:
        error=1
    
    lista_valores=[]
#    for a1 in elementos: 
    lista_valores+=[{'conexion':error}]
    return HttpResponse(simplejson.dumps(lista_valores),content_type = 'application/javascript; charset=utf8')


@login_required
def movcascos(request):
    
    nombre_form='Movimientos de Cascos'
    descripcion_form='Movimientos de Cascos'
    titulo_form='Movimientos de Cascos' 
    controlador_form='Movimientos'
    accion_form=''
    mesg=[]
    
    mesg=[]
    if request.method == 'POST':
        form = MovCascos(request.POST)
        
        if form.is_valid():
            mov = form.cleaned_data['movimiento']
            cliente=form.cleaned_data['ccliente']
            organismo=form.cleaned_data['organismo']
            provincia=form.cleaned_data['provincia']
            medida=form.cleaned_data['medida']
            desde  = form.cleaned_data['desde']
            hasta  = form.cleaned_data['hasta']
            envia=False
            seleccion = form.cleaned_data['seleccionar_por']
            desglose=1 if seleccion=="Si" else 0
            agrupar_por = form.cleaned_data['agrupado_por']
            pdf_file_name=os.path.join(comerciax.settings.ADMIN_MEDIA_PDF,"Movimiento de Cascos.pdf")
            if request.POST.__contains__('submit2'): #Si se le pone enviar por email
                envia=True
#                cliente=form.cleaned_data['ccliente']
                if cliente==None:
                    mesg=mesg+['Debe seleccionar un cliente']
                    return render_to_response("comercial/reporteindex.html",{'vprev':1,'form':form,'title':titulo_form, 'form_name':nombre_form,'form_description':descripcion_form,
                                                                    'controlador':controlador_form,'accion':accion_form,'error2':mesg,'email':1},context_instance = RequestContext(request))
                correo=cliente.email
                if correo.__len__()==0:
                    mesg=mesg+['Este cliente no tiene correo']
                    return render_to_response("comercial/reporteindex.html",{'vprev':1,'form':form,'title':titulo_form, 'form_name':nombre_form,'form_description':descripcion_form,
                                                                   'controlador':controlador_form,'accion':accion_form,'error2':mesg,'email':1},context_instance = RequestContext(request))
                try:
                    querySet = Config_SMTPEmail.objects.get()
                except Exception, e:
                    mesg=mesg+['No está configurado el correo SMTP']
                    return render_to_response("comercial/reporteindex.html",{'vprev':1,'form':form,'title':titulo_form, 'form_name':nombre_form,'form_description':descripcion_form,
                                                                   'controlador':controlador_form,'accion':accion_form,'error2':mesg,'email':1},context_instance = RequestContext(request))
                servidor=querySet.servidor
                correo_envia=querySet.correo
                puerto = querySet.puerto
                ssl = querySet.ssl
                try:
                    contrasena = base64.b64decode(querySet.contrasena)
                except Exception, e:
                    mesg=mesg+['Revise la contraseña en la configuración del Correo SMTP']
                    return render_to_response("comercial/reporteindex.html",{'vprev':1,'form':form,'title':titulo_form, 'form_name':nombre_form,'form_description':descripcion_form,
                                                                   'controlador':controlador_form,'accion':accion_form,'error2':mesg,'email':1},context_instance = RequestContext(request))
                
            
            
            filtro=[]
            cade_where=""
            filtro.append('Desde: '+desde.strftime("%d/%m/%Y"))
            filtro.append('Hasta: '+hasta.strftime("%d/%m/%Y"))
            
#            cade_where+="(date(fecha_doc)>='"+desde.strftime("%d/%m/%Y")+"') AND "
#            cade_where+="(date(fecha_doc)<='"+hasta.strftime("%d/%m/%Y")+"')"
            
            cade_where="date(fecha_doc) between '"+desde.strftime("%Y-%m-%d")+"' and '"+hasta.strftime("%Y-%m-%d")+"'"
            
            if organismo!=None:
                filtro.append('Organismo: '+organismo.siglas_organismo)
                cade_where+=" AND (admincomerciax_organismo.id='"+organismo.id+"')"
            
            if provincia!=None:
                filtro.append('Provincia: '+provincia.descripcion_provincia)
                cade_where+=" AND (admincomerciax_provincias.codigo_provincia='"+provincia.codigo_provincia+"')"
                
            if cliente!=None:
                filtro.append('Cliente: '+cliente.nombre)
                cade_where+=" AND (admincomerciax_cliente.id='"+cliente.id+"')"
            
            if medida!=None:
                filtro.append('Medida: '+medida.descripcion)
                cade_where+=" AND (admincomerciax_producto.id='"+medida.id+"')"
            encabezado=""
            if mov=='Factura':
                tipo_doc=14
                cade_where+=" AND (casco_doc.tipo_doc = '14') AND (comercial_facturas.cancelada =false) AND (comercial_facturas.confirmar = true) " 
                encabezado="Cascos Facturados" 
                if desglose==1:
                    order_by = """ admincomerciax_organismo.siglas_organismo, admincomerciax_provincias.descripcion_provincia,
                                   admincomerciax_cliente.nombre,casco_doc.fecha_doc,comercial_facturas.factura_nro, 
                                   admincomerciax_producto.descripcion""" 
                    if agrupar_por:
                        order_by = """ admincomerciax_producto.descripcion,admincomerciax_organismo.siglas_organismo, 
                                       admincomerciax_provincias.descripcion_provincia,
                                       admincomerciax_cliente.nombre,casco_doc.fecha_doc,comercial_facturas.factura_nro"""
                    
                    resultado_sql="""
                       SELECT admincomerciax_organismo.siglas_organismo,admincomerciax_provincias.descripcion_provincia,
                          admincomerciax_cliente.nombre,casco_doc.fecha_doc, casco_doc.tipo_doc, 
                          comercial_facturas.factura_nro as doc_nro, comercial_facturas.cancelada, 
                          comercial_facturas.confirmar, SUM(comercial_detallefactura.precio_mn) AS mn, 
                          SUM(comercial_detallefactura.precio_casco) AS mn1, 
                          COUNT(admincomerciax_producto.descripcion) AS Cantidad, admincomerciax_producto.descripcion, 
                          admincomerciax_cliente.codigo
                       FROM  casco_doc 
                           INNER JOIN comercial_facturas ON casco_doc.id_doc = comercial_facturas.doc_factura_id 
                           INNER JOIN comercial_detallefactura ON comercial_facturas.doc_factura_id = comercial_detallefactura.factura_id 
                           INNER JOIN casco_casco ON comercial_detallefactura.casco_id = casco_casco.id_casco 
                           INNER JOIN admincomerciax_producto ON casco_casco.producto_salida_id = admincomerciax_producto.id 
                           INNER JOIN admincomerciax_cliente ON comercial_facturas.cliente_id = admincomerciax_cliente.id 
                           INNER JOIN admincomerciax_organismo ON admincomerciax_cliente.organismo_id = admincomerciax_organismo.id 
                           INNER JOIN admincomerciax_provincias ON admincomerciax_cliente.provincia_id = admincomerciax_provincias.codigo_provincia
                       WHERE """+cade_where+"""
                       GROUP BY casco_doc.fecha_doc, casco_doc.tipo_doc, comercial_facturas.factura_nro, 
                         comercial_facturas.cancelada, comercial_facturas.confirmar, admincomerciax_producto.descripcion, 
                         admincomerciax_cliente.codigo, admincomerciax_cliente.nombre, admincomerciax_organismo.siglas_organismo, admincomerciax_provincias.descripcion_provincia
                       ORDER BY """+order_by
                else:
                    resultado_sql="""
                       SELECT admincomerciax_organismo.siglas_organismo,admincomerciax_provincias.descripcion_provincia,
                          admincomerciax_cliente.nombre,casco_doc.fecha_doc, casco_doc.tipo_doc, 
                          comercial_facturas.factura_nro as doc_nro, comercial_facturas.cancelada, 
                          comercial_facturas.confirmar, SUM(comercial_detallefactura.precio_mn) AS mn, 
                          SUM(comercial_detallefactura.precio_casco) AS mn1, 
                          COUNT(comercial_detallefactura.id_detalle) AS Cantidad, 
                          admincomerciax_cliente.codigo
                       FROM  casco_doc 
                           INNER JOIN comercial_facturas ON casco_doc.id_doc = comercial_facturas.doc_factura_id 
                           INNER JOIN comercial_detallefactura ON comercial_facturas.doc_factura_id = comercial_detallefactura.factura_id 
                           INNER JOIN casco_casco ON comercial_detallefactura.casco_id = casco_casco.id_casco 
                           INNER JOIN admincomerciax_producto ON casco_casco.producto_salida_id = admincomerciax_producto.id 
                           INNER JOIN admincomerciax_cliente ON comercial_facturas.cliente_id = admincomerciax_cliente.id 
                           INNER JOIN admincomerciax_organismo ON admincomerciax_cliente.organismo_id = admincomerciax_organismo.id 
                           INNER JOIN admincomerciax_provincias ON admincomerciax_cliente.provincia_id = admincomerciax_provincias.codigo_provincia
                       WHERE """+cade_where+"""
                       GROUP BY casco_doc.fecha_doc, casco_doc.tipo_doc, comercial_facturas.factura_nro, 
                         comercial_facturas.cancelada, comercial_facturas.confirmar, 
                         admincomerciax_cliente.codigo, admincomerciax_cliente.nombre, admincomerciax_organismo.siglas_organismo, admincomerciax_provincias.descripcion_provincia
                       ORDER BY admincomerciax_organismo.siglas_organismo, admincomerciax_provincias.descripcion_provincia,admincomerciax_cliente.nombre,comercial_facturas.factura_nro"""
#                print resultado_sql
            elif mov=='Casco':
                tipo_doc=1
                cade_where+=" AND (casco_doc.tipo_doc = '1')" 
                encabezado="Recepción de Cascos"  
                if desglose==1:
                    order_by = """ admincomerciax_organismo.siglas_organismo,admincomerciax_provincias.descripcion_provincia,admincomerciax_cliente.nombre,
                                    casco_doc.fecha_doc,casco_recepcioncliente.recepcioncliente_nro,admincomerciax_producto.descripcion""" 
                    if agrupar_por:
                        order_by = """ admincomerciax_producto.descripcion,admincomerciax_organismo.siglas_organismo,admincomerciax_provincias.descripcion_provincia,admincomerciax_cliente.nombre,
                                    casco_doc.fecha_doc,casco_recepcioncliente.recepcioncliente_nro""" 
                        
                    resultado_sql= """
                                    SELECT  admincomerciax_organismo.siglas_organismo, 
                                        admincomerciax_provincias.descripcion_provincia,
                                        casco_recepcioncliente.recepcioncliente_nro as doc_nro,
                                        casco_doc.fecha_doc,
                                        admincomerciax_cliente.codigo, 
                                        admincomerciax_cliente.nombre,
                                        admincomerciax_producto.descripcion,
                                            COUNT(admincomerciax_producto.descripcion) AS Cantidad,
                                            admincomerciax_cliente.id, 
                                        admincomerciax_provincias.codigo_provincia, 
                                            admincomerciax_provincias.descripcion_provincia, 
                                        admincomerciax_organismo.codigo_organismo,0.0 as mn1, 0.0 as mn
                                    FROM casco_doc 
                                            INNER JOIN casco_recepcioncliente ON casco_recepcioncliente.doc_recepcioncliente_id = casco_doc.id_doc 
                                            INNER JOIN admincomerciax_cliente ON casco_recepcioncliente.cliente_id = admincomerciax_cliente.id 
                                            INNER JOIN casco_detallerc ON casco_detallerc.rc_id = casco_recepcioncliente.doc_recepcioncliente_id 
                                            INNER JOIN casco_casco ON casco_detallerc.casco_id = casco_casco.id_casco 
                                            INNER JOIN admincomerciax_producto ON casco_casco.producto_id = admincomerciax_producto.id 
                                            INNER JOIN admincomerciax_provincias ON admincomerciax_cliente.provincia_id = admincomerciax_provincias.codigo_provincia 
                                            INNER JOIN admincomerciax_organismo ON admincomerciax_cliente.organismo_id = admincomerciax_organismo.id  
                                    WHERE """+cade_where+"""
                                    GROUP BY casco_recepcioncliente.recepcioncliente_nro,casco_doc.fecha_doc,casco_recepcioncliente.cliente_id, 
                                             admincomerciax_cliente.codigo, admincomerciax_cliente.nombre,admincomerciax_cliente.id, 
                                             admincomerciax_provincias.codigo_provincia, admincomerciax_provincias.descripcion_provincia, 
                                             admincomerciax_organismo.id, admincomerciax_organismo.codigo_organismo,admincomerciax_producto.descripcion,
                                             admincomerciax_organismo.siglas_organismo
                                    order by  """+order_by
                else:
                    resultado_sql= """
                                    SELECT  admincomerciax_organismo.siglas_organismo, 
                                        admincomerciax_provincias.descripcion_provincia,
                                        casco_recepcioncliente.recepcioncliente_nro as doc_nro,
                                        casco_doc.fecha_doc,
                                        admincomerciax_cliente.codigo, 
                                        admincomerciax_cliente.nombre,
                                            COUNT(casco_detallerc.id_detallerc) AS Cantidad,
                                            admincomerciax_cliente.id, 
                                        admincomerciax_provincias.codigo_provincia, 
                                            admincomerciax_provincias.descripcion_provincia, 
                                        admincomerciax_organismo.codigo_organismo,0.0 as mn1, 0.0 as mn
                                    FROM casco_doc 
                                            INNER JOIN casco_recepcioncliente ON casco_recepcioncliente.doc_recepcioncliente_id = casco_doc.id_doc 
                                            INNER JOIN admincomerciax_cliente ON casco_recepcioncliente.cliente_id = admincomerciax_cliente.id 
                                            INNER JOIN casco_detallerc ON casco_detallerc.rc_id = casco_recepcioncliente.doc_recepcioncliente_id 
                                            INNER JOIN casco_casco ON casco_detallerc.casco_id = casco_casco.id_casco 
                                            INNER JOIN admincomerciax_producto ON casco_casco.producto_id = admincomerciax_producto.id 
                                            INNER JOIN admincomerciax_provincias ON admincomerciax_cliente.provincia_id = admincomerciax_provincias.codigo_provincia 
                                            INNER JOIN admincomerciax_organismo ON admincomerciax_cliente.organismo_id = admincomerciax_organismo.id  
                                    WHERE """+cade_where+"""
                                    GROUP BY casco_recepcioncliente.recepcioncliente_nro,casco_doc.fecha_doc,casco_recepcioncliente.cliente_id, 
                                             admincomerciax_cliente.codigo, admincomerciax_cliente.nombre,admincomerciax_cliente.id, 
                                             admincomerciax_provincias.codigo_provincia, admincomerciax_provincias.descripcion_provincia, 
                                             admincomerciax_organismo.id, admincomerciax_organismo.codigo_organismo,
                                             admincomerciax_organismo.siglas_organismo
                                    order by admincomerciax_organismo.siglas_organismo,admincomerciax_provincias.descripcion_provincia,admincomerciax_cliente.nombre,
                                             casco_recepcioncliente.recepcioncliente_nro """
            elif mov=='Produccion':
                cade_where+=" AND (casco_doc.tipo_doc = '2')"
                tipo_doc=2
                encabezado="Enviados de Casco a Producción"
                #aquiiiii
                if desglose==1:
                    order_by = """  
                                  admincomerciax_organismo.siglas_organismo, 
                                  admincomerciax_provincias.descripcion_provincia,
                                  admincomerciax_cliente.nombre,
                                  casco_doc.fecha_doc, 
                                  casco_cc.cc_nro,
                                  admincomerciax_producto.descripcion
                                  """ 
                    if agrupar_por:
                        order_by = """  
                                  admincomerciax_producto.descripcion,
                                  admincomerciax_organismo.siglas_organismo, 
                                  admincomerciax_provincias.descripcion_provincia,
                                  admincomerciax_cliente.nombre,
                                  casco_doc.fecha_doc, 
                                  casco_cc.cc_nro """
                                  
                    resultado_sql= """
                                    SELECT 
                                          casco_doc.fecha_doc, 
                                          casco_cc.cc_nro as doc_nro, 
                                          casco_casco.casco_nro, 
                                          admincomerciax_producto.descripcion, 
                                          admincomerciax_organismo.siglas_organismo, 
                                          admincomerciax_provincias.descripcion_provincia, 
                                          admincomerciax_cliente.nombre
                                        FROM 
                                          casco_doc
                                        inner join   casco_cc on casco_cc.doc_cc_id = casco_doc.id_doc 
                                        inner join   casco_detallecc on casco_detallecc.cc_id = casco_cc.doc_cc_id 
                                        inner join   casco_casco on casco_casco.id_casco = casco_detallecc.casco_id 
                                        inner join   admincomerciax_producto on casco_casco.producto_id = admincomerciax_producto.id 
                                        inner join   casco_detallerc on casco_detallerc.casco_id = casco_detallecc.casco_id 
                                        inner join   casco_recepcioncliente on casco_detallerc.rc_id = casco_recepcioncliente.doc_recepcioncliente_id 
                                        inner join   admincomerciax_cliente on casco_recepcioncliente.cliente_id = admincomerciax_cliente.id
                                        inner join   admincomerciax_organismo on admincomerciax_cliente.organismo_id = admincomerciax_organismo.id
                                        inner join  admincomerciax_provincias on admincomerciax_cliente.provincia_id = admincomerciax_provincias.codigo_provincia 
                                    WHERE """+cade_where+"""
                                    ORDER BY """+order_by
                else:
                    resultado_sql= """
                                    SELECT 
                                      casco_doc.fecha_doc, 
                                      casco_cc.cc_nro AS doc_nro,  
                                      COUNT(casco_detallecc.id_detallecc) AS Cantidad,
                                      admincomerciax_organismo.siglas_organismo, 
                                      admincomerciax_provincias.descripcion_provincia, 
                                      admincomerciax_cliente.nombre
                                    FROM 
                                      casco_doc
                                    inner join   casco_cc on casco_cc.doc_cc_id = casco_doc.id_doc 
                                    inner join   casco_detallecc on casco_detallecc.cc_id = casco_cc.doc_cc_id 
                                    inner join   casco_casco on casco_casco.id_casco = casco_detallecc.casco_id 
                                    inner join   casco_detallerc on casco_detallerc.casco_id = casco_detallecc.casco_id 
                                    inner join   casco_recepcioncliente on casco_detallerc.rc_id = casco_recepcioncliente.doc_recepcioncliente_id 
                                    inner join   admincomerciax_cliente on casco_recepcioncliente.cliente_id = admincomerciax_cliente.id
                                    inner join   admincomerciax_organismo on admincomerciax_cliente.organismo_id = admincomerciax_organismo.id
                                    inner join  admincomerciax_provincias on admincomerciax_cliente.provincia_id = admincomerciax_provincias.codigo_provincia 
                                    WHERE """+cade_where+"""
                                    GROUP BY casco_cc.cc_nro,casco_doc.fecha_doc,casco_recepcioncliente.cliente_id, 
                                                                             admincomerciax_cliente.codigo, admincomerciax_cliente.nombre,admincomerciax_cliente.id, 
                                                                             admincomerciax_provincias.codigo_provincia, admincomerciax_provincias.descripcion_provincia, 
                                                                             admincomerciax_organismo.id, admincomerciax_organismo.codigo_organismo,
                                                                             admincomerciax_organismo.siglas_organismo
                                    ORDER BY
                                      casco_doc.fecha_doc, 
                                      casco_cc.cc_nro, 
                                      admincomerciax_organismo.siglas_organismo, 
                                      admincomerciax_provincias.descripcion_provincia """
            elif mov=='PT':
                cade_where+=" AND (casco_doc.tipo_doc = '9')"
                tipo_doc=9
                encabezado="Enviados de Producción a Producción Terminada"
                #aquiiiii
                if desglose==1:
                    order_by = """  
                                  admincomerciax_organismo.siglas_organismo, 
                                  admincomerciax_provincias.descripcion_provincia,
                                  admincomerciax_cliente.nombre,
                                  casco_doc.fecha_doc, 
                                  casco_produccionterminada.produccionterminada_nro,
                                  admincomerciax_producto.descripcion
                                  """ 
                    if agrupar_por:
                        order_by = """  
                                  admincomerciax_producto.descripcion,
                                  admincomerciax_organismo.siglas_organismo, 
                                  admincomerciax_provincias.descripcion_provincia,
                                  admincomerciax_cliente.nombre,
                                  casco_doc.fecha_doc, 
                                  casco_produccionterminada.produccionterminada_nro,
                                  
                                  """ 
                    resultado_sql= """
                                    SELECT 
                                          casco_doc.fecha_doc, 
                                          casco_produccionterminada.produccionterminada_nro as doc_nro, 
                                          casco_casco.casco_nro, 
                                          admincomerciax_producto.descripcion, 
                                          admincomerciax_organismo.siglas_organismo, 
                                          admincomerciax_provincias.descripcion_provincia, 
                                          admincomerciax_cliente.nombre
                                        FROM 
                                          casco_doc
                                        inner join   casco_produccionterminada on casco_produccionterminada.doc_pt_id = casco_doc.id_doc 
                                        inner join   casco_detallept on casco_detallept.pt_id = casco_produccionterminada.doc_pt_id 
                                        inner join   casco_casco on casco_casco.id_casco = casco_detallept.casco_id 
                                        inner join   admincomerciax_producto on casco_casco.producto_id = admincomerciax_producto.id 
                                        inner join   casco_detallerc on casco_detallerc.casco_id = casco_detallept.casco_id 
                                        inner join   casco_recepcioncliente on casco_detallerc.rc_id = casco_recepcioncliente.doc_recepcioncliente_id 
                                        inner join   admincomerciax_cliente on casco_recepcioncliente.cliente_id = admincomerciax_cliente.id
                                        inner join   admincomerciax_organismo on admincomerciax_cliente.organismo_id = admincomerciax_organismo.id
                                        inner join  admincomerciax_provincias on admincomerciax_cliente.provincia_id = admincomerciax_provincias.codigo_provincia
                                    WHERE """+cade_where+"""
                                    ORDER BY
                                          casco_doc.fecha_doc, 
                                          casco_produccionterminada.produccionterminada_nro, 
                                          admincomerciax_organismo.siglas_organismo, 
                                          admincomerciax_provincias.descripcion_provincia,
                                          admincomerciax_cliente.nombre,
                                          admincomerciax_producto.descripcion,
                                          casco_casco.casco_nro"""
                else:
                    resultado_sql= """
                                    Select casco_doc.fecha_doc, 
                                      casco_produccionterminada.produccionterminada_nro AS doc_nro,  
                                      COUNT(casco_detallept.id_detallept) AS Cantidad,
                                      admincomerciax_organismo.siglas_organismo, 
                                      admincomerciax_provincias.descripcion_provincia, 
                                      admincomerciax_cliente.nombre
                                    FROM 
                                      casco_doc
                                    inner join   casco_produccionterminada on casco_produccionterminada.doc_pt_id = casco_doc.id_doc 
                                    inner join   casco_detallept on casco_detallept.pt_id = casco_produccionterminada.doc_pt_id 
                                    inner join   casco_casco on casco_casco.id_casco = casco_detallept.casco_id 
                                    inner join   casco_detallerc on casco_detallerc.casco_id = casco_detallept.casco_id 
                                    inner join   casco_recepcioncliente on casco_detallerc.rc_id = casco_recepcioncliente.doc_recepcioncliente_id 
                                    inner join   admincomerciax_cliente on casco_recepcioncliente.cliente_id = admincomerciax_cliente.id
                                    inner join   admincomerciax_organismo on admincomerciax_cliente.organismo_id = admincomerciax_organismo.id
                                    inner join  admincomerciax_provincias on admincomerciax_cliente.provincia_id = admincomerciax_provincias.codigo_provincia 
                                    WHERE """+cade_where+"""
                                    GROUP BY casco_produccionterminada.produccionterminada_nro,casco_doc.fecha_doc,casco_recepcioncliente.cliente_id, 
                                                                             admincomerciax_cliente.codigo, admincomerciax_cliente.nombre,admincomerciax_cliente.id, 
                                                                             admincomerciax_provincias.codigo_provincia, admincomerciax_provincias.descripcion_provincia, 
                                                                             admincomerciax_organismo.id, admincomerciax_organismo.codigo_organismo,
                                                                             admincomerciax_organismo.siglas_organismo
                                    ORDER BY
                                      casco_doc.fecha_doc, 
                                      casco_produccionterminada.produccionterminada_nro, 
                                      admincomerciax_organismo.siglas_organismo, 
                                      admincomerciax_provincias.descripcion_provincia """
                
            elif mov=='Decomiso':
                cade_where+=" AND (casco_doc.tipo_doc = '15')"
                tipo_doc=15
                encabezado="Decomiso de Cascos"
                if desglose==1:
                    order_by = """  
                                  admincomerciax_organismo.siglas_organismo, 
                                  admincomerciax_provincias.descripcion_provincia,
                                  admincomerciax_cliente.nombre,
                                  casco_doc.fecha_doc,
                                  casco_casco.casco_nro,
                                  admincomerciax_producto.descripcion
                                  """ 
                    if agrupar_por:
                        order_by = """  
                                  admincomerciax_producto.descripcion,
                                  admincomerciax_organismo.siglas_organismo, 
                                  admincomerciax_provincias.descripcion_provincia,
                                  admincomerciax_cliente.nombre,
                                  casco_doc.fecha_doc,
                                  casco_casco.casco_nro
                                  """ 
                    resultado_sql= """
                                    SELECT 
                                          casco_doc.fecha_doc, 
                                          casco_casco.casco_nro, 
                                          admincomerciax_producto.descripcion, 
                                          admincomerciax_organismo.siglas_organismo, 
                                          admincomerciax_provincias.descripcion_provincia, 
                                          admincomerciax_cliente.nombre
                                        FROM 
                                          casco_doc
                                        inner join   casco_cascodecomiso on casco_cascodecomiso.doc_decomiso_id = casco_doc.id_doc 
                                        inner join   casco_detalle_dc on casco_detalle_dc.doc_decomiso_id = casco_cascodecomiso.doc_decomiso_id 
                                        inner join   casco_casco on casco_casco.id_casco = casco_detalle_dc.casco_id 
                                        inner join   admincomerciax_producto on casco_casco.producto_id = admincomerciax_producto.id 
                                        inner join   casco_detallerc on casco_detallerc.casco_id = casco_detalle_dc.casco_id 
                                        inner join   casco_recepcioncliente on casco_detallerc.rc_id = casco_recepcioncliente.doc_recepcioncliente_id 
                                        inner join   admincomerciax_cliente on casco_recepcioncliente.cliente_id = admincomerciax_cliente.id
                                        inner join   admincomerciax_organismo on admincomerciax_cliente.organismo_id = admincomerciax_organismo.id
                                        inner join  admincomerciax_provincias on admincomerciax_cliente.provincia_id = admincomerciax_provincias.codigo_provincia
                                    WHERE """+cade_where+"""
                                    ORDER BY  """+order_by
                else:
                    resultado_sql= """
                                    Select 
                                          casco_doc.fecha_doc, 
                                          COUNT(casco_detalle_dc.id_detalledc) AS Cantidad,
                                          admincomerciax_organismo.siglas_organismo, 
                                          admincomerciax_provincias.descripcion_provincia, 
                                          admincomerciax_cliente.nombre
                                        FROM 
                                          casco_doc
                                        inner join   casco_cascodecomiso on casco_cascodecomiso.doc_decomiso_id = casco_doc.id_doc 
                                        inner join   casco_detalle_dc on casco_detalle_dc.doc_decomiso_id = casco_cascodecomiso.doc_decomiso_id 
                                        inner join   casco_casco on casco_casco.id_casco = casco_detalle_dc.casco_id 
                                        inner join   casco_detallerc on casco_detallerc.casco_id = casco_detalle_dc.casco_id 
                                        inner join   casco_recepcioncliente on casco_detallerc.rc_id = casco_recepcioncliente.doc_recepcioncliente_id 
                                        inner join   admincomerciax_cliente on casco_recepcioncliente.cliente_id = admincomerciax_cliente.id
                                        inner join   admincomerciax_organismo on admincomerciax_cliente.organismo_id = admincomerciax_organismo.id
                                        inner join  admincomerciax_provincias on admincomerciax_cliente.provincia_id = admincomerciax_provincias.codigo_provincia
                                    WHERE """+cade_where+"""
                                    GROUP BY casco_doc.fecha_doc,casco_recepcioncliente.cliente_id, 
                                             admincomerciax_cliente.codigo, admincomerciax_cliente.nombre,admincomerciax_cliente.id, 
                                             admincomerciax_provincias.codigo_provincia, admincomerciax_provincias.descripcion_provincia, 
                                             admincomerciax_organismo.id, admincomerciax_organismo.codigo_organismo,
                                             admincomerciax_organismo.siglas_organismo
                                    ORDER BY
                                          casco_doc.fecha_doc, 
                                          admincomerciax_organismo.siglas_organismo, 
                                          admincomerciax_provincias.descripcion_provincia,
                                          admincomerciax_cliente.nombre
                                        """
                
            
            resultado = query_to_dicts(resultado_sql)
            resultado_pdf=[]    
                             
            queryset=[]
            
            if request.POST.__contains__('submit1') or request.POST.__contains__('submit2'):
                if tipo_doc==2 or tipo_doc==9 or tipo_doc==15:
                     
                    if desglose==1:
                        for fila in resultado:
                            nro="" if tipo_doc==15 else fila['doc_nro']
                            resultado_pdf=resultado_pdf+[{'cliente':fila['siglas_organismo']+" - "+fila['descripcion_provincia']+" - "+fila['nombre'] if not agrupar_por else fila['nombre'],
                                                          'organismo':fila['siglas_organismo'],'provincia':fila['descripcion_provincia'],
                                                          'fecha_doc':fila['fecha_doc'].strftime("%d/%m/%Y"),'nro_doc':nro,
                                    'medida':fila['descripcion'],'nro_casco':fila['casco_nro'], 'cantidad': 1}]
                    else:
                        for fila in resultado:
                            nro="" if tipo_doc==15 else fila['doc_nro']
                            resultado_pdf=resultado_pdf+[{'cliente':fila['siglas_organismo']+" - "+fila['descripcion_provincia']+" - "+fila['nombre'],'fecha_doc':fila['fecha_doc'].strftime("%d/%m/%Y"),'nro_doc':nro,
                                                         'cantidad':fila['cantidad']}]
                    
                else:
                    if desglose==1:
                        for fila in resultado:
                            resultado_pdf=resultado_pdf+[{'cliente':fila['nombre'],'fecha_doc':fila['fecha_doc'].strftime("%d/%m/%Y"),'nro_doc':fila['doc_nro'],'provincia':fila['descripcion_provincia'],'organismo':fila['siglas_organismo'],
                                    'medida':fila['descripcion'],'cantidad':fila['cantidad'],'importe':fila['mn']+fila['mn1']}]
                    else:
                        for fila in resultado:
                            resultado_pdf=resultado_pdf+[{'cliente':fila['nombre'],'fecha_doc':fila['fecha_doc'].strftime("%d/%m/%Y"),'nro_doc':fila['doc_nro'],'provincia':fila['descripcion_provincia'],'organismo':fila['siglas_organismo'],
                                    'cantidad':fila['cantidad'],'importe':fila['mn']+fila['mn1']}]
                if resultado_pdf.__len__()==0:                              
                    mesg=mesg+['No existe información para mostrar']
                    return render_to_response("comercial/reporteindex.html",{'vprev':1,'form':form,'title':titulo_form, 'form_name':nombre_form,'form_description':descripcion_form,
                                                                   'controlador':controlador_form,'accion':accion_form,'error2':mesg,'email':1},context_instance = RequestContext(request))
                if desglose==1:
                    if tipo_doc==1:
                        if agrupar_por:
                            repo=report_class.Reportes.Mov_CascosDesgxMed(report_class.Reportes() , resultado_pdf, encabezado ,pdf_file_name,filtro)
                        else:   
                            repo=report_class.Reportes.Mov_CascosDesg(report_class.Reportes() , resultado_pdf, encabezado ,pdf_file_name,filtro)
                    elif tipo_doc==14:
                        if agrupar_por:
                            repo=report_class.Reportes.Mov_CascosDesgxMed(report_class.Reportes() , resultado_pdf, encabezado ,pdf_file_name,filtro)
                        else:
                            repo=report_class.Reportes.Mov_FactDesg(report_class.Reportes() , resultado_pdf, encabezado ,pdf_file_name,filtro)
                    elif tipo_doc==2 or tipo_doc==9 or tipo_doc==15:
                        if agrupar_por:
                            repo=report_class.Reportes.Mov_CascosDesgxMed(report_class.Reportes() , resultado_pdf, encabezado ,pdf_file_name,filtro)
                        else: 
                            repo=report_class.Reportes.Mov_ProdDesg(report_class.Reportes() , resultado_pdf, encabezado ,pdf_file_name,filtro)
                        
                else:
                    if tipo_doc==1:
                        repo=report_class.Reportes.Mov_Cascos(report_class.Reportes() , resultado_pdf, encabezado ,pdf_file_name,filtro)
                    elif tipo_doc==14:
                        repo=report_class.Reportes.Mov_Fact(report_class.Reportes() , resultado_pdf, encabezado ,pdf_file_name,filtro)
                    elif tipo_doc==2 or tipo_doc==9 or tipo_doc==15:
                        repo=report_class.Reportes.Mov_Prod(report_class.Reportes() , resultado_pdf, encabezado ,pdf_file_name,filtro)
                if repo==0:
#                if report_class.Reportes.GenerarRep(report_class.Reportes() , resultado_pdf, "mov_casco",pdf_file_name,filtro)==0:
                    mesg=mesg+['Debe cerrar el documento Movimiento de Cascos.pdf']
                    return render_to_response("comercial/reporteindex.html",{'vprev':1,'filtro':filtro,'resultado':resultado,'form':form,'title':titulo_form, 'form_name':nombre_form,'form_description':descripcion_form,
                                                        'controlador':controlador_form,'accion':accion_form,'error2':mesg,'email':1},context_instance = RequestContext(request))
                else:
                    input = PdfFileReader(file(pdf_file_name,"rb"))
                    output = PdfFileWriter()
                    for page in input.pages:
                        output.addPage(page)
                    buffer = StringIO.StringIO()
                    output.write(buffer)
                    response = HttpResponse(mimetype='application/pdf')
                    file_namesitio='%s'%(pdf_file_name)
                    response['Content-Disposition'] = 'attachment; filename=%s'%(pdf_file_name)
                    response.write(buffer.getvalue())
                    if envia:
                        import smtplib
                        from email.mime.application import MIMEApplication
                        from django.core.mail.message import EmailMessage
                        try:
                            message = EmailMessage(subject='Movimiento de Cascos',body='Enviado por '+request.user.first_name+' '+request.user.last_name, from_email=correo_envia, to=[correo])
                            part = MIMEApplication(open(file_namesitio,"rb").read())
                            part.add_header('Content-Disposition', 'attachment', filename="Facturas por Cobrar.pdf")
                            message.attach(part)
                            if ssl==True:
                                smtp = smtplib.SMTP_SSL(host=servidor,port=puerto)
                            else:
                                smtp = smtplib.SMTP(servidor)
                            smtp.ehlo()
                            smtp.login(correo_envia,contrasena)
                            smtp.sendmail(correo_envia,[correo],message.message().as_string())
                            smtp.close()
                            return response         
                        except Exception, e:
                            mesg=mesg+['Error de conexión. Revise la configuración del Correo SMTP']
                            return render_to_response("comercial/reporteindex.html",{'vprev':1,'filtro':filtro,'resultado':resultado,'form':form,'title':titulo_form, 'form_name':nombre_form,'form_description':descripcion_form,
                                                    'controlador':controlador_form,'accion':accion_form,'error2':mesg,'email':1},context_instance = RequestContext(request))
                    return response
    form = MovCascos() 
    
    return render_to_response("comercial/reporteindex.html",{'vprev':1,'form':form,'title':titulo_form, 'form_name':nombre_form,'form_description':descripcion_form,
                                                                'controlador':controlador_form,'accion':accion_form,'error2':mesg,'email':1},context_instance = RequestContext(request))

@login_required
def repplanes(request):
    
    nombre_form='Planes Contratados'
    descripcion_form='Planes Contratados'
    titulo_form='Planes Contratados' 
    controlador_form='Planes '
    accion_form=''
    mesg=[]
    
    mesg=[]
    if request.method == 'POST':
        form = RepPlanes(request.POST)
        
        if form.is_valid():

            cliente=form.cleaned_data['ccliente']
            organismo=form.cleaned_data['organismo']
            provincia=form.cleaned_data['provincia']
            ano=form.cleaned_data['ano']
            envia=False
            seleccion = form.cleaned_data['seleccion']
            desglose=1 if seleccion=="Si" else 0
            pdf_file_name=os.path.join(comerciax.settings.ADMIN_MEDIA_PDF,"Planes Contratados.pdf")
            
            
            filtro=[]
            cade_where="admincomerciax_cliente.eliminado = False"
            filtro.append('Año: '+str(ano))
            if desglose==1:
                filtro.append('Planes Contratados')
            else:
                filtro.append('Planes No Contratados')
            
            if organismo!=None:
                filtro.append('Organismo: '+organismo.siglas_organismo)
                cade_where+=" AND (admincomerciax_organismo.id='"+organismo.id+"')"
            
            if provincia!=None:
                filtro.append('Provincia: '+provincia.descripcion_provincia)
                cade_where+=" AND (admincomerciax_provincias.codigo_provincia='"+provincia.codigo_provincia+"')"
                
            if cliente!=None:
                filtro.append('Cliente: '+cliente.nombre)
                cade_where+=" AND (admincomerciax_cliente.id='"+cliente.id+"')"
            
            encabezado=""
            
            resultado_sql="""
                SELECT admincomerciax_organismo.siglas_organismo, admincomerciax_provincias.descripcion_provincia, 
                   admincomerciax_cliente.nombre, admincomerciax_planes.plan_contratado, admincomerciax_planes.plan_ano, 
                   admincomerciax_clientecontrato.contrato_id, admincomerciax_cliente.id, admincomerciax_cliente.eliminado, 
                   admincomerciax_cliente.organismo_id, admincomerciax_cliente.provincia_id,admincomerciax_contrato.contrato_nro
             FROM  admincomerciax_planes INNER JOIN
                               admincomerciax_clientecontrato ON admincomerciax_planes.contrato_id = admincomerciax_clientecontrato.contrato_id AND 
                               admincomerciax_planes.plan_ano = """ + str(ano)+""" RIGHT OUTER JOIN
                               admincomerciax_organismo INNER JOIN
                               admincomerciax_cliente ON admincomerciax_organismo.id = admincomerciax_cliente.organismo_id INNER JOIN
                               admincomerciax_provincias ON admincomerciax_cliente.provincia_id = admincomerciax_provincias.codigo_provincia ON 
                               admincomerciax_clientecontrato.cliente_id = admincomerciax_cliente.id LEFT OUTER JOIN
                               admincomerciax_contrato ON admincomerciax_clientecontrato.contrato_id=admincomerciax_contrato.id_contrato
                 WHERE """+cade_where+"""
                ORDER BY admincomerciax_organismo.siglas_organismo, 
                         admincomerciax_provincias.descripcion_provincia,
                         admincomerciax_cliente.nombre 
            """
#            print resultado_sql
            resultado = query_to_dicts(resultado_sql)
            resultado_pdf=[]    
                             
            queryset=[]
            
            if request.POST.__contains__('submit1'):
                if desglose==1:
                    for fila in resultado:
                        if fila['plan_ano']!=None:
                            resultado_pdf=resultado_pdf+[{'organismo':fila['siglas_organismo'],
                                                          'provincia':fila['descripcion_provincia'],
                                                          'cliente':fila['nombre'],'plan_ano':fila['plan_contratado'],
                                                          'contrato_nro':fila['contrato_nro']}]
                else:
                    for fila in resultado:
                        if fila['plan_ano']==None:
                            resultado_pdf=resultado_pdf+[{'organismo':fila['siglas_organismo'],
                                                          'provincia':fila['descripcion_provincia'],
                                                          'cliente':fila['nombre'],
                                                          'plan_ano':'-',
                                                          'contrato_nro':""}]
                if resultado_pdf.__len__()==0:                              
                    mesg=mesg+['No existe información para mostrar']
                    return render_to_response("comercial/reporteindex.html",{'vprev':1,'form':form,'title':titulo_form, 'form_name':nombre_form,'form_description':descripcion_form,
                                                                   'controlador':controlador_form,'accion':accion_form,'error2':mesg,'email':0},context_instance = RequestContext(request))
                if desglose==1:
                    repo=report_class.Reportes.GenerarRep(report_class.Reportes() , resultado_pdf, "rep_planes",pdf_file_name,filtro)
                else:
                    repo=report_class.Reportes.GenerarRep(report_class.Reportes() , resultado_pdf, "rep_planesnocontrat",pdf_file_name,filtro)
                if repo==0:
                    mesg=mesg+['Debe cerrar el documento Planes Contratados.pdf']
                    return render_to_response("comercial/reporteindex.html",{'vprev':1,'filtro':filtro,'resultado':resultado,'form':form,'title':titulo_form, 'form_name':nombre_form,'form_description':descripcion_form,
                                                        'controlador':controlador_form,'accion':accion_form,'error2':mesg,'email':1},context_instance = RequestContext(request))
                else:
                    input = PdfFileReader(file(pdf_file_name,"rb"))
                    output = PdfFileWriter()
                    for page in input.pages:
                        output.addPage(page)
                    buffer = StringIO.StringIO()
                    output.write(buffer)
                    response = HttpResponse(mimetype='application/pdf')
                    file_namesitio='%s'%(pdf_file_name)
                    response['Content-Disposition'] = 'attachment; filename=%s'%(pdf_file_name)
                    response.write(buffer.getvalue())
                    return response
          
    form = RepPlanes() 
    
    return render_to_response("comercial/reporteindex.html",{'vprev':1,'form':form,'title':titulo_form, 'form_name':nombre_form,'form_description':descripcion_form,
                                                                'controlador':controlador_form,'accion':accion_form,'error2':mesg,'email':0},context_instance = RequestContext(request))

@login_required
def cascosptcantidad(request):
    
    nombre_form='Cascos en PT por cantidad'
    descripcion_form='Cascos en PT por cantidad'
    titulo_form='Cascos en PT por cantidad' 
    controlador_form='Cascos en PT '
    accion_form=''
    mesg=[]
    if request.method == 'POST':
        form = RepPTCantidad(request.POST)
        
        if form.is_valid():

            cliente=form.cleaned_data['ccliente']
            organismo=form.cleaned_data['organismo']
            provincia=form.cleaned_data['provincia']
            cantidad=form.cleaned_data['cantidad']
            medida=form.cleaned_data['medida']
            envia=False
            seleccion = form.cleaned_data['seleccion']
            desglose=1 if seleccion=="Si" else 0
            pdf_file_name=os.path.join(comerciax.settings.ADMIN_MEDIA_PDF,"Cascos en PT por Cantidad.pdf")
            
            filtro=[]
            cade_where=" AND casco_casco.estado_actual='PT' "
            filtro.append('Más de : '+str(cantidad)+" cascos")
            if desglose==1:
                filtro.append('Desglosado por medida')
            else:
                filtro.append('Sin desglose por medida')
            if organismo!=None:
                filtro.append('Organismo: '+organismo.siglas_organismo)
                cade_where+=" AND (admincomerciax_organismo.id='"+organismo.id+"')"
            
            if provincia!=None:
                filtro.append('Provincia: '+provincia.descripcion_provincia)
                cade_where+=" AND (admincomerciax_provincias.codigo_provincia='"+provincia.codigo_provincia+"')"
                
            if cliente!=None:
                filtro.append('Cliente: '+cliente.nombre)
                cade_where+=" AND (admincomerciax_cliente.id='"+cliente.id+"')"
                
            if medida!=None:
                filtro.append('Medida: '+medida.descripcion)
                cade_where+=" AND (admincomerciax_producto.id='"+medida.id+"')"
                
            
            encabezado=""
            if desglose==1:
                resultado_sql = """
                  SELECT princ.siglas_organismo, 
                      princ.descripcion_provincia, 
                      princ.nombre, 
                      princ.descripcion, 
                      sum(princ.cantidad) as cantidad,
                      princ.precio_mn,
                      sum(princ.importe) as importe  from 
                    ((SELECT
                      admincomerciax_organismo.siglas_organismo, 
                      admincomerciax_provincias.descripcion_provincia, 
                      admincomerciax_cliente.nombre, 
                      admincomerciax_producto.descripcion, 
                      count(admincomerciax_producto.descripcion) as cantidad,
                      admincomerciax_producto.precio_mn,
                      admincomerciax_producto.precio_mn*count (admincomerciax_producto.descripcion) as importe
                    FROM 
                         public.casco_casco
                      inner join admincomerciax_producto on casco_casco.producto_salida_id = admincomerciax_producto.id 
                      inner join casco_detallept on casco_detallept.casco_id = casco_casco.id_casco 
                      inner join casco_produccionterminada on casco_detallept.pt_id = casco_produccionterminada.doc_pt_id 
                      inner join casco_doc on casco_produccionterminada.doc_pt_id = casco_doc.id_doc 
                      inner join casco_detallerc on casco_detallerc.casco_id = casco_casco.id_casco 
                      inner join casco_recepcioncliente on casco_detallerc.rc_id = casco_recepcioncliente.doc_recepcioncliente_id 
                      inner join admincomerciax_cliente on casco_recepcioncliente.cliente_id = admincomerciax_cliente.id
                      inner join admincomerciax_organismo on admincomerciax_cliente.organismo_id = admincomerciax_organismo.id 
                      inner join admincomerciax_provincias on admincomerciax_cliente.provincia_id = admincomerciax_provincias.codigo_provincia 
                    group by
                      admincomerciax_organismo.siglas_organismo,
                      admincomerciax_provincias.codigo_provincia,
                      admincomerciax_cliente.id,
                      casco_casco.estado_actual,
                      admincomerciax_organismo.id,
                      admincomerciax_provincias.descripcion_provincia, 
                      admincomerciax_cliente.nombre, 
                      admincomerciax_producto.precio_mn,admincomerciax_producto.descripcion,admincomerciax_producto.id
                    having count(admincomerciax_producto.descripcion)>="""+str(cantidad)+cade_where+""")
                     union
                     (SELECT
                      admincomerciax_organismo.siglas_organismo, 
                      admincomerciax_provincias.descripcion_provincia, 
                      admincomerciax_cliente.nombre, 
                      admincomerciax_producto.descripcion, 
                      count(admincomerciax_producto.descripcion) as cantidad,
                      admincomerciax_producto.precio_mn,
                      admincomerciax_producto.precio_mn*count (admincomerciax_producto.descripcion) as importe
                    FROM 
                         public.casco_casco
                      inner join admincomerciax_producto on casco_casco.producto_salida_id = admincomerciax_producto.id 
                      inner join casco_detallepte on casco_detallepte.casco_id = casco_casco.id_casco 
                      inner join casco_ptexternos on casco_detallepte.doc_pte_id = casco_ptexternos.doc_ptexternos_id 
                      inner join casco_doc on casco_ptexternos.doc_ptexternos_id = casco_doc.id_doc 
                      inner join casco_detallerc on casco_detallerc.casco_id = casco_casco.id_casco 
                      inner join casco_recepcioncliente on casco_detallerc.rc_id = casco_recepcioncliente.doc_recepcioncliente_id 
                      inner join admincomerciax_cliente on casco_recepcioncliente.cliente_id = admincomerciax_cliente.id
                      inner join admincomerciax_organismo on admincomerciax_cliente.organismo_id = admincomerciax_organismo.id 
                      inner join admincomerciax_provincias on admincomerciax_cliente.provincia_id = admincomerciax_provincias.codigo_provincia 
                    group by
                      admincomerciax_organismo.siglas_organismo,
                      admincomerciax_provincias.codigo_provincia,
                      admincomerciax_cliente.id,
                      casco_casco.estado_actual,
                      admincomerciax_organismo.id, 
                      admincomerciax_provincias.descripcion_provincia, 
                      admincomerciax_cliente.nombre, 
                      admincomerciax_producto.precio_mn,admincomerciax_producto.descripcion,admincomerciax_producto.id
                    having count(admincomerciax_producto.descripcion)>="""+str(cantidad)+cade_where+""")) as princ
                    group by 
                      princ.siglas_organismo, 
                      princ.descripcion_provincia, 
                      princ.nombre,
                      princ.descripcion,
                      princ.precio_mn
                    order by 
                      princ.siglas_organismo, 
                      princ.descripcion_provincia, 
                      princ.nombre, 
                      princ.descripcion
                """
            else:
                resultado_sql = """
                  SELECT princ.siglas_organismo, 
                      princ.descripcion_provincia, 
                      princ.nombre, 
                      sum(princ.cantidad) as cantidad,
                      sum(princ.importe) as importe  from 
                    ((SELECT
                      admincomerciax_organismo.siglas_organismo, 
                      admincomerciax_provincias.descripcion_provincia, 
                      admincomerciax_cliente.nombre, 
                      admincomerciax_producto.descripcion, 
                      count(admincomerciax_producto.descripcion) as cantidad,
                      admincomerciax_producto.precio_mn,
                      admincomerciax_producto.precio_mn*count (admincomerciax_producto.descripcion) as importe
                    FROM 
                         public.casco_casco
                      inner join admincomerciax_producto on casco_casco.producto_salida_id = admincomerciax_producto.id 
                      inner join casco_detallept on casco_detallept.casco_id = casco_casco.id_casco 
                      inner join casco_produccionterminada on casco_detallept.pt_id = casco_produccionterminada.doc_pt_id 
                      inner join casco_doc on casco_produccionterminada.doc_pt_id = casco_doc.id_doc 
                      inner join casco_detallerc on casco_detallerc.casco_id = casco_casco.id_casco 
                      inner join casco_recepcioncliente on casco_detallerc.rc_id = casco_recepcioncliente.doc_recepcioncliente_id 
                      inner join admincomerciax_cliente on casco_recepcioncliente.cliente_id = admincomerciax_cliente.id
                      inner join admincomerciax_organismo on admincomerciax_cliente.organismo_id = admincomerciax_organismo.id 
                      inner join admincomerciax_provincias on admincomerciax_cliente.provincia_id = admincomerciax_provincias.codigo_provincia 
                    group by
                      admincomerciax_provincias.codigo_provincia,
                      admincomerciax_cliente.id,
                      casco_casco.estado_actual,
                      admincomerciax_organismo.id,
                      admincomerciax_organismo.siglas_organismo, 
                      admincomerciax_provincias.descripcion_provincia, 
                      admincomerciax_cliente.nombre, 
                      admincomerciax_producto.precio_mn,admincomerciax_producto.descripcion,admincomerciax_producto.id
                    having count(admincomerciax_producto.descripcion)>="""+str(cantidad)+cade_where+""")
                     union
                     (SELECT
                      admincomerciax_organismo.siglas_organismo, 
                      admincomerciax_provincias.descripcion_provincia, 
                      admincomerciax_cliente.nombre, 
                      admincomerciax_producto.descripcion, 
                      count(admincomerciax_producto.descripcion) as cantidad,
                      admincomerciax_producto.precio_mn,
                      admincomerciax_producto.precio_mn*count (admincomerciax_producto.descripcion) as importe
                    FROM 
                         public.casco_casco
                      inner join admincomerciax_producto on casco_casco.producto_salida_id = admincomerciax_producto.id 
                      inner join casco_detallepte on casco_detallepte.casco_id = casco_casco.id_casco 
                      inner join casco_ptexternos on casco_detallepte.doc_pte_id = casco_ptexternos.doc_ptexternos_id 
                      inner join casco_doc on casco_ptexternos.doc_ptexternos_id = casco_doc.id_doc 
                      inner join casco_detallerc on casco_detallerc.casco_id = casco_casco.id_casco 
                      inner join casco_recepcioncliente on casco_detallerc.rc_id = casco_recepcioncliente.doc_recepcioncliente_id 
                      inner join admincomerciax_cliente on casco_recepcioncliente.cliente_id = admincomerciax_cliente.id
                      inner join admincomerciax_organismo on admincomerciax_cliente.organismo_id = admincomerciax_organismo.id 
                      inner join admincomerciax_provincias on admincomerciax_cliente.provincia_id = admincomerciax_provincias.codigo_provincia 
                    group by
                      casco_casco.estado_actual,
                      admincomerciax_organismo.id,
                      admincomerciax_organismo.siglas_organismo, 
                      admincomerciax_provincias.codigo_provincia,
                      admincomerciax_cliente.id,
                      admincomerciax_provincias.descripcion_provincia, 
                      admincomerciax_cliente.nombre, 
                      admincomerciax_producto.precio_mn,admincomerciax_producto.descripcion,admincomerciax_producto.id
                    having count(admincomerciax_producto.descripcion)>="""+str(cantidad)+cade_where+""")) as princ
                    group by 
                      princ.siglas_organismo, 
                      princ.descripcion_provincia, 
                      princ.nombre
                    order by 
                      princ.siglas_organismo, 
                      princ.descripcion_provincia, 
                      princ.nombre
                """
#            print resultado_sql
            resultado = query_to_dicts(resultado_sql)
            resultado_pdf=[]    
                             
            queryset=[]
            
            if request.POST.__contains__('submit1'):
                if desglose==1:
                    for fila in resultado:
                        resultado_pdf=resultado_pdf+[{'organismo':fila['siglas_organismo'],
                                                      'provincia':fila['descripcion_provincia'],
                                                      'cliente':fila['nombre'],'cantidad':fila['cantidad'],
                                                      'precio':fila['precio_mn'],
                                                      'importe':fila['importe'],
                                                      'medida':fila['descripcion']}]
                else:
                    for fila in resultado:
                        resultado_pdf=resultado_pdf+[{'organismo':fila['siglas_organismo'],
                                                      'provincia':fila['descripcion_provincia'],
                                                      'cliente':fila['nombre'],'cantidad':fila['cantidad'],
                                                      'importe':fila['importe']}]
                if resultado_pdf.__len__()==0:                              
                    mesg=mesg+['No existe información para mostrar']
                    return render_to_response("comercial/reporteindex.html",{'vprev':1,'form':form,'title':titulo_form, 'form_name':nombre_form,'form_description':descripcion_form,
                                                                   'controlador':controlador_form,'accion':accion_form,'error2':mesg,'email':0},context_instance = RequestContext(request))
                if desglose==1:
                    repo=report_class.Reportes.GenerarRep(report_class.Reportes() , resultado_pdf, "rep_ptcantdesg",pdf_file_name,filtro)
                else:
                    repo=report_class.Reportes.GenerarRep(report_class.Reportes() , resultado_pdf, "rep_ptcantnodesg",pdf_file_name,filtro)
                if repo==0:
                    mesg=mesg+['Debe cerrar el documento Cascos en PT por Cantidad.pdf']
                    return render_to_response("comercial/reporteindex.html",{'vprev':1,'filtro':filtro,'resultado':resultado,'form':form,'title':titulo_form, 'form_name':nombre_form,'form_description':descripcion_form,
                                                        'controlador':controlador_form,'accion':accion_form,'error2':mesg,'email':1},context_instance = RequestContext(request))
                else:
                    input = PdfFileReader(file(pdf_file_name,"rb"))
                    output = PdfFileWriter()
                    for page in input.pages:
                        output.addPage(page)
                    buffer = StringIO.StringIO()
                    output.write(buffer)
                    response = HttpResponse(mimetype='application/pdf')
                    file_namesitio='%s'%(pdf_file_name)
                    response['Content-Disposition'] = 'attachment; filename=%s'%(pdf_file_name)
                    response.write(buffer.getvalue())
                    return response
          
    form = RepPTCantidad() 
    
    return render_to_response("comercial/reporteindex.html",{'vprev':1,'form':form,'title':titulo_form, 'form_name':nombre_form,'form_description':descripcion_form,
                                                                'controlador':controlador_form,'accion':accion_form,'error2':mesg,'email':0},context_instance = RequestContext(request))


@login_required
def conciliacion(request):
    # sql = query_to_dicts(""" TODO ESTO ES PARA PONER EL CLIENTE EN CASCO EL QUE LE DIO ENTRADA
    #     SELECT
	# 	      casco_casco.id_casco,
	# 	      casco_recepcioncliente.cliente_id as rc_id_cliente,
    #                   (select casco_recepcioncliente.cliente_id from casco_detallerc
	# 		 inner join casco_recepcioncliente on casco_recepcioncliente.doc_recepcioncliente_id = casco_detallerc.rc_id
	# 		 where casco_id=casco_casco.id_casco) as cliente_recepcion
    #                 FROM
    #                   public.casco_casco
    #                 inner join public.casco_detallerc on casco_detallerc.casco_id = casco_casco.id_casco
    #                 left outer join public.casco_recepcioncliente on casco_recepcioncliente.cliente_id = casco_casco.id_cliente_id
    #                 inner join admincomerciax_cliente on casco_casco.id_cliente_id=admincomerciax_cliente.id
    #                 inner join admincomerciax_organismo on admincomerciax_organismo.id=admincomerciax_cliente.organismo_id
    #                 inner join admincomerciax_provincias on admincomerciax_provincias.codigo_provincia=admincomerciax_cliente.provincia_id
    #                 WHERE
    #                    casco_casco.estado_actual in ('Casco','Produccion','PT','Transferencia','DVP','DIP','ER','REE')
    #                    and casco_recepcioncliente.cliente_id is null
    #                 order by admincomerciax_organismo.siglas_organismo,admincomerciax_provincias.descripcion_provincia,
    #                 admincomerciax_cliente.nombre
    # """)
    # for k in sql:
    #     c = Casco.objects.get(id_casco=k['id_casco'])
    #     c.id_cliente_id=k['cliente_recepcion']
    #     c.save()

    nombre_form='Reportes'
    descripcion_form='Conciliación'
    titulo_form='Conciliación' 
    controlador_form='Reportes'
    accion_form='/comerciax/comercial/conciliacion/reporte'
    mesg=[]
    
    
    if request.method == 'POST':
        form = Fconciliacion(request.POST)
        
        if form.is_valid():
            envia=False
            fecha_cierre=Fechacierre.objects.get(almacen='cm')
            mes_inicio = fecha_cierre.mes
            ano_inicio = fecha_cierre.year
            mes_dato=mes_inicio+1
            ano_dato = ano_inicio
            if mes_inicio==12:
                mes_dato=1
                ano_dato = ano_inicio+1
            
            fecha_datos=str(ano_dato)+"-"+str(mes_dato)+"-1"
            cliente=form.cleaned_data['ccliente']
            organismo=form.cleaned_data['organismo']
            provincia=form.cleaned_data['provincia']
            if request.POST.__contains__('submit2'):
                envia=True
                if cliente==None:
                    mesg=mesg+['Debe seleccionar un cliente']
                    return render_to_response("comercial/reporteindex.html",{'vprev':1,'form':form,'title':titulo_form, 'form_name':nombre_form,'form_description':descripcion_form,
                                                                    'controlador':controlador_form,'accion':accion_form,'error2':mesg,'email':1},context_instance = RequestContext(request))
                correo=cliente.email
                if correo.__len__()==0:
                    mesg=mesg+['Este cliente no tiene correo']
                    return render_to_response("comercial/reporteindex.html",{'vprev':1,'form':form,'title':titulo_form, 'form_name':nombre_form,'form_description':descripcion_form,
                                                                   'controlador':controlador_form,'accion':accion_form,'error2':mesg,'email':1},context_instance = RequestContext(request))
                try:
                    querySet = Config_SMTPEmail.objects.get()
                except Exception, e:
                    mesg=mesg+['No está configurado el correo SMTP']
                    return render_to_response("comercial/reporteindex.html",{'vprev':1,'form':form,'title':titulo_form, 'form_name':nombre_form,'form_description':descripcion_form,
                                                                   'controlador':controlador_form,'accion':accion_form,'error2':mesg,'email':1},context_instance = RequestContext(request))
                servidor=querySet.servidor
                correo_envia=querySet.correo
                puerto = querySet.puerto
                ssl = querySet.ssl
                try:
                    contrasena = base64.b64decode(querySet.contrasena)
                except Exception, e:
                    mesg=mesg+['Revise la contraseña en la configuración del Correo SMTP']
                    return render_to_response("comercial/reporteindex.html",{'vprev':1,'form':form,'title':titulo_form, 'form_name':nombre_form,'form_description':descripcion_form,
                                                                   'controlador':controlador_form,'accion':accion_form,'error2':mesg,'email':1},context_instance = RequestContext(request))
            filtro=[]
            where=[]
            
#            resultado=Casco.objects.select_related().all().order_by('estado_actual','admincomerciax_producto.descripcion')
            if cliente!=None:
                where.append("admincomerciax_cliente.id='"+cliente.id+"'")
                filtro.append('Cliente: '+cliente.nombre)
            else:
                if organismo!=None:
                    where.append("siglas_organismo='"+organismo.siglas_organismo+"'")
                    filtro.append('Organismo: '+organismo.siglas_organismo)
                if provincia!=None:
                    where.append("codigo_provincia='"+provincia.codigo_provincia+"'")
                    filtro.append('Provincia: '+provincia.descripcion_provincia)
            estado=False                    
                
            optwhere=" AND " if len(where)>0 else ""               
            for a1 in range(len(where)):
                optwhere+= where[a1]+ " AND "
            long=len(optwhere)
            optwhere=optwhere[0:long-4]
            opt=str(optwhere)
            lista_cli=[]
            resultado1= """
            SELECT 
                  admincomerciax_organismo.siglas_organismo, admincomerciax_organismo.id as id_organismo,
                  admincomerciax_provincias.descripcion_provincia,admincomerciax_provincias.codigo_provincia,
                  admincomerciax_cliente.nombre,admincomerciax_cliente.id,
                  admincomerciax_clientecontrato.contrato_id,
                  case when comercial_invcliente.cantidad is NULL
                           then 0
                           else comercial_invcliente.cantidad
                      end as inicio
                FROM 
                  public.admincomerciax_cliente
                left outer join comercial_invcliente on admincomerciax_cliente.id =comercial_invcliente.cliente_id AND 
                comercial_invcliente.mes="""+str(mes_inicio)+""" AND  
                comercial_invcliente.year="""+str(ano_inicio)+"""
                inner join admincomerciax_organismo on admincomerciax_cliente.organismo_id=admincomerciax_organismo.id
                inner join admincomerciax_provincias on admincomerciax_cliente.provincia_id=admincomerciax_provincias.codigo_provincia
                left outer join admincomerciax_clientecontrato on admincomerciax_cliente.id =admincomerciax_clientecontrato.cliente_id and admincomerciax_clientecontrato.cerrado=False
                WHERE  admincomerciax_cliente.eliminado = False  """+opt+"""
                order by admincomerciax_organismo.siglas_organismo,admincomerciax_provincias.descripcion_provincia,
                admincomerciax_cliente.nombre
            """
            resultados = query_to_dicts(resultado1)
            dic_cli={}
            for datos in resultados:
                dic_cli[datos['id']]={'Inicio':datos['inicio'],
                                    'Organismo':datos['siglas_organismo'],
                                    'Provincia':datos['descripcion_provincia'],
                                    'Cliente':datos['nombre'],
                                    'Entregados':0,
                                    'Casco': 0,
                                    'Produccion':0,
                                    'PTer':0,
                                    'Transferencia':0,
                                    'DIP':0, #Devuelto a Inservible
                                    'DVP':0, #Devuelto a Vulca
                                    'ER':0, #Rechazado por error revision
                                    'ECR':0, #Casco Rechazado Entregado
                                    'REE':0, #Rechazado por Entidad Externa
                                    'Factura':0, #Facturado
                                    'Deco':0,      #Casco Decomisado
                                    'DCC':0,     #Devuelto al Cliente
                                    'Devoluc':0, # ECR+DCC
                                    'Inserv':0   #DIP+ER+REE
                                }
                lista_cli.append(datos['id'])
                
            sql_entradas="""
            SELECT 
                  casco_recepcioncliente.cliente_id,admincomerciax_organismo.siglas_organismo,admincomerciax_provincias.codigo_provincia,
                  admincomerciax_provincias.descripcion_provincia,admincomerciax_cliente.nombre,admincomerciax_cliente.id, 
                  count(public.casco_detallerc.rc_id) as recepcionados
                FROM 
                  public.casco_detallerc 
                inner join public.casco_recepcioncliente on casco_detallerc.rc_id = casco_recepcioncliente.doc_recepcioncliente_id 
                inner join public.casco_doc on casco_recepcioncliente.doc_recepcioncliente_id = casco_doc.id_doc
                inner join admincomerciax_cliente on casco_recepcioncliente.cliente_id=admincomerciax_cliente.id
                inner join admincomerciax_organismo on admincomerciax_organismo.id=admincomerciax_cliente.organismo_id
                inner join admincomerciax_provincias on admincomerciax_provincias.codigo_provincia=admincomerciax_cliente.provincia_id
                WHERE 
                  casco_recepcioncliente.doc_recepcioncliente_id = casco_doc.id_doc AND
                  casco_doc.fecha_doc >= '"""+fecha_datos+"""' """+str(opt)+"""  
                group by casco_recepcioncliente.cliente_id,admincomerciax_organismo.siglas_organismo,admincomerciax_provincias.codigo_provincia,
                admincomerciax_provincias.descripcion_provincia,admincomerciax_cliente.nombre,admincomerciax_cliente.id
                order by admincomerciax_organismo.siglas_organismo,admincomerciax_provincias.descripcion_provincia,
                admincomerciax_cliente.nombre 
                """

            resultados_entrada = query_to_dicts(sql_entradas)
            
            for datos in resultados_entrada:
                dic_cli[datos['cliente_id']]['Entregados']=datos['recepcionados']
            
            sql_salidas="""
                 SELECT 
                      casco_casco.id_cliente_id, 
                      casco_casco.estado_actual, 
                      casco_recepcioncliente.cliente_id,
                      count (casco_casco.estado_actual) as canti,
                      admincomerciax_organismo.siglas_organismo,admincomerciax_provincias.codigo_provincia,
                      admincomerciax_provincias.descripcion_provincia,admincomerciax_cliente.id,
                      admincomerciax_cliente.nombre
                    FROM 
                      public.casco_casco
                    inner join public.casco_detallerc on casco_detallerc.casco_id = casco_casco.id_casco
                    inner join public.casco_recepcioncliente on casco_recepcioncliente.cliente_id = casco_casco.id_cliente_id
                    inner join admincomerciax_cliente on casco_casco.id_cliente_id=admincomerciax_cliente.id
                    inner join admincomerciax_organismo on admincomerciax_organismo.id=admincomerciax_cliente.organismo_id
                    inner join admincomerciax_provincias on admincomerciax_provincias.codigo_provincia=admincomerciax_cliente.provincia_id
                    WHERE 
                      casco_detallerc.rc_id = casco_recepcioncliente.doc_recepcioncliente_id AND
                      casco_casco.fecha >='"""+fecha_datos+"""' """+str(opt)+""" AND casco_casco.estado_actual in ('DC','Factura','DCC','ECR')
                    group by casco_casco.id_cliente_id, casco_recepcioncliente.cliente_id,
                    casco_casco.estado_actual,admincomerciax_organismo.siglas_organismo,admincomerciax_cliente.nombre,
                    admincomerciax_provincias.codigo_provincia,admincomerciax_provincias.descripcion_provincia,admincomerciax_cliente.id
                    order by admincomerciax_organismo.siglas_organismo,admincomerciax_provincias.descripcion_provincia,
                    admincomerciax_cliente.nombre          
            """
            
            resultados_salidas = query_to_dicts(sql_salidas)
            for datos in resultados_salidas:
                if datos['estado_actual'] == 'DC':
                    estado = 'Deco'  
                else:
                    estado = datos['estado_actual']
                dic_cli[datos['id_cliente_id']][estado]+=int(datos['canti'])
            
            
            sql_existencia="""
                 SELECT 
                      casco_casco.id_cliente_id, 
                      casco_casco.estado_actual, 
                      casco_recepcioncliente.cliente_id,
                      count (casco_casco.estado_actual) as canti,
                      admincomerciax_organismo.siglas_organismo,admincomerciax_provincias.codigo_provincia,
                      admincomerciax_provincias.descripcion_provincia,admincomerciax_cliente.id,
                      admincomerciax_cliente.nombre
                    FROM 
                      public.casco_casco
                    inner join public.casco_detallerc on casco_detallerc.casco_id = casco_casco.id_casco
                    inner join public.casco_recepcioncliente on casco_recepcioncliente.cliente_id = casco_casco.id_cliente_id
                    inner join admincomerciax_cliente on casco_casco.id_cliente_id=admincomerciax_cliente.id
                    inner join admincomerciax_organismo on admincomerciax_organismo.id=admincomerciax_cliente.organismo_id
                    inner join admincomerciax_provincias on admincomerciax_provincias.codigo_provincia=admincomerciax_cliente.provincia_id
                    WHERE 
                      casco_detallerc.rc_id = casco_recepcioncliente.doc_recepcioncliente_id AND casco_casco.estado_actual in ('Casco','Produccion','PT','Transferencia','DVP','DIP','ER','REE')
                      """+str(opt)+""" 
                    group by casco_casco.id_cliente_id, casco_recepcioncliente.cliente_id,
                    casco_casco.estado_actual,admincomerciax_organismo.siglas_organismo,admincomerciax_cliente.nombre,
                    admincomerciax_provincias.codigo_provincia,admincomerciax_provincias.descripcion_provincia,admincomerciax_cliente.id
                    order by admincomerciax_organismo.siglas_organismo,admincomerciax_provincias.descripcion_provincia,
                    admincomerciax_cliente.nombre          
            """
            
            resultados_existencia = query_to_dicts(sql_existencia)    
            for datos in resultados_existencia:
                if datos['estado_actual'] == 'PT':
                    estado = 'PTer'  
                else:
                    estado = datos['estado_actual']
                dic_cli[datos['id_cliente_id']][estado]+=int(datos['canti'])
           
            resultado=[]
            for a1 in range(lista_cli.__len__()):
                dic_cli[lista_cli[a1]]['Devoluc']= dic_cli[lista_cli[a1]]['DCC']+dic_cli[lista_cli[a1]]['ECR']
                dic_cli[lista_cli[a1]]['Inserv']= dic_cli[lista_cli[a1]]['DIP']+dic_cli[lista_cli[a1]]['ER']++dic_cli[lista_cli[a1]]['REE']
                resultado.append(dic_cli[lista_cli[a1]])

            # rr = [] TODO ESTO ES PARA LOS QUE DESCUADRAN
            # for k in resultado:
            #     if k['Inicio']-k['Deco']+k['Entregados']-k['Factura']-k['Devoluc'] != k['Casco']+k['Produccion']+k['PTer']+k['Transferencia']+k['DVP']+k['Inserv']:
            #         rr.append(k)
            # resultado = rr
            if request.POST.__contains__('submit1') or request.POST.__contains__('submit2'):  
                    
                    if resultado.__len__():
                        pdf_file_name=os.path.join(comerciax.settings.ADMIN_MEDIA_PDF,"Cociliacion.pdf")
                        if report_class.Reportes.Conciliacion(report_class.Reportes() , resultado, "Conciliación",pdf_file_name,filtro)==0:
                            mesg.append('Debe cerrar el fichero Conciliacion.pdf')
                            return render_to_response("comercial/reporteindex.html",{'vprev':1,'filtro':filtro,'resultado':resultado,'form':form,'title':titulo_form, 'form_name':nombre_form,'form_description':descripcion_form,
                                                            'controlador':controlador_form,'accion':accion_form,'error2':mesg},context_instance = RequestContext(request))
                        else:
                            input = PdfFileReader(file(pdf_file_name,"rb"))
                            output = PdfFileWriter()
                            for page in input.pages:
                                output.addPage(page)
                            buffer = StringIO.StringIO()
                            output.write(buffer)
                            response = HttpResponse(mimetype='application/pdf')
                            file_namesitio='%s'%(pdf_file_name)
                            response['Content-Disposition'] = 'attachment; filename=%s'%(pdf_file_name)
                            response.write(buffer.getvalue())
                            #AQUIIIII EMAIL
                            if envia:
                                import smtplib
                                from email.mime.application import MIMEApplication
                                from django.core.mail.message import EmailMessage
                                try:
                                    message = EmailMessage(subject='Conciliacion',body='Enviado por '+request.user.first_name+' '+request.user.last_name, from_email=correo_envia, to=[correo])
                                    part = MIMEApplication(open(file_namesitio,"rb").read())
                                    part.add_header('Content-Disposition', 'attachment', filename="Conciliacion.pdf")
                                    message.attach(part)
                                    if ssl==True:
                                        smtp = smtplib.SMTP_SSL(host=servidor,port=puerto)
                                    else:
                                        smtp = smtplib.SMTP(servidor)
                                    smtp.ehlo()
                                    smtp.login(correo_envia,contrasena)
                                    smtp.sendmail(correo_envia,[correo],message.message().as_string())
                                    smtp.close()
                                    return response
                                except Exception, e:
                                    mesg=mesg+['Error de conexión. Revise la configuración del Correo SMTP']
                                    return render_to_response("comercial/reporteindex.html",{'vprev':1,'filtro':filtro,'resultado':resultado,'form':form,'title':titulo_form, 'form_name':nombre_form,'form_description':descripcion_form,
                                                            'controlador':controlador_form,'accion':accion_form,'error2':mesg},context_instance = RequestContext(request))
                                    
                        return response
                    else:
                        mesg=mesg+['No existe información para mostrar']
                        return render_to_response("comercial/reporteindex.html",{'vprev':1,'filtro':filtro,'resultado':resultado,'form':form,'title':titulo_form, 'form_name':nombre_form,'form_description':descripcion_form,
                                                            'controlador':controlador_form,'accion':accion_form,'error2':mesg},context_instance = RequestContext(request))
                           
            else:
                if resultado.__len__()==0:
                    mesg=mesg+['No existe información para mostrar']
                    return render_to_response("comercial/reporteindex.html",{'vprev':1,'form':form,'title':titulo_form, 'form_name':nombre_form,'form_description':descripcion_form,
                                                                    'controlador':controlador_form,'accion':accion_form,'error2':mesg},context_instance = RequestContext(request))
                
                    
                return render_to_response("report/conciliacion.html",{'filtro':filtro,'fecha_hoy':fecha_hoy(),'resultado':resultado,'error2':mesg},context_instance = RequestContext(request))
        
    form = Fconciliacion() 
    
    return render_to_response("comercial/reporteindex.html",{'vprev':1,'form':form,'title':titulo_form, 'form_name':nombre_form,'form_description':descripcion_form,
                                                                'controlador':controlador_form,'accion':accion_form,'error2':mesg,'email':1},context_instance = RequestContext(request))
  
@login_required
def servclient(request):
    
    nombre_form='Reportes'
    descripcion_form='Servicios a Clientes'
    titulo_form='Servicios a Clientes' 
    controlador_form='Reportes'
    accion_form='/comerciax/comercial/servclient/reporte'
    mesg=[]
    
    if request.method == 'POST':
        form = FServicios(request.POST)
        
        if form.is_valid():
            envia=False
#            fecha_cierre=Fechacierre.objects.get(almacen='cm')
            desde=form.cleaned_data['desde']
            hasta=form.cleaned_data['hasta']
            cliente=form.cleaned_data['ccliente']
            organismo=form.cleaned_data['organismo']
            provincia=form.cleaned_data['provincia']
            if request.POST.__contains__('submit2'):
                envia=True
                if cliente==None:
                    mesg=mesg+['Debe seleccionar un cliente']
                    return render_to_response("comercial/reporteindex.html",{'vprev':0,'vpdf':1,'form':form,'title':titulo_form, 'form_name':nombre_form,'form_description':descripcion_form,
                                                                    'controlador':controlador_form,'accion':accion_form,'error2':mesg,'email':0},context_instance = RequestContext(request))
                correo=cliente.email
                if correo.__len__()==0:
                    mesg=mesg+['Este cliente no tiene correo']
                    return render_to_response("comercial/reporteindex.html",{'vprev':0,'vpdf':1,'form':form,'title':titulo_form, 'form_name':nombre_form,'form_description':descripcion_form,
                                                                   'controlador':controlador_form,'accion':accion_form,'error2':mesg,'email':0},context_instance = RequestContext(request))
                try:
                    querySet = Config_SMTPEmail.objects.get()
                except Exception, e:
                    mesg=mesg+['No está configurado el correo SMTP']
                    return render_to_response("comercial/reporteindex.html",{'vprev':0,'vpdf':1,'form':form,'title':titulo_form, 'form_name':nombre_form,'form_description':descripcion_form,
                                                                   'controlador':controlador_form,'accion':accion_form,'error2':mesg,'email':0},context_instance = RequestContext(request))
                servidor=querySet.servidor
                correo_envia=querySet.correo
                puerto = querySet.puerto
                ssl = querySet.ssl
                try:
                    contrasena = base64.b64decode(querySet.contrasena)
                except Exception, e:
                    mesg=mesg+['Revise la contraseña en la configuración del Correo SMTP']
                    return render_to_response("comercial/reporteindex.html",{'vprev':0,'vpdf':1,'form':form,'title':titulo_form, 'form_name':nombre_form,'form_description':descripcion_form,
                                                                   'controlador':controlador_form,'accion':accion_form,'error2':mesg,'email':0},context_instance = RequestContext(request))
            filtro=[]
            where=[]
            filtro.append("Desde:"+desde.strftime("%d/%m/%Y")+" Hasta:"+hasta.strftime("%d/%m/%Y"))
            where.append("casco_doc.fecha_doc >='"+desde.strftime("%d/%m/%Y")+"'")
            where.append("casco_doc.fecha_doc <='"+hasta.strftime("%d/%m/%Y")+"'")
#            resultado=Casco.objects.select_related().all().order_by('estado_actual','admincomerciax_producto.descripcion')
            if cliente!=None:
                where.append("admincomerciax_cliente.id='"+cliente.id+"'")
                filtro.append('Cliente: '+cliente.nombre)
            else:
                if organismo!=None:
                    where.append("siglas_organismo='"+organismo.siglas_organismo+"'")
                    filtro.append('Organismo: '+organismo.siglas_organismo)
                if provincia!=None:
                    where.append("codigo_provincia='"+provincia.codigo_provincia+"'")
                    filtro.append('Provincia: '+provincia.descripcion_provincia)
            estado=False                    
                
#            optwhere=" AND " if len(where)>0 else ""  
            optwhere=""             
            for a1 in range(len(where)):
                optwhere+= where[a1]+ " AND "
            long=len(optwhere)
            optwhere=optwhere[0:long-4]
            opt=str(optwhere)
                
            sql_entradas="""
            SELECT admincomerciax_organismo.siglas_organismo, 
                    admincomerciax_cliente.nombre,
                    COUNT(casco_detallerc.id_detallerc) AS Cantidad,                        
                    admincomerciax_provincias.descripcion_provincia
            FROM casco_doc 
                    INNER JOIN casco_recepcioncliente ON casco_recepcioncliente.doc_recepcioncliente_id = casco_doc.id_doc 
                    INNER JOIN admincomerciax_cliente ON casco_recepcioncliente.cliente_id = admincomerciax_cliente.id 
                    INNER JOIN casco_detallerc ON casco_detallerc.rc_id = casco_recepcioncliente.doc_recepcioncliente_id 
                    INNER JOIN casco_casco ON casco_detallerc.casco_id = casco_casco.id_casco 
                    INNER JOIN admincomerciax_producto ON casco_casco.producto_id = admincomerciax_producto.id 
                    INNER JOIN admincomerciax_provincias ON admincomerciax_cliente.provincia_id = admincomerciax_provincias.codigo_provincia 
                    INNER JOIN admincomerciax_organismo ON admincomerciax_cliente.organismo_id = admincomerciax_organismo.id  
            WHERE """+str(opt)+"""
            GROUP BY 
                     admincomerciax_cliente.nombre, 
                     admincomerciax_provincias.descripcion_provincia, 
                     admincomerciax_organismo.siglas_organismo
            order by siglas_organismo,descripcion_provincia,nombre 
            """
            resultados_entrada = query_to_dicts(sql_entradas)
            dic_cli={}
            for datos in resultados_entrada:
                if not dic_cli.has_key(datos['siglas_organismo']):
                        dic_cli[datos['siglas_organismo']]={datos['descripcion_provincia']:
                                                        [{datos['nombre']:{'Entregados':int(datos['cantidad']),
                                                          'PT':0,
                                                          'Facturados':0,
                                                          'Decom':0,
                                                          'Devuelt':0}}]}
                else:
                    if not dic_cli[datos['siglas_organismo']].has_key(datos['descripcion_provincia']):
                        dic_cli[datos['siglas_organismo']][datos['descripcion_provincia']]=[{datos['nombre']:{'Entregados':int(datos['cantidad']),
                                                      'PT':0,
                                                      'Facturados':0,
                                                      'Decom':0,
                                                      'Devuelt':0}}]
                    else:
                        tiene=False
                        for k1 in range(dic_cli[datos['siglas_organismo']][datos['descripcion_provincia']].__len__()):
                            if dic_cli[datos['siglas_organismo']][datos['descripcion_provincia']][k1].has_key(datos['nombre']):
                                tiene=True
                                dic_cli[datos['siglas_organismo']][datos['descripcion_provincia']][k1][datos['nombre']]['Entregados']= int(datos['cantidad'])
                        if not tiene:
                            dic_cli[datos['siglas_organismo']][datos['descripcion_provincia']]+=[{datos['nombre']:{'Entregados':int(datos['cantidad']),
                                                      'PT':0,
                                                      'Facturados':0,
                                                      'Decom':0,
                                                      'Devuelt':0}}]
            
            optpt="where "+str(opt)+ " AND casco_doc.tipo_doc = '9'"
            optptext="where "+str(opt)+ " AND casco_doc.tipo_doc = '10'"
            sql_pt="""
                 SELECT 
                    sum (cons1.cantidad) as cantidad,
                    cons1.cliente_id as cliente_id,
                    cons1.nombre as nombre,
                    cons1.siglas_organismo as siglas_organismo,
                    cons1.descripcion_provincia as descripcion_provincia
                from 
                    ((SELECT  
                        count (casco_detallept.casco_id) as cantidad,
                        casco_casco.id_cliente_id as cliente_id,
                        admincomerciax_cliente.nombre,
                        admincomerciax_organismo.siglas_organismo,
                        admincomerciax_provincias.descripcion_provincia
                    FROM 
                    public.casco_doc
                        inner join casco_produccionterminada on casco_produccionterminada.doc_pt_id = casco_doc.id_doc 
                        inner join casco_detallept on casco_detallept.pt_id= casco_produccionterminada.doc_pt_id
                        inner join casco_casco on casco_casco.id_casco = casco_detallept.casco_id
                        left outer join admincomerciax_cliente on casco_casco.id_cliente_id=admincomerciax_cliente.id
                        left outer join admincomerciax_organismo on admincomerciax_cliente.organismo_id=admincomerciax_organismo.id
                        left outer join admincomerciax_provincias on admincomerciax_cliente.provincia_id=admincomerciax_provincias.codigo_provincia
                    """+str(optpt)+""" 
                    group by siglas_organismo,descripcion_provincia,cliente_id,admincomerciax_cliente.nombre
                    )
                    union all
                    (SELECT  
                    count (casco_detallepte.casco_id) as cantidad,
                    casco_casco.id_cliente_id as cliente_id,
                    admincomerciax_cliente.nombre,
                    admincomerciax_organismo.siglas_organismo,
                    admincomerciax_provincias.descripcion_provincia
                    FROM 
                    public.casco_doc
                    inner join casco_ptexternos on casco_ptexternos.doc_ptexternos_id = casco_doc.id_doc 
                    inner join casco_detallepte on casco_detallepte.doc_pte_id= casco_ptexternos.doc_ptexternos_id
                    inner join casco_casco on casco_casco.id_casco = casco_detallepte.casco_id
                    left outer join admincomerciax_cliente on casco_casco.id_cliente_id=admincomerciax_cliente.id
                    left outer join admincomerciax_organismo on admincomerciax_cliente.organismo_id=admincomerciax_organismo.id
                    left outer join admincomerciax_provincias on admincomerciax_cliente.provincia_id=admincomerciax_provincias.codigo_provincia
                    """+str(optptext)+"""
                    group by siglas_organismo,descripcion_provincia,cliente_id,admincomerciax_cliente.nombre,casco_casco.id_cliente_id
                    )) as cons1
                    group by siglas_organismo,descripcion_provincia,cliente_id,nombre
                    order by siglas_organismo,descripcion_provincia,nombre    
            """
            resultados_pt = query_to_dicts(sql_pt)

            for datos in resultados_pt:
                if not dic_cli.has_key(datos['siglas_organismo']):
                        dic_cli[datos['siglas_organismo']]={datos['descripcion_provincia']:
                                                        [{datos['nombre']:{'Entregados':0,
                                                          'PT':int(datos['cantidad']),
                                                          'Facturados':0,
                                                          'Decom':0,
                                                          'Devuelt':0}}]}
                else:
                    if not dic_cli[datos['siglas_organismo']].has_key(datos['descripcion_provincia']):
                        dic_cli[datos['siglas_organismo']][datos['descripcion_provincia']]=[{datos['nombre']:{'Entregados':0,
                                                      'PT':int(datos['cantidad']),
                                                      'Facturados':0,
                                                      'Decom':0,
                                                      'Devuelt':0}}]
                    else:
                        tiene=False
                        for k1 in range(dic_cli[datos['siglas_organismo']][datos['descripcion_provincia']].__len__()):
                            if dic_cli[datos['siglas_organismo']][datos['descripcion_provincia']][k1].has_key(datos['nombre']):
                                tiene=True
                                dic_cli[datos['siglas_organismo']][datos['descripcion_provincia']][k1][datos['nombre']]['PT']= int(datos['cantidad'])
                        if not tiene:
                            dic_cli[datos['siglas_organismo']][datos['descripcion_provincia']]+=[{datos['nombre']:{'Entregados':0,
                                                      'PT':int(datos['cantidad']),
                                                      'Facturados':0,
                                                      'Decom':0,
                                                      'Devuelt':0}}]
                
            optfact="where "+str(opt)+ " AND casco_doc.tipo_doc = '14'"
            sql_facturados="""
                 SELECT  
                      count (comercial_detallefactura.casco_id) as cantidad,
                      casco_casco.id_cliente_id as cliente_id,
                      admincomerciax_cliente.nombre as nombre,
                      admincomerciax_organismo.siglas_organismo,
                      admincomerciax_provincias.descripcion_provincia
                    FROM 
                      public.casco_doc
                    inner join comercial_facturas on comercial_facturas.doc_factura_id = casco_doc.id_doc 
                    inner join comercial_detallefactura on comercial_detallefactura.factura_id= comercial_facturas.doc_factura_id
                    inner join casco_casco on casco_casco.id_casco = comercial_detallefactura.casco_id
                    left outer join admincomerciax_cliente on casco_casco.id_cliente_id=admincomerciax_cliente.id
                    left outer join admincomerciax_organismo on admincomerciax_cliente.organismo_id=admincomerciax_organismo.id
                    left outer join admincomerciax_provincias on admincomerciax_cliente.provincia_id=admincomerciax_provincias.codigo_provincia
                    """+str(optfact)+"""
                    group by siglas_organismo,descripcion_provincia,cliente_id,admincomerciax_cliente.nombre,casco_casco.id_cliente_id
                    order by siglas_organismo,descripcion_provincia,admincomerciax_cliente.nombre           
            """
            resultados_facturados = query_to_dicts(sql_facturados)    
            for datos in resultados_facturados:
                if not dic_cli.has_key(datos['siglas_organismo']):
                        dic_cli[datos['siglas_organismo']]={datos['descripcion_provincia']:
                                                        [{datos['nombre']:{'Entregados':0,
                                                          'PT':0,
                                                          'Facturados':int(datos['cantidad']),
                                                          'Decom':0,
                                                          'Devuelt':0}}]}
                else:
                    if not dic_cli[datos['siglas_organismo']].has_key(datos['descripcion_provincia']):
                        dic_cli[datos['siglas_organismo']][datos['descripcion_provincia']]=[{datos['nombre']:{'Entregados':0,
                                                      'PT':0,
                                                      'Facturados':int(datos['cantidad']),
                                                      'Decom':0,
                                                      'Devuelt':0}}]
                    else:
                        tiene=False
                        for k1 in range(dic_cli[datos['siglas_organismo']][datos['descripcion_provincia']].__len__()):
                            if dic_cli[datos['siglas_organismo']][datos['descripcion_provincia']][k1].has_key(datos['nombre']):
                                tiene=True
                                dic_cli[datos['siglas_organismo']][datos['descripcion_provincia']][k1][datos['nombre']]['Facturados']= int(datos['cantidad'])
                        if not tiene:
                            dic_cli[datos['siglas_organismo']][datos['descripcion_provincia']]+=[{datos['nombre']:{'Entregados':0,
                                                      'PT':0,
                                                      'Facturados':int(datos['cantidad']),
                                                      'Decom':0,
                                                      'Devuelt':0}}]
        
        #Decomisados
            optdec="where "+str(opt)+ " AND casco_doc.tipo_doc = '15'"
            sql_decom="""
                 SELECT  
                    count (casco_detalle_dc.casco_id) as cantidad,
                    casco_casco.id_cliente_id as cliente_id,
                    admincomerciax_cliente.nombre as nombre,
                    admincomerciax_organismo.siglas_organismo,
                    admincomerciax_provincias.descripcion_provincia
                FROM 
                public.casco_doc
                    inner join casco_cascodecomiso on casco_cascodecomiso.doc_decomiso_id = casco_doc.id_doc 
                    inner join casco_detalle_dc on casco_detalle_dc.doc_decomiso_id= casco_cascodecomiso.doc_decomiso_id
                    inner join casco_casco on casco_casco.id_casco = casco_detalle_dc.casco_id
                    left outer join admincomerciax_cliente on casco_casco.id_cliente_id=admincomerciax_cliente.id
                    left outer join admincomerciax_organismo on admincomerciax_cliente.organismo_id=admincomerciax_organismo.id
                    left outer join admincomerciax_provincias on admincomerciax_cliente.provincia_id=admincomerciax_provincias.codigo_provincia
                    """+str(optdec)+"""
                    group by siglas_organismo,descripcion_provincia,cliente_id,admincomerciax_cliente.nombre,casco_casco.id_cliente_id
                    order by siglas_organismo,descripcion_provincia,admincomerciax_cliente.nombre             
            """
            resultados_decom = query_to_dicts(sql_decom)    
            for datos in resultados_decom:
                if not dic_cli.has_key(datos['siglas_organismo']):
                        dic_cli[datos['siglas_organismo']]={datos['descripcion_provincia']:
                                                        [{datos['nombre']:{'Entregados':0,
                                                          'PT':0,
                                                          'Facturados':0,
                                                          'Decom':int(datos['cantidad']),
                                                          'Devuelt':0}}]}
                else:
                    if not dic_cli[datos['siglas_organismo']].has_key(datos['descripcion_provincia']):
                        dic_cli[datos['siglas_organismo']][datos['descripcion_provincia']]=[{datos['nombre']:{'Entregados':0,
                                                      'PT':0,
                                                      'Facturados':0,
                                                      'Decom':int(datos['cantidad']),
                                                      'Devuelt':0}}]
                    else:
                        tiene=False
                        for k1 in range(dic_cli[datos['siglas_organismo']][datos['descripcion_provincia']].__len__()):
                            if dic_cli[datos['siglas_organismo']][datos['descripcion_provincia']][k1].has_key(datos['nombre']):
                                tiene=True
                                dic_cli[datos['siglas_organismo']][datos['descripcion_provincia']][k1][datos['nombre']]['Decom']= int(datos['cantidad'])
                        if not tiene:
                            dic_cli[datos['siglas_organismo']][datos['descripcion_provincia']]+=[{datos['nombre']:{'Entregados':0,
                                                      'PT':0,
                                                      'Facturados':0,
                                                      'Decom':int(datos['cantidad']),
                                                      'Devuelt':0}}]
        
            optdev="where "+str(opt)+ " AND casco_doc.tipo_doc = '19'"
            optdev2="where "+str(opt)+ " AND casco_doc.tipo_doc = '8'"
            sql_dev="""
            SELECT 
                sum (cons1.cantidad) as cantidad,
                cons1.cliente_id as cliente_id,
                cons1.nombre as nombre,
                cons1.siglas_organismo as siglas_organismo,
                cons1.descripcion_provincia as descripcion_provincia
            from 
                ((SELECT  
                count (casco_detalledcc.casco_id) as cantidad,
                casco_casco.id_cliente_id as cliente_id,
                admincomerciax_cliente.nombre,
                admincomerciax_organismo.siglas_organismo,
                admincomerciax_provincias.descripcion_provincia
                FROM 
                public.casco_doc
                inner join casco_devolucioncasco on casco_devolucioncasco.doc_devolucion_id = casco_doc.id_doc 
                inner join casco_detalledcc on casco_detalledcc.devolucion_id= casco_devolucioncasco.doc_devolucion_id
                inner join casco_casco on casco_casco.id_casco = casco_detalledcc.casco_id
                left outer join admincomerciax_cliente on casco_casco.id_cliente_id=admincomerciax_cliente.id
                left outer join admincomerciax_organismo on admincomerciax_cliente.organismo_id=admincomerciax_organismo.id
                left outer join admincomerciax_provincias on admincomerciax_cliente.provincia_id=admincomerciax_provincias.codigo_provincia
                """+optdev+"""
                group by siglas_organismo,descripcion_provincia,cliente_id,admincomerciax_cliente.nombre, casco_casco.id_cliente_id 
                )
                union 
                (SELECT  
                count (casco_detalleentregarechazado.casco_id) as cantidad,
                casco_casco.id_cliente_id as cliente_id,
                admincomerciax_cliente.nombre,
                admincomerciax_organismo.siglas_organismo,
                admincomerciax_provincias.descripcion_provincia
                FROM 
                public.casco_doc
                inner join casco_entregarechazado on casco_entregarechazado.doc_entregarechazado_id = casco_doc.id_doc 
                inner join casco_detalleentregarechazado on casco_detalleentregarechazado.erechazado_id= casco_entregarechazado.doc_entregarechazado_id
                inner join casco_casco on casco_casco.id_casco = casco_detalleentregarechazado.casco_id
                left outer join admincomerciax_cliente on casco_casco.id_cliente_id=admincomerciax_cliente.id
                left outer join admincomerciax_organismo on admincomerciax_cliente.organismo_id=admincomerciax_organismo.id
                left outer join admincomerciax_provincias on admincomerciax_cliente.provincia_id=admincomerciax_provincias.codigo_provincia
                """+optdev2+"""
                group by siglas_organismo,descripcion_provincia,cliente_id,admincomerciax_cliente.nombre,casco_casco.id_cliente_id
                )) as cons1
                group by siglas_organismo,descripcion_provincia,cliente_id,nombre
                order by siglas_organismo,descripcion_provincia,nombre
            """
            resultados_dev = query_to_dicts(sql_dev)
            for datos in resultados_dev:
                if not dic_cli.has_key(datos['siglas_organismo']):
                        dic_cli[datos['siglas_organismo']]={datos['descripcion_provincia']:
                                                        [{datos['nombre']:{'Entregados':0,
                                                          'PT':0,
                                                          'Facturados':0,
                                                          'Decom':0,
                                                          'Devuelt':int(datos['cantidad'])}}]}
                else:
                    if not dic_cli[datos['siglas_organismo']].has_key(datos['descripcion_provincia']):
                        dic_cli[datos['siglas_organismo']][datos['descripcion_provincia']]=[{datos['nombre']:{'Entregados':0,
                                                      'PT':0,
                                                      'Facturados':0,
                                                      'Decom':0,
                                                      'Devuelt':int(datos['cantidad'])}}]
                    else:
                        tiene=False
                        for k1 in range(dic_cli[datos['siglas_organismo']][datos['descripcion_provincia']].__len__()):
                            if dic_cli[datos['siglas_organismo']][datos['descripcion_provincia']][k1].has_key(datos['nombre']):
                                tiene=True
                                dic_cli[datos['siglas_organismo']][datos['descripcion_provincia']][k1][datos['nombre']]['Devuelt']= int(datos['cantidad'])
                        if not tiene:
                            dic_cli[datos['siglas_organismo']][datos['descripcion_provincia']]+=[{datos['nombre']:{'Entregados':0,
                                                      'PT':0,
                                                      'Facturados':0,
                                                      'Decom':0,
                                                      'Devuelt':int(datos['cantidad'])}}]
        
            organismos=dic_cli.keys()
            organismos.sort()
            if organismos.__len__()!=0:
                if organismos[0]==None:
                    organismos.remove(organismos[0])
            resultado=[]
            cantgen_entra=0
            cantgen_pt=0
            cantgen_fact=0
            cantgen_decom=0
            cantgen_devol=0
            for i in range(organismos.__len__()):
                organismo=organismos[i]
                provi=dic_cli[organismos[i]].keys()
                provi.sort()
                
                if provi[0]==None:
                    provi.remove(provi[0])
                cantorg_entra=0
                cantorg_pt=0
                cantorg_fact=0
                cantorg_decom=0
                cantorg_devol=0
                for k in range(provi.__len__()):
                    provincia=provi[k]
                    cliente=[]
                    for p1 in range(dic_cli[organismos[i]][provi[k]].__len__()):
                        cliente+=dic_cli[organismos[i]][provi[k]][p1].keys()
                    #cliente=dic_cli[organismos[i]][provi[k]].keys()
                    cliente.sort()
                    if cliente[0]==None:
                        cliente.remove(cliente[0])
                    cant_entra=0
                    cant_pt=0
                    cant_fact=0
                    cant_decom=0
                    cant_devol=0
                    for p in range(cliente.__len__()):
                        entra=dic_cli[organismos[i]][provi[k]][p][dic_cli[organismos[i]][provi[k]][p].keys()[0]]['Entregados']
                        cant_entra+=entra
                        llave_cli=dic_cli[organismos[i]][provi[k]][p].keys()[0]
                        pt=dic_cli[organismos[i]][provi[k]][p][llave_cli]['PT']
                        cant_pt+=pt
                        fact=dic_cli[organismos[i]][provi[k]][p][llave_cli]['Facturados']
                        cant_fact+=fact
                        decom=dic_cli[organismos[i]][provi[k]][p][llave_cli]['Decom']
                        cant_decom+=decom
                        devol=dic_cli[organismos[i]][provi[k]][p][llave_cli]['Devuelt']
                        cant_devol+=devol
                        dic={'organismo':organismo,
                         'provincia':provincia,
                         'cliente': cliente[p],
                         'entradas':entra,
                         'pt':pt,
                         'factura':fact,
                         'decom':decom,
                         'devol':devol}
                        resultado=resultado+[dic]
                        organismo=""
                        provincia=""
                    dic={'organismo':"=TOT. PROV.=",
                         'provincia':"",
                         'cliente': "",
                         'entradas':cant_entra,
                         'pt':cant_pt,
                         'factura':cant_fact,
                         'decom':cant_decom,
                         'devol':cant_devol}
                    resultado=resultado+[dic]
                    cantorg_entra+=cant_entra
                    cantorg_pt+=cant_pt
                    cantorg_fact+=cant_fact
                    cantorg_decom+=cant_decom
                    cantorg_devol+=cant_devol
                dic={'organismo':"=TOT. ORG.=",
                     'provincia':"",
                     'cliente': "",
                     'entradas':cantorg_entra,
                     'pt':cantorg_pt,
                     'factura':cantorg_fact,
                     'decom':cantorg_decom,
                     'devol':cantorg_devol}    
                resultado=resultado+[dic]
                cantgen_entra+=cantorg_entra
                cantgen_pt+=cantorg_pt
                cantgen_fact+=cantorg_fact
                cantgen_decom+=cantorg_decom
                cantgen_devol+=cantorg_devol
            
            dic={'organismo':"=TOT. GEN.=",
             'provincia':"",
             'cliente': "",
             'entradas':cantgen_entra,
             'pt':cantgen_pt,
             'factura':cantgen_fact,
             'decom':cantgen_decom,
             'devol':cantgen_devol}  
            resultado=resultado+[dic]          

            if resultado.__len__()==0:
                mesg=mesg+['No existe información para mostrar']
                return render_to_response("comercial/reporteindex.html",{'vprev':0,'vpdf':1,'form':form,'title':titulo_form, 'form_name':nombre_form,'form_description':descripcion_form,
                                                                'controlador':controlador_form,'accion':accion_form,'error2':mesg},context_instance = RequestContext(request))
            
                
            return render_to_response("report/servicios_cliente.html",{'filtro':filtro,'fecha_hoy':fecha_hoy(),'resultado':resultado,'error2':mesg},context_instance = RequestContext(request))
    
    form = FServicios() 
    
    return render_to_response("comercial/reporteindex.html",{'vpdf':1,'vprev':0,'form':form,'title':titulo_form, 'form_name':nombre_form,'form_description':descripcion_form,
                                                                'controlador':controlador_form,'accion':accion_form,'error2':mesg,'email':0},context_instance = RequestContext(request))
    
@login_required
def repcumpplanes(request):
    
    nombre_form='Cumplimiento de los Planes Contratados'
    descripcion_form='Cumplimiento de los Planes Contratados'
    titulo_form='Cumplimiento de los Planes Contratados' 
    controlador_form='Cumplimiento del Plan '
    accion_form='/comerciax/comercial/repcumpplanes/reporte'
    mesg=[]
    
    mesg=[]
    if request.method == 'POST':
        form = RepCumpPlanes(request.POST)
        
        if form.is_valid():

            cliente=form.cleaned_data['ccliente']
            organismo=form.cleaned_data['organismo']
            provincia=form.cleaned_data['provincia']
            ano=form.cleaned_data['ano']
            envia=False
            pdf_file_name=os.path.join(comerciax.settings.ADMIN_MEDIA_PDF,"Cumplim de Planes Contratados.pdf")
            
            
            filtro=[]
            cade_where="admincomerciax_cliente.eliminado = False"
            filtro.append('Periodo: '+str(ano))
            
            if organismo!=None:
                filtro.append('Organismo: '+organismo.siglas_organismo)
                cade_where+=" AND (admincomerciax_organismo.id='"+organismo.id+"')"
            
            if provincia!=None:
                filtro.append('Provincia: '+provincia.descripcion_provincia)
                cade_where+=" AND (admincomerciax_provincias.codigo_provincia='"+provincia.codigo_provincia+"')"
                
            if cliente!=None:
                filtro.append('Cliente: '+cliente.nombre)
                cade_where+=" AND (admincomerciax_cliente.id='"+cliente.id+"')"
            
            encabezado=""
            
            resultado_sql="""
                   SELECT admincomerciax_organismo.siglas_organismo, admincomerciax_provincias.descripcion_provincia, 
                       admincomerciax_cliente.nombre, admincomerciax_planes.plan_contratado,  
                       count(casco_detallerc.id_detallerc) as entradas,
                       cast((count(casco_detallerc.id_detallerc)*100)/cast(admincomerciax_planes.plan_contratado as real) as real) as cumplim    
                       FROM  admincomerciax_planes INNER JOIN
                                   admincomerciax_clientecontrato ON admincomerciax_planes.contrato_id = admincomerciax_clientecontrato.contrato_id AND 
                                   admincomerciax_planes.plan_ano = """ + str(ano)+""" INNER JOIN
                                   admincomerciax_organismo INNER JOIN
                                   admincomerciax_cliente ON admincomerciax_organismo.id = admincomerciax_cliente.organismo_id INNER JOIN
                                   admincomerciax_provincias ON admincomerciax_cliente.provincia_id = admincomerciax_provincias.codigo_provincia ON 
                                   admincomerciax_clientecontrato.cliente_id = admincomerciax_cliente.id LEFT OUTER JOIN
                                   admincomerciax_contrato ON admincomerciax_clientecontrato.contrato_id=admincomerciax_contrato.id_contrato
                                   left outer join casco_recepcioncliente on casco_recepcioncliente.cliente_id = admincomerciax_cliente.id 
                                   RIGHT OUTER JOIN casco_doc on casco_doc.id_doc = casco_recepcioncliente.doc_recepcioncliente_id and date_part('year',casco_doc.fecha_doc)=2015
                                   left join casco_detallerc on casco_detallerc.rc_id = casco_recepcioncliente.doc_recepcioncliente_id and casco_recepcioncliente.recepcioncliente_tipo='O'
                    WHERE """+cade_where+"""
                    group by admincomerciax_organismo.siglas_organismo,
                    admincomerciax_organismo.siglas_organismo, admincomerciax_provincias.descripcion_provincia, 
                       admincomerciax_cliente.nombre, admincomerciax_planes.plan_contratado, admincomerciax_planes.plan_ano, 
                       admincomerciax_clientecontrato.contrato_id, admincomerciax_cliente.id, admincomerciax_cliente.eliminado, 
                       admincomerciax_cliente.organismo_id, admincomerciax_cliente.provincia_id
                    ORDER BY admincomerciax_organismo.siglas_organismo, 
                             admincomerciax_provincias.descripcion_provincia,
                             admincomerciax_cliente.nombre 
            """
#            print resultado_sql
            resultado = query_to_dicts(resultado_sql)
            dic_cli={}
            for datos in resultado:
                if not dic_cli.has_key(datos['siglas_organismo']):
                        dic_cli[datos['siglas_organismo']]={datos['descripcion_provincia']:
                                                        [{datos['nombre']:{'Entregados':int(datos['entradas']),
                                                          'Plan':int(datos['plan_contratado']),
                                                          'cumplim':utils.redondeo(datos['cumplim'],2)
                                                          }}]}
                else:
                    if not dic_cli[datos['siglas_organismo']].has_key(datos['descripcion_provincia']):
                        dic_cli[datos['siglas_organismo']][datos['descripcion_provincia']]=[{datos['nombre']:{'Entregados':int(datos['entradas']),
                                                      'Plan':int(datos['plan_contratado']),
                                                      'cumplim':utils.redondeo(datos['cumplim'],2)
                                                      }}]
                    else:
                        tiene=False
                        for k1 in range(dic_cli[datos['siglas_organismo']][datos['descripcion_provincia']].__len__()):
                            if dic_cli[datos['siglas_organismo']][datos['descripcion_provincia']][k1].has_key(datos['nombre']):
                                tiene=True
                                dic_cli[datos['siglas_organismo']][datos['descripcion_provincia']][k1][datos['nombre']]['Entregados']= int(datos['entradas'])
                        if not tiene:
                            dic_cli[datos['siglas_organismo']][datos['descripcion_provincia']]+=[{datos['nombre']:{'Entregados':int(datos['entradas']),
                                                      'Plan':int(datos['plan_contratado']),
                                                       'cumplim':utils.redondeo(datos['cumplim'],2)
                                                      }}]
            
            organismos=dic_cli.keys()
            organismos.sort()
            if organismos.__len__()!=0:
                if organismos[0]==None:
                    organismos.remove(organismos[0])
            resultado=[]
            cantgen_entra=0.0
            cantgen_plan=0.0
#            cantgen_fact=0
#            cantgen_decom=0
#            cantgen_devol=0
            for i in range(organismos.__len__()):
                organismo=organismos[i]
                provi=dic_cli[organismos[i]].keys()
                provi.sort()
                
                if provi[0]==None:
                    provi.remove(provi[0])
                cantorg_entra=0.0
                cantorg_plan=0.0
                for k in range(provi.__len__()):
                    provincia=provi[k]
                    cliente=[]
                    for p1 in range(dic_cli[organismos[i]][provi[k]].__len__()):
                        cliente+=dic_cli[organismos[i]][provi[k]][p1].keys()
                    #cliente=dic_cli[organismos[i]][provi[k]].keys()
                    cliente.sort()
                    if cliente[0]==None:
                        cliente.remove(cliente[0])
                    cant_entra=0.0
                    cant_plan=0.0
                    for p in range(cliente.__len__()):
                        entra=dic_cli[organismos[i]][provi[k]][p][dic_cli[organismos[i]][provi[k]][p].keys()[0]]['Entregados']
                        cant_entra+=entra
                        llave_cli=dic_cli[organismos[i]][provi[k]][p].keys()[0]
                        plan=dic_cli[organismos[i]][provi[k]][p][llave_cli]['Plan']
                        cant_plan+=plan
                        cumplim=dic_cli[organismos[i]][provi[k]][p][llave_cli]['cumplim']
                        dic={'organismo':organismo,
                         'provincia':provincia,
                         'cliente': cliente[p],
                         'entradas':entra,
                         'plan':plan,
                         'cumplim':cumplim
                         }
                        resultado=resultado+[dic]
                        organismo=""
                        provincia=""
                    dic={'organismo':"=TOT. PROV.=",
                         'provincia':"",
                         'cliente': "",
                         'entradas':int(cant_entra),
                         'plan':int(cant_plan),
                         'cumplim':utils.redondeo((cant_entra*100)/cant_plan,2)
                         }
                    resultado=resultado+[dic]
                    cantorg_entra+=cant_entra
                    cantorg_plan+=cant_plan
                dic={'organismo':"=TOT. ORG.=",
                     'provincia':"",
                     'cliente': "",
                     'entradas':int(cantorg_entra),
                     'plan':int(cantorg_plan),
                     'cumplim':utils.redondeo((cantorg_entra*100)/cantorg_plan,2)
                     }    
                resultado=resultado+[dic]
                cantgen_entra+=cantorg_entra
                cantgen_plan+=cantorg_plan
            
            dic={'organismo':"=TOT. GEN.=",
             'provincia':"",
             'cliente': "",
             'entradas':int(cantgen_entra),
             'plan':int(cantgen_plan),
             'cumplim':utils.redondeo((cantgen_entra*100)/cantgen_plan,2)}  
            resultado=resultado+[dic]          

            if resultado.__len__()==0:
                mesg=mesg+['No existe información para mostrar']
                return render_to_response("comercial/reporteindex.html",{'vprev':0,'vpdf':1,'form':form,'title':titulo_form, 'form_name':nombre_form,'form_description':descripcion_form,
                                                                'controlador':controlador_form,'accion':accion_form,'error2':mesg},context_instance = RequestContext(request))
            
                
            return render_to_response("report/cumplimiento_plan.html",{'filtro':filtro,'fecha_hoy':fecha_hoy(),'resultado':resultado,'error2':mesg},context_instance = RequestContext(request))
    
    form = RepCumpPlanes() 
    
    return render_to_response("comercial/reporteindex.html",{'vpdf':1,'vprev':0,'form':form,'title':titulo_form, 'form_name':nombre_form,'form_description':descripcion_form,
                                                                'controlador':controlador_form,'accion':accion_form,'error2':mesg,'email':0},context_instance = RequestContext(request))

@login_required
def plazoscasco(request, *error):
    l=[]
    if error.__len__() > 0:
        l=error[0]
    error2 = l
    
    elementos = query_to_dicts("""
            select dat.Casco,dat.DIP, dat.DVP, dat.ER, dat.REE,dat.Produccion, dat.ProduccionT,
                   dat.Casco+dat.DIP+dat.DVP+dat.ER+dat.REE as totalcasco
            from
            (SELECT 
                  coalesce(max(case when casco_casco.estado_actual = 'Casco' then
                     (select cast(sum(dat1.dias)/sum(dat1.cant) as integer) as promCasco
                     from
                        (select count(casco_casco.id_casco) as cant,sum(DATE_PART('day', now()-casco_doc.fecha_doc)) as dias from casco_detallerc 
                                                         inner join casco_casco on casco_casco.id_casco = casco_detallerc.casco_id
                                                         inner join casco_recepcioncliente on casco_recepcioncliente.doc_recepcioncliente_id = casco_detallerc.rc_id
                                                         inner join casco_doc on casco_recepcioncliente.doc_recepcioncliente_id = casco_doc.id_doc
                                                         where casco_casco.estado_actual = 'Casco' and casco_casco.ocioso = False
                        union all
                        select count(casco_casco.id_casco) as cant, sum(DATE_PART('day', now()- casco_doc.fecha_doc)) as dias from casco_detallerp
                                     inner join casco_casco on casco_casco.id_casco = casco_detallerp.casco_id
                                                 inner join casco_recepcionparticular on casco_recepcionparticular.doc_recepcionparticular_id = casco_detallerp.rp_id
                                                 inner join casco_doc on casco_recepcionparticular.doc_recepcionparticular_id = casco_doc.id_doc
                                                where casco_casco.estado_actual = 'Casco' and casco_casco.ocioso = False) as dat1)
                end),0) as Casco,
                 coalesce(max(case when casco_casco.estado_actual = 'DIP' then
                     (select cast(sum(DATE_PART('day', now()-casco_doc.fecha_doc))/count(casco_casco.id_casco) as integer)
                                            from casco_detalledip 
                                            inner join casco_casco on casco_casco.id_casco = casco_detalledip.casco_id
                                            inner join casco_dip on casco_dip.doc_dip_id = casco_detalledip.dip_id
                                            inner join casco_doc on casco_dip.doc_dip_id = casco_doc.id_doc
                                            where casco_casco.estado_actual = 'DIP' and casco_casco.ocioso = False)
                end),0) as DIP,
                coalesce(max(case when casco_casco.estado_actual = 'DVP' then
                     (select cast(sum(DATE_PART('day', now()-casco_doc.fecha_doc))/count(casco_casco.id_casco) as integer)
                                            from casco_detalledvp 
                                            inner join casco_casco on casco_casco.id_casco = casco_detalledvp.casco_id
                                            inner join casco_dvp on casco_dvp.doc_dvp_id = casco_detalledvp.dvp_id
                                            inner join casco_doc on casco_dvp.doc_dvp_id = casco_doc.id_doc
                                            where casco_casco.estado_actual = 'DVP' and casco_casco.ocioso = False)
                end),0) as DVP,
                coalesce(max(case when casco_casco.estado_actual = 'ER' then
                     (select cast(sum(DATE_PART('day', now()-casco_doc.fecha_doc))/count(casco_casco.id_casco) as integer)
                                            from casco_detalle_er 
                                            inner join casco_casco on casco_casco.id_casco = casco_detalle_er.casco_id
                                            inner join casco_errorrecepcion on casco_errorrecepcion.doc_errorrecepcion_id = casco_detalle_er.errro_revision_id
                                            inner join casco_doc on casco_errorrecepcion.doc_errorrecepcion_id = casco_doc.id_doc
                                            where casco_casco.estado_actual = 'ER' and casco_casco.ocioso = False)
                end),0) as ER,
                coalesce(max(case when casco_casco.estado_actual = 'REE' then
                     (select cast(sum(DATE_PART('day', now()-casco_doc.fecha_doc))/count(casco_casco.id_casco) as integer)
                                            from casco_detallerre 
                                            inner join casco_casco on casco_casco.id_casco = casco_detallerre.casco_id
                                            inner join casco_receprechaext on casco_receprechaext.doc_receprechaext_id = casco_detallerre.receprechaext_id
                                            inner join casco_doc on casco_receprechaext.doc_receprechaext_id = casco_doc.id_doc
                                            where casco_casco.estado_actual = 'REE' and casco_casco.ocioso = False)
                end),0) as REE,
                coalesce(max(case when casco_casco.estado_actual = 'Produccion' then
                     (select cast(sum(dat1.dias)/sum(dat1.cant) as integer) as promCasco
                     from
                        (select count(casco_casco.id_casco) as cant,sum(DATE_PART('day', now()-casco_doc.fecha_doc)) as dias from casco_detallevp 
                         inner join casco_casco on casco_casco.id_casco = casco_detallevp.casco_id
                     inner join casco_vulcaproduccion on casco_vulcaproduccion.doc_vulcaproduccion_id = casco_detallevp.vp_id
                          inner join casco_doc on casco_vulcaproduccion.doc_vulcaproduccion_id = casco_doc.id_doc
                      where casco_casco.estado_actual = 'Produccion' and casco_casco.ocioso = False
                        union all
                        select count(casco_casco.id_casco) as cant, sum(DATE_PART('day', now()- casco_doc.fecha_doc)) as dias from casco_detallecc
                     inner join casco_casco on casco_casco.id_casco = casco_detallecc.casco_id
                     inner join casco_cc on casco_cc.doc_cc_id = casco_detallecc.cc_id
                     inner join casco_doc on casco_cc.doc_cc_id = casco_doc.id_doc
                         where casco_casco.estado_actual = 'Produccion' and casco_casco.ocioso = False) as dat1)
                end),0) as Produccion,
                coalesce(max(case when casco_casco.estado_actual = 'PT' then
                     (select cast(sum(dat1.dias)/sum(dat1.cant) as integer) as promCasco
                     from
                        (select count(casco_casco.id_casco) as cant,sum(DATE_PART('day', now()-casco_doc.fecha_doc)) as dias from casco_detallept 
                         inner join casco_casco on casco_casco.id_casco = casco_detallept.casco_id
                     inner join casco_produccionterminada on casco_produccionterminada.doc_pt_id = casco_detallept.pt_id
                         inner join casco_doc on casco_produccionterminada.doc_pt_id = casco_doc.id_doc
                      where casco_casco.estado_actual = 'PT' and casco_casco.ocioso = False
                        union all
                        select count(casco_casco.id_casco) as cant, sum(DATE_PART('day', now()- casco_doc.fecha_doc)) as dias from casco_detallepte
                     inner join casco_casco on casco_casco.id_casco = casco_detallepte.casco_id
                     inner join casco_ptexternos on casco_ptexternos.doc_ptexternos_id = casco_detallepte.doc_pte_id
                             inner join casco_doc on casco_ptexternos.doc_ptexternos_id = casco_doc.id_doc
                         where casco_casco.estado_actual = 'PT' and casco_casco.ocioso = False) as dat1)
                end),0) as ProduccionT
               FROM casco_casco
                 JOIN admincomerciax_producto ON casco_casco.producto_id::text = admincomerciax_producto.id::text
               WHERE casco_casco.estado_actual::text <> 'Transferencia'::text AND 
                    casco_casco.estado_actual::text <> 'Facturado'::text AND 
                    casco_casco.estado_actual::text <> 'ECR'::text and 
                    casco_casco.ocioso = False) dat
    """)
    
    fechacierre = Fechacierre.objects.filter(almacen='c').all()
    ultimo_mes_anyo = fechacierre[0]
    messes = ultimo_mes_anyo.mes + 1 
        
    return render_to_response("report/plazos.html",locals(),context_instance = RequestContext(request))    

def plazosfabricaall_pdf(request):
    elementos = query_to_dicts("""
            select dat.Casco,dat.DIP, dat.DVP, dat.ER, dat.REE,dat.Produccion, dat.ProduccionT,
                   dat.Casco+dat.DIP+dat.DVP+dat.ER+dat.REE as totalcasco
            from
            (SELECT 
                  coalesce(max(case when casco_casco.estado_actual = 'Casco' then
                     (select cast(sum(dat1.dias)/sum(dat1.cant) as integer) as promCasco
                     from
                        (select count(casco_casco.id_casco) as cant,sum(DATE_PART('day', now()-casco_doc.fecha_doc)) as dias from casco_detallerc 
                                                         inner join casco_casco on casco_casco.id_casco = casco_detallerc.casco_id
                                                         inner join casco_recepcioncliente on casco_recepcioncliente.doc_recepcioncliente_id = casco_detallerc.rc_id
                                                         inner join casco_doc on casco_recepcioncliente.doc_recepcioncliente_id = casco_doc.id_doc
                                                         where casco_casco.estado_actual = 'Casco' and casco_casco.ocioso = False
                        union all
                        select count(casco_casco.id_casco) as cant, sum(DATE_PART('day', now()- casco_doc.fecha_doc)) as dias from casco_detallerp
                                     inner join casco_casco on casco_casco.id_casco = casco_detallerp.casco_id
                                                 inner join casco_recepcionparticular on casco_recepcionparticular.doc_recepcionparticular_id = casco_detallerp.rp_id
                                                 inner join casco_doc on casco_recepcionparticular.doc_recepcionparticular_id = casco_doc.id_doc
                                                where casco_casco.estado_actual = 'Casco' and casco_casco.ocioso = False) as dat1)
                end),0) as Casco,
                 coalesce(max(case when casco_casco.estado_actual = 'DIP' then
                     (select cast(sum(DATE_PART('day', now()-casco_doc.fecha_doc))/count(casco_casco.id_casco) as integer)
                                            from casco_detalledip 
                                            inner join casco_casco on casco_casco.id_casco = casco_detalledip.casco_id
                                            inner join casco_dip on casco_dip.doc_dip_id = casco_detalledip.dip_id
                                            inner join casco_doc on casco_dip.doc_dip_id = casco_doc.id_doc
                                            where casco_casco.estado_actual = 'DIP' and casco_casco.ocioso = False)
                end),0) as DIP,
                coalesce(max(case when casco_casco.estado_actual = 'DVP' then
                     (select cast(sum(DATE_PART('day', now()-casco_doc.fecha_doc))/count(casco_casco.id_casco) as integer)
                                            from casco_detalledvp 
                                            inner join casco_casco on casco_casco.id_casco = casco_detalledvp.casco_id
                                            inner join casco_dvp on casco_dvp.doc_dvp_id = casco_detalledvp.dvp_id
                                            inner join casco_doc on casco_dvp.doc_dvp_id = casco_doc.id_doc
                                            where casco_casco.estado_actual = 'DVP' and casco_casco.ocioso = False)
                end),0) as DVP,
                coalesce(max(case when casco_casco.estado_actual = 'ER' then
                     (select cast(sum(DATE_PART('day', now()-casco_doc.fecha_doc))/count(casco_casco.id_casco) as integer)
                                            from casco_detalle_er 
                                            inner join casco_casco on casco_casco.id_casco = casco_detalle_er.casco_id
                                            inner join casco_errorrecepcion on casco_errorrecepcion.doc_errorrecepcion_id = casco_detalle_er.errro_revision_id
                                            inner join casco_doc on casco_errorrecepcion.doc_errorrecepcion_id = casco_doc.id_doc
                                            where casco_casco.estado_actual = 'ER' and casco_casco.ocioso = False)
                end),0) as ER,
                coalesce(max(case when casco_casco.estado_actual = 'REE' then
                     (select cast(sum(DATE_PART('day', now()-casco_doc.fecha_doc))/count(casco_casco.id_casco) as integer)
                                            from casco_detallerre 
                                            inner join casco_casco on casco_casco.id_casco = casco_detallerre.casco_id
                                            inner join casco_receprechaext on casco_receprechaext.doc_receprechaext_id = casco_detallerre.receprechaext_id
                                            inner join casco_doc on casco_receprechaext.doc_receprechaext_id = casco_doc.id_doc
                                            where casco_casco.estado_actual = 'REE' and casco_casco.ocioso = False)
                end),0) as REE,
                coalesce(max(case when casco_casco.estado_actual = 'Produccion' then
                     (select cast(sum(dat1.dias)/sum(dat1.cant) as integer) as promCasco
                     from
                        (select count(casco_casco.id_casco) as cant,sum(DATE_PART('day', now()-casco_doc.fecha_doc)) as dias from casco_detallevp 
                         inner join casco_casco on casco_casco.id_casco = casco_detallevp.casco_id
                     inner join casco_vulcaproduccion on casco_vulcaproduccion.doc_vulcaproduccion_id = casco_detallevp.vp_id
                          inner join casco_doc on casco_vulcaproduccion.doc_vulcaproduccion_id = casco_doc.id_doc
                      where casco_casco.estado_actual = 'Produccion' and casco_casco.ocioso = False
                        union all
                        select count(casco_casco.id_casco) as cant, sum(DATE_PART('day', now()- casco_doc.fecha_doc)) as dias from casco_detallecc
                     inner join casco_casco on casco_casco.id_casco = casco_detallecc.casco_id
                     inner join casco_cc on casco_cc.doc_cc_id = casco_detallecc.cc_id
                     inner join casco_doc on casco_cc.doc_cc_id = casco_doc.id_doc
                         where casco_casco.estado_actual = 'Produccion' and casco_casco.ocioso = False) as dat1)
                end),0) as Produccion,
                coalesce(max(case when casco_casco.estado_actual = 'PT' then
                     (select cast(sum(dat1.dias)/sum(dat1.cant) as integer) as promCasco
                     from
                        (select count(casco_casco.id_casco) as cant,sum(DATE_PART('day', now()-casco_doc.fecha_doc)) as dias from casco_detallept 
                         inner join casco_casco on casco_casco.id_casco = casco_detallept.casco_id
                     inner join casco_produccionterminada on casco_produccionterminada.doc_pt_id = casco_detallept.pt_id
                         inner join casco_doc on casco_produccionterminada.doc_pt_id = casco_doc.id_doc
                      where casco_casco.estado_actual = 'PT' and casco_casco.ocioso = False
                        union all
                        select count(casco_casco.id_casco) as cant, sum(DATE_PART('day', now()- casco_doc.fecha_doc)) as dias from casco_detallepte
                     inner join casco_casco on casco_casco.id_casco = casco_detallepte.casco_id
                     inner join casco_ptexternos on casco_ptexternos.doc_ptexternos_id = casco_detallepte.doc_pte_id
                             inner join casco_doc on casco_ptexternos.doc_ptexternos_id = casco_doc.id_doc
                         where casco_casco.estado_actual = 'PT' and casco_casco.ocioso = False) as dat1)
                end),0) as ProduccionT
               FROM casco_casco
                 JOIN admincomerciax_producto ON casco_casco.producto_id::text = admincomerciax_producto.id::text
               WHERE casco_casco.estado_actual::text <> 'Transferencia'::text AND 
                    casco_casco.estado_actual::text <> 'Facturado'::text AND 
                    casco_casco.estado_actual::text <> 'ECR'::text and 
                    casco_casco.ocioso = False) dat
    """)
    
    fechacierre = Fechacierre.objects.filter(almacen='c').all()
    ultimo_mes_anyo = fechacierre[0]
    messes = ultimo_mes_anyo.mes + 1 
    pdf_file_name=os.path.join(comerciax.settings.ADMIN_MEDIA_PDF,"Plazos en Fabrica.pdf")
    filtro=[]
    mesg=[]
    if report_class.Reportes.GenerarRep(report_class.Reportes() , elementos, "plazos_fabrica",pdf_file_name,filtro)==0:
        mesg.append('Debe cerrar el fichero Plazos en Fabrica.pdf')
    else:
        input = PdfFileReader(file(pdf_file_name,"rb"))
        output = PdfFileWriter()
        for page in input.pages:
            output.addPage(page)
        buffer = StringIO.StringIO()
        output.write(buffer)
        response = HttpResponse(mimetype='application/pdf')
        response['Content-Disposition'] = 'attachment; filename=%s'%(pdf_file_name)
        response.write(buffer.getvalue())
        return response


# ===============================================================================
# FACTURA SERVICIOS ENTIDADES
# ===============================================================================
@login_required
def get_fact_servicios_list(request):
    # prepare the params
    try:
        fecha_desde = Fecha_Ver.objects.get()
    except Exception, e:
        fecha_desde = None
    if fecha_desde == None:
        querySet = FacturasServicios.objects.select_related().filter(cliente__externo=False)
    else:
        querySet = FacturasServicios.objects.select_related().filter(cliente__externo=False,
                                                            doc_factura__fecha_doc__gte=fecha_desde.fecha)

    columnIndexNameMap = {0: '-doc_factura__fecha_doc', 1: 'factura_nro', 2: 'admincomerciax_cliente.nombre',
                          3: 'doc_factura__fecha_doc',
                          4: 'cancelada', 5: 'confirmar'}

    searchableColumns = ['confirmar', 'cancelada', 'factura_nro', 'cliente__nombre', 'doc_factura__fecha_doc']
    # path to template used to generate json
    jsonTemplatePath = 'comercial/json/json_factura_servicios.txt'

    # call to generic function from utils
    return get_datatables_records(request, querySet, columnIndexNameMap, searchableColumns, jsonTemplatePath)


@login_required
def factura_servicios_index(request):
    if not request.user.has_perm('comercial.factura'):
        return render_to_response("denegado.html", locals(), context_instance=RequestContext(request))
    return render_to_response('comercial/facturaserviciosindex.html', locals(), context_instance=RequestContext(request))


@login_required
@transaction.commit_on_success()
def factura_servicios_add(request):
    if not request.user.has_perm('comercial.factura'):
        return render_to_response("denegado.html", locals(), context_instance=RequestContext(request))

    nombre_form = 'Servicios'
    descripcion_form = 'Realizar Factura de Servicios'
    titulo_form = 'Servicios'
    controlador_form = 'Servicios'
    accion_form = '/comerciax/comercial/factura_servicios/add'
    cancelbtn_form = '/comerciax/comercial/factura_servicios/index'
    fecha_hoy = datetime.date.today().strftime("%d/%m/%Y")
    fecha_cierre = Fechacierre.objects.get(almacen='cm').fechaminima()
    fecha_maxima = Fechacierre.objects.get(almacen='cm').fechamaxima()
    c = None
    l = []
    if request.method == 'POST':
        form = FacturaServiciosForm(request.POST)
        if form.is_valid():
            obj_cliente = Cliente.objects.get(pk=form.data['cliente1'])
            try:
                tipoc = obj_cliente.get_contrato_tipo()
            except Exception, e:
                tipoc = None

            if tipoc == None:
                l = ['Este cliente no tiene contrato por lo que no se puede realizar la factura']
                return render_to_response('comercial/facturaadd.html', {'form': form, 'form_name': nombre_form,
                                                                        'form_description': descripcion_form,
                                                                        'accion': accion_form,
                                                                        'titulo': titulo_form,
                                                                        'controlador': controlador_form,
                                                                        'cancelbtn': cancelbtn_form,
                                                                        'fecha_minima': fecha_cierre,
                                                                        'fecha_maxima': fecha_maxima,
                                                                        'error2': l},
                                          context_instance=RequestContext(request))

            pk_user = User.objects.get(pk=request.user.id)

            fact = FacturasServicios()

            pk_doc = uuid4()
            obj_doc = Doc()

            obj_doc.id_doc = pk_doc
            obj_doc.tipo_doc = '20'
            obj_doc.fecha_doc = form.cleaned_data['fecha']
            obj_doc.operador = pk_user
            obj_doc.fecha_operacion = datetime.date.today()
            obj_doc.observaciones = form.cleaned_data['observaciones']

            fact.doc_factura = obj_doc
            fact.factura_nro = str(random.randint(1, 100000)) + "S/C"
            fact.cliente = Cliente.objects.get(pk=form.data['cliente1'])
            fact.confirmada = hashlib.sha1(pk_doc.__str__() + 'NO').hexdigest()

            fact.chapa = form.cleaned_data['chapa']
            fact.licencia = form.cleaned_data['licencia']
            fact.transportador = Transpotador.objects.get(pk=form.data['transportador'])

            try:
                obj_doc.save()
                fact.save()
                #                nume.save()
                return HttpResponseRedirect('/comerciax/comercial/factura_servicios/view/' + pk_doc.__str__())
            except Exception, e:
                exc_info = e.__str__()  # sys.exc_info()[:1]
                c = exc_info.find("DETAIL:")

                if c < 0:
                    l = l + ["Error Fatal."]
                else:
                    c = exc_info[c + 7:]
                    l = l + [c]

                transaction.rollback()
                form = FacturaServiciosForm(request.POST)
                return render_to_response('comercial/facturaserviciosadd.html',
                                          {'form': form, 'form_name': nombre_form, 'form_description': descripcion_form,
                                           'accion': accion_form, 'titulo': titulo_form,
                                           'controlador': controlador_form,
                                           'cancelbtn': cancelbtn_form, 'fecha_minima': fecha_cierre,
                                           'fecha_maxima': fecha_maxima, 'error2': l},
                                          context_instance=RequestContext(request))
            else:
                transaction.commit()
    else:
        meshoy = int(fecha_hoy.split('/')[1])
        mescierre = int(fecha_cierre.split('/')[1])

        if meshoy == mescierre:
            fecha_cierre = fecha_hoy
        form = FacturaServiciosForm(initial={'fecha': fecha_cierre})

    return render_to_response('comercial/facturaserviciosadd.html',
                              {'form': form, 'form_name': nombre_form, 'form_description': descripcion_form,
                               'accion': accion_form, 'titulo': titulo_form, 'controlador': controlador_form,
                               'cancelbtn': cancelbtn_form, 'fecha_minima': fecha_cierre, 'fecha_maxima': fecha_maxima,
                               'error2': c}, context_instance=RequestContext(request))


@login_required
def factura_servicios_view(request, idfa):
    if not request.user.has_perm('comercial.factura'):
        return render_to_response("denegado.html", locals(), context_instance=RequestContext(request))

    l = []
    cancelar = 0
    fact = FacturasServicios.objects.select_related().get(pk=idfa)
    if fact.cancelada == True:
        cancelar = 1
    confir = fact.get_confirmada()
    confirmar = 2
    if confir == 'N':
        confirmar = 0
    elif confir == 'S':
        confirmar = 1

    eliminar = 1
    editar = 1
    if confirmar == 2 or confirmar == 1:
        eliminar = 0
        editar = 0

    rc_fecha = fact.doc_factura.fecha_doc.strftime("%d/%m/%Y")
    rc_cliente = fact.cliente.nombre
    rc_nro = fact.factura_nro
    importecup = fact.get_importetotalcup()
    cant_servicios = fact.cantidad_servicios()
    cant_renglones = fact.get_renglones()

    precio_CUP = "Precio CUP"

    rc_observaciones = fact.doc_factura.observaciones
    filas = DetalleFacturaServicios.objects.select_related().filter(factura=idfa).order_by('servicio__descripcion')

    rc_transportador = fact.transportador.nombre
    rc_chapa = fact.chapa
    rc_licencia = fact.licencia
    hay_cup = 1

    elementos_detalle = []
    id1 = ''
    k = 0
    k2 = 0
    t_preciocup = 0.0

    for a1 in filas:
        if k != 0:
            if id1 != a1.servicio.id:
                elementos_detalle[k - 1]['cantidad'] = k2
                elementos_detalle[k - 1]['t_preciocup'] = t_preciocup
                t_preciocuc = 0.0
                t_preciocup = 0.0
                k2 = 0
        elementos_detalle += [{'servicio_id': a1.servicio.id,
                               'codigo': a1.servicio.codigo,
                               'servicio': a1.servicio.descripcion,
                               'precio_cup': a1.format_precio_mn()
                               }]
        k += 1
        k2 += 1
        t_preciocup += float(a1.precio_mn)
        id1 = a1.servicio.id
    if k != 0:
        elementos_detalle[k - 1]['cantidad'] = k2
        elementos_detalle[k - 1]['t_preciocup'] = t_preciocup
    return render_to_response('comercial/viewfacturaservicios.html', {'total_servicios': k, 'hay_cup': hay_cup,
                                                                      'hay_cuc': 0,
                                                             'eliminar': eliminar, 'editar': editar,
                                                             'cancelar': cancelar,
                                                             'confirmar': confirmar, 'transportador': rc_transportador,
                                                             'chapa': rc_chapa,
                                                             # 'importecasco': importecasco,
                                                             'transportador': rc_transportador, 'licencia': rc_licencia,
                                                             'precio_CUP': precio_CUP,
                                                             'importecup': importecup,
                                                             'fecha': rc_fecha,
                                                             'rc_nro': rc_nro,
                                                             'cliente': rc_cliente,
                                                             'observaciones': rc_observaciones, 'rc_id': idfa,
                                                             'elementos_detalle': elementos_detalle,
                                                             'error2': l, 'cant_servicios': cant_servicios,
                                                             'cant_renglones': cant_renglones},
                              context_instance=RequestContext(request))


def verfacturaservicios(request, idfactura, haycup, haycuc, cantservicios):
    empresaobj1 = Empresa.objects.all()
    hay_cup = int(haycup)
    hay_cuc = int(haycuc)
    es_servicios=1
    for empresaobj in empresaobj1:
        titular_name = empresaobj.nombre
        titular_dir = empresaobj.direccion
        titular_codigo = empresaobj.codigo
        titular_email = empresaobj.email
        titular_phone = empresaobj.telefono
        titular_fax = empresaobj.fax
        titular_cuenta_mn = empresaobj.cuenta_mn
        titular_cuenta_cuc = empresaobj.cuenta_usd
        titular_sucursal_mn = empresaobj.sucursal_mn
        titular_sucursal_cuc = empresaobj.sucursal_usd

    factura = FacturasServicios.objects.select_related().get(doc_factura=idfactura)
    pk_user = User.objects.get(pk=request.user.id)
    vendedor = pk_user.first_name + " " + pk_user.last_name

    user_doc = Doc.objects.get(id_doc=factura.doc_factura.id_doc).operador
    operador_ = User.objects.get(pk=user_doc.id)
    confeccionado = operador_.first_name + " " + operador_.last_name

    detallesFact = DetalleFacturaServicios.objects.select_related().filter(factura=idfactura).values('factura','precio_mn',
                                                                                                'servicio__codigo',
                                                                                                'servicio__descripcion', \
                                                                                                'servicio__um__descripcion') \
        .annotate(cantidad=Count('servicio__descripcion'))
    for a1 in range(detallesFact.__len__()):
        detallesFact[a1]['importecup'] = detallesFact[a1]['precio_mn'] * detallesFact[a1]['cantidad']
        detallesFact[a1]['precio_mn'] = str(detallesFact[a1]['precio_mn'])

    cliente = factura.cliente
    fecha_confeccionado = factura.doc_factura.fecha_doc

    cliente_codigo = cliente.codigo
    cliente_nombre = cliente.nombre
    cliente_dir = cliente.direccion
    cliente_phone = cliente.telefono
    cliente_email = cliente.email
    cliente_fax = cliente.fax

    contrato = ClienteContrato.objects.select_related().get(cliente=cliente.id, cerrado=False)
    contrato_sucursal_mn = contrato.contrato.sucursal_mn
    contrato_sucursal_cuc = contrato.contrato.sucursal_usd
    contrato_cuenta_mn = contrato.contrato.cuenta_mn
    contrato_cuenta_cuc = contrato.contrato.cuenta_usd
    contrato_nro = contrato.contrato.contrato_nro

    transportador = factura.transportador
    transportador_nombre = transportador.nombre
    transportador_ci = transportador.ci
    transportador_chapa = factura.chapa
    transportador_licencia = factura.licencia

    cancelada = factura.cancelada

    importetotalcup = factura.get_importetotalcup()
    importecup = factura.get_importecup()

    observaciones = factura.doc_factura.observaciones

    return render_to_response("report/factura.html", locals(), context_instance=RequestContext(request))


@login_required
@transaction.commit_on_success()
def factura_servicios_del(request, idfa):
    if not request.user.has_perm('comercial.factura'):
        return render_to_response("denegado.html", locals(), context_instance=RequestContext(request))

    l = []
    fact = FacturasServicios.objects.get(pk=idfa)
    noelim = 0
    if fact.confirmada == hashlib.sha1(fact.pk.__str__() + 'YES').hexdigest():
        mensa = "No se puede eliminar la factura Nro. " + fact.factura_nro + " porque ya está confirmada"
        noelim = 1
    elif fact.confirmada != hashlib.sha1(fact.pk.__str__() + 'NO').hexdigest():
        mensa = "No se puede eliminar la factura Nro. " + fact.factura_nro + " porque está corrupta"
        noelim = 1
    if noelim == 1:
        l = [mensa]
        rc_fecha = fact.doc_factura.fecha_doc.strftime("%d/%m/%Y")
        rc_cliente = fact.cliente.nombre
        rc_nro = fact.factura_nro
        importecup = FacturasServicios.objects.get(pk=idfa).get_importetotalcup()

        pmn = ClienteContrato.objects.select_related().get(cliente=fact.cliente.id, cerrado=False)

        precio_CUP = "Precio CUP"

        rc_observaciones = fact.doc_factura.observaciones
        filas = DetalleFacturaServicios.objects.select_related().filter(factura=idfa).order_by('casco_casco.casco_nro')

        rc_transportador = fact.transportador.nombre
        rc_chapa = fact.chapa
        rc_licencia = fact.licencia
        hay_cup = 1
        # Verificar si se puede editar. Se puede editar si todos los cascos relacionados con el estado es Casco

        return render_to_response('comercial/viewfacturaservicios.html',
                                  {'hay_cup': hay_cup, 'eliminar': 0, 'editar': 1, 'cancelar': 0,
                                   'confirmar': 0, 'transportador': rc_transportador, 'chapa': rc_chapa,
                                   'licencia': fact.licencia, 'transportador': rc_transportador, 'chapa': rc_chapa,
                                   'precio_CUP': precio_CUP, 'importecup': importecup,
                                   'rc_nro': rc_nro, 'fecha': rc_fecha, 'cliente': rc_cliente,
                                   'observaciones': rc_observaciones, 'rc_id': idfa, 'elementos_detalle': filas,
                                   'error2': l}, context_instance=RequestContext(request))
    try:
        Doc.objects.select_related().get(pk=idfa).delete()

        return HttpResponseRedirect('/comerciax/comercial/factura_servicios/index')
        # return render_to_response("casco/recepcionclienteindex.html",locals(),context_instance = RequestContext(request))
    except Exception, e:
        transaction.rollback()
        l = ['Error al eliminar el documento']
        fact = FacturasServicios.objects.select_related().get(pk=idfa)
        rc_fecha = fact.doc_factura.fecha_doc.strftime("%d/%m/%Y")
        rc_cliente = fact.cliente.nombre
        rc_nro = fact.factura_nro
        rc_observaciones = fact.doc_factura.observaciones
        filas = DetalleFacturaServicios.objects.select_related().filter(factura=idfa).order_by('servicios.descripcion')

        return render_to_response('comercial/viewfacturaservicios.html',
                                  {'hay_cup': hay_cup, 'rc_nro': rc_nro, 'fecha': rc_fecha,
                                   'cliente': rc_cliente, 'observaciones': rc_observaciones, 'rc_id': idfa,
                                   'elementos_detalle': filas, 'error2': l}, context_instance=RequestContext(request))
    else:
        transaction.commit()

    return 0


@login_required
@transaction.commit_on_success()
def factura_servicios_edit(request, idfa):
    if not request.user.has_perm('comercial.factura'):
        return render_to_response("denegado.html", locals(), context_instance=RequestContext(request))

    fact = FacturasServicios.objects.select_related().get(pk=idfa)
    noedit = 0
    if fact.confirmada == hashlib.sha1(fact.pk.__str__() + 'YES').hexdigest():
        mensa = "No se puede editar la factura Nro. " + fact.factura_nro + " porque ya está confirmada"
        noedit = 1
    elif fact.confirmada != hashlib.sha1(fact.pk.__str__() + 'NO').hexdigest():
        mensa = "No se puede editar la factura Nro. " + fact.factura_nro + " porque está corrupta"
        noedit = 1
    if noedit == 1:
        l = [mensa]
        rc_fecha = fact.doc_factura.fecha_doc.strftime("%d/%m/%Y")
        rc_cliente = fact.cliente.nombre
        rc_nro = fact.factura_nro

        importecup = FacturasServicios.objects.get(pk=idfa).get_importecup()

        pmn = ClienteContrato.objects.select_related().get(cliente=fact.cliente.id, cerrado=False)

        precio_CUP = "Precio CUP"

        rc_observaciones = fact.doc_factura.observaciones
        filas = DetalleFacturaServicios.objects.select_related().filter(factura=idfa).order_by('casco_casco.casco_nro')

        rc_transportador = fact.transportador.nombre
        rc_chapa = fact.chapa
        rc_licencia = fact.licencia
        hay_cup = 0

        # Verificar si se puede editar. Se puede editar si todos los cascos relacionados con el estado es Casco
        return render_to_response('comercial/viewfacturaservicios.html',
                                  {'hay_cup': hay_cup, 'eliminar': 0, 'editar': 1, 'cancelar': 0,
                                   'confirmar': 0, 'transportador': rc_transportador, 'chapa': rc_chapa,
                                   'transportador': rc_transportador, 'licencia': rc_licencia,
                                   'precio_CUP': precio_CUP, 'importecup': importecup,
                                   'rc_nro': rc_nro, 'fecha': rc_fecha, 'cliente': rc_cliente,
                                   'observaciones': rc_observaciones, 'rc_id': idfa, 'elementos_detalle': filas,
                                   'error2': l}, context_instance=RequestContext(request))

    nombre_form = 'Facturas Servicios'
    descripcion_form = 'Realizar Factura de Servicios a Clientes'
    titulo_form = 'Facturas Servicios'
    controlador_form = 'Facturas Servicios'
    accion_form = '/comerciax/comercial/factura_servicios/edit/' + idfa + '/'
    cancelbtn_form = '/comerciax/comercial/factura_servicios/view/' + idfa + '/'
    fecha_cierre = Fechacierre.objects.get(almacen='cm').fechaminima()
    fecha_maxima = Fechacierre.objects.get(almacen='cm').fechamaxima()
    c = None

    l = []

    detalles = DetalleFacturaServicios.objects.filter(factura=idfa).count()

    if request.method == 'POST':
        if detalles == 0:
            form = FacturaServiciosForm(request.POST)
        else:
            form = FacturaServiciosForm2(request.POST)
        if form.is_valid():
            if detalles == 0:
                cc = form.data['cliente1']
            else:
                cc = form.data['cliente']
            if (cc.find("|") < 0):
                obj_cliente = Cliente.objects.get(pk=cc)
            else:
                obj_cliente = Cliente.objects.get(pk=fact.cliente.id)
            try:
                tipoc = obj_cliente.get_contrato_tipo()
            except Exception, e:
                tipoc = None

            if tipoc == None:
                l = ['Este cliente no tiene contrato por lo que no se puede realizar la factura']
                return render_to_response('form/form_adddetalle.html',
                                          {'tipocliente': '0', 'form': form, 'form_name': nombre_form,
                                           'form_description': descripcion_form, 'accion': accion_form,
                                           'titulo': titulo_form, 'controlador': controlador_form,
                                           'cancelbtn': cancelbtn_form, 'fecha_minima': fecha_cierre,
                                           'fecha_maxima': fecha_maxima,
                                           'error2': l}, context_instance=RequestContext(request))

            pk_user = User.objects.get(pk=request.user.id)

            fact = FacturasServicios.objects.get(pk=idfa)
            doc = Doc.objects.get(pk=idfa)

            doc.fecha_doc = form.cleaned_data['fecha']
            doc.operador = pk_user
            doc.doc_operacion = datetime.date.today()
            doc.observaciones = form.cleaned_data['observaciones']
            fact.cliente = obj_cliente
            fact.transportador = Transpotador.objects.get(pk=form.data['transportador'])
            fact.chapa = form.cleaned_data['chapa']
            fact.licencia = form.cleaned_data['licencia']

            try:
                doc.save()
                fact.save()

                return HttpResponseRedirect('/comerciax/comercial/factura_servicios/view/' + idfa)

            except Exception, e:
                exc_info = e.__str__()  # sys.exc_info()[:1]
                c = exc_info.find("DETAIL:")

                if c < 0:
                    l = l + ["Error Fatal."]
                else:
                    c = exc_info[c + 7:]
                    l = l + [c]

                transaction.rollback()

                form = FacturaServiciosForm(request.POST)
                return render_to_response('form/form_adddetalle.html',
                                          {'tipocliente': '0', 'form': form, 'form_name': nombre_form,
                                           'form_description': descripcion_form,
                                           'accion': accion_form, 'titulo': titulo_form,
                                           'controlador': controlador_form,
                                           'cancelbtn': cancelbtn_form, 'fecha_minima': fecha_cierre,
                                           'fecha_maxima': fecha_maxima, 'error2': l},
                                          context_instance=RequestContext(request))
            else:
                transaction.commit()
    else:
        if detalles == 0:
            form = FacturaServiciosForm(
                initial={'transportador': fact.transportador, 'chapa': fact.chapa, 'licencia': fact.licencia,
                         'nro': fact.factura_nro, 'fecha': fact.doc_factura.fecha_doc,
                         'cliente1': fact.cliente, 'observaciones': fact.doc_factura.observaciones})
        else:

            form = FacturaServiciosForm2(initial={'transportador': fact.transportador,
                                         'licencia': fact.licencia,
                                         'chapa': fact.chapa, 'nro': fact.factura_nro,
                                         'fecha': fact.doc_factura.fecha_doc,
                                         'cliente': fact.cliente,
                                         'transportador': fact.transportador,
                                         'observaciones': fact.doc_factura.observaciones})

    return render_to_response('comercial/facturaserviciosedit.html',
                              {'form': form, 'form_name': nombre_form, 'form_description': descripcion_form,
                               'accion': accion_form, 'titulo': titulo_form, 'controlador': controlador_form,
                               'cancelbtn': cancelbtn_form, 'fecha_minima': fecha_cierre, 'fecha_maxima': fecha_maxima},
                              context_instance=RequestContext(request))


@login_required
@transaction.commit_on_success()
def factura_servicios_confirmar(request, idfa):
    if not request.user.has_perm('comercial.factura'):
        return render_to_response("denegado.html", locals(), context_instance=RequestContext(request))

    l = []
    fact = FacturasServicios.objects.get(pk=idfa)
    if fact.get_renglones() > 30:
        l = []
        cancelar = 0
        fact = FacturasServicios.objects.select_related().get(pk=idfa)
        if fact.cancelada == True:
            cancelar = 1
        confir = fact.get_confirmada()
        confirmar = 2
        if confir == 'N':
            confirmar = 0
        elif confir == 'S':
            confirmar = 1

        eliminar = 1
        editar = 1
        if confirmar == 2 or confirmar == 1:
            eliminar = 0
            editar = 0

        rc_fecha = fact.doc_factura.fecha_doc.strftime("%d/%m/%Y")
        rc_cliente = fact.cliente.nombre
        rc_nro = fact.factura_nro
        importecup = fact.get_importetotalcup()
        importecuc = fact.get_importecuc()
        cant_renglones = fact.get_renglones()
        pmn = ClienteContrato.objects.select_related().get(cliente=fact.cliente.id, cerrado=False)
        mncosto = pmn.contrato.preciocostomn
        cuccosto = pmn.contrato.preciocostocuc

        precio_CUP = "Precio CUP"

        rc_observaciones = fact.doc_factura.observaciones
        filas = DetalleFacturaServicios.objects.select_related().filter(factura=idfa).order_by(
            'servicio__descripcion')

        rc_transportador = fact.transportador.nombre
        rc_chapa = fact.chapa
        rc_licencia = fact.licencia
        hay_cup = 1
        l = ["La factura excede los 30 renglones, no se puede confirmar"]
        return render_to_response('comercial/viewfacturaservicios.html',
                                  {'hay_cup': hay_cup, 'eliminar': eliminar, 'editar': editar,
                                   'cancelar': cancelar, 'confirmar': confirmar, 'transportador': rc_transportador,
                                   'chapa': rc_chapa,
                                   'transportador': rc_transportador, 'licencia': rc_licencia,
                                   'precio_CUP': precio_CUP, 'importecup': importecup,
                                   'rc_nro': rc_nro, 'fecha': rc_fecha, 'cliente': rc_cliente,
                                   'observaciones': rc_observaciones, 'rc_id': idfa, 'elementos_detalle': filas,
                                   'error2': l, 'cant_renglones': cant_renglones},
                                  context_instance=RequestContext(request))

    else:

        pk_user = User.objects.get(pk=request.user.id)
        nrodoc = 1
        if NumeroDoc.objects.count() != 0:
            nrodoc = NumeroDoc.objects.get().nro_factura_servicios + 1
        nume = NumeroDoc()
        if NumeroDoc.objects.count() == 0:
            nume.id_numerodoc = uuid4()
        else:
            nume = NumeroDoc.objects.get()
        nume.nro_factura_servicios = nrodoc
        nume.save()
        Doc.objects.filter(pk=FacturasServicios.objects.get(pk=idfa).doc_factura).update(operador=pk_user)
        FacturasServicios.objects.filter(pk=idfa).update(confirmada=hashlib.sha1(idfa.__str__() + 'YES').hexdigest(),
                                                factura_nro=nrodoc, confirmar=True)
        return HttpResponseRedirect('/comerciax/comercial/factura_servicios/view/' + idfa)

@login_required
@transaction.commit_on_success()
def factura_servicios_imprimir(request, idfa):
    if not request.user.has_perm('comercial.factura'):
        return render_to_response("denegado.html", locals(), context_instance=RequestContext(request))

    l = []
    fact = FacturasServicios.objects.get(pk=idfa)
    if fact.confirmada != hashlib.sha1(fact.pk.__str__() + 'YES').hexdigest():
        mensa = "No se puede imprimir la factura Nro. " + fact.factura_nro + " porque no está confirmada"
        l = [mensa]
        rc_fecha = fact.doc_factura.fecha_doc.strftime("%d/%m/%Y")
        rc_cliente = fact.cliente.nombre
        rc_nro = fact.factura_nro
        importetotalcup = fact.get_importetotalcup()
        importecup = fact.get_importecup()

        precio_CUP = "Precio CUP"
        rc_observaciones = fact.doc_factura.observaciones
        filas = DetalleFacturaServicios.objects.select_related().filter(factura=idfa).order_by('servicios.descripcion')

        if filas.__len__() == 0:
            hay_venta = False

        rc_transportador = fact.transportador.nombre
        rc_chapa = fact.chapa
        rc_licencia = fact.licencia
        # Verificar si se puede editar. Se puede editar si todos los cascos relacionados con el estado es Casco
        hay_cup = 0
        return render_to_response('comercial/viewfacturaservicios.html',
                                  {'hay_cup': hay_cup, 'eliminar': 0, 'editar': 1, 'cancelar': 0,
                                   'confirmar': 0, 'transportador': rc_transportador, 'chapa': rc_chapa,
                                   'transportador': rc_transportador, 'chapa': rc_chapa, 'licencia': rc_licencia,
                                   'precio_CUP': precio_CUP, 'importecup': importecup,
                                   'importetotalcup': importetotalcup,
                                   'rc_nro': rc_nro, 'fecha': rc_fecha,
                                   'cliente': rc_cliente,
                                   'observaciones': rc_observaciones, 'rc_id': idfa, 'elementos_detalle': filas,
                                   'error2': l}, context_instance=RequestContext(request))
    return 0


@login_required
@transaction.commit_on_success()
def factura_servicios_cancelar(request, idfa):
    if not request.user.has_perm('comercial.factura'):
        return render_to_response("denegado.html", locals(), context_instance=RequestContext(request))

    l = []
    fact = FacturasServicios.objects.get(pk=idfa)
    # pagosfact = PagosFacturas.objects.filter(facturas=fact).count()
    pagosfact = 0.0
    if fact.confirmada != hashlib.sha1(fact.pk.__str__() + 'YES').hexdigest() or pagosfact != 0:
        mensa = "No se puede cancelar la factura Nro. " + fact.factura_nro + " porque no está confirmada"
        if pagosfact > 0:
            mensa = "No se puede cancelar la factura Nro. " + fact.factura_nro + " porque se han realizado pagos"
        l = [mensa]
        rc_fecha = fact.doc_factura.fecha_doc.strftime("%d/%m/%Y")
        rc_cliente = fact.cliente.nombre
        rc_nro = fact.factura_nro
        importecup = fact.get_importetotalcup()

        precio_CUP = "Precio CUP"

        rc_observaciones = fact.doc_factura.observaciones
        filas = DetalleFacturaServicios.objects.select_related().filter(factura=idfa).order_by('servicio.descripcion')

        rc_transportador = fact.transportador.nombre
        rc_chapa = fact.chapa
        rc_licencia = fact.licencia
        # Verificar si se puede editar. Se puede editar si todos los cascos relacionados con el estado es Casco
        hay_cup = 1
        return render_to_response('comercial/viewfacturaservicios.html',
                                  {'hay_cup': hay_cup, 'eliminar': 0, 'editar': 1, 'cancelar': 0,
                                   'confirmar': 0, 'transportador': rc_transportador, 'chapa': rc_chapa,
                                   'licencia': rc_licencia, 'transportador': rc_transportador,
                                   'precio_CUP': precio_CUP, 'importecup': importecup,
                                   'rc_nro': rc_nro, 'fecha': rc_fecha, 'cliente': rc_cliente,
                                   'observaciones': rc_observaciones, 'rc_id': idfa, 'elementos_detalle': filas,
                                   'error2': l}, context_instance=RequestContext(request))

    try:
        hay_cup = 1

        FacturasServicios.objects.filter(pk=idfa).update(cancelada=True)
        pk_user = User.objects.get(pk=request.user.id)
        Doc.objects.filter(pk=FacturasServicios.objects.get(pk=idfa).doc_factura).update(operador=pk_user)

        return HttpResponseRedirect('/comerciax/comercial/factura_servicios/index')
    except Exception, e:
        transaction.rollback()
        l = ['Error al cancelar factura']
        fact = Facturas.objects.select_related().get(pk=idfa)
        importecup = fact.get_importetotalcup()

        rc_fecha = fact.doc_factura.fecha_doc.strftime("%d/%m/%Y")
        rc_cliente = fact.cliente.nombre
        rc_transportador = fact.transportador.nombre
        rc_nro = fact.factura_nro
        rc_observaciones = fact.doc_factura.observaciones
        rc_chapa = fact.chapa
        rc_licencia = fact.licencia

        precio_CUP = "Precio CUP"
        return render_to_response('comercial/viewfacturaservicios.html',
                                  {'hay_cup': hay_cup,  'transportador': rc_transportador,
                                   'chapa': rc_chapa, 'licencia': rc_licencia, 'transportador': rc_transportador,
                                   'precio_CUP': precio_CUP, 'importecup': importecup,
                                   'rc_nro': rc_nro, 'fecha': rc_fecha, 'cliente': rc_cliente,
                                   'observaciones': rc_observaciones, 'rc_id': idfa, 'elementos_detalle': filas,
                                   'error2': l, 'cantcascos': '4'}, context_instance=RequestContext(request))
    else:
        transaction.commit()


@login_required
# @transaction.commit_on_success()
def detalleFacturaServicios_add(request, idfa):
    if not request.user.has_perm('comercial.factura'):
        return render_to_response("denegado.html", locals(), context_instance=RequestContext(request))

    l = []
    fact = FacturasServicios.objects.prefetch_related('detallefacturaservicios_set').get(pk=idfa)
    serv = [x.servicio.id for x in fact.detallefacturaservicios_set.all()]

    servicios = Servicio.objects.all().exclude(pk__in=serv).order_by('descripcion')
    noelim = 0
    if fact.confirmada == hashlib.sha1(fact.pk.__str__() + 'YES').hexdigest():
        mensa = "No se puede adicionar servicios a la factura Nro. " + fact.factura_nro + " porque ya está confirmada"
        noelim = 1
    elif fact.confirmada != hashlib.sha1(fact.pk.__str__() + 'NO').hexdigest():
        mensa = "No se puede adcionar servicios a la factura Nro. " + fact.factura_nro + " porque está corrupta"
        noelim = 1
    if noelim == 1:
        l = [mensa]
        rc_fecha = fact.doc_factura.fecha_doc.strftime("%d/%m/%Y")
        rc_cliente = fact.cliente.nombre
        rc_clientecomercializador = fact.cliente.comercializadora
        rc_nro = fact.factura_nro
        importecup = fact.get_importe_totalcup()

        precio_CUP = "Precio CUP"

        rc_observaciones = fact.doc_factura.observaciones
        filas = fact.detallefacturaservicios_set.all().order_by('servicio.descripcion')

        rc_transportador = fact.transportador.nombre
        rc_chapa = fact.chapa
        rc_licencia = fact.licencia
        # Verificar si se puede editar. Se puede editar si todos los cascos relacionados con el estado es Casco
        hay_cup = 1
        return render_to_response('comercial/viewfactura.html',
                                  {'hay_cup': hay_cup,  'eliminar': 0, 'editar': 1, 'cancelar': 0,
                                   'confirmar': 0, 'transportador': rc_transportador, 'chapa': rc_chapa,
                                   'transportador': rc_transportador, 'licencia': rc_licencia,
                                   'precio_CUP': precio_CUP, 'importecup': importecup,
                                   'rc_nro': rc_nro, 'fecha': rc_fecha, 'cliente': rc_cliente,
                                   'observaciones': rc_observaciones, 'rc_id': idfa,
                                   'elementos_detalle': filas,
                                   'error2': l}, context_instance=RequestContext(request))

    titulo_form = 'Facturas de Servicios'
    controlador_form = 'Facturas de Servicios'
    descripcion_form = 'Seleccionar servicio para la factura'

    accion_form = 'detalleFacturaServicios_add'
    cancelbtn_form = '/comerciax/comercial/factura_servicios/view/' + idfa

    if request.method == 'POST':
        pmn = ClienteContrato.objects.select_related().get(cliente=fact.cliente.id, cerrado=False)
        mn = pmn.contrato.preciomn
        seleccion = request.POST.keys()
        if 'submit' in seleccion:
            seleccion.remove('submit')
        elif 'submit1' in seleccion:
            seleccion.remove('submit1')
        k = 0
        ids = []
        while True:
            if k == seleccion.__len__():
                break
            servicio = Servicio.objects.filter(pk=seleccion[k])
            if servicio.count() != 0:
                ids.append(seleccion[k])
                detalle = DetalleFacturaServicios()
                serv=servicio[0] #Servicio.objects.get(pk=seleccion[k])
                if DetalleFacturaServicios.objects.filter(factura=idfa, servicio=serv).count() != 0:
                    detalle = DetalleFacturaServicios.objects.get(factura=idfa, servicio=serv)
                else:
                    detalle.id_detalle = uuid4()

                detalle.factura = FacturasServicios.objects.get(pk=idfa)
                detalle.servicio = serv
                detalle.precio_mn = Decimal(serv.precio_mn)

                detalle.save()

            k = k + 1
        servicios = servicios.exclude(pk__in=ids)
        if request.POST.__contains__('submit1'):

            return render_to_response('comercial/seleccionar_servicio.html',
                                      {'title': titulo_form, 'controlador': controlador_form,
                                       'accion': accion_form,
                                       'servicios': servicios,
                                       'cancelbtn': cancelbtn_form,
                                       'nro': fact.factura_nro,
                                       'form_description': descripcion_form,
                                       'fecha': fact.doc_factura.fecha_doc.strftime("%d/%m/%Y"),
                                       'observaciones': fact.doc_factura.observaciones,
                                       'rc_id': idfa,
                                       'dettransfe': True,
                                       'elementos_detalle': servicios,
                                       'nohay':servicios.__len__()==0}, context_instance=RequestContext(request))
        else:
            return HttpResponseRedirect('/comerciax/comercial/factura_servicios/view/' + idfa)

    return render_to_response('comercial/seleccionar_servicio.html',
                              {'title': titulo_form, 'controlador': controlador_form,
                               'accion': accion_form,
                               'servicios': servicios,
                               'cancelbtn': cancelbtn_form,
                               'nro': fact.factura_nro,
                               'form_description': descripcion_form,
                               'fecha': fact.doc_factura.fecha_doc.strftime("%d/%m/%Y"),
                               'observaciones': fact.doc_factura.observaciones,
                               'rc_id': idfa,
                               'dettransfe': True,
                               'elementos_detalle':servicios,
                               'nohay':servicios.__len__()==0}, context_instance=RequestContext(request))


@login_required
def detalleFacturaServicio_delete(request, idfa, idservicio):
    if not request.user.has_perm('comercial.factura'):
        return render_to_response("denegado.html", locals(), context_instance=RequestContext(request))

    fact = FacturasServicios.objects.get(pk=idfa)

    l = []

    DetalleFacturaServicios.objects.get(servicio=idservicio, factura=idfa).delete()
    cant_renglones = str(FacturasServicios.objects.get(doc_factura=idfa).get_renglones())
    data = []
    filas = DetalleFacturaServicios.objects.select_related().filter(factura=idfa).order_by('servicio__descripcion')
    total_servicio = str(filas.count())
    elementos_detalle = []

    for a1 in filas:

        importetotalcup = a1.factura.get_importetotalcup()

        elementos_detalle += [
            {'total_servicios': total_servicio,
             'cant_renglones': cant_renglones,
             'id_doc': a1.factura.doc_factura.id_doc,
             'servicio': a1.servicio.descripcion,
             'codigo': a1.servicio.codigo,
             'importetotalcup': importetotalcup,
             'servicio_id': a1.servicio.id,
             'precio_cup': a1.format_precio_mn()}]

    return HttpResponse(simplejson.dumps(elementos_detalle), content_type='application/javascript; charset=utf8')


@login_required
def servfacturas(request):
    nombre_form = 'Reportes'
    descripcion_form = 'Registro de Facturas de Asistencia Técnica'
    titulo_form = 'Registro de Facturas de Asistencia Técnica'
    controlador_form = 'Reportes'
    accion_form = '/comerciax/comercial/servfacturas/reporte'
    mesg = []

    if request.method == 'POST':
        form = Rep_RegFacturas(request.POST)

        if form.is_valid():
            desde = form.cleaned_data['fecha_desde']
            hasta = form.cleaned_data['fecha_hasta']
            filtro = []
            queryset = []
            filtro.append(
                'Facturas de Asistencia Técnica emitidas entre el ' + desde.strftime("%d/%m/%Y") + ' y el ' + hasta.strftime("%d/%m/%Y"))
            resultado = FacturasServicios.objects.select_related().filter(doc_factura__fecha_doc__gte=desde,
                                                                 doc_factura__fecha_doc__lte=hasta,
                                                                 confirmar=True).order_by('factura_nro')


            if resultado.__len__() == 0:
                mesg = mesg + ['No existe información para mostrar']
                return render_to_response("comercial/reporteindex.html",
                                          {'form': form, 'title': titulo_form, 'form_name': nombre_form,
                                           'form_description': descripcion_form,
                                           'controlador': controlador_form, 'accion': accion_form, 'error2': mesg},
                                          context_instance=RequestContext(request))
            else:
                total_importecup1 = 0
                total_cascocliente = 0
                for k in range(resultado.__len__()):
                    if resultado[k].get_confirmada() == 'S':
                        val = Decimal('0.00') if resultado[k].cancelada else resultado[k].get_importetotalcup(1)
                        queryset.append({'nombre': resultado[k].cliente.nombre, 'tipo': 'Clientes',
                                         'codigo': resultado[k].cliente.codigo,
                                         'factura_nro': str(resultado[k].factura_nro),
                                         'fecha_doc': resultado[k].get_fecha(),
                                         'cascos': resultado[k].cantidad_servicios() if not resultado[k].cancelada else 0,
                                         'importetotalcup': val,
                                         'cancelada': 'Cancelada' if resultado[k].cancelada == True else ''
                                         })
                    if resultado[k].cancelada == False:
                        total_cascocliente += resultado[k].cantidad_servicios()
                        total_importecup1 += resultado[k].get_importetotalcup(1)

                valor_cliente = total_importecup1
                total_importecup3 = 0

                total_cup = float(total_importecup1) + float(total_importecup3)
                total_cascototal = total_cascocliente

                total_cascototal = '{:20,.0f}'.format(total_cascototal)
                total_cascocliente = '{:20,.0f}'.format(total_cascocliente)

                total_importecup1 = 0 if total_importecup1 == 0 else '{:20,.2f}'.format(total_importecup1)
                total_importecup3 = 0 if total_importecup3 == 0 else '{:20,.2f}'.format(total_importecup3)

                if not request.POST.__contains__('submit1'):
                    return render_to_response("report/registro_facturas_servicios.html",
                                              {'filtro': filtro, 'fecha_hoy': fecha_hoy(), \
                                               'resultado': resultado, \
                                               'total_importecup1': total_importecup1,
                                               'total_importecup3': total_importecup3, \
                                               'total_cup': '{:20,.2f}'.format(total_cup),
                                               'valor_cliente': valor_cliente, \
                                               'total_cascototal': total_cascototal, \
                                               'total_cascocliente': total_cascocliente, \
                                               'error2': mesg}, context_instance=RequestContext(request))

                else:
                    pdf_file_name = os.path.join(comerciax.settings.ADMIN_MEDIA_PDF, "Registro de Facturas de Asistencia Técnica.pdf")
                    if report_class.Reportes.GenerarRep(report_class.Reportes(), queryset, "registro_fac_serv",
                                                        pdf_file_name, filtro) == 0:
                        mesg = mesg + ['Debe cerrar el documento Registro de Facturas de Asistencia Técnica.pdf']
                        return render_to_response("comercial/reporteindex.html",
                                                  {'filtro': filtro, 'resultado': resultado, 'form': form,
                                                   'title': titulo_form, 'form_name': nombre_form,
                                                   'form_description': descripcion_form,
                                                   'controlador': controlador_form, 'accion': accion_form,
                                                   'error2': mesg}, context_instance=RequestContext(request))
                    else:
                        input = PdfFileReader(file(pdf_file_name, "rb"))
                        output = PdfFileWriter()
                        for page in input.pages:
                            output.addPage(page)
                        buffer = StringIO.StringIO()
                        output.write(buffer)
                        response = HttpResponse(mimetype='application/pdf')
                        response['Content-Disposition'] = 'attachment; filename=%s' % (pdf_file_name)
                        response.write(buffer.getvalue())
                        return response

    form = Rep_RegFacturas()

    return render_to_response("comercial/reporteindex.html",
                              {'form': form, 'title': titulo_form, 'form_name': nombre_form,
                               'form_description': descripcion_form,
                               'controlador': controlador_form, 'accion': accion_form, 'error2': mesg},
                              context_instance=RequestContext(request))

##################################################
#   FACTURA PRODUCCIONES ALTERNATIVAS CLIENTES   #
#################################################
@login_required
def get_fact_producciones_list(request):
    # prepare the params
    try:
        fecha_desde = Fecha_Ver.objects.get()
    except Exception, e:
        fecha_desde = None
    if fecha_desde == None:
        querySet = FacturasProdAlter.objects.select_related().filter(cliente__externo=False)
    else:
        querySet = FacturasProdAlter.objects.select_related().filter(cliente__externo=False,
                                                            doc_factura__fecha_doc__gte=fecha_desde.fecha)

    columnIndexNameMap = {0: '-doc_factura__fecha_doc', 1: 'factura_nro', 2: 'admincomerciax_cliente.nombre',
                          3: 'doc_factura__fecha_doc',
                          4: 'cancelada', 5: 'confirmar'}

    searchableColumns = ['confirmar', 'cancelada', 'factura_nro', 'cliente__nombre', 'doc_factura__fecha_doc']
    # path to template used to generate json
    jsonTemplatePath = 'comercial/json/json_factura_producciones.txt'

    # call to generic function from utils
    return get_datatables_records(request, querySet, columnIndexNameMap, searchableColumns, jsonTemplatePath)


@login_required
def factura_producciones_index(request):
    if not request.user.has_perm('comercial.facturasprodalter'):
        return render_to_response("denegado.html", locals(), context_instance=RequestContext(request))
    return render_to_response('comercial/facturaproduccionesindex.html', locals(), context_instance=RequestContext(request))

@login_required
@transaction.commit_on_success()
def factura_producciones_add(request):
    if not request.user.has_perm('comercial.facturasprodalter'):
        return render_to_response("denegado.html", locals(), context_instance=RequestContext(request))

    nombre_form = 'Producciones Alternativas'
    descripcion_form = 'Realizar Factura de Producciones Alternativas'
    titulo_form = 'Producciones Alternativas'
    controlador_form = 'Producciones Alternativas'
    accion_form = '/comerciax/comercial/factura_producciones/add'
    cancelbtn_form = '/comerciax/comercial/factura_producciones/index'
    fecha_hoy = datetime.date.today().strftime("%d/%m/%Y")
    fecha_cierre = Fechacierre.objects.get(almacen='cm').fechaminima()
    fecha_maxima = Fechacierre.objects.get(almacen='cm').fechamaxima()
    c = None
    l = []
    if request.method == 'POST':
        form = FacturaProduccionesForm(request.POST)
        if form.is_valid():
            obj_cliente = Cliente.objects.get(pk=form.data['cliente1'])
            try:
                tipoc = obj_cliente.get_contrato_tipo()
            except Exception, e:
                tipoc = None

            if tipoc == None:
                l = ['Este cliente no tiene contrato por lo que no se puede realizar la factura']
                return render_to_response('comercial/facturaadd.html', {'form': form, 'form_name': nombre_form,
                                                                        'form_description': descripcion_form,
                                                                        'accion': accion_form,
                                                                        'titulo': titulo_form,
                                                                        'controlador': controlador_form,
                                                                        'cancelbtn': cancelbtn_form,
                                                                        'fecha_minima': fecha_cierre,
                                                                        'fecha_maxima': fecha_maxima,
                                                                        'error2': l},
                                          context_instance=RequestContext(request))

            pk_user = User.objects.get(pk=request.user.id)

            fact = FacturasProdAlter()

            pk_doc = uuid4()
            obj_doc = Doc()

            obj_doc.id_doc = pk_doc
            obj_doc.tipo_doc = '21'
            obj_doc.fecha_doc = form.cleaned_data['fecha']
            obj_doc.operador = pk_user
            obj_doc.fecha_operacion = datetime.date.today()
            obj_doc.observaciones = form.cleaned_data['observaciones']

            fact.doc_factura = obj_doc
            fact.factura_nro = str(random.randint(1, 100000)) + "S/C"
            fact.cliente = Cliente.objects.get(pk=form.data['cliente1'])
            fact.confirmada = hashlib.sha1(pk_doc.__str__() + 'NO').hexdigest()

            # fact.chapa = form.cleaned_data['chapa']
            # fact.licencia = form.cleaned_data['licencia']
            # fact.transportador = Transpotador.objects.get(pk=form.data['transportador'])

            try:
                obj_doc.save()
                fact.save()
                #                nume.save()
                return HttpResponseRedirect('/comerciax/comercial/factura_producciones/view/' + pk_doc.__str__())
            except Exception, e:
                exc_info = e.__str__()  # sys.exc_info()[:1]
                c = exc_info.find("DETAIL:")

                if c < 0:
                    l = l + ["Error Fatal."]
                else:
                    c = exc_info[c + 7:]
                    l = l + [c]

                transaction.rollback()
                form = FacturaProduccionesForm(request.POST)
                return render_to_response('comercial/facturaproduccionesadd.html',
                                          {'form': form, 'form_name': nombre_form, 'form_description': descripcion_form,
                                           'accion': accion_form, 'titulo': titulo_form,
                                           'controlador': controlador_form,
                                           'cancelbtn': cancelbtn_form, 'fecha_minima': fecha_cierre,
                                           'fecha_maxima': fecha_maxima, 'error2': l},
                                          context_instance=RequestContext(request))
            else:
                transaction.commit()
    else:
        meshoy = int(fecha_hoy.split('/')[1])
        mescierre = int(fecha_cierre.split('/')[1])

        if meshoy == mescierre:
            fecha_cierre = fecha_hoy
        form = FacturaProduccionesForm(initial={'fecha': fecha_cierre})

    return render_to_response('comercial/facturaproduccionesadd.html',
                              {'form': form, 'form_name': nombre_form, 'form_description': descripcion_form,
                               'accion': accion_form, 'titulo': titulo_form, 'controlador': controlador_form,
                               'cancelbtn': cancelbtn_form, 'fecha_minima': fecha_cierre, 'fecha_maxima': fecha_maxima,
                               'error2': c}, context_instance=RequestContext(request))

@login_required
def factura_producciones_view(request, idfa):
    if not request.user.has_perm('comercial.facturasprodalter'):
        return render_to_response("denegado.html", locals(), context_instance=RequestContext(request))

    l = []
    cancelar = 0
    fact = FacturasProdAlter.objects.select_related().get(pk=idfa)
    if fact.cancelada == True:
        cancelar = 1
    confir = fact.get_confirmada()
    confirmar = 2
    if confir == 'N':
        confirmar = 0
    elif confir == 'S':
        confirmar = 1

    eliminar = 1
    editar = 1
    if confirmar == 2 or confirmar == 1:
        eliminar = 0
        editar = 0

    rc_fecha = fact.doc_factura.fecha_doc.strftime("%d/%m/%Y")
    rc_cliente = fact.cliente.nombre
    rc_nro = fact.factura_nro
    importecup = fact.get_importetotalcup()
    cant_producciones = fact.cantidad_producciones()
    cant_renglones = fact.get_renglones()

    precio_CUP = "Precio CUP"
    importe_CUP = "Importe CUP"

    rc_observaciones = fact.doc_factura.observaciones
    filas = DetalleFacturaProdAlter.objects.select_related().filter(factura=idfa).all().order_by('produccionalter__descripcion')

    hay_cup = 1

    return render_to_response('comercial/viewfacturaproducciones.html', {'total_producciones': cant_producciones,
                                                                         'hay_cup': hay_cup,
                                                                      'hay_cuc': 0,
                                                             'eliminar': eliminar, 'editar': editar,
                                                             'cancelar': cancelar,
                                                             'confirmar': confirmar,
                                                             # 'importecasco': importecasco,
                                                             'precio_CUP': precio_CUP,
                                                             'importe_CUP': importe_CUP,
                                                             'importecup': importecup,
                                                             'fecha': rc_fecha,
                                                             'rc_nro': rc_nro,
                                                             'cliente': rc_cliente,
                                                             'observaciones': rc_observaciones, 'rc_id': idfa,
                                                             'elementos_detalle': filas,
                                                             'error2': l, 'cant_producciones': cant_producciones,
                                                             'cant_renglones': cant_renglones},
                              context_instance=RequestContext(request))


def verfacturaproducciones(request, idfactura, haycup, haycuc, cantproducciones):
    empresaobj1 = Empresa.objects.all()
    hay_cup = int(haycup)
    hay_cuc = int(haycuc)
    es_producciones = True
    for empresaobj in empresaobj1:
        titular_name = empresaobj.nombre
        titular_dir = empresaobj.direccion
        titular_codigo = empresaobj.codigo
        titular_email = empresaobj.email
        titular_phone = empresaobj.telefono
        titular_fax = empresaobj.fax
        titular_cuenta_mn = empresaobj.cuenta_mn
        titular_cuenta_cuc = empresaobj.cuenta_usd
        titular_sucursal_mn = empresaobj.sucursal_mn
        titular_sucursal_cuc = empresaobj.sucursal_usd

    factura = FacturasProdAlter.objects.select_related().get(doc_factura=idfactura)
    pk_user = User.objects.get(pk=request.user.id)
    # vendedor = pk_user.first_name + " " + pk_user.last_name

    user_doc = Doc.objects.get(id_doc=factura.doc_factura.id_doc).operador
    operador_ = User.objects.get(pk=user_doc.id)
    confeccionado = operador_.first_name + " " + operador_.last_name

    detallesFact = DetalleFacturaProdAlter.objects.select_related().filter(factura=idfactura).values('factura','precio_mn',
                                                                                                'produccionalter__codigo',
                                                                                                'cantidad',
                                                                                                'importe_mn',
                                                                                                'produccionalter__descripcion', \
                                                                                                'produccionalter__um__descripcion')
    for a1 in range(detallesFact.__len__()):
        detallesFact[a1]['importecup'] = str(detallesFact[a1]['importe_mn'])
        detallesFact[a1]['precio_mn'] = str(detallesFact[a1]['precio_mn'])
        detallesFact[a1]['cantidad'] = str(detallesFact[a1]['cantidad'])

    cliente = factura.cliente
    fecha_confeccionado = factura.doc_factura.fecha_doc

    cliente_codigo = cliente.codigo
    cliente_nombre = cliente.nombre
    cliente_dir = cliente.direccion
    cliente_phone = cliente.telefono
    cliente_email = cliente.email
    cliente_fax = cliente.fax

    contrato = ClienteContrato.objects.select_related().get(cliente=cliente.id, cerrado=False)
    contrato_sucursal_mn = contrato.contrato.sucursal_mn
    contrato_sucursal_cuc = contrato.contrato.sucursal_usd
    contrato_cuenta_mn = contrato.contrato.cuenta_mn
    contrato_cuenta_cuc = contrato.contrato.cuenta_usd
    contrato_nro = contrato.contrato.contrato_nro

    cancelada = factura.cancelada

    importetotalcup = factura.get_importetotalcup()
    importecup = factura.get_importecup()

    observaciones = factura.doc_factura.observaciones

    return render_to_response("report/factura.html", locals(), context_instance=RequestContext(request))

@login_required
@transaction.commit_on_success()
def factura_producciones_del(request, idfa):
    if not request.user.has_perm('comercial.facturasprodalter'):
        return render_to_response("denegado.html", locals(), context_instance=RequestContext(request))

    l = []
    fact = FacturasProdAlter.objects.get(pk=idfa)
    noelim = 0
    if fact.confirmada == hashlib.sha1(fact.pk.__str__() + 'YES').hexdigest():
        mensa = "No se puede eliminar la factura Nro. " + fact.factura_nro + " porque ya está confirmada"
        noelim = 1
    elif fact.confirmada != hashlib.sha1(fact.pk.__str__() + 'NO').hexdigest():
        mensa = "No se puede eliminar la factura Nro. " + fact.factura_nro + " porque está corrupta"
        noelim = 1
    if noelim == 1:
        l = [mensa]
        rc_fecha = fact.doc_factura.fecha_doc.strftime("%d/%m/%Y")
        rc_cliente = fact.cliente.nombre
        rc_nro = fact.factura_nro
        importecup = FacturasProdAlter.objects.get(pk=idfa).get_importetotalcup()

        pmn = ClienteContrato.objects.select_related().get(cliente=fact.cliente.id, cerrado=False)

        precio_CUP = "Precio CUP"

        rc_observaciones = fact.doc_factura.observaciones
        filas = DetalleFacturaProdAlter.objects.select_related().filter(factura=idfa).order_by('produccionalter.descripcion')

        # rc_transportador = fact.transportador.nombre
        # rc_chapa = fact.chapa
        # rc_licencia = fact.licencia
        hay_cup = 1
        # Verificar si se puede editar. Se puede editar si todos los cascos relacionados con el estado es Casco

        return render_to_response('comercial/viewfacturaproducciones.html',
                                  {'hay_cup': hay_cup, 'eliminar': 0, 'editar': 1, 'cancelar': 0,
                                   'confirmar': 0,
                                   'precio_CUP': precio_CUP, 'importecup': importecup,
                                   'rc_nro': rc_nro, 'fecha': rc_fecha, 'cliente': rc_cliente,
                                   'observaciones': rc_observaciones, 'rc_id': idfa, 'elementos_detalle': filas,
                                   'error2': l}, context_instance=RequestContext(request))
    try:
        Doc.objects.select_related().get(pk=idfa).delete()

        return HttpResponseRedirect('/comerciax/comercial/factura_producciones/index')
        # return render_to_response("casco/recepcionclienteindex.html",locals(),context_instance = RequestContext(request))
    except Exception, e:
        transaction.rollback()
        l = ['Error al eliminar el documento']
        fact = FacturasProdAlter.objects.select_related().get(pk=idfa)
        rc_fecha = fact.doc_factura.fecha_doc.strftime("%d/%m/%Y")
        rc_cliente = fact.cliente.nombre
        rc_nro = fact.factura_nro
        rc_observaciones = fact.doc_factura.observaciones
        filas = DetalleFacturaProdAlter.objects.select_related().filter(factura=idfa).order_by('produccionalter.descripcion')

        return render_to_response('comercial/viewfacturaproducciones.html',
                                  {'hay_cup': hay_cup, 'rc_nro': rc_nro, 'fecha': rc_fecha,
                                   'cliente': rc_cliente, 'observaciones': rc_observaciones, 'rc_id': idfa,
                                   'elementos_detalle': filas, 'error2': l}, context_instance=RequestContext(request))
    else:
        transaction.commit()

    return 0

@login_required
def detalleFacturaProduccion_delete(request, idfa, idproduccion):
    if not request.user.has_perm('comercial.facturasprodalter'):
        return render_to_response("denegado.html", locals(), context_instance=RequestContext(request))

    fact = FacturasProdAlter.objects.get(pk=idfa)

    l = []

    DetalleFacturaProdAlter.objects.get(produccionalter=idproduccion, factura=idfa).delete()
    cant_renglones = str(FacturasProdAlter.objects.get(doc_factura=idfa).get_renglones())
    data = []
    filas = DetalleFacturaProdAlter.objects.select_related().filter(factura=idfa).order_by('produccionalter__descripcion')
    total_produccion = str(filas.count())
    elementos_detalle = []
    importetotalcup = fact.get_importetotalcup()
    for a1 in filas:

        # importetotalcup = a1.factura.get_importetotalcup()

        elementos_detalle += [
            {
             'cant_renglones': cant_renglones,
             'id_doc': a1.factura.doc_factura.id_doc,
             'produccionalter': a1.produccionalter.descripcion,
             'codigo': a1.produccionalter.codigo,
             'importetotalcup': importetotalcup,
             'produccionalter_id': a1.produccionalter.id,
             'precio_cup': a1.format_precio_mn(),
             'um':a1.produccionalter.um.descripcion,
             'importe_cup': a1.format_importe_mn(),
             'cantidad': a1.format_cantidad()}]

    return HttpResponse(simplejson.dumps(elementos_detalle), content_type='application/javascript; charset=utf8')


@login_required
@transaction.commit_on_success()
def factura_producciones_edit(request, idfa):
    if not request.user.has_perm('comercial.factura'):
        return render_to_response("denegado.html", locals(), context_instance=RequestContext(request))

    fact = FacturasProdAlter.objects.select_related().get(pk=idfa)
    noedit = 0
    if fact.confirmada == hashlib.sha1(fact.pk.__str__() + 'YES').hexdigest():
        mensa = "No se puede editar la factura Nro. " + fact.factura_nro + " porque ya está confirmada"
        noedit = 1
    elif fact.confirmada != hashlib.sha1(fact.pk.__str__() + 'NO').hexdigest():
        mensa = "No se puede editar la factura Nro. " + fact.factura_nro + " porque está corrupta"
        noedit = 1
    if noedit == 1:
        l = [mensa]
        rc_fecha = fact.doc_factura.fecha_doc.strftime("%d/%m/%Y")
        rc_cliente = fact.cliente.nombre
        rc_nro = fact.factura_nro

        importecup = FacturasProdAlter.objects.get(pk=idfa).get_importecup()

        pmn = FacturasProdAlter.objects.select_related().get(cliente=fact.cliente.id, cerrado=False)

        precio_CUP = "Precio CUP"
        importe_CUP = "Importe CUP"


        rc_observaciones = fact.doc_factura.observaciones
        filas = DetalleFacturaProdAlter.objects.select_related().filter(factura=idfa).order_by('produccionalter.descripcion')

        # rc_transportador = fact.transportador.nombre
        # rc_chapa = fact.chapa
        # rc_licencia = fact.licencia
        hay_cup = 0

        # Verificar si se puede editar. Se puede editar si todos los cascos relacionados con el estado es Casco
        return render_to_response('comercial/viewfacturaproducciones.html',
                                  {'hay_cup': hay_cup, 'eliminar': 0, 'editar': 1, 'cancelar': 0,
                                   'confirmar': 0,
                                   'precio_CUP': precio_CUP, 'importecup': importecup,
                                   'importe_CUP': importe_CUP,
                                   'rc_nro': rc_nro, 'fecha': rc_fecha, 'cliente': rc_cliente,
                                   'observaciones': rc_observaciones, 'rc_id': idfa, 'elementos_detalle': filas,
                                   'error2': l}, context_instance=RequestContext(request))

    nombre_form = 'Facturas Producciones Alternativas'
    descripcion_form = 'Realizar Factura de Producciones Alternativas a Clientes'
    titulo_form = 'Facturas Producciones Alternativas'
    controlador_form = 'Facturas Producciones Alternativas'
    accion_form = '/comerciax/comercial/factura_producciones/edit/' + idfa + '/'
    cancelbtn_form = '/comerciax/comercial/factura_producciones/view/' + idfa + '/'
    fecha_cierre = Fechacierre.objects.get(almacen='cm').fechaminima()
    fecha_maxima = Fechacierre.objects.get(almacen='cm').fechamaxima()
    c = None

    l = []

    detalles = DetalleFacturaProdAlter.objects.filter(factura=idfa).count()

    if request.method == 'POST':
        if detalles == 0:
            form = FacturaProduccionesForm(request.POST)
        else:
            form = FacturaProduccionesForm2(request.POST)
        if form.is_valid():
            if detalles == 0:
                cc = form.data['cliente1']
            else:
                cc = form.data['cliente']
            if (cc.find("|") < 0):
                obj_cliente = Cliente.objects.get(pk=cc)
            else:
                obj_cliente = Cliente.objects.get(pk=fact.cliente.id)
            try:
                tipoc = obj_cliente.get_contrato_tipo()
            except Exception, e:
                tipoc = None

            if tipoc == None:
                l = ['Este cliente no tiene contrato por lo que no se puede realizar la factura']
                return render_to_response('form/form_adddetalle.html',
                                          {'tipocliente': '0', 'form': form, 'form_name': nombre_form,
                                           'form_description': descripcion_form, 'accion': accion_form,
                                           'titulo': titulo_form, 'controlador': controlador_form,
                                           'cancelbtn': cancelbtn_form, 'fecha_minima': fecha_cierre,
                                           'fecha_maxima': fecha_maxima,
                                           'error2': l}, context_instance=RequestContext(request))

            pk_user = User.objects.get(pk=request.user.id)

            fact = FacturasProdAlter.objects.get(pk=idfa)
            doc = Doc.objects.get(pk=idfa)

            doc.fecha_doc = form.cleaned_data['fecha']
            doc.operador = pk_user
            doc.doc_operacion = datetime.date.today()
            doc.observaciones = form.cleaned_data['observaciones']
            fact.cliente = obj_cliente


            try:
                doc.save()
                fact.save()

                return HttpResponseRedirect('/comerciax/comercial/factura_producciones/view/' + idfa)

            except Exception, e:
                exc_info = e.__str__()  # sys.exc_info()[:1]
                c = exc_info.find("DETAIL:")

                if c < 0:
                    l = l + ["Error Fatal."]
                else:
                    c = exc_info[c + 7:]
                    l = l + [c]

                transaction.rollback()

                form = FacturaProduccionesForm(request.POST)
                return render_to_response('form/form_adddetalle.html',
                                          {'tipocliente': '0', 'form': form, 'form_name': nombre_form,
                                           'form_description': descripcion_form,
                                           'accion': accion_form, 'titulo': titulo_form,
                                           'controlador': controlador_form,
                                           'cancelbtn': cancelbtn_form, 'fecha_minima': fecha_cierre,
                                           'fecha_maxima': fecha_maxima, 'error2': l},
                                          context_instance=RequestContext(request))
            else:
                transaction.commit()
    else:
        if detalles == 0:
            form = FacturaProduccionesForm(
                initial={
                         'nro': fact.factura_nro, 'fecha': fact.doc_factura.fecha_doc,
                         'cliente1': fact.cliente, 'observaciones': fact.doc_factura.observaciones})
        else:

            form = FacturaProduccionesForm2(initial={
                                         'fecha': fact.doc_factura.fecha_doc,
                                         'cliente': fact.cliente,
                                         'observaciones': fact.doc_factura.observaciones})

    return render_to_response('comercial/facturaproduccionesedit.html',
                              {'form': form, 'form_name': nombre_form, 'form_description': descripcion_form,
                               'accion': accion_form, 'titulo': titulo_form, 'controlador': controlador_form,
                               'cancelbtn': cancelbtn_form, 'fecha_minima': fecha_cierre, 'fecha_maxima': fecha_maxima},
                              context_instance=RequestContext(request))

@login_required
@transaction.commit_on_success()
def factura_producciones_confirmar(request, idfa):
    if not request.user.has_perm('comercial.factura'):
        return render_to_response("denegado.html", locals(), context_instance=RequestContext(request))

    l = []
    fact = FacturasProdAlter.objects.get(pk=idfa)
    if fact.get_renglones() > 30:
        l = []
        cancelar = 0
        fact = FacturasProdAlter.objects.select_related().get(pk=idfa)
        if fact.cancelada == True:
            cancelar = 1
        confir = fact.get_confirmada()
        confirmar = 2
        if confir == 'N':
            confirmar = 0
        elif confir == 'S':
            confirmar = 1

        eliminar = 1
        editar = 1
        if confirmar == 2 or confirmar == 1:
            eliminar = 0
            editar = 0

        rc_fecha = fact.doc_factura.fecha_doc.strftime("%d/%m/%Y")
        rc_cliente = fact.cliente.nombre
        rc_nro = fact.factura_nro
        importecup = fact.get_importetotalcup()
        importecuc = fact.get_importecuc()
        cant_renglones = fact.get_renglones()
        pmn = ClienteContrato.objects.select_related().get(cliente=fact.cliente.id, cerrado=False)
        mncosto = pmn.contrato.preciocostomn
        cuccosto = pmn.contrato.preciocostocuc

        precio_CUP = "Precio CUP"

        rc_observaciones = fact.doc_factura.observaciones
        filas = DetalleFacturaProdAlter.objects.select_related().filter(factura=idfa).order_by(
            'produccionalter__descripcion')


        hay_cup = 1
        l = ["La factura excede los 30 renglones, no se puede confirmar"]
        return render_to_response('comercial/viewfacturaproducciones.html',
                                  {'hay_cup': hay_cup, 'eliminar': eliminar, 'editar': editar,
                                   'cancelar': cancelar, 'confirmar': confirmar,
                                   'precio_CUP': precio_CUP, 'importecup': importecup,
                                   'rc_nro': rc_nro, 'fecha': rc_fecha, 'cliente': rc_cliente,
                                   'observaciones': rc_observaciones, 'rc_id': idfa, 'elementos_detalle': filas,
                                   'error2': l, 'cant_renglones': cant_renglones},
                                  context_instance=RequestContext(request))

    else:

        pk_user = User.objects.get(pk=request.user.id)
        nrodoc = 1
        if NumeroDoc.objects.count() != 0:
            nrodoc = NumeroDoc.objects.get().nro_factura_prodalter + 1
        nume = NumeroDoc()
        if NumeroDoc.objects.count() == 0:
            nume.id_numerodoc = uuid4()
        else:
            nume = NumeroDoc.objects.get()
        nume.nro_factura_prodalter = nrodoc
        nume.save()
        Doc.objects.filter(pk=FacturasProdAlter.objects.get(pk=idfa).doc_factura).update(operador=pk_user)
        FacturasProdAlter.objects.filter(pk=idfa).update(confirmada=hashlib.sha1(idfa.__str__() + 'YES').hexdigest(),
                                                factura_nro=nrodoc, confirmar=True)
        return HttpResponseRedirect('/comerciax/comercial/factura_producciones/view/' + idfa)

@login_required
@transaction.commit_on_success()
def factura_producciones_cancelar(request, idfa):
    if not request.user.has_perm('comercial.factura'):
        return render_to_response("denegado.html", locals(), context_instance=RequestContext(request))

    l = []
    fact = FacturasProdAlter.objects.get(pk=idfa)
    pagosfact = 0.0
    if fact.confirmada != hashlib.sha1(fact.pk.__str__() + 'YES').hexdigest() or pagosfact != 0:
        mensa = "No se puede cancelar la factura Nro. " + fact.factura_nro + " porque no está confirmada"
        if pagosfact > 0:
            mensa = "No se puede cancelar la factura Nro. " + fact.factura_nro + " porque se han realizado pagos"
        l = [mensa]
        rc_fecha = fact.doc_factura.fecha_doc.strftime("%d/%m/%Y")
        rc_cliente = fact.cliente.nombre
        rc_nro = fact.factura_nro
        importecup = fact.get_importetotalcup()

        precio_CUP = "Precio CUP"

        rc_observaciones = fact.doc_factura.observaciones
        filas = DetalleFacturaProdAlter.objects.select_related().filter(factura=idfa).order_by('produccionalter.descripcion')


        # Verificar si se puede editar. Se puede editar si todos los cascos relacionados con el estado es Casco
        hay_cup = 1
        return render_to_response('comercial/viewfacturaproducciones.html',
                                  {'hay_cup': hay_cup, 'eliminar': 0, 'editar': 1, 'cancelar': 0,
                                   'confirmar': 0,
                                   'precio_CUP': precio_CUP, 'importecup': importecup,
                                   'rc_nro': rc_nro, 'fecha': rc_fecha, 'cliente': rc_cliente,
                                   'observaciones': rc_observaciones, 'rc_id': idfa, 'elementos_detalle': filas,
                                   'error2': l}, context_instance=RequestContext(request))

    try:
        hay_cup = 1

        FacturasProdAlter.objects.filter(pk=idfa).update(cancelada=True)
        pk_user = User.objects.get(pk=request.user.id)
        Doc.objects.filter(pk=FacturasProdAlter.objects.get(pk=idfa).doc_factura).update(operador=pk_user)

        return HttpResponseRedirect('/comerciax/comercial/factura_producciones/index')
    except Exception, e:
        transaction.rollback()
        l = ['Error al cancelar factura']
        fact = FacturasProdAlter.objects.select_related().get(pk=idfa)
        importecup = fact.get_importetotalcup()

        rc_fecha = fact.doc_factura.fecha_doc.strftime("%d/%m/%Y")
        rc_cliente = fact.cliente.nombre
        rc_nro = fact.factura_nro
        rc_observaciones = fact.doc_factura.observaciones

        precio_CUP = "Precio CUP"
        return render_to_response('comercial/viewfacturaproducciones.html',
                                  {'hay_cup': hay_cup,
                                   'precio_CUP': precio_CUP, 'importecup': importecup,
                                   'rc_nro': rc_nro, 'fecha': rc_fecha, 'cliente': rc_cliente,
                                   'observaciones': rc_observaciones, 'rc_id': idfa, 'elementos_detalle': filas,
                                   'error2': l, 'cantcascos': '4'}, context_instance=RequestContext(request))
    else:
        transaction.commit()


@login_required
# @transaction.commit_on_success()
def detalleFacturaProducciones_add(request, idfa):
    if not request.user.has_perm('comercial.factura'):
        return render_to_response("denegado.html", locals(), context_instance=RequestContext(request))

    l = []
    fact = FacturasProdAlter.objects.prefetch_related('detallefacturaprodalter_set').get(pk=idfa)
    producc = [x.produccionalter.id for x in fact.detallefacturaprodalter_set.all()]

    producciones = ProdAlter.objects.all().exclude(pk__in=producc).order_by('descripcion')
    noelim = 0
    if fact.confirmada == hashlib.sha1(fact.pk.__str__() + 'YES').hexdigest():
        mensa = "No se puede adicionar producciones a la factura Nro. " + fact.factura_nro + " porque ya está confirmada"
        noelim = 1
    elif fact.confirmada != hashlib.sha1(fact.pk.__str__() + 'NO').hexdigest():
        mensa = "No se puede adcionar producciones a la factura Nro. " + fact.factura_nro + " porque está corrupta"
        noelim = 1
    if noelim == 1:
        l = [mensa]
        rc_fecha = fact.doc_factura.fecha_doc.strftime("%d/%m/%Y")
        rc_cliente = fact.cliente.nombre
        rc_clientecomercializador = fact.cliente.comercializadora
        rc_nro = fact.factura_nro
        importecup = fact.get_importe_totalcup()

        precio_CUP = "Precio CUP"

        rc_observaciones = fact.doc_factura.observaciones
        filas = fact.detallefacturaprodalter_set.all().order_by('produccionalter.descripcion')


        # Verificar si se puede editar. Se puede editar si todos los cascos relacionados con el estado es Casco
        hay_cup = 1
        return render_to_response('comercial/viewfacturaproducciones.html',
                                  {'hay_cup': hay_cup,  'eliminar': 0, 'editar': 1, 'cancelar': 0,
                                   'confirmar': 0,
                                   'precio_CUP': precio_CUP, 'importecup': importecup,
                                   'rc_nro': rc_nro, 'fecha': rc_fecha, 'cliente': rc_cliente,
                                   'observaciones': rc_observaciones, 'rc_id': idfa,
                                   'elementos_detalle': filas,
                                   'error2': l}, context_instance=RequestContext(request))

    titulo_form = 'Facturas de Producciones Alternativas'
    nombre_form = 'Facturas de Producciones Alternativas'
    controlador_form = 'Facturas de Producciones Alternativas'
    descripcion_form = 'Seleccionar Producción Alternativa para la factura'

    accion_form = 'detalleFacturaProducciones_add'
    cancelbtn_form = '/comerciax/comercial/factura_producciones/view/' + idfa

    if request.method == 'POST':
        # pmn = ClienteContrato.objects.select_related().get(cliente=fact.cliente.id, cerrado=False)
        # mn = pmn.contrato.preciomn
        form = DetalleFacturaProdAlterForm(request.POST)
        if form.is_valid():
            cantidad = form.cleaned_data['cantidad']
            if Decimal(form.data['cantidad']) < 0.01:
                l=['La cantidad debe ser mayor que 0.00']
                return render_to_response('form/form_add.html',
                                          {'form': form, 'form_name': nombre_form, 'form_description': descripcion_form,
                                           'accion': accion_form, 'titulo': titulo_form, 'controlador': controlador_form,
                                           'cancelbtn': cancelbtn_form, 'error2': l},
                                          context_instance=RequestContext(request))
            producto = form.cleaned_data['producto']
            detalle = DetalleFacturaProdAlter.objects.filter(factura=idfa, produccionalter=producto)
            if detalle:
                detalle = DetalleFacturaProdAlter.objects.get(factura=idfa, produccionalter=producto)
                detalle.cantidad = detalle.cantidad + cantidad
                detalle.importe_mn = utils.redondeo(detalle.cantidad * detalle.precio_mn,2)
            else:
                detalle = DetalleFacturaProdAlter()
                detalle.id_detalle = uuid4()
                detalle.cantidad = cantidad
                detalle.produccionalter = producto
                detalle.precio_mn = producto.precio_mn
                detalle.importe_mn = utils.redondeo(detalle.cantidad * detalle.precio_mn,2)
                detalle.factura = fact
            detalle.save()
        if request.POST.__contains__('submit1'):
            return HttpResponseRedirect('/comerciax/comercial/factura_producciones/view/' + idfa)

    form = DetalleFacturaProdAlterForm()
    return render_to_response('form/form_add.html',
                              {'form': form, 'form_name': nombre_form, 'form_description': descripcion_form,
                               'accion': accion_form, 'titulo': titulo_form, 'controlador': controlador_form,
                               'cancelbtn': cancelbtn_form, 'error2': l}, context_instance=RequestContext(request))


@login_required
@transaction.commit_on_success()
def detalleFacturaProduccion_edit(request, idfa, idproduccion):
    if not request.user.has_perm('comercial.factura'):
        return render_to_response("denegado.html", locals(), context_instance=RequestContext(request))

    c = None
    l = []

    nombre_form = 'Editar Producción Alternativa Facturada'
    descripcion_form = 'Editar Producción Alternativa Facturada'
    titulo_form = 'Editar Producción Alternativa Facturada'
    controlador_form = 'Editar Producción Alternativa Facturada'
    accion_form = 'detalleFacturaProduccion_edit/' + idfa + '/' + idproduccion
    cancelbtn_form = '/comerciax/comercial/factura_producciones/view/' + idfa + '/'

    if request.method == 'POST':
        form = DetalleFacturaProdAlterForm2(request.POST)

        if form.is_valid():
            fact = FacturasProdAlter.objects.select_related().get(pk=idfa)

            prodsave = ProdAlter.objects.get(pk=idproduccion)
            detalle = DetalleFacturaProdAlter.objects.get(produccionalter=prodsave, factura=fact)

            try:

                detalle.cantidad = form.data['cantidad']
                detalle.precio_mn = prodsave.precio_mn
                detalle.importe_mn = prodsave.precio_mn * Decimal(form.data['cantidad'])
                detalle.save()
                importecup = FacturasProdAlter.objects.get(pk=idfa).get_importetotalcup()
                return factura_producciones_view(request, idfa)
            except Exception, e:
                exc_info = e.__str__()  # sys.exc_info()[:1]
                c = exc_info.find("DETAIL:")
                if c < 0:
                    l = l + ["Error Fatal."]
                else:
                    c = exc_info[c + 7:]
                    # l=l+[c]
                    l = ['Error al cambiar la medida de salida del casco']
                transaction.rollback()
                form = DetalleFacturaProdAlterForm2(request.POST)
                return render_to_response("form/form_edit.html",
                                          {'tipocliente': '0', 'form': form, 'title': titulo_form,
                                           'form_name': nombre_form, 'form_description': descripcion_form,
                                           'controlador': controlador_form, 'accion': accion_form
                                              , 'cancelbtn': cancelbtn_form, 'error2': l},
                                          context_instance=RequestContext(request))
            else:
                transaction.commit()
    else:
        rp = ProdAlter.objects.select_related().get(pk=idproduccion)
        fact = FacturasProdAlter.objects.select_related().get(pk=idfa)
        detalle = DetalleFacturaProdAlter.objects.get(produccionalter=rp, factura=fact)
        form = DetalleFacturaProdAlterForm2(initial={'producto': rp, 'cantidad':detalle.cantidad})
        return render_to_response('form/form_edit.html', {'form': form, 'form_name': nombre_form,
                                                          'form_description': descripcion_form, 'accion': accion_form,
                                                          'titulo': titulo_form, 'controlador': controlador_form,
                                                          'cancelbtn': cancelbtn_form},
                                  context_instance=RequestContext(request))
    return factura_producciones_view(request, idfa)


####################################################
#   FACTURA PRODUCCIONES ALTERNATIVAS PARTICULAR   #
####################################################
@login_required
def get_fact_produccionespart_list(request):
    # prepare the params
    # prepare the params
    try:
        fecha_desde = Fecha_Ver.objects.get()
    except Exception, e:
        fecha_desde = None
    if fecha_desde == None:
        querySet = FacturasProdAlterPart.objects.select_related().all()
    else:
        querySet = FacturasProdAlterPart.objects.select_related().filter(doc_factura__fecha_doc__gte=fecha_desde.fecha)
    # querySet = querySet.filter(doc__fecha_doc__year=2010)

    columnIndexNameMap = {0: '-doc_factura__fecha_doc', 1: 'factura_nro', 2: 'doc_factura__fecha_doc', 3: 'nombre',
                          4: 'ci', 5: 'cancelada', 6: 'confirmar'}

    # {0: 'oferta_nro',1: 'oferta_nro',2:'admincomerciax_cliente.nombre',3:'doc_oferta__fecha_oferta',4:'oferta_tipo'}

    searchableColumns = ['factura_nro', 'nombre', 'ci', 'confirmar', 'doc_factura__fecha_doc']
    # path to template used to generate json
    jsonTemplatePath = 'comercial/json/json_facturaprodpart.txt'

    # call to generic function from utils
    return get_datatables_records(request, querySet, columnIndexNameMap, searchableColumns, jsonTemplatePath)

@login_required
def factura_produccionespart_index(request):
    if not request.user.has_perm('comercial.facturasprodalter'):
        return render_to_response("denegado.html", locals(), context_instance=RequestContext(request))
    return render_to_response('comercial/facturaproduccionespartindex.html', locals(), context_instance=RequestContext(request))

@login_required
@transaction.commit_on_success()
def factura_produccionespart_add(request):
    if not request.user.has_perm('comercial.facturasprodalter'):
        return render_to_response("denegado.html", locals(), context_instance=RequestContext(request))

    nombre_form = 'Producciones Alternativas Particular'
    descripcion_form = 'Realizar Factura de Producciones Alternativas Particular'
    titulo_form = 'Producciones Alternativas Particular'
    controlador_form = 'Producciones Alternativas Particular'
    accion_form = '/comerciax/comercial/factura_produccionespart/add'
    cancelbtn_form = '/comerciax/comercial/factura_produccionespart/index'
    fecha_hoy = datetime.date.today().strftime("%d/%m/%Y")
    fecha_cierre = Fechacierre.objects.get(almacen='cm').fechaminima()
    fecha_maxima = Fechacierre.objects.get(almacen='cm').fechamaxima()
    c = None
    l = []
    if request.method == 'POST':
        form = FacturaProduccionesPartForm(request.POST)
        if form.is_valid():

            pk_user = User.objects.get(pk=request.user.id)

            fact = FacturasProdAlterPart()

            pk_doc = uuid4()
            obj_doc = Doc()

            obj_doc.id_doc = pk_doc
            obj_doc.tipo_doc = '22'
            obj_doc.fecha_doc = form.cleaned_data['fecha']
            obj_doc.operador = pk_user
            obj_doc.fecha_operacion = datetime.date.today()
            obj_doc.observaciones = form.cleaned_data['observaciones']

            fact.doc_factura = obj_doc
            fact.factura_nro = str(random.randint(1, 100000)) + "S/C"
            fact.nombre = form.cleaned_data['nombre']
            fact.ci = form.cleaned_data['ci']
            fact.recargo = form.cleaned_data['recargo']
            fact.confirmada = hashlib.sha1(pk_doc.__str__() + 'NO').hexdigest()

            try:
                obj_doc.save()
                fact.save()
                #                nume.save()
                return HttpResponseRedirect('/comerciax/comercial/factura_produccionespart/view/' + pk_doc.__str__())
            except Exception, e:
                exc_info = e.__str__()  # sys.exc_info()[:1]
                c = exc_info.find("DETAIL:")

                if c < 0:
                    l = l + ["Error Fatal."]
                else:
                    c = exc_info[c + 7:]
                    l = l + [c]

                transaction.rollback()
                form = FacturaProduccionesPartForm(request.POST)
                return render_to_response('comercial/facturaproduccionespartadd.html',
                                          {'form': form, 'form_name': nombre_form,
                                           'form_description': descripcion_form,
                                           'accion': accion_form, 'titulo': titulo_form,
                                           'controlador': controlador_form,
                                           'cancelbtn': cancelbtn_form, 'fecha_minima': fecha_cierre,
                                           'fecha_maxima': fecha_maxima, 'error2': l},
                                          context_instance=RequestContext(request))
            else:
                transaction.commit()
    else:
        meshoy = int(fecha_hoy.split('/')[1])
        mescierre = int(fecha_cierre.split('/')[1])

        if meshoy == mescierre:
            fecha_cierre = fecha_hoy
        form = FacturaProduccionesPartForm(initial={'fecha': fecha_cierre})

    return render_to_response('comercial/facturaproduccionespartadd.html',
                              {'form': form, 'form_name': nombre_form, 'form_description': descripcion_form,
                               'accion': accion_form, 'titulo': titulo_form, 'controlador': controlador_form,
                               'cancelbtn': cancelbtn_form, 'fecha_minima': fecha_cierre,
                               'fecha_maxima': fecha_maxima,
                               'error2': c}, context_instance=RequestContext(request))

@login_required
def factura_produccionespart_view(request, idfa):
    if not request.user.has_perm('comercial.facturasprodalter'):
        return render_to_response("denegado.html", locals(), context_instance=RequestContext(request))

    l = []
    cancelar = 0
    fact = FacturasProdAlterPart.objects.select_related().get(pk=idfa)
    if fact.cancelada == True:
        cancelar = 1
    confir = fact.get_confirmada()
    confirmar = 2
    if confir == 'N':
        confirmar = 0
    elif confir == 'S':
        confirmar = 1

    eliminar = 1
    editar = 1
    if confirmar == 2 or confirmar == 1:
        eliminar = 0
        editar = 0

    rc_fecha = fact.doc_factura.fecha_doc.strftime("%d/%m/%Y")
    nombre = fact.nombre
    ci = fact.ci
    rc_nro = fact.factura_nro
    importecup = fact.get_importetotalcup()
    cant_producciones = fact.cantidad_producciones()
    recargo = fact.recargo
    cant_renglones = fact.get_renglones()
    totalpagar = fact.get_importe_total(recargo)

    precio_CUP = "Precio CUP"
    importe_CUP = "Importe CUP"

    rc_observaciones = fact.doc_factura.observaciones
    filas = DetalleFacturaProdAlterPart.objects.select_related().filter(factura=idfa).all().order_by('produccionalter__descripcion')

    hay_cup = 1

    return render_to_response('comercial/viewfacturaproduccionespart.html', {'total_producciones': cant_producciones,
                                                                         'hay_cup': hay_cup,
                                                                      'hay_cuc': 0,
                                                             'eliminar': eliminar, 'editar': editar,
                                                             'cancelar': cancelar,
                                                             'confirmar': confirmar,
                                                             'recargo': fact.format_recargo(),
                                                             'precio_CUP': precio_CUP,
                                                             'importe_CUP': importe_CUP,
                                                             'importecup': importecup,
                                                             'fecha': rc_fecha,
                                                             'rc_nro': rc_nro,
                                                             'nombre': nombre,
                                                             'ci': ci,
                                                             'totalpagar': totalpagar,
                                                             'observaciones': rc_observaciones, 'rc_id': idfa,
                                                             'elementos_detalle': filas,
                                                             'error2': l, 'cant_producciones': cant_producciones,
                                                             'cant_renglones': cant_renglones},
                              context_instance=RequestContext(request))

def verfacturaproduccionespart(request, idfactura, haycup, haycuc, cantproducciones):
    empresaobj1 = Empresa.objects.all()
    hay_cup = int(haycup)
    hay_cuc = int(haycuc)
    es_producciones = True
    for empresaobj in empresaobj1:
        titular_name = empresaobj.nombre
        titular_dir = empresaobj.direccion
        titular_codigo = empresaobj.codigo
        titular_email = empresaobj.email
        titular_phone = empresaobj.telefono
        titular_fax = empresaobj.fax
        titular_cuenta_mn = empresaobj.cuenta_mn
        titular_cuenta_cuc = empresaobj.cuenta_usd
        titular_sucursal_mn = empresaobj.sucursal_mn
        titular_sucursal_cuc = empresaobj.sucursal_usd
    factura = FacturasProdAlterPart.objects.select_related().get(doc_factura=idfactura)
    pk_user = User.objects.get(pk=request.user.id)
    # vendedor = pk_user.first_name + " " + pk_user.last_name

    user_doc = Doc.objects.get(id_doc=factura.doc_factura.id_doc).operador
    operador_ = User.objects.get(pk=user_doc.id)
    confeccionado = operador_.first_name + " " + operador_.last_name

    cliente_codigo = factura.ci
    cliente_nombre = factura.nombre

    detallesFact = DetalleFacturaProdAlterPart.objects.select_related().filter(factura=idfactura).values('factura','precio_mn',
                                                                                                'produccionalter__codigo',
                                                                                                'cantidad',
                                                                                                'importe_mn',
                                                                                                'produccionalter__descripcion',
                                                                                                'produccionalter__um__descripcion')
    for a1 in range(detallesFact.__len__()):

        detallesFact[a1]['importecup'] = str(detallesFact[a1]['importe_mn'])
        detallesFact[a1]['precio_mn'] = str(detallesFact[a1]['precio_mn'])
        detallesFact[a1]['cantidad'] = str(detallesFact[a1]['cantidad'])

    nombre = factura.nombre
    ci = factura.ci
    fecha_confeccionado = factura.doc_factura.fecha_doc


    importetotalcup = factura.get_importetotalcup()
    importecup = factura.get_importecup()

    observaciones = factura.doc_factura.observaciones

    if factura.recargo > 0.0:
        recargo = float(factura.recargo)
        importe_ = float(importetotalcup.replace(' ', '').replace(',', '').replace('$', ''))
        val = utils.redondeo((importe_ * recargo)/100, 2)
        importetotalcup_ = utils.redondeo(importe_ + val,2)
        importetotalcup_ = '$' + '{:20,.2f}'.format(importetotalcup_)
        recargo = str(float(factura.recargo))

    return render_to_response("report/factura.html", locals(), context_instance=RequestContext(request))

@login_required
@transaction.commit_on_success()
def factura_produccionespart_del(request, idfa):
    if not request.user.has_perm('comercial.facturasprodalter'):
        return render_to_response("denegado.html", locals(), context_instance=RequestContext(request))

    l = []
    fact = FacturasProdAlterPart.objects.get(pk=idfa)
    totalpagar = fact.get_importe_total(fact.recargo)
    noelim = 0
    if fact.confirmada == hashlib.sha1(fact.pk.__str__() + 'YES').hexdigest():
        mensa = "No se puede eliminar la factura Nro. " + fact.factura_nro + " porque ya está confirmada"
        noelim = 1
    elif fact.confirmada != hashlib.sha1(fact.pk.__str__() + 'NO').hexdigest():
        mensa = "No se puede eliminar la factura Nro. " + fact.factura_nro + " porque está corrupta"
        noelim = 1
    if noelim == 1:
        l = [mensa]
        rc_fecha = fact.doc_factura.fecha_doc.strftime("%d/%m/%Y")
        rc_cliente = fact.cliente.nombre
        rc_nro = fact.factura_nro
        importecup = fact.get_importetotalcup()


        precio_CUP = "Precio CUP"

        rc_observaciones = fact.doc_factura.observaciones
        filas = DetalleFacturaProdAlterPart.objects.select_related().filter(factura=idfa).order_by('produccionalter.descripcion')

        hay_cup = 1
        # Verificar si se puede editar. Se puede editar si todos los cascos relacionados con el estado es Casco

        return render_to_response('comercial/viewfacturaproduccionespart.html',
                                  {'hay_cup': hay_cup, 'eliminar': 0, 'editar': 1, 'cancelar': 0,
                                   'confirmar': 0,
                                   'precio_CUP': precio_CUP, 'importecup': importecup,
                                   'rc_nro': rc_nro, 'fecha': rc_fecha, 'nombre': fact.nombre,
                                   'ci':fact.ci, 'recargo':fact.format_recargo(),
                                   'totalpagar': totalpagar,
                                   'observaciones': rc_observaciones, 'rc_id': idfa, 'elementos_detalle': filas,
                                   'error2': l}, context_instance=RequestContext(request))
    try:
        Doc.objects.select_related().get(pk=idfa).delete()

        return HttpResponseRedirect('/comerciax/comercial/factura_produccionespart/index')
        # return render_to_response("casco/recepcionclienteindex.html",locals(),context_instance = RequestContext(request))
    except Exception, e:
        transaction.rollback()
        l = ['Error al eliminar el documento']
        fact = FacturasProdAlterPart.objects.select_related().get(pk=idfa)
        rc_fecha = fact.doc_factura.fecha_doc.strftime("%d/%m/%Y")
        nombre = fact.nombre
        ci = fact.ci
        racargo = fact.recargo
        rc_nro = fact.factura_nro
        rc_observaciones = fact.doc_factura.observaciones
        filas = DetalleFacturaProdAlterPart.objects.select_related().filter(factura=idfa).order_by('produccionalter.descripcion')

        return render_to_response('comercial/viewfacturaproduccionespart.html',
                                  {'rc_nro': rc_nro, 'fecha': rc_fecha,
                                   'nombre': nombre, 'ci':ci, 'recargo':fact.format_recargo(),
                                   'totalpagar': totalpagar,
                                   'observaciones': rc_observaciones, 'rc_id': idfa,
                                   'elementos_detalle': filas, 'error2': l}, context_instance=RequestContext(request))
    else:
        transaction.commit()

    return 0

@login_required
@transaction.commit_on_success()
def factura_produccionespart_edit(request, idfa):
    if not request.user.has_perm('comercial.factura'):
        return render_to_response("denegado.html", locals(), context_instance=RequestContext(request))

    fact = FacturasProdAlterPart.objects.select_related().get(pk=idfa)
    totalpagar = fact.get_importe_total(fact.recargo)
    noedit = 0
    if fact.confirmada == hashlib.sha1(fact.pk.__str__() + 'YES').hexdigest():
        mensa = "No se puede editar la factura Nro. " + fact.factura_nro + " porque ya está confirmada"
        noedit = 1
    elif fact.confirmada != hashlib.sha1(fact.pk.__str__() + 'NO').hexdigest():
        mensa = "No se puede editar la factura Nro. " + fact.factura_nro + " porque está corrupta"
        noedit = 1
    if noedit == 1:
        l = [mensa]
        rc_fecha = fact.doc_factura.fecha_doc.strftime("%d/%m/%Y")
        rc_cliente = fact.cliente.nombre
        rc_nro = fact.factura_nro

        importecup = fact.get_importecup()

        # pmn = FacturasProdAlter.objects.select_related().get(cliente=fact.cliente.id, cerrado=False)

        precio_CUP = "Precio CUP"
        importe_CUP = "Importe CUP"


        rc_observaciones = fact.doc_factura.observaciones
        filas = DetalleFacturaProdAlterPart.objects.select_related().filter(factura=idfa).order_by('produccionalter.descripcion')


        hay_cup = 0

        # Verificar si se puede editar. Se puede editar si todos los cascos relacionados con el estado es Casco
        return render_to_response('comercial/viewfacturaproduccionespart.html',
                                  {'hay_cup': hay_cup, 'eliminar': 0, 'editar': 1, 'cancelar': 0,
                                   'confirmar': 0,
                                   'precio_CUP': precio_CUP, 'importecup': importecup,
                                   'importe_CUP': importe_CUP,
                                   'rc_nro': rc_nro, 'fecha': rc_fecha, 'nombre': fact.nombre,
                                   'ci': fact.ci, 'recargo': fact.format_recargo(),
                                   'totalpagar': totalpagar,
                                   'observaciones': rc_observaciones, 'rc_id': idfa, 'elementos_detalle': filas,
                                   'error2': l}, context_instance=RequestContext(request))

    nombre_form = 'Facturas Producciones Alternativas'
    descripcion_form = 'Realizar Factura de Producciones Alternativas a Particulares'
    titulo_form = 'Facturas Producciones Alternativas'
    controlador_form = 'Facturas Producciones Alternativas'
    accion_form = '/comerciax/comercial/factura_produccionespart/edit/' + idfa + '/'
    cancelbtn_form = '/comerciax/comercial/factura_produccionespart/view/' + idfa + '/'
    fecha_cierre = Fechacierre.objects.get(almacen='cm').fechaminima()
    fecha_maxima = Fechacierre.objects.get(almacen='cm').fechamaxima()
    c = None

    l = []

    detalles = DetalleFacturaProdAlterPart.objects.filter(factura=idfa).count()

    if request.method == 'POST':
        form = FacturaProduccionesPartForm(request.POST)

        if form.is_valid():
            nombre = form.data['nombre']
            ci = form.data['ci']
            recargo = form.data['recargo']
            pk_user = User.objects.get(pk=request.user.id)

            fact = FacturasProdAlterPart.objects.get(pk=idfa)
            doc = Doc.objects.get(pk=idfa)

            doc.fecha_doc = form.cleaned_data['fecha']
            doc.operador = pk_user
            doc.doc_operacion = datetime.date.today()
            doc.observaciones = form.cleaned_data['observaciones']
            fact.nombre = nombre
            fact.ci = ci
            fact.recargo = recargo
            fact.observaciones = form.data['observaciones']

            try:
                doc.save()
                fact.save()

                return HttpResponseRedirect('/comerciax/comercial/factura_produccionespart/view/' + idfa)

            except Exception, e:
                exc_info = e.__str__()  # sys.exc_info()[:1]
                c = exc_info.find("DETAIL:")

                if c < 0:
                    l = l + ["Error Fatal."]
                else:
                    c = exc_info[c + 7:]
                    l = l + [c]

                transaction.rollback()

                form = FacturaProduccionesPartForm(request.POST)
                return render_to_response('form/form_adddetalle.html',
                                          {'tipocliente': '0', 'form': form, 'form_name': nombre_form,
                                           'form_description': descripcion_form,
                                           'accion': accion_form, 'titulo': titulo_form,
                                           'controlador': controlador_form,
                                           'cancelbtn': cancelbtn_form, 'fecha_minima': fecha_cierre,
                                           'fecha_maxima': fecha_maxima, 'error2': l},
                                          context_instance=RequestContext(request))
            else:
                transaction.commit()
    else:
        form = FacturaProduccionesPartForm(
            initial={
                     'nro': fact.factura_nro, 'fecha': fact.doc_factura.fecha_doc,
                     'nombre': fact.nombre, 'ci': fact.ci,
                      'recargo': fact.recargo,
                      'observaciones': fact.doc_factura.observaciones})

    return render_to_response('comercial/facturaproduccionespartedit.html',
                              {'form': form, 'form_name': nombre_form, 'form_description': descripcion_form,
                               'accion': accion_form, 'titulo': titulo_form, 'controlador': controlador_form,
                               'cancelbtn': cancelbtn_form, 'fecha_minima': fecha_cierre, 'fecha_maxima': fecha_maxima},
                              context_instance=RequestContext(request))

@login_required
# @transaction.commit_on_success()
def detalleFacturaProduccionesPart_add(request, idfa):
    if not request.user.has_perm('comercial.factura'):
        return render_to_response("denegado.html", locals(), context_instance=RequestContext(request))

    l = []
    fact = FacturasProdAlterPart.objects.prefetch_related('detallefacturaprodalterpart_set').get(pk=idfa)
    producc = [x.produccionalter.id for x in fact.detallefacturaprodalterpart_set.all()]

    producciones = ProdAlter.objects.all().exclude(pk__in=producc).order_by('descripcion')
    noelim = 0
    if fact.confirmada == hashlib.sha1(fact.pk.__str__() + 'YES').hexdigest():
        mensa = "No se puede adicionar producciones a la factura Nro. " + fact.factura_nro + " porque ya está confirmada"
        noelim = 1
    elif fact.confirmada != hashlib.sha1(fact.pk.__str__() + 'NO').hexdigest():
        mensa = "No se puede adcionar producciones a la factura Nro. " + fact.factura_nro + " porque está corrupta"
        noelim = 1
    if noelim == 1:
        l = [mensa]
        rc_fecha = fact.doc_factura.fecha_doc.strftime("%d/%m/%Y")
        nombre = fact.nombre
        ci = fact.ci
        recargo = fact.format_recargo()
        rc_nro = fact.factura_nro
        importecup = fact.get_importe_totalcup()

        precio_CUP = "Precio CUP"

        rc_observaciones = fact.doc_factura.observaciones
        filas = fact.detallefacturaprodalterpart_set.all().order_by('produccionalter.descripcion')


        # Verificar si se puede editar. Se puede editar si todos los cascos relacionados con el estado es Casco
        hay_cup = 1
        return render_to_response('comercial/viewfacturaproduccionespart.html',
                                  {'hay_cup': hay_cup,  'eliminar': 0, 'editar': 1, 'cancelar': 0,
                                   'confirmar': 0,
                                   'precio_CUP': precio_CUP, 'importecup': importecup,
                                   'rc_nro': rc_nro, 'fecha': rc_fecha, 'nombre': nombre,
                                   'ci': ci, 'fecha': rc_fecha, 'recargo': fact.format_recargo(),
                                   'totalpagar':fact.get_importe_total(fact.recargo),
                                   'observaciones': rc_observaciones, 'rc_id': idfa,
                                   'elementos_detalle': filas,
                                   'error2': l}, context_instance=RequestContext(request))

    titulo_form = 'Facturas de Producciones Alternativas Particular'
    nombre_form = 'Facturas de Producciones Alternativas Particular'
    controlador_form = 'Facturas de Producciones Alternativas Particular'
    descripcion_form = 'Seleccionar Producción Alternativa para la factura'

    accion_form = 'detalleFacturaProduccionesPart_add'
    cancelbtn_form = '/comerciax/comercial/factura_produccionespart/view/' + idfa

    if request.method == 'POST':
        form = DetalleFacturaProdAlterForm(request.POST)
        if form.is_valid():
            cantidad = form.cleaned_data['cantidad']
            if Decimal(form.data['cantidad']) < 0.01:
                l=['La cantidad debe ser mayor que 0.00']
                return render_to_response('form/form_add.html',
                                          {'form': form, 'form_name': nombre_form, 'form_description': descripcion_form,
                                           'accion': accion_form, 'titulo': titulo_form, 'controlador': controlador_form,
                                           'cancelbtn': cancelbtn_form, 'error2': l},
                                          context_instance=RequestContext(request))
            producto = form.cleaned_data['producto']
            detalle = DetalleFacturaProdAlterPart.objects.filter(factura=idfa, produccionalter=producto)
            if detalle:
                detalle = DetalleFacturaProdAlterPart.objects.get(factura=idfa, produccionalter=producto)
                detalle.cantidad = detalle.cantidad + cantidad
                detalle.importe_mn = utils.redondeo(detalle.cantidad * detalle.precio_mn,2)
            else:
                detalle = DetalleFacturaProdAlterPart()
                detalle.id_detalle = uuid4()
                detalle.cantidad = cantidad
                detalle.produccionalter = producto
                detalle.precio_mn = producto.precio_mn
                detalle.importe_mn = utils.redondeo(detalle.cantidad * detalle.precio_mn,2)
                detalle.factura = fact
            detalle.save()
        if request.POST.__contains__('submit1'):
            return HttpResponseRedirect('/comerciax/comercial/factura_produccionespart/view/' + idfa)

    form = DetalleFacturaProdAlterForm()
    return render_to_response('form/form_add.html',
                              {'form': form, 'form_name': nombre_form, 'form_description': descripcion_form,
                               'accion': accion_form, 'titulo': titulo_form, 'controlador': controlador_form,
                               'cancelbtn': cancelbtn_form, 'error2': l}, context_instance=RequestContext(request))


@login_required
def detalleFacturaProduccionPart_delete(request, idfa, idproduccion):
    if not request.user.has_perm('comercial.facturasprodalter'):
        return render_to_response("denegado.html", locals(), context_instance=RequestContext(request))

    fact = FacturasProdAlterPart.objects.get(pk=idfa)

    l = []

    DetalleFacturaProdAlterPart.objects.get(produccionalter=idproduccion, factura=idfa).delete()

    data = []
    filas = DetalleFacturaProdAlterPart.objects.select_related().filter(factura=idfa).order_by('produccionalter__descripcion')
    cant_renglones = filas.count()
    total_produccion = str(filas.count())
    elementos_detalle = []
    importetotalcup = fact.get_importetotalcup()
    recargo = fact.format_recargo()
    totalpagar = fact.get_importe_total(recargo)
    for a1 in filas:

        # importetotalcup = a1.factura.get_importetotalcup()

        elementos_detalle += [
            {
             'cant_renglones': cant_renglones,
             'id_doc': a1.factura.doc_factura.id_doc,
             'produccionalter': a1.produccionalter.descripcion,
             'codigo': a1.produccionalter.codigo,
             'importetotalcup': importetotalcup,
             'produccionalter_id': a1.produccionalter.id,
             'precio_cup': a1.format_precio_mn(),
             'um':a1.produccionalter.um.descripcion,
             'importe_cup': a1.format_importe_mn(),
             'cantidad': a1.format_cantidad(),
             'recargo': recargo,
             'totalpagar':totalpagar}]

    return HttpResponse(simplejson.dumps(elementos_detalle), content_type='application/javascript; charset=utf8')

@login_required
@transaction.commit_on_success()
def detalleFacturaProduccionPart_edit(request, idfa, idproduccion):
    if not request.user.has_perm('comercial.factura'):
        return render_to_response("denegado.html", locals(), context_instance=RequestContext(request))

    c = None
    l = []

    nombre_form = 'Editar Producción Alternativa Facturada'
    descripcion_form = 'Editar Producción Alternativa Facturada'
    titulo_form = 'Editar Producción Alternativa Facturada'
    controlador_form = 'Editar Producción Alternativa Facturada'
    accion_form = 'detalleFacturaProduccionPart_edit/' + idfa + '/' + idproduccion
    cancelbtn_form = '/comerciax/comercial/factura_produccionespart/view/' + idfa + '/'

    if request.method == 'POST':
        form = DetalleFacturaProdAlterForm2(request.POST)

        if form.is_valid():
            fact = FacturasProdAlterPart.objects.select_related().get(pk=idfa)

            prodsave = ProdAlter.objects.get(pk=idproduccion)
            detalle = DetalleFacturaProdAlterPart.objects.get(produccionalter=prodsave, factura=fact)

            try:

                detalle.cantidad = form.data['cantidad']
                detalle.precio_mn = prodsave.precio_mn
                detalle.importe_mn = prodsave.precio_mn * Decimal(form.data['cantidad'])
                detalle.save()
                importecup = FacturasProdAlterPart.objects.get(pk=idfa).get_importetotalcup()
                return factura_produccionespart_view(request, idfa)
            except Exception, e:
                exc_info = e.__str__()  # sys.exc_info()[:1]
                c = exc_info.find("DETAIL:")
                if c < 0:
                    l = l + ["Error Fatal."]
                else:
                    c = exc_info[c + 7:]
                    # l=l+[c]
                    l = ['Error al cambiar la medida de salida del casco']
                transaction.rollback()
                form = DetalleFacturaProdAlterForm2(request.POST)
                return render_to_response("form/form_edit.html",
                                          {'tipocliente': '0', 'form': form, 'title': titulo_form,
                                           'form_name': nombre_form, 'form_description': descripcion_form,
                                           'controlador': controlador_form, 'accion': accion_form
                                              , 'cancelbtn': cancelbtn_form, 'error2': l},
                                          context_instance=RequestContext(request))
            else:
                transaction.commit()
    else:
        rp = ProdAlter.objects.select_related().get(pk=idproduccion)
        fact = FacturasProdAlterPart.objects.select_related().get(pk=idfa)
        detalle = DetalleFacturaProdAlterPart.objects.get(produccionalter=rp, factura=fact)
        form = DetalleFacturaProdAlterForm2(initial={'producto': rp, 'cantidad':detalle.cantidad})
        return render_to_response('form/form_edit.html', {'form': form, 'form_name': nombre_form,
                                                          'form_description': descripcion_form, 'accion': accion_form,
                                                          'titulo': titulo_form, 'controlador': controlador_form,
                                                          'cancelbtn': cancelbtn_form},
                                  context_instance=RequestContext(request))
    return factura_produccionespart_view(request, idfa)

@login_required
@transaction.commit_on_success()
def factura_produccionespart_confirmar(request, idfa):
    if not request.user.has_perm('comercial.factura'):
        return render_to_response("denegado.html", locals(), context_instance=RequestContext(request))

    l = []
    fact = FacturasProdAlterPart.objects.get(pk=idfa)
    if fact.get_renglones() > 30:
        l = []
        cancelar = 0
        fact = FacturasProdAlterPart.objects.select_related().get(pk=idfa)
        if fact.cancelada == True:
            cancelar = 1
        confir = fact.get_confirmada()
        confirmar = 2
        if confir == 'N':
            confirmar = 0
        elif confir == 'S':
            confirmar = 1

        eliminar = 1
        editar = 1
        if confirmar == 2 or confirmar == 1:
            eliminar = 0
            editar = 0

        rc_fecha = fact.doc_factura.fecha_doc.strftime("%d/%m/%Y")
        rc_cliente = fact.cliente.nombre
        rc_nro = fact.factura_nro
        importecup = fact.get_importetotalcup()
        importecuc = fact.get_importecuc()
        cant_renglones = fact.get_renglones()
        # pmn = ClienteContrato.objects.select_related().get(cliente=fact.cliente.id, cerrado=False)
        # mncosto = pmn.contrato.preciocostomn
        # cuccosto = pmn.contrato.preciocostocuc

        precio_CUP = "Precio CUP"

        rc_observaciones = fact.doc_factura.observaciones
        filas = DetalleFacturaProdAlterPart.objects.select_related().filter(factura=idfa).order_by(
            'produccionalter__descripcion')


        hay_cup = 1
        l = ["La factura excede los 30 renglones, no se puede confirmar"]
        return render_to_response('comercial/viewfacturaproduccionespart.html',
                                  {'hay_cup': hay_cup, 'eliminar': eliminar, 'editar': editar,
                                   'cancelar': cancelar, 'confirmar': confirmar,
                                   'precio_CUP': precio_CUP, 'importecup': importecup,
                                   'rc_nro': rc_nro, 'fecha': rc_fecha, 'cliente': rc_cliente,
                                   'observaciones': rc_observaciones, 'rc_id': idfa, 'elementos_detalle': filas,
                                   'error2': l, 'cant_renglones': cant_renglones},
                                  context_instance=RequestContext(request))

    else:

        pk_user = User.objects.get(pk=request.user.id)
        nrodoc = 1
        if NumeroDoc.objects.count() != 0:
            nrodoc = NumeroDoc.objects.get().nro_factura_prodalter + 1
        nume = NumeroDoc()
        if NumeroDoc.objects.count() == 0:
            nume.id_numerodoc = uuid4()
        else:
            nume = NumeroDoc.objects.get()
        nume.nro_factura_prodalter = nrodoc
        nume.save()
        Doc.objects.filter(pk=FacturasProdAlterPart.objects.get(pk=idfa).doc_factura).update(operador=pk_user)
        FacturasProdAlterPart.objects.filter(pk=idfa).update(confirmada=hashlib.sha1(idfa.__str__() + 'YES').hexdigest(),
                                                factura_nro=nrodoc, confirmar=True)
        return HttpResponseRedirect('/comerciax/comercial/factura_produccionespart/view/' + idfa)

@login_required
@transaction.commit_on_success()
def factura_produccionespart_cancelar(request, idfa):
    if not request.user.has_perm('comercial.factura'):
        return render_to_response("denegado.html", locals(), context_instance=RequestContext(request))

    l = []
    fact = FacturasProdAlterPart.objects.get(pk=idfa)
    filas = DetalleFacturaProdAlterPart.objects.select_related().filter(factura=idfa).order_by(
        'produccionalter.descripcion')
    pagosfact = 0.0
    if fact.confirmada != hashlib.sha1(fact.pk.__str__() + 'YES').hexdigest() or pagosfact != 0:
        mensa = "No se puede cancelar la factura Nro. " + fact.factura_nro + " porque no está confirmada"
        if pagosfact > 0:
            mensa = "No se puede cancelar la factura Nro. " + fact.factura_nro + " porque se han realizado pagos"
        l = [mensa]
        rc_fecha = fact.doc_factura.fecha_doc.strftime("%d/%m/%Y")
        rc_cliente = fact.cliente.nombre
        rc_nro = fact.factura_nro
        importecup = fact.get_importetotalcup()

        precio_CUP = "Precio CUP"

        rc_observaciones = fact.doc_factura.observaciones


        # Verificar si se puede editar. Se puede editar si todos los cascos relacionados con el estado es Casco
        hay_cup = 1
        return render_to_response('comercial/viewfacturaproduccionespart.html',
                                  {'hay_cup': hay_cup, 'eliminar': 0, 'editar': 1, 'cancelar': 0,
                                   'confirmar': 0,
                                   'precio_CUP': precio_CUP, 'importecup': importecup,
                                   'rc_nro': rc_nro, 'fecha': rc_fecha, 'cliente': rc_cliente,
                                   'observaciones': rc_observaciones, 'rc_id': idfa, 'elementos_detalle': filas,
                                   'error2': l}, context_instance=RequestContext(request))

    try:
        hay_cup = 1

        FacturasProdAlterPart.objects.filter(pk=idfa).update(cancelada=True)
        pk_user = User.objects.get(pk=request.user.id)
        Doc.objects.filter(pk=FacturasProdAlter.objects.get(pk=idfa).doc_factura).update(operador=pk_user)

        return HttpResponseRedirect('/comerciax/comercial/factura_produccionespart/index')
    except Exception, e:
        transaction.rollback()
        l = ['Error al cancelar factura']
        fact = FacturasProdAlterPart.objects.select_related().get(pk=idfa)
        importecup = fact.get_importetotalcup()

        rc_fecha = fact.doc_factura.fecha_doc.strftime("%d/%m/%Y")
        rc_cliente = fact.nombre
        rc_nro = fact.factura_nro
        rc_observaciones = fact.doc_factura.observaciones

        precio_CUP = "Precio CUP"
        return render_to_response('comercial/viewfacturaproduccionespart.html',
                                  {'hay_cup': hay_cup,
                                   'precio_CUP': precio_CUP, 'importecup': importecup,
                                   'rc_nro': rc_nro, 'fecha': rc_fecha, 'cliente': rc_cliente,
                                   'observaciones': rc_observaciones, 'rc_id': idfa,
                                   'elementos_detalle': filas,
                                   'error2': l, 'cantcascos': '4'}, context_instance=RequestContext(request))
    else:
        transaction.commit()