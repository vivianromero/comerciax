#-*- coding: utf-8 -*-
from django.contrib.auth.decorators import login_required
from django.shortcuts import render_to_response
from django.template.context import RequestContext
from django.template import Template, Context
from django import template

from comerciax.casco.forms import *
from comerciax.casco.models import *
from comerciax.admincomerciax.models import *
from comerciax.admincomerciax.forms import *
from comerciax.utils import * 
#import datetime
#from time import  strftime, gmtime, strptime
from uuid import uuid4
from django.http import HttpResponseRedirect, HttpRequest
from django.db import transaction
import json
from django.utils import simplejson
from django.core import serializers
import time,datetime
from datetime import timedelta
from time import  strftime, gmtime

from django.db.models import Count

#############################################################
#                        INVENTARIO DE CIERRE               #
#############################################################

def invcierre(request):
    if not request.user.has_perm('comercial.oferta'):
        return render_to_response("denegado.html",locals(),context_instance = RequestContext(request))
    elementos = query_to_dicts("""
    SELECT
        *
    FROM
        auxinvpreview
    """)
    
    return render_to_response("inventario/invcierre.html",locals(),context_instance = RequestContext(request))


def invfisicoall(request, *error):
    if not request.user.has_perm('casco.invalmcasco'):
        return render_to_response("denegado.html",locals(),context_instance = RequestContext(request))
    l=[]
    if error.__len__() > 0:
        l=error[0]
    error2 = l
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
        
    return render_to_response("report/invfisicomensual.html",locals(),context_instance = RequestContext(request))

def balacvsrecap(request, *error):
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
                registro['fact'] = inout['Factura']
                registro['balance'] = elemento['inicialcasco'] + inout['Casco'] + inout['ER'] + inout['REE'] + inout['DIP'] - inout['Factura'] - inout['Transferencia'] - inout['ECR']
                
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
            registro['fact'] = inout2['Factura']
            registro['balance'] = inout2['Casco'] + inout2['ER'] + inout2['REE'] + inout2['DIP'] - inout2['Factura'] - inout2['Transferencia'] - inout2['ECR']
            
            totales['tcasco'] = totales['tcasco'] + registro['casco']
            totales['ter'] = totales['ter'] + registro['er']
            totales['tree'] = totales['tree'] + registro['ree']
            totales['tdip'] = totales['tdip'] + registro['dip']
            totales['tecr'] = totales['tecr'] + registro['ecr']
            totales['ttranf'] = totales['ttranf'] + registro['tranf']
            totales['tfact'] = totales['tfact'] + registro['fact']
            totales['tbalance'] = totales['tbalance'] + registro['balance']
            
            resultado.append(registro)
                  
    return render_to_response("report/balancecasco_vs_recape.html",locals(),context_instance = RequestContext(request))


def invcierrealmc(request, *error):
    if not request.user.has_perm('casco.invalmcasco'):
        return render_to_response("denegado.html",locals(),context_instance = RequestContext(request))
    l=[]
    if error.__len__() > 0:
        l=error[0]
    error2 = l
    elementos = query_to_dicts("""
    SELECT
        *
    FROM
        almacenc
    """)
    fechacierre = Fechacierre.objects.filter(almacen='c').all()
    ultimo_mes_anyo = fechacierre[0]
    messes = ultimo_mes_anyo.mes + 1 
    if messes == 13:
        mes =  Meses.meses_name[1]
        year =  ultimo_mes_anyo.year + 1 
    else:
        mes =  Meses.meses_name[ultimo_mes_anyo.mes + 1]
        year =  ultimo_mes_anyo.year
        
    elementos1=query_to_dicts("""
        SELECT (select count(casco_casco.estado_actual) 
          FROM casco_casco
          WHERE casco_casco.estado_actual = 'Casco'
          GROUP BY casco_casco.estado_actual) AS canti_c, 
          (select count(casco_casco.estado_actual) 
          FROM casco_casco
          WHERE casco_casco.estado_actual = 'DIP'
          GROUP BY casco_casco.estado_actual )AS canti_dip,
          (select count(casco_casco.estado_actual) 
          FROM casco_casco
          WHERE casco_casco.estado_actual = 'DVP'
          GROUP BY casco_casco.estado_actual )AS canti_dvp,
          (select count(casco_casco.estado_actual='ER') 
          FROM casco_casco
          WHERE casco_casco.estado_actual = 'ER'
          GROUP BY casco_casco.estado_actual )AS canti_er,
          (select count(casco_casco.estado_actual) 
          FROM casco_casco
          WHERE casco_casco.estado_actual = 'EER'
          GROUP BY casco_casco.estado_actual )AS canti_eer
    """)
        
    return render_to_response("inventario/invalmc.html",locals(),context_instance = RequestContext(request))

def invcierrealmp(request, *error):
    if not request.user.has_perm('casco.invalmprod'):
        return render_to_response("denegado.html",locals(),context_instance = RequestContext(request))
    l=[]
    if error.__len__() > 0:
        l=error[0]
    error2 = l
    elementos = query_to_dicts("""
    SELECT
        *
    FROM
        almacenp
    """)
    
    elementos1=query_to_dicts("""
          SELECT (select count(casco_casco.estado_actual) 
                  FROM casco_casco
                  WHERE casco_casco.estado_actual = 'Produccion'
                  GROUP BY casco_casco.estado_actual) AS "canti_p", 
                  (select count(casco_casco.estado_actual) 
                  FROM casco_casco
                  WHERE casco_casco.estado_actual = 'PT'
                  GROUP BY casco_casco.estado_actual )AS canti_pt
    """)
    
    fechacierre = Fechacierre.objects.filter(almacen='p').all()
    ultimo_mes_anyo = fechacierre[0]
    messes = ultimo_mes_anyo.mes + 1 
    if messes == 13:
        mes =  Meses.meses_name[1]
        year =  ultimo_mes_anyo.year + 1 
    else:
        mes =  Meses.meses_name[ultimo_mes_anyo.mes + 1]
        year =  ultimo_mes_anyo.year
    return render_to_response("inventario/invalmp.html",locals(),context_instance = RequestContext(request))

@transaction.commit_on_success
def cerrar_mesalmcasco(request):
    if not request.user.has_perm('comercial.invalmcasco'):
        return render_to_response("denegado.html",locals(),context_instance = RequestContext(request))
    c=None
    l=[]
    Invalmc =  Invalmacencasco.objects.all()
    fechacierre = Fechacierre.objects.filter(almacen='c').all()
    ultimo_mes_anyo = fechacierre[0]
    messes = ultimo_mes_anyo.mes
    years = ultimo_mes_anyo.year
    if messes == 12:
        newmes =  Meses.meses_name[1]
        newmes_ = 1
        newyear =  ultimo_mes_anyo.year + 1 
    else:
        newmes_ = messes+1
        newmes =  Meses.meses_name[ultimo_mes_anyo.mes + 1]
        newyear =  ultimo_mes_anyo.year
        
    elementos = query_to_dicts("""
    SELECT
        *
    FROM
        almacenc
    """)
    ya = False
    try:
        for dato in elementos:
            almacen = Invalmacencasco()
            almacen.id = uuid4()
            almacen.mes = newmes_
            almacen.year = newyear 
            almacen.almacen = dato['almacen']
            almacen.dvp = dato['dvp']
            almacen.dip = dato['dip']
            almacen.er = dato['er']
            almacen.ree = dato['ree']
            almacen.medida = Producto.objects.get(descripcion = dato['medida'])
            almacen.save()  
            '''
            tengo que realizar un bloque transaccion porque salvo en varias tablas.
             1- salvar en la tabla "invalmacencasco"
            '''
            
            '''
              2- actualizar el campo 'procesado' de todos los documentos que contienen esos estados
              DIP, DVP, RecepcionCliente, RecepRechaExt, RechazadoRevision.
              hacerlo una sola vez para eso es la variable 'ya'
            '''
            if not ya:
                ya = True
                RecepcionCliente.objects.filter(procesado=False).update(procesado=True)
                RecepRechaExt.objects.filter(procesado=False).update(procesado=True)
                RechazadoRevision.objects.filter(procesado=False).update(procesado=True)
                Transferencia.objects.filter(procesado=False).update(procesado=True)
                ErrorRecepcion.objects.filter(procesado=False).update(procesado=True)
                EntregaRechazado.objects.filter(procesado=False).update(procesado=True)
                VulcaProduccion.objects.filter(procesado=False).update(procesado=True)
                RecepcionParticular.objects.filter(procesado=False).update(procesado=True)
        
        Fechacierre.objects.filter(almacen='c').update(mes=newmes_,year=newyear)
          
        return render_to_response("index.html",context_instance = RequestContext(request))
    except Exception, e:
        transaction.rollback()
        exc_info = e.__str__() #sys.exc_info()[:1]
        l=l+[exc_info]
        c = exc_info.find("DETAIL:")
        if c < 0:
            l=l+["Error Fatal."]
        else:
            c = exc_info[c + 7:]
            l=l+[c]
        return invcierrealmc(request, l)

@transaction.commit_on_success
def cerrar_mesalmprod(request):
    if not request.user.has_perm('comercial.invalmprod'):
        return render_to_response("denegado.html",locals(),context_instance = RequestContext(request))
    c=None
    l=[]
    fechacierre = Fechacierre.objects.filter(almacen='p').all()

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
    elementos = query_to_dicts("""
    SELECT
        *
    FROM
        almacenp
    """)
    ya = False
    try:
        for dato in elementos:
            #Inventario Almacen Produccion
            if dato['Produccion'] > 0:
                almacen = Invalmacenprod()
                almacen.id = uuid4()
                almacen.mes = newmes_
                almacen.year = newyear
                almacen.produccion = dato['Produccion']
                almacen.medida = Producto.objects.get(descripcion = dato['medida'])
                almacen.save()  
            
            #Inventario Almacen Produccion Terminada
            if dato['ProduccionT'] > 0:
                almacenpt = Invalmacenprodterm()
                almacenpt.id = uuid4()
                almacenpt.mes = newmes_
                almacenpt.year = newyear 
                almacenpt.pt = dato['ProduccionT']
                almacenpt.medida = Producto.objects.get(descripcion = dato['medida'])
                almacenpt.save()
            '''
            tengo que realizar un bloque transaccion porque salvo en varias tablas.
             1- salvar en la tabla "invalmacencasco"
            '''
            
            '''
              2- actualizar el campo 'procesado' de todos los documentos que contienen esos estados
              DIP, DVP, RecepcionCliente, RecepRechaExt, RechazadoRevision.
              hacerlo una sola vez para eso es la variable 'ya'
            '''
            if not ya:
                ya = True
                DIP.objects.filter(procesado=False).update(procesado=True)
                CascoDecomiso.objects.filter(procesado=False).update(procesado=True)
                DVP.objects.filter(procesado=False).update(procesado=True)
                CC.objects.filter(procesado=False).update(procesado=True)
                ProduccionTerminada.objects.filter(procesado=False).update(procesado=True)
                PTExternos.objects.filter(procesado=False).update(procesado=True)
                
        # Actualizar la tabla de Fechacierre
        
        Fechacierre.objects.filter(almacen='p').update(mes=newmes_,year=newyear)
        Fechacierre.objects.filter(almacen='pt').update(mes=newmes_,year=newyear)
            
        return render_to_response("index.html",context_instance = RequestContext(request))
    except Exception, e:
        transaction.rollback()
        exc_info = e.__str__() #sys.exc_info()[:1]
        l=l+[exc_info]
        c = exc_info.find("DETAIL:")
        if c < 0:
            l=l+["Error Fatal."]
        else:
            c = exc_info[c + 7:]
            l=l+[c]
        return invcierrealmp(request, l)            

def reportclientemio(request):
    lista_valores=[]
    results = query_to_dicts("""
    SELECT
        *
    FROM
        auxinvpreview
    """)
    for rel in results:
        lista_valores += [rel]
    return HttpResponse(simplejson.dumps(lista_valores),content_type = 'application/javascript; charset=utf8')

def cerrar_mes_almc(request):
    if not request.user.has_perm('comercial.invalmcasco'):
        return render_to_response("denegado.html",locals(),context_instance = RequestContext(request))
    elementos = query_to_dicts("""
    SELECT
        *
    FROM
        auxinvpreview
    """)
    '''
        - guardar la informacion de la tabla Invcierre
        - actualizar el campo "procesado" de los documentos en dependencia de sus estados
    '''
    for dato in elementos:
        invcierre = Invcierre()
        invcierre.mes = "Enero"
        invcierre.year = "2011"
        invcierre.medida = dato['medida']
        invcierre.almcasco = dato['AlmacenC']
        invcierre.almproduccion = dato['AlmacenP']
        invcierre.almprodterminada = dato['AlmacenPT']
        try:
            invcierre.save()
        except Exception, e:
            a = "as"
    return render_to_response("index.html",context_instance = RequestContext(request))
    

def datoscierrealmc(request):
    lista_valores=[]
    results = query_to_dicts("""
    SELECT
        *
    FROM
        auxinvpreview
    """)
    for rel in results:
        lista_valores += [rel]
    return HttpResponse(simplejson.dumps(lista_valores),content_type = 'application/javascript; charset=utf8')


def add_trazabilidad(idcasco,iddoc,estado,*ofer):
    traza=TrazabilidadCasco.objects.filter(casco=idcasco).order_by('nro')
    for elem in traza:
        nrotraza=elem.nro
    
    traza=TrazabilidadCasco()
    traza.id_trazabilidad=uuid4()
    traza.nro=nrotraza+1
    traza.casco=Casco.objects.get(pk=idcasco)
    traza.doc=Doc.objects.get(pk=iddoc)
    traza.estado=estado
    traza.save()
    return 

'''
Se actualiza la trazabilidad y el estado actual
'''
def actualiza_traza(idcasco,iddoc):
    traza=TrazabilidadCasco.objects.get(casco=idcasco,doc=iddoc)
    nrotraza=traza.nro
    '''for elem in traza:
        nrotraza=elem.nro'''

    traza.delete()
    traza=TrazabilidadCasco.objects.get(casco=idcasco,nro=nrotraza-1)
    estadoactual=traza.estado
    try:
        cascoD=DetalleRC.objects.get(casco=idcasco)
    except Exception, e:
        Casco.objects.filter(id_casco=idcasco).update(estado_actual=estadoactual,fecha=None,id_cliente=None)
        return
    Casco.objects.filter(id_casco=idcasco).update(estado_actual=estadoactual,fecha=traza.doc.fecha_doc,id_cliente=Cliente.objects.get(pk=cascoD.rc.cliente.id))
    return

def eliminar_detalle_sino(idcasco,iddoc):
    '''
    Un elemento del detalle de un documento se puede eliminar si su estado no ha cambiado, o sea, si no hay otro documento en 
    el que este detalle este presente 
    '''
    traza=TrazabilidadCasco.objects.select_related().filter(casco=idcasco).order_by('nro')
    
    if traza.__len__()==0:
        return True
    for elem in traza:
        docum1=elem.doc.id_doc
    if docum1!=iddoc:
        return False
    return True

    
def editar_documento(filas,iddoc):
    ''' 
        Un documento es editable o se puede eliminar  si todos los elementos de su detalle mantienen el 
        estado que generó el documento que se quiere editar o eliminar, o sea, si no han cambiado de estado
    '''
    
    for cascos in filas:
        traza=TrazabilidadCasco.objects.select_related().filter(casco=cascos.casco.id_casco).order_by('nro')
        for elem in traza:
            docum2=elem.doc.id_doc
        if docum2!=iddoc:
            return 2
    return 1

#############################################################
#        RECEPCION DE CASCOS A PARTICULARES                      #
#############################################################
@login_required
def get_rp_list(request):
    #prepare the params
    
    try:
        fecha_desde=Fecha_Ver.objects.get()
    except Exception, e:
        fecha_desde=None
    if fecha_desde == None:
        querySet = RecepcionParticular.objects.select_related().all().order_by('-doc_recepcionparticular__fecha_doc')
    else:
        querySet = RecepcionParticular.objects.select_related().filter(doc_recepcionparticular__fecha_doc__gte=fecha_desde.fecha).order_by('-doc_recepcionparticular__fecha_doc')
        
    #querySet = querySet.filter(doc__fecha_doc__year=2010)
   
    columnIndexNameMap = {0: '-casco_doc.fecha_doc',1: 'recepcionparticular_nro',2:'casco_doc.fecha_doc',3:'nombre',4:'ci',5:'recepcionparticular_tipo'}

    searchableColumns = ['nombre','ci','recepcionparticular_nro','recepcionparticular_tipo','doc_recepcionparticular__fecha_doc']
    
    #path to template used to generate json
    jsonTemplatePath = 'casco/json/json_rp.txt'

    #call to generic function from utils
    return get_datatables_records(request, querySet, columnIndexNameMap, searchableColumns, jsonTemplatePath)
@login_required    
def recepcionparticulares_index(request):
    if not request.user.has_perm('casco.recepcioncliente'):
        return render_to_response("denegado.html",locals(),context_instance = RequestContext(request))
    
    return render_to_response('casco/recepcionparticularesindex.html',locals(),context_instance = RequestContext(request))


@login_required
@transaction.commit_on_success()
def recepcionparticulares_add(request):
    
    if not request.user.has_perm('casco.recepcioncliente'):
        return render_to_response("denegado.html",locals(),context_instance = RequestContext(request))
    
    nombre_form='Recepción de Cascos'
    descripcion_form='Recepción de Cascos a Particulares'
    titulo_form='Recepción de Cascos' 
    controlador_form='Recepción de Cascos'
    accion_form='/comerciax/casco/recepcionparticulares/add'
    cancelbtn_form='/comerciax/casco/recepcionparticulares/index'
    #fecha_cierre1=datetime.date.today().strftime("%d/%m/%Y")
    #fecha_cierre=date(2011,07,20).strftime("%d/%m/%Y")
    fecha_cierre=Fechacierre.objects.get(almacen='c').fechaminima()
    fecha_maxima=Fechacierre.objects.get(almacen='c').fechamaxima()
    
    c=None
    l=[]
            
    if request.method == 'POST':
        form = RecepcionParticularesForm(request.POST)

        #rajuste = form.cleaned_data['ajuste']
        if form.is_valid():
            doc=Doc()
            fechadoc=form.cleaned_data['fecha']
            doc.fecha_doc=fechadoc
            doc.observaciones=form.cleaned_data['observaciones']
            doc.fecha_operacion=datetime.date.today()
            doc.fecha_doc=fechadoc
            
            doc.tipo_doc='16'
         
            pk_user=User.objects.get(pk=request.user.id)
            # esto hay que cambiarlo y poner el operador
            pk_doc=uuid4()
            

            doc.id_doc = pk_doc 
            doc.operador=pk_user
            
            
            rp=RecepcionParticular()
            
            rp_nro=form.cleaned_data['nro']
            
            tipo=form.cleaned_data['recepcion_tipo']
            nombre=form.cleaned_data['nombre']
            ci=form.cleaned_data['ci']
                
            #AQUIIIII cascos=DetalleRC.objects.filter(rc__cliente=obj_cliente,rc__recepcioncliente_tipo='A',casco__estado_actual=Estados.estados["Casco"])
            
            rp.recepcionparticular_nro=rp_nro
            
            rp.recepcionparticular_tipo=tipo
            rp.nombre=nombre
            rp.ci=ci
            rp.doc_recepcionparticular=doc
            
            recep=RecepcionParticular.objects.filter(recepcionparticular_nro=rp_nro)
            if recep.__len__()!=0:
                for a1 in recep:
                    if a1.doc_recepcionparticular.fecha_doc.year == fechadoc.year:
                        l=['Número de documento existente']
                        return render_to_response('form/form_adddetalle.html',  {'tipocliente':'0','form': form, 'form_name':nombre_form,'form_description':descripcion_form,
                                                                                 'accion':accion_form,'titulo':titulo_form,'controlador':controlador_form,
                                                                                 'cancelbtn':cancelbtn_form,'fecha_minima':fecha_cierre,'fecha_maxima':fecha_maxima,'error2':l},context_instance = RequestContext(request))

            try:
                doc.save()
                rp.save() 
 
                return HttpResponseRedirect('/comerciax/casco/recepcionparticulares/view/'+pk_doc.__str__())  
            except Exception, e:
                exc_info = e.__str__() # sys.exc_info()[:1]
                c = exc_info.find("DETAIL:")
                
                if c < 0:
                    l=l+["Error Fatal."]
                else:
                    c = exc_info[c + 7:]
                    l=l+[c] 
                                     
                transaction.rollback()
                form = RecepcionParticularesForm(request.POST)
                cliente="Nombre y Apellidos"
                return render_to_response('form/form_adddetalle.html',  {'tipocliente':'2','form': form, 'form_name':nombre_form,'form_description':descripcion_form,'cliente':cliente,
                                                                         'accion':accion_form,'titulo':titulo_form,'controlador':controlador_form,
                                                                         'cancelbtn':cancelbtn_form,'fecha_minima':fecha_cierre,'fecha_maxima':fecha_maxima,'error2':l},context_instance = RequestContext(request))
            else:
                transaction.commit()
    else:
        form = RecepcionParticularesForm(initial={'fecha':fecha_cierre}) 
    cliente="Nombre y Apellidos"        
    return render_to_response('form/form_adddetalle.html',  {'tipocliente':'2','form': form, 'form_name':nombre_form,'form_description':descripcion_form,'cliente':cliente,
                                                             'accion':accion_form,'titulo':titulo_form,'controlador':controlador_form,
                                                             'cancelbtn':cancelbtn_form,'fecha_minima':fecha_cierre,'fecha_maxima':fecha_maxima,'error2':c},context_instance = RequestContext(request))
@login_required
def recepcionparticulares_view(request,idrp):
    if not request.user.has_perm('casco.recepcioncliente'):
        return render_to_response("denegado.html",locals(),context_instance = RequestContext(request))
    l=[]
    
    rp = RecepcionParticular.objects.select_related().get(pk=idrp)
    rp_fecha=rp.doc_recepcionparticular.fecha_doc.strftime("%d/%m/%Y")
    rp_nombre=rp.nombre
    rp_ci=rp.ci
    rp_nro=rp.recepcionparticular_nro
    tipo=rp.recepcionparticular_tipo

    rp_tipo='Venta'
    if tipo == 'O':
        rp_tipo='Otro'
    elif tipo == 'A':
        rp_tipo='Ajuste'
    elif tipo == 'K':
        rp_tipo='Vulca'
    elif tipo == 'R':
        rp_tipo='Regrabable'
    rp_observaciones=rp.doc_recepcionparticular.observaciones
    filas = DetalleRP.objects.select_related().filter(rp=idrp).order_by('casco__producto__descripcion','casco__casco_nro')

    adiciono=True
    # Verificar si se puede editar. Se puede editar si todos los cascos relacionados con él el estado es Casco
    if rp.procesado==True:
        editar=False
        adiciono=False
    else:
        editar=editar_documento(filas, idrp)
        
#    cantidades=DetalleRP.objects.filter(rp=idrp).values("casco__producto__id").annotate(Count('casco__producto__id')) 
    elementos_detalle=[]
#    cantidad=0
    id1=''
    k=0
    k2=0
    for a1 in filas:
        if k!=0:
            if id1!=a1.casco.producto.id:
                elementos_detalle[k-1]['cantidad']=k2
                k2=0
        elementos_detalle+=[{'casco_id':a1.casco.id_casco,'casco_nro':a1.casco.casco_nro,'producto':a1.casco.producto,'productoid':a1.casco.producto.id}]
        k+=1
        k2+=1
        id1=a1.casco.producto.id 
    if k!=0: 
        elementos_detalle[k-1]['cantidad']=k2
    return render_to_response('casco/viewrecepparticular.html',{'total_casco':k,'rp_nro':rp_nro,'fecha':rp_fecha,'cliente':rp_nombre,'tipo':rp_tipo,'ci':rp_ci,
                                                             'observaciones':rp_observaciones,'rp_id':idrp,'elementos_detalle':elementos_detalle, 
                                                             'edito':editar,'adiciono':adiciono, 'error2':l},context_instance = RequestContext(request))

@login_required
@transaction.commit_on_success()
def recepcionparticulares_edit(request,idrp):
    if not request.user.has_perm('casco.recepcioncliente'):
        return render_to_response("denegado.html",locals(),context_instance = RequestContext(request))
    
    nombre_form='Recepción de Cascos'
    descripcion_form='Recepción de Cascos a Particulares'
    titulo_form='Recepción de Cascos' 
    controlador_form='Recepción de Cascos'
    accion_form='/comerciax/casco/recepcionparticulares/edit/' + idrp +'/'
    cancelbtn_form='/comerciax/casco/recepcionparticulares/view/'+idrp+'/'
    c=None
    l=[]
    fecha_cierre=Fechacierre.objects.get(almacen='c').fechaminima()
    fecha_maxima=Fechacierre.objects.get(almacen='c').fechamaxima() 
    if request.method == 'POST':
        form = RecepcionParticularesForm(request.POST)

        #rajuste = form.cleaned_data['ajuste']
        if form.is_valid():
            rp=RecepcionParticular.objects.get(pk=idrp)
            object_doc=Doc.objects.get(pk=idrp)
            
            object_doc.fecha_doc=form.cleaned_data['fecha']
            fechadoc1=form.cleaned_data['fecha']
            object_doc.observaciones=form.cleaned_data['observaciones']
            object_doc.fecha_operacion=datetime.date.today()
         
            pk_user=User.objects.get(pk=request.user.id)
            # esto hay que cambiarlo y poner el operador
            #pk_doc=uuid4()
            

            object_doc.operador=pk_user
            
            rp.recepcionparticular_nro=form.cleaned_data['nro']
            rc_nro1=form.cleaned_data['nro']
            
            rp.recepcionparticular_tipo=form.cleaned_data['recepcion_tipo']
            rp.nombre=form.cleaned_data['nombre']

            tipo=form.cleaned_data['recepcion_tipo']
            recep=RecepcionParticular.objects.filter(recepcionparticular_nro=rc_nro1)
            if recep.__len__()!=0:
                for a1 in recep:
                    if a1.doc_recepcionparticular.fecha_doc.year == fechadoc1.year and a1.pk!=idrp:
                        l=['Número de documento existente']
                        return render_to_response('form/form_adddetalle.html',  {'tipocliente':'0','form': form, 'form_name':nombre_form,'form_description':descripcion_form,
                                                                                 'accion':accion_form,'titulo':titulo_form,'controlador':controlador_form,
                                                                                 'cancelbtn':cancelbtn_form,'error2':l,'fecha_minima':fecha_cierre,'fecha_maxima':fecha_maxima},context_instance = RequestContext(request))        
            try:
                object_doc.save()
                rp.save() 
 
                return HttpResponseRedirect('/comerciax/casco/recepcionparticulares/view/'+idrp)  

            except Exception, e:
                exc_info = e.__str__() # sys.exc_info()[:1]
                c = exc_info.find("DETAIL:")
                
                if c < 0:
                    l=l+["Error Fatal."]
                else:
                    c = exc_info[c + 7:]
                    l=l+[c]
                    
                transaction.rollback()
                form = RecepcionClienteForm(request.POST)
                return render_to_response('form/form_adddetalle.html',  {'tipocliente':'0','form': form, 'form_name':nombre_form,'form_description':descripcion_form,
                                                                         'accion':accion_form,'titulo':titulo_form,'controlador':controlador_form,
                                                                         'cancelbtn':cancelbtn_form,'error2':l,'fecha_minima':fecha_cierre,'fecha_maxima':fecha_maxima},context_instance = RequestContext(request))
            else:
                transaction.commit()     
    else:
        rp = RecepcionParticular.objects.select_related().get(pk=idrp)
        form = RecepcionParticularesForm(initial={'nro':rp.recepcionparticular_nro,'fecha':rp.doc_recepcionparticular.fecha_doc,
                                             'nombre':rp.nombre,'observaciones':rp.doc_recepcionparticular.observaciones,
                                             'recepcion_tipo':rp.recepcionparticular_tipo,'ci':rp.ci})
    return render_to_response('form/form_edit.html',  {'tipocliente':'2','form': form, 'form_name':nombre_form,'form_description':descripcion_form,
                                                       'accion':accion_form,'titulo':titulo_form,'controlador':controlador_form,
                                                       'cancelbtn':cancelbtn_form,'fecha_minima':fecha_cierre,'fecha_maxima':fecha_maxima},context_instance = RequestContext(request))
    
@login_required
@transaction.commit_on_success()
def recepcionparticular_del(request,idrp):
    if not request.user.has_perm('casco.recepcioncliente'):
        return render_to_response("denegado.html",locals(),context_instance = RequestContext(request))
    
    l=[]
    try:
        
        filas = DetalleRP.objects.filter(rp=idrp)
        det_casco=[]
        for canti in filas:
            det_casco=det_casco+[canti.casco.id_casco]
        
        Doc.objects.select_related().get(pk=idrp).delete()
        for canti in det_casco:
            Casco.objects.get(pk=canti).delete()
        return HttpResponseRedirect('/comerciax/casco/recepcionparticulares/index')
        #return render_to_response("casco/recepcionclienteindex.html",locals(),context_instance = RequestContext(request))
    except Exception :
        transaction.rollback()
        l = ['Error al eliminar el documento']
        rp = RecepcionParticular.objects.select_related().get(pk=idrp)
        rp_fecha=rp.doc_recepcionparticular.fecha_doc.strftime("%d/%m/%Y")
        rp_cliente=rp.nombre
        rp_ci=rp.ci
        rp_nro=rp.recepcionparticular_nro
        tipo=rp.recepcionparticular_tipo
        editar=1
        rp_tipo='Venta'
        if tipo == 'O':
            rp_tipo='Otro'
        elif tipo == 'A':
            rp_tipo='Ajuste'
        elif tipo == 'K':
            rp_tipo='Vulca'
        elif tipo == 'R':
            rp_tipo='Regrabable'
        rp_observaciones=rp.doc_recepcionparticular.observaciones
        filas = DetalleRP.objects.select_related().filter(rp=idrp).order_by('admincomerciax_producto.descripcion','casco_casco.casco_nro')
  
    # Verificar si se puede editar. Se puede editar si todos los cascos relacionados con él el estado es Casco
        return render_to_response('casco/viewrecepparticular.html',{'rp_nro':rp_nro,'fecha':rp_fecha,'cliente':rp_cliente,'tipo':rp_tipo,'ci':rp_ci,\
                                                                 'observaciones':rp_observaciones,'rp_id':idrp,'elementos_detalle':filas, 'edito':editar,'error2':l},context_instance = RequestContext(request))
    else:
        transaction.commit()
#===============================================================================
# DETALLES RECEPCION A PARTICULARES
#===============================================================================
@login_required
@transaction.commit_on_success()
def detalleRP_add(request,idrp):
    if not request.user.has_perm('casco.recepcioncliente'):
        return render_to_response("denegado.html",locals(),context_instance = RequestContext(request))
    
    c=None
    l=[]
    nombre_form='Recepción de Cascos'
    descripcion_form='Recepción de Cascos a Particulares'
    titulo_form='Recepción de Cascos' 
    controlador_form='Recepción de Cascos'
    #accion_form='/comerciax/casco/detalle_rc/add/'+idrc
    accion_form='detalleRP_add'
    cancelbtn_form='/comerciax/casco/recepcionparticulares/view/'+idrp
    if request.method == 'POST':
        form = DetalleRPForm(request.POST) 
        #rajuste = form.cleaned_data['ajuste']
        if form.is_valid():
            
            # Creo Casco
            
            # El ID del casco está formado por 
            #numero del casco.organismo.año
            # si el organismo tiene un consecutivo aparte (tabla ConsOrg) es el codigo del organ.,
            # sino es 000
            #
            
            cantidad=form.cleaned_data['cantidad']
            inicio=form.cleaned_data['nro']
            fin=form.cleaned_data['nro_final']
            if fin-inicio!=cantidad-1:
                l=['No se corresponde la cantidad con el número inicial y final de los cascos']
                return render_to_response('form/form_add.html',  {'form': form, 'form_name':nombre_form,'form_description':descripcion_form,'accion':accion_form ,'titulo':titulo_form,'controlador':controlador_form,'cancelbtn':cancelbtn_form,'error2':l},context_instance = RequestContext(request))
            k=1
            nrocrea=inicio
            while k <= cantidad:
                
                pk_casco=generar_id(idrp,str(nrocrea),2)
            
                #pk_casco=generar_id(idrc,form.cleaned_data['nro'])
                casco=Casco.objects.filter(pk=pk_casco)
                
                if casco.__len__()!=0:
                    l=['El casco nro '+ str(nrocrea) + ' existente']
                    return render_to_response('form/form_add.html',  {'form': form, 'form_name':nombre_form,'form_description':descripcion_form,'accion':accion_form ,'titulo':titulo_form,'controlador':controlador_form,'cancelbtn':cancelbtn_form,'error2':l},context_instance = RequestContext(request))
                #else:
                casco=Casco() 
                       
            
                casco.id_casco=pk_casco
            
                casco.casco_nro=nrocrea 
                casco.producto=Producto.objects.get(pk = form.data['medida'])
                casco.producto_salida=Producto.objects.get(pk = form.data['medida'])
                casco.estado_actual="Casco"
                casco.particular=True
                casco.venta = True if (RecepcionParticular.objects.get(pk=idrp).recepcionparticular_tipo=='V') else False
                

            
            # Detalle RP

                detalle=DetalleRP()
                detalle.id_detallerp=uuid4()
                detalle.rp=RecepcionParticular.objects.get(pk=idrp)
                detalle.casco=casco
            
            # trazabilidad
            
                traza=TrazabilidadCasco()
                traza.id_trazabilidad=uuid4()
                traza.nro=1
                object_doc=Doc.objects.get(pk=idrp)
            
                try:
                    traza.doc=object_doc
                #traza.estado=EstadoCasco.objects.get(descripcion='Casco')
                #estados=estados_casco()
                    traza.estado="Casco"
                    traza.casco=casco
                
                
                    casco.save()
                    detalle.save()
                    traza.save()
                
                    
                except Exception, e:
                    exc_info = e.__str__() # sys.exc_info()[:1]
                    c = exc_info.find("DETAIL:")
                
                    if c < 0:
                        l=l+["Error Fatal."]
                    else:
                        c = exc_info[c + 7:]
                        #l=l+[c]
                        l=l+['El casco nro '+ str(nrocrea) + ' ya existe']
                        transaction.rollback()
                        form = DetalleRCForm(request.POST)
                        return render_to_response('form/form_add.html',  {'form': form, 'form_name':nombre_form,'form_description':descripcion_form,
                                                                  'accion':accion_form ,'titulo':titulo_form,'controlador':controlador_form,
                                                                  'cancelbtn':cancelbtn_form,'error2':l},context_instance = RequestContext(request))
                k=k+1
                nrocrea=nrocrea+1
                
        transaction.commit()
        if request.POST.__contains__('submit1'):
            return HttpResponseRedirect('/comerciax/casco/recepcionparticulares/view/' + idrp)
        else:
            form = DetalleRPForm()        
                    
    else:
        form = DetalleRPForm() 
    return render_to_response('form/form_add.html',  {'form': form, 'form_name':nombre_form,'form_description':descripcion_form,
                                                      'accion':accion_form ,'titulo':titulo_form,'controlador':controlador_form,
                                                      'cancelbtn':cancelbtn_form,'error2':l},context_instance = RequestContext(request))


@login_required
def detalleRP_delete(request,idcasco,idrp):
    if not request.user.has_perm('casco.recepcioncliente'):
        return render_to_response("denegado.html",locals(),context_instance = RequestContext(request))
    
    casco=Casco.objects.select_related().get(pk=idcasco)
    nro=casco.casco_nro
    
    if eliminar_detalle_sino(idcasco,idrp):
        casco.delete()
        filas = DetalleRP.objects.select_related().filter(rp=idrp).order_by('casco__producto__descripcion','casco__casco_nro')
#        cantidades=DetalleRP.objects.filter(rp=idrp).values("casco__producto__id").annotate(Count('casco__producto__id')) 
        total_casco=str(filas.count())
        elementos_detalle=[]
        id1=''
        k=0
        k2=0
        for a1 in filas:
            if k!=0:
                if id1!=a1.casco.producto.id:
                    elementos_detalle[k-1]['cantidad']=k2
                    k2=0
            elementos_detalle+=[{'total_casco':total_casco,'id_doc':a1.rp.doc_recepcionparticular.id_doc,'casco_id':a1.casco.id_casco,'casco_nro':a1.casco.casco_nro,'producto':a1.casco.producto.descripcion,'productoid':a1.casco.producto.id}]
            k+=1
            k2+=1
            id1=a1.casco.producto.id 
        if k!=0: 
            elementos_detalle[k-1]['cantidad']=k2
        return HttpResponse(simplejson.dumps(elementos_detalle),content_type = 'application/javascript; charset=utf8')
    else:
        error2 = "No se puede eliminar el casco " + str(nro) + " ya que su estado ha cambiado"
        return HttpResponse(json.dumps({'error':True, 'message':error2}),mimetype=u'application/json')

@login_required
@transaction.commit_on_success()
def detalleRP_edit(request,idcasco,idrp):
    if not request.user.has_perm('casco.recepcioncliente'):
        return render_to_response("denegado.html",locals(),context_instance = RequestContext(request))
    
    c=None
    l=[]
    
    nombre_form='Recepción de Cascos'
    descripcion_form='Recepción de Cascos a Particulares'
    titulo_form='Recepción de Cascos' 
    controlador_form='Recepción de Cascos'
    accion_form='detalleRP_edit/' + idrp +'/' +idcasco
    cancelbtn_form='/comerciax/casco/recepcionparticulares/view/' + idrp +'/'
    
    
    if request.method == 'POST':
        form = DetalleRPFormEdit(request.POST)
        
        if form.is_valid():
            #form = DetalleRCForm(request.POST)
            casco_medida=form.data['medida']
            nro_new=form.cleaned_data['nro']
            cascosave=Casco.objects.get(pk=idcasco)
            nro_old=cascosave.casco_nro
            id_old=cascosave.id_casco

            try:
                if nro_old!=nro_new:
                    
                    pk_casco=generar_id(idrp,str(nro_new),2)
                                        
                    casco_=Casco.objects.filter(pk=pk_casco)
                
                    if casco_.__len__()!=0:
                        l=['El casco nro '+ str(nro_new) + ' existente']
                        return render_to_response('form/form_edit.html',  {'form': form, 'form_name':nombre_form,'form_description':descripcion_form,'accion':accion_form ,'titulo':titulo_form,'controlador':controlador_form,'cancelbtn':cancelbtn_form,'error2':l},context_instance = RequestContext(request))

                    
                    cascosave.id_casco=pk_casco
                    cascosave.casco_nro=nro_new
                    cascosave.producto=Producto.objects.get(pk = casco_medida)
                    cascosave.producto_salida=Producto.objects.get(pk = casco_medida)
                    cascosave.venta = True if (RecepcionParticular.objects.get(pk=idrp).recepcionparticular_tipo=='V') else False
                    cascosave.save()
                    
                    cascosave=Casco.objects.get(pk=pk_casco)
                    
                    '''
                    Trazabilidad
                    '''
                    
                    TrazabilidadCasco.objects.filter(casco=id_old).update(casco=cascosave) 
                    
                    '''
                    detalles
                    '''
                    
                    DetalleRP.objects.filter(casco=id_old).update(casco=cascosave)
                    DetalleRRE.objects.filter(casco=id_old).update(casco=cascosave)
                    DetalleDIP.objects.filter(casco=id_old).update(casco=cascosave)
                    DetalleDVP.objects.filter(casco=id_old).update(casco=cascosave)
                    DetalleTransferencia.objects.filter(casco=id_old).update(casco=cascosave)
                    DetalleEntregaRechazado.objects.filter(casco=id_old).update(casco=cascosave)
                    DetalleCC.objects.filter(casco=id_old).update(casco=cascosave)
                    DetalleVP.objects.filter(casco=id_old).update(casco=cascosave)
                    DetallePT.objects.filter(casco=id_old).update(casco=cascosave)
                    DetallePTE.objects.filter(casco=id_old).update(casco=cascosave)
                    Detalle_ER.objects.filter(casco=id_old).update(casco=cascosave)
                        
                    '''
                    Eliminar el viejo de Casco
                    ''' 
                    Casco.objects.get(pk=id_old).delete()
                else:
                    cascosave.producto=Producto.objects.get(pk = casco_medida)
                    cascosave.producto_salida=Producto.objects.get(pk = casco_medida)
                    cascosave.save()
                    return recepcionparticulares_view(request, idrp)
            except Exception, e:
                exc_info = e.__str__() # sys.exc_info()[:1]
                c = exc_info.find("DETAIL:")
                if c < 0:
                    l = l + ["Error Fatal, "+exc_info]
                else:
                    c = exc_info[c + 7:]
                    #l=l+[c]
                    l=['No se puede cambiar el nro del casco, el casco ' + str(nro_new) +' ya existe']
                transaction.rollback()
                form = DetalleRPFormEdit(request.POST)
                return render_to_response("form/form_edit.html",{'tipocliente':'2','form':form,'title':titulo_form, 'form_name': nombre_form,'form_description':descripcion_form,'controlador':controlador_form,'accion':accion_form
                                                         , 'cancelbtn':cancelbtn_form,'error2':l},context_instance = RequestContext(request))
            else:
                transaction.commit()
    else:   
        rp =Casco.objects.select_related().get(id_casco=idcasco)
        form = DetalleRPFormEdit(initial={'medida':rp.producto,'nro':rp.casco_nro})
        return render_to_response('form/form_edit.html',  {'tipocliente':'2','form': form, 'form_name':nombre_form,'form_description':descripcion_form,'accion':accion_form,'titulo':titulo_form,'controlador':controlador_form,'cancelbtn':cancelbtn_form},context_instance = RequestContext(request))
    return recepcionparticulares_view(request, idrp)  


#############################################################
#        RECEPCION DE CASCOS A CLIENTE                      #
#############################################################
@login_required
def get_rc_list(request):
    #prepare the params
    try:
        fecha_desde=Fecha_Ver.objects.get()
    except Exception, e:
        fecha_desde=None
    if  fecha_desde == None:       
        querySet = RecepcionCliente.objects.select_related().filter(cliente__externo=False)
    else:
        querySet = RecepcionCliente.objects.select_related().filter(cliente__externo=False, doc_recepcioncliente__fecha_doc__gte=fecha_desde.fecha)
        
    
    #querySet = querySet.filter(doc__fecha_doc__year=2010)
    
    columnIndexNameMap = {0: '-casco_doc.fecha_doc',1: 'recepcioncliente_nro',2:'casco_doc.fecha_doc',3:'admincomerciax_cliente.nombre',4:'recepcioncliente_tipo'}

    searchableColumns = ['recepcioncliente_nro','cliente__nombre','recepcioncliente_tipo','doc_recepcioncliente__fecha_doc']
    #path to template used to generate json
    jsonTemplatePath = 'casco/json/json_rc.txt'

    #call to generic function from utils
    return get_datatables_records(request, querySet, columnIndexNameMap, searchableColumns, jsonTemplatePath)

    
@login_required    
def recepcioncliente_index(request):
    if not request.user.has_perm('casco.recepcioncliente'):
        return render_to_response("denegado.html",locals(),context_instance = RequestContext(request))
    
    return render_to_response('casco/recepcionclienteindex.html',locals(),context_instance = RequestContext(request))
    
@login_required
@transaction.commit_on_success()
def recepcioncliente_add(request):
    
    if not request.user.has_perm('casco.recepcioncliente'):
        return render_to_response("denegado.html",locals(),context_instance = RequestContext(request))
    
    nombre_form='Recepción de Cascos'
    descripcion_form='Recepción de Cascos a Clientes'
    titulo_form='Recepción de Cascos' 
    controlador_form='Recepción de Cascos'
    accion_form='/comerciax/casco/recepcioncliente/add'
    cancelbtn_form='/comerciax/casco/recepcioncliente/index'
    #fecha_cierre1=datetime.date.today().strftime("%d/%m/%Y")
    #fecha_cierre=date(2011,07,20).strftime("%d/%m/%Y")
    fecha_cierre=Fechacierre.objects.get(almacen='c').fechaminima()
    fecha_maxima=Fechacierre.objects.get(almacen='c').fechamaxima()
    
    c=None
    l=[]
            
    if request.method == 'POST':
        form = RecepcionClienteForm(request.POST)

        #rajuste = form.cleaned_data['ajuste']
        if form.is_valid():
            doc=Doc()
            fechadoc=form.cleaned_data['fecha']
            doc.fecha_doc=fechadoc
            doc.observaciones=form.cleaned_data['observaciones']
            doc.fecha_operacion=datetime.date.today()
            doc.fecha_doc=fechadoc
 
            doc.tipo_doc='1'
         
            pk_user=User.objects.get(pk=request.user.id)
            # esto hay que cambiarlo y poner el operador
            pk_doc=uuid4()
            

            doc.id_doc = pk_doc 
            doc.operador=pk_user
            
            
            rc=RecepcionCliente()
            
            rc_nro=form.cleaned_data['nro']
            
            
            obj_cliente = Cliente.objects.get(pk = form.data['cliente']) 
            try:
                tipoc=obj_cliente.get_contrato_tipo()
            except Exception, e:
                tipoc=None
            tipo=form.cleaned_data['recepcioncliente_tipo']
        
            if (tipoc == None) and (tipo=='A'):
                l=['Este cliente no tiene contrato, por lo que no se pueden recibir ajustes']
                return render_to_response('form/form_adddetalle.html',  {'tipocliente':'0','form': form, 'form_name':nombre_form,'form_description':descripcion_form,
                                                                         'accion':accion_form,'titulo':titulo_form,'controlador':controlador_form,
                                                                         'cancelbtn':cancelbtn_form,'fecha_minima':fecha_cierre,'fecha_maxima':fecha_maxima,'error2':l},context_instance = RequestContext(request))

            else:
                if (tipoc == False or tipoc==None) and (tipo=='V'):
                    l=['Este cliente no tiene contrato de cascos para la venta, por lo que no se pueden recibir por el tipo seleccionado']
                    return render_to_response('form/form_adddetalle.html',  {'tipocliente':'0','form': form, 'form_name':nombre_form,'form_description':descripcion_form,
                                                                         'accion':accion_form,'titulo':titulo_form,'controlador':controlador_form,
                                                                         'cancelbtn':cancelbtn_form,'fecha_minima':fecha_cierre,'fecha_maxima':fecha_maxima,'error2':l},context_instance = RequestContext(request))
                else:
                    if (tipoc == True) and (tipo=='O' or tipo=='A'):
                        l=['Este cliente tiene contrato de cascos para la venta, por lo que no se pueden recibir por el tipo seleccionado']
                        return render_to_response('form/form_adddetalle.html',  {'tipocliente':'0','form': form, 'form_name':nombre_form,'form_description':descripcion_form,
                                                                             'accion':accion_form,'titulo':titulo_form,'controlador':controlador_form,
                                                                             'cancelbtn':cancelbtn_form,'fecha_minima':fecha_cierre,'fecha_maxima':fecha_maxima,'error2':l},context_instance = RequestContext(request))

            recep=RecepcionCliente.objects.filter(recepcioncliente_nro=rc_nro)
            if recep.__len__()!=0:
                for a1 in recep:
                    if a1.doc_recepcioncliente.fecha_doc.year == fechadoc.year:
                        l=['Número de documento existente']
                        return render_to_response('form/form_adddetalle.html',  {'tipocliente':'0','form': form, 'form_name':nombre_form,'form_description':descripcion_form,
                                                                                 'accion':accion_form,'titulo':titulo_form,'controlador':controlador_form,
                                                                                 'cancelbtn':cancelbtn_form,'fecha_minima':fecha_cierre,'fecha_maxima':fecha_maxima,'error2':l},context_instance = RequestContext(request))
            rc.recepcioncliente_nro=rc_nro
            
            rc.recepcioncliente_tipo=tipo
            rc.cliente=obj_cliente
            rc.doc_recepcioncliente=doc
            try:
                doc.save()
                rc.save() 
                return HttpResponseRedirect('/comerciax/casco/recepcioncliente/view/'+pk_doc.__str__())  
            except Exception, e:
                exc_info = e.__str__() # sys.exc_info()[:1]
                c = exc_info.find("DETAIL:")
                
                if c < 0:
                    l=l+["Error Fatal."]
                else:
                    c = exc_info[c + 7:]
                    l=l+[c] 
                                     
                transaction.rollback()
                form = RecepcionClienteForm(request.POST)
                cliente="Cliente"
                return render_to_response('form/form_adddetalle.html',  {'tipocliente':'0','form': form, 'form_name':nombre_form,'form_description':descripcion_form,'cliente':cliente,
                                                                         'accion':accion_form,'titulo':titulo_form,'controlador':controlador_form,
                                                                         'cancelbtn':cancelbtn_form,'fecha_minima':fecha_cierre,'fecha_maxima':fecha_maxima,'error2':l},context_instance = RequestContext(request))
            else:
                transaction.commit()
    else:
        form = RecepcionClienteForm(initial={'fecha':fecha_cierre}) 
    cliente="Cliente"        
    return render_to_response('form/form_adddetalle.html',  {'tipocliente':'0','form': form, 'form_name':nombre_form,'form_description':descripcion_form,'cliente':cliente,
                                                             'accion':accion_form,'titulo':titulo_form,'controlador':controlador_form,
                                                             'cancelbtn':cancelbtn_form,'fecha_minima':fecha_cierre,'fecha_maxima':fecha_maxima,'error2':c},context_instance = RequestContext(request))


@login_required
@transaction.commit_on_success()
def recepcioncliente_edit(request,idrc):
    if not request.user.has_perm('casco.recepcioncliente'):
        return render_to_response("denegado.html",locals(),context_instance = RequestContext(request))
    
    nombre_form='Recepción de Cascos'
    descripcion_form='Recepción de Cascos a Clientes'
    titulo_form='Recepción de Cascos' 
    controlador_form='Recepción de Cascos'
    accion_form='/comerciax/casco/recepcioncliente/edit/' + idrc +'/'
    cancelbtn_form='/comerciax/casco/recepcioncliente/view/'+idrc+'/'
    c=None
    l=[]
    fecha_cierre=Fechacierre.objects.get(almacen='c').fechaminima()
    fecha_maxima=Fechacierre.objects.get(almacen='c').fechamaxima() 
    if request.method == 'POST':
        form = RecepcionClienteForm(request.POST)

        #rajuste = form.cleaned_data['ajuste']
        if form.is_valid():
            rc=RecepcionCliente.objects.get(pk=idrc)
            object_doc=Doc.objects.get(pk=idrc)
            
            object_doc.fecha_doc=form.cleaned_data['fecha']
            fechadoc1=form.cleaned_data['fecha']
            object_doc.observaciones=form.cleaned_data['observaciones']
            object_doc.fecha_operacion=datetime.date.today()
         
            pk_user=User.objects.get(pk=request.user.id)
            # esto hay que cambiarlo y poner el operador
            #pk_doc=uuid4()
            

            object_doc.operador=pk_user
            
            rc.recepcioncliente_nro=form.cleaned_data['nro']
            rc_nro1=form.cleaned_data['nro']
            
            rc.recepcioncliente_tipo=form.cleaned_data['recepcioncliente_tipo']
            rc.cliente=Cliente.objects.get(pk = form.data['cliente'])

            obj_cliente = Cliente.objects.get(pk = form.data['cliente']) 
            try:
                tipoc=obj_cliente.get_contrato_tipo()
            except Exception, e:
                tipoc=None
            tipo=form.cleaned_data['recepcioncliente_tipo']
            
            if (tipoc == None) and (tipo=='A'):
                l=['Este cliente no tiene contrato, por lo que no se pueden recibir ajustes']
                return render_to_response('form/form_adddetalle.html',  {'tipocliente':'0','form': form, 'form_name':nombre_form,'form_description':descripcion_form,
                                                                         'accion':accion_form,'titulo':titulo_form,'controlador':controlador_form,
                                                                         'cancelbtn':cancelbtn_form,'error2':l,'fecha_minima':fecha_cierre,'fecha_maxima':fecha_maxima},context_instance = RequestContext(request))
            else:
                if (tipoc == False or tipoc==None) and (tipo=='V'):
                    l=['Este cliente no tiene contrato de cascos para la venta, por lo que no se pueden recibir por el tipo seleccionado']
                    return render_to_response('form/form_adddetalle.html',  {'tipocliente':'0','form': form, 'form_name':nombre_form,'form_description':descripcion_form,
                                                                         'accion':accion_form,'titulo':titulo_form,'controlador':controlador_form,
                                                                         'cancelbtn':cancelbtn_form,'error2':l,'fecha_minima':fecha_cierre,'fecha_maxima':fecha_maxima},context_instance = RequestContext(request))

                
                else: 
                    if (tipoc == True) and (tipo=='O' or tipo=='A'):
                        l=['Este cliente tiene contrato de cascos para la venta, por lo que no se pueden recibir por el tipo seleccionado']
                        return render_to_response('form/form_adddetalle.html',  {'tipocliente':'0','form': form, 'form_name':nombre_form,'form_description':descripcion_form,
                                                                                 'accion':accion_form,'titulo':titulo_form,'controlador':controlador_form,
                                                                                 'cancelbtn':cancelbtn_form,'error2':l,'fecha_minima':fecha_cierre,'fecha_maxima':fecha_maxima},context_instance = RequestContext(request))
            recep=RecepcionCliente.objects.filter(recepcioncliente_nro=rc_nro1)
            if recep.__len__()!=0:
                for a1 in recep:
                    if a1.doc_recepcioncliente.fecha_doc.year == fechadoc1.year and a1.pk!=idrc:
                        l=['Número de documento existente']
                        return render_to_response('form/form_adddetalle.html',  {'tipocliente':'0','form': form, 'form_name':nombre_form,'form_description':descripcion_form,
                                                                                 'accion':accion_form,'titulo':titulo_form,'controlador':controlador_form,
                                                                                 'cancelbtn':cancelbtn_form,'error2':l,'fecha_minima':fecha_cierre,'fecha_maxima':fecha_maxima},context_instance = RequestContext(request))
            #RecepcionCliente.objects.create(doc_recepcioncliente=obj_doc,recepcioncliente_nro=nro,recepcioncliente_ajuste=ajuste,cliente=obj_cliente)
            try:
                object_doc.save()
                rc.save() 
 
                return HttpResponseRedirect('/comerciax/casco/recepcioncliente/view/'+idrc)  

            except Exception, e:
                exc_info = e.__str__() # sys.exc_info()[:1]
                c = exc_info.find("DETAIL:")
                
                if c < 0:
                    l=l+["Error Fatal."]
                else:
                    c = exc_info[c + 7:]
                    l=l+[c]
                    
                transaction.rollback()
                form = RecepcionClienteForm(request.POST)
                return render_to_response('form/form_adddetalle.html',  {'tipocliente':'0','form': form, 'form_name':nombre_form,'form_description':descripcion_form,
                                                                         'accion':accion_form,'titulo':titulo_form,'controlador':controlador_form,
                                                                         'cancelbtn':cancelbtn_form,'error2':l,'fecha_minima':fecha_cierre,'fecha_maxima':fecha_maxima},context_instance = RequestContext(request))
            else:
                transaction.commit()     
    else:
        rc = RecepcionCliente.objects.select_related().get(pk=idrc)
        form = RecepcionClienteForm(initial={'nro':rc.recepcioncliente_nro,'fecha':rc.doc_recepcioncliente.fecha_doc,
                                             'cliente':rc.cliente,'observaciones':rc.doc_recepcioncliente.observaciones,
                                             'recepcioncliente_tipo':rc.recepcioncliente_tipo})
    return render_to_response('form/form_edit.html',  {'tipocliente':'0','form': form, 'form_name':nombre_form,'form_description':descripcion_form,
                                                       'accion':accion_form,'titulo':titulo_form,'controlador':controlador_form,
                                                       'cancelbtn':cancelbtn_form,'fecha_minima':fecha_cierre,'fecha_maxima':fecha_maxima},context_instance = RequestContext(request))

@login_required
def recepcioncliente_view(request,idrc):
    if not request.user.has_perm('casco.recepcioncliente'):
        return render_to_response("denegado.html",locals(),context_instance = RequestContext(request))
    l=[]
    
    rc = RecepcionCliente.objects.select_related().get(pk=idrc)
    rc_fecha=rc.doc_recepcioncliente.fecha_doc.strftime("%d/%m/%Y")
    rc_cliente=rc.cliente.nombre
    rc_nro=rc.recepcioncliente_nro
    tipo=rc.recepcioncliente_tipo

    rc_tipo='Venta'
    if tipo == 'O':
        rc_tipo='Otro'
    elif tipo == 'A':
        rc_tipo='Ajuste'
    elif tipo== 'K':
        rc_tipo='Vulca'
    elif tipo== 'R':
        rc_tipo='Regrabable'
    rc_observaciones=rc.doc_recepcioncliente.observaciones
    filas = DetalleRC.objects.select_related().filter(rc=idrc).order_by('casco__producto__descripcion','casco__casco_nro')

#    Item.objects.values("data").annotate(Count("id"))
    adiciono=True
    # Verificar si se puede editar. Se puede editar si todos los cascos relacionados con él el estado es Casco
    if rc.procesado==True:
        editar=False
        adiciono=False
    else:
        editar=editar_documento(filas, idrc)

#    cantidades=DetalleRC.objects.filter(rc=idrc).values("casco__producto__id").annotate(Count('casco__producto__id')) 
    elementos_detalle=[]
    id1=''
    k=0
    k2=0
    for a1 in filas:
        if k!=0:
            if id1!=a1.casco.producto.id:
                elementos_detalle[k-1]['cantidad'] = k2
                k2=0
                
        elementos_detalle+=[{'casco_id':a1.casco.id_casco,'casco_nro':a1.casco.casco_nro,'producto':a1.casco.producto,'productoid':a1.casco.producto.id}]
        k+=1
        k2+=1
        id1=a1.casco.producto.id  
    if k!=0:
        elementos_detalle[k-1]['cantidad']=k2
    return render_to_response('casco/viewrecepcliente.html',{'total_casco':k,'rc_nro':rc_nro,'fecha':rc_fecha,'cliente':rc_cliente,'tipo':rc_tipo,
                                                             'observaciones':rc_observaciones,'rc_id':idrc,'elementos_detalle':elementos_detalle, 
                                                             'edito':editar,'adiciono':adiciono, 'error2':l},context_instance = RequestContext(request))

@login_required
@transaction.commit_on_success()
def recepcioncliente_del(request,idrc):
    if not request.user.has_perm('casco.recepcioncliente'):
        return render_to_response("denegado.html",locals(),context_instance = RequestContext(request))
    
    l=[]
    try:
        
        filas = DetalleRC.objects.filter(rc=idrc)
        det_casco=[]
        for canti in filas:
            det_casco=det_casco+[canti.casco.id_casco]
        
        Doc.objects.select_related().get(pk=idrc).delete()
        for canti in det_casco:
            Casco.objects.get(pk=canti).delete()
        return HttpResponseRedirect('/comerciax/casco/recepcioncliente/index')
        #return render_to_response("casco/recepcionclienteindex.html",locals(),context_instance = RequestContext(request))
    except Exception :
        transaction.rollback()
        l = ['Error al eliminar el documento']
        rc = RecepcionCliente.objects.select_related().get(pk=idrc)
        rc_fecha=rc.doc_recepcioncliente.fecha_doc.strftime("%d/%m/%Y")
        rc_cliente=rc.cliente.nombre
        rc_nro=rc.recepcioncliente_nro
        tipo=rc.recepcioncliente_tipo
        editar=1
        rc_tipo='Venta'
        if tipo == 'O':
            rc_tipo='Otro'
        elif tipo == 'A':
            rc_tipo='Ajuste'
        elif tipo == 'K':
            rc_tipo='Vulca'
        elif tipo == 'R':
            rc_tipo = 'Regrabable'
        rc_observaciones=rc.doc_recepcioncliente.observaciones
        filas = DetalleRC.objects.select_related().filter(rc=idrc).order_by('admincomerciax_producto.descripcion','casco_casco.casco_nro')
  
    # Verificar si se puede editar. Se puede editar si todos los cascos relacionados con él el estado es Casco
        return render_to_response('casco/viewrecepcliente.html',{'rc_nro':rc_nro,'fecha':rc_fecha,'cliente':rc_cliente,'tipo':rc_tipo,'observaciones':rc_observaciones,'rc_id':idrc,'elementos_detalle':filas, 'edito':editar,'error2':l},context_instance = RequestContext(request))
    else:
        transaction.commit()
        
#############################################################
#        DETALLE RECEPCION CASCOS A CLIENTE
#############################################################

# Generar el id del casco
def generar_id(idrc,nro,clase):
    if clase==1: #cliente
        rc=RecepcionCliente.objects.select_related(depth=2).get(pk=idrc)
        org=ConsOrg.objects.filter(org=rc.cliente.organismo.id)
        cod_org=rc.cliente.organismo.codigo_organismo
        if org.__len__()==0:
            cod_org='000'
        fecha=rc.doc_recepcioncliente.fecha_doc
    else:
        rc=RecepcionParticular.objects.select_related().get(pk=idrc) 
        fecha=rc.doc_recepcionparticular.fecha_doc
        cod_org='xxx'
    ano=fecha.year
    return (nro+'-'+cod_org+'-'+ano.__str__())

@login_required
@transaction.commit_on_success()
def detalleRC_add(request,idrc):
    if not request.user.has_perm('casco.recepcioncliente'):
        return render_to_response("denegado.html",locals(),context_instance = RequestContext(request))
    
    c=None
    l=[]
    nombre_form='Recepción de Cascos'
    descripcion_form='Recepción de Cascos a Clientes'
    titulo_form='Recepción de Cascos' 
    controlador_form='Recepción de Cascos'
    #accion_form='/comerciax/casco/detalle_rc/add/'+idrc
    accion_form='detalleRC_add'
    cancelbtn_form='/comerciax/casco/recepcioncliente/view/'+idrc
    if request.method == 'POST':
        form = DetalleRCForm(request.POST) 
        #rajuste = form.cleaned_data['ajuste']
        if form.is_valid():
            
            # Creo Casco
            
            # El ID del casco está formado por 
            #numero del casco.organismo.año
            # si el organismo tiene un consecutivo aparte (tabla ConsOrg) es el codigo del organ.,
            # sino es 000
            #
            
            cantidad=form.cleaned_data['cantidad']
            inicio=form.cleaned_data['nro']
            fin=form.cleaned_data['nro_final']
            if fin-inicio!=cantidad-1:
                l=['No se corresponde la cantidad con el número inicial y final de los cascos']
                return render_to_response('form/form_add.html',  {'form': form, 'form_name':nombre_form,'form_description':descripcion_form,'accion':accion_form ,'titulo':titulo_form,'controlador':controlador_form,'cancelbtn':cancelbtn_form,'error2':l},context_instance = RequestContext(request))
            k=1
            nrocrea=inicio
            object_doc=Doc.objects.get(pk=idrc)
            while k <= cantidad:
                
                pk_casco=generar_id(idrc,str(nrocrea),1)
            
                #pk_casco=generar_id(idrc,form.cleaned_data['nro'])
                casco=Casco.objects.filter(pk=pk_casco)
                
                if casco.__len__()!=0:
                    l=['El casco nro '+ str(nrocrea) + ' existente']
                    return render_to_response('form/form_add.html',  {'form': form, 'form_name':nombre_form,'form_description':descripcion_form,'accion':accion_form ,'titulo':titulo_form,'controlador':controlador_form,'cancelbtn':cancelbtn_form,'error2':l},context_instance = RequestContext(request))
                #else:
                casco=Casco() 
                casco.id_casco=pk_casco
            
                casco.casco_nro=nrocrea 
                casco.producto=Producto.objects.get(pk = form.data['medida'])
                casco.producto_salida=Producto.objects.get(pk = form.data['medida'])
                casco.estado_actual="Casco"
                casco.venta = True if (RecepcionCliente.objects.get(pk=idrc).recepcioncliente_tipo=='V') else False
                casco.id_cliente=RecepcionCliente.objects.get(pk=idrc).cliente
                casco.fecha=object_doc.fecha_doc
                
            # Detalle RC

                detalle=DetalleRC()
                detalle.id_detallerc=uuid4()
                detalle.rc=RecepcionCliente.objects.get(pk=idrc)
                detalle.casco=casco
            
            # trazabilidad
            
                traza=TrazabilidadCasco()
                traza.id_trazabilidad=uuid4()
                traza.nro=1
            
                try:
                    traza.doc=object_doc
                #traza.estado=EstadoCasco.objects.get(descripcion='Casco')
                #estados=estados_casco()
                    traza.estado="Casco"
                    traza.casco=casco
                
                    casco.save()
                    detalle.save()
                    traza.save()
                except Exception, e:
                    exc_info = e.__str__() # sys.exc_info()[:1]
                    c = exc_info.find("DETAIL:")
                    if c < 0:
                        l=l+["Error Fatal."]
                    else:
                        c = exc_info[c + 7:]
                        #l=l+[c]
                        l=l+['El casco nro '+ str(nrocrea) + ' ya existe']
                        transaction.rollback()
                        form = DetalleRCForm(request.POST)
                        return render_to_response('form/form_add.html',  {'form': form, 'form_name':nombre_form,'form_description':descripcion_form,
                                                                  'accion':accion_form ,'titulo':titulo_form,'controlador':controlador_form,
                                                                  'cancelbtn':cancelbtn_form,'error2':l},context_instance = RequestContext(request))
                k=k+1
                nrocrea=nrocrea+1
        transaction.commit()
        if request.POST.__contains__('submit1'):
            return HttpResponseRedirect('/comerciax/casco/recepcioncliente/view/' + idrc)
        else:
            form = DetalleRCForm()        
    else:
        form = DetalleRCForm() 
    return render_to_response('form/form_add.html',  {'form': form, 'form_name':nombre_form,'form_description':descripcion_form,
                                                      'accion':accion_form ,'titulo':titulo_form,'controlador':controlador_form,
                                                      'cancelbtn':cancelbtn_form,'error2':l},context_instance = RequestContext(request))


@login_required
def detalleRC_delete(request,idcasco,idrc):
    if not request.user.has_perm('casco.recepcioncliente'):
        return render_to_response("denegado.html",locals(),context_instance = RequestContext(request))
    
    casco=Casco.objects.select_related().get(pk=idcasco)
    nro=casco.casco_nro
    
    if eliminar_detalle_sino(idcasco,idrc):
        casco.delete()
        
#        detallerc = DetalleRC.objects.select_related().filter(rc=idrc).order_by('admincomerciax_producto.descripcion','casco_casco.casco_nro')
        
        filas = DetalleRC.objects.select_related().filter(rc=idrc).order_by('casco__producto__descripcion','casco__casco_nro')

#        cantidades=DetalleRC.objects.filter(rc=idrc).values("casco__producto__id").annotate(Count('casco__producto__id')) 
        total_casco=str(filas.count())
        elementos_detalle=[]
        cantidad=0
        id1=''
        k=0
        k2=0
        for a1 in filas:
            if k!=0:
                if id1!=a1.casco.producto.id:
                    elementos_detalle[k-1]['cantidad']=k2
                    k2=0
                    
            elementos_detalle+=[{'total_casco':total_casco,'id_doc':a1.rc.doc_recepcioncliente.id_doc,'casco_id':a1.casco.id_casco,'casco_nro':a1.casco.casco_nro,'producto':a1.casco.producto.descripcion,'productoid':a1.casco.producto.id}]
            k+=1
            k2+=1
            id1=a1.casco.producto.id  
        if k!=0:
            elementos_detalle[k-1]['cantidad']=k2
        return HttpResponse(simplejson.dumps(elementos_detalle),content_type = 'application/javascript; charset=utf8')  
    else:
        error2 = "No se puede eliminar el casco " + str(nro) + " ya que su estado ha cambiado"
        return HttpResponse(json.dumps({'error':True, 'message':error2}),mimetype=u'application/json')

@login_required
@transaction.commit_on_success()
def detalleRC_edit(request,idcasco,idrc):
    if not request.user.has_perm('casco.recepcioncliente'):
        return render_to_response("denegado.html",locals(),context_instance = RequestContext(request))
    
    c=None
    l=[]
    
    nombre_form='Recepción de Cascos'
    descripcion_form='Recepción de Cascos a Clientes'
    titulo_form='Recepción de Cascos' 
    controlador_form='Recepción de Cascos'
    accion_form='detalleRC_edit/' + idrc +'/' +idcasco
    cancelbtn_form='/comerciax/casco/recepcioncliente/view/' + idrc +'/'
    
    
    if request.method == 'POST':
        form = DetalleRCFormEdit(request.POST)
        
        if form.is_valid():
            #form = DetalleRCForm(request.POST)
            casco_medida=form.data['medida']
            nro_new=form.cleaned_data['nro']
            cascosave=Casco.objects.get(pk=idcasco)
            nro_old=cascosave.casco_nro
            id_old=cascosave.id_casco

            try:
                if nro_old!=nro_new:
                    
                    pk_casco=generar_id(idrc,str(nro_new),1)
                    
                    
                    casco_=Casco.objects.filter(pk=pk_casco)
                
                    if casco_.__len__()!=0:
                        l=['El casco nro '+ str(nro_new) + ' existente']
                        return render_to_response('form/form_edit.html',  {'form': form, 'form_name':nombre_form,'form_description':descripcion_form,'accion':accion_form ,'titulo':titulo_form,'controlador':controlador_form,'cancelbtn':cancelbtn_form,'error2':l},context_instance = RequestContext(request))
                    
                    
                    cascosave.id_casco=pk_casco
                    cascosave.casco_nro=nro_new
                    cascosave.producto=Producto.objects.get(pk = casco_medida)
                    cascosave.producto_salida=Producto.objects.get(pk = casco_medida)
                    cascosave.venta = True if (RecepcionCliente.objects.get(pk=idrc).recepcioncliente_tipo=='V') else False
                    cascosave.save()
                    
                    cascosave=Casco.objects.get(pk=pk_casco)
                    
                    '''
                    Trazabilidad
                    '''
                    
                    TrazabilidadCasco.objects.filter(casco=id_old).update(casco=cascosave) 
                    
                    '''
                    detalles
                    '''
                    DetalleRC.objects.filter(casco=id_old).update(casco=cascosave)
                    DetalleRRE.objects.filter(casco=id_old).update(casco=cascosave)
                    DetalleDIP.objects.filter(casco=id_old).update(casco=cascosave)
                    DetalleDVP.objects.filter(casco=id_old).update(casco=cascosave)
                    DetalleTransferencia.objects.filter(casco=id_old).update(casco=cascosave)
                    DetalleEntregaRechazado.objects.filter(casco=id_old).update(casco=cascosave)
                    DetalleCC.objects.filter(casco=id_old).update(casco=cascosave)
                    DetalleVP.objects.filter(casco=id_old).update(casco=cascosave)
                    DetallePT.objects.filter(casco=id_old).update(casco=cascosave)
                    DetallePTE.objects.filter(casco=id_old).update(casco=cascosave)
                    Detalle_ER.objects.filter(casco=id_old).update(casco=cascosave)
                        
                    '''
                    Eliminar el viejo de Casco
                    ''' 
                    Casco.objects.get(pk=id_old).delete()
                else:
                    cascosave.producto=Producto.objects.get(pk = casco_medida)
                    cascosave.producto_salida=Producto.objects.get(pk = casco_medida)
                    cascosave.save()
                    return recepcioncliente_view(request, idrc)
            except Exception, e:
                exc_info = e.__str__() # sys.exc_info()[:1]
                c = exc_info.find("DETAIL:")
                if c < 0:
                    l = l + ["Error Fatal, "+exc_info]
                else:
                    c = exc_info[c + 7:]
                    #l=l+[c]
                    l=['No se puede cambiar el nro del casco, el casco ' + str(nro_new) +' ya existe']
                transaction.rollback()
                form = DetalleRCFormEdit(request.POST)
                return render_to_response("form/form_edit.html",{'tipocliente':'0','form':form,'title':titulo_form, 'form_name': nombre_form,'form_description':descripcion_form,'controlador':controlador_form,'accion':accion_form
                                                         , 'cancelbtn':cancelbtn_form,'error2':l},context_instance = RequestContext(request))
            else:
                transaction.commit()
    else:   
        rc =Casco.objects.select_related().get(id_casco=idcasco)
        form = DetalleRCFormEdit(initial={'medida':rc.producto,'nro':rc.casco_nro})
        return render_to_response('form/form_edit.html',  {'tipocliente':'0','form': form, 'form_name':nombre_form,'form_description':descripcion_form,'accion':accion_form,'titulo':titulo_form,'controlador':controlador_form,'cancelbtn':cancelbtn_form},context_instance = RequestContext(request))
    return recepcioncliente_view(request, idrc)  


  
  
#############################################################
#        RECEPCION DE CASCOS A CLIENTE EXTERNOS             #
#############################################################

@login_required
def get_rcext_list(request):
    #prepare the params
    
    try:
        fecha_desde=Fecha_Ver.objects.get()
    except Exception, e:
        fecha_desde=None
    if  fecha_desde == None:       
        querySet = RecepcionCliente.objects.select_related().filter(cliente__externo=True,cliente__eliminado=False).order_by('-doc_recepcioncliente__fecha_doc')
    else:
        querySet = RecepcionCliente.objects.select_related().filter(cliente__externo=True,cliente__eliminado=False,doc_recepcioncliente__fecha_doc__gte=fecha_desde.fecha).order_by('-doc_recepcioncliente__fecha_doc')
    #querySet = querySet.filter(doc__fecha_doc__year=2010)
 
    columnIndexNameMap = {0: '-casco_doc.fecha_doc',1: 'recepcioncliente_nro',2:'casco_doc.fecha_doc',3:'admincomerciax_cliente.nombre',4:'recepcioncliente_tipo'}

    searchableColumns = ['cliente__nombre','recepcioncliente_nro','recepcioncliente_tipo','doc_recepcioncliente__fecha_doc']
    
    #path to template used to generate json
    jsonTemplatePath = 'casco/json/json_rc.txt'

    #call to generic function from utils
    return get_datatables_records(request, querySet, columnIndexNameMap, searchableColumns, jsonTemplatePath)


@login_required   
def recepcionclienteext_index(request):
    if not request.user.has_perm('casco.recepcioncliente'):
        return render_to_response("denegado.html",locals(),context_instance = RequestContext(request))
    return render_to_response('casco/recepcionclienteextindex.html',locals(),context_instance = RequestContext(request))

@login_required
@transaction.commit_on_success()
def recepcionclienteext_add(request):
    if not request.user.has_perm('casco.recepcioncliente'):
        return render_to_response("denegado.html",locals(),context_instance = RequestContext(request))
    nombre_form='Recepción de Cascos'
    descripcion_form='Recepción de Cascos a Clientes Externos'
    titulo_form='Recepción de Cascos' 
    controlador_form='Recepción de Cascos'
    accion_form='/comerciax/casco/recepcionclienteext/add'
    cancelbtn_form='/comerciax/casco/recepcionclienteext/index'
    fecha_cierre=Fechacierre.objects.get(almacen='c').fechaminima()
    fecha_maxima=Fechacierre.objects.get(almacen='c').fechamaxima()
    c=None
    l=[]
    
    if request.method == 'POST':
        form = RecepcionClienteExtForm(request.POST)

        #rajuste = form.cleaned_data['ajuste']
        if form.is_valid():
            doc=Doc()

            fechadoc=form.cleaned_data['fecha']
            doc.fecha_doc=fechadoc
            doc.observaciones=form.cleaned_data['observaciones']
            doc.fecha_operacion=datetime.date.today()
            doc.fecha_doc=fechadoc
            doc.tipo_doc='3'
         
            pk_user=User.objects.get(pk=request.user.id)
            # esto hay que cambiarlo y poner el operador
            pk_doc=uuid4()
            

            doc.id_doc = pk_doc 
            doc.operador=pk_user
            
            
            rc=RecepcionCliente()
            
            rc_nro=form.cleaned_data['nro']
            
            
            rc.recepcioncliente_nro=rc_nro
            rc.recepcioncliente_tipo='O'
            rc.cliente=Cliente.objects.get(pk = form.data['cliente'])
            rc.doc_recepcioncliente=doc
            
            recep=RecepcionCliente.objects.filter(recepcioncliente_nro=rc_nro)
            if recep.__len__()!=0:
                for a1 in recep:
                    if a1.doc_recepcioncliente.fecha_doc.year == fechadoc.year:
                        l=['Número de documento existente']
                        return render_to_response('form/form_adddetalle.html',  {'tipocliente':'0','form': form, 'form_name':nombre_form,'form_description':descripcion_form,
                                                                                 'accion':accion_form,'titulo':titulo_form,'controlador':controlador_form,
                                                                                 'cancelbtn':cancelbtn_form,'fecha_minima':fecha_cierre,'fecha_maxima':fecha_maxima,'error2':l},context_instance = RequestContext(request))
            try:

                doc.save()
                rc.save() 
                return HttpResponseRedirect('/comerciax/casco/recepcionclienteext/view/'+pk_doc.__str__()) 
            except Exception, e:
                exc_info = e.__str__() # sys.exc_info()[:1]
                c = exc_info.find("DETAIL:")
                
                if c < 0:
                    l=l+["Error Fatal."]
                else:
                    c = exc_info[c + 7:]
                    l=l+[c] 
                                     
                transaction.rollback()
                form = RecepcionClienteExtForm(request.POST)
                return render_to_response('form/form_adddetalle.html',  {'tipocliente':'1','form': form, 'form_name':nombre_form,'form_description':descripcion_form,
                                                                         'accion':accion_form,'titulo':titulo_form,'controlador':controlador_form,
                                                                         'cancelbtn':cancelbtn_form,'fecha_minima':fecha_cierre,'fecha_maxima':fecha_maxima,'error2':l},context_instance = RequestContext(request))
            else:
                transaction.commit()
    else:
        form = RecepcionClienteExtForm(initial={'fecha':fecha_cierre}) 
    return render_to_response('form/form_adddetalle.html',  {'tipocliente':'1','form': form, 'form_name':nombre_form,'form_description':descripcion_form,
                                                             'accion':accion_form,'titulo':titulo_form,'controlador':controlador_form,
                                                             'cancelbtn':cancelbtn_form,'fecha_minima':fecha_cierre,'fecha_maxima':fecha_maxima,'error2':c},context_instance = RequestContext(request))



@login_required
@transaction.commit_on_success()
def recepcionclienteext_edit(request,idrc):
    if not request.user.has_perm('casco.recepcioncliente'):
        return render_to_response("denegado.html",locals(),context_instance = RequestContext(request))
    nombre_form='Recepción de Cascos'
    descripcion_form='Recepción de Cascos a Clientes Externos'
    titulo_form='Recepción de Cascos' 
    controlador_form='Recepción de Cascos'
    accion_form='/comerciax/casco/recepcionclienteext/edit/' + idrc +'/'
    cancelbtn_form='/comerciax/casco/recepcionclienteext/view/' + idrc +'/'
    fecha_cierre=Fechacierre.objects.get(almacen='c').fechaminima()
    fecha_maxima=Fechacierre.objects.get(almacen='c').fechamaxima()
    c=None
    l=[]
    
    if request.method == 'POST':
        form = RecepcionClienteExtForm(request.POST)

        #rajuste = form.cleaned_data['ajuste']
        if form.is_valid():
            rc=RecepcionCliente.objects.get(pk=idrc)
            object_doc=Doc.objects.get(pk=idrc)
            
            object_doc.fecha_doc=form.cleaned_data['fecha']
            fechadoc1=form.cleaned_data['fecha']
            object_doc.observaciones=form.cleaned_data['observaciones']
            object_doc.fecha_operacion=datetime.date.today()
         
            pk_user=User.objects.get(pk=request.user.id)
            # esto hay que cambiarlo y poner el operador
            #pk_doc=uuid4()
            

            object_doc.operador=pk_user
            
            rc.recepcioncliente_nro=form.cleaned_data['nro']
            rc_nro1=form.cleaned_data['nro']
            
            #rc.recepcioncliente_tipo=form.cleaned_data['recepcioncliente_tipo']
            rc.cliente=Cliente.objects.get(pk = form.data['cliente'])
            recep=RecepcionCliente.objects.filter(recepcioncliente_nro=rc_nro1)
            if recep.__len__()!=0:
                for a1 in recep:
                    if a1.doc_recepcioncliente.fecha_doc.year == fechadoc1.year and a1.pk!=idrc:
                        l=['Número de documento existente']
                        return render_to_response('form/form_adddetalle.html',  {'tipocliente':'0','form': form, 'form_name':nombre_form,'form_description':descripcion_form,
                                                                                 'accion':accion_form,'titulo':titulo_form,'controlador':controlador_form,
                                                                                 'cancelbtn':cancelbtn_form,'error2':l,'fecha_minima':fecha_cierre,'fecha_maxima':fecha_maxima},context_instance = RequestContext(request))                                                                                 
            
            #RecepcionCliente.objects.create(doc_recepcioncliente=obj_doc,recepcioncliente_nro=nro,recepcioncliente_ajuste=ajuste,cliente=obj_cliente)
            try:
                object_doc.save()
                rc.save() 
 
                return HttpResponseRedirect('/comerciax/casco/recepcionclienteext/view/'+idrc)  

            except Exception, e:
                exc_info = e.__str__() # sys.exc_info()[:1]
                c = exc_info.find("DETAIL:")
                
                if c < 0:
                    l=l+["Error Fatal."]
                else:
                    c = exc_info[c + 7:]
                    l=l+[c]
                    
                transaction.rollback()
                form = RecepcionClienteExtForm(request.POST)
                return render_to_response('form/form_adddetalle.html',  {'tipocliente':'1','form': form, 'form_name':nombre_form,'form_description':descripcion_form,
                                                                         'accion':accion_form,'titulo':titulo_form,'controlador':controlador_form,
                                                                         'cancelbtn':cancelbtn_form,'fecha_minima':fecha_cierre,'fecha_maxima':fecha_maxima,'error2':l},context_instance = RequestContext(request))
            else:
                transaction.commit()     
    else:
        rc = RecepcionCliente.objects.select_related().get(pk=idrc)
        form = RecepcionClienteExtForm(initial={'nro':rc.recepcioncliente_nro,'fecha':rc.doc_recepcioncliente.fecha_doc,
                                             'cliente':rc.cliente,'observaciones':rc.doc_recepcioncliente.observaciones})
    return render_to_response('form/form_edit.html',  {'tipocliente':'1','form': form, 'form_name':nombre_form,'form_description':descripcion_form,
                                                       'accion':accion_form,'titulo':titulo_form,'controlador':controlador_form,
                                                       'cancelbtn':cancelbtn_form,'fecha_minima':fecha_cierre,'fecha_maxima':fecha_maxima},context_instance = RequestContext(request))

@login_required
def recepcionclienteext_view(request,idrc):
    if not request.user.has_perm('casco.recepcioncliente'):
        return render_to_response("denegado.html",locals(),context_instance = RequestContext(request))
    l=[]
    
    rc = RecepcionCliente.objects.select_related().get(pk=idrc)
    rc_fecha=rc.doc_recepcioncliente.fecha_doc.strftime("%d/%m/%Y")
    rc_cliente=rc.cliente.nombre
    rc_nro=rc.recepcioncliente_nro
    tipo=rc.recepcioncliente_tipo
    rc_tipo='Venta'
    if tipo == 'O':
        rc_tipo='Otro'
    elif tipo == 'A':
        rc_tipo='Ajuste'
    elif tipo == 'K':
        rc_tipo='Vulca'
    elif tipo== 'R':
        rc_tipo='Regrabable'
    rc_observaciones=rc.doc_recepcioncliente.observaciones
    filas = DetalleRC.objects.select_related().filter(rc=idrc).order_by('casco__producto__descripcion','casco__casco_nro')
    adiciono=True
    if rc.procesado==True:
        editar=False
        adiciono=False
    else:
        editar=editar_documento(filas, idrc)
    # Verificar si se puede editar. Se puede editar si todos los cascos relacionados con él el estado es Casco
    
#    cantidades=DetalleRC.objects.filter(rc=idrc).values("casco__producto__id").annotate(Count('casco__producto__id')) 
    elementos_detalle=[]
    id1=''
    k=0
    k2=0
    for a1 in filas:
        if k!=0:
            if id1!=a1.casco.producto.id:
                elementos_detalle[k-1]['cantidad']=k2
                k2=0
        elementos_detalle+=[{'nro_ext':a1.nro_externo,'casco_id':a1.casco.id_casco,'casco_nro':a1.casco.casco_nro,'producto':a1.casco.producto,'productoid':a1.casco.producto.id}]
        k+=1
        k2+=1
        id1=a1.casco.producto.id  
    
    if k!=0:
        elementos_detalle[k-1]['cantidad']=k2
    return render_to_response('casco/viewrecepclienteext.html',{'total_casco':k,'rc_nro':rc_nro,'fecha':rc_fecha,'cliente':rc_cliente,'tipo':rc_tipo,
                                                                'observaciones':rc_observaciones,'rc_id':idrc,'elementos_detalle':elementos_detalle, 
                                                                'edito':editar,'adiciono':adiciono,'error2':l},context_instance = RequestContext(request))

@login_required
@transaction.commit_on_success()
def recepcionclienteext_del(request,idrc):
    if not request.user.has_perm('casco.recepcioncliente'):
        return render_to_response("denegado.html",locals(),context_instance = RequestContext(request))
    
    try:
        
        filas = DetalleRC.objects.filter(rc=idrc)
        det_casco=[]
        for canti in filas:
            det_casco=det_casco+[canti.casco.id_casco]
        
        Doc.objects.select_related().get(pk=idrc).delete()
        for canti in det_casco:
            Casco.objects.get(pk=canti).delete()
            
        return HttpResponseRedirect('/comerciax/casco/recepcionclienteext/index')
        
    except Exception :
        transaction.rollback()
        l = ['Error al eliminar el documento']
        rc = RecepcionCliente.objects.select_related().get(pk=idrc)
        rc_fecha=rc.doc_recepcioncliente.fecha_doc.strftime("%d/%m/%Y")
        rc_cliente=rc.cliente.nombre
        rc_nro=rc.recepcioncliente_nro
        tipo=rc.recepcioncliente_tipo
        editar=1
        rc_tipo='Venta'
        if tipo == 'O':
            rc_tipo='Otro'
        elif tipo == 'A':
            rc_tipo='Ajuste'
        elif tipo == 'K':
            rc_tipo='Vulca'
        elif tipo == 'R':
            rc_tipo = 'Regrabable'
        rc_observaciones=rc.doc_recepcioncliente.observaciones
        filas = DetalleRC.objects.select_related().filter(rc=idrc).order_by('admincomerciax_producto.descripcion','casco_casco.casco_nro')
  
        
        #return recepcioncliente_view(request,idrc)
        return render_to_response('casco/viewrecepclienteext.html',{'rc_nro':rc_nro,'fecha':rc_fecha,'cliente':rc_cliente,'tipo':rc_tipo,'observaciones':rc_observaciones,'rc_id':idrc,'elementos_detalle':filas, 'edito':editar,'error2':l},context_instance = RequestContext(request))
        #return HttpResponseRedirect('/comerciax/casco/recepcioncliente/view/',{'rc_id':idrc,'error2':l})
        
        #return HttpResponseRedirect('/comerciax/casco/recepcioncliente/view/'+idrc,{'error2':l})  
    else:
        transaction.commit()

#############################################################
#        DETALLE RECEPCION CASCOS A CLIENTE EXTERNOS
#############################################################

@login_required
@transaction.commit_on_success()
def detalleRCext_add(request,idrc):
    if not request.user.has_perm('casco.recepcioncliente'):
        return render_to_response("denegado.html",locals(),context_instance = RequestContext(request))
    
    c=None
    l=[]
    nombre_form='Recepción de Cascos'
    descripcion_form='Recepción de Cascos a Clientes Externos'
    titulo_form='Recepción de Cascos' 
    controlador_form='Recepción de Cascos'
    #accion_form='/comerciax/casco/detalle_rc/add/'+idrc
    accion_form='detalleRCext_add'
    cancelbtn_form='/comerciax/casco/recepcionclienteext/view/'+idrc
    if request.method == 'POST':
        form = DetalleRCForm(request.POST) 
        #rajuste = form.cleaned_data['ajuste']
        if form.is_valid():
            
            # Creo Casco
            
            # El ID del casco está formado por 
            #numero del casco.organismo.año
            # si el organismo tiene un consecutivo aparte (tabla ConsOrg) es el codigo del organ.,
            # sino es 000
            #
            
            cantidad=form.cleaned_data['cantidad']
            inicio=form.cleaned_data['nro']
            fin=form.cleaned_data['nro_final']
            if fin-inicio!=cantidad-1:
                l=['No se corresponde la cantidad con el número inicial y final de los cascos']
                return render_to_response('form/form_add.html',  {'form': form, 'form_name':nombre_form,'form_description':descripcion_form,'accion':accion_form ,'titulo':titulo_form,'controlador':controlador_form,'cancelbtn':cancelbtn_form,'error2':l},context_instance = RequestContext(request))
            k=1
            nrocrea=inicio
            object_doc=Doc.objects.get(pk=idrc)
            while k <= cantidad:
                
                pk_casco=generar_id(idrc,str(nrocrea),1)
            
                #pk_casco=generar_id(idrc,form.cleaned_data['nro'])
                casco=Casco.objects.filter(pk=pk_casco)
                
                if casco.__len__()!=0:
                    l=['El casco nro '+ str(nrocrea) + ' existente']
                    return render_to_response('form/form_add.html',  {'form': form, 'form_name':nombre_form,'form_description':descripcion_form,'accion':accion_form ,'titulo':titulo_form,'controlador':controlador_form,'cancelbtn':cancelbtn_form,'error2':l},context_instance = RequestContext(request))
                #else:
                casco=Casco() 
                       
            
                casco.id_casco=pk_casco
            
                casco.casco_nro=nrocrea 
                casco.producto=Producto.objects.get(pk = form.data['medida'])
                casco.producto_salida=Producto.objects.get(pk = form.data['medida'])
                casco.estado_actual="Casco"
                casco.id_cliente=RecepcionCliente.objects.get(pk=idrc).cliente
                casco.fecha=object_doc.fecha_doc

            
            # Detalle RC

                detalle=DetalleRC()
                detalle.id_detallerc=uuid4()
                detalle.rc=RecepcionCliente.objects.get(pk=idrc)
                detalle.casco=casco
            
            # trazabilidad
            
                traza=TrazabilidadCasco()
                traza.id_trazabilidad=uuid4()
                traza.nro=1
                
            
                try:
                    traza.doc=object_doc
                #traza.estado=EstadoCasco.objects.get(descripcion='Casco')
                #estados=estados_casco()
                    traza.estado="Casco"
                    traza.casco=casco
                
                
                    casco.save()
                    detalle.save()
                    traza.save()
                
                    
                except Exception, e:
                    exc_info = e.__str__() # sys.exc_info()[:1]
                    c = exc_info.find("DETAIL:")
                
                    if c < 0:
                        l=l+["Error Fatal."]
                    else:
                        c = exc_info[c + 7:]
                        #l=l+[c]
                        l=l+['El casco nro '+ str(nrocrea) + ' ya existe']
                        transaction.rollback()
                        form = DetalleRCForm(request.POST)
                        return render_to_response('form/form_add.html',  {'form': form, 'form_name':nombre_form,'form_description':descripcion_form,
                                                                  'accion':accion_form ,'titulo':titulo_form,'controlador':controlador_form,
                                                                  'cancelbtn':cancelbtn_form,'error2':l},context_instance = RequestContext(request))
                k=k+1
                nrocrea=nrocrea+1
                
        transaction.commit()
        if request.POST.__contains__('submit1'):
            return HttpResponseRedirect('/comerciax/casco/recepcionclienteext/view/' + idrc)
        else:
            form = DetalleRCForm()        
                    
    else:
        form = DetalleRCForm() 
    return render_to_response('form/form_add.html',  {'form': form, 'form_name':nombre_form,'form_description':descripcion_form,
                                                      'accion':accion_form ,'titulo':titulo_form,'controlador':controlador_form,
                                                      'cancelbtn':cancelbtn_form,'error2':l},context_instance = RequestContext(request))

@login_required
def detalleRCext_delete(request,idcasco,idrc):
    if not request.user.has_perm('casco.recepcioncliente'):
        return render_to_response("denegado.html",locals(),context_instance = RequestContext(request))
    
    casco=Casco.objects.select_related().get(pk=idcasco)
    nro=casco.casco_nro
    if eliminar_detalle_sino(idcasco,idrc):
        casco.delete()
        filas = DetalleRC.objects.select_related().filter(rc=idrc).order_by('casco__producto__descripcion','casco__casco_nro')

#        cantidades=DetalleRC.objects.filter(rc=idrc).values("casco__producto__id").annotate(Count('casco__producto__id')) 
        total_casco=str(filas.count())
        elementos_detalle=[]
        id1=''
        k=0
        k2=0
        for a1 in filas:
            if k!=0:
                if id1!=a1.casco.producto.id:
                    elementos_detalle[k-1]['cantidad']=k2
                    k2=0
            elementos_detalle+=[{'nro_ext':a1.nro_externo,'total_casco':total_casco,
                                 'id_doc':a1.rc.doc_recepcioncliente.id_doc,
                                 'casco_id':a1.casco.id_casco,'casco_nro':a1.casco.casco_nro,
                                 'producto':a1.casco.producto.descripcion,'productoid':a1.casco.producto.id}]
            k+=1
            k2+=1
            id1=a1.casco.producto.id  
        
        if k!=0:
            elementos_detalle[k-1]['cantidad'] = k2
        
        return HttpResponse(simplejson.dumps(elementos_detalle),content_type = 'application/javascript; charset=utf8')  
        #return HttpResponseRedirect("/comerciax/casco/recepcionclienteext/view/" + idrc)
    else:
        error2 = "No se puede eliminar el casco " + str(nro) + " ya que su estado ha cambiado"
        return HttpResponse(json.dumps({'error':True, 'message':error2}),mimetype=u'application/json')
        #return recepcioncliente_view(request, idrc,error2)
 
@login_required
@transaction.commit_on_success()
def detalleRCext_edit(request,idcasco,idrc):
    if not request.user.has_perm('casco.recepcioncliente'):
        return render_to_response("denegado.html",locals(),context_instance = RequestContext(request))
    
    c=None
    l=[]
    
    nombre_form='Recepción de Cascos'
    descripcion_form='Recepción de Cascos a Clientes Externos'
    titulo_form='Recepción de Cascos' 
    controlador_form='Recepción de Cascos'
    accion_form='detalleRCext_edit/' + idrc +'/' +idcasco
    
    cancelbtn_form='/comerciax/casco/recepcionclienteext/view/' + idrc +'/'
    
    
    if request.method == 'POST':
        form = DetalleRCExtForm(request.POST)
        
        if form.is_valid():
            #form = DetalleRCForm(request.POST)
            casco_medida=form.data['medida']
            nro_new=form.cleaned_data['nro']
            cascosave=Casco.objects.get(pk=idcasco)
            nro_old=cascosave.casco_nro
            id_old=cascosave.id_casco

            try:
                if nro_old!=nro_new:
                    pk_casco=generar_id(idrc,str(nro_new),1)
                    
                    casco_=Casco.objects.filter(pk=pk_casco)
                
                    if casco_.__len__()!=0:
                        l=['El casco nro '+ str(nro_new) + ' existente']
                        return render_to_response('form/form_edit.html',  {'form': form, 'form_name':nombre_form,'form_description':descripcion_form,'accion':accion_form ,'titulo':titulo_form,'controlador':controlador_form,'cancelbtn':cancelbtn_form,'error2':l},context_instance = RequestContext(request))

                    
                
                    #if casco.__len__()!=0:
                    #    cascosave.producto=Producto.objects.get(pk = casco_medida)
                    #    cascosave.save()
                    #    l=['No se puede cambiar el nro del casco, el Nro de casco ya existe']
                    #    return render_to_response("form/form_edit.html",{'form':form,'title':titulo_form, 'form_name': nombre_form,'form_description':descripcion_form,'controlador':controlador_form,'accion':accion_form
                    #                                     , 'cancelbtn':cancelbtn_form,'error2':l},context_instance = RequestContext(request))
                    #else:
                        #cascosave=Casco.objects.select_related().filter(pk=idcasco).update(id_casco=pk_casco,casco_nro=nro_new,producto=Producto.objects.get(pk =casco_medida))
                    cascosave.id_casco=pk_casco
                    cascosave.casco_nro=nro_new
                    cascosave.producto=Producto.objects.get(pk = casco_medida)
                    cascosave.producto_salida=Producto.objects.get(pk = casco_medida)
                    cascosave.save()
                    
                    cascosave=Casco.objects.get(pk=pk_casco)
                    
                    '''
                    trazabilidad
                    '''
                    TrazabilidadCasco.objects.filter(casco=id_old).update(casco=cascosave) 
                    
                    '''
                    detalles
                    '''
                    DetalleRC.objects.filter(casco=id_old).update(nro_externo=form.data['nro_externo'])
                    DetalleRC.objects.filter(casco=id_old).update(casco=cascosave)
                    DetalleRRE.objects.filter(casco=id_old).update(casco=cascosave)
                    DetalleDIP.objects.filter(casco=id_old).update(casco=cascosave)
                    DetalleDVP.objects.filter(casco=id_old).update(casco=cascosave)
                    DetalleTransferencia.objects.filter(casco=id_old).update(casco=cascosave)
                    DetalleEntregaRechazado.objects.filter(casco=id_old).update(casco=cascosave)
                    DetalleCC.objects.filter(casco=id_old).update(casco=cascosave)
                    DetalleVP.objects.filter(casco=id_old).update(casco=cascosave)
                    DetallePT.objects.filter(casco=id_old).update(casco=cascosave)
                    DetallePTE.objects.filter(casco=id_old).update(casco=cascosave)
                    Detalle_ER.objects.filter(casco=id_old).update(casco=cascosave)
                        
                    '''
                    Eliminar el viejo de Casco
                    ''' 
                    Casco.objects.get(pk=id_old).delete()
                else:
                    DetalleRC.objects.filter(casco=id_old).update(nro_externo=form.data['nro_externo'])
                    cascosave.producto=Producto.objects.get(pk = casco_medida)
                    cascosave.producto_salida=Producto.objects.get(pk = casco_medida)
                    cascosave.save()
                    return recepcionclienteext_view(request, idrc)
            except Exception, e:
                exc_info = e.__str__() # sys.exc_info()[:1]
                c = exc_info.find("DETAIL:")
                if c < 0:
                    l = l + ["Error Fatal."]
                else:
                    c = exc_info[c + 7:]
                    #l=l+[c]
                    l=l+['No se puede cambiar el nro del casco, el casco ' + str(nro_new) +' ya existe']
                    
                transaction.rollback()
                form = DetalleRCExtForm(request.POST)
                return render_to_response("form/form_edit.html",{'tipocliente':'1','form':form,'title':titulo_form, 'form_name': nombre_form,'form_description':descripcion_form,'controlador':controlador_form,'accion':accion_form
                                                         , 'cancelbtn':cancelbtn_form,'error2':l},context_instance = RequestContext(request))
            else:
                transaction.commit()
    else:   
        rc =Casco.objects.select_related().get(id_casco=idcasco)
        detalle=DetalleRC.objects.get(casco=idcasco,rc=idrc)
        nroext=detalle.nro_externo
        form = DetalleRCExtForm(initial={'medida':rc.producto,'nro':rc.casco_nro,'nro_externo':nroext})
        return render_to_response('form/form_edit.html',  {'tipocliente':'1','form': form, 'form_name':nombre_form,'form_description':descripcion_form,'accion':accion_form,'titulo':titulo_form,'controlador':controlador_form,'cancelbtn':cancelbtn_form},context_instance = RequestContext(request))
    return recepcionclienteext_view(request, idrc)  

#############################################################
#        ENTREGA DE CASCOS A PRODUCCION
#############################################################

@login_required
def get_cc_list(request):
    #prepare the params
    try:
        fecha_desde=Fecha_Ver.objects.get()
    except Exception, e:
        fecha_desde=None
    if  fecha_desde == None:  
        querySet = CC.objects.select_related().all().order_by('-doc_cc__fecha_doc')
    else:
        querySet = CC.objects.select_related().filter(doc_cc__fecha_doc__gte=fecha_desde.fecha).order_by('-doc_cc__fecha_doc')
    #querySet = querySet.filter(doc__fecha_doc__year=2010)
 
    columnIndexNameMap = {0: '-casco_doc.fecha_doc',1: 'cc_nro',2:'casco_doc.fecha_doc'}
    #searchableColumns = ['cliente__nombre','recepcioncliente_nro']
    searchableColumns = ['cc_nro','doc_cc__fecha_doc']
    #path to template used to generate json
    jsonTemplatePath = 'casco/json/json_cc.txt'


    #call to generic function from utils
    return get_datatables_records(request, querySet, columnIndexNameMap, searchableColumns, jsonTemplatePath)

@login_required
def cascocc_index(request):
    if not request.user.has_perm('casco.cc'):
        return render_to_response("denegado.html",locals(),context_instance = RequestContext(request))
    
    return render_to_response('casco/cascoccindex.html',locals(),context_instance = RequestContext(request))

@login_required
@transaction.commit_on_success()
def cascocc_add(request):
    if not request.user.has_perm('casco.cc'):
        return render_to_response("denegado.html",locals(),context_instance = RequestContext(request))
    
    nombre_form='Cascos a Producción'
    descripcion_form='Entrega de Cascos a Producción'
    titulo_form='Cascos a Producción' 
    controlador_form='Cascos a Producción'
    accion_form='/comerciax/casco/cascocc/add'
    cancelbtn_form='/comerciax/casco/cascocc/index'
    fecha_cierre=Fechacierre.objects.get(almacen='c').fechaminima()
    fecha_maxima=Fechacierre.objects.get(almacen='c').fechamaxima()
    c=None
    l=[]
    
    if request.method == 'POST':
        form = CascoCCForm(request.POST)

        #rajuste = form.cleaned_data['ajuste']
        if form.is_valid():
            doc=Doc()

            fechadoc=form.cleaned_data['fecha']
            doc.fecha_doc=fechadoc
            doc.observaciones=form.cleaned_data['observaciones']
            doc.fecha_operacion=datetime.date.today()
            doc.fecha_doc=fechadoc
            doc.tipo_doc='2'
         
            pk_user=User.objects.get(pk=request.user.id)
            # esto hay que cambiarlo y poner el operador
            pk_doc=uuid4()
            

            doc.id_doc = pk_doc 
            doc.operador=pk_user
            
            cp=CC()
            
            cp_nro=form.cleaned_data['nro']
            cp.cc_nro=cp_nro
            
            cp.doc_cc=doc
            recep=CC.objects.filter(cc_nro=cp_nro)
            if recep.__len__()!=0:
                for a1 in recep:
                    if a1.doc_cc.fecha_doc.year == fechadoc.year:
                        l=['Número de documento existente']
                        return render_to_response('form/form_adddetalle.html',  {'tipocliente':'0','form': form, 'form_name':nombre_form,'form_description':descripcion_form,
                                                                                 'accion':accion_form,'titulo':titulo_form,'controlador':controlador_form,
                                                                                 'cancelbtn':cancelbtn_form,'fecha_minima':fecha_cierre,'fecha_maxima':fecha_maxima,'error2':l},context_instance = RequestContext(request))
            try:

                doc.save()
                cp.save() 
                return HttpResponseRedirect('/comerciax/casco/cascocc/view/'+pk_doc.__str__())  
            except Exception, e:
                exc_info = e.__str__() # sys.exc_info()[:1]
                c = exc_info.find("DETAIL:")
                
                if c < 0:
                    l=l+["Error Fatal."]
                else:
                    c = exc_info[c + 7:]
                    l=l+[c] 
                                     
                transaction.rollback()
                form = CascoCCForm(request.POST)
                return render_to_response('form/form_adddetalle.html',  {'tipocliente':'2','form': form, 'form_name':nombre_form,'form_description':descripcion_form,
                                                                         'accion':accion_form,'titulo':titulo_form,'controlador':controlador_form,
                                                                         'cancelbtn':cancelbtn_form,'fecha_minima':fecha_cierre,'fecha_maxima':fecha_maxima,'error2':l},context_instance = RequestContext(request))
            else:
                transaction.commit()
    else:
        form = CascoCCForm(initial={'fecha':fecha_cierre}) 
    return render_to_response('form/form_adddetalle.html',  {'tipocliente':'2','form': form, 'form_name':nombre_form,'form_description':descripcion_form,
                                                             'accion':accion_form,'titulo':titulo_form,'controlador':controlador_form,
                                                             'cancelbtn':cancelbtn_form,'fecha_minima':fecha_cierre,'fecha_maxima':fecha_maxima,'error2':c},context_instance = RequestContext(request))

@login_required
@transaction.commit_on_success()
def cascocc_edit(request,idcp):
    if not request.user.has_perm('casco.cc'):
        return render_to_response("denegado.html",locals(),context_instance = RequestContext(request))
    
    nombre_form='Cascos a Producción'
    descripcion_form='Entrega de Casco a Producción'
    titulo_form='Cascos a Producción' 
    controlador_form='Cascos a Producción'
    accion_form='/comerciax/casco/cascocc/edit/'+idcp+'/'
    cancelbtn_form='/comerciax/casco/cascocc/view/'+idcp+'/'
    fecha_cierre=Fechacierre.objects.get(almacen='c').fechaminima()
    fecha_maxima=Fechacierre.objects.get(almacen='c').fechamaxima()
    c=None
    l=[]
        
    if request.method == 'POST':
        form = CascoCCForm(request.POST)

        #rajuste = form.cleaned_data['ajuste']
        if form.is_valid():
            cp=CC.objects.get(pk=idcp)
            object_doc=Doc.objects.get(pk=idcp)
            
            object_doc.fecha_doc=form.cleaned_data['fecha']
            fechadoc1=form.cleaned_data['fecha']
            object_doc.observaciones=form.cleaned_data['observaciones']
            object_doc.fecha_operacion=datetime.date.today()
         
            pk_user=User.objects.get(pk=request.user.id)
            # esto hay que cambiarlo y poner el operador
            #pk_doc=uuid4()
            

            object_doc.operador=pk_user
            
            cp.cc_nro=form.cleaned_data['nro']
            rc_nro1=form.cleaned_data['nro']
            
            recep=CC.objects.filter(cc_nro=rc_nro1)
            if recep.__len__()!=0:
                for a1 in recep:
                    if a1.doc_cc.fecha_doc.year == fechadoc1.year and a1.pk!=idcp:
                        l=['Número de documento existente']
                        return render_to_response('form/form_adddetalle.html',  {'tipocliente':'0','form': form, 'form_name':nombre_form,'form_description':descripcion_form,
                                                                                 'accion':accion_form,'titulo':titulo_form,'controlador':controlador_form,
                                                                                 'cancelbtn':cancelbtn_form,'error2':l,'fecha_minima':fecha_cierre,'fecha_maxima':fecha_maxima},context_instance = RequestContext(request))        
            #RecepcionCliente.objects.create(doc_recepcioncliente=obj_doc,recepcioncliente_nro=nro,recepcioncliente_ajuste=ajuste,cliente=obj_cliente)
            try:
                object_doc.save()
                cp.save() 
 
                return HttpResponseRedirect('/comerciax/casco/cascocc/view/'+idcp)  

            except Exception, e:
                exc_info = e.__str__() # sys.exc_info()[:1]
                c = exc_info.find("DETAIL:")
                
                if c < 0:
                    l=l+["Error Fatal."]
                else:
                    c = exc_info[c + 7:]
                    l=l+[c]
                    
                transaction.rollback()
                form = CascoCCForm(request.POST)
                return render_to_response('form/form_adddetalle.html',  {'tipocliente':'2','form': form, 'form_name':nombre_form,'form_description':descripcion_form,
                                                                         'accion':accion_form,'titulo':titulo_form,'controlador':controlador_form,
                                                                         'cancelbtn':cancelbtn_form,'fecha_minima':fecha_cierre,'fecha_maxima':fecha_maxima,'error2':l},context_instance = RequestContext(request))
            else:
                transaction.commit()     
    else:
        cp = CC.objects.select_related().get(pk=idcp)
        form = CascoCCForm(initial={'nro':cp.cc_nro,'fecha':cp.doc_cc.fecha_doc,
                                             'observaciones':cp.doc_cc.observaciones})
    return render_to_response('form/form_edit.html',  {'tipocliente':'2','form': form, 'form_name':nombre_form,'form_description':descripcion_form,'accion':accion_form,'titulo':titulo_form,'controlador':controlador_form,'cancelbtn':cancelbtn_form,'fecha_minima':fecha_cierre,'fecha_maxima':fecha_maxima},context_instance = RequestContext(request))

@login_required
def cascocc_view(request,idcp):
    if not request.user.has_perm('casco.cc'):
        return render_to_response("denegado.html",locals(),context_instance = RequestContext(request))
    
    l=[]
    cp = CC.objects.select_related().get(pk=idcp)
    rc_fecha=cp.doc_cc.fecha_doc.strftime("%d/%m/%Y")
    rc_nro=cp.cc_nro
    rc_observaciones=cp.doc_cc.observaciones
    
    filas = DetalleCC.objects.select_related().filter(cc=idcp).order_by('casco__producto__descripcion','casco__casco_nro')
    adiciono=True
    if cp.procesado==True:
        adiciono=False
        editar=False
    else:
        editar=editar_documento(filas, idcp)
        
#    cantidades=DetalleCC.objects.filter(cc=idcp).values("casco__producto__id").annotate(Count('casco__producto__id')) 
    elementos_detalle=[]
    id1=''
    k=0
    k2=0
    for a1 in filas:
        if k!=0:
            if id1!=a1.casco.producto.id:
                elementos_detalle[k-1]['cantidad'] = k2
                k2=0
        elementos_detalle+=[{'cliente':a1.casco.get_cliente,'casco_id':a1.casco.id_casco,
                             'casco_nro':a1.casco.casco_nro,'producto':a1.casco.producto,
                             'productoid':a1.casco.producto.id}]
        k+=1
        k2+=1
        id1=a1.casco.producto.id  
    if k!=0:
        elementos_detalle[k-1]['cantidad'] = k2
    return render_to_response('casco/viewcascocc.html',{'total_casco':k,'rc_nro':rc_nro,'fecha':rc_fecha,'observaciones':rc_observaciones,
                                                              'rc_id':idcp,'elementos_detalle':elementos_detalle, 'edito':editar,
                                                              'adiciono':adiciono,'error2':l},context_instance = RequestContext(request))
    
@login_required
@transaction.commit_on_success()
def cascocc_del(request,idcp):
    if not request.user.has_perm('casco.cc'):
        return render_to_response("denegado.html",locals(),context_instance = RequestContext(request))
    try:
        
        filas = DetalleCC.objects.filter(cc=idcp)
        for canti in filas:
            actualiza_traza(canti.casco.id_casco,idcp)
        
        Doc.objects.select_related().get(pk=idcp).delete()

        
        return HttpResponseRedirect('/comerciax/casco/cascocc/index')
    except Exception :
        transaction.rollback()
        l = ['Error al eliminar el documento']
        cp = CC.objects.select_related().get(pk=idcp)
        rc_fecha=cp.doc_cc.fecha_doc.strftime("%d/%m/%Y")

        rc_nro=cp.cc_nro
        editar=1
        rc_observaciones=cp.doc_cc.observaciones
        filas = DetalleCC.objects.select_related().filter(rc=idcp).order_by('admincomerciax_producto.descripcion','casco_casco.casco_nro')

        return render_to_response('casco/viewcascocc.html',{'rc_nro':rc_nro,'fecha':rc_fecha,'observaciones':rc_observaciones,'rc_id':idcp,'elementos_detalle':filas, 'edito':editar,'error2':l},context_instance = RequestContext(request))

    else:
        transaction.commit()

#############################################################
#        DETALLE CASCO A PRODUCCION
#############################################################

@login_required
@transaction.commit_on_success()
def detalleCC_add(request,idcp):
    if not request.user.has_perm('casco.cc'):
        return render_to_response("denegado.html",locals(),context_instance = RequestContext(request))
    
    titulo_form='Cascos a Producción' 
    controlador_form='Cascos a Producción'
    descripcion_form='Seleccionar cascos para producción'
    
    accion_form='detalleCC_add'
    cancelbtn_form='/comerciax/casco/cascocc/view/'+idcp
    estado="Casco" 
    ocioso="No"
    l=[]
    cc=CC.objects.get(pk=idcp)
    medidas=Producto.objects.all()
    #cascos=Casco.objects.select_related().filter(estado_actual=Estados.estados["Casco"]).order_by('admincomerciax_producto.descripcion','casco_nro')
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
                '''
                detalle=DetalleCC()
                detalle.id_detallecc=uuid4()
                detalle.cc=CC.objects.get(pk=idcp)
                detalle.casco=Casco.objects.get(pk=seleccion[k])
                cascocc=Casco.objects.get(pk=seleccion[k])
                nro=cascocc.casco_nro
                try:
                    detalle.save()
                    
                except Exception, e:
                    exc_info = e.__str__() # sys.exc_info()[:1]
                    c = exc_info.find("DETAIL:")
                    
                    if c < 0:
                        l=l+["Error Fatal."]
                    else:
                        l=['El casco ' + str(nro) +' ya existe en este documento']
                        c = exc_info[c + 7:]
                        transaction.rollback()
                        return render_to_response('casco/form_seleccion.html', {'error2':l,'estado':estado,'title':titulo_form,'controlador':controlador_form,'accion':accion_form,
                                                     'cancelbtn':cancelbtn_form, 'nro':cc.cc_nro,'form_description':descripcion_form,
                                                     'fecha':cc.doc_cc.fecha_doc.strftime("%d/%m/%Y"),'medida':medidas,'observaciones':cc.doc_cc.observaciones,
                                                     'rc_id':idcp},context_instance = RequestContext(request))
                
                Casco.objects.filter(pk=seleccion[k]).update(estado_actual="Produccion",fecha=CC.objects.get(pk=idcp).doc_cc.fecha_doc,ocioso=False)
                add_trazabilidad(seleccion[k], idcp, "Produccion")
                
            k=k+1
        if request.POST.__contains__('submit1'):
            medidas=Producto.objects.all()
                          
              
            #cascos=Casco.objects.select_related().filter(estado_actual=Estados.estados["Casco"]).order_by('admincomerciax_producto.descripcion','casco_nro')
            return render_to_response('casco/form_seleccion.html', {'estado':estado,'title':titulo_form,'controlador':controlador_form,'accion':accion_form,
                                                     'cancelbtn':cancelbtn_form, 'nro':cc.cc_nro,'form_description':descripcion_form,
                                                     'fecha':cc.doc_cc.fecha_doc.strftime("%d/%m/%Y"),'medida':medidas,'observaciones':cc.doc_cc.observaciones,
                                                     'rc_id':idcp,'ocioso':ocioso},context_instance = RequestContext(request))
        else:
            return HttpResponseRedirect('/comerciax/casco/cascocc/view/' + idcp)
    medidas=Producto.objects.all()  
    return render_to_response('casco/form_seleccion.html', {'estado':estado,'title':titulo_form,'controlador':controlador_form,'accion':accion_form,
                                                      'cancelbtn':cancelbtn_form, 'nro':cc.cc_nro,'form_description':descripcion_form,
                                                      'fecha':cc.doc_cc.fecha_doc.strftime("%d/%m/%Y"),'medida':medidas,'observaciones':cc.doc_cc.observaciones,
                                                      'rc_id':idcp,'ocioso':ocioso},context_instance = RequestContext(request))    

@login_required
def detalleDev_list(request,idprod,estado,idcliente):
    filtro=[]
    estados=estado.split("-")
    cantidad=estados.__len__()
    k=0
    while k < cantidad:
        filtro=filtro+[estados[k]]
        k=k+1
    
    cascos=Casco.objects.select_related().filter(ocioso=False,estado_actual__in=filtro,producto__id=idprod).order_by('admincomerciax_producto.descripcion','casco_nro')
    
    lista_valores=[]
    for detalles in cascos:
        if detalles.get_idcliente()==idcliente:
            lista_valores=lista_valores+[{"casco_nro":detalles.casco_nro,"pk":detalles.id_casco,
                                      "medida":detalles.producto.descripcion,"cliente":detalles.get_cliente()}]
    
    return HttpResponse(simplejson.dumps(lista_valores),content_type = 'application/javascript; charset=utf8')

@login_required
def detalleCC_list(request,idprod,estado,ocioso):
    filtro=[]
    estados=estado.split("-")
    cantidad=estados.__len__()
    k=0
    while k < cantidad:
        filtro=filtro+[estados[k]]
        k=k+1
    oci = False
    if ocioso == "Si":
        oci = True
    
    cascos=Casco.objects.select_related().filter(ocioso=oci,estado_actual__in=filtro,producto__id=idprod).order_by('admincomerciax_producto.descripcion','casco_nro')
    
    lista_valores=[]
    for detalles in cascos:
        causa=""
        if detalles.estado_actual in ["DIP","ER","REE"]:
            causa=detalles.get_causa_rechazo()
            
        #causa=detalles.get_causa_rechazo()
        lista_valores=lista_valores+[{"casco_nro":detalles.casco_nro,"pk":detalles.id_casco,
                                      "medida":detalles.producto.descripcion,"cliente":detalles.get_cliente(),"causa":causa}]
    
    return HttpResponse(simplejson.dumps(lista_valores),content_type = 'application/javascript; charset=utf8')

@login_required
def detalleTrans_list(request,idprod,estado,clienteext):
    filtro=[]
    estados=estado.split("-")
    cantidad=estados.__len__()
    k=0
    while k < cantidad:
        filtro=filtro+[estados[k]]
        k=k+1
    
    cascos=Casco.objects.select_related().filter(estado_actual__in=filtro,producto__id=idprod).order_by('admincomerciax_producto.descripcion','casco_nro')
    
    lista_valores=[]
    for detalles in cascos:
        if detalles.get_trans_para()==clienteext:
            lista_valores=lista_valores+[{"casco_nro":detalles.casco_nro,"pk":detalles.id_casco,"medida":detalles.producto.descripcion,"cliente":detalles.get_cliente()}]
    
    return HttpResponse(simplejson.dumps(lista_valores),content_type = 'application/javascript; charset=utf8')

    
@login_required
def detalleCC_delete(request,idcp,idcasco):
    if not request.user.has_perm('casco.cc'):
        return render_to_response("denegado.html",locals(),context_instance = RequestContext(request))
    
    casco=Casco.objects.select_related().get(pk=idcasco)
    nro=casco.casco_nro
    
    if eliminar_detalle_sino(casco.id_casco,idcp):
        DetalleCC.objects.select_related().filter(cc=idcp,casco__id_casco=idcasco).delete()
        actualiza_traza(idcasco,idcp)
        filas = DetalleCC.objects.select_related().filter(cc=idcp).order_by('casco__producto__descripcion','casco__casco_nro')

#        cantidades2=DetalleCC.objects.filter(cc=idcp).values("casco__producto__id").annotate(Count('casco__producto__id')) 
        total_casco=str(filas.count())
            
        elementos_detalle=[]
        id1=''
        k=0
        k2=0
        for a1 in filas:
            if k!=0:
                if id1!=a1.casco.producto.id:
#                    elementos_detalle[k-1]['cantidad'] = elementos_detalle[k-1]['productoid']
                    elementos_detalle[k-1]['cantidad'] = k2
                    k2=0
                    
            elementos_detalle+=[{'total_casco':total_casco,
                                 'id_doc':a1.cc.doc_cc.id_doc,'casco_id':a1.casco.id_casco,
                                 'casco_nro':a1.casco.casco_nro,'producto':a1.casco.producto.descripcion,
                                 'productoid':a1.casco.producto.id,'cliente':a1.casco.get_cliente()}]
            k+=1
            id1=a1.casco.producto.id 
            k2+=1
            
        if k!=0:
            elementos_detalle[k-1]['cantidad'] = k2
        return HttpResponse(simplejson.dumps(elementos_detalle),content_type = 'application/javascript; charset=utf8')
    else:
        error2 = "No se puede eliminar el casco " + str(nro) + " ya que su estado ha cambiado "
        return HttpResponse(json.dumps({'error':True, 'message':error2}),mimetype=u'application/json')


#############################################################
#        ENTREGA DE CASCOS DE PRODUCCION A INSERVIBLE
#############################################################
@login_required
def get_dip_list(request):
    #prepare the params
    try:
        fecha_desde=Fecha_Ver.objects.get()
    except Exception, e:
        fecha_desde=None
    if  fecha_desde == None:  
        querySet = DIP.objects.select_related().all().order_by('-doc_dip__fecha_doc')
    else:
        querySet = DIP.objects.select_related().filter(doc_dip__fecha_doc__gte=fecha_desde.fecha).order_by('-doc_dip__fecha_doc')
    #querySet = querySet.filter(doc__fecha_doc__year=2010)
 
    columnIndexNameMap = {0: '-casco_doc.fecha_doc',1: 'nro_dip',2:'casco_doc.fecha_doc'}
    #searchableColumns = ['cliente__nombre','recepcioncliente_nro']
    searchableColumns = ['nro_dip','doc_dip__fecha_doc']
    #path to template used to generate json
    jsonTemplatePath = 'casco/json/json_dip.txt'


    #call to generic function from utils
    return get_datatables_records(request, querySet, columnIndexNameMap, searchableColumns, jsonTemplatePath)

@login_required
def cascodip_index(request):
    if not request.user.has_perm('casco.dip'):
        return render_to_response("denegado.html",locals(),context_instance = RequestContext(request))
    
    return render_to_response('casco/cascodipindex.html',locals(),context_instance = RequestContext(request))

@login_required
@transaction.commit_on_success()
def cascodip_add(request):
    if not request.user.has_perm('casco.dip'):
        return render_to_response("denegado.html",locals(),context_instance = RequestContext(request))
    
    nombre_form='Cascos Inservibles'
    descripcion_form='Devolución de Cascos a Inservibles'
    titulo_form='Cascos Inservibles' 
    controlador_form='Cascos Inservibles'
    accion_form='/comerciax/casco/cascodip/add'
    cancelbtn_form='/comerciax/casco/cascodip/index'
    fecha_cierre=Fechacierre.objects.get(almacen='p').fechaminima()
    fecha_maxima=Fechacierre.objects.get(almacen='p').fechamaxima()
    c=None
    l=[]
    if request.method == 'POST':
        form = CascoDIPForm(request.POST)

        #rajuste = form.cleaned_data['ajuste']
        if form.is_valid():
            doc=Doc()

            
            fechadoc=form.cleaned_data['fecha']
            doc.fecha_doc=fechadoc
            doc.observaciones=form.cleaned_data['observaciones']
            doc.fecha_operacion=datetime.date.today()
            doc.fecha_doc=fechadoc
            doc.tipo_doc='4'
         
            pk_user=User.objects.get(pk=request.user.id)
            # esto hay que cambiarlo y poner el operador
            pk_doc=uuid4()
            

            doc.id_doc = pk_doc 
            doc.operador=pk_user
            
            
            dip=DIP()
            

            dip.nro_dip=form.cleaned_data['nro']
            nro_dip1=form.cleaned_data['nro']
            dip.doc_dip=doc
            recep=DIP.objects.filter(nro_dip=nro_dip1)
            if recep.__len__()!=0:
                for a1 in recep:
                    if a1.doc_dip.fecha_doc.year == fechadoc.year:
                        l=['Número de documento existente']
                        return render_to_response('form/form_adddetalle.html',  {'tipocliente':'0','form': form, 'form_name':nombre_form,'form_description':descripcion_form,
                                                                                 'accion':accion_form,'titulo':titulo_form,'controlador':controlador_form,
                                                                                 'cancelbtn':cancelbtn_form,'fecha_minima':fecha_cierre,'fecha_maxima':fecha_maxima,'error2':l},context_instance = RequestContext(request))
            try:

                doc.save()
                dip.save() 
 
                return HttpResponseRedirect('/comerciax/casco/cascodip/view/'+pk_doc.__str__())  
            except Exception, e:
                exc_info = e.__str__() # sys.exc_info()[:1]
                c = exc_info.find("DETAIL:")
                
                if c < 0:
                    l=l+["Error Fatal."]
                else:
                    c = exc_info[c + 7:]
                    l=l+[c] 
                                     
                transaction.rollback()
                form = CascoDIPForm(request.POST)
                return render_to_response('form/form_adddetalle.html',  {'tipocliente':'2','form': form, 'form_name':nombre_form,'form_description':descripcion_form,
                                                                         'accion':accion_form,'titulo':titulo_form,'controlador':controlador_form,
                                                                         'cancelbtn':cancelbtn_form,'fecha_minima':fecha_cierre,'fecha_maxima':fecha_maxima,'error2':l},context_instance = RequestContext(request))
            else:
                transaction.commit()
    else:
        form = CascoDIPForm(initial={'fecha':fecha_cierre}) 
#        form = RecepcionParticularesForm(initial={'nro':rp.recepcionparticular_nro,'fecha':rp.doc_recepcionparticular.fecha_doc,
#                                             'nombre':rp.nombre,'observaciones':rp.doc_recepcionparticular.observaciones,
#                                             'recepcion_tipo':rp.recepcionparticular_tipo,'ci':rp.ci})
    return render_to_response('form/form_adddetalle.html',  {'tipocliente':'2','form': form, 'form_name':nombre_form,'form_description':descripcion_form,
                                                             'accion':accion_form,'titulo':titulo_form,'controlador':controlador_form,
                                                             'cancelbtn':cancelbtn_form,'fecha_minima':fecha_cierre,'fecha_maxima':fecha_maxima,'error2':c},context_instance = RequestContext(request))
@login_required
@transaction.commit_on_success()
def cascodip_edit(request,iddip):
    if not request.user.has_perm('casco.dip'):
        return render_to_response("denegado.html",locals(),context_instance = RequestContext(request))
    
    nombre_form='Cascos Inservibles'
    descripcion_form='Devolución de Cascos a Inservibles'
    titulo_form='Cascos Inservibles' 
    controlador_form='Cascos Inservibles'
    accion_form='/comerciax/casco/cascodip/edit/'+iddip+'/'
    cancelbtn_form='/comerciax/casco/cascodip/view/'+iddip+'/'
    fecha_cierre=Fechacierre.objects.get(almacen='p').fechaminima()
    fecha_maxima=Fechacierre.objects.get(almacen='p').fechamaxima()
    c=None
    l=[]
        
    if request.method == 'POST':
        form = CascoDIPForm(request.POST)

        #rajuste = form.cleaned_data['ajuste']
        if form.is_valid():
            dip=DIP.objects.get(pk=iddip)
            object_doc=Doc.objects.get(pk=iddip)
            
            object_doc.fecha_doc=form.cleaned_data['fecha']
            fechadoc1=form.cleaned_data['fecha']
            object_doc.observaciones=form.cleaned_data['observaciones']
            object_doc.fecha_operacion=datetime.date.today()
         
            pk_user=User.objects.get(pk=request.user.id)
            # esto hay que cambiarlo y poner el operador
            #pk_doc=uuid4()
            

            object_doc.operador=pk_user
            
            dip.nro_dip=form.cleaned_data['nro']
            rc_nro1=form.cleaned_data['nro']
            recep=DIP.objects.filter(nro_dip=rc_nro1)
            if recep.__len__()!=0:
                for a1 in recep:
                    if a1.doc_dip.fecha_doc.year == fechadoc1.year and a1.pk!=iddip:
                        l=['Número de documento existente']
                        return render_to_response('form/form_adddetalle.html',  {'tipocliente':'0','form': form, 'form_name':nombre_form,'form_description':descripcion_form,
                                                                                 'accion':accion_form,'titulo':titulo_form,'controlador':controlador_form,
                                                                                 'cancelbtn':cancelbtn_form,'error2':l,'fecha_minima':fecha_cierre,'fecha_maxima':fecha_maxima},context_instance = RequestContext(request))            
         
            #RecepcionCliente.objects.create(doc_recepcioncliente=obj_doc,recepcioncliente_nro=nro,recepcioncliente_ajuste=ajuste,cliente=obj_cliente)
            try:
                object_doc.save()
                dip.save() 
 
                return HttpResponseRedirect('/comerciax/casco/cascodip/view/'+iddip)  

            except Exception, e:
                exc_info = e.__str__() # sys.exc_info()[:1]
                c = exc_info.find("DETAIL:")
                
                if c < 0:
                    l=l+["Error Fatal."]
                else:
                    c = exc_info[c + 7:]
                    l=l+[c]
                    
                transaction.rollback()
                form = CascoDIPForm(request.POST)
                return render_to_response('form/form_adddetalle.html',  {'tipocliente':'2','form': form, 'form_name':nombre_form,'form_description':descripcion_form,
                                                                         'accion':accion_form,'titulo':titulo_form,'controlador':controlador_form,
                                                                         'cancelbtn':cancelbtn_form,'fecha_minima':fecha_cierre,'fecha_maxima':fecha_maxima,'error2':l},context_instance = RequestContext(request))
            else:
                transaction.commit()     
    else:
        dip = DIP.objects.select_related().get(pk=iddip)
        form = CascoDIPForm(initial={'nro':dip.nro_dip,'fecha':dip.doc_dip.fecha_doc,
                                             'observaciones':dip.doc_dip.observaciones})
    return render_to_response('form/form_edit.html',  {'tipocliente':'2','form': form, 'form_name':nombre_form,'form_description':descripcion_form,'accion':accion_form,'titulo':titulo_form,'controlador':controlador_form,'cancelbtn':cancelbtn_form,'fecha_minima':fecha_cierre,'fecha_maxima':fecha_maxima},context_instance = RequestContext(request))


@login_required
def cascodip_view(request,iddip):
    if not request.user.has_perm('casco.dip'):
        return render_to_response("denegado.html",locals(),context_instance = RequestContext(request))
    
    l=[]
    dip = DIP.objects.select_related().get(pk=iddip)
    rc_fecha=dip.doc_dip.fecha_doc.strftime("%d/%m/%Y")
    rc_nro=dip.nro_dip
    
    rc_observaciones=dip.doc_dip.observaciones
    filas = DetalleDIP.objects.select_related().filter(dip=iddip).order_by('casco__producto__descripcion','casco__casco_nro')
    adiciono=True
    if dip.procesado==True:
        editar=False
        adiciono=False
    else:
        editar=editar_documento(filas, iddip)  
    elementos_detalle=[]
    id1=''
    k=0
    k2=0
    for a1 in filas:
        if k!=0:
            if id1!=a1.casco.producto.id:
                elementos_detalle[k-1]['cantidad'] = k2
                k2=0
        elementos_detalle+=[{'cliente':a1.casco.get_cliente,'casco_id':a1.casco.id_casco,
                             'casco_nro':a1.casco.casco_nro,'producto':a1.casco.producto,
                             'productoid':a1.casco.producto.id,'area':a1.area.descripcion,'causa':a1.causa.descripcion}]
        k+=1
        k2+=1
        id1=a1.casco.producto.id  
    if k!=0:
        elementos_detalle[k-1]['cantidad'] = k2
    return render_to_response('casco/viewcascodip.html',{'total_casco':k,'rc_nro':rc_nro,'fecha':rc_fecha,'observaciones':rc_observaciones,
                                                          'muestra_area':True,'rc_id':iddip,'elementos_detalle':elementos_detalle, 'edito':editar,
                                                          'adiciono':adiciono,'error2':l},context_instance = RequestContext(request))
@login_required
@transaction.commit_on_success()
def cascodip_del(request,iddip):
    if not request.user.has_perm('casco.dip'):
        return render_to_response("denegado.html",locals(),context_instance = RequestContext(request))
    
    try:
        filas = DetalleDIP.objects.filter(dip=iddip)
        for canti in filas:
            actualiza_traza(canti.casco.id_casco,iddip)
        
        Doc.objects.select_related().get(pk=iddip).delete()
        return HttpResponseRedirect('/comerciax/casco/cascodip/index')
    except Exception :
        transaction.rollback()
        l = ['Error al eliminar el documento']
        dip = DIP.objects.select_related().get(pk=iddip)
        rc_fecha=dip.doc_dip.fecha_doc.strftime("%d/%m/%Y")

        rc_nro=dip.nro_dip

        editar=1
        rc_observaciones=dip.doc_dip.observaciones
        filas = DetalleDIP.objects.select_related().filter(dip=iddip).order_by('admincomerciax_producto.descripcion','casco_casco.casco_nro')

        return render_to_response('casco/viewcascodip.html',{'rc_nro':rc_nro,'fecha':rc_fecha,'observaciones':rc_observaciones,'rc_id':iddip,'elementos_detalle':filas, 'edito':editar,'error2':l},context_instance = RequestContext(request))

    else:
        transaction.commit()

#############################################################
#        DETALLE CASCO DE PRODUCCION A INSERVIBLE
#############################################################

@login_required
@transaction.commit_on_success()
def detalleDIP_add(request,iddip):
    if not request.user.has_perm('casco.dip'):
        return render_to_response("denegado.html",locals(),context_instance = RequestContext(request))
    
    l=[]
    titulo_form='Devolución de Producción a Inservibles' 
    controlador_form='Devolución a Inservibles'
    descripcion_form='Seleccionar los cascos inservibles'
    accion_form='detalleDIP_add'
    cancelbtn_form='/comerciax/casco/cascodip/view/'+iddip
    estado="Produccion"
    medidas=Producto.objects.all()
    areas=Area.objects.all()
    causas=CausasRechazo.objects.all()
 
    dip=DIP.objects.get(pk=iddip)
    #cascos=Casco.objects.select_related().filter(estado_actual=Estados.estados["Produccion"]).order_by('admincomerciax_producto.descripcion','casco_nro')
    mostrararea=True
    mostrarcausa=True
    if request.method == 'POST':
        seleccion=request.POST.keys()
        k=0
        causa=request.POST["causa"]
        area=request.POST["area"]
        while True:
            if k==seleccion.__len__():
                break
            casco=Casco.objects.filter(pk=seleccion[k])
            
            if casco.count()!=0:
            
                '''
                Los selecionados los cambio de estado, agregar a detalle del documento y actualizar trazabilidad
                '''
                
                
                detalle=DetalleDIP()
                detalle.id_detalledip=uuid4()
                detalle.dip=DIP.objects.get(pk=iddip)
                detalle.casco=Casco.objects.get(pk=seleccion[k])
                detalle.area=Area.objects.get(pk=area)
                detalle.causa=CausasRechazo.objects.get(pk=causa)
                nro=Casco.objects.get(pk=seleccion[k]).casco_nro
                try:
                    detalle.save()
                except Exception, e:
                    exc_info = e.__str__() # sys.exc_info()[:1]
                    c = exc_info.find("DETAIL:")
                    
                    if c < 0:
                        l=l+["Error Fatal."]
                    else:
                        l=['El casco ' + str(nro) +' ya existe en este documento']
                        c = exc_info[c + 7:]
                        transaction.rollback()
                        return render_to_response('casco/form_seleccion.html',{'estado':estado,'title':titulo_form,'controlador':controlador_form,'accion':accion_form,
                                                      'cancelbtn':cancelbtn_form,'medida':medidas, 'nro':dip.nro_dip,'form_description':descripcion_form,
                                                      'fecha':dip.doc_dip.fecha_doc.strftime("%d/%m/%Y"),'observaciones':dip.doc_dip.observaciones,
                                                      'rc_id':iddip,'area':areas,'causas_rechazo':causas,'muestra_area':mostrararea,
                                                      'isreq':'required','muestra_causa':mostrarcausa,'error2':l},context_instance = RequestContext(request))
                        
                        
                Casco.objects.filter(pk=seleccion[k]).update(estado_actual="DIP")
                add_trazabilidad(seleccion[k], iddip, "DIP")
                
            k=k+1
        if request.POST.__contains__('submit1'):
           
            #cascos=Casco.objects.select_related().filter(estado_actual=Estados.estados["Produccion"]).order_by('admincomerciax_producto.descripcion','casco_nro')
            return render_to_response('casco/form_seleccion.html',{'estado':estado,'title':titulo_form,'controlador':controlador_form,'accion':accion_form,
                                                      'cancelbtn':cancelbtn_form,'medida':medidas, 'nro':dip.nro_dip,'form_description':descripcion_form,
                                                      'fecha':dip.doc_dip.fecha_doc.strftime("%d/%m/%Y"),'observaciones':dip.doc_dip.observaciones,
                                                      'rc_id':iddip,'area':areas,'causas_rechazo':causas,'muestra_area':mostrararea,
                                                      'isreq':'required','muestra_causa':mostrarcausa,'error2':l},context_instance = RequestContext(request))
        else:
            return HttpResponseRedirect('/comerciax/casco/cascodip/view/' + iddip)
    areas=Area.objects.all()
    causas=CausasRechazo.objects.all()
    return render_to_response('casco/form_seleccion.html', {'estado':estado,'title':titulo_form,'controlador':controlador_form,'accion':accion_form,
                                                      'cancelbtn':cancelbtn_form,'medida':medidas, 'nro':dip.nro_dip, 'form_description':descripcion_form,
                                                      'fecha':dip.doc_dip.fecha_doc.strftime("%d/%m/%Y"),'observaciones':dip.doc_dip.observaciones,
                                                      'rc_id':iddip,'area':areas,'causas_rechazo':causas,'muestra_area':mostrararea,
                                                      'isreq':'required','muestra_causa':mostrarcausa,'error2':l},context_instance = RequestContext(request))
    
@login_required
def detalleDIP_delete(request,iddip,idcasco):
    if not request.user.has_perm('casco.dip'):
        return render_to_response("denegado.html",locals(),context_instance = RequestContext(request))
        
    casco=Casco.objects.select_related().get(pk=idcasco)
    nro=casco.casco_nro
    
    if eliminar_detalle_sino(casco.id_casco,iddip):
        DetalleDIP.objects.get(casco=idcasco).delete()
        
        actualiza_traza(idcasco,iddip)
        filas = DetalleDIP.objects.select_related().filter(dip=iddip).order_by('casco__producto__descripcion','casco__casco_nro')
        total_casco=str(filas.count())
            
        elementos_detalle=[]
        id1=''
        k=0
        k2=0
        for a1 in filas:
            if k!=0:
                if id1!=a1.casco.producto.id:
#                    elementos_detalle[k-1]['cantidad'] = elementos_detalle[k-1]['productoid']
                    elementos_detalle[k-1]['cantidad'] = k2
                    k2=0
                    
            elementos_detalle+=[{'total_casco':total_casco,
                                 'id_doc':a1.dip.doc_dip.id_doc,'casco_id':a1.casco.id_casco,
                                 'casco_nro':a1.casco.casco_nro,'producto':a1.casco.producto.descripcion,
                                 'productoid':a1.casco.producto.id,'cliente':a1.casco.get_cliente(),
                                 'causa':a1.causa.descripcion,'area':a1.area.descripcion}]
            k+=1
            id1=a1.casco.producto.id 
            k2+=1
            
        if k!=0:
            elementos_detalle[k-1]['cantidad'] = k2
        return HttpResponse(simplejson.dumps(elementos_detalle),content_type = 'application/javascript; charset=utf8')
    else:
        error2 = "No se puede eliminar el casco " + str(nro) + " ya que su estado ha cambiado "
        return HttpResponse(json.dumps({'error':True, 'message':error2}),mimetype=u'application/json')
        #return cascodip_view(request, iddip,error2)
    
@login_required
def detalleDIP_edit(request,idcasco,iddip):
    if not request.user.has_perm('casco.dip'):
        return render_to_response("denegado.html",locals(),context_instance = RequestContext(request))
    
    c=None
    l=[]
    
    nombre_form='nombre'
    descripcion_form='Devolución de Casco a inservible'
    titulo_form='titulo' 
    controlador_form='Devolución Inservible'
    accion_form='detalleDIP_edit/' + iddip +'/' +idcasco
    cancelbtn_form='/comerciax/casco/cascodip/view/' + iddip +'/'
    
    
    if request.method == 'POST':
        form = DetalleDIPForm(request.POST)
        
        if form.is_valid():
            di=DetalleDIP.objects.get(casco=idcasco,dip=iddip)
            
            di.area=Area.objects.get(pk = form.data['area'])
            di.causa=CausasRechazo.objects.get(pk = form.data['causa'])
            
            try:
                di.save()
                return cascodip_view(request, iddip)
            except Exception, e:
                exc_info = e.__str__() # sys.exc_info()[:1]
                c = exc_info.find("DETAIL:")
                if c < 0:
                    l = l + ["Error Fatal."]
                else:
                    c = exc_info[c + 7:]
                    l=l+[c]
                transaction.rollback()
                form = DetalleDIPForm(request.POST)
                return render_to_response("form/form_edit.html",{'tipocliente':'2','form':form,'title':titulo_form, 'form_name': nombre_form,'form_description':descripcion_form,'controlador':controlador_form,'accion':accion_form
                                                         , 'cancelbtn':cancelbtn_form,'error2':l},context_instance = RequestContext(request))
            else:
                transaction.commit()
    else:   
        rdip =DetalleDIP.objects.select_related().get(casco=idcasco,dip=iddip)
        form = DetalleDIPForm(initial={'nro':rdip.casco.casco_nro,'area':rdip.area,'causa':rdip.causa})
        return render_to_response('form/form_edit.html',  {'tipocliente':'2','form': form, 'form_name':nombre_form,'form_description':descripcion_form,'accion':accion_form,'titulo':titulo_form,'controlador':controlador_form,'cancelbtn':cancelbtn_form},context_instance = RequestContext(request))
    return cascodip_view(request, iddip)  

#############################################################
#        ENTREGA DE VULCA A PRODUCCION
#############################################################

@login_required
def get_vp_list(request):
    #prepare the params
    try:
        fecha_desde=Fecha_Ver.objects.get()
    except Exception, e:
        fecha_desde=None
    if  fecha_desde == None:  
        querySet = VulcaProduccion.objects.select_related().all().order_by('-doc_vulcaproduccion__fecha_doc')
    else:
        querySet = VulcaProduccion.objects.select_related().filter(doc_vulcaproduccion__fecha_doc__gte=fecha_desde.fecha).order_by('-doc_vulcaproduccion__fecha_doc')
    #querySet = querySet.filter(doc__fecha_doc__year=2010)
 
    columnIndexNameMap = {0: '-casco_doc.fecha_doc',1: 'vulcaproduccion_nro',2:'casco_doc.fecha_doc'}
    #searchableColumns = ['cliente__nombre','recepcioncliente_nro']
    searchableColumns = ['vulcaproduccion_nro','doc_vulcaproduccion__fecha_doc']
    #path to template used to generate json
    jsonTemplatePath = 'casco/json/json_vp.txt'


    #call to generic function from utils
    return get_datatables_records(request, querySet, columnIndexNameMap, searchableColumns, jsonTemplatePath)

@login_required
def cascovp_index(request):
    if not request.user.has_perm('casco.vulcaprod'):
        return render_to_response("denegado.html",locals(),context_instance = RequestContext(request))
    
    return render_to_response('casco/cascovpindex.html',locals(),context_instance = RequestContext(request))

@login_required
@transaction.commit_on_success()
def cascovp_add(request):
    if not request.user.has_perm('casco.vulcaprod'):
        return render_to_response("denegado.html",locals(),context_instance = RequestContext(request))
    
    nombre_form='Vulca a Producción'
    descripcion_form='Entrega de Vulca a Producción'
    titulo_form='Vulca a Producción' 
    controlador_form='Vulca a Producción'
    accion_form='/comerciax/casco/cascovp/add'
    cancelbtn_form='/comerciax/casco/cascovp/index'
    fecha_cierre=Fechacierre.objects.get(almacen='c').fechaminima()
    fecha_maxima=Fechacierre.objects.get(almacen='c').fechamaxima()    
    c=None
    l=[]
    if request.method == 'POST':
        form = CascoCCForm(request.POST)

        #rajuste = form.cleaned_data['ajuste']
        if form.is_valid():
            doc=Doc()

            
            fechadoc=form.cleaned_data['fecha']
            doc.fecha_doc=fechadoc
            doc.observaciones=form.cleaned_data['observaciones']
            doc.fecha_operacion=datetime.date.today()
            doc.fecha_doc=fechadoc
            doc.tipo_doc='12'
         
            pk_user=User.objects.get(pk=request.user.id)
            # esto hay que cambiarlo y poner el operador
            pk_doc=uuid4()

            doc.id_doc = pk_doc 
            doc.operador=pk_user
            
            
            cp=VulcaProduccion()
            
            cp_nro=form.cleaned_data['nro']
            cp.vulcaproduccion_nro=cp_nro
            cp.doc_vulcaproduccion=doc
            
            recep=VulcaProduccion.objects.filter(vulcaproduccion_nro=cp_nro)
            if recep.__len__()!=0:
                for a1 in recep:
                    if a1.doc_vulcaproduccion.fecha_doc.year == fechadoc.year:
                        l=['Número de documento existente']
                        return render_to_response('form/form_adddetalle.html',  {'tipocliente':'0','form': form, 'form_name':nombre_form,'form_description':descripcion_form,
                                                                                 'accion':accion_form,'titulo':titulo_form,'controlador':controlador_form,
                                                                                 'cancelbtn':cancelbtn_form,'fecha_minima':fecha_cierre,'fecha_maxima':fecha_maxima,'error2':l},context_instance = RequestContext(request))

            try:

                doc.save()
                cp.save() 
                return HttpResponseRedirect('/comerciax/casco/cascovp/view/'+pk_doc.__str__())  
            except Exception, e:
                exc_info = e.__str__() # sys.exc_info()[:1]
                c = exc_info.find("DETAIL:")
                
                if c < 0:
                    l=l+["Error Fatal."]
                else:
                    c = exc_info[c + 7:]
                    l=l+[c] 
                                     
                transaction.rollback()
                form = CascoCCForm(request.POST)
                return render_to_response('form/form_adddetalle.html',  {'tipocliente':'2','form': form, 'form_name':nombre_form,'form_description':descripcion_form,
                                                                         'accion':accion_form,'titulo':titulo_form,'controlador':controlador_form,
                                                                         'cancelbtn':cancelbtn_form,'fecha_minima':fecha_cierre,'fecha_maxima':fecha_maxima,'error2':l},context_instance = RequestContext(request))
            else:
                transaction.commit()
    else:
        form = CascoCCForm(initial={'fecha':fecha_cierre}) 
    return render_to_response('form/form_adddetalle.html',  {'tipocliente':'2','form': form, 'form_name':nombre_form,'form_description':descripcion_form,
                                                             'accion':accion_form,'titulo':titulo_form,'controlador':controlador_form,
                                                             'cancelbtn':cancelbtn_form,'fecha_minima':fecha_cierre,'fecha_maxima':fecha_maxima,'error2':c},context_instance = RequestContext(request))

@login_required
@transaction.commit_on_success()
def cascovp_edit(request,idvp):
    if not request.user.has_perm('casco.vulcaprod'):
        return render_to_response("denegado.html",locals(),context_instance = RequestContext(request))
    
    nombre_form='Cascos a Producción'
    descripcion_form='Entrega de Casco a Producción'
    titulo_form='Cascos a Producción' 
    controlador_form='Cascos a Producción'
    accion_form='/comerciax/casco/cascovp/edit/'+idvp+'/'
    cancelbtn_form='/comerciax/casco/cascovp/view/'+idvp+'/'
    fecha_cierre=Fechacierre.objects.get(almacen='c').fechaminima()
    fecha_maxima=Fechacierre.objects.get(almacen='c').fechamaxima()
    c=None
    l=[]
        
    if request.method == 'POST':
        form = CascoCCForm(request.POST)

        #rajuste = form.cleaned_data['ajuste']
        if form.is_valid():
            cp=VulcaProduccion.objects.get(pk=idvp)
            object_doc=Doc.objects.get(pk=idvp)
            
            object_doc.fecha_doc=form.cleaned_data['fecha']
            fechadoc1=form.cleaned_data['fecha']
            object_doc.observaciones=form.cleaned_data['observaciones']
            object_doc.fecha_operacion=datetime.date.today()
         
            pk_user=User.objects.get(pk=request.user.id)
            # esto hay que cambiarlo y poner el operador
            #pk_doc=uuid4()
            

            object_doc.operador=pk_user
            
            cp.vulcaproduccion_nro=form.cleaned_data['nro']
            rc_nro1=form.cleaned_data['nro']
            
            recep=VulcaProduccion.objects.filter(vulcaproduccion_nro=rc_nro1)
            if recep.__len__()!=0:
                for a1 in recep:
                    if a1.doc_vulcaproduccion.fecha_doc.year == fechadoc1.year and a1.pk!=idvp:
                        l=['Número de documento existente']
                        return render_to_response('form/form_adddetalle.html',  {'tipocliente':'0','form': form, 'form_name':nombre_form,'form_description':descripcion_form,
                                                                                 'accion':accion_form,'titulo':titulo_form,'controlador':controlador_form,
                                                                                 'cancelbtn':cancelbtn_form,'error2':l,'fecha_minima':fecha_cierre,'fecha_maxima':fecha_maxima},context_instance = RequestContext(request))                                                                                 

         
            #RecepcionCliente.objects.create(doc_recepcioncliente=obj_doc,recepcioncliente_nro=nro,recepcioncliente_ajuste=ajuste,cliente=obj_cliente)
            try:
                object_doc.save()
                cp.save() 
 
                return HttpResponseRedirect('/comerciax/casco/cascovp/view/'+idvp)  

            except Exception, e:
                exc_info = e.__str__() # sys.exc_info()[:1]
                c = exc_info.find("DETAIL:")
                
                if c < 0:
                    l=l+["Error Fatal."]
                else:
                    c = exc_info[c + 7:]
                    l=l+[c]
                    
                transaction.rollback()
                form = CascoCCForm(request.POST)
                return render_to_response('form/form_adddetalle.html',  {'tipocliente':'2','form': form, 'form_name':nombre_form,'form_description':descripcion_form,
                                                                         'accion':accion_form,'titulo':titulo_form,'controlador':controlador_form,
                                                                         'cancelbtn':cancelbtn_form,'fecha_minima':fecha_cierre,'fecha_maxima':fecha_maxima,'error2':l},context_instance = RequestContext(request))
            else:
                transaction.commit()     
    else:
        cp = VulcaProduccion.objects.select_related().get(pk=idvp)
        form = CascoCCForm(initial={'nro':cp.vulcaproduccion_nro,'fecha':cp.doc_vulcaproduccion.fecha_doc,
                                             'observaciones':cp.doc_vulcaproduccion.observaciones})
    return render_to_response('form/form_edit.html',  {'tipocliente':'2','form': form, 'form_name':nombre_form,'form_description':descripcion_form,'accion':accion_form,'titulo':titulo_form,
                                                       'controlador':controlador_form,'cancelbtn':cancelbtn_form,'fecha_minima':fecha_cierre,'fecha_maxima':fecha_maxima},context_instance = RequestContext(request))

@login_required
def cascovp_view(request,idvp):
    if not request.user.has_perm('casco.vulcaprod'):
        return render_to_response("denegado.html",locals(),context_instance = RequestContext(request))
    
    l=[]
    cp = VulcaProduccion.objects.select_related().get(pk=idvp)
    rc_fecha=cp.doc_vulcaproduccion.fecha_doc.strftime("%d/%m/%Y")
    rc_nro=cp.vulcaproduccion_nro
    rc_observaciones=cp.doc_vulcaproduccion.observaciones
    
    filas = DetalleVP.objects.select_related().filter(vp=idvp).order_by('admincomerciax_producto.descripcion','casco_casco.casco_nro')
    adiciono=True
    if cp.procesado==True:
        adiciono=True
        editar=False
    else:
        editar=editar_documento(filas, idvp)
        
    elementos_detalle=[]
    id1=''
    k=0
    k2=0
    for a1 in filas:
        if k!=0:
            if id1!=a1.casco.producto.id:
                elementos_detalle[k-1]['cantidad'] = k2
                k2=0
        elementos_detalle+=[{'cliente':a1.casco.get_cliente,'casco_id':a1.casco.id_casco,
                             'casco_nro':a1.casco.casco_nro,'producto':a1.casco.producto,
                             'productoid':a1.casco.producto.id}]
        k+=1
        k2+=1
        id1=a1.casco.producto.id  
    if k!=0:
        elementos_detalle[k-1]['cantidad'] = k2

        
    return render_to_response('casco/viewcascovp.html',{'total_casco':k,'rc_nro':rc_nro,'fecha':rc_fecha,'observaciones':rc_observaciones,'rc_id':idvp,
                                                        'elementos_detalle':elementos_detalle, 'edito':editar,'adiciono':adiciono,'error2':l},context_instance = RequestContext(request))

@login_required
@transaction.commit_on_success()
def cascovp_del(request,idvp):
    if not request.user.has_perm('casco.vulcaprod'):
        return render_to_response("denegado.html",locals(),context_instance = RequestContext(request))
    
    try:
        
        filas = DetalleVP.objects.filter(vp=idvp)
        for canti in filas:
            actualiza_traza(canti.casco.id_casco,idvp)
        
        Doc.objects.select_related().get(pk=idvp).delete()
        return HttpResponseRedirect('/comerciax/casco/cascovp/index')
    except Exception :
        transaction.rollback()
        l = ['Error al eliminar el documento']
        cp = VulcaProduccion.objects.select_related().get(pk=idvp)
        rc_fecha=cp.doc_vulcaproduccion.fecha_doc.strftime("%d/%m/%Y")

        rc_nro=cp.vulcaproduccion_nro
        editar=1
        rc_observaciones=cp.doc_vulcaproduccion.observaciones
        filas = DetalleVP.objects.select_related().filter(vp=idvp).order_by('admincomerciax_producto.descripcion','casco_casco.casco_nro')

        return render_to_response('casco/viewcascovp.html',{'rc_nro':rc_nro,'fecha':rc_fecha,'observaciones':rc_observaciones,'rc_id':idvp,'elementos_detalle':filas, 'edito':editar,'error2':l},context_instance = RequestContext(request))

    else:
        transaction.commit()


#############################################################
#        DETALLE VULCA A PRODUCCION 
#############################################################
@login_required
@transaction.commit_on_success()
def detalleVP_add(request,idvp):
    if not request.user.has_perm('casco.vulcaprod'):
        return render_to_response("denegado.html",locals(),context_instance = RequestContext(request))
    
    titulo_form='Cascos a Producción' 
    controlador_form='Cascos a Producción'
    descripcion_form='Seleccionar cascos para producción'
    
    accion_form='detalleVP_add'
    cancelbtn_form='/comerciax/casco/cascovp/view/'+idvp
    estado="DVP" 
    l=[]
    medidas=Producto.objects.all()
 
    cc=VulcaProduccion.objects.get(pk=idvp)
    #cascos=Casco.objects.select_related().filter(estado_actual=Estados.estados["Casco"]).order_by('admincomerciax_producto.descripcion','casco_nro')
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
                '''
                
                
                detalle=DetalleVP()
                detalle.id_detallevp=uuid4()
                detalle.vp=VulcaProduccion.objects.get(pk=idvp)
                detalle.casco=Casco.objects.get(pk=seleccion[k])
                nro=Casco.objects.get(pk=seleccion[k]).casco_nro
                try:
                    detalle.save()
                except Exception, e:
                    exc_info = e.__str__() # sys.exc_info()[:1]
                    c = exc_info.find("DETAIL:")
                    
                    if c < 0:
                        l=l+["Error Fatal."]
                    else:
                        l=['El casco ' + str(nro) +' ya existe en este documento']
                        c = exc_info[c + 7:]
                        transaction.rollback()
                        return render_to_response('casco/form_seleccion.html', {'estado':estado,'title':titulo_form,'controlador':controlador_form,'accion':accion_form,
                                                     'cancelbtn':cancelbtn_form, 'nro':cc.vulcaproduccion_nro,'form_description':descripcion_form,
                                                     'fecha':cc.doc_vulcaproduccion.fecha_doc.strftime("%d/%m/%Y"),'medida':medidas,'observaciones':cc.doc_vulcaproduccion.observaciones,
                                                     'rc_id':idvp,'error2':l},context_instance = RequestContext(request))
                        
                Casco.objects.filter(pk=seleccion[k]).update(estado_actual="Produccion",fecha=VulcaProduccion.objects.get(pk=idvp).doc_vulcaproduccion.fecha_doc)
                add_trazabilidad(seleccion[k], idvp, "Produccion")
                
                
            k=k+1
        if request.POST.__contains__('submit1'):
            return render_to_response('casco/form_seleccion.html', {'estado':estado,'title':titulo_form,'controlador':controlador_form,'accion':accion_form,
                                                     'cancelbtn':cancelbtn_form, 'nro':cc.vulcaproduccion_nro,'form_description':descripcion_form,
                                                     'fecha':cc.doc_vulcaproduccion.fecha_doc.strftime("%d/%m/%Y"),'medida':medidas,'observaciones':cc.doc_vulcaproduccion.observaciones,
                                                     'rc_id':idvp},context_instance = RequestContext(request))
        else:
            return HttpResponseRedirect('/comerciax/casco/cascovp/view/' + idvp)
    medidas=Producto.objects.all()  
    return render_to_response('casco/form_seleccion.html', {'estado':estado,'title':titulo_form,'controlador':controlador_form,'accion':accion_form,
                                                      'cancelbtn':cancelbtn_form, 'nro':cc.doc_vulcaproduccion,'form_description':descripcion_form,
                                                      'fecha':cc.doc_vulcaproduccion.fecha_doc.strftime("%d/%m/%Y"),'medida':medidas,'observaciones':cc.doc_vulcaproduccion.observaciones,
                                                      'rc_id':idvp},context_instance = RequestContext(request))    

@login_required
def detalleVP_delete(request,idvp,idcasco):
    if not request.user.has_perm('casco.vulcaprod'):
        return render_to_response("denegado.html",locals(),context_instance = RequestContext(request))
    
    casco=Casco.objects.select_related().get(pk=idcasco)
    nro=casco.casco_nro
    
    if eliminar_detalle_sino(casco.id_casco,idvp):
        DetalleVP.objects.get(casco=idcasco).delete()
        actualiza_traza(idcasco,idvp)
        
        filas = DetalleVP.objects.select_related().filter(vp=idvp).order_by('casco__producto__descripcion','casco__casco_nro')

#        cantidades2=DetalleCC.objects.filter(cc=idcp).values("casco__producto__id").annotate(Count('casco__producto__id')) 
        total_casco=str(filas.count())
            
        elementos_detalle=[]
        id1=''
        k=0
        k2=0
        for a1 in filas:
            if k!=0:
                if id1!=a1.casco.producto.id:
#                    elementos_detalle[k-1]['cantidad'] = elementos_detalle[k-1]['productoid']
                    elementos_detalle[k-1]['cantidad'] = k2
                    k2=0
                    
            elementos_detalle+=[{'total_casco':total_casco,
                                 'id_doc':a1.vp.doc_vulcaproduccion.id_doc,'casco_id':a1.casco.id_casco,
                                 'casco_nro':a1.casco.casco_nro,'producto':a1.casco.producto.descripcion,
                                 'productoid':a1.casco.producto.id,'cliente':a1.casco.get_cliente()}]
            k+=1
            id1=a1.casco.producto.id 
            k2+=1
            
        if k!=0:
            elementos_detalle[k-1]['cantidad'] = k2
        return HttpResponse(simplejson.dumps(elementos_detalle),content_type = 'application/javascript; charset=utf8')
    else:
        error2 = "No se puede eliminar el casco " + str(nro) + " ya que su estado ha cambiado "
        return HttpResponse(json.dumps({'error':True, 'message':error2}),mimetype=u'application/json')


#############################################################
#        ENTREGA DE CASCOS DE PRODUCCION A VULCA
#############################################################

@login_required
def get_dvp_list(request):
    #prepare the params
    try:
        fecha_desde=Fecha_Ver.objects.get()
    except Exception, e:
        fecha_desde=None
    if  fecha_desde == None:  
        querySet = DVP.objects.select_related().all().order_by('-doc_dvp__fecha_doc')
    else:
        querySet = DVP.objects.select_related().filter(doc_dvp__fecha_doc__gte=fecha_desde.fecha).order_by('-doc_dvp__fecha_doc')
    
    #querySet = querySet.filter(doc__fecha_doc__year=2010)
 
    columnIndexNameMap = {0: '-casco_doc.fecha_doc',1: 'nro_dvp',2:'casco_doc.fecha_doc'}
    #searchableColumns = ['cliente__nombre','recepcioncliente_nro']
    searchableColumns = ['nro_dvp','doc_dvp__fecha_doc']
    #path to template used to generate json
    jsonTemplatePath = 'casco/json/json_dvp.txt'


    #call to generic function from utils
    return get_datatables_records(request, querySet, columnIndexNameMap, searchableColumns, jsonTemplatePath)


@login_required
def cascodvp_index(request):
    if not request.user.has_perm('casco.vulcaprod'):
        return render_to_response("denegado.html",locals(),context_instance = RequestContext(request))
    
    return render_to_response('casco/cascodvpindex.html',locals(),context_instance = RequestContext(request))


@login_required
@transaction.commit_on_success()
def cascodvp_add(request):
    if not request.user.has_perm('casco.vulcaprod'):
        return render_to_response("denegado.html",locals(),context_instance = RequestContext(request))
    
    nombre_form='Cascos Vulca'
    descripcion_form='Devolución de Cascos a Vulca'
    titulo_form='Cascos Vulca' 
    controlador_form='Cascos Vulca'
    accion_form='/comerciax/casco/cascodvp/add'
    cancelbtn_form='/comerciax/casco/cascodvp/index'
    fecha_cierre=Fechacierre.objects.get(almacen='c').fechaminima()
    fecha_maxima=Fechacierre.objects.get(almacen='c').fechamaxima()
    c=None
    l=[]
    if request.method == 'POST':
        form = CascoDIPForm(request.POST)

        #rajuste = form.cleaned_data['ajuste']
        if form.is_valid():
            doc=Doc()

            fechadoc=form.cleaned_data['fecha']
            doc.fecha_doc=fechadoc
            doc.observaciones=form.cleaned_data['observaciones']
            doc.fecha_operacion=datetime.date.today()
            doc.fecha_doc=fechadoc
            doc.tipo_doc='5'
         
            pk_user=User.objects.get(pk=request.user.id)
            # esto hay que cambiarlo y poner el operador
            pk_doc=uuid4()
            

            doc.id_doc = pk_doc 
            doc.operador=pk_user
            
            
            dvp=DVP()
            

            dvp.nro_dvp=form.cleaned_data['nro']
            rc_nro1=form.cleaned_data['nro']
            dvp.doc_dvp=doc
            recep=DVP.objects.filter(nro_dvp=rc_nro1)
            if recep.__len__()!=0:
                for a1 in recep:
                    if a1.doc_dvp.fecha_doc.year == fechadoc.year:
                        l=['Número de documento existente']
                        return render_to_response('form/form_adddetalle.html',  {'tipocliente':'0','form': form, 'form_name':nombre_form,'form_description':descripcion_form,
                                                                                 'accion':accion_form,'titulo':titulo_form,'controlador':controlador_form,
                                                                                 'cancelbtn':cancelbtn_form,'fecha_minima':fecha_cierre,'fecha_maxima':fecha_maxima,'error2':l},context_instance = RequestContext(request))

                                    
            try:

                doc.save()
                dvp.save() 
 
                return HttpResponseRedirect('/comerciax/casco/cascodvp/view/'+pk_doc.__str__())  
            except Exception, e:
                exc_info = e.__str__() # sys.exc_info()[:1]
                c = exc_info.find("DETAIL:")
                
                if c < 0:
                    l=l+["Error Fatal."]
                else:
                    c = exc_info[c + 7:]
                    l=l+[c] 
                                     
                transaction.rollback()
                form = CascoDIPForm(request.POST)
                return render_to_response('form/form_adddetalle.html',  {'tipocliente':'2','form': form, 'form_name':nombre_form,'form_description':descripcion_form,
                                                                         'accion':accion_form,'titulo':titulo_form,'controlador':controlador_form,
                                                                         'cancelbtn':cancelbtn_form,'fecha_minima':fecha_cierre,'fecha_maxima':fecha_maxima,'error2':l},context_instance = RequestContext(request))
            else:
                transaction.commit()
    else:
        form = CascoDIPForm(initial={'fecha':fecha_cierre}) 
    return render_to_response('form/form_adddetalle.html',  {'tipocliente':'2','form': form, 'form_name':nombre_form,'form_description':descripcion_form,
                                                             'accion':accion_form,'titulo':titulo_form,'controlador':controlador_form,
                                                             'cancelbtn':cancelbtn_form,'fecha_minima':fecha_cierre,'fecha_maxima':fecha_maxima,'error2':c},context_instance = RequestContext(request))


@login_required
@transaction.commit_on_success()
def cascodvp_edit(request,iddvp):
    if not request.user.has_perm('casco.vulcaprod'):
        return render_to_response("denegado.html",locals(),context_instance = RequestContext(request))
    
    nombre_form='Cascos Vulca'
    descripcion_form='Devolución de Cascos a Vulca'
    titulo_form='Cascos Vulca' 
    controlador_form='Cascos Vulca'
    accion_form='/comerciax/casco/cascodvp/edit/'+iddvp+'/'
    cancelbtn_form='/comerciax/casco/cascodvp/view/'+iddvp+'/'
    fecha_cierre=Fechacierre.objects.get(almacen='c').fechaminima()
    fecha_maxima=Fechacierre.objects.get(almacen='c').fechamaxima()
    c=None
    l=[]
        
    if request.method == 'POST':
        form = CascoDIPForm(request.POST)

        #rajuste = form.cleaned_data['ajuste']
        if form.is_valid():
            dvp=DVP.objects.get(pk=iddvp)
            object_doc=Doc.objects.get(pk=iddvp)
            
            object_doc.fecha_doc=form.cleaned_data['fecha']
            fechadoc1=form.cleaned_data['fecha']
            object_doc.observaciones=form.cleaned_data['observaciones']
            object_doc.fecha_operacion=datetime.date.today()
         
            pk_user=User.objects.get(pk=request.user.id)
            # esto hay que cambiarlo y poner el operador
            #pk_doc=uuid4()
            

            object_doc.operador=pk_user
            
            dvp.nro_dvp=form.cleaned_data['nro']
            rc_nro1=form.cleaned_data['nro']
            
            recep=DVP.objects.filter(nro_dvp=rc_nro1)
            if recep.__len__()!=0:
                for a1 in recep:
                    if a1.doc_dvp.fecha_doc.year == fechadoc1.year and a1.pk!=iddvp:
                        l=['Número de documento existente']
                        return render_to_response('form/form_adddetalle.html',  {'tipocliente':'0','form': form, 'form_name':nombre_form,'form_description':descripcion_form,
                                                                                 'accion':accion_form,'titulo':titulo_form,'controlador':controlador_form,
                                                                                 'cancelbtn':cancelbtn_form,'error2':l,'fecha_minima':fecha_cierre,'fecha_maxima':fecha_maxima},context_instance = RequestContext(request))    
            #RecepcionCliente.objects.create(doc_recepcioncliente=obj_doc,recepcioncliente_nro=nro,recepcioncliente_ajuste=ajuste,cliente=obj_cliente)
            try:
                object_doc.save()
                dvp.save() 
 
                return HttpResponseRedirect('/comerciax/casco/cascodvp/view/'+iddvp)  

            except Exception, e:
                exc_info = e.__str__() # sys.exc_info()[:1]
                c = exc_info.find("DETAIL:")
                
                if c < 0:
                    l=l+["Error Fatal."]
                else:
                    c = exc_info[c + 7:]
                    l=l+[c]
                    
                transaction.rollback()
                form = CascoDIPForm(request.POST)
                return render_to_response('form/form_adddetalle.html',  {'tipocliente':'2','form': form, 'form_name':nombre_form,'form_description':descripcion_form,
                                                                         'accion':accion_form,'titulo':titulo_form,'controlador':controlador_form,
                                                                         'cancelbtn':cancelbtn_form,'fecha_minima':fecha_cierre,'fecha_maxima':fecha_maxima,'error2':l},context_instance = RequestContext(request))
            else:
                transaction.commit()     
    else:
        dvp = DVP.objects.select_related().get(pk=iddvp)
        form = CascoDIPForm(initial={'nro':dvp.nro_dvp,'fecha':dvp.doc_dvp.fecha_doc,
                                             'observaciones':dvp.doc_dvp.observaciones})
    return render_to_response('form/form_edit.html',  {'tipocliente':'2','form': form, 'form_name':nombre_form,'form_description':descripcion_form,'accion':accion_form,'titulo':titulo_form,
                                                       'controlador':controlador_form,'cancelbtn':cancelbtn_form,'fecha_minima':fecha_cierre,'fecha_maxima':fecha_maxima},context_instance = RequestContext(request))

@login_required
def cascodvp_view(request,iddvp):
    if not request.user.has_perm('casco.vulcaprod'):
        return render_to_response("denegado.html",locals(),context_instance = RequestContext(request))
    
    l=[]
    dvp = DVP.objects.select_related().get(pk=iddvp)
    rc_fecha=dvp.doc_dvp.fecha_doc.strftime("%d/%m/%Y")
    rc_nro=dvp.nro_dvp
    
    rc_observaciones=dvp.doc_dvp.observaciones
    filas = DetalleDVP.objects.select_related().filter(dvp=iddvp).order_by('casco__producto__descripcion','casco__casco_nro')
    adiciono=True
    if dvp.procesado==True:
        editar=False
        adiciono=False
    else:
        editar=editar_documento(filas, iddvp)  
    elementos_detalle=[]
    id1=''
    k=0
    k2=0
    for a1 in filas:
        if k!=0:
            if id1!=a1.casco.producto.id:
                elementos_detalle[k-1]['cantidad'] = k2
                k2=0
        elementos_detalle+=[{'cliente':a1.casco.get_cliente,'casco_id':a1.casco.id_casco,
                             'casco_nro':a1.casco.casco_nro,'producto':a1.casco.producto,
                             'productoid':a1.casco.producto.id}]
        k+=1
        k2+=1
        id1=a1.casco.producto.id  
    if k!=0:
        elementos_detalle[k-1]['cantidad'] = k2
    return render_to_response('casco/viewcascodvp.html',{'total_casco':k,'rc_nro':rc_nro,'fecha':rc_fecha,'observaciones':rc_observaciones,
                                                              'rc_id':iddvp,'elementos_detalle':elementos_detalle, 'edito':editar,
                                                              'adiciono':adiciono,'error2':l},context_instance = RequestContext(request))    
         
#    return render_to_response('casco/viewcascodvp.html',{'rc_nro':rc_nro,'fecha':rc_fecha,'observaciones':rc_observaciones,'rc_id':iddvp,
#                                                         'elementos_detalle':filas, 'edito':editar,'adiciono':adiciono,'error2':l},context_instance = RequestContext(request))

@login_required
@transaction.commit_on_success()
def cascodvp_del(request,iddvp):
    if not request.user.has_perm('casco.vulcaprod'):
        return render_to_response("denegado.html",locals(),context_instance = RequestContext(request))
    
    
    try:
        filas = DetalleDVP.objects.filter(dvp=iddvp)
        for canti in filas:
            actualiza_traza(canti.casco.id_casco,iddvp)
        
        Doc.objects.select_related().get(pk=iddvp).delete()
        return HttpResponseRedirect('/comerciax/casco/cascodvp/index')
    except Exception :
        transaction.rollback()
        l = ['Error al eliminar el documento']
        dvp = DVP.objects.select_related().get(pk=iddvp)
        rc_fecha=dvp.doc_dvp.fecha_doc.strftime("%d/%m/%Y")

        rc_nro=dvp.nro_dvp

        editar=1
        rc_observaciones=dvp.doc_dvp.observaciones
        filas = DetalleDVP.objects.select_related().filter(dvp=iddvp).order_by('admincomerciax_producto.descripcion','casco_casco.casco_nro')

        return render_to_response('casco/viewcascodvp.html',{'rc_nro':rc_nro,'fecha':rc_fecha,'observaciones':rc_observaciones,'rc_id':iddvp,'elementos_detalle':filas, 'edito':editar,'error2':l},context_instance = RequestContext(request))

    else:
        transaction.commit()

#############################################################
#        DETALLE CASCO DE PRODUCCION A VULCA
#############################################################
@login_required
@transaction.commit_on_success()
def detalleDVP_add(request,iddvp):
    if not request.user.has_perm('casco.dvp'):
        return render_to_response("denegado.html",locals(),context_instance = RequestContext(request))
    
    l=[]
    titulo_form='Devolución de Producción a Vulca' 
    controlador_form='Devolución a Vulca'
    descripcion_form='Seleccionar cascos para vulca'
    accion_form='detalleDVP_add'
    cancelbtn_form='/comerciax/casco/cascodvp/view/'+iddvp
    estado="Produccion"
 
    dvp=DVP.objects.get(pk=iddvp)
    medidas=Producto.objects.all()
    #cascos=Casco.objects.select_related().filter(estado_actual=Estados.estados["Produccion"]).order_by('admincomerciax_producto.descripcion','casco_nro')

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
                '''
                
                
                detalle=DetalleDVP()
                detalle.id_detalledvp=uuid4()
                detalle.dvp=DVP.objects.get(pk=iddvp)
                detalle.casco=Casco.objects.get(pk=seleccion[k])
                nro=Casco.objects.get(pk=seleccion[k]).casco_nro
                try:
                    detalle.save()
                except Exception, e:
                    exc_info = e.__str__() # sys.exc_info()[:1]
                    c = exc_info.find("DETAIL:")
                    
                    if c < 0:
                        l=l+["Error Fatal."]
                    else:
                        l=['El casco ' + str(nro) +' ya existe en este documento']
                        c = exc_info[c + 7:]
                        transaction.rollback()
                        return render_to_response('casco/form_seleccion.html',{'medida':medidas,'estado':estado,'title':titulo_form,'controlador':controlador_form,'accion':accion_form,
                                                      'cancelbtn':cancelbtn_form, 'nro':dvp.nro_dvp,'form_description':descripcion_form,
                                                      'fecha':dvp.doc_dvp.fecha_doc.strftime("%d/%m/%Y"),'observaciones':dvp.doc_dvp.observaciones,
                                                      'rc_id':iddvp,'error2':l},context_instance = RequestContext(request))
                
                Casco.objects.filter(pk=seleccion[k]).update(estado_actual="DVP")
                add_trazabilidad(seleccion[k], iddvp, "DVP")
                
            k=k+1
        if request.POST.__contains__('submit1'):
            return render_to_response('casco/form_seleccion.html',{'medida':medidas,'estado':estado,'title':titulo_form,'controlador':controlador_form,'accion':accion_form,
                                                      'cancelbtn':cancelbtn_form, 'nro':dvp.nro_dvp,'form_description':descripcion_form,
                                                      'fecha':dvp.doc_dvp.fecha_doc.strftime("%d/%m/%Y"),'observaciones':dvp.doc_dvp.observaciones,
                                                      'rc_id':iddvp,'error2':l},context_instance = RequestContext(request))
        else:
            return HttpResponseRedirect('/comerciax/casco/cascodvp/view/' + iddvp)
    return render_to_response('casco/form_seleccion.html', {'medida':medidas,'estado':estado,'title':titulo_form,'controlador':controlador_form,'accion':accion_form,
                                                      'cancelbtn':cancelbtn_form, 'nro':dvp.nro_dvp, 'form_description':descripcion_form,
                                                      'fecha':dvp.doc_dvp.fecha_doc.strftime("%d/%m/%Y"),'observaciones':dvp.doc_dvp.observaciones,
                                                      'rc_id':iddvp,'error2':l},context_instance = RequestContext(request))    

@login_required
def detalleDVP_delete(request,iddvp,idcasco):  
    if not request.user.has_perm('casco.dvp'):
        return render_to_response("denegado.html",locals(),context_instance = RequestContext(request))
      
    casco=Casco.objects.select_related().get(pk=idcasco)
    nro=casco.casco_nro
    
    if eliminar_detalle_sino(casco.id_casco,iddvp):
        DetalleDVP.objects.get(casco=idcasco).delete()
        
        actualiza_traza(idcasco,iddvp)
        filas = DetalleDVP.objects.select_related().filter(dvp=iddvp).order_by('casco__producto__descripcion','casco__casco_nro')
        
        total_casco=str(filas.count())
            
        elementos_detalle=[]
        id1=''
        k=0
        k2=0
        for a1 in filas:
            if k!=0:
                if id1!=a1.casco.producto.id:
#                    elementos_detalle[k-1]['cantidad'] = elementos_detalle[k-1]['productoid']
                    elementos_detalle[k-1]['cantidad'] = k2
                    k2=0
                    
            elementos_detalle+=[{'total_casco':total_casco,
                                 'id_doc':a1.dvp.doc_dvp.id_doc,'casco_id':a1.casco.id_casco,
                                 'casco_nro':a1.casco.casco_nro,'producto':a1.casco.producto.descripcion,
                                 'productoid':a1.casco.producto.id,'cliente':a1.casco.get_cliente()}]
            k+=1
            id1=a1.casco.producto.id 
            k2+=1
            
        if k!=0:
            elementos_detalle[k-1]['cantidad'] = k2
        return HttpResponse(simplejson.dumps(elementos_detalle),content_type = 'application/javascript; charset=utf8')
    else:
        error2 = "No se puede eliminar el casco " + str(nro) + " ya que su estado ha cambiado "
        return HttpResponse(json.dumps({'error':True, 'message':error2}),mimetype=u'application/json')
        #return cascodvp_view(request, iddvp,error2)
    

#############################################################
#        TRANSFERENCIA DE CASCO A ENT. EXTERNAS             #
#############################################################
@login_required
def get_tc_list(request):
    #prepare the params
    
    try:
        fecha_desde=Fecha_Ver.objects.get()
    except Exception, e:
        fecha_desde=None
    if  fecha_desde == None:  
        querySet = Transferencia.objects.select_related().all().order_by('-doc_transferencia__fecha_doc')
    else:
        querySet = Transferencia.objects.select_related().filter(doc_transferencia__fecha_doc__gte=fecha_desde.fecha).order_by('-doc_transferencia__fecha_doc')
    
    #querySet = querySet.filter(doc__fecha_doc__year=2010)
 
    columnIndexNameMap = {0: '-casco_doc.fecha_doc',1: 'transferencia_nro',2:'casco_doc.fecha_doc',3:'admincomerciax_cliente.nombre',4:'cerrada'}

    searchableColumns = ['transferencia_nro','doc_transferencia__fecha_doc','destino__nombre']
    #path to template used to generate json
    jsonTemplatePath = 'casco/json/json_tc.txt'

    #call to generic function from utils
    return get_datatables_records(request, querySet, columnIndexNameMap, searchableColumns, jsonTemplatePath)


@login_required    
def trans_index(request):
    if not request.user.has_perm('casco.transferencia'):
        return render_to_response("denegado.html",locals(),context_instance = RequestContext(request))
    
    return render_to_response('casco/transindex.html',locals(),context_instance = RequestContext(request))

@login_required
@transaction.commit_on_success()
def trans_add(request):
    if not request.user.has_perm('casco.transferencia'):
        return render_to_response("denegado.html",locals(),context_instance = RequestContext(request))
    
    nombre_form='Transferencia de Cascos'
    descripcion_form='Transferencia de Cascos a Clientes Externos'
    titulo_form='Transferencia de Cascos' 
    controlador_form='Transferencia de Cascos'
    accion_form='/comerciax/casco/trans/add'
    cancelbtn_form='/comerciax/casco/trans/index'
    fecha_cierre=Fechacierre.objects.get(almacen='c').fechaminima()
    fecha_maxima=Fechacierre.objects.get(almacen='c').fechamaxima()
    c=None
    l=[]
    if request.method == 'POST':
        form = TransferenciaForm(request.POST)

        #rajuste = form.cleaned_data['ajuste']
        if form.is_valid():
            doc=Doc()

            
            fechadoc=form.cleaned_data['fecha']
            doc.fecha_doc=fechadoc
            doc.observaciones=form.cleaned_data['observaciones']
            doc.fecha_operacion=datetime.date.today()
            doc.tipo_doc='6'
         
            pk_user=User.objects.get(pk=request.user.id)
            # esto hay que cambiarlo y poner el operador
            pk_doc=uuid4()
            

            doc.id_doc = pk_doc 
            doc.operador=pk_user
            
            
            tc=Transferencia()
            
            tc_nro=form.cleaned_data['nro']
            
            
            obj_destino = Cliente.objects.get(pk = form.data['destino']) 
            tc.transferencia_nro=tc_nro
            tc.destino=obj_destino
            tc.doc_transferencia=doc
            
            recep=Transferencia.objects.filter(transferencia_nro=tc_nro)
            if recep.__len__()!=0:
                for a1 in recep:
                    if a1.doc_transferencia.fecha_doc.year == fechadoc.year:
                        l=['Número de documento existente']
                        return render_to_response('form/form_adddetalle.html',  {'tipocliente':'0','form': form, 'form_name':nombre_form,'form_description':descripcion_form,
                                                                                 'accion':accion_form,'titulo':titulo_form,'controlador':controlador_form,
                                                                                 'cancelbtn':cancelbtn_form,'fecha_minima':fecha_cierre,'fecha_maxima':fecha_maxima,'error2':l},context_instance = RequestContext(request))

            try:

                doc.save()
                tc.save() 
 
                return HttpResponseRedirect('/comerciax/casco/trans/view/'+pk_doc.__str__())  
            except Exception, e:
                exc_info = e.__str__() # sys.exc_info()[:1]
                c = exc_info.find("DETAIL:")
                
                if c < 0:
                    l=l+["Error Fatal."]
                else:
                    c = exc_info[c + 7:]
                    l=l+[c] 
                                     
                transaction.rollback()
                form = TransferenciaForm(request.POST)
                return render_to_response('form/form_adddetalle.html',  {'tipocliente':'2','form': form, 'form_name':nombre_form,'form_description':descripcion_form,
                                                                         'accion':accion_form,'titulo':titulo_form,'controlador':controlador_form,
                                                                         'cancelbtn':cancelbtn_form,'fecha_minima':fecha_cierre,'fecha_maxima':fecha_maxima,'error2':l},context_instance = RequestContext(request))
            else:
                transaction.commit()
    else:
        form = TransferenciaForm(initial={'fecha':fecha_cierre}) 
    return render_to_response('form/form_adddetalle.html',  {'tipocliente':'2','form': form, 'form_name':nombre_form,'form_description':descripcion_form,
                                                             'accion':accion_form,'titulo':titulo_form,'controlador':controlador_form,
                                                             'cancelbtn':cancelbtn_form,'fecha_minima':fecha_cierre,'fecha_maxima':fecha_maxima,'error2':c},context_instance = RequestContext(request))


@login_required
@transaction.commit_on_success()
def trans_edit(request,idtc):
    if not request.user.has_perm('casco.transferencia'):
        return render_to_response("denegado.html",locals(),context_instance = RequestContext(request))
    
    nombre_form='Transferencia de Cascos'
    descripcion_form='Transferencia de Cascos a Clientes Externos'
    titulo_form='Transferencia de Cascos' 
    controlador_form='Transferir Cascos'
    accion_form='/comerciax/casco/trans/edit/' + idtc +'/'
    cancelbtn_form='/comerciax/casco/trans/view/'+ idtc +'/'
    fecha_cierre=Fechacierre.objects.get(almacen='c').fechaminima()
    fecha_maxima=Fechacierre.objects.get(almacen='c').fechamaxima()
    c=None
    l=[]
        
    if request.method == 'POST':
        form = TransferenciaForm(request.POST)

        #rajuste = form.cleaned_data['ajuste']
        if form.is_valid():
            tc=Transferencia.objects.get(pk=idtc)
            object_doc=Doc.objects.get(pk=idtc)
            
            object_doc.fecha_doc=form.cleaned_data['fecha']
            fechadoc1=form.cleaned_data['fecha']
            object_doc.observaciones=form.cleaned_data['observaciones']
            object_doc.fecha_operacion=datetime.date.today()
         
            pk_user=User.objects.get(pk=request.user.id)

            object_doc.operador=pk_user
            
            tc.transferencia_nro=form.cleaned_data['nro']
            rc_nro1=form.cleaned_data['nro']
            
            tc.destino=Cliente.objects.get(pk = form.data['destino'])
            recep=Transferencia.objects.filter(transferencia_nro=rc_nro1)
            if recep.__len__()!=0:
                for a1 in recep:
                    if a1.doc_transferencia.fecha_doc.year == fechadoc1.year and a1.pk!=idtc:
                        l=['Número de documento existente']
                        return render_to_response('form/form_adddetalle.html',  {'tipocliente':'0','form': form, 'form_name':nombre_form,'form_description':descripcion_form,
                                                                                 'accion':accion_form,'titulo':titulo_form,'controlador':controlador_form,
                                                                                 'cancelbtn':cancelbtn_form,'error2':l,'fecha_minima':fecha_cierre,'fecha_maxima':fecha_maxima},context_instance = RequestContext(request))    
            try:
                object_doc.save()
                tc.save() 
 
                return HttpResponseRedirect('/comerciax/casco/trans/view/'+idtc)  

            except Exception, e:
                exc_info = e.__str__() # sys.exc_info()[:1]
                c = exc_info.find("DETAIL:")
                
                if c < 0:
                    l=l+["Error Fatal."]
                else:
                    c = exc_info[c + 7:]
                    l=l+[c]
                    
                transaction.rollback()
                form = TransferenciaForm(request.POST)
                return render_to_response('form/form_adddetalle.html',  {'tipocliente':'2','form': form, 'form_name':nombre_form,'form_description':descripcion_form,
                                                                         'accion':accion_form,'titulo':titulo_form,'controlador':controlador_form,
                                                                         'cancelbtn':cancelbtn_form,'fecha_minima':fecha_cierre,'fecha_maxima':fecha_maxima,'error2':l},context_instance = RequestContext(request))
            else:
                transaction.commit()     
    else:
        tc = Transferencia.objects.select_related().get(pk=idtc)
        form = TransferenciaForm(initial={'nro':tc.transferencia_nro,'fecha':tc.doc_transferencia.fecha_doc,
                                             'destino':tc.destino,'observaciones':tc.doc_transferencia.observaciones,'transf_cerrada':tc.cerrada})
    return render_to_response('form/form_edit.html',  {'tipocliente':'2','form': form, 'form_name':nombre_form,'form_description':descripcion_form,'accion':accion_form,
                                                       'titulo':titulo_form,'controlador':controlador_form,'cancelbtn':cancelbtn_form,
                                                       'fecha_minima':fecha_cierre,'fecha_maxima':fecha_maxima},context_instance = RequestContext(request))


@login_required
def trans_view(request,idtc):
    if not request.user.has_perm('casco.transferencia'):
        return render_to_response("denegado.html",locals(),context_instance = RequestContext(request))
    
    l=[]
    tc = Transferencia.objects.select_related().get(pk=idtc)
    tc_fecha=tc.doc_transferencia.fecha_doc.strftime("%d/%m/%Y")
    tc_destino=tc.destino.nombre
    tc_nro=tc.transferencia_nro
    cerrada=tc.cerrada

    tc_observaciones=tc.doc_transferencia.observaciones
    elementos_detalle=[]
    filas = DetalleTransferencia.objects.select_related().filter(transf=idtc).order_by('casco__producto__descripcion','casco__casco_nro')
    adiciono=True
    if tc.procesado==True:
        editar=False
        adiciono=False
    else:
        editar=editar_documento(filas, idtc)
        elementos_detalle=[]
    id1=''
    k=0
    k2=0
    for a1 in filas:
        if k!=0:
            if id1!=a1.casco.producto.id:
                elementos_detalle[k-1]['cantidad'] = k2
                k2=0
        elementos_detalle+=[{'cliente':a1.casco.get_cliente,'casco_id':a1.casco.id_casco,
                             'casco_nro':a1.casco.casco_nro,'producto':a1.casco.producto,
                             'productoid':a1.casco.producto.id}]
        k+=1
        k2+=1
        id1=a1.casco.producto.id  
    if k!=0:
        elementos_detalle[k-1]['cantidad'] = k2
    return render_to_response('casco/viewtrans.html',{'destino':tc_destino,'cerrada':cerrada,'total_casco':k,'rc_nro':tc_nro,'fecha':tc_fecha,'observaciones':tc_observaciones,
                                                              'tc_id':idtc,'elementos_detalle':elementos_detalle, 'edito':editar,
                                                              'adiciono':adiciono,'error2':l},context_instance = RequestContext(request))


@login_required
@transaction.commit_on_success()
def trans_del(request,idtc):
    if not request.user.has_perm('casco.transferencia'):
        return render_to_response("denegado.html",locals(),context_instance = RequestContext(request))
    
    try:
        
        filas = DetalleTransferencia.objects.filter(transf=idtc)
        for canti in filas:
            actualiza_traza(canti.casco.id_casco,idtc)
        
        Doc.objects.select_related().get(pk=idtc).delete()
        return HttpResponseRedirect('/comerciax/casco/trans/index')
    except Exception :
        transaction.rollback()
        l = ['Error al eliminar el documento']
        tc = Transferencia.objects.select_related().get(pk=idtc)
        tc_fecha=tc.doc_transferencia.fecha_doc.strftime("%d/%m/%Y")
        tc_destino=tc.destino.nombre
        tc_nro=tc.transferencia_nro
        editar=1

        tc_observaciones=tc.doc_transferencia.observaciones
        filas = DetalleTransferencia.objects.select_related().filter(transf=idtc).order_by('admincomerciax_producto.descripcion','casco_casco.casco_nro')
  
    # Verificar si se puede editar. Se puede editar si todos los cascos relacionados con él el estado es Casco
        return render_to_response('casco/viewtrans.html',{'nro':tc_nro,'fecha':tc_fecha,'destino':tc_destino,'observaciones':tc_observaciones,'tc_id':idtc,'elementos_detalle':filas, 'edito':editar,'error2':l},context_instance = RequestContext(request))
    else:
        transaction.commit()
        
#############################################################
#        DETALLE TRANSFERENCIA DE CASCO
#############################################################

@login_required
@transaction.commit_on_success()
def detalleTC_add(request,idtc):
    if not request.user.has_perm('casco.transferencia'):
        return render_to_response("denegado.html",locals(),context_instance = RequestContext(request))
    
    l=[]
    titulo_form='Transferencia de Cascos' 
    controlador_form='Transferir Cascos'
    descripcion_form='Seleccionar cascos para transferir'
    
    accion_form='detalleTC_add'
    cancelbtn_form='/comerciax/casco/trans/view/'+idtc
    estado="Casco"
    medidas=Producto.objects.all()
 
    tc=Transferencia.objects.get(pk=idtc)
    #cascos=Casco.objects.select_related().filter(estado_actual=Estados.estados["Casco"]).order_by('admincomerciax_producto.descripcion','casco_nro')
    
  
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
                '''
                
                
                detalle=DetalleTransferencia()
                detalle.id_detalletransferencia=uuid4()
                detalle.transf=Transferencia.objects.get(pk=idtc)
                detalle.casco=Casco.objects.get(pk=seleccion[k])
                nro=Casco.objects.get(pk=seleccion[k]).casco_nro
                try:
                    detalle.save()
                except Exception, e:
                    exc_info = e.__str__() # sys.exc_info()[:1]
                    c = exc_info.find("DETAIL:")
                    
                    if c < 0:
                        l=l+["Error Fatal."]
                    else:
                        l=['El casco ' + str(nro) +' ya existe en este documento']
                        c = exc_info[c + 7:]
                        transaction.rollback()
                        return render_to_response('casco/form_seleccion.html', {'estado':estado,'title':titulo_form,'controlador':controlador_form,'accion':accion_form,
                                                     'cancelbtn':cancelbtn_form,'medida':medidas,'nro':tc.transferencia_nro,'form_description':descripcion_form,
                                                     'fecha':tc.doc_transferencia.fecha_doc.strftime("%d/%m/%Y"),'observaciones':tc.doc_transferencia.observaciones,
                                                     'rc_id':idtc,'error2':l},context_instance = RequestContext(request))
                        
                
                Casco.objects.filter(pk=seleccion[k]).update(estado_actual="Transferencia",fecha=Transferencia.objects.get(pk=idtc).doc_transferencia.fecha_doc)
                add_trazabilidad(seleccion[k], idtc, "Transferencia")
                
            k=k+1
        if request.POST.__contains__('submit1'):
            
            #cascos=Casco.objects.select_related().filter(estado_actual=Estados.estados["Casco"]).order_by('admincomerciax_producto.descripcion','casco_nro')
            return render_to_response('casco/form_seleccion.html', {'estado':estado,'title':titulo_form,'controlador':controlador_form,'accion':accion_form,
                                                     'cancelbtn':cancelbtn_form,'medida':medidas,'nro':tc.transferencia_nro,'form_description':descripcion_form,
                                                     'fecha':tc.doc_transferencia.fecha_doc.strftime("%d/%m/%Y"),'observaciones':tc.doc_transferencia.observaciones,
                                                     'rc_id':idtc},context_instance = RequestContext(request))
        else:
            return HttpResponseRedirect('/comerciax/casco/trans/view/' + idtc)
    return render_to_response('casco/form_seleccion.html', {'estado':estado,'title':titulo_form,'medida':medidas,'controlador':controlador_form,'accion':accion_form,
                                                      'cancelbtn':cancelbtn_form, 'nro':tc.transferencia_nro,'form_description':descripcion_form,
                                                      'fecha':tc.doc_transferencia.fecha_doc.strftime("%d/%m/%Y"),'observaciones':tc.doc_transferencia.observaciones,
                                                      'rc_id':idtc},context_instance = RequestContext(request))    


@login_required
def detalleTC_delete(request,idcasco,idtc):
    if not request.user.has_perm('casco.transferencia'):
        return render_to_response("denegado.html",locals(),context_instance = RequestContext(request))
    
    casco=Casco.objects.select_related().get(pk=idcasco)
    nro=casco.casco_nro
    
    if eliminar_detalle_sino(casco.id_casco,idtc):
        DetalleTransferencia.objects.get(casco=idcasco).delete()
        actualiza_traza(idcasco,idtc)
        
        filas = DetalleTransferencia.objects.select_related().filter(transf=idtc).order_by('casco__producto__descripcion','casco__casco_nro')
        
        total_casco=str(filas.count())
            
        elementos_detalle=[]
        id1=''
        k=0
        k2=0
        for a1 in filas:
            if k!=0:
                if id1!=a1.casco.producto.id:
#                    elementos_detalle[k-1]['cantidad'] = elementos_detalle[k-1]['productoid']
                    elementos_detalle[k-1]['cantidad'] = k2
                    k2=0
                    
            elementos_detalle+=[{'total_casco':total_casco,
                                 'id_doc':a1.transf.doc_transferencia.id_doc,'casco_id':a1.casco.id_casco,
                                 'casco_nro':a1.casco.casco_nro,'producto':a1.casco.producto.descripcion,
                                 'productoid':a1.casco.producto.id,'cliente':a1.casco.get_cliente()}]
            k+=1
            id1=a1.casco.producto.id 
            k2+=1
            
        if k!=0:
            elementos_detalle[k-1]['cantidad'] = k2
        return HttpResponse(simplejson.dumps(elementos_detalle),content_type = 'application/javascript; charset=utf8')
    else:
        error2 = "No se puede eliminar el casco " + str(nro) + " ya que su estado ha cambiado "
        return HttpResponse(json.dumps({'error':True, 'message':error2}),mimetype=u'application/json')


#############################################################
#        RECHHAZAR CASCOS POR ERROR DE RECEPCION
#############################################################

@login_required
def get_er_list(request):
    #prepare the params
    try:
        fecha_desde=Fecha_Ver.objects.get()
    except Exception, e:
        fecha_desde=None
    if  fecha_desde == None:  
        querySet = ErrorRecepcion.objects.select_related().all().order_by('-doc_errorrecepcion__fecha_doc')
    else:
        querySet = ErrorRecepcion.objects.select_related().filter(doc_errorrecepcion__fecha_doc__gte=fecha_desde.fecha).order_by('-doc_errorrecepcion__fecha_doc')
    #querySet = querySet.filter(doc__fecha_doc__year=2010)
 
    columnIndexNameMap = {0: '-casco_doc.fecha_doc',1:'doc_errorrecepcion.fecha_doc'}
    #searchableColumns = ['cliente__nombre','recepcioncliente_nro']
    searchableColumns = ['doc_errorrecepcion__fecha_doc']
    #path to template used to generate json
    jsonTemplatePath = 'casco/json/json_er.txt'

    #call to generic function from utils
    return get_datatables_records(request, querySet, columnIndexNameMap, searchableColumns, jsonTemplatePath)


@login_required
def cascoer_index(request):
    return render_to_response('casco/cascoerindex.html',locals(),context_instance = RequestContext(request))


@login_required
@transaction.commit_on_success()
def cascoer_add(request):
    if not request.user.has_perm('casco.errorrecep'):
        return render_to_response("denegado.html",locals(),context_instance = RequestContext(request))
    
    nombre_form='Cascos Rechazados'
    descripcion_form='Rechazar Cascos por Error en Revisión'
    titulo_form='Cascos Rechazados' 
    controlador_form='Cascos Rechazados'
    accion_form='/comerciax/casco/cascoer/add'
    cancelbtn_form='/comerciax/casco/cascoer/index'
    fecha_cierre=Fechacierre.objects.get(almacen='c').fechaminima()
    fecha_maxima=Fechacierre.objects.get(almacen='c').fechamaxima()
    c=None
    l=[]
    if request.method == 'POST':
        form = CascoERForm(request.POST)

        #rajuste = form.cleaned_data['ajuste']
        if form.is_valid():
            doc=Doc()

            fechadoc=form.cleaned_data['fecha']
            doc.fecha_doc=fechadoc
            doc.observaciones=form.cleaned_data['observaciones']
            doc.fecha_operacion=datetime.date.today()
            doc.fecha_doc=fechadoc
            doc.tipo_doc='7'
         
            pk_user=User.objects.get(pk=request.user.id)
            # esto hay que cambiarlo y poner el operador
            pk_doc=uuid4()
            

            doc.id_doc = pk_doc 
            doc.operador=pk_user
            
            
            er=ErrorRecepcion()
            

            er.doc_errorrecepcion=doc
            
            try:

                doc.save()
                er.save() 
 
                return HttpResponseRedirect('/comerciax/casco/cascoer/view/'+pk_doc.__str__())  
            except Exception, e:
                exc_info = e.__str__() # sys.exc_info()[:1]
                c = exc_info.find("DETAIL:")
                
                if c < 0:
                    l=l+["Error Fatal."]
                else:
                    c = exc_info[c + 7:]
                    l=l+[c] 
                                     
                transaction.rollback()
                form = CascoERForm(request.POST)
                return render_to_response('form/form_adddetalle.html',  {'tipocliente':'2','form': form, 'form_name':nombre_form,'form_description':descripcion_form,
                                                                         'accion':accion_form,'titulo':titulo_form,'controlador':controlador_form,
                                                                         'cancelbtn':cancelbtn_form,'fecha_minima':fecha_cierre,'fecha_maxima':fecha_maxima,'error2':l},context_instance = RequestContext(request))
            else:
                transaction.commit()
    else:
        form = CascoERForm(initial={'fecha':fecha_cierre}) 
    return render_to_response('form/form_adddetalle.html',  {'tipocliente':'2','form': form, 'form_name':nombre_form,'form_description':descripcion_form,
                                                             'accion':accion_form,'titulo':titulo_form,'controlador':controlador_form,
                                                             'cancelbtn':cancelbtn_form,'fecha_minima':fecha_cierre,'fecha_maxima':fecha_maxima,'error2':c},context_instance = RequestContext(request))

@login_required
@transaction.commit_on_success()
def cascoer_edit(request,ider):
    if not request.user.has_perm('casco.errorrecep'):
        return render_to_response("denegado.html",locals(),context_instance = RequestContext(request))
    
    nombre_form='Cascos Rechazados'
    descripcion_form='Rechazar Cascos por Error en Revisión'
    titulo_form='Cascos Rechazados' 
    controlador_form='Cascos Rechazados'
    accion_form='/comerciax/casco/cascoer/edit/'+ider+'/'
    cancelbtn_form='/comerciax/casco/cascoer/view/'+ider+'/'
    fecha_cierre=Fechacierre.objects.get(almacen='c').fechaminima()
    fecha_maxima=Fechacierre.objects.get(almacen='c').fechamaxima()
    c=None
    l=[]
        
    if request.method == 'POST':
        form = CascoERForm(request.POST)

        #rajuste = form.cleaned_data['ajuste']
        if form.is_valid():
            er=ErrorRecepcion.objects.get(pk=ider)
            object_doc=Doc.objects.get(pk=ider)
            
            object_doc.fecha_doc=form.cleaned_data['fecha']
            object_doc.observaciones=form.cleaned_data['observaciones']
            object_doc.fecha_operacion=datetime.date.today()
         
            pk_user=User.objects.get(pk=request.user.id)

            object_doc.operador=pk_user
         
            #RecepcionCliente.objects.create(doc_recepcioncliente=obj_doc,recepcioncliente_nro=nro,recepcioncliente_ajuste=ajuste,cliente=obj_cliente)
            try:
                object_doc.save()
                er.save() 
 
                return HttpResponseRedirect('/comerciax/casco/cascoer/view/'+ider)  

            except Exception, e:
                exc_info = e.__str__() # sys.exc_info()[:1]
                c = exc_info.find("DETAIL:")
                
                if c < 0:
                    l=l+["Error Fatal."]
                else:
                    c = exc_info[c + 7:]
                    l=l+[c]
                    
                transaction.rollback()
                form = CascoERForm(request.POST)
                return render_to_response('form/form_adddetalle.html',  {'tipocliente':'2','form': form, 'form_name':nombre_form,'form_description':descripcion_form,
                                                                         'accion':accion_form,'titulo':titulo_form,'controlador':controlador_form,
                                                                         'cancelbtn':cancelbtn_form,'fecha_minima':fecha_cierre,'fecha_maxima':fecha_maxima,'error2':l},context_instance = RequestContext(request))
            else:
                transaction.commit()     
    else:
        er = ErrorRecepcion.objects.select_related().get(pk=ider)
        form = CascoERForm(initial={'fecha':er.doc_errorrecepcion.fecha_doc,
                                             'observaciones':er.doc_errorrecepcion.observaciones})
    return render_to_response('form/form_edit.html',  {'tipocliente':'2','form': form, 'form_name':nombre_form,'form_description':descripcion_form,'accion':accion_form,
                                                       'titulo':titulo_form,'controlador':controlador_form,'cancelbtn':cancelbtn_form,
                                                       'fecha_minima':fecha_cierre,'fecha_maxima':fecha_maxima},context_instance = RequestContext(request))

@login_required
def cascoer_view(request,ider):
    if not request.user.has_perm('casco.errorrecep'):
        return render_to_response("denegado.html",locals(),context_instance = RequestContext(request))
    
    l=[]
    er = ErrorRecepcion.objects.select_related().get(pk=ider)
    rc_fecha=er.doc_errorrecepcion.fecha_doc.strftime("%d/%m/%Y")
    
    rc_observaciones=er.doc_errorrecepcion.observaciones
    filas = Detalle_ER.objects.select_related().filter(errro_revision=ider).order_by('casco__producto__descripcion','casco__casco_nro')
    #for a in filas:
    #    aa=a.causarechazo_er.causa
    adiciono=True
    if er.procesado==True:
        editar=False
        adiciono=False
        
    else:
        editar=editar_documento(filas, ider)   
        
    elementos_detalle=[]
    id1=''
    k=0
    k2=0
    for a1 in filas:
        if k!=0:
            if id1!=a1.casco.producto.id:
                elementos_detalle[k-1]['cantidad'] = k2
                k2=0
        causa=CausaRechazo_ER.objects.filter(detalle_er=a1.id_detalleer)
        causa_rec=''
        for ss in causa:
            causa_rec=ss.causa.descripcion
        elementos_detalle+=[{'cliente':a1.casco.get_cliente,'casco_id':a1.casco.id_casco,
                             'casco_nro':a1.casco.casco_nro,'producto':a1.casco.producto,
                             'productoid':a1.casco.producto.id,'causa':causa_rec}]
        k+=1
        k2+=1
        id1=a1.casco.producto.id  
    if k!=0:
        elementos_detalle[k-1]['cantidad'] = k2
    return render_to_response('casco/viewcascoer.html',{'total_casco':k,'fecha':rc_fecha,'observaciones':rc_observaciones,
                                                              'rc_id':ider,'elementos_detalle':elementos_detalle, 'edito':editar,
                                                              'adiciono':adiciono,'error2':l},context_instance = RequestContext(request))

@login_required
@transaction.commit_on_success()
def cascoer_del(request,ider):
    if not request.user.has_perm('casco.errorrecep'):
        return render_to_response("denegado.html",locals(),context_instance = RequestContext(request))
    
    try:
        filas = Detalle_ER.objects.filter(errro_revision=ider)
        for canti in filas:
            actualiza_traza(canti.casco.id_casco,ider)
        
        Doc.objects.select_related().get(pk=ider).delete()
        return HttpResponseRedirect('/comerciax/casco/cascoer/index')
    except Exception :
        transaction.rollback()
        l = ['Error al eliminar el documento']
        er = ErrorRecepcion.objects.select_related().get(pk=ider)
        rc_fecha=er.doc_errorrecepcion.fecha_doc.strftime("%d/%m/%Y")


        editar=1
        rc_observaciones=er.doc_errorrecepcion.observaciones
        filas = Detalle_ER.objects.select_related().filter(errro_revision=ider).order_by('casco_casco.casco_nro')

        return render_to_response('casco/viewcascoer.html',{'fecha':rc_fecha,'observaciones':rc_observaciones,'rc_id':ider,
                                                            'elementos_detalle':filas, 'edito':editar,'error2':l},context_instance = RequestContext(request))

    else:
        transaction.commit()

#############################################################
#        DETALLE DE CASCOS RECHAZADOS POR ERROR DE RECEPC.
#############################################################

@login_required
@transaction.commit_on_success()
def detalleER_add(request,ider):
    if not request.user.has_perm('casco.errorrecep'):
        return render_to_response("denegado.html",locals(),context_instance = RequestContext(request))
    
    l=[]
    titulo_form='Cacos Rechazados por error en Revisión' 
    controlador_form='Cascos Rechazados'
    descripcion_form='Seleccionar los cascos a rechazar'
    accion_form='detalleER_add'
    cancelbtn_form='/comerciax/casco/cascoer/view/'+ider
    estado="Casco"
    medidas=Producto.objects.all()
    
    
    er=ErrorRecepcion.objects.get(pk=ider)
    #cascos=Casco.objects.select_related().filter(estado_actual=Estados.estados["Casco"]).order_by('admincomerciax_producto.descripcion','casco_nro')
    mostrarcausa=True
    causas=CausasRechazo.objects.all()
    if request.method == 'POST':
        seleccion=request.POST.keys()
        k=0
        causa=request.POST["causa"]
        while True:
            if k==seleccion.__len__():
                break
            casco=Casco.objects.filter(pk=seleccion[k])
            
            if casco.count()!=0:

                '''
                Los selecionados los cambio de estado, agregar a detalle del documento y actualizar trazabilidad
                '''
                
                
                detalle=Detalle_ER()
                pk_detalle=uuid4()
                detalle.id_detalleer=pk_detalle
                detalle.errro_revision=ErrorRecepcion.objects.get(pk=ider)
                detalle.casco=Casco.objects.get(pk=seleccion[k])
                nro=Casco.objects.get(pk=seleccion[k]).casco_nro
                #detalle.causa=CausasRechazo.objects.get(pk=causa)
                try:
                    detalle.save()
                except Exception, e:
                    exc_info = e.__str__() # sys.exc_info()[:1]
                    c = exc_info.find("DETAIL:")
                    
                    if c < 0:
                        l=l+["Error Fatal."]
                    else:
                        l=['El casco ' + str(nro) +' ya existe en este documento']
                        c = exc_info[c + 7:]
                        transaction.rollback()
                        return render_to_response('casco/form_seleccion.html',{'medida':medidas,'estado':estado,'title':titulo_form,'controlador':controlador_form,'accion':accion_form,
                                                      'cancelbtn':cancelbtn_form, 'form_description':descripcion_form,
                                                      'fecha':er.doc_errorrecepcion.fecha_doc.strftime("%d/%m/%Y"),'observaciones':er.doc_errorrecepcion.observaciones,
                                                      'rc_id':ider,'causas_rechazo':causas,'muestra_causa':mostrarcausa,'error2':l},context_instance = RequestContext(request))
                        
                
                Casco.objects.filter(pk=seleccion[k]).update(estado_actual="ER",fecha=ErrorRecepcion.objects.get(pk=ider).doc_errorrecepcion.fecha_doc)
                add_trazabilidad(seleccion[k], ider, "ER")
                
                if causa.__len__()!=0:
                    causaer=CausaRechazo_ER()
                    obj_detalle = Detalle_ER.objects.get(pk = pk_detalle)
                    causaer.detalle_er=obj_detalle
                    causaer.causa=CausasRechazo.objects.get(pk=causa)
                    causaer.save()
            k=k+1
        
            
        
        if request.POST.__contains__('submit1'):
            return render_to_response('casco/form_seleccion.html',{'medida':medidas,'estado':estado,'title':titulo_form,'controlador':controlador_form,'accion':accion_form,
                                                      'cancelbtn':cancelbtn_form, 'form_description':descripcion_form,
                                                      'fecha':er.doc_errorrecepcion.fecha_doc.strftime("%d/%m/%Y"),'observaciones':er.doc_errorrecepcion.observaciones,
                                                      'rc_id':ider,'causas_rechazo':causas,'muestra_causa':mostrarcausa,'error2':l},context_instance = RequestContext(request))
        else:
            return HttpResponseRedirect('/comerciax/casco/cascoer/view/' + ider)
    
    return render_to_response('casco/form_seleccion.html', {'medida':medidas,'estado':estado,'title':titulo_form,'controlador':controlador_form,'accion':accion_form,
                                                      'cancelbtn':cancelbtn_form, 'form_description':descripcion_form,
                                                      'fecha':er.doc_errorrecepcion.fecha_doc.strftime("%d/%m/%Y"),'observaciones':er.doc_errorrecepcion.observaciones,
                                                      'rc_id':ider,'causas_rechazo':causas,'muestra_causa':mostrarcausa,'error2':l},context_instance = RequestContext(request))    

@login_required
def detalleER_delete(request,ider,idcasco): 
    if not request.user.has_perm('casco.errorrecep'):
        return render_to_response("denegado.html",locals(),context_instance = RequestContext(request))
    
    casco=Casco.objects.select_related().get(pk=idcasco)
    nro=casco.casco_nro
    
    
    if eliminar_detalle_sino(casco.id_casco,ider):
        Detalle_ER.objects.get(casco=idcasco).delete()
        
        actualiza_traza(idcasco,ider)
        filas = Detalle_ER.objects.select_related().filter(errro_revision=ider).order_by('casco__producto__descripcion','casco__casco_nro')
#        for detalles in filas:
#            casco.delete()

        total_casco=str(filas.count())
            
        elementos_detalle=[]
        id1=''
        k=0
        k2=0
        for a1 in filas:
            idpk=a1.id_detalleer
            if k!=0:
                if id1!=a1.casco.producto.id:
#                    elementos_detalle[k-1]['cantidad'] = elementos_detalle[k-1]['productoid']
                    elementos_detalle[k-1]['cantidad'] = k2
                    k2=0
            
            try:
                causa=a1.causarechazo_er.causa.descripcion  
            except Exception, e:
                causa=''     
            
            elementos_detalle+=[{'total_casco':total_casco,'causa':causa,
                                 'id_doc':a1.errro_revision.doc_errorrecepcion.id_doc,'casco_id':a1.casco.id_casco,
                                 'casco_nro':a1.casco.casco_nro,'producto':a1.casco.producto.descripcion,
                                 'productoid':a1.casco.producto.id,'cliente':a1.casco.get_cliente()}]
            k+=1
            id1=a1.casco.producto.id 
            k2+=1
            
        if k!=0:
            elementos_detalle[k-1]['cantidad'] = k2
        return HttpResponse(simplejson.dumps(elementos_detalle),content_type = 'application/javascript; charset=utf8')
    else:
        error2 = "No se puede eliminar el casco " + str(nro) + " ya que su estado ha cambiado "
        return HttpResponse(json.dumps({'error':True, 'message':error2}),mimetype=u'application/json')
    

@login_required
@transaction.commit_on_success()
def detalleER_edit(request,idcasco,ider):
    if not request.user.has_perm('casco.errorrecep'):
        return render_to_response("denegado.html",locals(),context_instance = RequestContext(request))
    
    c=None
    l=[]
    
    nombre_form='Cascos Rechazados'
    descripcion_form='Rechazar Cascos por Error en Revisión'
    titulo_form='Cascos Rechazados' 
    controlador_form='Cascos Rechazados'
    accion_form='detalleER_edit/' + ider +'/' +idcasco
    cancelbtn_form='/comerciax/casco/cascoer/view/' + ider +'/'
    
    
    if request.method == 'POST':
        form = DetalleERForm(request.POST)
        
        if form.is_valid():
            er=Detalle_ER.objects.get(casco=idcasco,errro_revision=ider)
            
            causa=CausasRechazo.objects.filter(pk = form.data['causa'])
            
            try:
                er.save()
                causarer=CausaRechazo_ER.objects.filter(pk=er.id_detalleer)
                
                if causarer.__len__()==0 and causa.__len__()!=0:
                    '''Se añade la causa '''
                    causarersave=CausaRechazo_ER()
                    causarersave.detalle_er=Detalle_ER.objects.get(pk = er.id_detalleer)
                    causarersave.causa=CausasRechazo.objects.get(pk=causa)
                    causarersave.save()
                elif causarer.__len__()!=0 and causa.__len__()==0:
                    '''Se quita la causa '''
                    CausaRechazo_ER.objects.get(pk = er.id_detalleer).delete()
                else:
                    causarersave=CausaRechazo_ER.objects.get(pk=er.id_detalleer)
                    causarersave.causa=CausasRechazo.objects.get(pk=causa)
                    causarersave.save()
                return cascoer_view(request, ider)
            except Exception, e:
                exc_info = e.__str__() # sys.exc_info()[:1]
                c = exc_info.find("DETAIL:")
                if c < 0:
                    l = l + ["Error Fatal."]
                else:
                    c = exc_info[c + 7:]
                    l=l+[c]
                transaction.rollback()
                form = DetalleERForm(request.POST)
                return render_to_response("form/form_edit.html",{'tipocliente':'2','form':form,'title':titulo_form, 'form_name': nombre_form,'form_description':descripcion_form,'controlador':controlador_form,'accion':accion_form
                                                         , 'cancelbtn':cancelbtn_form,'error2':l},context_instance = RequestContext(request))
            else:
                transaction.commit()
    else:   
        rer =Detalle_ER.objects.select_related().get(casco=idcasco,errro_revision=ider)
        causaer=CausaRechazo_ER.objects.filter(pk=rer.id_detalleer)
        if causaer.__len__()!=0:
            cusarer =CausaRechazo_ER.objects.get(pk=rer.id_detalleer)
            form = DetalleERForm(initial={'nro':rer.casco.casco_nro,'causa':cusarer.causa})
        else:
            form = DetalleERForm(initial={'nro':rer.casco.casco_nro,'causa':CausasRechazo.objects.all()})
        return render_to_response('form/form_edit.html',  {'tipocliente':'2','form': form, 'form_name':nombre_form,'form_description':descripcion_form,'accion':accion_form,'titulo':titulo_form,'controlador':controlador_form,'cancelbtn':cancelbtn_form},context_instance = RequestContext(request))
    return cascoer_view(request, ider)  



#############################################################
#        DEVOLUCION DE CASCOS A CLIENTES
##################################################################
@login_required
def get_dcc_list(request):
    #prepare the params
    try:
        fecha_desde=Fecha_Ver.objects.get()
    except Exception, e:
        fecha_desde=None
    if  fecha_desde == None:  
        querySet = DevolucionCasco.objects.select_related().all().order_by('-doc_devolucion__fecha_doc')
    else:
        querySet = DevolucionCasco.objects.select_related().filter(doc_devolucion__fecha_doc__gte=fecha_desde.fecha).order_by('-doc_devolucion__fecha_doc')
    #querySet = querySet.filter(doc__fecha_doc__year=2010)
 
    columnIndexNameMap = {0: '-casco_doc.fecha_doc',1: 'devolucion_nro',2:'casco_doc.fecha_doc',3:'admincomerciax_cliente.nombre'}
    #searchableColumns = ['cliente__nombre','recepcioncliente_nro']
    searchableColumns = ['devolucion_nro','doc_devolucion__fecha_doc','cliente__nombre']
    #path to template used to generate json
    jsonTemplatePath = 'casco/json/json_dcc.txt'

    #call to generic function from utils
    return get_datatables_records(request, querySet, columnIndexNameMap, searchableColumns, jsonTemplatePath)

@login_required
def cascodcc_index(request):
    if not request.user.has_perm('casco.devolucion'):
        return render_to_response("denegado.html",locals(),context_instance = RequestContext(request))
    
    return render_to_response('casco/cascodccindex.html',locals(),context_instance = RequestContext(request))

@login_required
@transaction.commit_on_success()
def cascodcc_add(request):
    if not request.user.has_perm('casco.devolucion'):
        return render_to_response("denegado.html",locals(),context_instance = RequestContext(request))
    
    nombre_form='Devolución de Cascos'
    descripcion_form='Devolución de Cascos'
    titulo_form='Devolución de Cascos' 
    controlador_form='Devolución de Cascos'
    accion_form='/comerciax/casco/cascodcc/add'
    cancelbtn_form='/comerciax/casco/cascodcc/index'
    fecha_cierre=Fechacierre.objects.get(almacen='c').fechaminima()
    fecha_maxima=Fechacierre.objects.get(almacen='c').fechamaxima()
    c=None
    l=[]
    if request.method == 'POST':
        form = CascoDCCForm(request.POST)

        #rajuste = form.cleaned_data['ajuste']
        if form.is_valid():
            doc=Doc()

            fechadoc=form.cleaned_data['fecha']
            doc.fecha_doc=fechadoc
            doc.observaciones=form.cleaned_data['observaciones']
            doc.fecha_operacion=datetime.date.today()
            doc.fecha_doc=fechadoc
            doc.tipo_doc='19'
         
            pk_user=User.objects.get(pk=request.user.id)
            # esto hay que cambiarlo y poner el operador
            pk_doc=uuid4()
            

            doc.id_doc = pk_doc 
            doc.operador=pk_user
            
            
            dcc=DevolucionCasco()
            
            dcc_nro=form.cleaned_data['nro']
            dcc.devolucion_nro=dcc_nro
            dcc.doc_devolucion=doc
            dcc.cliente=Cliente.objects.get(pk = form.data['cliente'])
            recep=DevolucionCasco.objects.filter(devolucion_nro=dcc_nro)
            if recep.__len__()!=0:
                for a1 in recep:
                    if a1.doc_devolucion.fecha_doc.year == fechadoc.year:
                        l=['Número de documento existente']
                        return render_to_response('form/form_adddetalle.html',  {'tipocliente':'0','form': form, 'form_name':nombre_form,'form_description':descripcion_form,
                                                                                 'accion':accion_form,'titulo':titulo_form,'controlador':controlador_form,
                                                                                 'cancelbtn':cancelbtn_form,'fecha_minima':fecha_cierre,'fecha_maxima':fecha_maxima,'error2':l},context_instance = RequestContext(request))

            try:

                doc.save()
                dcc.save() 
                return HttpResponseRedirect('/comerciax/casco/cascodcc/view/'+pk_doc.__str__())  
            except Exception, e:
                exc_info = e.__str__() # sys.exc_info()[:1]
                c = exc_info.find("DETAIL:")
                
                if c < 0:
                    l=l+["Error Fatal."]
                else:
                    c = exc_info[c + 7:]
                    l=l+[c] 
                                     
                transaction.rollback()
                form = CascoDCCForm(request.POST)
                return render_to_response('form/form_adddetalle.html',  {'tipocliente':'2','form': form, 'form_name':nombre_form,'form_description':descripcion_form,
                                                                         'accion':accion_form,'titulo':titulo_form,'controlador':controlador_form,
                                                                         'cancelbtn':cancelbtn_form,'fecha_minima':fecha_cierre,'fecha_maxima':fecha_maxima,'error2':l},context_instance = RequestContext(request))
            else:
                transaction.commit()
    else:
        form = CascoDCCForm(initial={'fecha':fecha_cierre}) 
    return render_to_response('form/form_adddetalle.html',  {'tipocliente':'2','form': form, 'form_name':nombre_form,'form_description':descripcion_form,
                                                             'accion':accion_form,'titulo':titulo_form,'controlador':controlador_form,
                                                             'cancelbtn':cancelbtn_form,'fecha_minima':fecha_cierre,'fecha_maxima':fecha_maxima,'error2':c},context_instance = RequestContext(request))


@login_required
@transaction.commit_on_success()
def cascodcc_edit(request,iddcc):
    if not request.user.has_perm('casco.devolucion'):
        return render_to_response("denegado.html",locals(),context_instance = RequestContext(request))
    
    nombre_form='Devolución de Cascos'
    descripcion_form='Devolución de Cascos'
    titulo_form='Devolución de Cascos' 
    controlador_form='Devolución de Cascos'
    accion_form='/comerciax/casco/cascodcc/edit/'+iddcc+'/'
    cancelbtn_form='/comerciax/casco/cascodcc/view/'+iddcc+'/'
    fecha_cierre=Fechacierre.objects.get(almacen='c').fechaminima()
    fecha_maxima=Fechacierre.objects.get(almacen='c').fechamaxima()
    c=None
    l=[]
        
    if request.method == 'POST':
        form = CascoDCCForm(request.POST)

        #rajuste = form.cleaned_data['ajuste']
        if form.is_valid():
            dcc=DevolucionCasco.objects.get(pk=iddcc)
            object_doc=Doc.objects.get(pk=iddcc)
            
            object_doc.fecha_doc=form.cleaned_data['fecha']
            fechadoc1=form.cleaned_data['fecha']
            object_doc.observaciones=form.cleaned_data['observaciones']
            object_doc.fecha_operacion=datetime.date.today()
         
            pk_user=User.objects.get(pk=request.user.id)
            # esto hay que cambiarlo y poner el operador
            #pk_doc=uuid4()
            

            object_doc.operador=pk_user
            
            dcc.devolucion_nro=form.cleaned_data['nro']
            dcc_nro1=form.cleaned_data['nro']
            
            dcc.cliente=Cliente.objects.get(pk = form.data['cliente'])
            recep=DevolucionCasco.objects.filter(devolucion_nro=dcc_nro1)
            if recep.__len__()!=0:
                for a1 in recep:
                    if a1.doc_devolucion.fecha_doc.year == fechadoc1.year and a1.pk!=iddcc:
                        l=['Número de documento existente']
                        return render_to_response('form/form_adddetalle.html',  {'tipocliente':'0','form': form, 'form_name':nombre_form,'form_description':descripcion_form,
                                                                                 'accion':accion_form,'titulo':titulo_form,'controlador':controlador_form,
                                                                                 'cancelbtn':cancelbtn_form,'error2':l,'fecha_minima':fecha_cierre,'fecha_maxima':fecha_maxima},context_instance = RequestContext(request))        
         
            #RecepcionCliente.objects.create(doc_recepcioncliente=obj_doc,recepcioncliente_nro=nro,recepcioncliente_ajuste=ajuste,cliente=obj_cliente)
            try:
                object_doc.save()
                dcc.save() 
 
                return HttpResponseRedirect('/comerciax/casco/cascodcc/view/'+iddcc)  

            except Exception, e:
                exc_info = e.__str__() # sys.exc_info()[:1]
                c = exc_info.find("DETAIL:")
                
                if c < 0:
                    l=l+["Error Fatal."]
                else:
                    c = exc_info[c + 7:]
                    l=l+[c]
                    
                transaction.rollback()
                form = CascoDCCForm(request.POST)
                return render_to_response('form/form_adddetalle.html',  {'tipocliente':'2','form': form, 'form_name':nombre_form,'form_description':descripcion_form,
                                                                         'accion':accion_form,'titulo':titulo_form,'controlador':controlador_form,
                                                                         'cancelbtn':cancelbtn_form,'fecha_minima':fecha_cierre,'fecha_maxima':fecha_maxima,'error2':l},context_instance = RequestContext(request))
            else:
                transaction.commit()     
    else:
        dcc = DevolucionCasco.objects.select_related().get(pk=iddcc)
        form = CascoDCCForm(initial={'nro':dcc.devolucion_nro,'fecha':dcc.doc_devolucion.fecha_doc,
                                             'observaciones':dcc.doc_devolucion.observaciones,'cliente':dcc.cliente})
    return render_to_response('form/form_edit.html',  {'tipocliente':'2','form': form, 'form_name':nombre_form,'form_description':descripcion_form,'accion':accion_form,'titulo':titulo_form,
                                                       'controlador':controlador_form,'cancelbtn':cancelbtn_form,'fecha_minima':fecha_cierre,'fecha_maxima':fecha_maxima},context_instance = RequestContext(request))


@login_required
def cascodcc_view(request,iddcc):
    if not request.user.has_perm('casco.devolucion'):
        return render_to_response("denegado.html",locals(),context_instance = RequestContext(request))
    
    l=[]
    dcc = DevolucionCasco.objects.select_related().get(pk=iddcc)
    dcc_fecha=dcc.doc_devolucion.fecha_doc.strftime("%d/%m/%Y")
    dcc_nro=dcc.devolucion_nro
    dcc_observaciones=dcc.doc_devolucion.observaciones
    dcc_cliente=dcc.cliente.nombre
    id_cliente=dcc.cliente.id
    
    filas = DetalleDCC.objects.select_related().filter(devolucion=iddcc).order_by('casco__producto__descripcion','casco__casco_nro')
    adiciono=True
    if dcc.procesado==True:
        editar=False
        adiciono=False
    else:
        editar=editar_documento(filas, iddcc)
        
    elementos_detalle=[]
    id1=''
    k=0
    k2=0
    for a1 in filas:
        if k!=0:
            if id1!=a1.casco.producto.id:
                elementos_detalle[k-1]['cantidad'] = k2
                k2=0
        elementos_detalle+=[{'cliente':a1.casco.get_cliente,'casco_id':a1.casco.id_casco,
                             'casco_nro':a1.casco.casco_nro,'producto':a1.casco.producto,
                             'productoid':a1.casco.producto.id}]
        k+=1
        k2+=1
        id1=a1.casco.producto.id  
    if k!=0:
        elementos_detalle[k-1]['cantidad'] = k2
    return render_to_response('casco/viewcascodcc.html',{'id_cliente':id_cliente,'dcc_cliente':dcc_cliente,'total_casco':k,'dcc_nro':dcc_nro,'fecha':dcc_fecha,'observaciones':dcc_observaciones,
                                                              'dcc_id':iddcc,'elementos_detalle':elementos_detalle, 'edito':editar,
                                                              'adiciono':adiciono,'error2':l},context_instance = RequestContext(request))

@login_required
@transaction.commit_on_success()
def cascodcc_del(request,iddcc):
    if not request.user.has_perm('casco.devolucion'):
        return render_to_response("denegado.html",locals(),context_instance = RequestContext(request))
    try:
        filas = DetalleDCC.objects.filter(devolucion=iddcc)
        for canti in filas:
            actualiza_traza(canti.casco.id_casco,iddcc)
        
        Doc.objects.select_related().get(pk=iddcc).delete()

        
        return HttpResponseRedirect('/comerciax/casco/cascodcc/index')
    except Exception :
        transaction.rollback()
        l = ['Error al eliminar el documento']
        dcc = EntregaRechazado.objects.select_related().get(pk=iddcc)
        dcc_fecha=dcc.doc_devolucion.fecha_doc.strftime("%d/%m/%Y")

        dcc_nro=dcc.entregarechazado_nro
        editar=1
        dcc_observaciones=dcc.doc_devolucion.observaciones
        filas = DetalleDCC.objects.select_related().filter(devolucion=iddcc).order_by('casco_casco.casco_nro')

        return render_to_response('casco/viewcascodcc.html',{'dcc_nro':dcc_nro,'fecha':dcc_fecha,'observaciones':dcc_observaciones,'rc_id':iddcc,'elementos_detalle':filas, 'edito':editar,'error2':l},context_instance = RequestContext(request))

    else:
        transaction.commit()
        
#############################################################
#        DETALLE ENTREGA DE CASCOS RECHAZADOS
#############################################################

@login_required
@transaction.commit_on_success()
def detalleDCC_add(request,iddcc,idcliente):
    if not request.user.has_perm('casco.devolucion'):
        return render_to_response("denegado.html",locals(),context_instance = RequestContext(request))
    
    titulo_form='Devolución de Casco' 
    controlador_form='Devolución de Casco'
    descripcion_form='Seleccionar cascos a entregar'
    
    accion_form='detalleDCC_add'
    cancelbtn_form='/comerciax/casco/cascodcc/view/'+iddcc
    cc=DevolucionCasco.objects.get(pk=iddcc)
    estado="Casco"
    l=[]
    
    medidas=Producto.objects.all()
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
                '''
                
                detalle=DetalleDCC()
                detalle.id_detalle=uuid4()
                detalle.devolucion=DevolucionCasco.objects.get(pk=iddcc)
                detalle.casco=Casco.objects.get(pk=seleccion[k])
                nro=Casco.objects.get(pk=seleccion[k]).casco_nro
                try:
                    detalle.save()
                except Exception, e:
                    exc_info = e.__str__() # sys.exc_info()[:1]
                    c = exc_info.find("DETAIL:")
                    
                    if c < 0:
                        l=l+["Error Fatal."]
                    else:
                        l=['El casco ' + str(nro) +' ya existe en este documento']
                        c = exc_info[c + 7:]
                        transaction.rollback()
                        return render_to_response('casco/form_seleccion.html', {'estado':estado,'entrgarecha':False,'colum3':"","colCli":False,
                                                    'estado':estado,'title':titulo_form,
                                                    'controlador':controlador_form,'accion':accion_form,
                                                     'cancelbtn':cancelbtn_form, 'nro':cc.entregarechazado_nro,
                                                     'form_description':descripcion_form,'medidadev':medidas,
                                                     'fecha':cc.doc_entregarechazado.fecha_doc.strftime("%d/%m/%Y"),
                                                     'observaciones':cc.doc_entregarechazado.observaciones,
                                                     'rc_id':iddcc,'error2':l},context_instance = RequestContext(request))

                        
                Casco.objects.filter(pk=seleccion[k]).update(estado_actual="DCC",fecha=DevolucionCasco.objects.get(pk=iddcc).doc_devolucion.fecha_doc)
                add_trazabilidad(seleccion[k], iddcc,"DCC")
                
            k=k+1
        if request.POST.__contains__('submit1'):
            medidas=Producto.objects.all()
            return render_to_response('casco/form_seleccion.html', {'estado':estado,'title':titulo_form,'controlador':controlador_form,'accion':accion_form,
                                                     'cancelbtn':cancelbtn_form, 'nro':cc.devolucion_nro,'form_description':descripcion_form,"colCli":True,
                                                     'fecha':cc.doc_devolucion.fecha_doc.strftime("%d/%m/%Y"),'observaciones':cc.doc_devolucion.observaciones,
                                                     'rc_id':iddcc,'medidadev':medidas,'id_cliente':idcliente},context_instance = RequestContext(request))
        else:
            return HttpResponseRedirect('/comerciax/casco/cascodcc/view/' + iddcc)
        
    return render_to_response('casco/form_seleccion.html', {'estado':estado,'title':titulo_form,'controlador':controlador_form,'accion':accion_form,
                                                      'cancelbtn':cancelbtn_form,'nro':cc.devolucion_nro,'form_description':descripcion_form,
                                                      'fecha':cc.doc_devolucion.fecha_doc.strftime("%d/%m/%Y"),'observaciones':cc.doc_devolucion.observaciones,
                                                      'rc_id':iddcc,'medidadev':medidas,'id_cliente':idcliente},context_instance = RequestContext(request))    


@login_required
def detalleDCC_delete(request,iddcc,idcasco):
    if not request.user.has_perm('casco.devolucion'):
        return render_to_response("denegado.html",locals(),context_instance = RequestContext(request))
    
    casco=Casco.objects.select_related().get(pk=idcasco)
    nro=casco.casco_nro
    
    if eliminar_detalle_sino(idcasco,iddcc):
        DetalleDCC.objects.select_related().filter(devolucion=iddcc,casco__id_casco=idcasco).delete()
        actualiza_traza(idcasco,iddcc)
        filas = DetalleDCC.objects.select_related().filter(devolucion=iddcc).order_by('casco__producto__descripcion','casco__casco_nro')
#        cantidades=DetalleRP.objects.filter(rp=idrp).values("casco__producto__id").annotate(Count('casco__producto__id')) 
        total_casco=str(filas.count())
        elementos_detalle=[]
        id1=''
        k=0
        k2=0
        for a1 in filas:
            if k!=0:
                if id1!=a1.casco.producto.id:
                    elementos_detalle[k-1]['cantidad']=k2
                    k2=0
            elementos_detalle+=[{'total_casco':total_casco,
                                 'id_doc':a1.devolucion.doc_devolucion.id_doc,
                                 'casco_id':a1.casco.id_casco,
                                 'casco_nro':a1.casco.casco_nro,
                                 'producto':a1.casco.producto.descripcion,
                                 'productoid':a1.casco.producto.id}]
            k+=1
            k2+=1
            id1=a1.casco.producto.id 
        if k!=0: 
            elementos_detalle[k-1]['cantidad']=k2
        return HttpResponse(simplejson.dumps(elementos_detalle),content_type = 'application/javascript; charset=utf8')
    else:
        error2 = "No se puede eliminar el casco " + str(nro) + " ya que su estado ha cambiado"
        return HttpResponse(json.dumps({'error':True, 'message':error2}),mimetype=u'application/json')
        #return cascocr_view(request, idcr,error2)
        
########################################################
#        ENTREGA DE CASCOS RECHAZADOS
#############################################################
@login_required
def get_cr_list(request):
    #prepare the params
    try:
        fecha_desde=Fecha_Ver.objects.get()
    except Exception, e:
        fecha_desde=None
    if  fecha_desde == None:  
        querySet = EntregaRechazado.objects.select_related().all().order_by('-doc_entregarechazado__fecha_doc')
    else:
        querySet = EntregaRechazado.objects.select_related().filter(doc_entregarechazado__fecha_doc__gte=fecha_desde.fecha).order_by('-doc_entregarechazado__fecha_doc')
    #querySet = querySet.filter(doc__fecha_doc__year=2010)
 
    columnIndexNameMap = {0: '-casco_doc.fecha_doc',1: 'entregarechazado_nro',2:'casco_doc.fecha_doc',3:'admincomerciax_cliente.nombre'}
    #searchableColumns = ['cliente__nombre','recepcioncliente_nro']
    searchableColumns = ['entregarechazado_nro','doc_entregarechazado__fecha_doc','cliente__nombre']
    #path to template used to generate json
    jsonTemplatePath = 'casco/json/json_cr.txt'

    #call to generic function from utils
    return get_datatables_records(request, querySet, columnIndexNameMap, searchableColumns, jsonTemplatePath)

@login_required
def cascocr_index(request):
    if not request.user.has_perm('casco.entregrech'):
        return render_to_response("denegado.html",locals(),context_instance = RequestContext(request))
    
    return render_to_response('casco/cascocrindex.html',locals(),context_instance = RequestContext(request))


@login_required
@transaction.commit_on_success()
def cascocr_add(request):
    if not request.user.has_perm('casco.entregrech'):
        return render_to_response("denegado.html",locals(),context_instance = RequestContext(request))
    
    nombre_form='Entrega de Cascos'
    descripcion_form='Entrega de Cascos Rechazados'
    titulo_form='Entrega de Cascos' 
    controlador_form='Entregar Rechazados'
    accion_form='/comerciax/casco/cascocr/add'
    cancelbtn_form='/comerciax/casco/cascocr/index'
    fecha_cierre=Fechacierre.objects.get(almacen='c').fechaminima()
    fecha_maxima=Fechacierre.objects.get(almacen='c').fechamaxima()
    c=None
    l=[]
    if request.method == 'POST':
        form = CascoCRForm(request.POST)

        #rajuste = form.cleaned_data['ajuste']
        if form.is_valid():
            doc=Doc()

            fechadoc=form.cleaned_data['fecha']
            doc.fecha_doc=fechadoc
            doc.observaciones=form.cleaned_data['observaciones']
            doc.fecha_operacion=datetime.date.today()
            doc.fecha_doc=fechadoc
            doc.tipo_doc='8'
         
            pk_user=User.objects.get(pk=request.user.id)
            # esto hay que cambiarlo y poner el operador
            pk_doc=uuid4()
            

            doc.id_doc = pk_doc 
            doc.operador=pk_user
            
            
            cr=EntregaRechazado()
            
            cr_nro=form.cleaned_data['nro']
            cr.entregarechazado_nro=cr_nro
            cr.doc_entregarechazado=doc
            cr.cliente=Cliente.objects.get(pk = form.data['cliente'])
            recep=EntregaRechazado.objects.filter(entregarechazado_nro=cr_nro)
            if recep.__len__()!=0:
                for a1 in recep:
                    if a1.doc_entregarechazado.fecha_doc.year == fechadoc.year:
                        l=['Número de documento existente']
                        return render_to_response('form/form_adddetalle.html',  {'tipocliente':'0','form': form, 'form_name':nombre_form,'form_description':descripcion_form,
                                                                                 'accion':accion_form,'titulo':titulo_form,'controlador':controlador_form,
                                                                                 'cancelbtn':cancelbtn_form,'fecha_minima':fecha_cierre,'fecha_maxima':fecha_maxima,'error2':l},context_instance = RequestContext(request))

            try:

                doc.save()
                cr.save() 
                return HttpResponseRedirect('/comerciax/casco/cascocr/view/'+pk_doc.__str__())  
            except Exception, e:
                exc_info = e.__str__() # sys.exc_info()[:1]
                c = exc_info.find("DETAIL:")
                
                if c < 0:
                    l=l+["Error Fatal."]
                else:
                    c = exc_info[c + 7:]
                    l=l+[c] 
                                     
                transaction.rollback()
                form = CascoCRForm(request.POST)
                return render_to_response('form/form_adddetalle.html',  {'tipocliente':'2','form': form, 'form_name':nombre_form,'form_description':descripcion_form,
                                                                         'accion':accion_form,'titulo':titulo_form,'controlador':controlador_form,
                                                                         'cancelbtn':cancelbtn_form,'fecha_minima':fecha_cierre,'fecha_maxima':fecha_maxima,'error2':l},context_instance = RequestContext(request))
            else:
                transaction.commit()
    else:
        form = CascoCRForm(initial={'fecha':fecha_cierre}) 
    return render_to_response('form/form_adddetalle.html',  {'tipocliente':'2','form': form, 'form_name':nombre_form,'form_description':descripcion_form,
                                                             'accion':accion_form,'titulo':titulo_form,'controlador':controlador_form,
                                                             'cancelbtn':cancelbtn_form,'fecha_minima':fecha_cierre,'fecha_maxima':fecha_maxima,'error2':c},context_instance = RequestContext(request))


@login_required
@transaction.commit_on_success()
def cascocr_edit(request,idcr):
    if not request.user.has_perm('casco.entregrech'):
        return render_to_response("denegado.html",locals(),context_instance = RequestContext(request))
    
    nombre_form='Cascos a Producción'
    descripcion_form='Entrega de Casco a Producción'
    titulo_form='Cascos a Producción' 
    controlador_form='Cascos a Producción'
    accion_form='/comerciax/casco/cascocr/edit/'+idcr+'/'
    cancelbtn_form='/comerciax/casco/cascocr/view/'+idcr+'/'
    fecha_cierre=Fechacierre.objects.get(almacen='c').fechaminima()
    fecha_maxima=Fechacierre.objects.get(almacen='c').fechamaxima()
    c=None
    l=[]
        
    if request.method == 'POST':
        form = CascoCRForm(request.POST)

        #rajuste = form.cleaned_data['ajuste']
        if form.is_valid():
            cr=EntregaRechazado.objects.get(pk=idcr)
            object_doc=Doc.objects.get(pk=idcr)
            
            object_doc.fecha_doc=form.cleaned_data['fecha']
            fechadoc1=form.cleaned_data['fecha']
            object_doc.observaciones=form.cleaned_data['observaciones']
            object_doc.fecha_operacion=datetime.date.today()
         
            pk_user=User.objects.get(pk=request.user.id)
            # esto hay que cambiarlo y poner el operador
            #pk_doc=uuid4()
            

            object_doc.operador=pk_user
            
            cr.entregarechazado_nro=form.cleaned_data['nro']
            rc_nro1=form.cleaned_data['nro']
            
            cr.cliente=Cliente.objects.get(pk = form.data['cliente'])
            recep=EntregaRechazado.objects.filter(entregarechazado_nro=rc_nro1)
            if recep.__len__()!=0:
                for a1 in recep:
                    if a1.doc_entregarechazado.fecha_doc.year == fechadoc1.year and a1.pk!=idcr:
                        l=['Número de documento existente']
                        return render_to_response('form/form_adddetalle.html',  {'tipocliente':'0','form': form, 'form_name':nombre_form,'form_description':descripcion_form,
                                                                                 'accion':accion_form,'titulo':titulo_form,'controlador':controlador_form,
                                                                                 'cancelbtn':cancelbtn_form,'error2':l,'fecha_minima':fecha_cierre,'fecha_maxima':fecha_maxima},context_instance = RequestContext(request))        
         
            #RecepcionCliente.objects.create(doc_recepcioncliente=obj_doc,recepcioncliente_nro=nro,recepcioncliente_ajuste=ajuste,cliente=obj_cliente)
            try:
                object_doc.save()
                cr.save() 
 
                return HttpResponseRedirect('/comerciax/casco/cascocr/view/'+idcr)  

            except Exception, e:
                exc_info = e.__str__() # sys.exc_info()[:1]
                c = exc_info.find("DETAIL:")
                
                if c < 0:
                    l=l+["Error Fatal."]
                else:
                    c = exc_info[c + 7:]
                    l=l+[c]
                    
                transaction.rollback()
                form = CascoCRForm(request.POST)
                return render_to_response('form/form_adddetalle.html',  {'tipocliente':'2','form': form, 'form_name':nombre_form,'form_description':descripcion_form,
                                                                         'accion':accion_form,'titulo':titulo_form,'controlador':controlador_form,
                                                                         'cancelbtn':cancelbtn_form,'fecha_minima':fecha_cierre,'fecha_maxima':fecha_maxima,'error2':l},context_instance = RequestContext(request))
            else:
                transaction.commit()     
    else:
        cr = EntregaRechazado.objects.select_related().get(pk=idcr)
        form = CascoCRForm(initial={'nro':cr.entregarechazado_nro,'fecha':cr.doc_entregarechazado.fecha_doc,
                                             'observaciones':cr.doc_entregarechazado.observaciones,'cliente':cr.cliente})
    return render_to_response('form/form_edit.html',  {'tipocliente':'2','form': form, 'form_name':nombre_form,'form_description':descripcion_form,'accion':accion_form,'titulo':titulo_form,
                                                       'controlador':controlador_form,'cancelbtn':cancelbtn_form,'fecha_minima':fecha_cierre,'fecha_maxima':fecha_maxima},context_instance = RequestContext(request))


@login_required
def cascocr_view(request,idcr):
    if not request.user.has_perm('casco.entregrech'):
        return render_to_response("denegado.html",locals(),context_instance = RequestContext(request))
    
    l=[]
    cr = EntregaRechazado.objects.select_related().get(pk=idcr)
    rc_fecha=cr.doc_entregarechazado.fecha_doc.strftime("%d/%m/%Y")
    rc_nro=cr.entregarechazado_nro
    rc_observaciones=cr.doc_entregarechazado.observaciones
    rc_cliente=cr.cliente.nombre
    
    filas = DetalleEntregaRechazado.objects.select_related().filter(erechazado=idcr).order_by('casco__producto__descripcion','casco__casco_nro')
    adiciono=True
    if cr.procesado==True:
        editar=False
        adiciono=False
    else:
        editar=editar_documento(filas, idcr)
        
    elementos_detalle=[]
    id1=''
    k=0
    k2=0
    for a1 in filas:
        if k!=0:
            if id1!=a1.casco.producto.id:
                elementos_detalle[k-1]['cantidad'] = k2
                k2=0
        elementos_detalle+=[{'cliente':a1.casco.get_cliente,'casco_id':a1.casco.id_casco,
                             'casco_nro':a1.casco.casco_nro,'producto':a1.casco.producto,
                             'productoid':a1.casco.producto.id}]
        k+=1
        k2+=1
        id1=a1.casco.producto.id  
    if k!=0:
        elementos_detalle[k-1]['cantidad'] = k2
    return render_to_response('casco/viewcascocr.html',{'rc_cliente':rc_cliente,'total_casco':k,'rc_nro':rc_nro,'fecha':rc_fecha,'observaciones':rc_observaciones,
                                                              'rc_id':idcr,'elementos_detalle':elementos_detalle, 'edito':editar,
                                                              'adiciono':adiciono,'error2':l},context_instance = RequestContext(request))
    
#    return render_to_response('casco/viewcascocr.html',{'rc_cliente':rc_cliente,'rc_nro':rc_nro,'fecha':rc_fecha,'observaciones':rc_observaciones,'rc_id':idcr,
#                                                        'elementos_detalle':filas, 'edito':editar,'adiciono':adiciono, 'error2':l},context_instance = RequestContext(request))

@login_required
@transaction.commit_on_success()
def cascocr_del(request,idcr):
    if not request.user.has_perm('casco.entregrech'):
        return render_to_response("denegado.html",locals(),context_instance = RequestContext(request))
    
    
    try:
        
        filas = DetalleEntregaRechazado.objects.filter(erechazado=idcr)
        for canti in filas:
            actualiza_traza(canti.casco.id_casco,idcr)
        
        Doc.objects.select_related().get(pk=idcr).delete()

        
        return HttpResponseRedirect('/comerciax/casco/cascocr/index')
    except Exception :
        transaction.rollback()
        l = ['Error al eliminar el documento']
        cr = EntregaRechazado.objects.select_related().get(pk=idcr)
        rc_fecha=cr.doc_entregarechazado.fecha_doc.strftime("%d/%m/%Y")

        rc_nro=cr.entregarechazado_nro
        editar=1
        rc_observaciones=cr.doc_entregarechazado.observaciones
        filas = DetalleEntregaRechazado.objects.select_related().filter(erechazado=idcr).order_by('casco_casco.casco_nro')

        return render_to_response('casco/viewcascocr.html',{'rc_nro':rc_nro,'fecha':rc_fecha,'observaciones':rc_observaciones,'rc_id':idcr,'elementos_detalle':filas, 'edito':editar,'error2':l},context_instance = RequestContext(request))

    else:
        
        transaction.commit()

#############################################################
#        DETALLE ENTREGA DE CASCOS RECHAZADOS
#############################################################

@login_required
@transaction.commit_on_success()
def detalleCR_add(request,idcr):
    if not request.user.has_perm('casco.entregrech'):
        return render_to_response("denegado.html",locals(),context_instance = RequestContext(request))
    
    titulo_form='Entregar Cascos Rechazados' 
    controlador_form='Entregar Cascos Rechazados'
    descripcion_form='Seleccionar cascos rechazados a entregar'
    
    accion_form='detalleCR_add'
    cancelbtn_form='/comerciax/casco/cascocr/view/'+idcr
    cc=EntregaRechazado.objects.get(pk=idcr)
    estado="DIP-ER-REE"
    colum3='Causa de Rechazo'
    l=[]
    
#    cascos=DetalleRC.objects.select_related().filter(casco__estado_actual__in=estado).order_by('admincomerciax_producto.descripcion','casco_casco.casco_nro')
    medidas=Producto.objects.all()
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
                '''
                
                detalle=DetalleEntregaRechazado()
                detalle.id_detalleer=uuid4()
                detalle.erechazado=EntregaRechazado.objects.get(pk=idcr)
                detalle.casco=Casco.objects.get(pk=seleccion[k])
                nro=Casco.objects.get(pk=seleccion[k]).casco_nro
                try:
                    detalle.save()
                except Exception, e:
                    exc_info = e.__str__() # sys.exc_info()[:1]
                    c = exc_info.find("DETAIL:")
                    
                    if c < 0:
                        l=l+["Error Fatal."]
                    else:
                        l=['El casco ' + str(nro) +' ya existe en este documento']
                        c = exc_info[c + 7:]
                        transaction.rollback()
                        return render_to_response('casco/form_seleccion.html', {'estado':estado,'entrgarecha':True,'colum3':colum3,"colCli":True,
                                                    'estado':estado,'title':titulo_form,
                                                    'controlador':controlador_form,'accion':accion_form,
                                                     'cancelbtn':cancelbtn_form, 'nro':cc.entregarechazado_nro,
                                                     'form_description':descripcion_form,'medidarecha':medidas,
                                                     'fecha':cc.doc_entregarechazado.fecha_doc.strftime("%d/%m/%Y"),
                                                     'observaciones':cc.doc_entregarechazado.observaciones,
                                                     'rc_id':idcr,'error2':l},context_instance = RequestContext(request))

                        
                Casco.objects.filter(pk=seleccion[k]).update(estado_actual="ECR",fecha=EntregaRechazado.objects.get(pk=idcr).doc_entregarechazado.fecha_doc)
                add_trazabilidad(seleccion[k], idcr,"ECR")
                
            k=k+1
        if request.POST.__contains__('submit1'):
            return render_to_response('casco/form_seleccion.html', {'entrgarecha':True,'colum3':colum3,'estado':estado,'title':titulo_form,'controlador':controlador_form,'accion':accion_form,
                                                     'cancelbtn':cancelbtn_form, 'nro':cc.entregarechazado_nro,'form_description':descripcion_form,"colCli":True,
                                                     'fecha':cc.doc_entregarechazado.fecha_doc.strftime("%d/%m/%Y"),'observaciones':cc.doc_entregarechazado.observaciones,
                                                     'rc_id':idcr,'medidarecha':medidas},context_instance = RequestContext(request))
        else:
            return HttpResponseRedirect('/comerciax/casco/cascocr/view/' + idcr)
        
    return render_to_response('casco/form_seleccion.html', {'entrgarecha':True,'colum3':colum3,'estado':estado,'title':titulo_form,'controlador':controlador_form,'accion':accion_form,
                                                      'cancelbtn':cancelbtn_form,'nro':cc.entregarechazado_nro,'form_description':descripcion_form,"colCli":True,
                                                      'fecha':cc.doc_entregarechazado.fecha_doc.strftime("%d/%m/%Y"),'observaciones':cc.doc_entregarechazado.observaciones,
                                                      'rc_id':idcr,'medidarecha':medidas},context_instance = RequestContext(request))    


@login_required
def detalleCR_delete(request,idcr,idcasco):
    if not request.user.has_perm('casco.entregrech'):
        return render_to_response("denegado.html",locals(),context_instance = RequestContext(request))
    
    casco=Casco.objects.select_related().get(pk=idcasco)
    nro=casco.casco_nro
    
    if eliminar_detalle_sino(casco.id_casco,idcr):
        DetalleEntregaRechazado.objects.get(casco=idcasco).delete()
        actualiza_traza(idcasco,idcr)
        
        filas = DetalleEntregaRechazado.objects.select_related().filter(erechazado=idcr).order_by('casco__producto__descripcion','casco__casco_nro')
        total_casco=str(filas.count())
            
        elementos_detalle=[]
        id1=''
        k=0
        k2=0
        for a1 in filas:
            idpk=a1.id_detalleer
            if k!=0:
                if id1!=a1.casco.producto.id:
                    elementos_detalle[k-1]['cantidad'] = k2
                    k2=0
            try:
                causa=a1.erechazado.causa.descripcion  
            except Exception, e:
                causa=''     
            
            elementos_detalle+=[{'total_casco':total_casco,'causa':causa,
                                 'id_doc':a1.erechazado.doc_entregarechazado.id_doc,'casco_id':a1.casco.id_casco,
                                 'casco_nro':a1.casco.casco_nro,'producto':a1.casco.producto.descripcion,
                                 'productoid':a1.casco.producto.id,'cliente':a1.casco.get_cliente()}]
            k+=1
            id1=a1.casco.producto.id 
            k2+=1
            
        if k!=0:
            elementos_detalle[k-1]['cantidad'] = k2
        return HttpResponse(simplejson.dumps(elementos_detalle),content_type = 'application/javascript; charset=utf8')
        
#        detallecc = DetalleEntregaRechazado.objects.select_related().filter(erechazado=idcr).order_by('admincomerciax_producto.descripcion','casco_casco.casco_nro')
#        
#        json_serializer = serializers.get_serializer("json")()
#        response = HttpResponse()
#        response["Content-type"] = "text/json"
#
#        json_serializer.serialize(detallecc,ensure_ascii = False, stream = response, use_natural_keys=True)
#        #json_serializer.serialize(detallerc,ensure_ascii = False, stream = response)
#        return response
#
#        
#        #return HttpResponseRedirect("/comerciax/casco/cascocr/view/" + idcr)
    else:
        error2 = "No se puede eliminar el casco " + str(nro) + " ya que su estado ha cambiado "
        return HttpResponse(json.dumps({'error':True, 'message':error2}),mimetype=u'application/json')
        #return cascocr_view(request, idcr,error2)

#############################################################
#        ENTREGA DE CASCOS A PRODUCCION TERMINADA           #
#############################################################
@login_required
def get_pt_list(request):
    #prepare the params
    try:
        fecha_desde=Fecha_Ver.objects.get()
    except Exception, e:
        fecha_desde=None
    if  fecha_desde == None:  
        querySet = ProduccionTerminada.objects.select_related().all().order_by('-doc_pt__fecha_doc')
    else:
        querySet = querySet = ProduccionTerminada.objects.select_related().filter(doc_pt__fecha_doc__gte=fecha_desde.fecha).order_by('-doc_pt__fecha_doc')
    #querySet = querySet.filter(doc__fecha_doc__year=2010)
 
    columnIndexNameMap = {0: '-casco_doc.fecha_doc',1: 'produccionterminada_nro',2:'casco_doc.fecha_doc'}
    #searchableColumns = ['cliente__nombre','recepcioncliente_nro']
    searchableColumns = ['produccionterminada_nro','doc_pt__fecha_doc']
    #path to template used to generate json
    jsonTemplatePath = 'casco/json/json_pt.txt'


    #call to generic function from utils
    return get_datatables_records(request, querySet, columnIndexNameMap, searchableColumns, jsonTemplatePath)


@login_required
def cascopt_index(request):
    if not request.user.has_perm('casco.prodterm'):
        return render_to_response("denegado.html",locals(),context_instance = RequestContext(request))
    
    return render_to_response('casco/cascoptindex.html',locals(),context_instance = RequestContext(request))


@login_required
@transaction.commit_on_success()
def cascopt_add(request):
    nombre_form='Producción Terminada'
    descripcion_form='Entrega de Cascos a Producción Terminada'
    titulo_form='Producción Terminada' 
    controlador_form='Producción Terminada'
    accion_form='/comerciax/casco/cascopt/add'
    cancelbtn_form='/comerciax/casco/cascopt/index'
    fecha_cierre=Fechacierre.objects.get(almacen='p').fechaminima()
    fecha_maxima=Fechacierre.objects.get(almacen='p').fechamaxima()
    c=None
    l=[]
    if request.method == 'POST':
        form = CascoDIPForm(request.POST)

        #rajuste = form.cleaned_data['ajuste']
        if form.is_valid():
            doc=Doc()

            fechadoc=form.cleaned_data['fecha']
            doc.fecha_doc=fechadoc
            doc.observaciones=form.cleaned_data['observaciones']
            doc.fecha_operacion=datetime.date.today()
            doc.fecha_doc=fechadoc
            doc.tipo_doc='9'
         
            pk_user=User.objects.get(pk=request.user.id)
            # esto hay que cambiarlo y poner el operador
            pk_doc=uuid4()
            

            doc.id_doc = pk_doc 
            doc.operador=pk_user
            
            
            dpt=ProduccionTerminada()
            

            dpt.produccionterminada_nro=form.cleaned_data['nro']
            rc_nro1=form.cleaned_data['nro']
            dpt.doc_pt=doc
            recep=ProduccionTerminada.objects.filter(produccionterminada_nro=rc_nro1)
            if recep.__len__()!=0:
                for a1 in recep:
                    if a1.doc_pt.fecha_doc.year == fechadoc.year:
                        l=['Número de documento existente']
                        return render_to_response('form/form_adddetalle.html',  {'tipocliente':'0','form': form, 'form_name':nombre_form,'form_description':descripcion_form,
                                                                                 'accion':accion_form,'titulo':titulo_form,'controlador':controlador_form,
                                                                                 'cancelbtn':cancelbtn_form,'fecha_minima':fecha_cierre,'fecha_maxima':fecha_maxima,'error2':l},context_instance = RequestContext(request))
            try:

                doc.save()
                dpt.save() 
 
                return HttpResponseRedirect('/comerciax/casco/cascopt/view/'+pk_doc.__str__())  
            except Exception, e:
                exc_info = e.__str__() # sys.exc_info()[:1]
                c = exc_info.find("DETAIL:")
                
                if c < 0:
                    l=l+["Error Fatal."]
                else:
                    c = exc_info[c + 7:]
                    l=l+[c] 
                                     
                transaction.rollback()
                form = CascoDIPForm(request.POST)
                return render_to_response('form/form_adddetalle.html',  {'tipocliente':'2','form': form, 'form_name':nombre_form,'form_description':descripcion_form,
                                                                         'accion':accion_form,'titulo':titulo_form,'controlador':controlador_form,
                                                                         'cancelbtn':cancelbtn_form,'fecha_minima':fecha_cierre,'fecha_maxima':fecha_maxima,'error2':l},context_instance = RequestContext(request))
            else:
                transaction.commit()
    else:
        form = CascoDIPForm(initial={'fecha':fecha_cierre}) 
    return render_to_response('form/form_adddetalle.html',  {'tipocliente':'2','form': form, 'form_name':nombre_form,'form_description':descripcion_form,
                                                             'accion':accion_form,'titulo':titulo_form,'controlador':controlador_form,
                                                             'cancelbtn':cancelbtn_form,'fecha_minima':fecha_cierre,'fecha_maxima':fecha_maxima,'error2':c},context_instance = RequestContext(request))


@login_required
@transaction.commit_on_success()
def cascopt_edit(request,idpt):
    if not request.user.has_perm('casco.prodterm'):
        return render_to_response("denegado.html",locals(),context_instance = RequestContext(request))
    
    nombre_form='Producción Terminada'
    descripcion_form='Entrega de Cascos a Producción Terminada'
    titulo_form='Producción Terminada' 
    controlador_form='Producción Terminada'
    accion_form='/comerciax/casco/cascopt/edit/'+idpt+'/'
    cancelbtn_form='/comerciax/casco/cascopt/view/'+idpt+'/'
    fecha_cierre=Fechacierre.objects.get(almacen='p').fechaminima()
    fecha_maxima=Fechacierre.objects.get(almacen='p').fechamaxima()
    c=None
    l=[]
        
    if request.method == 'POST':
        form = CascoDIPForm(request.POST)

        #rajuste = form.cleaned_data['ajuste']
        if form.is_valid():
            dpt=ProduccionTerminada.objects.get(pk=idpt)
            object_doc=Doc.objects.get(pk=idpt)
            
            object_doc.fecha_doc=form.cleaned_data['fecha']
            fechadoc1=form.cleaned_data['fecha']
            object_doc.observaciones=form.cleaned_data['observaciones']
            object_doc.fecha_operacion=datetime.date.today()
         
            pk_user=User.objects.get(pk=request.user.id)
            # esto hay que cambiarlo y poner el operador
            #pk_doc=uuid4()
            

            object_doc.operador=pk_user
            
            dpt.produccionterminada_nro=form.cleaned_data['nro']
            rc_nro1=form.cleaned_data['nro']
            
            recep=ProduccionTerminada.objects.filter(produccionterminada_nro=rc_nro1)
            if recep.__len__()!=0:
                for a1 in recep:
                    if a1.doc_pt.fecha_doc.year == fechadoc1.year and a1.pk!=idpt:
                        l=['Número de documento existente']
                        return render_to_response('form/form_adddetalle.html',  {'tipocliente':'0','form': form, 'form_name':nombre_form,'form_description':descripcion_form,
                                                                                 'accion':accion_form,'titulo':titulo_form,'controlador':controlador_form,
                                                                                 'cancelbtn':cancelbtn_form,'error2':l,'fecha_minima':fecha_cierre,'fecha_maxima':fecha_maxima},context_instance = RequestContext(request))    
            #RecepcionCliente.objects.create(doc_recepcioncliente=obj_doc,recepcioncliente_nro=nro,recepcioncliente_ajuste=ajuste,cliente=obj_cliente)
            try:
                object_doc.save()
                dpt.save() 
 
                return HttpResponseRedirect('/comerciax/casco/cascopt/view/'+idpt)  

            except Exception, e:
                exc_info = e.__str__() # sys.exc_info()[:1]
                c = exc_info.find("DETAIL:")
                
                if c < 0:
                    l=l+["Error Fatal."]
                else:
                    c = exc_info[c + 7:]
                    l=l+[c]
                    
                transaction.rollback()
                form = CascoDIPForm(request.POST)
                return render_to_response('form/form_adddetalle.html',  {'tipocliente':'2','form': form, 'form_name':nombre_form,'form_description':descripcion_form,
                                                                         'accion':accion_form,'titulo':titulo_form,'controlador':controlador_form,
                                                                         'cancelbtn':cancelbtn_form,'fecha_minima':fecha_cierre,'fecha_maxima':fecha_maxima,'error2':l},context_instance = RequestContext(request))
            else:
                transaction.commit()     
    else:
        dpt = ProduccionTerminada.objects.select_related().get(pk=idpt)
        form = CascoDIPForm(initial={'nro':dpt.produccionterminada_nro,'fecha':dpt.doc_pt.fecha_doc,
                                             'observaciones':dpt.doc_pt.observaciones})
    return render_to_response('form/form_edit.html',  {'tipocliente':'2','form': form, 'form_name':nombre_form,'form_description':descripcion_form,'accion':accion_form,'titulo':titulo_form,
                                                       'controlador':controlador_form,'cancelbtn':cancelbtn_form,'fecha_minima':fecha_cierre,'fecha_maxima':fecha_maxima},context_instance = RequestContext(request))

@login_required
def cascopt_view(request,idpt):
    if not request.user.has_perm('casco.prodterm'):
        return render_to_response("denegado.html",locals(),context_instance = RequestContext(request))
    
    l=[]
    dpt = ProduccionTerminada.objects.select_related().get(pk=idpt)
    rc_fecha=dpt.doc_pt.fecha_doc.strftime("%d/%m/%Y")
    rc_nro=dpt.produccionterminada_nro
    
    rc_observaciones=dpt.doc_pt.observaciones
    filas = DetallePT.objects.select_related().filter(pt=idpt).order_by('casco__producto__descripcion','casco__casco_nro')
    adiciono=True
    if dpt.procesado==True:
        editar=False
        adiciono=False
    else:
        editar=editar_documento(filas, idpt)   
    elementos_detalle=[]
    id1=''
    k=0
    k2=0
    for a1 in filas:
        if k!=0:
            if id1!=a1.casco.producto.id:
                elementos_detalle[k-1]['cantidad'] = k2
                k2=0
        elementos_detalle+=[{'cliente':a1.casco.get_cliente,'casco_id':a1.casco.id_casco,
                             'casco_nro':a1.casco.casco_nro,'producto':a1.casco.producto,
                             'productosalida':a1.casco.producto_salida.descripcion,
                             'productoid':a1.casco.producto.id}]
        k+=1 
        k2+=1
        id1=a1.casco.producto.id  
    if k!=0:
        elementos_detalle[k-1]['cantidad'] = k2
    return render_to_response('casco/viewcascopt.html',{'total_casco':k,'rc_nro':rc_nro,'fecha':rc_fecha,'observaciones':rc_observaciones,
                                                              'rc_id':idpt,'elementos_detalle':elementos_detalle, 'edito':editar,
                                                              'adiciono':adiciono,'error2':l},context_instance = RequestContext(request))    

@login_required
@transaction.commit_on_success()
def cascopt_del(request,idpt):
    if not request.user.has_perm('casco.prodterm'):
        return render_to_response("denegado.html",locals(),context_instance = RequestContext(request))
    
    
    try:
        filas = DetallePT.objects.filter(pt=idpt)
        for canti in filas:
            actualiza_traza(canti.casco.id_casco,idpt)
        
        Doc.objects.select_related().get(pk=idpt).delete()
        return HttpResponseRedirect('/comerciax/casco/cascopt/index')
    except Exception :
        transaction.rollback()
        l = ['Error al eliminar el documento']
        dpt = ProduccionTerminada.objects.select_related().get(pk=idpt)
        rc_fecha=dpt.doc_pt.fecha_doc.strftime("%d/%m/%Y")

        rc_nro=dpt.produccionterminada_nro

        editar=1
        rc_observaciones=dpt.doc_pt.observaciones
        filas = DetallePT.objects.select_related().filter(pt=idpt).order_by('admincomerciax_producto.descripcion','casco_casco.casco_nro')

        return render_to_response('casco/viewcascopt.html',{'rc_nro':rc_nro,'fecha':rc_fecha,'observaciones':rc_observaciones,'rc_id':idpt,'elementos_detalle':filas, 'edito':editar,'error2':l},context_instance = RequestContext(request))

    else:
        transaction.commit()

#############################################################
#        DETALLE CASCO PARA PRODUCCION TERMINADA
#############################################################

@login_required
@transaction.commit_on_success()
def detallePT_add(request,idpt):
    if not request.user.has_perm('casco.prodterm'):
        return render_to_response("denegado.html",locals(),context_instance = RequestContext(request))
    
    l=[]
    titulo_form='Producción Terminada' 
    controlador_form='Producción Terminada'
    descripcion_form='Seleccionar cascos para la producción terminada'
    accion_form='detallePT_add'
    cancelbtn_form='/comerciax/casco/cascopt/view/'+idpt
    estado="Produccion"
    medidas=Producto.objects.all()
    medidasalida=Producto.objects.all()
    dpt=ProduccionTerminada.objects.get(pk=idpt)

    #cascos=Casco.objects.select_related().filter(estado_actual=Estados.estados["Produccion"]).order_by('admincomerciax_producto.descripcion','casco_nro')
  
    if request.method == 'POST':
        seleccion=request.POST.keys()
        medidasalida=request.POST["medidasalida"]
        k=0
        while True:
            if k==seleccion.__len__():
                break
            casco=Casco.objects.filter(pk=seleccion[k])
            
            if casco.count()!=0:
                '''
                Los selecionados los cambio de estado, agregar a detalle del documento y actualizar trazabilidad
                '''
                
                
                detalle=DetallePT()
                detalle.id_detallept=uuid4()
                detalle.pt=ProduccionTerminada.objects.get(pk=idpt)
                detalle.casco=Casco.objects.get(pk=seleccion[k])
                cascocc=Casco.objects.get(pk=seleccion[k])
                nro=cascocc.casco_nro
                if medidasalida.__len__()==0:
                    cascocc.producto_salida=Producto.objects.get(pk=cascocc.producto.id)
                else:
                    cascocc.producto_salida=Producto.objects.get(pk=medidasalida)
                    
                
                try:
                    detalle.save()
                    cascocc.save()
                except Exception, e:
                    exc_info = e.__str__() # sys.exc_info()[:1]
                    c = exc_info.find("DETAIL:")
                    
                    if c < 0:
                        l=l+["Error Fatal."]
                    else:
                        l=['El casco ' + str(nro) +' ya existe en este documento']
                        c = exc_info[c + 7:]
                        transaction.rollback()
                        return render_to_response('casco/form_seleccion.html',{'medida':medidas,'medidasalida':medidasalida,'estado':estado,'title':titulo_form,'controlador':controlador_form,'accion':accion_form,
                                                      'cancelbtn':cancelbtn_form,'nro':dpt.produccionterminada_nro,'form_description':descripcion_form,
                                                      'fecha':dpt.doc_pt.fecha_doc.strftime("%d/%m/%Y"),'observaciones':dpt.doc_pt.observaciones,
                                                      'rc_id':idpt,'error2':l},context_instance = RequestContext(request))
                        
                        
                Casco.objects.filter(pk=seleccion[k]).update(estado_actual="PT")
                add_trazabilidad(seleccion[k], idpt, "PT")
                
            k=k+1
        if request.POST.__contains__('submit1'):
            medidas=Producto.objects.all()
            medidasalida=Producto.objects.all()
            #cascos=Casco.objects.select_related().filter(estado_actual=Estados.estados["Produccion"]).order_by('admincomerciax_producto.descripcion','casco_nro')
            return render_to_response('casco/form_seleccion.html',{'medida':medidas,'medidasalida':medidasalida,'estado':estado,'title':titulo_form,'controlador':controlador_form,'accion':accion_form,
                                                      'cancelbtn':cancelbtn_form,'nro':dpt.produccionterminada_nro,'form_description':descripcion_form,
                                                      'fecha':dpt.doc_pt.fecha_doc.strftime("%d/%m/%Y"),'observaciones':dpt.doc_pt.observaciones,
                                                      'rc_id':idpt,'error2':l},context_instance = RequestContext(request))
        else:
            return HttpResponseRedirect('/comerciax/casco/cascopt/view/' + idpt)
    return render_to_response('casco/form_seleccion.html', {'medida':medidas,'medidasalida':medidasalida,'estado':estado,'title':titulo_form,'controlador':controlador_form,'accion':accion_form,
                                                      'cancelbtn':cancelbtn_form, 'nro':dpt.produccionterminada_nro, 'form_description':descripcion_form,
                                                      'fecha':dpt.doc_pt.fecha_doc.strftime("%d/%m/%Y"),'observaciones':dpt.doc_pt.observaciones,
                                                      'rc_id':idpt,'error2':l},context_instance = RequestContext(request))    

@login_required
def detallePT_delete(request,idpt,idcasco): 
    if not request.user.has_perm('casco.prodterm'):
        return render_to_response("denegado.html",locals(),context_instance = RequestContext(request))
       
    casco=Casco.objects.select_related().get(pk=idcasco)
    nro=casco.casco_nro
    
    if eliminar_detalle_sino(casco.id_casco,idpt):
        DetallePT.objects.get(casco=idcasco).delete()
        
        actualiza_traza(idcasco,idpt)
        filas = DetallePT.objects.select_related().filter(pt=idpt).order_by('casco__producto__descripcion','casco__casco_nro')
        
        total_casco=str(filas.count())
            
        elementos_detalle=[]
        id1=''
        k=0
        k2=0
        for a1 in filas:
            if k!=0:
                if id1!=a1.casco.producto.id:
#                    elementos_detalle[k-1]['cantidad'] = elementos_detalle[k-1]['productoid']
                    elementos_detalle[k-1]['cantidad'] = k2
                    k2=0
                    
            elementos_detalle+=[{'total_casco':total_casco,
                                 'id_doc':a1.pt.doc_pt.id_doc,'casco_id':a1.casco.id_casco,
                                 'casco_nro':a1.casco.casco_nro,'producto':a1.casco.producto.descripcion,
                                 'productoid':a1.casco.producto.id,'cliente':a1.casco.get_cliente(),'productosalida':a1.casco.producto_salida.descripcion}]
            k+=1
            id1=a1.casco.producto.id 
            k2+=1
            
        if k!=0:
            elementos_detalle[k-1]['cantidad'] = k2
        return HttpResponse(simplejson.dumps(elementos_detalle),content_type = 'application/javascript; charset=utf8')
    else:
        error2 = "No se puede eliminar el casco " + str(nro) + " ya que su estado ha cambiado "
        return HttpResponse(json.dumps({'error':True, 'message':error2}),mimetype=u'application/json')
        #return cascopt_view(request, idpt,error2)
    

#############################################################
#        RECEPCION DE PT A CLIENTES EXTRENOS                #
#############################################################
'''
ESTOS SON LOS CASCOS QUE SE TRANFIRIERON Y SE RECIBEN EN PT
'''

@login_required
def get_rept_list(request):
    #prepare the params
    try:
        fecha_desde=Fecha_Ver.objects.get()
    except Exception, e:
        fecha_desde=None
    if  fecha_desde == None:  
        querySet = PTExternos.objects.select_related().all().order_by('-doc_ptexternos__fecha_doc')
    else:
        querySet = PTExternos.objects.select_related().filter(doc_ptexternos__fecha_doc__gte=fecha_desde.fecha).order_by('-doc_ptexternos__fecha_doc')
    
    #querySet = querySet.filter(doc__fecha_doc__year=2010)
 
    columnIndexNameMap = {0: '-casco_doc.fecha_doc',1: 'ptexternos_nro',2:'casco_doc.fecha_doc',3:'admincomerciax_cliente.nombre'}
    #searchableColumns = ['cliente__nombre','recepcioncliente_nro']
    searchableColumns = ['ptexternos_nro','doc_ptexternos__fecha_doc','cliente__nombre']

    #path to template used to generate json
    jsonTemplatePath = 'casco/json/json_rept.txt'


    #call to generic function from utils
    return get_datatables_records(request, querySet, columnIndexNameMap, searchableColumns, jsonTemplatePath)


    
@login_required
def ptexternos_index(request):
    if not request.user.has_perm('casco.ptext'):
        return render_to_response("denegado.html",locals(),context_instance = RequestContext(request))
    
    return render_to_response('casco/ptexternosindex.html',locals(),context_instance = RequestContext(request))

@login_required
@transaction.commit_on_success()
def ptexternos_add(request):
    if not request.user.has_perm('casco.ptext'):
        return render_to_response("denegado.html",locals(),context_instance = RequestContext(request))
    
    nombre_form='Producción Terminada' 
    descripcion_form='Casco para producción terminada desde entidades externas' 
    titulo_form='Producción Terminada' 
    controlador_form='Producción Terminada'
    accion_form='/comerciax/casco/ptexternos/add'
    cancelbtn_form='/comerciax/casco/ptexternos/index'
    fecha_cierre=Fechacierre.objects.get(almacen='pt').fechaminima()
    fecha_maxima=Fechacierre.objects.get(almacen='pt').fechamaxima()
    c=None
    l=[]
    if request.method == 'POST':
        form = PTExternosForm(request.POST)

        #rajuste = form.cleaned_data['ajuste']
        if form.is_valid():
            doc=Doc()

            fechadoc=form.cleaned_data['fecha']
            doc.fecha_doc=fechadoc
            doc.observaciones=form.cleaned_data['observaciones']
            doc.fecha_operacion=datetime.date.today()
            doc.fecha_doc=fechadoc
            doc.tipo_doc='10'
         
            pk_user=User.objects.get(pk=request.user.id)
            # esto hay que cambiarlo y poner el operador
            pk_doc=uuid4()
            

            doc.id_doc = pk_doc 
            doc.operador=pk_user
            
            
            rpte=PTExternos()
            
            rc_nro=form.cleaned_data['nro']
            
            
            obj_cliente = Cliente.objects.get(pk = form.data['cliente']) 
            rpte.ptexternos_nro=rc_nro
            rpte.nro_factura=form.cleaned_data['nrofactura']
            rpte.cliente=obj_cliente
            rpte.doc_ptexternos=doc
            recep=PTExternos.objects.filter(ptexternos_nro=rc_nro)
            if recep.__len__()!=0:
                for a1 in recep:
                    if a1.doc_ptexternos.fecha_doc.year == fechadoc.year:
                        l=['Número de documento existente']
                        return render_to_response('form/form_adddetalle.html',  {'tipocliente':'0','form': form, 'form_name':nombre_form,'form_description':descripcion_form,
                                                                                 'accion':accion_form,'titulo':titulo_form,'controlador':controlador_form,
                                                                                 'cancelbtn':cancelbtn_form,'fecha_minima':fecha_cierre,'fecha_maxima':fecha_maxima,'error2':l},context_instance = RequestContext(request))

                                            
            try:

                doc.save()
                rpte.save() 
 
                return HttpResponseRedirect('/comerciax/casco/ptexternos/view/'+pk_doc.__str__())  
            except Exception, e:
                exc_info = e.__str__() # sys.exc_info()[:1]
                c = exc_info.find("DETAIL:")
                
                if c < 0:
                    l=l+["Error Fatal."]
                else:
                    c = exc_info[c + 7:]
                    l=l+[c] 
                                     
                transaction.rollback()
                form = PTExternosForm(request.POST)
                return render_to_response('form/form_adddetalle.html',  {'tipocliente':'1','form': form, 'form_name':nombre_form,'form_description':descripcion_form,
                                                                         'accion':accion_form,'titulo':titulo_form,'controlador':controlador_form,
                                                                         'cancelbtn':cancelbtn_form,'fecha_minima':fecha_cierre,'fecha_maxima':fecha_maxima,'error2':l},context_instance = RequestContext(request))
            else:
                transaction.commit()
    else:
        form = PTExternosForm(initial={'fecha':fecha_cierre}) 
    return render_to_response('form/form_adddetalle.html',  {'tipocliente':'1','form': form, 'form_name':nombre_form,'form_description':descripcion_form,
                                                             'accion':accion_form,'titulo':titulo_form,'controlador':controlador_form,
                                                             'cancelbtn':cancelbtn_form,'fecha_minima':fecha_cierre,'fecha_maxima':fecha_maxima,'error2':c},context_instance = RequestContext(request))
    
@login_required
def ptexternos_view(request,idpte):
    if not request.user.has_perm('casco.ptext'):
        return render_to_response("denegado.html",locals(),context_instance = RequestContext(request))
    
    l=[]
    
    rpte = PTExternos.objects.select_related().get(pk=idpte)
    rc_fecha=rpte.doc_ptexternos.fecha_doc.strftime("%d/%m/%Y")
    rc_cliente=rpte.cliente.nombre
    rc_nro=rpte.ptexternos_nro
    rc_observaciones=rpte.doc_ptexternos.observaciones
    filas = DetallePTE.objects.select_related().filter(doc_pte=idpte).order_by('casco__producto__descripcion','casco__casco_nro')
    adiciono=True
    # Verificar si se puede editar. Se puede editar si todos los cascos relacionados con él el estado es Casco
    if rpte.procesado==True:
        editar=False
        adiciono=False
    else:
        editar=editar_documento(filas, idpte)
        
    elementos_detalle=[]
    id1=''
    k=0
    k2=0
    for a1 in filas:
        if k!=0:
            if id1!=a1.casco.producto.id:
                elementos_detalle[k-1]['cantidad'] = k2
                k2=0
        elementos_detalle+=[{'cliente':a1.casco.get_cliente,'casco_id':a1.casco.id_casco,
                             'casco_nro':a1.casco.casco_nro,'producto':a1.casco.producto,
                             'productosalida':a1.casco.producto_salida.descripcion,
                             'productoid':a1.casco.producto.id,'nro_ext':a1.nro_externo}]
        k+=1
        k2+=1
        id1=a1.casco.producto.id  
    if k!=0:
        elementos_detalle[k-1]['cantidad'] = k2
    return render_to_response('casco/viewptexternos.html',{'total_casco':k,'rc_nro':rc_nro,'fecha':rc_fecha,'observaciones':rc_observaciones,
                                                              'rc_id':idpte,'elementos_detalle':elementos_detalle, 'edito':editar,'cliente':rc_cliente,
                                                              'adiciono':adiciono,'error2':l},context_instance = RequestContext(request))
    
#    return render_to_response('casco/viewptexternos.html',{'rc_nro':rc_nro,'fecha':rc_fecha,'cliente':rc_cliente,'observaciones':rc_observaciones,'rc_id':idpte,'elementos_detalle':filas, 
#                                                           'edito':editar,'adiciono':adiciono,'error2':l},context_instance = RequestContext(request))


@login_required
@transaction.commit_on_success()
def ptexternos_edit(request,idpte):
    if not request.user.has_perm('casco.ptext'):
        return render_to_response("denegado.html",locals(),context_instance = RequestContext(request))
    
    nombre_form='Producción Terminada' 
    descripcion_form='Casco para producción terminada desde entidades externas' 
    titulo_form='Producción Terminada' 
    controlador_form='Producción Terminada'
    accion_form='/comerciax/casco/ptexternos/edit/' + idpte +'/'
    cancelbtn_form='/comerciax/casco/ptexternos/view/' + idpte +'/'
    fecha_cierre=Fechacierre.objects.get(almacen='pt').fechaminima()
    fecha_maxima=Fechacierre.objects.get(almacen='pt').fechamaxima()
    c=None
    l=[]
        
    if request.method == 'POST':
        form = PTExternosForm(request.POST)

        #rajuste = form.cleaned_data['ajuste']
        if form.is_valid():
            rpte=PTExternos.objects.get(pk=idpte)
            object_doc=Doc.objects.get(pk=idpte)
            
            object_doc.fecha_doc=form.cleaned_data['fecha']
            fechadoc1=form.cleaned_data['fecha']
            object_doc.observaciones=form.cleaned_data['observaciones']
            object_doc.fecha_operacion=datetime.date.today()
         
            pk_user=User.objects.get(pk=request.user.id)
            # esto hay que cambiarlo y poner el operador
            #pk_doc=uuid4()
            

            object_doc.operador=pk_user
            
            
            rpte.ptexternos_nro=form.cleaned_data['nro']
            rc_nro1=form.cleaned_data['nro']
            rpte.nro_factura=form.cleaned_data['nrofactura']
            rpte.cliente=Cliente.objects.get(pk = form.data['cliente'])
            
            recep=PTExternos.objects.filter(ptexternos_nro=rc_nro1)
            if recep.__len__()!=0:
                for a1 in recep:
                    if a1.doc_ptexternos.fecha_doc.year == fechadoc1.year and a1.pk!=idpte:
                        l=['Número de documento existente']
                        return render_to_response('form/form_adddetalle.html',  {'tipocliente':'0','form': form, 'form_name':nombre_form,'form_description':descripcion_form,
                                                                                 'accion':accion_form,'titulo':titulo_form,'controlador':controlador_form,
                                                                                 'cancelbtn':cancelbtn_form,'error2':l,'fecha_minima':fecha_cierre,'fecha_maxima':fecha_maxima},context_instance = RequestContext(request))    
            #PTExternos.objects.create(doc_ptexternos=obj_doc,ptexternos_nro=nro,ptexternos_ajuste=ajuste,cliente=obj_cliente)
            try:
                object_doc.save()
                rpte.save() 
 
                return HttpResponseRedirect('/comerciax/casco/ptexternos/view/'+idpte)  

            except Exception, e:
                exc_info = e.__str__() # sys.exc_info()[:1]
                c = exc_info.find("DETAIL:")
                
                if c < 0:
                    l=l+["Error Fatal."]
                else:
                    c = exc_info[c + 7:]
                    l=l+[c]
                    
                transaction.rollback()
                form = PTExternosForm(request.POST)
                return render_to_response('form/form_adddetalle.html',  {'tipocliente':'1','form': form, 'form_name':nombre_form,'form_description':descripcion_form,
                                                                         'accion':accion_form,'titulo':titulo_form,'controlador':controlador_form,
                                                                         'cancelbtn':cancelbtn_form,'fecha_minima':fecha_cierre,'fecha_maxima':fecha_maxima,'error2':l},context_instance = RequestContext(request))
            else:
                transaction.commit()     
    else:
        rpte = PTExternos.objects.select_related().get(pk=idpte)
        form = PTExternosForm(initial={'nro':rpte.ptexternos_nro,'fecha':rpte.doc_ptexternos.fecha_doc,
                                             'cliente':rpte.cliente,'observaciones':rpte.doc_ptexternos.observaciones})
    return render_to_response('form/form_edit.html',  {'tipocliente':'1','form': form, 'form_name':nombre_form,'form_description':descripcion_form,
                                                       'accion':accion_form,'titulo':titulo_form,'controlador':controlador_form,
                                                       'cancelbtn':cancelbtn_form,'fecha_minima':fecha_cierre,'fecha_maxima':fecha_maxima},context_instance = RequestContext(request))

@login_required
@transaction.commit_on_success()
def ptexternos_del(request,idpte):
    if not request.user.has_perm('casco.ptext'):
        return render_to_response("denegado.html",locals(),context_instance = RequestContext(request))
    
    try:
        filas = DetallePTE.objects.filter(doc_pte=idpte)
        for canti in filas:
            actualiza_traza(canti.casco.id_casco,idpte)
            DetalleTransferencia.objects.filter(casco=canti.casco.id_casco).update(id_docrecepc='')
        
        Doc.objects.select_related().get(pk=idpte).delete()

        return HttpResponseRedirect('/comerciax/casco/ptexternos/index')
    except Exception,e :
        transaction.rollback()
        l = ['Error al eliminar el documento']
        cp = PTExternos.objects.select_related().get(pk=idpte)
        rc_fecha=cp.doc_ptexternos.fecha_doc.strftime("%d/%m/%Y")

        rc_nro=cp.ptexternos_nro
        editar=1
        rc_observaciones=cp.doc_ptexternos.observaciones
        filas = DetallePTE.objects.select_related().filter(doc_pte=idpte).order_by('admincomerciax_producto.descripcion','casco_casco.casco_nro')

        return render_to_response('casco/viewptexternos.html',{'rc_nro':rc_nro,'fecha':rc_fecha,'observaciones':rc_observaciones,'rc_id':idpte,'elementos_detalle':filas, 'edito':editar,'error2':l},context_instance = RequestContext(request))

    else:
        
        transaction.commit()


@login_required
@transaction.commit_on_success()
def detallePTE_add(request,idpte):
    if not request.user.has_perm('casco.prodterm'):
        return render_to_response("denegado.html",locals(),context_instance = RequestContext(request))
    
    l=[]
    titulo_form='Producción Terminada' 
    controlador_form='Producción Terminada'
    descripcion_form='Seleccionar cascos para la producción terminada'
    accion_form='detallePTE_add'
    
    cancelbtn_form='/comerciax/casco/ptexternos/view/'+idpte
    estado="Transferencia"
    medidas=Producto.objects.all()
    medidasalida=Producto.objects.all()
    pte=PTExternos.objects.get(pk=idpte)
    id_clieext=pte.cliente.id
#    transfe=DetalleTransferencia.objects.select_related().filter(transf=idpte).order_by('casco__producto','casco__casco_nro')
    #cascos=Casco.objects.select_related().filter(estado_actual=Estados.estados["Produccion"]).order_by('admincomerciax_producto.descripcion','casco_nro')
  
    if request.method == 'POST':
        seleccion=request.POST.keys()
        medidasalida=request.POST["medidasalida"]
        k=0
        while True:
            if k==seleccion.__len__():
                break
            casco=Casco.objects.filter(pk=seleccion[k])
            
            if casco.count()!=0:
                '''
                Los selecionados los cambio de estado, agregar a detalle del documento y actualizar trazabilidad
                '''
                detalle=DetallePTE()
                detalle.id_detallepte=uuid4()
                detalle.doc_pte=PTExternos.objects.get(pk=idpte)
                detalle.casco=Casco.objects.get(pk=seleccion[k])
                cascocc=Casco.objects.get(pk=seleccion[k])
                nro=cascocc.casco_nro
                if medidasalida.__len__()==0:
                    cascocc.producto_salida=Producto.objects.get(pk=cascocc.producto.id)
                else:
                    cascocc.producto_salida=Producto.objects.get(pk=medidasalida)
                try:
                    detalle.save()
                    cascocc.save()
                except Exception, e:
                    exc_info = e.__str__() # sys.exc_info()[:1]
                    c = exc_info.find("DETAIL:")
                    
                    if c < 0:
                        l=l+["Error Fatal."]
                    else:
                        l=['El casco ' + str(nro) +' ya existe en este documento']
                        c = exc_info[c + 7:]
                        transaction.rollback()
                        return render_to_response('casco/form_seleccion.html',{'medida':medidas,'medidasalida':medidasalida,'estado':estado,'title':titulo_form,'controlador':controlador_form,'accion':accion_form,
                                                      'cancelbtn':cancelbtn_form,'nro':pte.ptexternos_nro,'form_description':descripcion_form,
                                                      'fecha':pte.doc_ptexternos.fecha_doc.strftime("%d/%m/%Y"),'observaciones':pte.doc_ptexternos.observaciones,
                                                      'rc_id':idpte,'error2':l,'id_clieext':id_clieext},context_instance = RequestContext(request))
                        
                        
                Casco.objects.filter(pk=seleccion[k]).update(estado_actual="PT")
                add_trazabilidad(seleccion[k], idpte, "PT")
                
            k=k+1
        if request.POST.__contains__('submit1'):
            medidas=Producto.objects.all()
            medidasalida=Producto.objects.all()
            #cascos=Casco.objects.select_related().filter(estado_actual=Estados.estados["Produccion"]).order_by('admincomerciax_producto.descripcion','casco_nro')
            return render_to_response('casco/form_seleccion.html',{'medida':medidas,'medidasalida':medidasalida,'estado':estado,'title':titulo_form,'controlador':controlador_form,'accion':accion_form,
                                                      'cancelbtn':cancelbtn_form,'nro':pte.ptexternos_nro,'form_description':descripcion_form,
                                                      'fecha':pte.doc_ptexternos.fecha_doc.strftime("%d/%m/%Y"),'observaciones':pte.doc_ptexternos.observaciones,
                                                      'rc_id':idpte,'error2':l,'id_clieext':id_clieext},context_instance = RequestContext(request))
        else:
            return HttpResponseRedirect('/comerciax/casco/ptexternos/view/' + idpte)
    return render_to_response('casco/form_seleccion.html', {'medida':medidas,'medidasalida':medidasalida,'estado':estado,'title':titulo_form,
                                                            'controlador':controlador_form,'accion':accion_form,'cancelbtn':cancelbtn_form, 
                                                            'nro':pte.ptexternos_nro, 'form_description':descripcion_form,
                                                            'fecha':pte.doc_ptexternos.fecha_doc.strftime("%d/%m/%Y"),'observaciones':pte.doc_ptexternos.observaciones,
                                                            'rc_id':pte,'error2':l,'id_clieext':id_clieext},context_instance = RequestContext(request))

@login_required
def detallePTE_delete(request,idcasco,idpte):
    if not request.user.has_perm('casco.ptext'):
        return render_to_response("denegado.html",locals(),context_instance = RequestContext(request))
    
    casco=Casco.objects.select_related().get(pk=idcasco)
    nro=casco.casco_nro
    
    if eliminar_detalle_sino(casco.id_casco,idpte):
        DetallePTE.objects.get(casco=idcasco).delete()
        actualiza_traza(idcasco,idpte)
        
        DetalleTransferencia.objects.filter(casco=idcasco).update(id_docrecepc='')
        
        Transferencia.objects.filter(transferencia_nro=DetalleTransferencia.objects.get(casco=idcasco).transf).update(cerrada=False)

        filas = DetallePTE.objects.select_related().filter(doc_pte=idpte).order_by('casco__producto__descripcion','casco__casco_nro')
        
        total_casco=str(filas.count())
            
        elementos_detalle=[]
        id1=''
        k=0
        k2=0
        for a1 in filas:
            if k!=0:
                if id1!=a1.casco.producto.id:
#                    elementos_detalle[k-1]['cantidad'] = elementos_detalle[k-1]['productoid']
                    elementos_detalle[k-1]['cantidad'] = k2
                    k2=0
                    
            elementos_detalle+=[{'total_casco':total_casco,
                                 'id_doc':a1.doc_pte.doc_ptexternos.id_doc,'casco_id':a1.casco.id_casco,
                                 'casco_nro':a1.casco.casco_nro,'producto':a1.casco.producto.descripcion,
                                 'productoid':a1.casco.producto.id,'cliente':a1.casco.get_cliente(),
                                 'productosalida':a1.casco.producto_salida.descripcion,'nro_ext':a1.nro_externo}]
            k+=1
            id1=a1.casco.producto.id 
            k2+=1
            
        if k!=0:
            elementos_detalle[k-1]['cantidad'] = k2
        return HttpResponse(simplejson.dumps(elementos_detalle),content_type = 'application/javascript; charset=utf8')
    else:
        error2 = "No se puede eliminar el casco " + str(nro) + " ya que su estado ha cambiado "
        return HttpResponse(json.dumps({'error':True, 'message':error2}),mimetype=u'application/json')
        #return cascocc_view(request, idpte,error2)

@login_required
@transaction.commit_on_success()
def detallePTE_edit(request,idpte,idcasco):
    if not request.user.has_perm('casco.ptext'):
        return render_to_response("denegado.html",locals(),context_instance = RequestContext(request))
    
    c=None
    l=[]
    
    nombre_form='Producción Terminada' 
    descripcion_form='Casco para producción terminada desde entidades externas' 
    titulo_form='Producción Terminada' 
    controlador_form='Producción Terminada'
    accion_form='detallePTE_edit/' + idpte +'/' +idcasco
    cancelbtn_form='/comerciax/casco/ptexternos/view/' + idpte +'/'
    
    
    if request.method == 'POST':
        form = DetallePTEForm(request.POST)
        
        if form.is_valid():
            di=DetallePTE.objects.get(casco=idcasco,doc_pte=idpte)
            
            di.nro_externo=form.data['nro_externo']
            cascocc=Casco.objects.get(pk=idcasco)
            medidasalida=form.data['medida_salida']
            if medidasalida.__len__()==0:
                cascocc.producto_salida=Producto.objects.get(pk=cascocc.producto.id)
            else:
                cascocc.producto_salida=Producto.objects.get(pk=medidasalida)
                
            try:
                di.save()
                cascocc.save()
                return ptexternos_view(request, idpte)
            except Exception, e:
                exc_info = e.__str__() # sys.exc_info()[:1]
                c = exc_info.find("DETAIL:")
                if c < 0:
                    l = l + ["Error Fatal."]
                else:
                    c = exc_info[c + 7:]
                    l=l+[c]
                transaction.rollback()
                form = DetallePTEForm(request.POST)
                return render_to_response("form/form_edit.html",{'tipocliente':'1','form':form,'title':titulo_form, 'form_name': nombre_form,'form_description':descripcion_form,'controlador':controlador_form,'accion':accion_form
                                                         , 'cancelbtn':cancelbtn_form,'error2':l},context_instance = RequestContext(request))
            else:
                transaction.commit()
    else:   
        rdip =DetallePTE.objects.select_related().get(casco=idcasco,doc_pte=idpte)
        aa=rdip.casco.producto_salida.descripcion
        form = DetallePTEForm(initial={'nro':rdip.casco.casco_nro,'nro_externo':rdip.nro_externo,'medida_salida':rdip.casco.producto_salida})
        return render_to_response('form/form_edit.html',  {'tipocliente':'1','form': form, 'form_name':nombre_form,'form_description':descripcion_form,'accion':accion_form,'titulo':titulo_form,'controlador':controlador_form,'cancelbtn':cancelbtn_form},context_instance = RequestContext(request))
    return ptexternos_view(request, idpte)  


#############################################################
#        RECEPCION DE RECHAZO A CLIENTES EXTRENOS           #
#############################################################
'''
ESTOS SON LOS CASCOS QUE SE TRANFIRIERON Y SE RECIBEN COMO RECHAZADOS
'''
@login_required
def get_rere_list(request):
    #prepare the params
    try:
        fecha_desde=Fecha_Ver.objects.get()
    except Exception, e:
        fecha_desde=None
    if  fecha_desde == None:  
        querySet = RecepRechaExt.objects.select_related().all().order_by('-doc_receprechaext__fecha_doc')
    else:
        querySet = RecepRechaExt.objects.select_related().filter(doc_receprechaext__fecha_doc__gte=fecha_desde.fecha).order_by('-doc_receprechaext__fecha_doc')
    
    #querySet = querySet.filter(doc__fecha_doc__year=2010)
        
    columnIndexNameMap = {0: '-casco_doc.fecha_doc',1: 'receprechaext_nro',2:'casco_doc.fecha_doc',3:'admincomerciax.cliente_nombre'}
    #searchableColumns = ['cliente__nombre','recepcioncliente_nro']
    searchableColumns = ['receprechaext_nro','doc_receprechaext__fecha_doc','cliente__nombre']
    #path to template used to generate json
    jsonTemplatePath = 'casco/json/json_rre.txt'


    #call to generic function from utils
    return get_datatables_records(request, querySet, columnIndexNameMap, searchableColumns, jsonTemplatePath)


    
@login_required
def rechaexternos_index(request):
    if not request.user.has_perm('casco.receprechext'):
        return render_to_response("denegado.html",locals(),context_instance = RequestContext(request))
    
    return render_to_response('casco/rechaexternosindex.html',locals(),context_instance = RequestContext(request))

@login_required
@transaction.commit_on_success()
def rechaexternos_add(request):
    if not request.user.has_perm('casco.receprechext'):
        return render_to_response("denegado.html",locals(),context_instance = RequestContext(request))
    
    nombre_form='Recepción de Cascos'
    descripcion_form='Recepción de Cascos Rechazados por Entidades Externas'
    titulo_form='Recepción de Cascos' 
    controlador_form='Recepción de Cascos'
    accion_form='/comerciax/casco/rechaexternos/add'
    cancelbtn_form='/comerciax/casco/rechaexternos/index'
    fecha_cierre=Fechacierre.objects.get(almacen='c').fechaminima()
    fecha_maxima=Fechacierre.objects.get(almacen='c').fechamaxima()
    c=None
    l=[]
    if request.method == 'POST':
        form = ReExternosForm(request.POST)

        #rajuste = form.cleaned_data['ajuste']
        if form.is_valid():
            doc=Doc()

            fechadoc=form.cleaned_data['fecha']
            doc.fecha_doc=fechadoc
            doc.observaciones=form.cleaned_data['observaciones']
            doc.fecha_operacion=datetime.date.today()
            doc.fecha_doc=fechadoc
            doc.tipo_doc='11'
         
            pk_user=User.objects.get(pk=request.user.id)
            # esto hay que cambiarlo y poner el operador
            pk_doc=uuid4()
            

            doc.id_doc = pk_doc 
            doc.operador=pk_user
            
            
            rpte=RecepRechaExt()
            
            rc_nro=form.cleaned_data['nro']
            
            
            obj_cliente = Cliente.objects.get(pk = form.data['cliente']) 
            rpte.receprechaext_nro=rc_nro
            rpte.nro_factura=form.cleaned_data['nrofactura']
            rpte.cliente=obj_cliente
            rpte.doc_receprechaext=doc
            recep=RecepRechaExt.objects.filter(receprechaext_nro=rc_nro)
            if recep.__len__()!=0:
                for a1 in recep:
                    if a1.doc_receprechaext.fecha_doc.year == fechadoc.year:
                        l=['Número de documento existente']
                        return render_to_response('form/form_adddetalle.html',  {'tipocliente':'0','form': form, 'form_name':nombre_form,'form_description':descripcion_form,
                                                                                 'accion':accion_form,'titulo':titulo_form,'controlador':controlador_form,
                                                                                 'cancelbtn':cancelbtn_form,'fecha_minima':fecha_cierre,'fecha_maxima':fecha_maxima,'error2':l},context_instance = RequestContext(request))
            try:

                doc.save()
                rpte.save() 
 
                return HttpResponseRedirect('/comerciax/casco/rechaexternos/view/'+pk_doc.__str__())  
            except Exception, e:
                exc_info = e.__str__() # sys.exc_info()[:1]
                c = exc_info.find("DETAIL:")
                
                if c < 0:
                    l=l+["Error Fatal."]
                else:
                    c = exc_info[c + 7:]
                    l=l+[c] 
                                     
                transaction.rollback()
                form = ReExternosForm(request.POST)
                return render_to_response('form/form_adddetalle.html',  {'tipocliente':'1','form': form, 'form_name':nombre_form,'form_description':descripcion_form,
                                                                         'accion':accion_form,'titulo':titulo_form,'controlador':controlador_form,
                                                                         'cancelbtn':cancelbtn_form,'fecha_minima':fecha_cierre,'fecha_maxima':fecha_maxima,'error2':l},context_instance = RequestContext(request))
            else:
                transaction.commit()
    else:
        form = ReExternosForm(initial={'fecha':fecha_cierre}) 
    return render_to_response('form/form_adddetalle.html',  {'tipocliente':'1','form': form, 'form_name':nombre_form,'form_description':descripcion_form,
                                                             'accion':accion_form,'titulo':titulo_form,'controlador':controlador_form,
                                                             'cancelbtn':cancelbtn_form,'fecha_minima':fecha_cierre,'fecha_maxima':fecha_maxima,'error2':c},context_instance = RequestContext(request))
    
@login_required
def rechaexternos_view(request,idrre):
    if not request.user.has_perm('casco.receprechext'):
        return render_to_response("denegado.html",locals(),context_instance = RequestContext(request))
    
    l=[]
    
    rrext = RecepRechaExt.objects.select_related().get(pk=idrre)
    rc_fecha=rrext.doc_receprechaext.fecha_doc.strftime("%d/%m/%Y")
    rc_cliente=rrext.cliente.nombre
    rc_nro=rrext.receprechaext_nro
    rc_observaciones=rrext.doc_receprechaext.observaciones
    filas = DetalleRRE.objects.select_related().filter(receprechaext=idrre).order_by('casco__producto__descripcion','casco__casco_nro')
    adiciono=True
    # Verificar si se puede editar. Se puede editar si todos los cascos relacionados con él el estado es Casco
    if rrext.procesado==True:
        editar=False
        adiciono=False
    else:
        editar=editar_documento(filas, idrre)

#    cantidades=DetalleRRE.objects.filter(receprechaext=idrre).values("casco__producto__id").annotate(Count('casco__producto__id')) 
    elementos_detalle=[]
    id1=''
    k=0
    k2=0
    for a1 in filas:
        if k!=0:
            if id1!=a1.casco.producto.id:
                elementos_detalle[k-1]['cantidad'] = k2
                k2=0
        causa=CausaRechazoRRE.objects.filter(detalle_rre=a1.id_detallerre)
        causa_rec=''
        for ss in causa:
            causa_rec=ss.causa.descripcion
        elementos_detalle+=[{'nro_ext':a1.nro_externo,'causa':causa_rec,'cliente':a1.receprechaext.cliente.nombre,'casco_id':a1.casco.id_casco,'casco_nro':a1.casco.casco_nro,'producto':a1.casco.producto,'productoid':a1.casco.producto.id}]
        k+=1
        k2+=1
        id1=a1.casco.producto.id  

    if k!=0:
        elementos_detalle[k-1]['cantidad'] = k2  
    
    return render_to_response('casco/viewrechaexternos.html',{'total_casco':k,'rc_nro':rc_nro,'fecha':rc_fecha,'cliente':rc_cliente,'observaciones':rc_observaciones,
                                                              'rc_id':idrre,'elementos_detalle':elementos_detalle, 'edito':editar,
                                                              'adiciono':adiciono,'error2':l},context_instance = RequestContext(request))

@login_required
@transaction.commit_on_success()
def rechaexternos_edit(request,idrre):
    if not request.user.has_perm('casco.receprechext'):
        return render_to_response("denegado.html",locals(),context_instance = RequestContext(request))
    
    
    nombre_form='Recepción de Cascos'
    descripcion_form='Recepción de Cascos Rechazados por Entidades Externas'
    titulo_form='Recepción de Cascos' 
    controlador_form='Recepción de Cascos'
    accion_form='/comerciax/casco/rechaexternos/edit/' + idrre +'/'
    cancelbtn_form='/comerciax/casco/rechaexternos/view/' + idrre +'/'
    fecha_cierre=Fechacierre.objects.get(almacen='c').fechaminima()
    fecha_maxima=Fechacierre.objects.get(almacen='c').fechamaxima()
    c=None
    l=[]
        
    if request.method == 'POST':
        form = ReExternosForm(request.POST)

        #rajuste = form.cleaned_data['ajuste']
        if form.is_valid():
            rpte=RecepRechaExt.objects.get(pk=idrre)
            object_doc=Doc.objects.get(pk=idrre)
            
            object_doc.fecha_doc=form.cleaned_data['fecha']
            fechadoc1=form.cleaned_data['fecha']
            object_doc.observaciones=form.cleaned_data['observaciones']
            object_doc.fecha_operacion=datetime.date.today()
         
            pk_user=User.objects.get(pk=request.user.id)
            # esto hay que cambiarlo y poner el operador
            #pk_doc=uuid4()
            

            object_doc.operador=pk_user
            
            
            rpte.receprechaext_nro=form.cleaned_data['nro']
            rc_nro1=form.cleaned_data['nro']
            rpte.nro_factura=form.cleaned_data['nrofactura']
            rpte.cliente=Cliente.objects.get(pk = form.data['cliente'])
            
            recep=RecepRechaExt.objects.filter(receprechaext_nro=rc_nro1)
            if recep.__len__()!=0:
                for a1 in recep:
                    if a1.doc_receprechaext.fecha_doc.year == fechadoc1.year and a1.pk!=idrre:
                        l=['Número de documento existente']
                        return render_to_response('form/form_adddetalle.html',  {'tipocliente':'0','form': form, 'form_name':nombre_form,'form_description':descripcion_form,
                                                                                 'accion':accion_form,'titulo':titulo_form,'controlador':controlador_form,
                                                                                 'cancelbtn':cancelbtn_form,'error2':l,'fecha_minima':fecha_cierre,'fecha_maxima':fecha_maxima},context_instance = RequestContext(request))        
            #RecepRechaExt.objects.create(doc_receprechaext=obj_doc,receprechaext_nro=nro,ptexternos_ajuste=ajuste,cliente=obj_cliente)
            try:
                object_doc.save()
                rpte.save() 
 
                return HttpResponseRedirect('/comerciax/casco/rechaexternos/view/'+idrre)  

            except Exception, e:
                exc_info = e.__str__() # sys.exc_info()[:1]
                c = exc_info.find("DETAIL:")
                
                if c < 0:
                    l=l+["Error Fatal."]
                else:
                    c = exc_info[c + 7:]
                    l=l+[c]
                    
                transaction.rollback()
                form = ReExternosForm(request.POST)
                return render_to_response('form/form_adddetalle.html',  {'tipocliente':'1','form': form, 'form_name':nombre_form,'form_description':descripcion_form,
                                                                         'accion':accion_form,'titulo':titulo_form,'controlador':controlador_form,
                                                                         'cancelbtn':cancelbtn_form,'fecha_minima':fecha_cierre,'fecha_maxima':fecha_maxima,'error2':l},context_instance = RequestContext(request))
            else:
                transaction.commit()     
    else:
        rpte = RecepRechaExt.objects.select_related().get(pk=idrre)
        form = ReExternosForm(initial={'nro':rpte.receprechaext_nro,'fecha':rpte.doc_receprechaext.fecha_doc,
                                       'nrofactura':rpte.nro_factura,'cliente':rpte.cliente,'observaciones':rpte.doc_receprechaext.observaciones})
    return render_to_response('form/form_edit.html',  {'tipocliente':'1','form': form, 'form_name':nombre_form,'form_description':descripcion_form,
                                                       'accion':accion_form,'titulo':titulo_form,'controlador':controlador_form,
                                                       'cancelbtn':cancelbtn_form,'fecha_minima':fecha_cierre,'fecha_maxima':fecha_maxima},context_instance = RequestContext(request))

@login_required
@transaction.commit_on_success()
def rechaexternos_del(request,idrre):
    if not request.user.has_perm('casco.receprechext'):
        return render_to_response("denegado.html",locals(),context_instance = RequestContext(request))
    
    
    try:
        filas = DetalleRRE.objects.filter(receprechaext=idrre)
        for canti in filas:
            actualiza_traza(canti.casco.id_casco,idrre)
            DetalleTransferencia.objects.filter(casco=canti.casco.id_casco).update(id_docrecepc='')
        Doc.objects.select_related().get(pk=idrre).delete()

        return HttpResponseRedirect('/comerciax/casco/rechaexternos/index')
    except Exception,e :
        transaction.rollback()
        l = ['Error al eliminar el documento']
        cp = RecepRechaExt.objects.select_related().get(pk=idrre)
        rc_fecha=cp.doc_receprechaext.fecha_doc.strftime("%d/%m/%Y")

        rc_nro=cp.receprechaext_nro
        editar=1
        rc_observaciones=cp.doc_receprechaext.observaciones
        filas = DetalleRRE.objects.select_related().filter(receprechaext=idrre).order_by('admincomerciax_producto.descripcion','casco_casco.casco_nro')

        return render_to_response('casco/viewrechaexternos.html',{'rc_nro':rc_nro,'fecha':rc_fecha,'observaciones':rc_observaciones,'rc_id':idrre,'elementos_detalle':filas, 'edito':editar,'error2':l},context_instance = RequestContext(request))

    else:
        
        transaction.commit()
#############################################################
#        DETALLE RECEPCION RECHAZO A CLIENTES EXTRENOS      #
#############################################################

@login_required
@transaction.commit_on_success()
def detalleRRE_add(request,idrre):
    if not request.user.has_perm('casco.receprechext'):
        return render_to_response("denegado.html",locals(),context_instance = RequestContext(request))
    
    titulo_form='Recepción de Cascos' 
    controlador_form='Recepción de Cascos'
    descripcion_form='Recepción de Cascos Rechazados por Entidades Externas'
    
    accion_form='detalleRRE_add'
    cancelbtn_form='/comerciax/casco/rechaexternos/view/'+idrre
    l=[]
    
    pte=RecepRechaExt.objects.get(pk=idrre)
    causas=CausasRechazo.objects.all()
    estado="Casco"
    medidas=Producto.objects.all() 
#    transfe=DetalleTransferencia.objects.select_related().filter(transf__destino=pte.cliente,id_docrecepc='').order_by('casco__producto','casco__casco_nro')
    #cascos=Casco.objects.select_related().filter(estado_actual=Estados.estados["Casco"]).order_by('admincomerciax_producto.descripcion','casco_nro')
    if request.method == 'POST':
        seleccion=request.POST.keys()
        k=0
        nro=RecepRechaExt.objects.get(pk=idrre).doc_receprechaext
        causa=request.POST["causa"]
        while True:
            if k==seleccion.__len__():
                break
            casco=Casco.objects.filter(pk=seleccion[k])

            if casco.count()!=0:
                '''
                Los selecionados los cambio de estado, agregar a detalle del documento y actualizar trazabilidad
                '''
                detalle=DetalleRRE()
                pk_detalle=uuid4()
                detalle.id_detallerre=pk_detalle
                detalle.receprechaext=RecepRechaExt.objects.get(pk=idrre)
                detalle.casco=Casco.objects.get(pk=seleccion[k])
                nroc=Casco.objects.get(pk=seleccion[k]).casco_nro
                try:
                    detalle.save()
                except Exception, e:
                    exc_info = e.__str__() # sys.exc_info()[:1]
                    c = exc_info.find("DETAIL:")
                    
                    if c < 0:
                        l=l+["Error Fatal."]
                    else:
                        l=['El casco ' + str(nroc) +' ya existe en este documento']
                        c = exc_info[c + 7:]
                        transaction.rollback()
                        return render_to_response('casco/form_seleccion.html', {'este':True,'estado':estado,'title':titulo_form,'controlador':controlador_form,'accion':accion_form,
                                                      'cancelbtn':cancelbtn_form, 'nro':pte.receprechaext_nro,'form_description':descripcion_form,
                                                      'fecha':pte.doc_receprechaext.fecha_doc.strftime("%d/%m/%Y"),'observaciones':pte.doc_receprechaext.observaciones,
                                                      'rc_id':idrre,'causas_rechazo':causas,'muestra_causa':True,'medidarec':medidas,'estado':'Transferencia','id_clieext':pte.cliente.id},context_instance = RequestContext(request))

                
                Casco.objects.filter(pk=seleccion[k]).update(estado_actual="REE",fecha=RecepRechaExt.objects.get(pk=idrre).doc_receprechaext.fecha_doc)
                add_trazabilidad(seleccion[k], idrre, "REE")
                
                DetalleTransferencia.objects.filter(casco=Casco.objects.get(pk=seleccion[k])).update(id_docrecepc=nro,rechazado=True)
                
                docu=DetalleTransferencia.objects.get(casco=Casco.objects.get(pk=seleccion[k]))
                
                if DetalleTransferencia.objects.filter(transf=docu.transf,id_docrecepc='').count()==0:
                    Transferencia.objects.filter(transferencia_nro=DetalleTransferencia.objects.get(casco=seleccion[k]).transf).update(cerrada=True)
        
                if causa.__len__()!=0:
                    causaer=CausaRechazoRRE()
                    obj_detalle = DetalleRRE.objects.get(pk = pk_detalle)
                    causaer.detalle_rre=obj_detalle
                    causaer.causa=CausasRechazo.objects.get(pk=causa)
                    causaer.save()
                
            k=k+1
            
        if request.POST.__contains__('submit1'):
            #cascos=Casco.objects.select_related().filter(estado_actual=Estados.estados["Casco"]).order_by('admincomerciax_producto.descripcion','casco_nro')
            
#            transfe=DetalleTransferencia.objects.select_related().filter(transf__destino=pte.cliente,id_docrecepc='').order_by('casco__producto','casco__casco_nro')
            return render_to_response('casco/form_seleccion.html', {'este':True,'estado':estado,'title':titulo_form,'controlador':controlador_form,'accion':accion_form,
                                                      'cancelbtn':cancelbtn_form, 'nro':pte.receprechaext_nro,'form_description':descripcion_form,
                                                      'fecha':pte.doc_receprechaext.fecha_doc.strftime("%d/%m/%Y"),'observaciones':pte.doc_receprechaext.observaciones,
                                                      'rc_id':idrre,'causas_rechazo':causas,'muestra_causa':True,'medidarec':medidas,'estado':'Transferencia','id_clieext':pte.cliente.id},context_instance = RequestContext(request))
        else:
            return HttpResponseRedirect('/comerciax/casco/rechaexternos/view/' + idrre)
    

    causas=CausasRechazo.objects.all() 
    return render_to_response('casco/form_seleccion.html', {'este':True,'estado':estado,'title':titulo_form,'controlador':controlador_form,'accion':accion_form,
                                                      'cancelbtn':cancelbtn_form, 'nro':pte.receprechaext_nro,'form_description':descripcion_form,
                                                      'fecha':pte.doc_receprechaext.fecha_doc.strftime("%d/%m/%Y"),'observaciones':pte.doc_receprechaext.observaciones,
                                                      'rc_id':idrre,'causas_rechazo':causas,'muestra_causa':True,'medidarec':medidas,'estado':'Transferencia','id_clieext':pte.cliente.id},context_instance = RequestContext(request))


@login_required
def detalleRRE_delete(request,idcasco,idrre):
    if not request.user.has_perm('casco.receprechext'):
        return render_to_response("denegado.html",locals(),context_instance = RequestContext(request))
    
    casco=Casco.objects.select_related().get(pk=idcasco)
    nro=casco.casco_nro
    
    if eliminar_detalle_sino(casco.id_casco,idrre):
        DetalleRRE.objects.get(casco=idcasco).delete()
        actualiza_traza(idcasco,idrre)
        
        DetalleTransferencia.objects.filter(casco=idcasco).update(id_docrecepc='')
        
        Transferencia.objects.filter(transferencia_nro=DetalleTransferencia.objects.get(casco=idcasco).transf).update(cerrada=False)

#        detallerre = DetalleRRE.objects.select_related().filter(receprechaext=idrre).order_by('admincomerciax_producto.descripcion','casco_casco.casco_nro')
        filas = DetalleRRE.objects.select_related().filter(receprechaext=idrre).order_by('casco__producto__descripcion','casco__casco_nro')
        total_casco=str(filas.count())
            
        elementos_detalle=[]
        id1=''
        k=0
        k2=0
        for a1 in filas:
            causa=CausaRechazoRRE.objects.filter(pk=a1.id_detallerre)
            if causa.__len__()==0:
                causa1=''
            else:
                causa1=a1.causarechazorre.causa.descripcion
            if k!=0:
                if id1!=a1.casco.producto.id:
#                    elementos_detalle[k-1]['cantidad'] = elementos_detalle[k-1]['productoid']
                    elementos_detalle[k-1]['cantidad'] = k2
                    k2=0
                    
            elementos_detalle+=[{'total_casco':total_casco,
                                 'id_doc':a1.receprechaext.doc_receprechaext.id_doc,'casco_id':a1.casco.id_casco,
                                 'casco_nro':a1.casco.casco_nro,'producto':a1.casco.producto.descripcion,
                                 'productoid':a1.casco.producto.id,'cliente':a1.casco.get_cliente(),
                                 'causa':causa1,'nro_ext':a1.nro_externo}]
            k+=1
            id1=a1.casco.producto.id 
            k2+=1
            
        if k!=0:
            elementos_detalle[k-1]['cantidad'] = k2
        return HttpResponse(simplejson.dumps(elementos_detalle),content_type = 'application/javascript; charset=utf8')
#        
#        
#        
#        
#        
#        total_casco = detallerre.count()
#        lista_valores=[]
#        for detalles in detallerre:
#            idpk=detalles.id_detallerre
#            causa=CausaRechazoRRE.objects.filter(pk=idpk)
#            medidacasco=DetalleRRE.objects.select_related().get(pk=idpk)
#            medidac=medidacasco.casco.producto.descripcion
#            cliente=medidacasco.casco.get_cliente()
#            if causa.__len__()==0:
#                causa1=''
#            else:
#                causa1=detalles.causarechazorre.causa.descripcion
#            lista_valores=lista_valores+[{"cliente":cliente,"nro_ext":detalles.nro_externo,"pk":detalles.id_detallerre,
#                                          "producto":medidac,"casco_nro":detalles.casco.casco_nro,
#                                          "casco_id":detalles.casco.id_casco,"total_casco":total_casco,
#                                          "id_doc":detalles.receprechaext.doc_receprechaext.id_doc,"causa":causa1}] 
#        #"pk":detalles.id_detalleer,"nrocasco":detalles.casco.casco_nro,"medida":detalles.casco.producto,"idcasco":detalles.casco.id_casco,"docum":detalles.errro_revision.doc_errorrecepcion.id_doc,"causa":causa1}]
#        return HttpResponse(simplejson.dumps(lista_valores),content_type = 'application/javascript; charset=utf8')
        
        #return HttpResponseRedirect("/comerciax/casco/cascocc/view/" + idrre)
    else:
        error2 = "No se puede eliminar el casco " + str(nro) + " ya que su estado ha cambiado "
        return HttpResponse(json.dumps({'error':True, 'message':error2}),mimetype=u'application/json')
        #return cascocc_view(request, idrre,error2)

@login_required
@transaction.commit_on_success()
def detalleRRE_edit(request,idcasco,idrre):
    if not request.user.has_perm('casco.receprechext'):
        return render_to_response("denegado.html",locals(),context_instance = RequestContext(request))
    
    c=None
    l=[]
    
    nombre_form='Recepción de Cascos'
    descripcion_form='Recepción de Cascos Rechazados por Entidades Externas'
    titulo_form='Recepción de Cascos' 
    controlador_form='Recepción de Cascos'
    accion_form='detalleRRE_edit/' + idrre +'/' +idcasco
    cancelbtn_form='/comerciax/casco/rechaexternos/view/' + idrre +'/'

    if request.method == 'POST':
        form = DetalleRREForm(request.POST)
        
        if form.is_valid():
            
            
            DetalleRRE.objects.filter(casco=idcasco,receprechaext=idrre).update(nro_externo=form.data['nro_externo'])
            er=DetalleRRE.objects.get(casco=idcasco,receprechaext=idrre)
            
            causa=CausasRechazo.objects.filter(pk = form.data['causa'])
            
            try:
                er.save()
                causarer=CausaRechazoRRE.objects.filter(pk=er.id_detallerre)
                
                if causarer.__len__()==0 and causa.__len__()!=0:
                    '''Se añade la causa '''
                    causarersave=CausaRechazoRRE()
                    causarersave.detalle_rre=DetalleRRE.objects.get(pk = er.id_detallerre)
                    causarersave.causa=CausasRechazo.objects.get(pk=causa)
                    causarersave.save()
                elif causarer.__len__()!=0 and causa.__len__()==0:
                    '''Se quita la causa '''
                    CausaRechazoRRE.objects.get(pk = er.id_detallerre).delete()
                else:
                    causarersave=CausaRechazoRRE.objects.get(pk=er.id_detallerre)
                    causarersave.causa=CausasRechazo.objects.get(pk=causa)
                    causarersave.save()
                return rechaexternos_view(request, idrre)
            except Exception, e:
                exc_info = e.__str__() # sys.exc_info()[:1]
                c = exc_info.find("DETAIL:")
                if c < 0:
                    l = l + ["Error Fatal."]
                else:
                    c = exc_info[c + 7:]
                    l=l+[c]
                transaction.rollback()
                form = DetalleRREForm(request.POST)
                return render_to_response("form/form_edit.html",{'tipocliente':'1','form':form,'title':titulo_form, 'form_name': nombre_form,'form_description':descripcion_form,'controlador':controlador_form,'accion':accion_form
                                                         , 'cancelbtn':cancelbtn_form,'error2':l},context_instance = RequestContext(request))
            else:
                transaction.commit()
    else:   
        rer =DetalleRRE.objects.select_related().get(casco=idcasco,receprechaext=idrre)
        causaer=CausaRechazoRRE.objects.filter(pk=rer.id_detallerre)
        if causaer.__len__()!=0:
            cusarer =CausaRechazoRRE.objects.get(pk=rer.id_detallerre)
            form = DetalleRREForm(initial={'nro':rer.casco.casco_nro,'causa':cusarer.causa})
        else:
            form = DetalleRREForm(initial={'nro':rer.casco.casco_nro,'causa':CausasRechazo.objects.all()})
        return render_to_response('form/form_edit.html',  {'tipocliente':'1','form': form, 'form_name':nombre_form,'form_description':descripcion_form,'accion':accion_form,'titulo':titulo_form,'controlador':controlador_form,'cancelbtn':cancelbtn_form},context_instance = RequestContext(request))
    return rechaexternos_view(request, idrre)  

#############################################################
#        RECEPCION DE CASCO A CLIENTES EXTRENOS           #
#############################################################
'''
ESTOS SON LOS CASCOS QUE SE TRANFIRIERON NO SE RECAPARON  Y NO SON RECHAZAD.
'''
@login_required
def get_reca_list(request):
    #prepare the params
    try:
        fecha_desde=Fecha_Ver.objects.get()
    except Exception, e:
        fecha_desde=None
    if  fecha_desde == None:  
        querySet = RecepCascoExt.objects.select_related().all().order_by('-doc_recepcascoext__fecha_doc')
    else:
        querySet = RecepCascoExt.objects.select_related().filter(doc_recepcascoext__fecha_doc__gte=fecha_desde.fecha).order_by('-doc_recepcascoext__fecha_doc')
    for a1 in querySet:
        a1.recepcascoext_nro
    #querySet = querySet.filter(doc__fecha_doc__year=2010)
        
    columnIndexNameMap = {0: '-casco_doc.fecha_doc',1: 'recepcascoext_nro',2:'casco_doc.fecha_doc',3:'admincomerciax.cliente_nombre'}
    #searchableColumns = ['cliente__nombre','recepcioncliente_nro']
    searchableColumns = ['recepcascoext_nro','doc_recepcascoext__fecha_doc','cliente__nombre']
    #path to template used to generate json
    jsonTemplatePath = 'casco/json/json_cre.txt'

    #call to generic function from utils
    return get_datatables_records(request, querySet, columnIndexNameMap, searchableColumns, jsonTemplatePath)

@login_required
def cascoexternos_index(request):
    if not request.user.has_perm('casco.recepcascoext'):
        return render_to_response("denegado.html",locals(),context_instance = RequestContext(request))
    
    return render_to_response('casco/cascoexternosindex.html',locals(),context_instance = RequestContext(request))

@login_required
@transaction.commit_on_success()
def cascoexternos_add(request):
    if not request.user.has_perm('casco.recepcascoext'):
        return render_to_response("denegado.html",locals(),context_instance = RequestContext(request))
    
    nombre_form='Recepción de Cascos'
    descripcion_form='Recepción de Cascos No Recapados por Entidades Externas'
    titulo_form='Recepción de Cascos' 
    controlador_form='Recepción de Cascos'
    accion_form='/comerciax/casco/cascoexternos/add'
    cancelbtn_form='/comerciax/casco/cascoexternos/index'
    fecha_cierre=Fechacierre.objects.get(almacen='c').fechaminima()
    fecha_maxima=Fechacierre.objects.get(almacen='c').fechamaxima()
    c=None
    l=[]
    if request.method == 'POST':
        form = CaExternosForm(request.POST)

        #rajuste = form.cleaned_data['ajuste']
        if form.is_valid():
            doc=Doc()

            fechadoc=form.cleaned_data['fecha']
            doc.fecha_doc=fechadoc
            doc.observaciones=form.cleaned_data['observaciones']
            doc.fecha_operacion=datetime.date.today()
            doc.fecha_doc=fechadoc
            doc.tipo_doc='18'
         
            pk_user=User.objects.get(pk=request.user.id)
            # esto hay que cambiarlo y poner el operador
            pk_doc=uuid4()
            

            doc.id_doc = pk_doc 
            doc.operador=pk_user
            
            
            rpte=RecepCascoExt()
            
            rc_nro=form.cleaned_data['nro']
            
            obj_cliente = Cliente.objects.get(pk = form.data['cliente']) 
            rpte.recepcascoext_nro=rc_nro
            rpte.nro_factura=form.cleaned_data['nrofactura']
            rpte.cliente=obj_cliente
            rpte.doc_recepcascoext=doc
            recep=RecepCascoExt.objects.filter(recepcascoext_nro=rc_nro)
            if recep.__len__()!=0:
                for a1 in recep:
                    if a1.doc_recepcascoext.fecha_doc.year == fechadoc.year:
                        l=['Número de documento existente']
                        return render_to_response('form/form_adddetalle.html',  {'tipocliente':'0','form': form, 'form_name':nombre_form,'form_description':descripcion_form,
                                                                                 'accion':accion_form,'titulo':titulo_form,'controlador':controlador_form,
                                                                                 'cancelbtn':cancelbtn_form,'fecha_minima':fecha_cierre,'fecha_maxima':fecha_maxima,'error2':l},context_instance = RequestContext(request))
            try:

                doc.save()
                rpte.save() 
 
                return HttpResponseRedirect('/comerciax/casco/cascoexternos/view/'+pk_doc.__str__())  
            except Exception, e:
                exc_info = e.__str__() # sys.exc_info()[:1]
                c = exc_info.find("DETAIL:")
                
                if c < 0:
                    l=l+["Error Fatal."]
                else:
                    c = exc_info[c + 7:]
                    l=l+[c] 
                                     
                transaction.rollback()
                form = CaExternosForm(request.POST)
                return render_to_response('form/form_adddetalle.html',  {'tipocliente':'1','form': form, 'form_name':nombre_form,'form_description':descripcion_form,
                                                                         'accion':accion_form,'titulo':titulo_form,'controlador':controlador_form,
                                                                         'cancelbtn':cancelbtn_form,'fecha_minima':fecha_cierre,'fecha_maxima':fecha_maxima,'error2':l},context_instance = RequestContext(request))
            else:
                transaction.commit()
    else:
        form = CaExternosForm(initial={'fecha':fecha_cierre}) 
    return render_to_response('form/form_adddetalle.html',  {'tipocliente':'1','form': form, 'form_name':nombre_form,'form_description':descripcion_form,
                                                             'accion':accion_form,'titulo':titulo_form,'controlador':controlador_form,
                                                             'cancelbtn':cancelbtn_form,'fecha_minima':fecha_cierre,'fecha_maxima':fecha_maxima,'error2':c},context_instance = RequestContext(request))
    
@login_required
def cascoexternos_view(request,idrce):
    if not request.user.has_perm('casco.recepcascoext'):
        return render_to_response("denegado.html",locals(),context_instance = RequestContext(request))
    
    l=[]
    
    rrext = RecepCascoExt.objects.select_related().get(pk=idrce)
    rc_fecha=rrext.doc_recepcascoext.fecha_doc.strftime("%d/%m/%Y")
    rc_cliente=rrext.cliente.nombre
    rc_nro=rrext.recepcascoext_nro
    rc_observaciones=rrext.doc_recepcascoext.observaciones
    filas = DetalleRCE.objects.select_related().filter(recepcascoext=idrce).order_by('casco__producto__descripcion','casco__casco_nro')
    adiciono=True
    # Verificar si se puede editar. Se puede editar si todos los cascos relacionados con él el estado es Casco
    if rrext.procesado==True:
        editar=False
        adiciono=False
    else:
        editar=editar_documento(filas, idrce)
        
#    cantidades=DetalleRCE.objects.filter(recepcascoext=idrce).values("casco__producto__id").annotate(Count('casco__producto__id')) 
    elementos_detalle=[]
    id1=''
    k=0
    k2=0
    for a1 in filas:
        if k!=0:
            if id1!=a1.casco.producto.id:
                elementos_detalle[k-1]['cantidad'] = k2
                k2=0
        elementos_detalle+=[{'nro_ext':a1.nro_externo,'cliente':a1.recepcascoext.cliente.nombre,'casco_id':a1.casco.id_casco,'casco_nro':a1.casco.casco_nro,'producto':a1.casco.producto,'productoid':a1.casco.producto.id}]
        k+=1
        k2+=1
        id1=a1.casco.producto.id 
    if k!=0: 
        elementos_detalle[k-1]['cantidad'] = k2
    
    return render_to_response('casco/viewcascoexternos.html',{'total_casco':k,'rc_nro':rc_nro,'fecha':rc_fecha,'cliente':rc_cliente,'observaciones':rc_observaciones,
                                                              'rc_id':idrce,'elementos_detalle':elementos_detalle, 'edito':editar,'adiciono':adiciono,'error2':l},context_instance = RequestContext(request))

@login_required
@transaction.commit_on_success()
def cascoexternos_edit(request,idrce):
    if not request.user.has_perm('casco.recepcascoext'):
        return render_to_response("denegado.html",locals(),context_instance = RequestContext(request))
    
    
    nombre_form='Recepción de Cascos'
    descripcion_form='Recepción de Cascos Rechazados por Entidades Externas'
    titulo_form='Recepción de Cascos' 
    controlador_form='Recepción de Cascos'
    accion_form='/comerciax/casco/cascoexternos/view/' + idrce +'/'
    cancelbtn_form='/comerciax/casco/cascoexternos/view/' + idrce +'/'
    fecha_cierre=Fechacierre.objects.get(almacen='c').fechaminima()
    fecha_maxima=Fechacierre.objects.get(almacen='c').fechamaxima()
    c=None
    l=[]
        
    if request.method == 'POST':
        form = CaExternosForm(request.POST)

        #rajuste = form.cleaned_data['ajuste']
        if form.is_valid():
            rpte=RecepCascoExt.objects.get(pk=idrce)
            object_doc=Doc.objects.get(pk=idrce)
            
            object_doc.fecha_doc=form.cleaned_data['fecha']
            fechadoc1=form.cleaned_data['fecha']
            object_doc.observaciones=form.cleaned_data['observaciones']
            object_doc.fecha_operacion=datetime.date.today()
         
            pk_user=User.objects.get(pk=request.user.id)
            # esto hay que cambiarlo y poner el operador
            #pk_doc=uuid4()
            

            object_doc.operador=pk_user
            
            
            rpte.recepcascoext_nro=form.cleaned_data['nro']
            rc_nro1=form.cleaned_data['nro']
            rpte.nro_factura=form.cleaned_data['nrofactura']
            rpte.cliente=Cliente.objects.get(pk = form.data['cliente'])
            
            recep=RecepCascoExt.objects.filter(recepcascoext_nro=rc_nro1)
            if recep.__len__()!=0:
                for a1 in recep:
                    if a1.doc_recepcascoext.fecha_doc.year == fechadoc1.year and a1.pk!=idrce:
                        l=['Número de documento existente']
                        return render_to_response('form/form_adddetalle.html',  {'tipocliente':'0','form': form, 'form_name':nombre_form,'form_description':descripcion_form,
                                                                                 'accion':accion_form,'titulo':titulo_form,'controlador':controlador_form,
                                                                                 'cancelbtn':cancelbtn_form,'error2':l,'fecha_minima':fecha_cierre,'fecha_maxima':fecha_maxima},context_instance = RequestContext(request))        
            #RecepCascoExt.objects.create(doc_RecepCascoExt=obj_doc,RecepCascoExt_nro=nro,ptexternos_ajuste=ajuste,cliente=obj_cliente)
            try:
                object_doc.save()
                rpte.save() 
 
                return HttpResponseRedirect('/comerciax/casco/cascoexternos/view/'+idrce)  

            except Exception, e:
                exc_info = e.__str__() # sys.exc_info()[:1]
                c = exc_info.find("DETAIL:")
                
                if c < 0:
                    l=l+["Error Fatal."]
                else:
                    c = exc_info[c + 7:]
                    l=l+[c]
                    
                transaction.rollback()
                form = CaExternosForm(request.POST)
                return render_to_response('form/form_adddetalle.html',  {'tipocliente':'1','form': form, 'form_name':nombre_form,'form_description':descripcion_form,
                                                                         'accion':accion_form,'titulo':titulo_form,'controlador':controlador_form,
                                                                         'cancelbtn':cancelbtn_form,'fecha_minima':fecha_cierre,'fecha_maxima':fecha_maxima,'error2':l},context_instance = RequestContext(request))
            else:
                transaction.commit()     
    else:
        rpte = RecepCascoExt.objects.select_related().get(pk=idrce)
        form = CaExternosForm(initial={'nro':rpte.recepcascoext_nro,'fecha':rpte.doc_recepcascoext.fecha_doc,'nrofactura':rpte.nro_factura,
                                             'cliente':rpte.cliente,'observaciones':rpte.doc_recepcascoext.observaciones})
    return render_to_response('form/form_edit.html',  {'tipocliente':'1','form': form, 'form_name':nombre_form,'form_description':descripcion_form,
                                                       'accion':accion_form,'titulo':titulo_form,'controlador':controlador_form,
                                                       'cancelbtn':cancelbtn_form,'fecha_minima':fecha_cierre,'fecha_maxima':fecha_maxima},context_instance = RequestContext(request))



@login_required
@transaction.commit_on_success()
def cascoexternos_del(request,idrce):
    if not request.user.has_perm('casco.recepcascoext'):
        return render_to_response("denegado.html",locals(),context_instance = RequestContext(request))
    try:
        filas = DetalleRRE.objects.filter(receprechaext=idrce)
        for canti in filas:
            actualiza_traza(canti.casco.id_casco,idrce)
            DetalleTransferencia.objects.filter(casco=canti.casco.id_casco).update(id_docrecepc='')
        Doc.objects.select_related().get(pk=idrce).delete()
        return HttpResponseRedirect('/comerciax/casco/cascoexternos/index')
    except Exception,e :
        transaction.rollback()
        l = ['Error al eliminar el documento']
        cp = RecepCascoExt.objects.select_related().get(pk=idrce)
        rc_fecha=cp.doc_recepcascoext.fecha_doc.strftime("%d/%m/%Y")

        rc_nro=cp.recepcascoext_nro
        editar=1
        rc_observaciones=cp.doc_recepcascoext.observaciones
        filas = DetalleRRE.objects.select_related().filter(RecepCascoExt=idrce).order_by('admincomerciax_producto.descripcion','casco_casco.casco_nro')

        return render_to_response('casco/viewcascoexternos.html',{'rc_nro':rc_nro,'fecha':rc_fecha,'observaciones':rc_observaciones,'rc_id':idrce,'elementos_detalle':filas, 'edito':editar,'error2':l},context_instance = RequestContext(request))
    else:
        transaction.commit()
#############################################################
#        DETALLE RECEPCION CASCOS A CLIENTES EXTRENOS      #
#############################################################

@login_required
@transaction.commit_on_success()
def detalleRCE_add(request,idrce):
    if not request.user.has_perm('casco.recepcascoext'):
        return render_to_response("denegado.html",locals(),context_instance = RequestContext(request))
    
    titulo_form='Recepción de Cascos' 
    controlador_form='Recepción de Cascos'
    descripcion_form='Recepción de Cascos Rechazados por Entidades Externas'
    
    accion_form='detalleRCE_add'
    cancelbtn_form='/comerciax/casco/cascoexternos/view/'+idrce
    l=[]
    
    pte=RecepCascoExt.objects.get(pk=idrce)
    estado="Casco"
    medidas=Producto.objects.all() 
#    transfe=DetalleTransferencia.objects.select_related().filter(transf__destino=pte.cliente,id_docrecepc='').order_by('casco__producto','casco__casco_nro')
    #cascos=Casco.objects.select_related().filter(estado_actual=Estados.estados["Casco"]).order_by('admincomerciax_producto.descripcion','casco_nro')
    if request.method == 'POST':
        seleccion=request.POST.keys()
        k=0
        nro=RecepCascoExt.objects.get(pk=idrce).doc_recepcascoext
        while True:
            if k==seleccion.__len__():
                break
            casco=Casco.objects.filter(pk=seleccion[k])

            if casco.count()!=0:
                '''
                Los selecionados los cambio de estado, agregar a detalle del documento y actualizar trazabilidad
                '''
                detalle=DetalleRCE()
                pk_detalle=uuid4()
                detalle.id_detallerce=pk_detalle
                detalle.recepcascoext=RecepCascoExt.objects.get(pk=idrce)
                detalle.casco=Casco.objects.get(pk=seleccion[k])
                nroc=Casco.objects.get(pk=seleccion[k]).casco_nro
                try:
                    detalle.save()
                except Exception, e:
                    exc_info = e.__str__() # sys.exc_info()[:1]
                    c = exc_info.find("DETAIL:")
                    
                    if c < 0:
                        l=l+["Error Fatal."]
                    else:
                        l=['El casco ' + str(nroc) +' ya existe en este documento']
                        c = exc_info[c + 7:]
                        transaction.rollback()
                        return render_to_response('casco/form_seleccion.html', {'este':True,'estado':estado,'title':titulo_form,'controlador':controlador_form,'accion':accion_form,
                                                      'cancelbtn':cancelbtn_form, 'nro':pte.recepcascoext_nro,'form_description':descripcion_form,
                                                      'fecha':pte.doc_recepcascoext.fecha_doc.strftime("%d/%m/%Y"),'observaciones':pte.doc_recepcascoext.observaciones,
                                                      'rc_id':idrce,'muestra_causa':False,'medidarec':medidas,'estado':'Transferencia','id_clieext':pte.cliente.id},context_instance = RequestContext(request))

                Casco.objects.filter(pk=seleccion[k]).update(estado_actual="Casco",fecha=RecepCascoExt.objects.select_related().get(pk=idrce).doc_recepcascoext.fecha_doc)
                add_trazabilidad(seleccion[k], idrce, "Casco")
                
                DetalleTransferencia.objects.filter(casco=Casco.objects.get(pk=seleccion[k])).update(id_docrecepc=nro,rechazado=True)
                
                docu=DetalleTransferencia.objects.get(casco=Casco.objects.get(pk=seleccion[k]))
                
                if DetalleTransferencia.objects.filter(transf=docu.transf,id_docrecepc='').count()==0:
                    Transferencia.objects.filter(transferencia_nro=DetalleTransferencia.objects.get(casco=seleccion[k]).transf).update(cerrada=True)

                
            k=k+1
            
        if request.POST.__contains__('submit1'):
            #cascos=Casco.objects.select_related().filter(estado_actual=Estados.estados["Casco"]).order_by('admincomerciax_producto.descripcion','casco_nro')
            
#            transfe=DetalleTransferencia.objects.select_related().filter(transf__destino=pte.cliente,id_docrecepc='').order_by('casco__producto','casco__casco_nro')
            return render_to_response('casco/form_seleccion.html', {'este':True,'estado':estado,'title':titulo_form,'controlador':controlador_form,'accion':accion_form,
                                                      'cancelbtn':cancelbtn_form, 'nro':pte.recepcascoext_nro,'form_description':descripcion_form,
                                                      'fecha':pte.doc_recepcascoext.fecha_doc.strftime("%d/%m/%Y"),'observaciones':pte.doc_recepcascoext.observaciones,
                                                      'rc_id':idrce,'muestra_causa':False,'medidarec':medidas,'estado':'Transferencia','id_clieext':pte.cliente.id},context_instance = RequestContext(request))
        else:
            return HttpResponseRedirect('/comerciax/casco/cascoexternos/view/' + idrce)
    

    causas=CausasRechazo.objects.all() 
    return render_to_response('casco/form_seleccion.html', {'este':True,'estado':estado,'title':titulo_form,'controlador':controlador_form,'accion':accion_form,
                                                      'cancelbtn':cancelbtn_form, 'nro':pte.recepcascoext_nro,'form_description':descripcion_form,
                                                      'fecha':pte.doc_recepcascoext.fecha_doc.strftime("%d/%m/%Y"),'observaciones':pte.doc_recepcascoext.observaciones,
                                                      'rc_id':idrce,'muestra_causa':False,'medidarec':medidas,'estado':'Transferencia','id_clieext':pte.cliente.id},context_instance = RequestContext(request))


@login_required
def detalleRCE_delete(request,idcasco,idrce):
    if not request.user.has_perm('casco.recepcascoext'):
        return render_to_response("denegado.html",locals(),context_instance = RequestContext(request))
    
    casco=Casco.objects.select_related().get(pk=idcasco)
    nro=casco.casco_nro
    
    if eliminar_detalle_sino(casco.id_casco,idrce):
        DetalleRCE.objects.get(casco=idcasco).delete()
        actualiza_traza(idcasco,idrce)
        
        DetalleTransferencia.objects.filter(casco=idcasco).update(id_docrecepc='')
        
        Transferencia.objects.filter(transferencia_nro=DetalleTransferencia.objects.get(casco=idcasco).transf).update(cerrada=False)

        filas = DetalleRCE.objects.select_related().filter(recepcascoext=idrce).order_by('casco__producto__descripcion','casco__casco_nro')
#        cantidades=DetalleRCE.objects.filter(recepcascoext=idrce).values("casco__producto__id").annotate(Count('casco__producto__id')) 
        total_casco=str(filas.count())
        elementos_detalle=[]
        id1=''
        k=0
        k2=0
        for a1 in filas:
            if k!=0:
                if id1!=a1.casco.producto.id:
                    elementos_detalle[k-1]['cantidad'] = k2
                    
            elementos_detalle+=[{'total_casco':total_casco,'id_doc':a1.recepcascoext.doc_recepcascoext.id_doc,'nro_ext':a1.nro_externo,
                                 'casco_id':a1.casco.id_casco,'casco_nro':a1.casco.casco_nro,'cliente':a1.recepcascoext.cliente.nombre,
                                 'producto':a1.casco.producto.descripcion,'productoid':a1.casco.producto.id}]
            k+=1
            k2+=1
            id1=a1.casco.producto.id  
        
        if k!=0:
            elementos_detalle[k-1]['cantidad'] = k2 
        return HttpResponse(simplejson.dumps(elementos_detalle),content_type = 'application/javascript; charset=utf8')
    else:
        error2 = "No se puede eliminar el casco " + str(nro) + " ya que su estado ha cambiado "
        return HttpResponse(json.dumps({'error':True, 'message':error2}),mimetype=u'application/json')
        #return cascocc_view(request, idrre,error2)

@login_required
@transaction.commit_on_success()
def detalleRCE_edit(request,idcasco,idrce):
    if not request.user.has_perm('casco.recepcascoext'):
        return render_to_response("denegado.html",locals(),context_instance = RequestContext(request))
    
    c=None
    l=[]
    
    nombre_form='Recepción de Cascos'
    descripcion_form='Recepción de Cascos no Procesados por Entidades Externas'
    titulo_form='Recepción de Cascos' 
    controlador_form='Recepción de Cascos'
    accion_form='detalleRCE_edit/' + idcasco +'/' +idrce
    cancelbtn_form='/comerciax/casco/cascoexternos/view/' + idrce +'/'

    if request.method == 'POST':
        form = DetalleRCEForm(request.POST)
        
        if form.is_valid():
            DetalleRCE.objects.filter(casco=idcasco,recepcascoext=idrce).update(nro_externo=form.data['nro_externo'])
            er=DetalleRCE.objects.get(casco=idcasco,recepcascoext=idrce)
            try:
                er.save()
                return cascoexternos_view(request, idrce)
            except Exception, e:
                exc_info = e.__str__() # sys.exc_info()[:1]
                c = exc_info.find("DETAIL:")
                if c < 0:
                    l = l + ["Error Fatal."]
                else:
                    c = exc_info[c + 7:]
                    l=l+[c]
                transaction.rollback()
                form = DetalleRCEForm(request.POST)
                return render_to_response("form/form_edit.html",{'tipocliente':'1','form':form,'title':titulo_form, 'form_name': nombre_form,'form_description':descripcion_form,'controlador':controlador_form,'accion':accion_form
                                                         , 'cancelbtn':cancelbtn_form,'error2':l},context_instance = RequestContext(request))
            else:
                transaction.commit()
    else:   
        rer =DetalleRCE.objects.select_related().get(casco=idcasco,recepcascoext=idrce)
        
        form = DetalleRCEForm(initial={'nro':rer.casco.casco_nro,'causa':CausasRechazo.objects.all()})
        return render_to_response('form/form_edit.html',  {'tipocliente':'1','form': form, 'form_name':nombre_form,'form_description':descripcion_form,'accion':accion_form,'titulo':titulo_form,'controlador':controlador_form,'cancelbtn':cancelbtn_form},context_instance = RequestContext(request))
    return cascoexternos_view(request, idrce)  
 
 #############################################################
#        DECOMISAR CASCOS
#############################################################

@login_required
def get_dc_list(request):
    #prepare the params
    try:
        fecha_desde=Fecha_Ver.objects.get()
    except Exception, e:
        fecha_desde=None
    if  fecha_desde == None:  
        querySet = CascoDecomiso.objects.select_related().all().order_by('-doc_decomiso__fecha_doc')
    else:
        querySet = CascoDecomiso.objects.select_related().filter(doc_decomiso__fecha_doc__gte=fecha_desde.fecha).order_by('-doc_decomiso__fecha_doc')
    #querySet = querySet.filter(doc__fecha_doc__year=2010)
 
    columnIndexNameMap = {0: '-casco_doc.fecha_doc',1:'casco_doc.fecha_doc',2:'dias'}
    #searchableColumns = ['cliente__nombre','recepcioncliente_nro']
    searchableColumns = ['doc_decomiso__fecha_doc','dias']
    #path to template used to generate json
    jsonTemplatePath = 'casco/json/json_dc.txt'


    #call to generic function from utils
    return get_datatables_records(request, querySet, columnIndexNameMap, searchableColumns, jsonTemplatePath)


@login_required
def cascodc_index(request):
    return render_to_response('casco/cascodcindex.html',locals(),context_instance = RequestContext(request))


@login_required
@transaction.commit_on_success()
def cascodc_add(request):
    if not request.user.has_perm('casco.decomisar'):
        return render_to_response("denegado.html",locals(),context_instance = RequestContext(request))
    
    nombre_form='Decomisar Cascos'
    descripcion_form='Decomisar Cascos'
    titulo_form='Decomisar Cascos' 
    controlador_form='Decomisar Cascos'
    accion_form='/comerciax/casco/cascodc/add'
    cancelbtn_form='/comerciax/casco/cascodc/index'
    fecha_cierre=Fechacierre.objects.get(almacen='pt').fechaminima()
    fecha_maxima=Fechacierre.objects.get(almacen='pt').fechamaxima()
    
    c=None
    l=[]
    if request.method == 'POST':
        form = CascoDCForm(request.POST)

        #rajuste = form.cleaned_data['ajuste']
        if form.is_valid():
            doc=Doc()

            fechadoc=form.cleaned_data['fecha']
            doc.fecha_doc=fechadoc
            doc.observaciones=form.cleaned_data['observaciones']
            doc.fecha_operacion=datetime.date.today()
            doc.fecha_doc=fechadoc
            doc.tipo_doc='15'
         
            pk_user=User.objects.get(pk=request.user.id)
            # esto hay que cambiarlo y poner el operador
            pk_doc=uuid4()
            

            doc.id_doc = pk_doc 
            doc.operador=pk_user
            
            
            dc=CascoDecomiso()
            

            dc.doc_decomiso=doc
            dc.dias=form.cleaned_data['dias']
            try:

                doc.save()
                dc.save() 
 
                return HttpResponseRedirect('/comerciax/casco/cascodc/view/'+pk_doc.__str__())  
            except Exception, e:
                exc_info = e.__str__() # sys.exc_info()[:1]
                c = exc_info.find("DETAIL:")
                
                if c < 0:
                    l=l+["Error Fatal."]
                else:
                    c = exc_info[c + 7:]
                    l=l+[c] 
                                     
                transaction.rollback()
                form = CascoERForm(request.POST)
                return render_to_response('form/form_adddetalle.html',  {'tipocliente':'2','fecha_minima':fecha_cierre,'fecha_maxima':fecha_maxima,'form': form, 'form_name':nombre_form,'form_description':descripcion_form,
                                                                         'accion':accion_form,'titulo':titulo_form,'controlador':controlador_form,
                                                                         'cancelbtn':cancelbtn_form,'error2':l},context_instance = RequestContext(request))
            else:
                transaction.commit()
    else:
        form = CascoDCForm(initial={'fecha':fecha_cierre}) 
    return render_to_response('form/form_adddetalle.html',  {'tipocliente':'2','fecha_minima':fecha_cierre,'fecha_maxima':fecha_maxima,'form': form, 'form_name':nombre_form,'form_description':descripcion_form,
                                                             'accion':accion_form,'titulo':titulo_form,'controlador':controlador_form,
                                                             'cancelbtn':cancelbtn_form,'error2':c},context_instance = RequestContext(request))

@login_required
@transaction.commit_on_success()
def cascodc_edit(request,iddc):
    if not request.user.has_perm('casco.decomisar'):
        return render_to_response("denegado.html",locals(),context_instance = RequestContext(request))
    
    nombre_form='Decomisar Cascos'
    descripcion_form='Decomisar Cascos'
    titulo_form='Decomisar Cascos' 
    controlador_form='Decomisar Cascos'
    accion_form='/comerciax/casco/cascodc/edit/'+iddc+'/'
    cancelbtn_form='/comerciax/casco/cascodc/view/'+iddc+'/'
    fecha_cierre=Fechacierre.objects.get(almacen='pt').fechaminima()
    fecha_maxima=Fechacierre.objects.get(almacen='pt').fechamaxima()
    c=None
    l=[]
    
    if request.method == 'POST':
        form = CascoDCFormEdit(request.POST)

        #rajuste = form.cleaned_data['ajuste']
        if form.is_valid():
            dc=CascoDecomiso.objects.get(pk=iddc)
            object_doc=Doc.objects.get(pk=iddc)
            
            object_doc.fecha_doc=form.cleaned_data['fecha']
            object_doc.observaciones=form.cleaned_data['observaciones']
            object_doc.fecha_operacion=datetime.date.today()
         
            pk_user=User.objects.get(pk=request.user.id)
            dc.dias=form.cleaned_data['dias']
            object_doc.operador=pk_user
         
            #RecepcionCliente.objects.create(doc_recepcioncliente=obj_doc,recepcioncliente_nro=nro,recepcioncliente_ajuste=ajuste,cliente=obj_cliente)
            try:
                object_doc.save()
                dc.save() 
 
                return HttpResponseRedirect('/comerciax/casco/cascodc/view/'+iddc)  

            except Exception, e:
                exc_info = e.__str__() # sys.exc_info()[:1]
                c = exc_info.find("DETAIL:")
                
                if c < 0:
                    l=l+["Error Fatal."]
                else:
                    c = exc_info[c + 7:]
                    l=l+[c]
                    
                transaction.rollback()
                form = CascoERForm(request.POST)
                return render_to_response('form/form_adddetalle.html',  {'tipocliente':'2','form': form, 'form_name':nombre_form,'form_description':descripcion_form,
                                                                         'accion':accion_form,'titulo':titulo_form,'controlador':controlador_form,
                                                                         'cancelbtn':cancelbtn_form,'error2':l},context_instance = RequestContext(request))
            else:
                transaction.commit()     
    else:
        dc = CascoDecomiso.objects.select_related().get(pk=iddc)
        form = CascoDCFormEdit(initial={'fecha':dc.doc_decomiso.fecha_doc,'dias':dc.dias,
                                             'observaciones':dc.doc_decomiso.observaciones})
    return render_to_response('form/form_edit.html',  {'tipocliente':'2','form': form, 'form_name':nombre_form,'form_description':descripcion_form,'accion':accion_form,
                                                       'titulo':titulo_form,'controlador':controlador_form,'cancelbtn':cancelbtn_form,
                                                       'fecha_minima':fecha_cierre,'fecha_maxima':fecha_maxima},context_instance = RequestContext(request))



@login_required
def cascodc_view(request,iddc):
    if not request.user.has_perm('casco.decomisar'):
        return render_to_response("denegado.html",locals(),context_instance = RequestContext(request))
    
    l=[]
    dc = CascoDecomiso.objects.select_related().get(pk=iddc)
    rc_fecha=dc.doc_decomiso.fecha_doc.strftime("%d/%m/%Y")
    rc_dias=dc.dias
    rc_observaciones=dc.doc_decomiso.observaciones
    filas=Detalle_DC.objects.select_related().filter(doc_decomiso=iddc).order_by('casco__producto__descripcion','casco__casco_nro')
    editar=True
    if dc.procesado==True:
        editar=False
        
    elementos_detalle=[]
    id1=''
    k=0
    k2=0
    for a1 in filas:
        if k!=0:
            if id1!=a1.casco.producto.id:
                elementos_detalle[k-1]['cantidad'] = k2
                k2=0
        elementos_detalle+=[{'cliente':a1.casco.get_cliente,'casco_id':a1.casco.id_casco,
                             'casco_nro':a1.casco.casco_nro,'dias':a1.dias,
                             'productosalida':a1.casco.producto_salida.descripcion
                             }]
        k+=1
        k2+=1
        id1=a1.casco.producto.id  
    if k!=0:
        elementos_detalle[k-1]['cantidad'] = k2
    return render_to_response('casco/viewcascodc.html',{'total_casco':k,'fecha':rc_fecha,'observaciones':rc_observaciones,
                                                         'dias':rc_dias,'rc_id':iddc,'elementos_detalle':elementos_detalle, 'edito':editar,
                                                              'error2':l},context_instance = RequestContext(request))
@login_required
@transaction.commit_on_success()
def cascodc_del(request,iddc):
    if not request.user.has_perm('casco.decomisar'):
        return render_to_response("denegado.html",locals(),context_instance = RequestContext(request))
    
    try:
        detalles=Detalle_DC.objects.select_related().filter(doc_decomiso=iddc)
        for a in detalles:
            Casco.objects.filter(id_casco=a.casco.id_casco).update(venta=False,decomisado=False)
        
        Doc.objects.select_related().get(pk=iddc).delete()
        return HttpResponseRedirect('/comerciax/casco/cascodc/index')
    except Exception,e :
        transaction.rollback()
        l = ['Error al eliminar el documento']
        dc = CascoDecomiso.objects.select_related().get(pk=iddc)
        rc_fecha=dc.doc_decomiso.fecha_doc.strftime("%d/%m/%Y")


        editar=1
        rc_observaciones=dc.doc_decomiso.observaciones
        filas = Detalle_DC.objects.select_related().filter(doc_decomiso=iddc).order_by('casco_casco.casco_nro')

        return render_to_response('casco/viewcascodc.html',{'fecha':rc_fecha,'observaciones':rc_observaciones,'rc_id':iddc,'dias':dc.dias,
                                                            'elementos_detalle':filas, 'edito':editar,'error2':l},context_instance = RequestContext(request))

    else:
        transaction.commit()

#############################################################
#        DETALLE DE CASCOS RECHAZADOS POR ERROR DE RECEPC.
#############################################################

@login_required
@transaction.commit_on_success()
def detalleDC_add(request,iddc):
    if not request.user.has_perm('casco.decomisar'):
        return render_to_response("denegado.html",locals(),context_instance = RequestContext(request))
    
    l=[]
    titulo_form='Decomisar Cascos' 
    controlador_form='Decomisar Cascos'
    descripcion_form='Seleccionar los cascos a decomisar'
    accion_form='detalleDC_add'
    cancelbtn_form='/comerciax/casco/cascodc/view/'+iddc
    #estado="Casco"
    medidas=Producto.objects.all()
      
    dc=CascoDecomiso.objects.get(pk=iddc)
    dias=dc.dias
    elementos=[]
    #elementos=CascoDecomiso.objects.all()
    #cascos=Casco.objects.select_related().filter(estado_actual=Estados.estados["Casco"]).order_by('admincomerciax_producto.descripcion','casco_nro')
    mostrarcausa=False
    #causas=CausasRechazo.objects.all()
    if request.method == 'POST':
        seleccion=request.POST.keys()
        k=0
        #causa=request.POST["causa"]
        while True:
            if k==seleccion.__len__():
                break
            casco=Casco.objects.filter(pk=seleccion[k])
            
            if casco.count()!=0:

                '''
                Los selecionados los cambio de estado, agregar a detalle del documento y actualizar trazabilidad
                '''
                detalle=Detalle_DC()
                pk_detalle=uuid4()
                detalle.id_detalledc=pk_detalle
                detalle.doc_decomiso=CascoDecomiso.objects.get(pk=iddc)
                detalle.casco=Casco.objects.get(pk=seleccion[k])
                detalle.dias=request.POST["D"+seleccion[k]]
                #detalle.causa=CausasRechazo.objects.get(pk=causa)
                try:
                    detalle.save()
                except Exception, e:
                    exc_info = e.__str__() # sys.exc_info()[:1]
                    c = exc_info.find("DETAIL:")
                    
                    if c < 0:
                        l=l+["Error Fatal."]
                    else:
                        l=['El casco ya existe en este documento']
                        c = exc_info[c + 7:]
                        transaction.rollback()
                        return render_to_response('casco/form_seleccion.html',{'medidadec':medidas,'title':titulo_form,'controlador':controlador_form,'accion':accion_form,
                                                      'cancelbtn':cancelbtn_form, 'form_description':descripcion_form,
                                                      'fecha':dc.doc_decomiso.fecha_doc.strftime("%d/%m/%Y"),'observaciones':dc.doc_decomiso.observaciones,
                                                      'rc_id':iddc,'error2':l},context_instance = RequestContext(request))
                        
                
                Casco.objects.filter(pk=seleccion[k]).update(venta=True,decomisado=True,estado_actual='DC',fecha=dc.doc_decomiso.fecha_doc)
                add_trazabilidad(seleccion[k], iddc, "DC")

            k=k+1
        
            
        
        if request.POST.__contains__('submit1'):
            return render_to_response('casco/form_seleccion.html',{'medidadec':medidas,'title':titulo_form,'controlador':controlador_form,'accion':accion_form,
                                                      'cancelbtn':cancelbtn_form, 'form_description':descripcion_form,
                                                      'fecha':dc.doc_decomiso.fecha_doc.strftime("%d/%m/%Y"),'observaciones':dc.doc_decomiso.observaciones,
                                                      'rc_id':iddc,'elementos_detalle':elementos,'decomiso':True,'error2':l},context_instance = RequestContext(request))
        else:
            return HttpResponseRedirect('/comerciax/casco/cascodc/view/' + iddc)
    
    return render_to_response('casco/form_seleccion.html', {'medidadec':medidas,'title':titulo_form,'controlador':controlador_form,'accion':accion_form,
                                                      'cancelbtn':cancelbtn_form, 'form_description':descripcion_form,
                                                      'fecha':dc.doc_decomiso.fecha_doc.strftime("%d/%m/%Y"),'observaciones':dc.doc_decomiso.observaciones,
                                                      'rc_id':iddc,'elementos_detalle':elementos,'decomiso':True,'error2':l},context_instance = RequestContext(request))    

@login_required
@transaction.commit_on_success()
def detalleDC_delete(request,iddc,idcasco): 
    if not request.user.has_perm('casco.decomisar'):
        return render_to_response("denegado.html",locals(),context_instance = RequestContext(request))
    
    Casco.objects.filter(pk=idcasco).update(venta=False,decomisado=False)
    casco=Casco.objects.get(pk=idcasco)
    nro=casco.casco_nro
    
    if eliminar_detalle_sino(casco.id_casco,iddc):
        Detalle_DC.objects.get(casco=idcasco).delete()
        actualiza_traza(idcasco,iddc)
        
        filas=Detalle_DC.objects.select_related().filter(doc_decomiso=iddc).order_by('casco__producto__descripcion','casco__casco_nro')
        total_casco=str(filas.count())
            
        elementos_detalle=[]
        id1=''
        k=0
        k2=0
        for a1 in filas:
            if k!=0:
                if id1!=a1.casco.producto.id:
#                    elementos_detalle[k-1]['cantidad'] = elementos_detalle[k-1]['productoid']
                    elementos_detalle[k-1]['cantidad'] = k2
                    k2=0
                    
            elementos_detalle+=[{'total_casco':total_casco,
                                 'id_doc':a1.doc_decomiso.doc_decomiso.id_doc,'casco_id':a1.casco.id_casco,
                                 'casco_nro':a1.casco.casco_nro,'productosalida':a1.casco.producto.descripcion,
                                 'dias':a1.dias,'cliente':a1.casco.get_cliente()}]
            k+=1
            id1=a1.casco.producto.id 
            k2+=1
            
        if k!=0:
            elementos_detalle[k-1]['cantidad'] = k2
        return HttpResponse(simplejson.dumps(elementos_detalle),content_type = 'application/javascript; charset=utf8')
    else:
        error2 = "No se puede eliminar el casco " + str(nro) + " ya que su estado ha cambiado "
        return HttpResponse(json.dumps({'error':True, 'message':error2}),mimetype=u'application/json')

    
@login_required
def detalleDC_list(request,idprod,iddc):

    if idprod.__len__()>0:
        elementos = query_to_dicts("""
        SELECT 
            *
        FROM 
          cascos_decomiso
        WHERE estado_actual = 'PT' AND dias>= %s AND id = %s
        order by descripcion,casco_nro,nombre,dias
        
        """,CascoDecomiso.objects.get(doc_decomiso=iddc).dias,idprod)
    else:
        elementos = query_to_dicts("""
        SELECT 
            *
        FROM 
          cascos_decomiso
        WHERE estado_actual = 'PT' AND dias>= %s
        order by descripcion,casco_nro,nombre,dias
        """,CascoDecomiso.objects.get(doc_decomiso=iddc).dias)
    
    lista_valores=[]
    for detalles in elementos:
        nombre=detalles["nombre"] if detalles['ci'] == None else '*'+detalles["nombre_particular"]
        lista_valores=lista_valores+[{"casco_nro":detalles["casco_nro"],"id":detalles["id"],"descripcion":detalles["descripcion"],
                                      "nombre":nombre,"id_casco":detalles["id_casco"],"dias":detalles["dias"]}]
        
    return HttpResponse(simplejson.dumps(lista_valores),content_type = 'application/javascript; charset=utf8')

def tiene_cuentas_por_cobrar(request,idcliente,fecha):
    elementos=Cliente.objects.get(id=idcliente)
    fecha1=fecha.split('-')
    fecha2=datetime.datetime.strptime(str(fecha1[2])+"/"+str(fecha1[1])+"/"+str(fecha1[0]), '%Y/%m/%d').date()
    vencido=1
    lista_valores=[]
    numero=""
    por_pagar=0
    vencido=0
    por_pagar=elementos.get_cuenta_porpagar()
#    if elementos.get_facturas_porpagar().__len__()!=0:
#        por_pagar=1
    numero=elementos.get_contrato_nro()
    vencido=0
    venta=''
    if numero!="Sin Contrato":
#        a1=ClienteContrato.objects.get(cliente__id=idcliente,cerrado=False,contrato__fecha_vencimiento__lte=fecha2)
        a1=ClienteContrato.objects.select_related().filter(cliente=idcliente,contrato__cerrado=False,contrato__fecha_vencimiento__lte=fecha2)
        if a1.__len__()!=0:
            vencido=1
            a1.contrato.fecha_vencimiento
        a1=ClienteContrato.objects.select_related().get(cliente=idcliente,contrato__cerrado=False)
        venta = '0' if a1.contrato.para_la_venta==False else '1'
    lista_valores+=[{'nro':numero,'nombre':elementos.nombre,'vencido':str(vencido),'por_pagar':str(por_pagar),'venta':venta}]
    return HttpResponse(simplejson.dumps(lista_valores),content_type = 'application/javascript; charset=utf8')
    
def obtenercontrato_list(request,idcliente,fecha):
    elementos=Cliente.objects.get(id=idcliente)
    fecha1=fecha.split('-')
    fecha2=datetime.datetime.strptime(str(fecha1[2])+"/"+str(fecha1[1])+"/"+str(fecha1[0]), '%Y/%m/%d').date()
    vencido=1
    lista_valores=[]
    numero=""
    por_pagar=0
    vencido=0
    if elementos.get_facturas_porpagar():
        por_pagar=1
    if elementos.get_contrato_nro()=="Sin Contrato":
        numero="Sin Contrato"
        vencido=0
    else:

#        a1=ClienteContrato.objects.get(cliente__id=idcliente,cerrado=False,contrato__fecha_vencimiento__lte=fecha2)

        a1=ClienteContrato.objects.select_related().filter(cliente=idcliente,contrato__cerrado=False,contrato__fecha_vencimiento__lte=fecha2)
        if a1.__len__()!=0:
            vencido=1
            a1.contrato.fecha_vencimiento
        a1=ClienteContrato.objects.select_related().get(cliente=idcliente,contrato__cerrado=False)
        venta = '0' if a1.contrato.para_la_venta==False else '1'
    lista_valores+=[{'nro':numero,'nombre':elementos.nombre,'vencido':str(vencido),'por_pagar':str(por_pagar),'venta':venta}]
    return HttpResponse(simplejson.dumps(lista_valores),content_type = 'application/javascript; charset=utf8')


def obtenerclientes_list(request,idorganismo,idprovincia,tipocliente):
    
    elementos=Cliente.objects.filter(eliminado=False).order_by('nombre')
    if int(tipocliente)==0: #No Externo
        elementos=elementos.filter(externo=False)
    if int(tipocliente)==1: #Externo
        elementos=elementos.filter(externo=True)
    
    
    if idorganismo!="0":
        elementos=elementos.filter(organismo=Organismo.objects.get(pk=idorganismo))
    if idprovincia!="0":
        elementos=elementos.filter(provincia=Provincias.objects.get(pk=idprovincia))
    lista_valores=[]
    for a1 in elementos: 
        lista_valores+=[{'id':a1.id,'codigo':a1.codigo,'nombre':a1.nombre}]
    return HttpResponse(simplejson.dumps(lista_valores),content_type = 'application/javascript; charset=utf8')
