#-*- coding: utf-8 -*-
from django.db.models import Q
from django.template.loader import render_to_string, get_template
from django.http import HttpResponse
from django.shortcuts import render_to_response, HttpResponseRedirect
from django.template import Context
import ho.pisa as pisa
import cStringIO as StringIO
from itertools import *
from django.db import connection
import comerciax.settings
from time import gmtime, strftime
import subprocess
import os
import glob
import time
from decimal import *

def write_pdf(template_src, context_dict):
    template = get_template(template_src)
    context = Context(context_dict)
    html  = template.render(context)
    result = StringIO.StringIO()
    pdf = pisa.pisaDocument(StringIO.StringIO(
        html.encode("UTF-8")), result)
    if not pdf.err:
        return HttpResponse(result.getvalue(), 
             mimetype='application/pdf')
    return render_to_response("denegado.html")

def fecha_hoy():
    import datetime
    return datetime.date.today().strftime("%d/%m/%Y")

def fecha_hoy_mas_tresanyos():
    import datetime
    #datetime.date.today().strftime("%d/%m/%Y")

    year, month, day = datetime.date.today().timetuple()[:3]
    new_year = year + 3
    if month==2 and day>29:
        month=3
        dia=1
        
    return datetime.date(new_year, month, day).strftime("%d/%m/%Y")

def get_datatables_records(request, querySet, columnIndexNameMap, searchableColumns, jsonTemplatePath, *args):

    #Safety measure. If someone messes with iDisplayLength manually, we clip it to
    #the max value of 100.
    if not 'iDisplayLength' in request.GET or not request.GET['iDisplayLength']:
        iDisplayLength = 10 # default value
    else: 
        iDisplayLength = min(int(request.GET['iDisplayLength']),100)

    if not 'iDisplayStart' in request.GET or not request.GET['iDisplayStart']:
        startRecord = 0 #default value
    else:
        startRecord = int(request.GET['iDisplayStart'])
    endRecord = startRecord + iDisplayLength 

    #apply ordering 
    if not 'iSortingCols' in request.GET or not request.GET['iSortingCols']:
        iSortingCols = 0 #default value
    else:
        iSortingCols = int(request.GET['iSortingCols'])
    asortingCols = []
    
    if iSortingCols>0:
        for sortedColIndex in range(0, iSortingCols):
            sortedColName = columnIndexNameMap[int(request.GET['iSortCol_'+str(sortedColIndex)])]
            sortingDirection = request.GET['iSortDir_'+str(sortedColIndex)]
            if sortingDirection == 'desc':
                sortedColName = '-'+sortedColName
            asortingCols.append(sortedColName) 
            
        querySet = querySet.order_by(*asortingCols)
    
    #apply filtering by value sent by user
    if not 'sSearch' in request.GET or not request.GET['sSearch']:
        customSearch = '' #default value
    else:
        customSearch = str(request.GET['sSearch']);
    if customSearch != '':
        outputQ = None
        first = True
        for searchableColumn in searchableColumns:
            kwargz = {searchableColumn+"__icontains" : customSearch}
            q = Q(**kwargz)
            if (first):
                first = False
                outputQ = q
            else:
                outputQ |= q
        
        querySet = querySet.filter(outputQ)
        
    #count how many records match the final criteria
    iTotalRecords = iTotalDisplayRecords = querySet.count()
    
    #get the slice
    querySet = querySet[startRecord:endRecord]
    
    #prepare the JSON with the response
    if not 'sEcho' in request.GET or not request.GET['sEcho']:
        sEcho = '0' #default value
    else:
        sEcho = request.GET['sEcho'] #this is required by datatables 
    jstonString = render_to_string(jsonTemplatePath, locals())
    
    return HttpResponse(jstonString, mimetype="application/javascript")

def redondeo(numero,lug_dec):
    formato='1.'
    for x in range(lug_dec):
        formato+='0'
    return float(Decimal(str(numero)).quantize(Decimal(formato), rounding=ROUND_HALF_UP))
        
def backup(*self):
 
# change these as appropriate for your platform/environment :
    USER = comerciax.settings.DATABASES['default']['USER']
    PASS = comerciax.settings.DATABASES['default']['PASSWORD']
    HOST = comerciax.settings.DATABASES['default']['HOST']
    database_name = comerciax.settings.DATABASES['default']['NAME']
     
    BACKUP_DIR = "c:\\postgresql_backups\\"
#    dumper = """ "pg_dump" -U %s -Z 9 -f %s -F c %s  """  
    dumper = """ "c:\\Program Files (x86)\\PostgreSQL\\9.0\\bin\\pg_dump" -U %s -Z 9 -f %s -F c %s  """
    
    x_days_ago = time.time() - ( 60 * 60 * 24 * 2 )
 
    os.putenv('PGPASSWORD', PASS)
    # Delete old backup files first.
    glob_list = glob.glob(BACKUP_DIR + database_name + '*' + '.pgdump')
    for file in glob_list:
        file_info = os.stat(file)
        if file_info.st_ctime < x_days_ago:
            print time.strftime("%Y-%m-%d-%H-%M-%S", time.gmtime()) + ": " + str("Unlink: %s" % file)
            os.unlink(file)
        else:
            print time.strftime("%Y-%m-%d-%H-%M-%S", time.gmtime()) + ": " + str("Keeping : %s" % file)
 
    print time.strftime("%Y-%m-%d-%H-%M-%S", time.gmtime()) + ": " + str("Backup files older than %s deleted." % time.strftime('%c', time.gmtime(x_days_ago)))
 
    # Now perform the backup.
    
    print time.strftime("%Y-%m-%d-%H-%M-%S", time.gmtime()) + ": " + str("dump started for %s" % database_name)
    thetime = str(strftime("%Y-%m-%d-%H-%M"))
    file_name = database_name + '_' + thetime + ".sql.pgdump"
    #Run the pg_dump command to the right directory
    command = dumper % (USER,  BACKUP_DIR + file_name, database_name)
    print time.strftime("%Y-%m-%d-%H-%M-%S", time.gmtime()) + ": " + str(command)
#    subprocess.Popen("pg_dump.exe")
    os.system("pg_dump.exe")
    subprocess.call(command,shell = True)
    print time.strftime("%Y-%m-%d-%H-%M-%S", time.gmtime()) + ": " + str("%s dump finished" % database_name)
    print time.strftime("%Y-%m-%d-%H-%M-%S", time.gmtime()) + ": " + str("Backup job complete.") 

#
# Almacen de casco
#  - Casco
#  - DVP
#  - DIP
#  - ER
#  - REE
# Almacen de produccion
#  - produccion
# Almacen de produccion terminada
#  - PT

# la descripcion no debe pasar de 30 caracteres
class Estados:
    
    estados = {"Casco": "Almacén de Casco",
               "Produccion":"Proceso de Producción",
               "PT":"Almacén Producción Terminada",
               "Transferencia":"Transferencia",
               "DIP":"Devuelto a Inservible",
               "DVP":"Devuelto a Vulca",
               "ER":"Rechazado por error revisión",
               "ECR":"Casco Rechazado Entregado",
               "REE":"Rechazado por Entidad Externa",
               "Factura":"Facturado",
               "DC":"Casco Decomisado",
               "DCC":"Devuelto al Cliente"}
    
    siglas_alm = {"c": "Almacén de Casco",
                  "p": "Almacén de Producción",
                  "pt": "Almacén de Producción Terminada",
                  "cm": "Cierre de Mes"
                  }
    
class disableCSRF:
    def process_request(self, request):
        setattr(request, '_dont_enforce_csrf_checks', True)
        return None    

'''def number_format(number, decimals, dec_point, thousands_sep, simbolo):
    try:
        number=0 if number == None else number
        number = round(float(number), decimals)
    except ValueError:
        return number
    neg = number < 0
    integer, fractional = str(abs(number)).split('.')
    m = len(integer) % 3
    if m:
        parts = [integer[:m]]
    else:
        parts = []
    
    parts.extend([integer[m+t:m+t+3] for t in xrange(0, len(integer[m:]), 3)])
    
    if decimals:
        return '%s%s%s%s%s' % (
            neg and '-' or '',
            simbolo, 
            thousands_sep.join(parts), 
            dec_point, 
            fractional.ljust(decimals, '0')[:decimals]
        )
    else:
        return '%s%s' % (neg and '-' or ''+simbolo, thousands_sep.join(parts))'''


def query_to_dicts(query_string, *query_args):
    """Run a simple query and produce a generator
    that returns the results as a bunch of dictionaries
    with keys for the column values selected.
    """
    cursor = connection.cursor()
    cursor.execute(query_string, query_args)
    col_names = [desc[0] for desc in cursor.description]
    while True:
        row = cursor.fetchone()
        if row is None:
            break
        row_dict = dict(izip(col_names, row))
        yield row_dict
    return 

class Meses:
    meses = {1: "30",
               3:"31",
               4:"30",
               5:"31",
               6:"30",
               7:"31",
               8:"31",
               9:"30",
               10:"31",
               11:"30",
               12: "31"}
    
    meses_name = {1:"Enero",
         2:"Febrero",
         3:"Marzo",
         4:"Abril",
         5:"Mayo",
         6:"Junio",
         7:"Julio",
         8:"Agosto",
         9:"Septiembre",
         10:"Octubre",
         11:"Noviembre",
         12:"Diciembre"}
    meses_no = {"Enero":1,
         "Febrero":2,
         "Marzo":3,
         "Abril":4,
         "Mayo":5,
         "Junio":6,
         "Julio":7,
         "Agosto":8,
         "Septiembre":9,
         "Octubre":10,
         "Noviembre":11,
         "Diciembre":12}

