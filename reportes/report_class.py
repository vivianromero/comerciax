# -*- coding: utf-8 -*-
'''
Created on 18/10/2013

@author: maykel
'''
import os
import datetime
#cur_dir = os.path.dirname(os.path.abspath(__file__))

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
from reportlab.lib.colors import navy, red
#
from comerciax.comercial.models import Clientepago,Factpago
from django.contrib.auth.models import User, Permission

from geraldo import Report, ReportBand, DetailBand, SystemField, Label, ObjectValue, ReportGroup,landscape
from geraldo.utils import cm, BAND_WIDTH, TA_CENTER, TA_RIGHT

from reportlab.lib.pagesizes import A5


from geraldo import Report, ReportBand, Label, ObjectValue, SystemField,\
    FIELD_ACTION_COUNT, FIELD_ACTION_SUM, BAND_WIDTH, Line, ReportGroup,\
    SubReport
from geraldo.generators import PDFGenerator
from django.shortcuts import render_to_response
global report 
from tempfile import TemporaryFile
mesg = []
#import comerciax.settings
from pyPdf import PdfFileReader, PdfFileWriter
from django.http import HttpResponse
import cStringIO as StringIO
import os
import os
cur_dir = os.path.dirname(os.path.abspath(__file__))

from django.contrib.auth.models import User, Permission
from comerciax.comercial.models import Clientepago,Factpago

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
from reportlab.lib.colors import navy, red
from reportlab.graphics.shapes import Drawing


from geraldo import Report, ReportBand, Label, ObjectValue, SystemField,\
    FIELD_ACTION_COUNT, FIELD_ACTION_SUM, BAND_WIDTH, Line, ReportGroup,SubReport,Image

class Reportes():


    def GenerarRep(self,queryset,type,pdf_file_name,filtro,*edad):
        tope=0
        cur_dir = os.path.dirname(os.path.abspath(__file__))
        self.attribute = 'cliente'
        if edad:
            self.attribute='edad'
        class Report_(Report):               
            if type == "reg_contrat":     
                title = 'Registro de Contratos'
                class band_detail(ReportBand):

                        height = 0.4*cm
                        elements = [
                            ObjectValue(expression = 'codigo', left=0.1*cm, style={'fontSize': 6}),
                            ObjectValue(expression = 'nombre', width=11*cm,left=1.5*cm, style={'fontSize': 5}),
                            ObjectValue(expression = 'contrato_nro', left=7.6*cm, style={'fontSize': 6}),
                            ObjectValue(expression = 'fecha_vigencia', left=9.3*cm, style={'fontSize': 6}),
                            ObjectValue(expression = 'fecha_vencimiento', left=10.8*cm, style={'fontSize': 6}),
                            ObjectValue(expression = 'cerrado', left=12.6*cm, style={'fontSize': 6}),
                            ObjectValue(expression = 'tipo', left=13.5*cm, style={'fontSize': 6}),
                            ObjectValue(expression = 'preciomn', left=14.7*cm, style={'fontSize': 6}),
                            ObjectValue(expression = 'preciocuc', left=16.3*cm, style={'fontSize': 6}),
                            ObjectValue(expression = 'dias', left=18*cm, style={'fontSize': 6}),
                            
                            ]                      
                    
                class band_page_header(ReportBand):
                    elements = [
                        SystemField(expression='%(report_title)s', top=0.1*cm, left=0, width=BAND_WIDTH,
                            style={'fontName': 'Helvetica-Bold', 'fontSize': 14, 'alignment': TA_CENTER}),
                        SystemField(expression=u'Página %(page_number)d de %(page_count)d', top=0.1*cm,
                            width=BAND_WIDTH, style={'alignment': TA_RIGHT,'fontSize': 5}),
                        SystemField(expression='Impreso el %(now:%d/%m/%Y )s a las %(now:%H:%M)s', top=0.1*cm,
                            width=BAND_WIDTH, style={'alignment': TA_LEFT,'fontSize': 5}),
#                        Image(left=0*cm, top=0*cm, right=0.5*cm, bottom=0.5*cm,filename=os.path.join(cur_dir, 'logo111.png'))
                        ]
                    if filtro.__len__()!=0:    
                        elements+=[Label(text="Filtro:", top=0.9*cm, left=0.1*cm, style={'fontSize': 5}),]
                    tope=1.2*cm
                    for k in range(filtro.__len__()):
                            
                            elements+=[Label(text=filtro[k], top=tope, left=0.1*cm, style={'fontSize': 5}, width=BAND_WIDTH),]
                            tope=tope+0.3*cm
                        
                    tope=tope+0.3*cm
                    elements+=[Label(text="Código", top=tope, left=0.1*cm, style={'fontSize':8}),
                    Label(text="Cliente", top=tope, left=1.9*cm, style={'fontSize':8}),
                    Label(text="Nro.Contrato", top=tope, left=7.3*cm, style={'fontSize': 8}),
                    Label(text="Fecha Vig.", top=tope, left=9.1*cm, style={'fontSize': 8}),
                    Label(text="Fecha Venc.", top=tope, left=10.6*cm, style={'fontSize': 8}),
                    Label(text="Cerrado", top=tope, left=12.4*cm, style={'fontSize': 8}),
                    Label(text="Tipo", top=tope, left=13.6*cm, style={'fontSize': 8}),
                    Label(text="Precio CUP", top=tope, left=14.3*cm, style={'fontSize': 8}),
                    Label(text="Precio MLC", top=tope, left=15.9*cm, style={'fontSize': 8}),
                    Label(text="Días caducar", top=tope, left=17.5*cm, style={'fontSize': 8}),
                    ]
                    height = tope+0.5*cm
                    borders = {'bottom': True}
            
                class band_page_footer(ReportBand):
                    height = 0.5*cm
                    elements = [
                        Label(text='Comerciax', top=0.1*cm),
                        ]
                    borders = {'top': True}
            if type == "rep_ptcantdesg":     
                title = 'Cantidad de Cascos en PT'
                class band_detail(ReportBand):

                        height = 0.4*cm
                        elements = [
                            ObjectValue(expression = 'medida',left=0.1*cm, style={'fontSize': 6}),
                            ObjectValue(expression = 'cantidad',width=1*cm, left=5.3*cm, style={'fontSize': 6,'alignment': TA_RIGHT}),
                            ObjectValue(expression = 'precio',width=1*cm,left=7.1*cm, style={'fontSize': 6,'alignment': TA_RIGHT}),
                            ObjectValue(expression = 'importe',width=1*cm,left=9.4*cm, style={'fontSize': 6,'alignment': TA_RIGHT}),
                            ]                      
                    
                class band_page_header(ReportBand):
                    elements = [
                        SystemField(expression='%(report_title)s', top=0.1*cm, left=0, width=BAND_WIDTH,
                            style={'fontName': 'Helvetica-Bold', 'fontSize': 14, 'alignment': TA_CENTER}),
                        SystemField(expression=u'Página %(page_number)d de %(page_count)d', top=0.1*cm,
                            width=BAND_WIDTH, style={'alignment': TA_RIGHT,'fontSize': 5}),
                        SystemField(expression='Impreso el %(now:%d/%m/%Y )s a las %(now:%H:%M)s', top=0.1*cm,
                            width=BAND_WIDTH, style={'alignment': TA_LEFT,'fontSize': 5}),
#                        Image(left=0*cm, top=0*cm, right=0.5*cm, bottom=0.5*cm,filename=os.path.join(cur_dir, 'logo111.png'))
                        ]
                    if filtro.__len__()!=0:    
                        elements+=[Label(text="Filtro:", top=0.9*cm, left=0.1*cm, style={'fontSize': 5}),]
                    tope=1.2*cm
                    for k in range(filtro.__len__()):
                            
                            elements+=[Label(text=filtro[k], top=tope, left=0.1*cm, style={'fontSize': 5}, width=BAND_WIDTH),]
                            tope=tope+0.3*cm
                        
                    tope=tope+0.3*cm
                    elements+=[
                    Label(text="Medida", top=tope, left=0.1*cm, style={'fontSize':8}),
                    Label(text="Cantidad", top=tope, left=5.3*cm, style={'fontSize':8}),
                    Label(text="Precio MN", top=tope, left=7.1*cm, style={'fontSize':8}),
                    Label(text="Importe", top=tope, left=9.4*cm, style={'fontSize':8}),
                    
                    ]
                    height = tope+0.5*cm
                    borders = {'bottom': True}
                    
            
                class band_page_footer(ReportBand):
                    height = 0.5*cm
                    elements = [
                        Label(text='Comerciax', top=0.1*cm),
                        ]
                    borders = {'top': True}
                
                class band_summary(ReportBand):
                    height = 0.5*cm
                    elements = [
                        Label(text='====  Total General ====', style={'fontSize': 6}),
                        ObjectValue(expression='sum(cantidad)', left=1.26*cm, style={'fontName': 'Helvetica-Bold', 'fontSize': 6, 'alignment': TA_RIGHT}),
                        ObjectValue(expression='sum(importe)', left=5.36*cm, style={'fontName': 'Helvetica-Bold', 'fontSize': 6, 'alignment': TA_RIGHT}),
                        ]

                groups = [
                     ReportGroup(
                        attribute_name='organismo',
                        band_header=DetailBand(
                            height=0.6*cm,
                            width = 6.67*cm,
                            elements=[
                                Label(text='>', style={'fontSize': 6}),
                                ObjectValue(expression='organismo',  left=5,style={'fontSize': 6})
                            ]
                        ),
                        band_footer=ReportBand(
                            height = 0.5*cm,
                            elements = [
                                Label(text='>  Total Organismo ====', style={'fontSize': 6}),
                                ObjectValue(expression='sum(cantidad)', left=1.26*cm, style={'fontName': 'Helvetica-Bold', 'fontSize': 6, 'alignment': TA_RIGHT}),
                                ObjectValue(expression='sum(importe)', left=5.36*cm, style={'fontName': 'Helvetica-Bold', 'fontSize': 6, 'alignment': TA_RIGHT}),
                                ],
                            borders = {'top': True, 'bottom': True, 'fontSize':6, 'fontName': 'Helvetica'}
                        ),
                        
                    ),
                    ReportGroup(
                        attribute_name='provincia',
                        band_header=DetailBand(
                            height=0.5*cm,
                            width = 6.67*cm,
                            elements=[
                                Label(text='>> ', style={'fontSize': 6}),
                                ObjectValue(expression='provincia', left=1.5*cm, style={'fontName': 'Helvetica-Bold', 'fontSize': 6, 'alignment': TA_LEFT}),
                            ]
                        ),
                        band_footer=ReportBand(
                            height = 0.5*cm,
                            elements = [
                                Label(text='>> Total Provincia', style={'fontSize': 6}),
                                ObjectValue(expression='sum(cantidad)', left=1.26*cm, style={'fontName': 'Helvetica-Bold', 'fontSize': 6, 'alignment': TA_RIGHT}),
                                ObjectValue(expression='sum(importe)', left=5.36*cm, style={'fontName': 'Helvetica-Bold', 'fontSize': 6, 'alignment': TA_RIGHT}),
                                ],
                            borders = {'top': True, 'bottom': True, 'fontSize':6, 'fontName': 'Helvetica'}
                        ),
                    ), 
                    ReportGroup(
                        attribute_name='cliente',
                        band_header=DetailBand(
                            height=0.5*cm,
                            width = 8*cm,
                            elements=[
                                Label(text='>>>', style={'fontSize': 6}),
                                ObjectValue(expression='cliente', style={'fontSize': 6}, left=2*cm, width = 12*cm)
                            ]
                        ),
                        band_footer=ReportBand(
                            height = 0.5*cm,
                            elements = [
                                Label(text='>>> Total Cliente', style={'fontSize': 6}),
                                ObjectValue(expression='sum(cantidad)', left=1.26*cm, style={'fontName': 'Helvetica-Bold', 'fontSize': 6, 'alignment': TA_RIGHT}),
                                ObjectValue(expression='sum(importe)', left=5.36*cm, style={'fontName': 'Helvetica-Bold', 'fontSize': 6, 'alignment': TA_RIGHT}),
                                ],
                            borders = {'top': True, 'bottom': True, 'fontSize':6, 'fontName': 'Helvetica'}
                        ),
                    ),
                ] 
            if type == "rep_ptcantnodesg":     
                title = 'Cantidad de Cascos en PT'
                class band_detail(ReportBand):

                        height = 0.4*cm
                        elements = [
                            ObjectValue(expression = 'cantidad',width=1*cm, left=5.3*cm, style={'fontSize': 6,'alignment': TA_RIGHT}),
                            ObjectValue(expression = 'importe',width=1*cm,left=7.1*cm, style={'fontSize': 6,'alignment': TA_RIGHT}),
                            ]                      
                    
                class band_page_header(ReportBand):
                    elements = [
                        SystemField(expression='%(report_title)s', top=0.1*cm, left=0, width=BAND_WIDTH,
                            style={'fontName': 'Helvetica-Bold', 'fontSize': 14, 'alignment': TA_CENTER}),
                        SystemField(expression=u'Página %(page_number)d de %(page_count)d', top=0.1*cm,
                            width=BAND_WIDTH, style={'alignment': TA_RIGHT,'fontSize': 5}),
                        SystemField(expression='Impreso el %(now:%d/%m/%Y )s a las %(now:%H:%M)s', top=0.1*cm,
                            width=BAND_WIDTH, style={'alignment': TA_LEFT,'fontSize': 5}),
#                        Image(left=0*cm, top=0*cm, right=0.5*cm, bottom=0.5*cm,filename=os.path.join(cur_dir, 'logo111.png'))
                        ]
                    if filtro.__len__()!=0:    
                        elements+=[Label(text="Filtro:", top=0.9*cm, left=0.1*cm, style={'fontSize': 5}),]
                    tope=1.2*cm
                    for k in range(filtro.__len__()):
                            
                            elements+=[Label(text=filtro[k], top=tope, left=0.1*cm, style={'fontSize': 5}, width=BAND_WIDTH),]
                            tope=tope+0.3*cm
                        
                    tope=tope+0.3*cm
                    elements+=[
                    Label(text="Cantidad", top=tope, left=5.3*cm, style={'fontSize':8}),
                    Label(text="Importe", top=tope, left=7.1*cm, style={'fontSize':8}),
                    
                    ]
                    height = tope+0.5*cm
                    borders = {'bottom': True}
                    
            
                class band_page_footer(ReportBand):
                    height = 0.5*cm
                    elements = [
                        Label(text='Comerciax', top=0.1*cm),
                        ]
                    borders = {'top': True}
                
                class band_summary(ReportBand):
                    height = 0.5*cm
                    elements = [
                        Label(text='====  Total General ====', style={'fontSize': 6}),
                        ObjectValue(expression='sum(cantidad)', left=1.26*cm, style={'fontName': 'Helvetica-Bold', 'fontSize': 6, 'alignment': TA_RIGHT}),
                        ObjectValue(expression='sum(importe)', left=3.14*cm, style={'fontName': 'Helvetica-Bold', 'fontSize': 6, 'alignment': TA_RIGHT}),
                        ]

                groups = [
                     ReportGroup(
                        attribute_name='organismo',
                        band_header=DetailBand(
                            height=0.6*cm,
                            width = 6.67*cm,
                            elements=[
                                Label(text='>', style={'fontSize': 6}),
                                ObjectValue(expression='organismo',  left=5,style={'fontSize': 6})
                            ]
                        ),
                        band_footer=ReportBand(
                            height = 0.5*cm,
                            elements = [
                                Label(text='>  Total Organismo ====', style={'fontSize': 6}),
                                ObjectValue(expression='sum(cantidad)', left=1.26*cm, style={'fontName': 'Helvetica-Bold', 'fontSize': 6, 'alignment': TA_RIGHT}),
                                ObjectValue(expression='sum(importe)', left=3.14*cm, style={'fontName': 'Helvetica-Bold', 'fontSize': 6, 'alignment': TA_RIGHT}),
                                ],
                            borders = {'top': True, 'bottom': True, 'fontSize':6, 'fontName': 'Helvetica'}
                        ),
                        
                    ),
                    ReportGroup(
                        attribute_name='provincia',
                        band_header=DetailBand(
                            height=0.5*cm,
                            width = 6.67*cm,
                            elements=[
                                Label(text='>> ', style={'fontSize': 6}),
                                ObjectValue(expression='provincia', left=1.5*cm, style={'fontName': 'Helvetica-Bold', 'fontSize': 6, 'alignment': TA_LEFT}),
                            ]
                        ),
                        band_footer=ReportBand(
                            height = 0.5*cm,
                            elements = [
                                Label(text='>> Total Provincia', style={'fontSize': 6}),
                                ObjectValue(expression='sum(cantidad)', left=1.26*cm, style={'fontName': 'Helvetica-Bold', 'fontSize': 6, 'alignment': TA_RIGHT}),
                                ObjectValue(expression='sum(importe)', left=3.14*cm, style={'fontName': 'Helvetica-Bold', 'fontSize': 6, 'alignment': TA_RIGHT}),
                                ],
                            borders = {'top': True, 'bottom': True, 'fontSize':6, 'fontName': 'Helvetica'}
                        ),
                    ), 
                    ReportGroup(
                        attribute_name='cliente',
                        band_header=DetailBand(
                            height=0.5*cm,
                            width = 8*cm,
                            elements=[
                                Label(text='>>>', style={'fontSize': 6}),
                                ObjectValue(expression='cliente', style={'fontSize': 6}, left=2*cm, width = 12*cm)
                            ]
                        ),
                        band_footer=ReportBand(
                            height = 0.5*cm,
                            elements = [
                                Label(text='>>> Total Cliente', style={'fontSize': 6}),
                                ObjectValue(expression='sum(cantidad)', left=1.26*cm, style={'fontName': 'Helvetica-Bold', 'fontSize': 6, 'alignment': TA_RIGHT}),
                                ObjectValue(expression='sum(importe)', left=3.14*cm, style={'fontName': 'Helvetica-Bold', 'fontSize': 6, 'alignment': TA_RIGHT}),
                                ],
                            borders = {'top': True, 'bottom': True, 'fontSize':6, 'fontName': 'Helvetica'}
                        ),
                    ),
                ] 
                    
            if type == "rep_planes":     
                title = 'Planes Contratados'
                class band_detail(ReportBand):

                        height = 0.4*cm
                        elements = [
                            ObjectValue(expression = 'cliente', width=11*cm,left=0.1*cm, style={'fontSize': 6}),
                            ObjectValue(expression = 'plan_ano',left=10*cm, style={'fontSize': 6}),
                            ObjectValue(expression = 'contrato_nro',left=12*cm, style={'fontSize': 6}),
                            ]                      
                    
                class band_page_header(ReportBand):
                    elements = [
                        SystemField(expression='%(report_title)s', top=0.1*cm, left=0, width=BAND_WIDTH,
                            style={'fontName': 'Helvetica-Bold', 'fontSize': 14, 'alignment': TA_CENTER}),
                        SystemField(expression=u'Página %(page_number)d de %(page_count)d', top=0.1*cm,
                            width=BAND_WIDTH, style={'alignment': TA_RIGHT,'fontSize': 5}),
                        SystemField(expression='Impreso el %(now:%d/%m/%Y )s a las %(now:%H:%M)s', top=0.1*cm,
                            width=BAND_WIDTH, style={'alignment': TA_LEFT,'fontSize': 5}),
#                        Image(left=0*cm, top=0*cm, right=0.5*cm, bottom=0.5*cm,filename=os.path.join(cur_dir, 'logo111.png'))
                        ]
                    if filtro.__len__()!=0:    
                        elements+=[Label(text="Filtro:", top=0.9*cm, left=0.1*cm, style={'fontSize': 5}),]
                    tope=1.2*cm
                    for k in range(filtro.__len__()):
                            
                            elements+=[Label(text=filtro[k], top=tope, left=0.1*cm, style={'fontSize': 5}, width=BAND_WIDTH),]
                            tope=tope+0.3*cm
                        
                    tope=tope+0.3*cm
                    elements+=[Label(text="Cliente", top=tope, left=0.1*cm, style={'fontSize':8}),
                    Label(text="Plan Contratado", top=tope, left=9*cm, style={'fontSize':8}),
                    Label(text="Nro. Contarto", top=tope, left=12*cm, style={'fontSize':8}),
                    
                    ]
                    height = tope+0.5*cm
                    borders = {'bottom': True}
                    
            
                class band_page_footer(ReportBand):
                    height = 0.5*cm
                    elements = [
                        Label(text='Comerciax', top=0.1*cm),
                        ]
                    borders = {'top': True}
                
                class band_summary(ReportBand):
                    height = 0.5*cm
                    elements = [
                        Label(text='====  Total General ====', style={'fontSize': 6}),
                        ObjectValue(expression='sum(plan_ano)', left=5.45*cm, style={'fontName': 'Helvetica-Bold', 'fontSize': 6, 'alignment': TA_RIGHT}),
                        ObjectValue(expression='count(cliente)', left=7.5*cm, style={'fontName': 'Helvetica-Bold', 'fontSize': 6, 'alignment': TA_RIGHT}),
                        ]

                groups = [
                     ReportGroup(
                        attribute_name='organismo',
                        band_header=DetailBand(
                            height=0.6*cm,
                            width = 6.67*cm,
                            elements=[
                                Label(text='>', style={'fontSize': 6}),
                                ObjectValue(expression='organismo',  left=5,style={'fontSize': 6})
                            ]
                        ),
                        band_footer=ReportBand(
                            height = 0.5*cm,
                            elements = [
                                Label(text='> Total Organismo', style={'fontSize': 6}),
                                ObjectValue(expression='sum(plan_ano)', left=5.45*cm, style={'fontName': 'Helvetica-Bold','fontSize':6, 'alignment': TA_RIGHT}),
                                ObjectValue(expression='count(cliente)', left=7.5*cm, style={'fontName': 'Helvetica-Bold', 'fontSize': 6, 'alignment': TA_RIGHT}),
                                ],
                            borders = {'top': True, 'bottom': True, 'fontSize':6, 'fontName': 'Helvetica'}
                        ),
                    ),
                    ReportGroup(
                        attribute_name='provincia',
                        band_header=DetailBand(
                            height=0.5*cm,
                            width = 6.67*cm,
                            elements=[
                                Label(text='>>', style={'fontSize': 6}),
                                ObjectValue(expression='provincia', style={'fontSize': 6}, left=2.2*cm)
                            ]
                        ),
                        band_footer=ReportBand(
                            height = 0.5*cm,
                            elements = [
                                Label(text='>> Total Provincia', style={'fontSize': 6}),
                                ObjectValue(expression='sum(plan_ano)', left=5.45*cm, style={'fontName': 'Helvetica-Bold','fontSize': 6, 'alignment': TA_RIGHT}),
                                ObjectValue(expression='count(cliente)', left=7.5*cm, style={'fontName': 'Helvetica-Bold', 'fontSize': 6, 'alignment': TA_RIGHT}),
                                ],
                            borders = {'top': True, 'bottom': True, 'fontSize':6, 'fontName': 'Helvetica'}
                        ),
                    ), 
                ]   
            if type == "rep_planesnocontrat":     
                title = 'Planes Contratados'
                class band_detail(ReportBand):

                        height = 0.4*cm
                        elements = [
                            ObjectValue(expression = 'cliente', width=11*cm,left=0.1*cm, style={'fontSize': 6}),
                            ObjectValue(expression = 'plan_ano',left=12*cm, style={'fontSize': 6}),
                            ]                      
                    
                class band_page_header(ReportBand):
                    elements = [
                        SystemField(expression='%(report_title)s', top=0.1*cm, left=0, width=BAND_WIDTH,
                            style={'fontName': 'Helvetica-Bold', 'fontSize': 14, 'alignment': TA_CENTER}),
                        SystemField(expression=u'Página %(page_number)d de %(page_count)d', top=0.1*cm,
                            width=BAND_WIDTH, style={'alignment': TA_RIGHT,'fontSize': 5}),
                        SystemField(expression='Impreso el %(now:%d/%m/%Y )s a las %(now:%H:%M)s', top=0.1*cm,
                            width=BAND_WIDTH, style={'alignment': TA_LEFT,'fontSize': 5}),
#                        Image(left=0*cm, top=0*cm, right=0.5*cm, bottom=0.5*cm,filename=os.path.join(cur_dir, 'logo111.png'))
                        ]
                    if filtro.__len__()!=0:    
                        elements+=[Label(text="Filtro:", top=0.9*cm, left=0.1*cm, style={'fontSize': 5}),]
                    tope=1.2*cm
                    for k in range(filtro.__len__()):
                            
                            elements+=[Label(text=filtro[k], top=tope, left=0.1*cm, style={'fontSize': 5}, width=BAND_WIDTH),]
                            tope=tope+0.3*cm
                        
                    tope=tope+0.3*cm
                    elements+=[Label(text="Cliente", top=tope, left=0.1*cm, style={'fontSize':8}),
                    Label(text="Plan Contratado", top=tope, left=11.7*cm, style={'fontSize':8}),
                    
                    ]
                    height = tope+0.5*cm
                    borders = {'bottom': True}
                    
            
                class band_page_footer(ReportBand):
                    height = 0.5*cm
                    elements = [
                        Label(text='Comerciax', top=0.1*cm),
                        ]
                    borders = {'top': True}
                
                class band_summary(ReportBand):
                    height = 0.5*cm
                    elements = [
                        Label(text='====  Total General ====', style={'fontSize': 6}),
                        ObjectValue(expression='count(plan_ano)', left=7.2*cm, style={'fontName': 'Helvetica-Bold', 'fontSize': 6, 'alignment': TA_RIGHT}),
                        ]

                groups = [
                     ReportGroup(
                        attribute_name='organismo',
                        band_header=DetailBand(
                            height=0.6*cm,
                            width = 6.67*cm,
                            elements=[
                                Label(text='>', style={'fontSize': 6}),
                                ObjectValue(expression='organismo',  left=5,style={'fontSize': 6})
                            ]
                        ),
                        band_footer=ReportBand(
                            height = 0.5*cm,
                            elements = [
                                Label(text='> Total Organismo', style={'fontSize': 6}),
                                ObjectValue(expression='count(plan_ano)', left=7.2*cm, style={'fontName': 'Helvetica-Bold','fontSize':6, 'alignment': TA_RIGHT}),
                                ],
                            borders = {'top': True, 'bottom': True, 'fontSize':6, 'fontName': 'Helvetica'}
                        ),
                    ),
                    ReportGroup(
                        attribute_name='provincia',
                        band_header=DetailBand(
                            height=0.5*cm,
                            width = 6.67*cm,
                            elements=[
                                Label(text='>>', style={'fontSize': 6}),
                                ObjectValue(expression='provincia', style={'fontSize': 6}, left=2.2*cm)
                            ]
                        ),
                        band_footer=ReportBand(
                            height = 0.5*cm,
                            elements = [
                                Label(text='>> Total Provincia', style={'fontSize': 6}),
                                ObjectValue(expression='count(plan_ano)', left=7.2*cm, style={'fontName': 'Helvetica-Bold','fontSize': 6, 'alignment': TA_RIGHT}),
                                ],
                            borders = {'top': True, 'bottom': True, 'fontSize':6, 'fontName': 'Helvetica'}
                        ),
                    ), 
                ] 
            if type == "cascos_client":     
                title = 'Cascos por Cliente'
                class band_detail(ReportBand):
                        height = 0.4*cm
                        elements = [
#                            ObjectValue(expression='ministerio', left=0.1*cm, style={'fontSize': 6}),
#                            ObjectValue(expression='provincia', left=1.7*cm, style={'fontSize': 6}),
#                            ObjectValue(expression='nombre', left=3.2*cm, width=11*cm, style={'fontSize': 5}),
                            ObjectValue(expression='casco_nro', left=9.2*cm, style={'fontSize': 6}),
                            ObjectValue(expression='descripcion', left=11.0*cm, style={'fontSize': 6}),
                            ObjectValue(expression='recepcioncliente_nro', left=14.4*cm, style={'fontSize': 6}),
                            ObjectValue(expression ='fecha_doc' , left=15*cm, style={'fontSize': 6}),
                            ObjectValue(expression='estado_actual', left=16.2*cm, style={'fontSize': 6}),
                            ]                   
                        
                class band_page_header(ReportBand):
                    
                    elements = [
                        SystemField(expression='%(report_title)s', top=0.1*cm, left=0, width=BAND_WIDTH,
                            style={'fontName': 'Helvetica-Bold', 'fontSize': 14, 'alignment': TA_CENTER}),
                        SystemField(expression=u'Página %(page_number)d de %(page_count)d', top=0.1*cm,
                            width=BAND_WIDTH, style={'alignment': TA_RIGHT,'fontSize': 5}),
                        SystemField(expression='Impreso el %(now:%d/%m/%Y )s a las %(now:%H:%M)s', top=0.1*cm,
                            width=BAND_WIDTH, style={'alignment': TA_LEFT,'fontSize': 5}),]
                    if filtro.__len__()!=0:     
                        elements+=[Label(text="Filtro:", top=0.9*cm, left=0.1*cm, style={'fontSize': 5}),]
                    tope=1.2*cm
                    for k in range(filtro.__len__()):
                            
                        elements+=[Label(text=filtro[k], top=tope, left=0.1*cm, style={'fontSize': 5}, width=BAND_WIDTH),]
                        tope=tope+0.3*cm
                        
                    tope=tope+0.3*cm
                    elements += [
                        Label(text="Organismo", top=tope, left=0.1*cm, style={'fontSize': 8}),
                        Label(text="Provincia", top=tope , left=1.7*cm, style={'fontSize': 8}),
                        Label(text="Cliente", top=tope , left=3.2*cm, style={'fontSize': 8}),
                        Label(text="Nro. Casco", top=tope, left=9.2*cm, style={'fontSize': 8}),
                        Label(text="Medida", top=tope, left=11.0*cm, style={'fontSize': 8}),
                        Label(text="Docum.Ent.", top=tope, left=14.4*cm, style={'fontSize': 8}),
                        Label(text="", top=tope, left=15*cm, style={'fontSize': 8}),
                        Label(text="Estado Actual", top=tope, left=16.2*cm, style={'fontSize': 8}),
                    ]
                    height = tope+0.5*cm
                    borders = {'bottom': True}
                    
                class band_page_footer(ReportBand):
                    height = 0.5*cm
                    elements = [
                        Label(text='Comerciax', top=0.1*cm),
                        ]
                    borders = {'top': True}
                
                groups = [
                     ReportGroup(
                        attribute_name='ministerio',
                        band_header=DetailBand(
                            height=0.6*cm,
                            width = 6.67*cm,
                            elements=[
                                Label(text='>', style={'fontSize': 6}),
                                ObjectValue(expression='ministerio',  left=5,style={'fontSize': 6})
                            ]
                        ),
#                        band_footer=ReportBand(
#                            height = 0.5*cm,
#                            elements = [
#                                Label(text='>  Total Organismo ====', style={'fontSize': 6}),
#                                ObjectValue(expression='sum(cantidad)', left=1.26*cm, style={'fontName': 'Helvetica-Bold', 'fontSize': 6, 'alignment': TA_RIGHT}),
#                                ObjectValue(expression='sum(importe)', left=5.36*cm, style={'fontName': 'Helvetica-Bold', 'fontSize': 6, 'alignment': TA_RIGHT}),
#                                ],
#                            borders = {'top': True, 'bottom': True, 'fontSize':6, 'fontName': 'Helvetica'}
#                        ),
                        
                    ),
                    ReportGroup(
                        attribute_name='provincia',
                        band_header=DetailBand(
                            height=0.5*cm,
                            width = 6.67*cm,
                            elements=[
                                Label(text='>> ', style={'fontSize': 6}),
                                ObjectValue(expression='provincia', left=1.5*cm, style={'fontName': 'Helvetica-Bold', 'fontSize': 6, 'alignment': TA_LEFT}),
                            ]
                        ),
#                        band_footer=ReportBand(
#                            height = 0.5*cm,
#                            elements = [
#                                Label(text='>> Total Provincia', style={'fontSize': 6}),
#                                ObjectValue(expression='sum(cantidad)', left=1.26*cm, style={'fontName': 'Helvetica-Bold', 'fontSize': 6, 'alignment': TA_RIGHT}),
#                                ObjectValue(expression='sum(importe)', left=5.36*cm, style={'fontName': 'Helvetica-Bold', 'fontSize': 6, 'alignment': TA_RIGHT}),
#                                ],
#                            borders = {'top': True, 'bottom': True, 'fontSize':6, 'fontName': 'Helvetica'}
#                        ),
                    ), 
                    ReportGroup(
                        attribute_name='nombre',
                        band_header=DetailBand(
                            height=0.5*cm,
                            width = 8*cm,
                            elements=[
                                Label(text='>>>', style={'fontSize': 6}),
                                ObjectValue(expression='nombre', style={'fontSize': 6}, left=2*cm, width = 12*cm)
                            ]
                        ),
#                        band_footer=ReportBand(
#                            height = 0.5*cm,
#                            elements = [
#                                Label(text='>>> Total Cliente', style={'fontSize': 6}),
#                                ObjectValue(expression='sum(cantidad)', left=1.26*cm, style={'fontName': 'Helvetica-Bold', 'fontSize': 6, 'alignment': TA_RIGHT}),
#                                ObjectValue(expression='sum(importe)', left=5.36*cm, style={'fontName': 'Helvetica-Bold', 'fontSize': 6, 'alignment': TA_RIGHT}),
#                                ],
#                            borders = {'top': True, 'bottom': True, 'fontSize':6, 'fontName': 'Helvetica'}
#                        ),
                    ),
                ] 
            if type == "cascos_estTransf":     
                title = 'Cascos por Estado'                
                class band_detail(ReportBand):
                        height = 0.4*cm
                        elements = [
                            ObjectValue(expression='estado_actual', left=0.1*cm, width=3*cm,style={'fontSize': 6}),
                            ObjectValue(expression='casco_nro', left=2*cm, style={'fontSize': 6}),
                            ObjectValue(expression='medida', left=4*cm, style={'fontSize': 5}),
                            ObjectValue(expression='cliente',  width=11*cm,left=7*cm, style={'fontSize': 6}),
                            ObjectValue(expression='dias', left=14*cm, style={'fontSize': 6}),
                            ObjectValue(expression='destino', left=16*cm, style={'fontSize': 6}),
                            ]                   
                        
                class band_page_header(ReportBand):
                    elements = [
                        SystemField(expression='%(report_title)s', top=0.1*cm, left=0, width=BAND_WIDTH,
                            style={'fontName': 'Helvetica-Bold', 'fontSize': 14, 'alignment': TA_CENTER}),
                        SystemField(expression='Impreso el %(now:%d/%m/%Y )s a las %(now:%H:%M)s', top=0.1*cm,
                            width=BAND_WIDTH, style={'alignment': TA_LEFT,'fontSize': 5}),
                        SystemField(expression=u'Página %(page_number)d de %(page_count)d', top=0.1*cm,
                            width=BAND_WIDTH, style={'alignment': TA_RIGHT,'fontSize': 8}),]
                    if filtro.__len__()!=0:
                        elements+=[Label(text="Filtro:", top=0.9*cm, left=0.1*cm, style={'fontSize': 5}),]
                    tope=1.2*cm
                    for k in range(filtro.__len__()):
                            elements+=[Label(text=filtro[k], top=tope, left=0.1*cm, style={'fontSize': 5}, width=BAND_WIDTH),]
                            tope=tope+0.3*cm
                    tope=tope+0.3*cm
                    elements+=[Label(text="Estado", top=tope, left=0.1*cm, style={'fontSize': 8}),
                        Label(text="Nro. Casco", top=tope , left=2*cm, style={'fontSize': 8}),
                        Label(text="Medida", top=tope , left=4*cm, style={'fontSize': 8}),
                        Label(text="Cliente", top=tope, left=7*cm, style={'fontSize': 8}),
                        Label(text="Edad (Días)", top=tope, left=14*cm, style={'fontSize': 8}),
                        Label(text="Destino", top=tope, left=16*cm, style={'fontSize': 8}),
                    ]
                    borders = {'bottom': True}
                    height = tope+0.5*cm
            
                class band_page_footer(ReportBand):
                    height = 0.5*cm
                    elements = [
                        Label(text='Comerciax', top=0.1*cm),
                        ]
                    borders = {'top': True}
            if type == "cascos_est":     
                title = 'Cascos por Estado' 
                self.elements2=[]               
                class band_detail(ReportBand):
                        height = 0.4*cm
                        elements = [
                            ObjectValue(expression='estado_actual', left=0.1*cm, style={'fontSize': 6}),
                            ObjectValue(expression='casco_nro', left=3.5*cm, style={'fontSize': 6}),
                            ObjectValue(expression='medida', left=5*cm, style={'fontSize': 5}),
                            ObjectValue(expression='cliente',  width=11*cm,left=8*cm, style={'fontSize': 6}),
                            ObjectValue(expression='dias', left=16*cm, style={'fontSize': 6}),
                            ]                   
                        
                class band_page_header(ReportBand):
                    elements = [
                        SystemField(expression='%(report_title)s', top=0.1*cm, left=0, width=BAND_WIDTH,
                            style={'fontName': 'Helvetica-Bold', 'fontSize': 14, 'alignment': TA_CENTER}),
                        SystemField(expression='Impreso el %(now:%d/%m/%Y )s a las %(now:%H:%M)s', top=0.1*cm,
                            width=BAND_WIDTH, style={'alignment': TA_LEFT,'fontSize': 5}),
                        SystemField(expression=u'Página %(page_number)d de %(page_count)d', top=0.1*cm,
                            width=BAND_WIDTH, style={'alignment': TA_RIGHT,'fontSize': 8}),]
                    if filtro.__len__()!=0:
                        elements+=[Label(text="Filtro:", top=0.9*cm, left=0.1*cm, style={'fontSize': 5}),]
                    tope=1.2*cm
                    for k in range(filtro.__len__()):
                        elements+=[Label(text=filtro[k], top=tope, left=0.1*cm, style={'fontSize': 5}, width=BAND_WIDTH),]
                        tope=tope+0.3*cm
                    tope=tope+0.3*cm
                    elements+=[Label(text="Estado", top=tope, left=0.1*cm, style={'fontSize': 8}),
                        Label(text="Nro. Casco", top=tope , left=3.1*cm, style={'fontSize': 8}),
                        Label(text="Medida", top=tope , left=5*cm, style={'fontSize': 8}),
                        Label(text="Cliente", top=tope, left=8*cm, style={'fontSize': 8}),
                        Label(text="Edad del Estado(Días)", top=tope, left=15*cm, style={'fontSize': 8}),
                    ]
                    borders = {'bottom': True}
                    height = tope+0.5*cm
            
                class band_page_footer(ReportBand):
                    height = 0.5*cm
                    elements = [
                        Label(text='Comerciax', top=0.1*cm),
                        ]
                    borders = {'top': True}
            if type == "cascos_traza":     
                title = 'Trazabilidad de Cascos'                
                class band_detail(ReportBand):
                        height = 0.4*cm
                        elements = [
                            ObjectValue(expression='nombre', left=0.1*cm, width=BAND_WIDTH, style={'fontSize': 6}),
                            ObjectValue(expression='casco_nro', left=6.3*cm, style={'fontSize': 6}),
                            ObjectValue(expression='descripcion', left=8*cm, style={'fontSize': 5}),
                            ObjectValue(expression= 'estado', left=11*cm, style={'fontSize': 6}),
                            ObjectValue(expression='fecha_doc', left=15.5*cm, style={'fontSize': 6}),
                            ObjectValue(expression='nrodoc', left=17*cm, style={'fontSize': 6}),
                            ]                   
                        
                class band_page_header(ReportBand):
                    elements = [
                        SystemField(expression='%(report_title)s', top=0.1*cm, left=0, width=BAND_WIDTH,
                            style={'fontName': 'Helvetica-Bold', 'fontSize': 14, 'alignment': TA_CENTER}),
                        SystemField(expression='Impreso el %(now:%d/%m/%Y )s a las %(now:%H:%M)s', top=0.1*cm,
                            width=BAND_WIDTH, style={'alignment': TA_LEFT,'fontSize': 5}),
                        SystemField(expression=u'Página %(page_number)d de %(page_count)d', top=0.1*cm,
                            width=BAND_WIDTH, style={'alignment': TA_RIGHT,'fontSize': 8}),]
                    if filtro.__len__()!=0:
                        elements+=[Label(text="Filtro:", top=0.9*cm, left=0.1*cm, style={'fontSize': 5}),]
                    tope=1.2*cm
                    for k in range(filtro.__len__()):
                            elements+=[Label(text=filtro[k], top=tope, left=0.1*cm, style={'fontSize': 5}, width=BAND_WIDTH),]
                            tope=tope+0.3*cm
                    tope=tope+0.3*cm
                    elements+=[Label(text="Cliente", top=tope, left=0.1*cm, style={'fontSize': 8}),
                        Label(text="Nro. Casco", top=tope , left=6*cm, style={'fontSize': 8}),
                        Label(text="Medida", top=tope , left=8*cm, style={'fontSize': 8}),
                        Label(text="Estado", top=tope, left=11*cm, style={'fontSize': 8}),
                        Label(text="Fecha", top=tope, left=15.5*cm, style={'fontSize': 8}),
                        Label(text="Docum.", top=tope, left=17*cm, style={'fontSize': 8}),
                    ]
                    height = tope+0.5*cm
                    borders = {'bottom': True}
            
                class band_page_footer(ReportBand):
                    height = 0.5*cm
                    elements = [
                        Label(text='Comerciax', top=0.1*cm),
#                        SystemField(expression='Impreso en %(now:%Y, %b %d)s a las %(now:%H:%M)s', top=0.1*cm,
#                            width=BAND_WIDTH, style={'alignment': TA_RIGHT}),
                        ]
                    borders = {'top': True}
            if type == "cascos_venta":     
                title = 'Cascos para la Venta en PT'                
                class band_detail(ReportBand):
                        height = 0.4*cm
                        elements = [
                            ObjectValue(expression='producto', left=0.11*cm, width=BAND_WIDTH, style={'fontSize': 6}),
                            ObjectValue(expression='casco_nro', left=6*cm, style={'fontSize': 6}),
                            ObjectValue(expression='nombre', width=11*cm,left=12*cm, style={'fontSize': 6}),                      
                            ]
                class band_page_header(ReportBand):
                    elements = [
                        SystemField(expression='%(report_title)s', top=0.1*cm, left=0, width=BAND_WIDTH,
                            style={'fontName': 'Helvetica-Bold', 'fontSize': 14, 'alignment': TA_CENTER}),
                        SystemField(expression='Impreso el %(now:%d/%m/%Y )s a las %(now:%H:%M)s', top=0.1*cm,
                            width=BAND_WIDTH, style={'alignment': TA_LEFT,'fontSize': 5}),
                        SystemField(expression=u'Página %(page_number)d de %(page_count)d', top=0.1*cm,
                            width=BAND_WIDTH, style={'alignment': TA_RIGHT,'fontSize': 8}),]
                    if filtro.__len__()!=0:
                        elements+=[Label(text="Filtro:", top=0.9*cm, left=0.1*cm, style={'fontSize': 5}),]
                    tope=1.2*cm
                    for k in range(filtro.__len__()):
                            
                            elements+=[Label(text=filtro[k], top=tope, left=0.1*cm, style={'fontSize': 5}, width=BAND_WIDTH),]
                            tope=tope+0.3*cm
                        
                    tope=tope+0.3*cm
                    elements+=[Label(text="Medida", top=tope, left=0.11*cm, style={'fontSize': 8}),
                        Label(text="Nro. Casco", top=tope , left=5.8*cm, style={'fontSize': 8}),
                        Label(text="Cliente", top=tope , left=12*cm, style={'fontSize': 8}),                      
                    ]
                    borders = {'bottom': True}
                    height = tope+0.5*cm
            
                class band_page_footer(ReportBand):
                    height = 0.5*cm
                    elements = [
                        Label(text='Comerciax', top=0.1*cm),
#                        SystemField(expression='Impreso en %(now:%Y, %b %d)s a las %(now:%H:%M)s', top=0.1*cm,
#                            width=BAND_WIDTH, style={'alignment': TA_RIGHT}),
                        ]
                    borders = {'top': True}
            #===================================================================
            # Pendiente
            #===================================================================
            if type == "reg_cobros":     
                title = 'Registro de Cobros'                
                class band_detail(ReportBand):
                        height = 0.4*cm
                        elements = [
                            ObjectValue(expression='producto', left=2.5*cm, width=BAND_WIDTH, style={'fontSize': 6}),
                            ObjectValue(expression='casco_nro', left=10*cm, style={'fontSize': 6}),
                            ObjectValue(expression='nombre', left=15*cm, style={'fontSize': 6}),                      
                            ]
                class band_page_header(ReportBand):
                    elements = [
                        SystemField(expression='%(report_title)s', top=0.1*cm, left=0, width=BAND_WIDTH,
                            style={'fontName': 'Helvetica-Bold', 'fontSize': 14, 'alignment': TA_CENTER}),
                        SystemField(expression='Impreso el %(now:%d/%m/%Y )s a las %(now:%H:%M)s', top=0.1*cm,
                            width=BAND_WIDTH, style={'alignment': TA_LEFT,'fontSize': 5}),
                        SystemField(expression=u'Página %(page_number)d de %(page_count)d', top=0.1*cm,
                            width=BAND_WIDTH, style={'alignment': TA_RIGHT,'fontSize': 8}),]
                    if filtro.__len__()!=0:
                        elements+=[Label(text="Filtro:", top=0.9*cm, left=0.1*cm, style={'fontSize': 5}),]
                    tope=1.2*cm
                    for k in range(filtro.__len__()):
                            elements+=[Label(text=filtro[k], top=tope, left=0.1*cm, style={'fontSize': 5}, width=BAND_WIDTH),]
                            tope=tope+0.3*cm
                    tope=tope+0.3*cm
                    elements+=[Label(text="Medida", top=1.20*cm, left=3*cm, style={'fontSize': 8}),
                        Label(text="Nro. Casco", top=1.20*cm , left=9.8*cm, style={'fontSize': 8}),
                        Label(text="Cliente", top=1.20*cm , left=15.5*cm, style={'fontSize': 8}),              
                    ]
                    height =tope+0.5*cm
                    borders = {'bottom': True}
            
                class band_page_footer(ReportBand):
                    height = 0.5*cm
                    elements = [
                        Label(text='Comerciax', top=0.1*cm),
#                        SystemField(expression='Impreso en %(now:%Y, %b %d)s a las %(now:%H:%M)s', top=0.1*cm,
#                            width=BAND_WIDTH, style={'alignment': TA_RIGHT}),
                        ]
                    borders = {'top': True}
            if type == "rec_organismos":     
                title = 'Servicio de Recape a Organismos'
                class band_detail(ReportBand):                    
                        height = 0.4*cm
                        
                        elements = [
                            ObjectValue(expression='codigo', left=1*cm, style={'fontSize': 6}),
                            ObjectValue(expression='nro', left=3*cm, style={'fontSize': 6}),
                            ObjectValue(expression='cliente',width=15*cm,left=5*cm, style={'fontSize': 6}),
                            ObjectValue(expression='cantidad', left=12.5*cm, style={'fontSize': 6}),
                            ObjectValue(expression='cuc', left=9.5*cm, style={'fontSize': 6,'alignment': TA_RIGHT}),
                            ObjectValue(expression = 'cup' , left=12*cm, style={'fontSize': 6,'alignment': TA_RIGHT}),
                        ]
#                            borders = {'bottom': True}
                class band_page_header(ReportBand):
                    elements = [
                        SystemField(expression='%(report_title)s', top=0.1*cm, left=0, width=BAND_WIDTH,
                            style={'fontName': 'Helvetica-Bold', 'fontSize': 14, 'alignment': TA_CENTER}),
                        SystemField(expression='Impreso el %(now:%d/%m/%Y )s a las %(now:%H:%M)s', top=0.1*cm,
                            width=BAND_WIDTH, style={'alignment': TA_LEFT,'fontSize': 5}),
                        SystemField(expression=u'Página %(page_number)d de %(page_count)d', top=0.1*cm,
                            width=BAND_WIDTH, style={'alignment': TA_RIGHT,'fontSize': 8}),]
                    if filtro.__len__()!=0:
                        elements+=[Label(text="Filtro:", top=0.9*cm, left=0.1*cm, style={'fontSize': 5}),]
                    tope=1.2*cm
                    for k in range(filtro.__len__()):
                            elements+=[Label(text=filtro[k], top=tope, left=0.1*cm, style={'fontSize': 5}, width=BAND_WIDTH),]
                            tope=tope+0.3*cm
                    tope=tope+0.3*cm
                    height = tope+0.5*cm
                    elements+=[Label(text="Código", top=tope, left=1*cm,style={'fontSize': 8}),
                        Label(text="Nro.", top=tope , left=3.2*cm, style={'fontSize': 8}),
                        Label(text="Cliente", top=tope , left=5*cm,style={'fontSize': 8}),
                        Label(text="Cantidad", top=tope, left=11.5*cm,style={'fontSize': 8}),
                        Label(text="Importe MLC", top=tope, left=13.5*cm,style={'fontSize': 8}),
                        Label(text="Importe CUP", top=tope, left=16*cm,style={'fontSize': 8}),
                    ]
                    borders = {'bottom': True}
                    
            
                class band_page_footer(ReportBand):
                    height = 0.5*cm
                    elements = [
                        Label(text='Comerciax', top=0.1*cm),
#                        SystemField(expression='Impreso en %(now:%Y, %b %d)s a las %(now:%H:%M)s', top=0.1*cm,
#                            width=BAND_WIDTH, style={'alignment': TA_RIGHT}),
                        ]
                    borders = {'top': True}
             
                class band_summary(ReportBand):
                    height = 0.5*cm
                    elements = [
                        Label(text='Especialista Comercial:', left=1.5*cm ,top=1.5*cm), 
                        Label(text='Director:', left=9*cm,top=1.5*cm),  
                        Label(text='Jefe de Area Comercial:', left=13.5*cm,top=1.5*cm),        
                        ]
#                    borders = {'top': True}          
                groups = [
                     ReportGroup(
                        attribute_name='organismo',
                        band_header=DetailBand(
                            height=0.6*cm,
                            elements=[
                                ObjectValue(expression='organismo',  width=BAND_WIDTH,style={'fontSize': 8})
                            ]
                        ),
                        band_footer=ReportBand(
                            height = 1.0*cm,
                            elements = [
                                Label(text='SubTotal del Organismo:'),
                                ObjectValue(expression='sum(cuc)', left=13.5*cm,style={'fontSize': 8}),
                                ObjectValue(expression='sum(cup)', left=16*cm,style={'fontSize': 8}),                             
                                ],
                            borders = {'top': True},
                        ),
                    ),                  
                ]
            if type == "transf_env":     
                title = 'Transferencias Enviadas'
                class band_detail(ReportBand):                    
                        height = 0.4*cm
                        
                        elements = [
                            ObjectValue(expression='medida', width=20*cm,left=3.2*cm, style={'fontSize': 6}),
                            ObjectValue(expression='transferidas',left=8.3*cm, style={'fontSize': 6}),
                            ObjectValue(expression='procesadas', left=10.9*cm, style={'fontSize': 6}),
                            ObjectValue(expression='noprocesadas', left=8.5*cm, style={'fontSize': 6,'alignment': TA_RIGHT}),
                            ObjectValue(expression='inservibles', left=10.5*cm, style={'fontSize': 6,'alignment': TA_RIGHT}),
                            ObjectValue(expression='pendientes', left=12.5*cm, style={'fontSize': 6,'alignment': TA_RIGHT}),
                        ]
#                            borders = {'bottom': True}
                class band_page_header(ReportBand):
                    elements = [
                        SystemField(expression='%(report_title)s', top=0.1*cm, left=0, width=BAND_WIDTH,
                            style={'fontName': 'Helvetica-Bold', 'fontSize': 14, 'alignment': TA_CENTER}),
                        SystemField(expression='Impreso el %(now:%d/%m/%Y )s a las %(now:%H:%M)s', top=0.1*cm,
                            width=BAND_WIDTH, style={'alignment': TA_LEFT,'fontSize': 5}),
                        SystemField(expression=u'Página %(page_number)d de %(page_count)d', top=0.1*cm,
                            width=BAND_WIDTH, style={'alignment': TA_RIGHT,'fontSize': 8}),]
                    if filtro.__len__()!=0:
                        elements+=[Label(text="Filtro:", top=0.9*cm, left=0.1*cm, style={'fontSize': 5}),]
                    tope=1.2*cm
                    for k in range(filtro.__len__()):
                            elements+=[Label(text=filtro[k], top=tope, left=0.1*cm, style={'fontSize': 5}, width=BAND_WIDTH),]
                            tope=tope+0.3*cm
                    tope=tope+0.3*cm
                    height = tope+0.5*cm
                    elements+=[Label(text="Transferida a:", top=tope, left=1*cm,style={'fontSize': 8}),
                        Label(text="Medida", top=tope , left=3.2*cm, style={'fontSize': 8}),
                        Label(text="Transferidas", top=tope , left=8*cm,style={'fontSize': 8}),
                        Label(text="Procesadas", top=tope, left=10.5*cm,style={'fontSize': 8}),
                        Label(text="Dev. sin Proc.", top=tope, left=12.5*cm,style={'fontSize': 8}),
                        Label(text="Dev. Inserv.", top=tope, left=14.5*cm,style={'fontSize': 8}),
                        Label(text="Pendientes", top=tope, left=16.5*cm,style={'fontSize': 8}),
                    ]
                    borders = {'bottom': True}
                    
            
                class band_page_footer(ReportBand):
                    height = 0.5*cm
                    elements = [
                        Label(text='Comerciax', top=0.1*cm),
#                        SystemField(expression='Impreso en %(now:%Y, %b %d)s a las %(now:%H:%M)s', top=0.1*cm,
#                            width=BAND_WIDTH, style={'alignment': TA_RIGHT}),
                        ]
                    borders = {'top': True}
             
                class band_summary(ReportBand):
                   #height = 0.2*cm  
                    elements = [
                            Label(text='Total General:',style={'fontSize': 8,'fontName': 'Helvetica-Bold'}),
                                    ObjectValue(expression='sum(transferidas)', left=8*cm, style={'fontSize': 6,'fontName': 'Helvetica-Bold'}),
                                    ObjectValue(expression='sum(procesadas)',left=10.5*cm, style={'fontSize': 6,'fontName': 'Helvetica-Bold'}), 
                                    ObjectValue(expression='sum(noprocesadas)',  left=13.5*cm, style={'fontSize': 6,'fontName': 'Helvetica-Bold'}),
                                    ObjectValue(expression='sum(inservibles)',  left=15.5*cm, style={'fontSize': 6,'fontName': 'Helvetica-Bold'}),
                                    ObjectValue(expression='sum(pendientes)',  left=17.5*cm, style={'fontSize': 6,'fontName': 'Helvetica-Bold'}),
                            ]       
                groups = [
                     ReportGroup(
                        attribute_name='cliente',
                        band_header=DetailBand(
#                            height=0.6*cm,
                            elements=[
                                ObjectValue(expression='cliente',  width=BAND_WIDTH,style={'fontSize': 8,'fontName': 'Helvetica-Bold'})
                            ]
                        ),
                        band_footer=ReportBand(
                            height = 1.0*cm,
                            elements = [
                                Label(text='SubTotal Cliente:',style={'fontSize': 8,'fontName': 'Helvetica-Bold'}),
                                ObjectValue(expression='sum(transferidas)', left=8*cm,style={'fontSize': 6,'fontName': 'Helvetica-Bold'}),
                                ObjectValue(expression='sum(procesadas)', left=10.5*cm,style={'fontSize': 6,'fontName': 'Helvetica-Bold'}),  
                                ObjectValue(expression='sum(noprocesadas)', left=13.5*cm,style={'fontSize': 6,'fontName': 'Helvetica-Bold'}), 
                                ObjectValue(expression='sum(inservibles)',  left=15.5*cm, style={'fontSize': 6,'fontName': 'Helvetica-Bold'}),
                                ObjectValue(expression='sum(pendientes)',  left=17.5*cm, style={'fontSize': 6,'fontName': 'Helvetica-Bold'}),                           
                                ],
                            borders = {'top': True},
                        ),
                    ),                  
                ]

            if type == "plazos_fabrica":     
                title = 'Plazos en Fábrica'                
                class band_detail(ReportBand):
                        height = 0.4*cm
                        elements = [
                            ObjectValue(expression='casco', left=1*cm, style={'fontSize': 8}),
                            ObjectValue(expression='dip', left=2*cm, style={'fontSize': 8}),
                            ObjectValue(expression= 'dvp', left=3*cm, style={'fontSize': 8}),
                            ObjectValue(expression='er', left=4*cm, style={'fontSize': 8}),
                            ObjectValue(expression='ree', left=5*cm, style={'fontSize': 8}),
                            ObjectValue(expression='totalcasco', left=6.3*cm, style={'fontSize': 8}),
                            ObjectValue(expression='produccion', left=8.5*cm, style={'fontSize': 8}),
                            ObjectValue(expression='producciont', left=11.5*cm, style={'fontSize': 8}),
                            ]                   
                        
                class band_page_header(ReportBand):
                    elements = [
                        SystemField(expression='%(report_title)s', top=0.1*cm, left=0, width=BAND_WIDTH,
                            style={'fontName': 'Helvetica-Bold', 'fontSize': 14, 'alignment': TA_CENTER}),
                        SystemField(expression='Impreso el %(now:%d/%m/%Y )s a las %(now:%H:%M)s', top=0.1*cm,
                            width=BAND_WIDTH, style={'alignment': TA_LEFT,'fontSize': 5}),
                        SystemField(expression=u'Página %(page_number)d de %(page_count)d', top=0.1*cm,
                            width=BAND_WIDTH, style={'alignment': TA_RIGHT,'fontSize': 8}),]
                    tope=1.2*cm
                    tope=tope+0.3*cm
                    elements+=[
                        Label(text="Almacén de Casco ", top=tope-11 , left=1*cm, style={'fontSize': 8, 'alignment': TA_CENTER}),
                        Label(text="_______________________________", top=tope-9 , left=1*cm, style={'fontSize': 8}),
                        Label(text="Alm", top=tope , left=1*cm, style={'fontSize': 8}),
                        Label(text="DIP", top=tope , left=2*cm, style={'fontSize': 8}),
                        Label(text="DVP", top=tope, left=3*cm, style={'fontSize': 8}),
                        Label(text="ER", top=tope, left=4*cm, style={'fontSize': 8}),
                        Label(text="REE", top=tope, left=5*cm, style={'fontSize': 8}),
                        Label(text="Total Casco", top=tope, left=6*cm, style={'fontSize': 8}),
                        Label(text="Cascos en Proceso", top=tope, left=8*cm, style={'fontSize': 8}),
                        Label(text="Prod. Terminada", top=tope, left=11*cm, style={'fontSize': 8}),
                    ]
                    height = tope+0.5*cm
                    borders = {'bottom': True}
            
                class band_page_footer(ReportBand):
                    height = 0.5*cm
                    elements = [
                        Label(text='Comerciax', top=0.1*cm),
#                        SystemField(expression='Impreso en %(now:%Y, %b %d)s a las %(now:%H:%M)s', top=0.1*cm,
#                            width=BAND_WIDTH, style={'alignment': TA_RIGHT}),
                        ]
                    borders = {'top': True}            
            if type == "inv_fismen":     
                title = 'Inventario Físico'                
                class band_detail(ReportBand):
                        height = 0.4*cm
                        elements = [
                            ObjectValue(expression='medida', left=0.1*cm, style={'fontSize': 8}),
                            ObjectValue(expression='Casco', left=6*cm, style={'fontSize': 8}),
                            ObjectValue(expression='DIP', left=7*cm, style={'fontSize': 8}),
                            ObjectValue(expression= 'DVP', left=8*cm, style={'fontSize': 8}),
                            ObjectValue(expression='ER', left=9*cm, style={'fontSize': 8}),
                            ObjectValue(expression='REE', left=10*cm, style={'fontSize': 8}),
                            ObjectValue(expression='Produccion', left=11.5*cm, style={'fontSize': 8}),
                            ObjectValue(expression='ProduccionT', left=14.5*cm, style={'fontSize': 8}),
                            ObjectValue(expression='TotalL', left=12.5*cm, style={'fontSize': 8,'alignment':TA_RIGHT}),
                            ]                   
                        
                class band_page_header(ReportBand):
                    elements = [
                        SystemField(expression='%(report_title)s', top=0.1*cm, left=0, width=BAND_WIDTH,
                            style={'fontName': 'Helvetica-Bold', 'fontSize': 14, 'alignment': TA_CENTER}),
                        SystemField(expression='Impreso el %(now:%d/%m/%Y )s a las %(now:%H:%M)s', top=0.1*cm,
                            width=BAND_WIDTH, style={'alignment': TA_LEFT,'fontSize': 5}),
                        SystemField(expression=u'Página %(page_number)d de %(page_count)d', top=0.1*cm,
                            width=BAND_WIDTH, style={'alignment': TA_RIGHT,'fontSize': 8}),]
                    if filtro.__len__()!=0:
                        elements+=[Label(text="Filtro:", top=0.9*cm, left=0.1*cm, style={'fontSize': 5}),]
                    tope=1.2*cm
                    for k in range(filtro.__len__()):
                            elements+=[Label(text=filtro[k], top=tope, left=0.1*cm, style={'fontSize': 5}, width=BAND_WIDTH),]
                            tope=tope+0.3*cm
                    tope=tope+0.3*cm
                    elements+=[Label(text="Medida", top=tope, left=0.1*cm, style={'fontSize': 8}),
                        Label(text="Almacén de Casco ", top=tope-11 , left=6*cm, style={'fontSize': 8, 'alignment': TA_CENTER}),
                        Label(text="_______________________________", top=tope-9 , left=6*cm, style={'fontSize': 8}),
                        Label(text="Alm", top=tope , left=6*cm, style={'fontSize': 8}),
                        Label(text="DIP", top=tope , left=7*cm, style={'fontSize': 8}),
                        Label(text="DVP", top=tope, left=8*cm, style={'fontSize': 8}),
                        Label(text="ER", top=tope, left=9*cm, style={'fontSize': 8}),
                        Label(text="REE", top=tope, left=10*cm, style={'fontSize': 8}),
                        Label(text="Cascos en Proceso", top=tope, left=11*cm, style={'fontSize': 8}),
                        Label(text="Prod. Terminada", top=tope, left=14*cm, style={'fontSize': 8}),
                        Label(text="Total", top=tope, left=17*cm, style={'fontSize': 8}),
                    ]
                    height = tope+0.5*cm
                    borders = {'bottom': True}
            
                class band_page_footer(ReportBand):
                    height = 0.5*cm
                    elements = [
                        Label(text='Comerciax', top=0.1*cm),
#                        SystemField(expression='Impreso en %(now:%Y, %b %d)s a las %(now:%H:%M)s', top=0.1*cm,
#                            width=BAND_WIDTH, style={'alignment': TA_RIGHT}),
                        ]
                    borders = {'top': True}   
            if type == "fac_cobrar":
                    title = 'Facturas por Cobrar'
                    class band_detail(ReportBand):                    
                            height = 0.4*cm                        
                            elements = [
                                ObjectValue(expression='nro', left=5*cm, style={'fontSize': 6}),
                                ObjectValue(expression='fecha', left=6.6*cm, style={'fontSize': 6}),
                                ObjectValue(expression='edad', left=3.5*cm, style={'fontSize': 6,'alignment': TA_RIGHT}),
                                ObjectValue(expression='importecup', left=5.2*cm, style={'fontSize': 6,'alignment': TA_RIGHT}),
                                ObjectValue(expression = 'importecuc' , left=6.6*cm, style={'fontSize': 6,'alignment': TA_RIGHT}),
                                ObjectValue(expression='cobradocup', left=8*cm, style={'fontSize': 6,'alignment': TA_RIGHT}),
                                ObjectValue(expression = 'cobradocuc' , left=9.2*cm, style={'fontSize': 6,'alignment': TA_RIGHT}),
                                ObjectValue(expression='pendientecup', left=10.7*cm, style={'fontSize': 6,'alignment': TA_RIGHT}),
                                ObjectValue(expression = 'pendientecuc' , left=12.2*cm, style={'fontSize': 6,'alignment': TA_RIGHT}),
                            ]
    #                            borders = {'bottom': True}
                    class band_page_header(ReportBand):
                        elements = [
                            SystemField(expression='%(report_title)s', top=0.1*cm, left=0, width=BAND_WIDTH,
                                style={'fontName': 'Helvetica-Bold', 'fontSize': 14, 'alignment': TA_CENTER}),
                            SystemField(expression='Impreso el %(now:%d/%m/%Y )s a las %(now:%H:%M)s', top=0.1*cm,
                                width=BAND_WIDTH, style={'alignment': TA_LEFT,'fontSize': 5}),
                            SystemField(expression=u'Página %(page_number)d de %(page_count)d', top=0.1*cm,
                                width=BAND_WIDTH, style={'alignment': TA_RIGHT,'fontSize': 8}),]
                        if filtro.__len__()!=0:
                            elements+=[Label(text="Filtro:", top=0.9*cm, left=0.1*cm, style={'fontSize': 5}),]
                        tope=1.2*cm
                        for k in range(filtro.__len__()):
                                elements+=[Label(text=filtro[k], top=tope, left=0.1*cm, style={'fontSize': 5}, width=BAND_WIDTH),]
                                tope=tope+0.3*cm
                        tope=tope+0.3*cm
                        height = tope+0.5*cm
                        elements+=[Label(text="Cliente", top=tope, left=0.11*cm,style={'fontSize': 8}),
                            Label(text="Factura", top=tope , left=5.5*cm, style={'fontSize': 8}),
                            Label(text="Fecha", top=tope , left=6.8*cm,style={'fontSize': 8}),
                            Label(text="Edad", top=tope, left=8.0*cm,style={'fontSize': 8}),                    
                            Label(text="CUP", top=tope, left=9.5*cm,style={'fontSize': 8}, borders = {'bottom': True}),
                            Label(text="MLC", top=tope, left=11*cm,style={'fontSize': 8}),
                            Label(text="CUP", top=tope, left=12.5*cm,style={'fontSize': 8}, borders = {'bottom': True}),
                            Label(text="MLC", top=tope, left=13.5*cm,style={'fontSize': 8}),
                            Label(text="CUP", top=tope, left=15*cm,style={'fontSize': 8}),
                            Label(text="MLC", top=tope, left=16.5*cm,style={'fontSize': 8}),
                            Label(text="Facturado", top=tope-0.5*cm, left=10*cm, style={'fontSize': 8}),
                            Label(text="Pagado", top=tope-0.5*cm, left=13*cm,style={'fontSize': 8}),
                            Label(text="Por Cobrar", top=tope-0.5*cm, left=15.5*cm,style={'fontSize': 8}),
                        ]
                        borders = {'bottom': True}
                        
                
                    class band_page_footer(ReportBand):
                        height = 0.5*cm
                        elements = [
                            Label(text='Comerciax', top=0.1*cm),
                            ]
                        borders = {'top': True}
                    class band_summary(ReportBand):
                        height = 0.5*cm
                        elements = [
                            Label(text='Totales:',style={'fontSize': 8}),
                                    ObjectValue(expression='sum(importecup)', left=5.2*cm, style={'fontSize': 6,'alignment': TA_RIGHT}),
                                    ObjectValue(expression='sum(importecuc)',left=6.6*cm, style={'fontSize': 6,'alignment': TA_RIGHT}), 
                                    ObjectValue(expression='sum(cobradocup)',  left=8*cm, style={'fontSize': 6,'alignment': TA_RIGHT}),
                                    ObjectValue(expression='sum(cobradocuc)',  left=9.2*cm, style={'fontSize': 6,'alignment': TA_RIGHT}),  
                                    ObjectValue(expression='sum(pendientecup)', left=10.7*cm, style={'fontSize': 6,'alignment': TA_RIGHT}),
                                    ObjectValue(expression='sum(pendientecuc)', left=12.2*cm, style={'fontSize': 6,'alignment': TA_RIGHT}),  
                            ]
                        
                        borders = {'top': True}   
                    if edad == True:                                 
                        groups = [                         
                                  ReportGroup(
                                        attribute_name = 'edad',                               
                                        band_header=DetailBand(
                                            height=0.6*cm,
                                            elements=[
                                                ObjectValue(expression='cliente',  width=BAND_WIDTH,style={'fontSize': 7})
                                            ]
                                        ),                                   
                                band_footer=ReportBand(
                                    height = 1.0*cm,
                                    elements = [
                                        Label(text='SubTotales:',style={'fontSize': 8}),
                                        ObjectValue(expression='sum(importecup)', left=5.2*cm, style={'fontSize': 6,'alignment': TA_RIGHT}),
                                        ObjectValue(expression='sum(importecuc)',left=6.6*cm, style={'fontSize': 6,'alignment': TA_RIGHT}), 
                                        ObjectValue(expression='sum(cobradocup)',  left=8*cm, style={'fontSize': 6,'alignment': TA_RIGHT}),
                                        ObjectValue(expression='sum(cobradocuc)',  left=9.2*cm, style={'fontSize': 6,'alignment': TA_RIGHT}),  
                                        ObjectValue(expression='sum(pendientecup)', left=10.7*cm, style={'fontSize': 6,'alignment': TA_RIGHT}),
                                        ObjectValue(expression='sum(pendientecuc)', left=12.2*cm, style={'fontSize': 6,'alignment': TA_RIGHT}),                               
                                        ],
                                    borders = {'top': True},
                                ),
                            ),                  
                        ]
                    else:
                        groups = [                         
                                  ReportGroup(
                                        attribute_name = 'cliente',                               
                                        band_header=DetailBand(
                                            height=0.6*cm,
                                            elements=[
                                                ObjectValue(expression='cliente',  width=BAND_WIDTH,style={'fontSize': 7})
                                            ]
                                        ),
                                       
                                band_footer=ReportBand(
                                    height = 1.0*cm,
                                    elements = [
                                        Label(text='SubTotales:',style={'fontSize': 8}),
                                        ObjectValue(expression='sum(importecup)', left=5.2*cm, style={'fontSize': 6,'alignment': TA_RIGHT}),
                                        ObjectValue(expression='sum(importecuc)',left=6.6*cm, style={'fontSize': 6,'alignment': TA_RIGHT}), 
                                        ObjectValue(expression='sum(cobradocup)',  left=8*cm, style={'fontSize': 6,'alignment': TA_RIGHT}),
                                        ObjectValue(expression='sum(cobradocuc)',  left=9.2*cm, style={'fontSize': 6,'alignment': TA_RIGHT}),  
                                        ObjectValue(expression='sum(pendientecup)', left=10.7*cm, style={'fontSize': 6,'alignment': TA_RIGHT}),
                                        ObjectValue(expression='sum(pendientecuc)', left=12.2*cm, style={'fontSize': 6,'alignment': TA_RIGHT}),                               
                                        ],
                                    borders = {'top': True},
                                ),
                            ),                  
                        ]
                    
            if type == "fac_cliente":
                title = 'Facturas por Cliente'
                class band_detail(ReportBand):                    
                        height = 0.25*cm                        
                        elements = [
                            ObjectValue(expression='nombre', width=13*cm,left=0.11*cm, style={'fontSize': 8}),
                            ObjectValue(expression='codigo', left=9.2*cm, style={'fontSize': 8}),
                            ObjectValue(expression='factura_nro', left=11*cm, style={'fontSize': 8}),
                            ObjectValue(expression='fecha_doc', left=12*cm, style={'fontSize': 8}),
                            ObjectValue(expression = 'importetotalcup' , left=10.2*cm, style={'fontSize': 8, 'alignment': TA_RIGHT}),
                            ObjectValue(expression='importecuc', left=12*cm, style={'fontSize': 8, 'alignment': TA_RIGHT}),
                            ObjectValue(expression = 'cancelada' , left=18*cm, style={'fontSize': 8}),
                        ]
                
                class band_page_header(ReportBand):
                    elements = [
                        SystemField(expression='%(report_title)s', top=0.1*cm, left=0, width=BAND_WIDTH,
                            style={'fontName': 'Helvetica-Bold', 'fontSize': 10, 'alignment': TA_CENTER}),
                        SystemField(expression='Impreso el %(now:%d/%m/%Y )s a las %(now:%H:%M)s', top=0.1*cm,
                            width=BAND_WIDTH, style={'alignment': TA_LEFT,'fontSize': 5}),
                        SystemField(expression=u'Página %(page_number)d de %(page_count)d', top=0.1*cm,
                            width=BAND_WIDTH, style={'alignment': TA_RIGHT,'fontSize': 8}),]
                    if filtro.__len__()!=0:
                        elements+=[Label(text="Filtro:", top=0.9*cm, left=0.1*cm, style={'fontSize': 5}),]
                    tope=1.2*cm
                    for k in range(filtro.__len__()):
                            elements+=[Label(text=filtro[k], top=tope, left=0.1*cm, style={'fontSize': 5}, width=BAND_WIDTH),]
                            tope=tope+0.3*cm
                    tope=tope+0.3*cm
                    height = tope+0.5*cm
                    elements+=[
                        Label(text="Cliente", top=tope, left=0.11*cm,style={'fontSize': 8}),
                        Label(text="Código", top=tope , left=9.2*cm, style={'fontSize': 8}),
                        Label(text="Nro.", top=tope , left=11*cm,style={'fontSize': 8}),
                        Label(text="Fecha Emisión", top=tope, left=11.7*cm,style={'fontSize': 8}),                    
                        Label(text="CUP", top=tope, left=14*cm,style={'fontSize': 8}),
                        Label(text="MLC", top=tope, left=15.8*cm,style={'fontSize': 8}),
                        Label(text="Cancelada", top=tope, left=17*cm,style={'fontSize': 8}),
                        Label(text="Importe", top=tope-0.53*cm, left=14.8*cm, style={'fontSize': 9}),
                    ]
                    borders = {'bottom': True}

                class band_summary(ReportBand):
                    height = 0*cm
                    elements = [
                        Label(text='Total General:',style={'fontName': 'Helvetica-Bold','fontSize': 7, 'alignment': TA_RIGHT}),
                        ObjectValue(expression='sum(importetotalcup)', left=10.2*cm, style={'fontName': 'Helvetica-Bold','fontSize': 7, 'alignment': TA_RIGHT}),
                        ObjectValue(expression='sum(importecuc)', left=12.0*cm, style={'fontName': 'Helvetica-Bold','fontSize': 7, 'alignment': TA_RIGHT}),
                        ]
                groups = [
                     ReportGroup(
                        attribute_name='cancelada',
                        # band_header=DetailBand(
                        #     height=0.5*cm,
                        #     elements=[
                        #         ObjectValue(expression='cancelada',  width=BAND_WIDTH,style={'fontSize': 7})
                        #     ]
                        # ),
                        band_footer=ReportBand(
                            height = 0.5*cm,
                            elements = [
                                Label(text='SubTotal: ',style={'fontName': 'Helvetica-Bold','fontSize': 7, 'alignment': TA_RIGHT}),
                                ObjectValue(expression='sum(importetotalcup)', left=10.2*cm, style={'fontName': 'Helvetica-Bold','fontSize': 7, 'alignment': TA_RIGHT}),
                                ObjectValue(expression='sum(importecuc)', left=12*cm, style={'fontName': 'Helvetica-Bold','fontSize': 7, 'alignment': TA_RIGHT}),
#                                ObjectValue(expression='sum(imp_cuc)', left=13.5*cm),
#                                ObjectValue(expression='sum(sub_total_line)', left=16*cm),
                                ],
#                            borders = {'top': True},
                        ),
                    ),
                ]
            
                class band_page_footer(ReportBand):
                    height = 0.5*cm
                    elements = [
                        Label(text='Comerciax', top=0.1*cm),
                        ]
                    borders = {'top': True}
                    
            if type == "fac_uncliente":
                title = 'Facturas por Cliente'
                class band_detail(ReportBand):                    
                        height = 0.1*cm                        
                        elements = [
                            ObjectValue(expression='factura_nro', left=1*cm, style={'fontSize': 7}),
                            ObjectValue(expression='fecha_doc', left=2.50*cm, style={'fontSize': 7}),
                            ObjectValue(expression = 'importetotalcup' , left=0.5*cm, style={'fontSize': 7, 'alignment': TA_RIGHT}),
                            ObjectValue(expression='importecuc', left=1.9*cm, style={'fontSize': 7, 'alignment': TA_RIGHT}),
                            ObjectValue(expression = 'cancelada' , left=7.5*cm, style={'fontSize': 7}),
                        ]
                
                class band_page_header(ReportBand):
                    elements = [
                        SystemField(expression='%(report_title)s', top=0.1*cm, left=0, width=BAND_WIDTH,
                            style={'fontName': 'Helvetica-Bold', 'fontSize': 10, 'alignment': TA_CENTER}),
                        SystemField(expression='Impreso el %(now:%d/%m/%Y )s a las %(now:%H:%M)s', top=0.1*cm,
                            width=BAND_WIDTH, style={'alignment': TA_LEFT,'fontSize': 5}),
                        SystemField(expression=u'Página %(page_number)d de %(page_count)d', top=0.1*cm,
                            width=BAND_WIDTH, style={'alignment': TA_RIGHT,'fontSize': 8}),]
                    if filtro.__len__()!=0:
                        elements+=[Label(text="Filtro:", top=0.9*cm, left=0.1*cm, style={'fontSize': 5}),]
                    tope=1.2*cm
                    for k in range(filtro.__len__()):
                            elements+=[Label(text=filtro[k], top=tope, left=0.1*cm, style={'fontSize': 5}, width=BAND_WIDTH),]
                            tope=tope+0.3*cm
                    tope=tope+0.3*cm
                    height = tope+0.5*cm
                    elements+=[
                        Label(text="Nro. Factura", top=tope , left=0.11*cm,style={'fontSize': 8}),
                        Label(text="Fecha Emisión", top=tope, left=2.00*cm,style={'fontSize': 8}),                    
                        Label(text="CUP", top=tope, left=4.7*cm,style={'fontSize': 8}),
                        Label(text="MLC", top=tope, left=6*cm,style={'fontSize': 8}),
                        Label(text="Cancelada", top=tope, left=7.5*cm,style={'fontSize': 8}),
                        Label(text="Importe", top=tope-0.40*cm, left=5.2*cm, style={'fontSize': 9}),
                    ]
                    borders = {'bottom': True}
                    
            
                class band_page_footer(ReportBand):
                    height = 0.5*cm
                    elements = [
                        Label(text='Comerciax', top=0.1*cm),
                        ]
                    borders = {'top': True}

            if type == "registro_fac":
                title = 'Registro de Facturas'
                class band_detail(ReportBand):                    
                        height = 0.25*cm                        
                        elements = [
                            ObjectValue(expression='codigo', left=0.1*cm, style={'fontSize': 6}),
                            ObjectValue(expression='nombre', width=11*cm,left=1.5*cm, style={'fontSize': 6}),
                            ObjectValue(expression='factura_nro', left=8.6*cm, style={'fontSize': 6}),
                            ObjectValue(expression='fecha_doc', left=9.8*cm, style={'fontSize': 6}),
                            ObjectValue(expression='cascos', left=12*cm, style={'fontSize': 6}),
                            ObjectValue(expression = 'importetotalcup' , left=9.6*cm, style={'fontSize': 6, 'alignment': TA_RIGHT}),
                            ObjectValue(expression='importecuc', left=11.0*cm, style={'fontSize': 6, 'alignment': TA_RIGHT}),
                            ObjectValue(expression = 'cancelada' , left=16.5*cm, style={'fontSize': 6}),
                        ]
                class band_page_header(ReportBand):
                    elements = [
                        SystemField(expression='%(report_title)s', top=0.1*cm, left=0, width=BAND_WIDTH,
                            style={'fontName': 'Helvetica-Bold', 'fontSize': 14, 'alignment': TA_CENTER}),
                        SystemField(expression='Impreso el %(now:%d/%m/%Y )s a las %(now:%H:%M)s', top=0.1*cm,
                            width=BAND_WIDTH, style={'alignment': TA_LEFT,'fontSize': 5}),
                        SystemField(expression=u'Página %(page_number)d de %(page_count)d', top=0.1*cm,
                            width=BAND_WIDTH, style={'alignment': TA_RIGHT,'fontSize': 8}),]
                    if filtro.__len__()!=0:
                        elements+=[Label(text="Filtro:", top=0.9*cm, left=0.1*cm, style={'fontSize': 5}),]
                    tope=1.2*cm
                    for k in range(filtro.__len__()):
                            elements+=[Label(text=filtro[k], top=tope, left=0.1*cm, style={'fontSize': 5}, width=BAND_WIDTH),]
                            tope=tope+0.3*cm
                    tope=tope+0.3*cm
                    height = tope+0.5*cm
                    elements+=[Label(text="Código", top=tope, left=0.1*cm,style={'fontSize': 8}),
                        Label(text="Nombre", top=tope , left=1.5*cm, style={'fontSize': 8}),
                        Label(text="Nro. Factura", top=tope , left=8.0*cm,style={'fontSize': 8}),
                        Label(text="Fecha Emisión", top=tope, left=9.7*cm,style={'fontSize': 8}),
                        Label(text="Cascos", top=tope, left=11.7*cm,style={'fontSize': 8}),                        
                        Label(text="CUP", top=tope, left=14*cm,style={'fontSize': 8}),
                        Label(text="MLC", top=tope, left=15*cm,style={'fontSize': 8}),
                        Label(text="Cancelada", top=tope, left=16*cm,style={'fontSize': 8}),
                        Label(text="Importe", top=tope-0.5*cm, left=14.3*cm, style={'fontSize': 9}),
                    ]
                    borders = {'bottom': True}
                class band_summary(ReportBand):
                    height = 0*cm
                    elements = [
                        Label(text='Total General:',style={'fontName': 'Helvetica-Bold','fontSize': 8, 'alignment': TA_RIGHT}),
                        ObjectValue(expression='sum(cascos)', left=7.1*cm, style={'fontName': 'Helvetica-Bold','fontSize': 7, 'alignment': TA_RIGHT}),
                        ObjectValue(expression='sum(importetotalcup)', left=9.6*cm, style={'fontName': 'Helvetica-Bold','fontSize': 7, 'alignment': TA_RIGHT}),
                        ObjectValue(expression='sum(importecuc)', left=11.0*cm, style={'fontName': 'Helvetica-Bold','fontSize': 7, 'alignment': TA_RIGHT}),
                        ]
                groups = [
                     ReportGroup(
                        attribute_name='tipo',

                        band_footer=ReportBand(
                            height = 0.8*cm,
                            elements = [
                                Label(text='SubTotal: ',style={'fontName': 'Helvetica-Bold','fontSize': 7, 'alignment': TA_RIGHT}),
                                ObjectValue(expression='sum(cascos)', left=7.1*cm, style={'fontName': 'Helvetica-Bold','fontSize': 7, 'alignment': TA_RIGHT}),
                                ObjectValue(expression='sum(importetotalcup)', left=9.6*cm, style={'fontName': 'Helvetica-Bold','fontSize': 7, 'alignment': TA_RIGHT}),
                                ObjectValue(expression='sum(importecuc)', left=11.0*cm, style={'fontName': 'Helvetica-Bold','fontSize': 7, 'alignment': TA_RIGHT}),
#                                ObjectValue(expression='sum(imp_cuc)', left=13.5*cm),
#                                ObjectValue(expression='sum(sub_total_line)', left=16*cm),
                                ],
#                            borders = {'top': True},
                        ),
                    ),
                ]
            
                class band_page_footer(ReportBand):
                    height = 0.5*cm
                    elements = [
                        Label(text='Comerciax', top=0.1*cm),
                        ]
                    borders = {'top': True}

            if type == "registro_fac_serv":
                title = 'Registro de Facturas de Asistencia Técnica'

                class band_detail(ReportBand):
                    height = 0.25 * cm
                    elements = [
                        ObjectValue(expression='codigo', left=0.1 * cm, style={'fontSize': 6}),
                        ObjectValue(expression='nombre', width=11 * cm, left=1.5 * cm, style={'fontSize': 6}),
                        ObjectValue(expression='factura_nro', left=8.6 * cm, style={'fontSize': 6}),
                        ObjectValue(expression='fecha_doc', left=9.8 * cm, style={'fontSize': 6}),
                        ObjectValue(expression='cascos', left=12 * cm, style={'fontSize': 6}),
                        ObjectValue(expression='importetotalcup', left=9.6 * cm,
                                    style={'fontSize': 6, 'alignment': TA_RIGHT}),
                        # ObjectValue(expression='importecuc', left=11.0 * cm,
                        #             style={'fontSize': 6, 'alignment': TA_RIGHT}),
                        ObjectValue(expression='cancelada', left=16.5 * cm, style={'fontSize': 6}),
                    ]

                class band_page_header(ReportBand):
                    elements = [
                        SystemField(expression='%(report_title)s', top=0.1 * cm, left=0, width=BAND_WIDTH,
                                    style={'fontName': 'Helvetica-Bold', 'fontSize': 14,
                                           'alignment': TA_CENTER}),
                        SystemField(expression='Impreso el %(now:%d/%m/%Y )s a las %(now:%H:%M)s', top=0.1 * cm,
                                    width=BAND_WIDTH, style={'alignment': TA_LEFT, 'fontSize': 5}),
                        SystemField(expression=u'Página %(page_number)d de %(page_count)d', top=0.1 * cm,
                                    width=BAND_WIDTH, style={'alignment': TA_RIGHT, 'fontSize': 8}), ]
                    if filtro.__len__() != 0:
                        elements += [
                            Label(text="Filtro:", top=0.9 * cm, left=0.1 * cm, style={'fontSize': 5}), ]
                    tope = 1.2 * cm
                    for k in range(filtro.__len__()):
                        elements += [Label(text=filtro[k], top=tope, left=0.1 * cm, style={'fontSize': 5},
                                           width=BAND_WIDTH), ]
                        tope = tope + 0.3 * cm
                    tope = tope + 0.3 * cm
                    height = tope + 0.5 * cm
                    elements += [Label(text="Código", top=tope, left=0.1 * cm, style={'fontSize': 8}),
                                 Label(text="Nombre", top=tope, left=1.5 * cm, style={'fontSize': 8}),
                                 Label(text="Nro. Factura", top=tope, left=8.0 * cm, style={'fontSize': 8}),
                                 Label(text="Fecha Emisión", top=tope, left=9.7 * cm, style={'fontSize': 8}),
                                 Label(text="Servicios", top=tope, left=11.7 * cm, style={'fontSize': 8}),
                                 Label(text="Importe CUP", top=tope, left=13 * cm, style={'fontSize': 8}),
                                 # Label(text="MLC", top=tope, left=15 * cm, style={'fontSize': 8}),
                                 Label(text="Cancelada", top=tope, left=16 * cm, style={'fontSize': 8}),
                                 # Label(text="Importe", top=tope - 0.5 * cm, left=14.3 * cm,
                                 #       style={'fontSize': 9}),
                                 ]
                    borders = {'bottom': True}

                class band_summary(ReportBand):
                    height = 0 * cm
                    elements = [
                        Label(text='Total General:',
                              style={'fontName': 'Helvetica-Bold', 'fontSize': 8, 'alignment': TA_RIGHT}),
                        ObjectValue(expression='sum(cascos)', left=7.1 * cm,
                                    style={'fontName': 'Helvetica-Bold', 'fontSize': 7, 'alignment': TA_RIGHT}),
                        ObjectValue(expression='sum(importetotalcup)', left=9.6 * cm,
                                    style={'fontName': 'Helvetica-Bold', 'fontSize': 7, 'alignment': TA_RIGHT}),
                        # ObjectValue(expression='sum(importecuc)', left=11.0 * cm,
                        #             style={'fontName': 'Helvetica-Bold', 'fontSize': 7, 'alignment': TA_RIGHT}),
                    ]

                # groups = [
                #     ReportGroup(
                #         attribute_name='tipo',
                #
                #         band_footer=ReportBand(
                #             height=0.8 * cm,
                #             elements=[
                #                 Label(text='SubTotal: ', style={'fontName': 'Helvetica-Bold', 'fontSize': 7,
                #                                                 'alignment': TA_RIGHT}),
                #                 ObjectValue(expression='sum(cascos)', left=7.1 * cm,
                #                             style={'fontName': 'Helvetica-Bold', 'fontSize': 7,
                #                                    'alignment': TA_RIGHT}),
                #                 ObjectValue(expression='sum(importetotalcup)', left=9.6 * cm,
                #                             style={'fontName': 'Helvetica-Bold', 'fontSize': 7,
                #                                    'alignment': TA_RIGHT}),
                #                 # ObjectValue(expression='sum(importecuc)', left=11.0 * cm,
                #                 #             style={'fontName': 'Helvetica-Bold', 'fontSize': 7,
                #                 #                    'alignment': TA_RIGHT}),
                #                 #                                ObjectValue(expression='sum(imp_cuc)', left=13.5*cm),
                #                 #                                ObjectValue(expression='sum(sub_total_line)', left=16*cm),
                #             ],
                #             #                            borders = {'top': True},
                #         ),
                #     ),
                # ]

                class band_page_footer(ReportBand):
                    height = 0.5 * cm
                    elements = [
                        Label(text='Comerciax', top=0.1 * cm),
                    ]
                    borders = {'top': True}
            if type == "cascos_pt_edad":
                title = 'Casco en PT x Edades'
               
                class band_page_header(ReportBand):
                    elements = [
                        SystemField(expression='%(report_title)s', top=0.1*cm, left=0, width=BAND_WIDTH,
                            style={'fontName': 'Helvetica-Bold', 'fontSize': 14, 'alignment': TA_CENTER}),
                        SystemField(expression='Impreso el %(now:%d/%m/%Y )s a las %(now:%H:%M)s', top=0.1*cm,
                            width=BAND_WIDTH, style={'alignment': TA_LEFT,'fontSize': 5}),
                        SystemField(expression=u'Página %(page_number)d de %(page_count)d', top=0.1*cm,
                            width=BAND_WIDTH, style={'alignment': TA_RIGHT,'fontSize': 8}),]
                    if filtro.__len__()!=0:
                        elements+=[Label(text="Filtro:", top=0.9*cm, left=0.1*cm, style={'fontSize': 5}),]
                    tope=1.2*cm
                    for k in range(filtro.__len__()):
                            elements+=[Label(text=filtro[k], top=tope, left=0.1*cm, style={'fontSize': 5}, width=BAND_WIDTH),]
                            tope=tope+0.3*cm
                    tope=tope+0.3*cm
                    height = tope+0.5*cm
                    elements+=[Label(text="Medida", top=tope, left=0.5*cm,style={'fontSize': 8,'fontName': 'Helvetica-Bold'}),
                        Label(text="De 0 a 30 días", top=tope , left=5.5*cm, style={'fontSize': 8,'fontName': 'Helvetica-Bold'}),
                        Label(text="Más de 30 hasta 45 días", top=tope , left=8.0*cm,style={'fontSize': 8,'fontName': 'Helvetica-Bold'}),
                        Label(text="Más de 45 días", top=tope, left=12.0*cm,style={'fontSize': 8,'fontName': 'Helvetica-Bold'}),
                        Label(text="Total", top=tope, left=15.3*cm,style={'fontSize': 8,'fontName': 'Helvetica-Bold'}),                        
                        
                    ]
                    borders = {'bottom': True}
                class band_detail(ReportBand):                    
                        height = 0.4*cm  
                                          
                        elements = [
                            ObjectValue(expression='medida',top=tope+0.1*cm, left=0.5*cm, style={'fontSize': 6}),
                            ObjectValue(expression='s1',top=tope+0.1*cm, left=5.8*cm, style={'fontSize': 6}),
                            ObjectValue(expression='s2', top=tope+0.1*cm,left=8.8*cm, style={'fontSize': 6}),
                            ObjectValue(expression='s3', top=tope+0.1*cm,left=12.8*cm, style={'fontSize': 6}),
                            ObjectValue(expression = 'total_prod' ,top=tope+0.1*cm, left=15.8*cm, style={'fontSize': 6,'fontName': 'Helvetica-Bold'}),
                        ]
                        
                class band_page_footer(ReportBand):
                    height = 0.5*cm
                    elements = [
                        Label(text='Comerciax', top=0.1*cm),
                        ]
                    borders = {'top': True}
                
                
            if type == "vent_decomiso":
                title = 'Ventas de Decomiso'
               
                class band_page_header(ReportBand):
                    elements = [
                        SystemField(expression='%(report_title)s', top=0.1*cm, left=0, width=BAND_WIDTH,
                            style={'fontName': 'Helvetica-Bold', 'fontSize': 14, 'alignment': TA_CENTER}),
                        SystemField(expression='Impreso el %(now:%d/%m/%Y )s a las %(now:%H:%M)s', top=0.1*cm,
                            width=BAND_WIDTH, style={'alignment': TA_LEFT,'fontSize': 5}),
                        SystemField(expression=u'Página %(page_number)d de %(page_count)d', top=0.1*cm,
                            width=BAND_WIDTH, style={'alignment': TA_RIGHT,'fontSize': 8}),]
                    if filtro.__len__()!=0:
                        elements+=[Label(text="Filtro:", top=0.9*cm, left=0.1*cm, style={'fontSize': 5}),]
                    tope=1.2*cm
                    for k in range(filtro.__len__()):
                            elements+=[Label(text=filtro[k], top=tope, left=0.1*cm, style={'fontSize': 5}, width=BAND_WIDTH),]
                            tope=tope+0.3*cm
                    tope=tope+0.3*cm
                    height = tope+0.5*cm
                    elements+=[
                        Label(text="Decomisado a:", top=tope, left=0.11*cm,style={'fontSize': 8} ,borders = {'top': True}),
                        Label(text="Vendido a:", top=tope , left=11*cm, style={'fontSize': 8}, borders = {'bottom': True}),
                        Label(text="Organismo", top=tope+0.5*cm, left=0.11*cm,style={'fontSize': 8},borders = {'top': True}),
                        Label(text="Cliente", top=tope+0.5*cm, left=1.8*cm,style={'fontSize': 8},borders = {'top': True}),                    
                        Label(text="Medida", top=tope+0.5*cm, left=6.7*cm,style={'fontSize': 8},borders = {'top': True}),
                        Label(text="Nro.Casco", top=tope+0.5*cm, left=9*cm,style={'fontSize': 8},borders = {'top': True}),
                        Label(text="Organismo", top=tope+0.5*cm, left=11*cm,style={'fontSize': 8},borders = {'top': True}),
                        Label(text="Cliente", top=tope+0.5*cm, left=12.7*cm,style={'fontSize': 8},borders = {'top': True}),
                        Label(text="Nro Factura", top=tope+0.5*cm, left=17*cm,style={'fontSize': 8}),
                    ]
                class band_detail(ReportBand):                    
                        height = 0.4*cm                        
                        elements = [
                            ObjectValue(expression='organismod',top=tope+0.7*cm, left=0.11*cm, style={'fontSize': 5}),
                            ObjectValue(expression='cliented',top=tope+0.7*cm, left=1.8*cm, style={'fontSize': 5}),
                            ObjectValue(expression='medida', top=tope+0.7*cm,left=6.7*cm, style={'fontSize': 6}),
                            ObjectValue(expression='casconro', top=tope+0.7*cm,left=9.2*cm, style={'fontSize': 6}),
                            ObjectValue(expression = 'organismov' ,top=tope+0.7*cm, left=11*cm, style={'fontSize': 5}),
                            ObjectValue(expression='clientev', top=tope+0.7*cm,left=12.7*cm, style={'fontSize': 5}),
                            ObjectValue(expression = 'nrofact' ,top=tope+0.7*cm, left=17.3*cm, style={'fontSize': 6}),
                        ]
                       
                class band_page_footer(ReportBand):
                    height = 0.5*cm
                    
                    elements = [
                        Label(text='__________________________________________________________________________________________________________________________________________________________________', top=0.7*cm,style={'fontSize': 6}),     
                        Label(text='Comerciax', top=1*cm,style={'fontSize': 6}),
                        ]
                    #borders = {'top': True,'fontSize': 6}
                    
            if type == "vent_decomiso_sindesglose":
                title = 'Ventas de Decomiso'
               
                class band_page_header(ReportBand):
                    elements = [
                        SystemField(expression='%(report_title)s', top=0.1*cm, left=0, width=BAND_WIDTH,
                            style={'fontName': 'Helvetica-Bold', 'fontSize': 14, 'alignment': TA_CENTER}),
                        SystemField(expression='Impreso el %(now:%d/%m/%Y )s a las %(now:%H:%M)s', top=0.1*cm,
                            width=BAND_WIDTH, style={'alignment': TA_LEFT,'fontSize': 5}),
                        SystemField(expression=u'Página %(page_number)d de %(page_count)d', top=0.1*cm,
                            width=BAND_WIDTH, style={'alignment': TA_RIGHT,'fontSize': 8}),]
                    if filtro.__len__()!=0:
                        elements+=[Label(text="Filtro:", top=0.9*cm, left=0.1*cm, style={'fontSize': 5}),]
                    tope=1.2*cm
                    for k in range(filtro.__len__()):
                            elements+=[Label(text=filtro[k], top=tope, left=0.1*cm, style={'fontSize': 5}, width=BAND_WIDTH),]
                            tope=tope+0.3*cm
                    tope=tope+0.3*cm
                    height = tope+0.5*cm
                    arr=[]
                    
                    elements+=[
                        Label(text="Decomisado a:", top=tope, left=0.11*cm,style={'fontSize': 8} ,borders = {'top': True}),
                        Label(text="Vendido a:", top=tope , left=11*cm, style={'fontSize': 8}, borders = {'bottom': True}),
                        Label(text="Organismo", top=tope+0.5*cm, left=0.11*cm,style={'fontSize': 8},borders = {'top': True}),
                        Label(text="Cliente", top=tope+0.5*cm, left=1.8*cm,style={'fontSize': 8},borders = {'top': True}),                    
                        Label(text="Medida", top=tope+0.5*cm, left=6.7*cm,style={'fontSize': 8},borders = {'top': True}),
                        Label(text="Nro.Casco", top=tope+0.5*cm, left=9*cm,style={'fontSize': 8},borders = {'top': True}),
                        Label(text="Organismo", top=tope+0.5*cm, left=11*cm,style={'fontSize': 8},borders = {'top': True}),
                        Label(text="Cliente", top=tope+0.5*cm, left=12.7*cm,style={'fontSize': 8},borders = {'top': True}),
                        Label(text="Nro Factura", top=tope+0.5*cm, left=17*cm,style={'fontSize': 8}),
                    ]
                class band_detail(ReportBand):                    
                        height = 0.4*cm                        
                        elements = [
                            ObjectValue(expression='1',top=tope+0.7*cm, left=0.11*cm, style={'fontSize': 6}),
                            ObjectValue(expression='2',top=tope+0.7*cm, left=1.8*cm, style={'fontSize': 5}),
                            ObjectValue(expression='3', top=tope+0.7*cm,left=6.7*cm, style={'fontSize': 6}),
                            ObjectValue(expression='4', top=tope+0.7*cm,left=9.2*cm, style={'fontSize': 6}),
                            ObjectValue(expression ='5' ,top=tope+0.7*cm, left=11*cm, style={'fontSize': 6}),
                            ObjectValue(expression='6', top=tope+0.7*cm,left=12.7*cm, style={'fontSize': 6}),
                            ObjectValue(expression = '7' ,top=tope+0.7*cm, left=17.3*cm, style={'fontSize': 6}),
                        ]
                       
                class band_page_footer(ReportBand):
                    height = 0.5*cm
                    elements = [
                        Label(text='Comerciax', top=0.1*cm),
                        ]
                    borders = {'top': True}                    
            if type == "concil_client":
                title = 'Conciliacion con Entidades'
               
                class band_page_header(ReportBand):
                    elements = [
                        SystemField(expression='%(report_title)s', top=0.1*cm, left=0, width=BAND_WIDTH,
                            style={'fontName': 'Helvetica-Bold', 'fontSize': 14, 'alignment': TA_CENTER}),
                        SystemField(expression='Impreso el %(now:%d/%m/%Y )s a las %(now:%H:%M)s', top=0.1*cm,
                            width=BAND_WIDTH, style={'alignment': TA_LEFT,'fontSize': 5}),
                        SystemField(expression=u'Página %(page_number)d de %(page_count)d', top=0.1*cm,
                            width=BAND_WIDTH, style={'alignment': TA_RIGHT,'fontSize': 8}),]
                    if filtro.__len__()!=0:
                        tope=1.2*cm
                        elements+=[Label(text="Filtro:", top=0.9*cm, left=0.1*cm, style={'fontSize': 5}),
                                   ]
                  
                    for k in range(filtro.__len__()):
                            elements+=[Label(text=filtro[k]['empresa'], top=tope, left=0.1*cm, style={'fontSize': 5}, width=BAND_WIDTH),]
                            tope=tope+0.3*cm
                            elements+=[Label(text='Desde: '+str(filtro[k]['desde'])+' Hasta:'+str(filtro[k]['hasta']), top=tope, left=0.1*cm, style={'fontSize': 5}, width=BAND_WIDTH),]
                            tope=tope+0.3*cm
                    tope=tope+0.3*cm
                    height = tope+0.5*cm
                    elements+=[
                        Label(text="Plan del Año", top=tope, left=0.11*cm,style={'fontSize': 8}),
                        Label(text="Inv. Inicial", top=tope , left=2.5*cm, style={'fontSize': 8}),
                        Label(text="Entregados", top=tope, left=4.5*cm,style={'fontSize': 8}),
                        Label(text="Terminados", top=tope, left=7.5*cm,style={'fontSize': 8}),                    
                        Label(text="Decomisados", top=tope, left=10*cm,style={'fontSize': 8}),
                        Label(text="Facturados", top=tope, left=13*cm,style={'fontSize': 8}),
                        Label(text="Inservibles", top=tope, left=15*cm,style={'fontSize': 8}),
                        Label(text="Deuda", top=tope, left=17.5*cm,style={'fontSize': 8}),
                    ]
                    borders = {'bottom': True}
                class band_detail(ReportBand):                    
                        height = 0.4*cm                        
                        elements = [
                            ObjectValue(expression='plan',top=tope, left=0.11*cm, style={'fontSize': 6}),
                            ObjectValue(expression='inv_ini',top=tope, left=2.5*cm, style={'fontSize': 5}),
                            ObjectValue(expression='entregados', top=tope,left=4.5*cm, style={'fontSize': 6}),
                            ObjectValue(expression='terminados', top=tope,left=7.5*cm, style={'fontSize': 6}),
                            ObjectValue(expression = 'decomisado' ,top=tope, left=10*cm, style={'fontSize': 6}),
                            ObjectValue(expression ='facturado', top=tope,left=13.2*cm, style={'fontSize': 6}),
                            ObjectValue(expression = 'inservible' ,top=tope, left=15.2*cm, style={'fontSize': 6}),
                            ObjectValue(expression = 'deuda' ,top=tope, left=17.8*cm, style={'fontSize': 6}),
                        ]        
                class band_summary(ReportBand):
                    height = 0.5*cm
                    elements = [
                        Label(text='Especialista Comercial:', left=1*cm ,top=1.5*cm , borders = {'bottom': True}),
                        Label(text='Director:', left=7*cm,top=1.5*cm, borders = {'bottom': True}),
                        Label(text='Jefe de Area Comercial:', left=13*cm,top=1.5*cm, borders = {'bottom': True}),
                        ] 
                class band_page_footer(ReportBand):
                    height = 0.5*cm
                    elements = [
                        Label(text='Comerciax', top=0.1*cm),
                        ]
                    borders = {'top': True}
            if type == "concil_recap":
                title = 'Conciliación Recape por Provincia'
                page_size = landscape(A5)

#                from geraldo import utils
#                utils.landscape()
               
                class band_page_header(ReportBand):
                    elements = [
                        SystemField(expression='%(report_title)s', top=0.1*cm, left=0, width=BAND_WIDTH,
                            style={'fontName': 'Helvetica-Bold', 'fontSize': 14, 'alignment': TA_CENTER}),
                        SystemField(expression='Impreso el %(now:%d/%m/%Y )s a las %(now:%H:%M)s', top=0.1*cm,
                            width=BAND_WIDTH, style={'alignment': TA_LEFT,'fontSize': 5}),
                        SystemField(expression=u'Página %(page_number)d de %(page_count)d', top=0.1*cm,
                            width=BAND_WIDTH, style={'alignment': TA_RIGHT,'fontSize': 8}),]
                    tope=1.2*cm
                    if filtro.__len__()!=0:
                        tope=1.2*cm
                        elements+=[
                                   Label(text="Filtro:", top=0.9*cm, left=0.1*cm, style={'fontSize': 5}),
                                   ]
                  
                    for k in range(filtro.__len__()):
                            elements+=[Label(text='Desde: '+str(filtro[k]['desde'])+' Hasta:'+str(filtro[k]['hasta']), top=tope, left=0.1*cm, style={'fontSize': 5}, width=BAND_WIDTH),]
                            tope=tope+0.3*cm
                            elements+=[Label(text='Organismo: '+filtro[k]['empresa'], top=tope, left=0.1*cm, style={'fontSize': 5}, width=BAND_WIDTH),]
                            tope=tope+0.3*cm
                    tope=tope+0.6*cm
                    height = tope+0.5*cm
                    elements+=[
                        Label(text="", top=tope-0.5*cm, left=0.1*cm,style={'fontSize': 7},borders = {'all': True}),
                        Label(text="Casco", top=tope-0.5*cm, left=3.1*cm,style={'fontSize': 8},borders = {'all': True}),
                        Label(text="Inservible", top=tope-0.5*cm, left=5.5*cm,style={'fontSize': 8},borders = {'all': True}),
                        Label(text="Facturado", top=tope-0.5*cm, left=8.4*cm,style={'fontSize': 8},borders = {'all': True}),
                        Label(text="Total", top=tope-0.5*cm, left=10.2*cm,style={'fontSize': 8},borders = {'all': True}),
                        Label(text="Por Recog.", top=tope-0.5*cm, left=11.3*cm,style={'fontSize': 8},borders = {'all': True}),
                        Label(text="Total.", top=tope-0.5*cm, left=13.4*cm,style={'fontSize': 8},borders = {'all': True}),
                        Label(text="Total.", top=tope-0.5*cm, left=16.2*cm,style={'fontSize': 8}),
                        Label(text="Provincia", top=tope, left=0.11*cm,style={'fontSize': 7}),
                        Label(text="cierre", top=tope , left=1.7*cm, style={'fontSize': 7}),
                        Label(text="semana", top=tope, left=2.6*cm,style={'fontSize': 7}),
                        Label(text="mes", top=tope, left=3.7*cm,style={'fontSize': 7}),                    
                        Label(text="año", top=tope, left=4.4*cm,style={'fontSize': 7}),
                        Label(text="semana", top=tope, left=5.1*cm,style={'fontSize': 7}),
                        Label(text="mes", top=tope, left=6.3*cm,style={'fontSize': 7}),
                        Label(text="año", top=tope, left=7.0*cm,style={'fontSize': 7}),
                        Label(text="semana", top=tope, left=7.7*cm,style={'fontSize': 7}),
                        Label(text="mes", top=tope, left=8.9*cm,style={'fontSize': 7}),
                        Label(text="año", top=tope, left=9.6*cm,style={'fontSize': 7}),
                        Label(text="Recog.", top=tope, left=10.2*cm,style={'fontSize': 8}),
                        Label(text="Term.", top=tope, left=11.2*cm,style={'fontSize': 8}),
                        Label(text="Inserv", top=tope, left=12.2*cm,style={'fontSize': 8}),
                        Label(text="Por Recog.", top=tope, left=13.2*cm,style={'fontSize': 8}),
                        Label(text="Decom.", top=tope, left=14.9*cm,style={'fontSize': 8}),
                        Label(text="Pendte.", top=tope, left=16.2*cm,style={'fontSize': 8}),
                        Label(text="Por Producir.", top=tope, left=17.5*cm,style={'fontSize': 8}),                      
                    ]
                    borders = {'bottom': True}
                class band_detail(ReportBand):                    
                        height = 0.4*cm                        
                        elements = [
                            ObjectValue(expression='provincia',top=tope, left=0.11*cm, style={'fontSize': 6}),
                            ObjectValue(expression='cierre',top=tope, left=2.0*cm, style={'fontSize': 5}),
                            ObjectValue(expression='almc_semana', top=tope,left=3.0*cm, style={'fontSize': 6}),
                            ObjectValue(expression='almc_mes', top=tope,left=3.9*cm, style={'fontSize': 6}),
                            ObjectValue(expression = 'almc_year' ,top=tope, left=4.6*cm, style={'fontSize': 6}),
                            ObjectValue(expression ='inserv_semana', top=tope,left=5.5*cm, style={'fontSize': 6}),
                            ObjectValue(expression = 'inserv_mes' ,top=tope, left=6.5*cm, style={'fontSize': 6}),
                            ObjectValue(expression = 'inserv_year' ,top=tope, left=7.2*cm, style={'fontSize': 6}),
                            ObjectValue(expression ='factu_semana', top=tope,left=8*cm, style={'fontSize': 6}),
                            ObjectValue(expression = 'factu_mes' ,top=tope, left=9*cm, style={'fontSize': 6}),
                            ObjectValue(expression = 'factu_year' ,top=tope, left=9.7*cm, style={'fontSize': 6}),
                            ObjectValue(expression = 'total_recog' ,top=tope, left=10.7*cm, style={'fontSize': 6}),
                            ObjectValue(expression = 'por_recog_terminados' ,top=tope, left=11.5*cm, style={'fontSize': 6}),
                            ObjectValue(expression = 'por_recog_inservible' ,top=tope, left=12.5*cm, style={'fontSize': 6}),
                            ObjectValue(expression = 'total_por_recog' ,top=tope, left=13.5*cm, style={'fontSize': 6}),
                            ObjectValue(expression = 'decom_year' ,top=tope, left=15*cm, style={'fontSize': 6}),
                            ObjectValue(expression = 'pend_total' ,top=tope, left=16.5*cm, style={'fontSize': 6}),
                            ObjectValue(expression = 'casco_x_prod' ,top=tope, left=18*cm, style={'fontSize': 6}),
                        ]        
                class band_summary(ReportBand):
                    height = 0.5*cm
                    elements = [
                        Label(text='Especialista Comercial:', left=1*cm ,top=1.5*cm , borders = {'bottom': True}),
                        Label(text='Director:', left=7*cm,top=1.5*cm, borders = {'bottom': True}),
                        Label(text='Jefe de Area Comercial:', left=13*cm,top=1.5*cm, borders = {'bottom': True}),
                        ] 
                class band_page_footer(ReportBand):
                    height = 0.5*cm
                    elements = [
                        Label(text='Comerciax', top=0.1*cm),
                        ]
                    borders = {'top': True}
            if type == "reg_cobros":
                title = 'Registro de Cobros'
                class band_page_header(ReportBand):
                    elements = [
                        SystemField(expression='%(report_title)s', top=0.1*cm, left=0, width=BAND_WIDTH,
                            style={'fontName': 'Helvetica-Bold', 'fontSize': 14, 'alignment': TA_CENTER}),
                        SystemField(expression='Impreso el %(now:%d/%m/%Y )s a las %(now:%H:%M)s', top=0.1*cm,
                            width=BAND_WIDTH, style={'alignment': TA_LEFT,'fontSize': 5}),
                        SystemField(expression=u'Página %(page_number)d de %(page_count)d', top=0.1*cm,
                            width=BAND_WIDTH, style={'alignment': TA_RIGHT,'fontSize': 8}),]
                    if filtro.__len__()!=0:
                        elements+=[Label(text="Filtro:", top=0.9*cm, left=0.1*cm, style={'fontSize': 5}),]
                    tope=1.2*cm
                    for k in range(filtro.__len__()):
                            elements+=[Label(text=filtro[k], top=tope, left=0.1*cm, style={'fontSize': 5}, width=BAND_WIDTH),]
                            tope=tope+0.3*cm
                    tope=tope+0.3*cm
                    height = tope+0.5*cm
                    elements+=[
                        Label(text="Cliente", top=tope, left=0.1*cm,style={'fontSize': 9}),
                        Label(text="Nro Pago", top=tope , left=5.2*cm, style={'fontSize': 9}),
                        Label(text="Fecha", top=tope , left=9.5*cm,style={'fontSize': 9}),
                        Label(text="Moneda", top=tope, left=10.8*cm,style={'fontSize': 9}),                    
                        Label(text="Forma Pago", top=tope, left=12.5*cm,style={'fontSize': 9}),
                        Label(text="Importe", top=tope, left=14.5*cm,style={'fontSize': 9}),
                        Label(text="Deposito Adelantado", top=tope, left=16*cm,style={'fontSize': 9}),
                    ]
                    borders = {'bottom': Line(stroke_color=red, stroke_width=3)}
                        
            
                class band_page_footer(ReportBand):
                    height = 0.5*cm
                    elements = [Label(text='ComerciaX', top=0.1*cm),]
                    borders = {'top':True}
            
                class band_detail(ReportBand):
                    height = 0.4*cm
                    elements = [
                         ObjectValue(attribute_name='clientep',left=5.2*cm, style={'fontSize': 6}),
                         ObjectValue(attribute_name='fecha_pagos', top=tope, left=9.4*cm, style={'fontSize': 6}),
                         ObjectValue(attribute_name='moneda',top=tope, left=11.2*cm, style={'fontSize': 6}),
                         ObjectValue(attribute_name='forma_pago', top=tope, left=13*cm, style={'fontSize': 6}),
                         ObjectValue(attribute_name='importe_pagado',top=tope,left=15*cm, style={'fontSize': 6}),
                         ObjectValue(attribute_name='deposito_adelantado', top=tope,  left=17*cm, style={'fontSize': 6}),
                     ]
                    borders = {'bottom': Line(stroke_color=navy)}
                groups = [                         
                          ReportGroup(
                                
                                attribute_name=self.attribute,
                                band_header=DetailBand(
                                    height=0.6*cm,
                                    elements=[
                                        ObjectValue(expression='cliente',  width=BAND_WIDTH,style={'fontSize': 6})
                                    ]
                                ),
                          ),
                    ]
                subreports = [
                     SubReport(
                         queryset_string = '%(object)s.factpago_set.all()',
                         band_header = ReportBand(
                                 height=0.5*cm,
                                 elements=[
                                     Label(text='Nro. Factura', top=0, left=5*cm, style={'fontSize': 8}),
                                     Label(text='Fecha', top=0, left=9*cm, style={'fontSize': 8}),
                                     Label(text='Imp. Pagado', top=0, left=13*cm, style={'fontSize': 8}),
                                 ],
                                  borders={'top': True},
                             ),
                         band_detail = ReportBand(
                                 height=0.5*cm,
                                 elements=[
                                     ObjectValue(attribute_name='nro', top=0, left=5*cm,style={'fontSize': 7}),
                                     ObjectValue(attribute_name='fecha', top=0, left=9*cm,style={'fontSize': 7}),
                                     ObjectValue(attribute_name='imp_pagado', top=0, left=13*cm,style={'fontSize': 7}),
                                 ],
                                
                             ),
                     ),
                ]   
            if type == "balanc_casc_recap":
                    title = 'Balance de Casco vs Recape'
                    class band_detail(ReportBand):                    
                            height = 0.4*cm                        
                            elements = [
                                ObjectValue(expression='medida', left=0.11*cm, style={'fontSize': 6}),
#                                ObjectValue(expression=' ', left=3.5*cm, style={'fontSize': 6}),
                                ObjectValue(expression='casco', left=0*cm, style={'fontSize': 6,'alignment': TA_RIGHT}),
                                ObjectValue(expression='dip', left=1*cm, style={'fontSize': 6,'alignment': TA_RIGHT}),
                                ObjectValue(expression = 'er' , left=2*cm, style={'fontSize': 6,'alignment': TA_RIGHT}),
                                ObjectValue(expression='ree', left=3*cm, style={'fontSize': 6,'alignment': TA_RIGHT}),
                                ObjectValue(expression = 'ecr' , left=4.5*cm, style={'fontSize': 6,'alignment': TA_RIGHT}),
                                ObjectValue(expression='fact', left=5.8*cm, style={'fontSize': 6,'alignment': TA_RIGHT}),
                                ObjectValue(expression = 'tranf' , left=6.9*cm, style={'fontSize': 6,'alignment': TA_RIGHT}),
                                 ObjectValue(expression = 'balance' , left=8.5*cm, style={'fontSize': 6,'alignment': TA_RIGHT}),
#                                ObjectValue(expression='invfinal', left=10.8*cm, style={'fontSize': 6,'alignment': TA_RIGHT}),
                                ObjectValue(expression = 'dif' , left=13*cm, style={'fontSize': 6,'alignment': TA_RIGHT}),
                            ]
    #                            borders = {'bottom': True}
                    class band_page_header(ReportBand):
                        elements = [
                            SystemField(expression='%(report_title)s', top=0.1*cm, left=0, width=BAND_WIDTH,
                                style={'fontName': 'Helvetica-Bold', 'fontSize': 14, 'alignment': TA_CENTER}),
                            SystemField(expression='Impreso el %(now:%d/%m/%Y )s a las %(now:%H:%M)s', top=0.1*cm,
                                width=BAND_WIDTH, style={'alignment': TA_LEFT,'fontSize': 5}),
                            SystemField(expression=u'Página %(page_number)d de %(page_count)d', top=0.1*cm,
                                width=BAND_WIDTH, style={'alignment': TA_RIGHT,'fontSize': 8}),]
                        if filtro.__len__()!=0:
                            elements+=[Label(text="Filtro:", top=0.9*cm, left=0.1*cm, style={'fontSize': 5}),]
                        tope=1.2*cm
                        for k in range(filtro.__len__()):
                                elements+=[Label(text=filtro[k], top=tope, left=0.1*cm, style={'fontSize': 5}, width=BAND_WIDTH),]
                                tope=tope+0.3*cm
                        tope=tope+0.3*cm
                        height = tope+0.5*cm 
                        elements+=[Label(text="Medida", top=tope, left=0.11*cm,style={'fontSize': 8}),
                            Label(text="Inv. Inicial", top=tope , left=2.9*cm, style={'fontSize': 8}),
                            Label(text="Entradas del Mes", top=tope-0.5*cm , left=5*cm,style={'fontSize': 8}),
                            Label(text="Alm", top=tope, left=4.5*cm,style={'fontSize': 8}),                    
                            Label(text="DIP", top=tope, left=5.6*cm,style={'fontSize': 8}),
                            Label(text="ER", top=tope, left=6.6*cm,style={'fontSize': 8}),
                            Label(text="REE", top=tope, left=7.6*cm,style={'fontSize': 8}),
                            Label(text="Devolucion", top=tope, left=8.8*cm,style={'fontSize': 8}),
                            Label(text="Salidas del Mes", top=tope-0.5*cm, left=10.5*cm,style={'fontSize': 8}),
                            Label(text="Fact", top=tope, left=10.5*cm,style={'fontSize': 8}),
                            Label(text="Transf", top=tope, left=11.5*cm, style={'fontSize': 8}),
                            Label(text="Balance", top=tope, left=13*cm, style={'fontSize': 8}),
                            Label(text="Inv. Final", top=tope, left=15*cm,style={'fontSize': 8}),
                            Label(text="Diferencia", top=tope, left=17.3*cm,style={'fontSize': 8}),
                        ]
                        borders = {'bottom': True}
                        
                
                    class band_page_footer(ReportBand):
                        height = 0.5*cm
                        elements = [
                            Label(text='Comerciax', top=0.1*cm),
                            ]
                        borders = {'top': True}
                    class band_summary(ReportBand):
                        height = 0.5*cm
                        elements = [
                            Label(text='Totales:',style={'fontSize': 8}),
                                    ObjectValue(expression='sum(invinicial)', left=-1.2*cm, style={'fontSize': 7,'alignment': TA_RIGHT}),
                                    ObjectValue(expression='sum(casco)',left=0.1*cm, style={'fontSize': 7,'alignment': TA_RIGHT}), 
                                    ObjectValue(expression='sum(dip)',  left=1.1*cm, style={'fontSize': 7,'alignment': TA_RIGHT}),
#                                    ObjectValue(expression='sum(er)',  left=2*cm, style={'fontSize': 7,'alignment': TA_RIGHT}),
#                                    ObjectValue(expression='sum(er)',  left=2*cm, style={'fontSize': 6,'alignment': TA_RIGHT}),  
                                    ObjectValue(expression='sum(ree)', left=3*cm, style={'fontSize': 7,'alignment': TA_RIGHT}),
                                    ObjectValue(expression='sum(ecr)', left=4.7*cm, style={'fontSize': 7,'alignment': TA_RIGHT}),
                                    ObjectValue(expression='sum(fact)', left=5.8*cm, style={'fontSize': 7,'alignment': TA_RIGHT}),
                                    ObjectValue(expression='sum(tranf)', left=7*cm, style={'fontSize': 7,'alignment': TA_RIGHT}),
                                    ObjectValue(expression='sum(balance)', left=8.8*cm, style={'fontSize': 7,'alignment': TA_RIGHT}),
                                    ObjectValue(expression='sum(invfinal)', left=11*cm, style={'fontSize': 7,'alignment': TA_RIGHT}),
                                    ObjectValue(expression='sum(dif)', left=13*cm, style={'fontSize': 7,'alignment': TA_RIGHT}),  
                            ]
                        
                        borders = {'top': True}
                        
        if type == "reg_cobros":
            queryset = Clientepago.objects.order_by('cliente')  
        report = Report_(queryset)
        try:
            fichero = open(pdf_file_name)
            fichero.close()
        except Exception, e:
            pass
        try:
            report.generate_by(PDFGenerator, pdf_file_name)
        except Exception, e:
            return 0
        return 2

    def Mov_Cascos(self,queryset,encabezado,pdf_name,filtro):
        cur_dir = os.path.dirname(os.path.abspath(__file__))
#        print cur_dir
        class Report_4(Report):
                title = encabezado
                class band_detail(ReportBand):
                        height = 0.4*cm
                        elements = [
                            ObjectValue(expression='nro_doc', left=5*cm, style={'fontSize': 6}),
                            ObjectValue(expression='fecha_doc', left=7*cm, style={'fontSize': 6}),
                            ObjectValue(expression='cantidad', left=9*cm, style={'fontSize': 6}),]             
                        
                class band_page_header(ReportBand):
                    elements = [
                        SystemField(expression='%(report_title)s', top=0.1*cm, left=0, width=BAND_WIDTH,
                            style={'fontName': 'Helvetica-Bold', 'fontSize': 14, 'alignment': TA_CENTER}),
                        SystemField(expression=u'Página %(page_number)d de %(page_count)d', top=0.1*cm,
                            width=BAND_WIDTH, style={'alignment': TA_RIGHT,'fontSize': 5}),
                        SystemField(expression='Impreso el %(now:%d/%m/%Y )s a las %(now:%H:%M)s', top=0.1*cm,
                            width=BAND_WIDTH, style={'alignment': TA_LEFT,'fontSize': 5}),]
                    if filtro.__len__()!=0:     
                        elements+=[Label(text="Filtro:", top=0.9*cm, left=0.1*cm, style={'fontSize': 5}),]
                    tope=1.2*cm
                    for k in range(filtro.__len__()):
                            elements+=[Label(text=filtro[k], top=tope, left=0.1*cm, style={'fontSize': 5}, width=BAND_WIDTH),]
                            tope=tope+0.3*cm
                        
                    tope=tope+0.3*cm
                    elements += [
                        Label(text="Documento", top=tope, left=5*cm, style={'fontSize': 8}),
                        Label(text="Fecha ", top=tope, left=7*cm, style={'fontSize': 8}),
                        Label(text="Cantidad", top=tope, left=9*cm, style={'fontSize': 8}),]

                    height = tope+0.5*cm
                    borders = {'bottom': True}
            
                class band_page_footer(ReportBand):
                    height = 0.5*cm
                    elements = [
                        Label(text='Comerciax', top=0.1*cm),
                        ]
                    borders = {'top': True}                          

                class band_summary(ReportBand):
                    height = 0.5*cm
                    elements = [
                        Label(text='====  Total General ====', style={'fontSize': 6}),
                        ObjectValue(expression='sum(cantidad)', left=4.1*cm, style={'fontName': 'Helvetica-Bold', 'fontSize': 6, 'alignment': TA_RIGHT}),
                        ]

                groups = [
                     ReportGroup(
                        attribute_name='organismo',
                        band_header=DetailBand(
                            height=0.6*cm,
                            width = 6.67*cm,
                            elements=[
                                Label(text='>', style={'fontSize': 6}),
                                ObjectValue(expression='organismo',  left=5,style={'fontSize': 6})
                            ]
                        ),
                        band_footer=ReportBand(
                            height = 0.5*cm,
                            elements = [
                                Label(text='> Total Organismo', style={'fontSize': 6}),
                                ObjectValue(expression='sum(cantidad)', left=4.1*cm, style={'fontName': 'Helvetica-Bold','fontSize':6, 'alignment': TA_RIGHT}),
                                ],
                            borders = {'top': True, 'bottom': True, 'fontSize':6, 'fontName': 'Helvetica'}
                        ),
                    ),
                    ReportGroup(
                        attribute_name='provincia',
                        band_header=DetailBand(
                            height=0.5*cm,
                            width = 6.67*cm,
                            elements=[
                                Label(text='>>', style={'fontSize': 6}),
                                ObjectValue(expression='provincia', style={'fontSize': 6}, left=2.2*cm)
                            ]
                        ),
                        band_footer=ReportBand(
                            height = 0.5*cm,
                            elements = [
                                Label(text='>> Total Provincia', style={'fontSize': 6}),
                                ObjectValue(expression='sum(cantidad)', left=4.1*cm, style={'fontName': 'Helvetica-Bold','fontSize': 6, 'alignment': TA_RIGHT}),
                                ],
                            borders = {'top': True, 'bottom': True, 'fontSize':6, 'fontName': 'Helvetica'}
                        ),
                    ),
                    ReportGroup(
                        attribute_name='cliente',
                        band_header=DetailBand(
                            height=0.5*cm,
                            width = 8*cm,
                            elements=[
                                Label(text='>>>', style={'fontSize': 6}),
                                ObjectValue(expression='cliente', style={'fontSize': 6}, left=4*cm, width = 12*cm)
                            ]
                        ),
                        band_footer=ReportBand(
                            height = 0.5*cm,
                            elements = [
                                Label(text='>>> Total Cliente', style={'fontSize': 6}),
                                ObjectValue(expression='sum(cantidad)', left=4.1*cm, style={'fontName': 'Helvetica-Bold','fontSize': 6, 'alignment': TA_RIGHT}),
                                ],
                            borders = {'top': True, 'bottom': True, 'fontSize':6, 'fontName': 'Helvetica'}
                        ),
                    ),
                          
                ]
        report = Report_4(queryset)
        try:
            fichero = open(pdf_name)
            fichero.close()
        except Exception, e:
            pass
        try:
            report.generate_by(PDFGenerator, pdf_name)
        except Exception, e:
            return 0
        return 2
    
    def Mov_CascosDesg(self,queryset,encabezado,pdf_name,filtro):
        #tipo 1- Recepcion Cliente
        #tipo 14 - Factura
        cur_dir = os.path.dirname(os.path.abspath(__file__))
        class Report_3(Report):
                title = encabezado
                class band_detail(ReportBand):
                        height = 0.4*cm
                        elements = [
                            ObjectValue(expression='nro_doc', left=5*cm, style={'fontSize': 6}),
                            ObjectValue(expression='fecha_doc', left=7*cm, style={'fontSize': 6}),
                            ObjectValue(expression='medida', left=9*cm, style={'fontSize': 6}),
                            ObjectValue(expression='cantidad', left=7.7*cm, style={'fontSize': 6,'alignment': TA_RIGHT}),] 
                        
                class band_page_header(ReportBand):
                    elements = [
                        SystemField(expression='%(report_title)s', top=0.1*cm, left=0, width=BAND_WIDTH,
                            style={'fontName': 'Helvetica-Bold', 'fontSize': 14, 'alignment': TA_CENTER}),
                        SystemField(expression=u'Página %(page_number)d de %(page_count)d', top=0.1*cm,
                            width=BAND_WIDTH, style={'alignment': TA_RIGHT,'fontSize': 5}),
                        SystemField(expression='Impreso el %(now:%d/%m/%Y )s a las %(now:%H:%M)s', top=0.1*cm,
                            width=BAND_WIDTH, style={'alignment': TA_LEFT,'fontSize': 5}),]
                    if filtro.__len__()!=0:     
                        elements+=[Label(text="Filtro:", top=0.9*cm, left=0.1*cm, style={'fontSize': 5}),]
                    tope=1.2*cm
                    for k in range(filtro.__len__()):
                            elements+=[Label(text=filtro[k], top=tope, left=0.1*cm, style={'fontSize': 5}, width=BAND_WIDTH),]
                            tope=tope+0.3*cm
                        
                    tope=tope+0.3*cm
                    elements += [
                        Label(text="Documento", top=tope, left=5*cm, style={'fontSize': 8}),
                        Label(text="Fecha ", top=tope, left=7*cm, style={'fontSize': 8}),
                        Label(text="Medida ", top=tope, left=9*cm, style={'fontSize': 8}),
                        Label(text="Cantidad", top=tope, left=12*cm, style={'fontSize': 8}),]

                    height = tope+0.5*cm
                    borders = {'bottom': True}
            
                class band_page_footer(ReportBand):
                    height = 0.5*cm
                    elements = [
                        Label(text='Comerciax', top=0.1*cm),
                        ]
                    borders = {'top': True}                          

                class band_summary(ReportBand):
                    height = 0.5*cm
                    elements = [
                        Label(text='====  Total General ====', style={'fontSize': 6}),
                        ObjectValue(expression='sum(cantidad)', left=7.7*cm, style={'fontName': 'Helvetica-Bold', 'fontSize': 6, 'alignment': TA_RIGHT}),
                        ]
                
                groups = [
                     ReportGroup(
                        attribute_name='organismo',
                        band_header=DetailBand(
                            height=0.6*cm,
                            width = 6.67*cm,
                            elements=[
                                Label(text='>', style={'fontSize': 6}),
                                ObjectValue(expression='organismo',  left=5,style={'fontSize': 6})
                            ]
                        ),
                                
                        band_footer=ReportBand(
                            height = 0.5*cm,
                            elements = [
                                Label(text='> Total Organismo', style={'fontSize': 6}),
                                ObjectValue(expression='sum(cantidad)', left=7.7*cm, style={'fontSize':6, 'alignment': TA_RIGHT}),
                                ],
                            borders = {'top': True, 'bottom': True, 'fontSize':6, 'fontName': 'Helvetica'}
                        ),
                    ),
                    ReportGroup(
                        attribute_name='provincia',
                        band_header=DetailBand(
                            height=0.5*cm,
                            width = 6.67*cm,
                            elements=[
                                Label(text='>>', style={'fontSize': 6}),
                                ObjectValue(expression='provincia', style={'fontSize': 6}, left=2.2*cm)
                            ]
                        ),
                        band_footer=ReportBand(
                            height = 0.5*cm,
                            elements = [
                                Label(text='>> Total Provincia', style={'fontSize': 6}),
                                ObjectValue(expression='sum(cantidad)', left=7.7*cm, style={'fontSize': 6, 'alignment': TA_RIGHT}),
                                ],
                            borders = {'top': True, 'bottom': True, 'fontSize':6, 'fontName': 'Helvetica'}
                        ),
                    ),
                    ReportGroup(
                        attribute_name='cliente',
                        band_header=DetailBand(
                            height=0.5*cm,
                            width = 8*cm,
                            elements=[
                                Label(text='>>>', style={'fontSize': 6}),
                                ObjectValue(expression='cliente', style={'fontSize': 6}, left=4*cm, width = 12*cm)
                            ]
                        ),
                        band_footer=ReportBand(
                            height = 0.5*cm,
                            elements = [
                                Label(text='>>> Total Cliente', style={'fontSize': 6}),
                                ObjectValue(expression='sum(cantidad)', left=7.7*cm, style={'fontSize': 6, 'alignment': TA_RIGHT}),
                                ],
                            borders = {'top': True, 'bottom': True, 'fontSize':6, 'fontName': 'Helvetica'}
                        ),
                    ),
                          
                    ReportGroup(
                        attribute_name='nro_doc',
                        band_footer=ReportBand(
                            height = 0.5*cm,
                            elements = [
                                Label(text='==== Total Documento ====', style={'fontSize': 6}),
                                ObjectValue(expression='sum(cantidad)', left=7.7*cm, style={'fontName': 'Helvetica-Bold','fontSize': 6, 'alignment': TA_RIGHT}),
                                ],
                            borders = {'top': True, 'bottom': True, 'fontSize':6, 'fontName': 'Helvetica'}
                        ),
                    ),
                ]
        report = Report_3(queryset)
        try:
            fichero = open(pdf_name)
            fichero.close()
        except Exception, e:
            pass
        try:
            report.generate_by(PDFGenerator, pdf_name)
        except Exception, e:
            return 0
        return 2
    
    def Mov_CascosDesgxMed(self,queryset,encabezado,pdf_name,filtro):
        #tipo 1- Recepcion Cliente
        #tipo 14 - Factura
        cur_dir = os.path.dirname(os.path.abspath(__file__))
        class Report_3(Report):
                title = encabezado
                class band_detail(ReportBand):
                        height = 0.4*cm
                        elements = [
                            ObjectValue(expression='nro_doc', left=5*cm, style={'fontSize': 9}),
                            ObjectValue(expression='fecha_doc', left=7*cm, style={'fontSize': 9}),
                            ObjectValue(expression='cantidad', left=7.7*cm, style={'fontSize': 9,'alignment': TA_RIGHT}),] 
                        
                class band_page_header(ReportBand):
                    elements = [
                        SystemField(expression='%(report_title)s', top=0.1*cm, left=0, width=BAND_WIDTH,
                            style={'fontName': 'Helvetica-Bold', 'fontSize': 14, 'alignment': TA_CENTER}),
                        SystemField(expression=u'Página %(page_number)d de %(page_count)d', top=0.1*cm,
                            width=BAND_WIDTH, style={'alignment': TA_RIGHT,'fontSize': 6}),
                        SystemField(expression='Impreso el %(now:%d/%m/%Y )s a las %(now:%H:%M)s', top=0.1*cm,
                            width=BAND_WIDTH, style={'alignment': TA_LEFT,'fontSize': 6}),]
                    if filtro.__len__()!=0:     
                        elements+=[Label(text="Filtro:", top=0.9*cm, left=0.1*cm, style={'fontSize': 6}),]
                    tope=1.2*cm
                    for k in range(filtro.__len__()):
                            elements+=[Label(text=filtro[k], top=tope, left=0.1*cm, style={'fontSize': 6}, width=BAND_WIDTH),]
                            tope=tope+0.3*cm
                        
                    tope=tope+0.3*cm
                    elements += [
                        Label(text="Documento", top=tope, left=5*cm, style={'fontSize': 8}),
                        Label(text="Fecha ", top=tope, left=7*cm, style={'fontSize': 8}),
                        Label(text="Cantidad", top=tope, left=12*cm, style={'fontSize': 8}),]

                    height = tope+0.5*cm
                    borders = {'bottom': True}
            
                class band_page_footer(ReportBand):
                    height = 0.5*cm
                    elements = [
                        Label(text='Comerciax', top=0.1*cm),
                        ]
                    borders = {'top': True}                          

                class band_summary(ReportBand):
                    height = 0.5*cm
                    elements = [
                        Label(text='====  Total General ====', style={'fontSize': 9}),
                        ObjectValue(expression='sum(cantidad)', left=7.7*cm, style={'fontName': 'Helvetica-Bold', 'fontSize': 9, 'alignment': TA_RIGHT}),
                        ]
                
                groups = [
                    ReportGroup(
                        attribute_name='medida',
                        band_header=DetailBand(
                            height=0.6*cm,
                            width = 6.67*cm,
                            elements=[
                                Label(text='>', style={'fontSize': 9}),
                                ObjectValue(expression='medida',  left=5,style={'fontSize': 9})
                            ]
                        ),
                                
                        band_footer=ReportBand(
                            height = 0.5*cm,
                            elements = [
                                Label(text='> Total Medida', style={'fontSize': 9}),
                                ObjectValue(expression='sum(cantidad)', left=7.7*cm, style={'fontSize':9, 'alignment': TA_RIGHT}),
                                ],
                            borders = {'top': True, 'bottom': True, 'fontSize':9, 'fontName': 'Helvetica'}
                        ),
                    ),
                     ReportGroup(
                        attribute_name='organismo',
                        band_header=DetailBand(
                            height=0.6*cm,
                            width = 6.67*cm,
                            elements=[
                                Label(text=' >>', style={'fontSize': 9}),
                                ObjectValue(expression='organismo',  left=1.5*cm,style={'fontSize': 9})
                            ]
                        ),
                                
                        band_footer=ReportBand(
                            height = 0.5*cm,
                            elements = [
                                Label(text='>> Total Organismo', style={'fontSize': 9}),
                                ObjectValue(expression='sum(cantidad)', left=7.7*cm, style={'fontSize':9, 'alignment': TA_RIGHT}),
                                ],
                            borders = {'top': True, 'bottom': True, 'fontSize':9, 'fontName': 'Helvetica'}
                        ),
                    ),
                    ReportGroup(
                        attribute_name='provincia',
                        band_header=DetailBand(
                            height=0.5*cm,
                            width = 6.67*cm,
                            elements=[
                                Label(text='>>>', style={'fontSize': 9}),
                                ObjectValue(expression='provincia', style={'fontSize': 9}, left=2.2*cm)
                            ]
                        ),
                        band_footer=ReportBand(
                            height = 0.5*cm,
                            elements = [
                                Label(text='>>> Total Provincia', style={'fontSize': 9}),
                                ObjectValue(expression='sum(cantidad)', left=7.7*cm, style={'fontSize': 9, 'alignment': TA_RIGHT}),
                                ],
                            borders = {'top': True, 'bottom': True, 'fontSize':9, 'fontName': 'Helvetica'}
                        ),
                    ),
                    ReportGroup(
                        attribute_name='cliente',
                        band_header=DetailBand(
                            height=0.5*cm,
                            width = 8*cm,
                            elements=[
                                Label(text='>>>>', style={'fontSize': 9}),
                                ObjectValue(expression='cliente', style={'fontSize': 9}, left=4*cm, width = 12*cm)
                            ]
                        ),
                        band_footer=ReportBand(
                            height = 0.5*cm,
                            elements = [
                                Label(text='>>>> Total Cliente', style={'fontSize': 9}),
                                ObjectValue(expression='sum(cantidad)', left=7.7*cm, style={'fontSize': 9, 'alignment': TA_RIGHT}),
                                ],
                            borders = {'top': True, 'bottom': True, 'fontSize':9, 'fontName': 'Helvetica'}
                        ),
                    ),
                ]
        report = Report_3(queryset)
        try:
            fichero = open(pdf_name)
            fichero.close()
        except Exception, e:
            pass
        try:
            report.generate_by(PDFGenerator, pdf_name)
        except Exception, e:
            return 0
        return 2

    def Mov_FactDesg(self,queryset,encabezado,pdf_name,filtro):
        #tipo 1- Recepcion Cliente
        #tipo 14 - Factura
        cur_dir = os.path.dirname(os.path.abspath(__file__))
        class Report_5(Report):
                title = encabezado
                class band_detail(ReportBand):
                        height = 0.4*cm
                        elements = [
                            ObjectValue(expression='nro_doc', left=5*cm, style={'fontSize': 6}),
                            ObjectValue(expression='fecha_doc', left=7*cm, style={'fontSize': 6}),
                            ObjectValue(expression='medida', left=9*cm, style={'fontSize': 6}),
                            ObjectValue(expression='cantidad', left=7.7*cm, style={'fontSize': 6,'alignment': TA_RIGHT}),
                            ObjectValue(expression='importe', left=9.95*cm, style={'fontSize': 6,'alignment': TA_RIGHT}),] 
                        
                class band_page_header(ReportBand):
                    elements = [
                        SystemField(expression='%(report_title)s', top=0.1*cm, left=0, width=BAND_WIDTH,
                            style={'fontName': 'Helvetica-Bold', 'fontSize': 14, 'alignment': TA_CENTER}),
                        SystemField(expression=u'Página %(page_number)d de %(page_count)d', top=0.1*cm,
                            width=BAND_WIDTH, style={'alignment': TA_RIGHT,'fontSize': 5}),
                        SystemField(expression='Impreso el %(now:%d/%m/%Y )s a las %(now:%H:%M)s', top=0.1*cm,
                            width=BAND_WIDTH, style={'alignment': TA_LEFT,'fontSize': 5}),]
                    if filtro.__len__()!=0:     
                        elements+=[Label(text="Filtro:", top=0.9*cm, left=0.1*cm, style={'fontSize': 5}),]
                    tope=1.2*cm
                    for k in range(filtro.__len__()):
                            elements+=[Label(text=filtro[k], top=tope, left=0.1*cm, style={'fontSize': 5}, width=BAND_WIDTH),]
                            tope=tope+0.3*cm
                        
                    tope=tope+0.3*cm
                    elements += [
                        Label(text="Factura", top=tope, left=5*cm, style={'fontSize': 8}),
                        Label(text="Fecha ", top=tope, left=7*cm, style={'fontSize': 8}),
                        Label(text="Medida ", top=tope, left=9*cm, style={'fontSize': 8}),
                        Label(text="Cantidad", top=tope, left=12*cm, style={'fontSize': 8}),
                        Label(text="Importe CUP", top=tope, left=14*cm, style={'fontSize': 8}),]

                    height = tope+0.5*cm
                    borders = {'bottom': True}
            
                class band_page_footer(ReportBand):
                    height = 0.5*cm
                    elements = [
                        Label(text='Comerciax', top=0.1*cm),
                        ]
                    borders = {'top': True}                          

                class band_summary(ReportBand):
                    height = 0.5*cm
                    elements = [
                        Label(text='====  Total General ====', style={'fontSize': 6}),
                        ObjectValue(expression='sum(cantidad)', left=7.7*cm, style={'fontName': 'Helvetica-Bold', 'fontSize': 6, 'alignment': TA_RIGHT}),
                        ObjectValue(expression='sum(importe)', left=9.95*cm, style={'fontName': 'Helvetica-Bold', 'fontSize': 6, 'alignment': TA_RIGHT}),
                        ]
                
                groups = [
                     ReportGroup(
                        attribute_name='organismo',
                        band_header=DetailBand(
                            height=0.6*cm,
                            width = 6.67*cm,
                            elements=[
                                Label(text='>', style={'fontSize': 6}),
                                ObjectValue(expression='organismo',  left=5,style={'fontSize': 6})
                            ]
                        ),
                                
                        band_footer=ReportBand(
                            height = 0.5*cm,
                            elements = [
                                Label(text='> Total Organismo', style={'fontSize': 6}),
                                ObjectValue(expression='sum(cantidad)', left=7.7*cm, style={'fontName': 'Helvetica-Bold','fontSize':6, 'alignment': TA_RIGHT}),
                                ObjectValue(expression='sum(importe)', left=9.95*cm, style={'fontName': 'Helvetica-Bold','fontName': 'Helvetica-Bold', 'fontSize': 6, 'alignment': TA_RIGHT}),
                                ],
                            borders = {'top': True, 'bottom': True, 'fontSize':6, 'fontName': 'Helvetica'}
                        ),
                    ),
                    ReportGroup(
                        attribute_name='provincia',
                        band_header=DetailBand(
                            height=0.5*cm,
                            width = 6.67*cm,
                            elements=[
                                Label(text='>>', style={'fontSize': 6}),
                                ObjectValue(expression='provincia', style={'fontSize': 6}, left=2.2*cm)
                            ]
                        ),
                        band_footer=ReportBand(
                            height = 0.5*cm,
                            elements = [
                                Label(text='>> Total Provincia', style={'fontSize': 6}),
                                ObjectValue(expression='sum(cantidad)', left=7.7*cm, style={'fontName': 'Helvetica-Bold','fontSize': 6, 'alignment': TA_RIGHT}),
                                ObjectValue(expression='sum(importe)', left=9.95*cm, style={'fontName': 'Helvetica-Bold', 'fontSize': 6, 'alignment': TA_RIGHT}),
                                ],
                            borders = {'top': True, 'bottom': True, 'fontSize':6, 'fontName': 'Helvetica'}
                        ),
                    ),
                    ReportGroup(
                        attribute_name='cliente',
                        band_header=DetailBand(
                            height=0.5*cm,
                            width = 8*cm,
                            elements=[
                                Label(text='>>>', style={'fontSize': 6}),
                                ObjectValue(expression='cliente', style={'fontSize': 6}, left=4*cm, width = 12*cm)
                            ]
                        ),
                        band_footer=ReportBand(
                            height = 0.5*cm,
                            elements = [
                                Label(text='>>> Total Cliente', style={'fontSize': 6}),
                                ObjectValue(expression='sum(cantidad)', left=7.7*cm, style={'fontName': 'Helvetica-Bold','fontSize': 6, 'alignment': TA_RIGHT}),
                                ObjectValue(expression='sum(importe)', left=9.95*cm, style={'fontName': 'Helvetica-Bold', 'fontSize': 6, 'alignment': TA_RIGHT}),
                                ],
                            borders = {'top': True, 'bottom': True, 'fontSize':6, 'fontName': 'Helvetica'}
                        ),
                    ),
                          
                    ReportGroup(
                        attribute_name='nro_doc',
                        band_footer=ReportBand(
                            height = 0.5*cm,
                            elements = [
                                Label(text='==== Total Factura ====', style={'fontSize': 6}),
                                ObjectValue(expression='sum(cantidad)', left=7.7*cm, style={'fontName': 'Helvetica-Bold','fontSize': 6, 'alignment': TA_RIGHT}),
                                ObjectValue(expression='sum(importe)', left=9.95*cm, style={'fontName': 'Helvetica-Bold', 'fontSize': 6, 'alignment': TA_RIGHT}),
                                ],
                            borders = {'top': True, 'bottom': True, 'fontSize':6, 'fontName': 'Helvetica'}
                        ),
                    ),
                ]
        report = Report_5(queryset)
        try:
            fichero = open(pdf_name)
            fichero.close()
        except Exception, e:
            pass
        try:
            report.generate_by(PDFGenerator, pdf_name)
        except Exception, e:
            return 0
        return 2
    
    def Mov_ProdDesg(self,queryset,encabezado,pdf_name,filtro):
        #tipo 1- Recepcion Cliente
        #tipo 14 - Factura
        cur_dir = os.path.dirname(os.path.abspath(__file__))
        class Report_5(Report):
                title = encabezado
                class band_detail(ReportBand):
                        height = 0.4*cm
                        elements = [
                                    
                            ObjectValue(expression="medida", left=8*cm, style={'fontSize': 6}),
                            ObjectValue(expression="nro_casco", left=6*cm, style={'fontSize': 6}),
                            ObjectValue(expression='cantidad', left=7.7*cm, style={'fontSize': 6,'alignment': TA_RIGHT})]
                        
                class band_page_header(ReportBand):
                    elements = [
                        SystemField(expression='%(report_title)s', top=-0.5*cm, left=0, width=BAND_WIDTH,
                            style={'fontName': 'Helvetica-Bold', 'fontSize': 14, 'alignment': TA_CENTER}),
                        SystemField(expression=u'Página %(page_number)d de %(page_count)d', top=0.1*cm,
                            width=BAND_WIDTH, style={'alignment': TA_RIGHT,'fontSize': 5}),
                        SystemField(expression='Impreso el %(now:%d/%m/%Y )s a las %(now:%H:%M)s', top=0.1*cm,
                            width=BAND_WIDTH, style={'alignment': TA_LEFT,'fontSize': 5}),]
                    
                    if filtro.__len__()!=0:     
                        elements+=[Label(text="Filtro:", top=0.9*cm, left=0.1*cm, style={'fontSize': 5}),]
                    tope=1.2*cm
                    for k in range(filtro.__len__()):
                            elements+=[Label(text=filtro[k], top=tope, left=0.1*cm, style={'fontSize': 5}, width=BAND_WIDTH),]
                            tope=tope+0.3*cm
                        
                    tope=tope+0.3*cm
 
                    elements += [
                        Label(text="Cantidad", top=tope, left=12*cm, style={'fontSize': 8}),
                        Label(text="Documento", top=tope, left=1*cm, style={'fontSize': 8}),
                        Label(text="Medida", top=tope, left=8*cm, style={'fontSize': 8}),
                        Label(text="Nro. Casco", top=tope, left=6*cm, style={'fontSize': 8}),
                        Label(text="Cliente", top=tope, left=4*cm, style={'fontSize': 8}),]

                    height = tope+0.5*cm
                    borders = {'bottom': True}
            
                class band_page_footer(ReportBand):
                    height = 0.5*cm
                    elements = [
                        Label(text='Comerciax', top=0.1*cm),
                        ]
                    borders = {'top': True}                          

                class band_summary(ReportBand):
                    height = 0.5*cm
                    elements = [
                        Label(text='====  Total General ====', style={'fontSize': 6}),
                        ObjectValue(expression='sum(cantidad)', left=7.7*cm, style={'fontName': 'Helvetica-Bold', 'fontSize': 6, 'alignment': TA_RIGHT}),
                        ]
                
                groups = [
                     ReportGroup(
                        attribute_name='nro_doc',
                        band_header=DetailBand(
                            height=0.6*cm,
                            width = 10*cm,
                            elements=[
                                Label(text='> Documento:', style={'fontSize': 6}, width =3*cm),
                                ObjectValue(expression='nro_doc',  left=0.5*cm, width =1.4*cm,style={'fontSize': 6, 'alignment': TA_RIGHT}),
                                ObjectValue(expression='fecha_doc',  left=2*cm, width =1.4*cm,style={'fontSize': 6, 'alignment': TA_RIGHT}),
                                
                            ]
                        ),
                                
                        band_footer=ReportBand(
                            height = 0.5*cm,
                            elements = [
                                Label(text='==== Total Documento ====', style={'fontSize': 6}),
                                ObjectValue(expression='sum(cantidad)', left=7.7*cm, style={'fontName': 'Helvetica-Bold','fontSize':6, 'alignment': TA_RIGHT}),
                                ],
                            borders = {'top': True, 'bottom': True, 'fontSize':6, 'fontName': 'Helvetica'}
                        ),
                    ),
                    ReportGroup(
                        attribute_name='cliente',
                        band_header=DetailBand(
                            height=0.5*cm,
                            width = 6.67*cm,
                            elements=[
                                Label(text='>>', style={'fontSize': 6}),
                                ObjectValue(expression='cliente', style={'fontSize': 6}, left=2.2*cm, width=8*cm)
                            ]
                        ),
                        band_footer=ReportBand(
                            height = 0.5*cm,
                            elements = [
                                Label(text='==== Total Cliente ====', left=2.2*cm, style={'fontSize': 6}),
                                ObjectValue(expression='sum(cantidad)', left=7.7*cm, style={'fontName': 'Helvetica-Bold','fontSize': 6, 'alignment': TA_RIGHT}),
                                ],
                            borders = {'top': True, 'bottom': True, 'fontSize':6, 'fontName': 'Helvetica'}
                        ),
                    ),
                    ReportGroup(
                        attribute_name='medida',
                        band_footer=ReportBand(
                            height = 0.5*cm,
                            elements = [
                                Label(text='==== Total Medida ====', left=8*cm, style={'fontSize': 6}),
                                ObjectValue(expression='sum(cantidad)', left=7.7*cm, style={'fontName': 'Helvetica-Bold','fontSize': 6, 'alignment': TA_RIGHT}),
                                ],
#                            borders = {'top': True, 'bottom': True, 'fontSize':6, 'fontName': 'Helvetica'}
                        ),
                    ),
                ]
        report = Report_5(queryset)
        try:
            fichero = open(pdf_name)
            fichero.close()
        except Exception, e:
            pass
        try:
            report.generate_by(PDFGenerator, pdf_name)
        except Exception, e:
            return 0
        return 2
    
    def Mov_Prod(self,queryset,encabezado,pdf_name,filtro):
        #tipo 1- Recepcion Cliente
        cur_dir = os.path.dirname(os.path.abspath(__file__))
        class Report_5(Report):
                title = encabezado
                class band_detail(ReportBand):
                        height = 0.4*cm
                        elements = [
                            ObjectValue(expression='cliente', left=1*cm, width=11*cm,style={'fontSize': 6,'alignment': TA_LEFT}),
                            ObjectValue(expression='cantidad', left=7.7*cm, style={'fontSize': 6,'alignment': TA_RIGHT})]
                        
                class band_page_header(ReportBand):
                    elements = [
                        SystemField(expression='%(report_title)s', top=-0.5*cm, left=0, width=BAND_WIDTH,
                            style={'fontName': 'Helvetica-Bold', 'fontSize': 14, 'alignment': TA_CENTER}),
                        SystemField(expression=u'Página %(page_number)d de %(page_count)d', top=0.1*cm,
                            width=BAND_WIDTH, style={'alignment': TA_RIGHT,'fontSize': 5}),
                        SystemField(expression='Impreso el %(now:%d/%m/%Y )s a las %(now:%H:%M)s', top=0.1*cm,
                            width=BAND_WIDTH, style={'alignment': TA_LEFT,'fontSize': 5}),]
                    
                    if filtro.__len__()!=0:     
                        elements+=[Label(text="Filtro:", top=0.9*cm, left=0.1*cm, style={'fontSize': 5}),]
                    tope=1.2*cm
                    for k in range(filtro.__len__()):
                            elements+=[Label(text=filtro[k], top=tope, left=0.1*cm, style={'fontSize': 5}, width=BAND_WIDTH),]
                            tope=tope+0.3*cm
                        
                    tope=tope+0.3*cm
                    elements += [
                        Label(text="Documento", top=tope, left=1*cm, style={'fontSize': 8}),
                        Label(text="Cliente", top=tope, left=4*cm, style={'fontSize': 8}),
                        Label(text="Cantidad", top=tope, left=12*cm, style={'fontSize': 8}),]

                    height = tope+0.5*cm
                    borders = {'bottom': True}
            
                class band_page_footer(ReportBand):
                    height = 0.5*cm
                    elements = [
                        Label(text='Comerciax', top=0.1*cm),
                        ]
                    borders = {'top': True}                          

                class band_summary(ReportBand):
                    height = 0.5*cm
                    elements = [
                        Label(text='====  Total General ====', style={'fontSize': 6}),
                        ObjectValue(expression='sum(cantidad)', left=7.7*cm, style={'fontName': 'Helvetica-Bold', 'fontSize': 6, 'alignment': TA_RIGHT}),
                        ]
                
                groups = [
                     ReportGroup(
                        attribute_name='nro_doc',
                        band_header=DetailBand(
                            height=0.6*cm,
                            width = 10*cm,
                            elements=[
                                Label(text='> Documento:', style={'fontSize': 6}, width =3*cm),
                                ObjectValue(expression='nro_doc',  left=0.5*cm, width =1.4*cm,style={'fontSize': 6, 'alignment': TA_RIGHT}),
                                ObjectValue(expression='fecha_doc',  left=2*cm, width =1.4*cm,style={'fontSize': 6, 'alignment': TA_RIGHT}),
                                
                            ]
                        ),
                                
                        band_footer=ReportBand(
                            height = 0.5*cm,
                            elements = [
                                Label(text='==== Total Documento ====', style={'fontSize': 6}),
                                ObjectValue(expression='sum(cantidad)', left=7.7*cm, style={'fontName': 'Helvetica-Bold','fontSize':6, 'alignment': TA_RIGHT}),
                                ],
                            borders = {'top': True, 'bottom': True, 'fontSize':6, 'fontName': 'Helvetica'}
                        ),
                    ),
                ]
        report = Report_5(queryset)
        try:
            fichero = open(pdf_name)
            fichero.close()
        except Exception, e:
            pass
        try:
            report.generate_by(PDFGenerator, pdf_name)
        except Exception, e:
            return 0
        return 2
    
    def Mov_Fact(self,queryset,encabezado,pdf_name,filtro):
        #tipo 1- Recepcion Cliente
        #tipo 14 - Factura
        cur_dir = os.path.dirname(os.path.abspath(__file__))
        class Report_6(Report):
                title = encabezado
                class band_detail(ReportBand):
                        height = 0.4*cm
                        elements = [
                            ObjectValue(expression='nro_doc', left=5*cm, style={'fontSize': 6}),
                            ObjectValue(expression='fecha_doc', left=7*cm, style={'fontSize': 6}),
                            ObjectValue(expression='cantidad', left=4.8*cm, style={'fontSize': 6,'alignment': TA_RIGHT}),
                            ObjectValue(expression='importe', left=7.9*cm, style={'fontSize': 6,'alignment': TA_RIGHT}),] 
                        
                class band_page_header(ReportBand):
                    elements = [
                        SystemField(expression='%(report_title)s', top=0.1*cm, left=0, width=BAND_WIDTH,
                            style={'fontName': 'Helvetica-Bold', 'fontSize': 14, 'alignment': TA_CENTER}),
                        SystemField(expression=u'Página %(page_number)d de %(page_count)d', top=0.1*cm,
                            width=BAND_WIDTH, style={'alignment': TA_RIGHT,'fontSize': 5}),
                        SystemField(expression='Impreso el %(now:%d/%m/%Y )s a las %(now:%H:%M)s', top=0.1*cm,
                            width=BAND_WIDTH, style={'alignment': TA_LEFT,'fontSize': 5}),]
                    if filtro.__len__()!=0:     
                        elements+=[Label(text="Filtro:", top=0.9*cm, left=0.1*cm, style={'fontSize': 5}),]
                    tope=1.2*cm
                    for k in range(filtro.__len__()):
                            elements+=[Label(text=filtro[k], top=tope, left=0.1*cm, style={'fontSize': 5}, width=BAND_WIDTH),]
                            tope=tope+0.3*cm
                        
                    tope=tope+0.3*cm
                    elements += [
                        Label(text="Factura", top=tope, left=5*cm, style={'fontSize': 8}),
                        Label(text="Fecha ", top=tope, left=7*cm, style={'fontSize': 8}),
                        Label(text="Cantidad", top=tope, left=9*cm, style={'fontSize': 8}),
                        Label(text="Importe CUP", top=tope, left=12*cm, style={'fontSize': 8}),]

                    height = tope+0.5*cm
                    borders = {'bottom': True}
            
                class band_page_footer(ReportBand):
                    height = 0.5*cm
                    elements = [
                        Label(text='Comerciax', top=0.1*cm),
                        ]
                    borders = {'top': True}                          

                class band_summary(ReportBand):
                    height = 0.5*cm
                    elements = [
                        Label(text='====  Total General ====', style={'fontSize': 6}),
                        ObjectValue(expression='sum(cantidad)', left=4.8*cm, style={'fontName': 'Helvetica-Bold', 'fontSize': 6, 'alignment': TA_RIGHT}),
                        ObjectValue(expression='sum(importe)', left=7.95*cm, style={'fontName': 'Helvetica-Bold', 'fontSize': 6, 'alignment': TA_RIGHT}),
                        ]
                
                groups = [
                     ReportGroup(
                        attribute_name='organismo',
                        band_header=DetailBand(
                            height=0.6*cm,
                            width = 6.67*cm,
                            elements=[
                                Label(text='>', style={'fontSize': 6}),
                                ObjectValue(expression='organismo',  left=5,style={'fontSize': 6})
                            ]
                        ),
                                
                        band_footer=ReportBand(
                            height = 0.5*cm,
                            elements = [
                                Label(text='> Total Organismo', style={'fontSize': 6}),
                                ObjectValue(expression='sum(cantidad)', left=4.8*cm, style={'fontSize':6, 'alignment': TA_RIGHT}),
                                ObjectValue(expression='sum(importe)', left=7.95*cm, style={'fontName': 'Helvetica-Bold', 'fontSize': 6, 'alignment': TA_RIGHT}),
                                ],
                            borders = {'top': True, 'bottom': True, 'fontSize':6, 'fontName': 'Helvetica'}
                        ),
                    ),
                    ReportGroup(
                        attribute_name='provincia',
                        band_header=DetailBand(
                            height=0.5*cm,
                            width = 6.67*cm,
                            elements=[
                                Label(text='>>', style={'fontSize': 6}),
                                ObjectValue(expression='provincia', style={'fontSize': 6}, left=2.2*cm)
                            ]
                        ),
                        band_footer=ReportBand(
                            height = 0.5*cm,
                            elements = [
                                Label(text='>> Total Provincia', style={'fontSize': 6}),
                                ObjectValue(expression='sum(cantidad)', left=4.8*cm, style={'fontSize': 6, 'alignment': TA_RIGHT}),
                                ObjectValue(expression='sum(importe)', left=7.95*cm, style={'fontName': 'Helvetica-Bold', 'fontSize': 6, 'alignment': TA_RIGHT}),
                                ],
                            borders = {'top': True, 'bottom': True, 'fontSize':6, 'fontName': 'Helvetica'}
                        ),
                    ),
                    ReportGroup(
                        attribute_name='cliente',
                        band_header=DetailBand(
                            height=0.5*cm,
                            width = 8*cm,
                            elements=[
                                Label(text='>>>', style={'fontSize': 6}),
                                ObjectValue(expression='cliente', style={'fontSize': 6}, left=4*cm, width = 12*cm)
                            ]
                        ),
                        band_footer=ReportBand(
                            height = 0.5*cm,
                            elements = [
                                Label(text='>>> Total Cliente', style={'fontSize': 6}),
                                ObjectValue(expression='sum(cantidad)', left=4.8*cm, style={'fontSize': 6, 'alignment': TA_RIGHT}),
                                ObjectValue(expression='sum(importe)', left=7.95*cm, style={'fontName': 'Helvetica-Bold', 'fontSize': 6, 'alignment': TA_RIGHT}),
                                ],
                            borders = {'top': True, 'bottom': True, 'fontSize':6, 'fontName': 'Helvetica'}
                        ),
                    ),
                          
                ]
        report = Report_6(queryset)
        try:
            fichero = open(pdf_name)
            fichero.close()
        except Exception, e:
            pass
        try:
            report.generate_by(PDFGenerator, pdf_name)
        except Exception, e:
            return 0
        return 2  
 
    def Conciliacion(self,queryset,encabezado,pdf_name,filtro):
        #tipo 1- Recepcion Cliente
        #tipo 14 - Factura
        cur_dir = os.path.dirname(os.path.abspath(__file__))
        class Report_1(Report):
                title = encabezado
                class band_detail(ReportBand):
                        height = 0.4*cm
                        elements = [
                            ObjectValue(expression='Inicio', left=3.1*cm, style={'fontSize': 8, 'fontName': 'Helvetica-Bold'}),
                            ObjectValue(expression='Entregados', left=4.2*cm, style={'fontSize': 8}),
                            ObjectValue(expression='Deco', left=5.3*cm, style={'fontSize': 8}),
                            ObjectValue(expression='Factura', left=6.4*cm, style={'fontSize': 8}),
                            ObjectValue(expression='Devoluc', left=7.5*cm, style={'fontSize': 8}),
                            ObjectValue(expression='Deco + Factura + Devoluc', left=8.6*cm, style={'fontSize': 8, 'fontName': 'Helvetica-Bold'}),
                            ObjectValue(expression='Casco', left=10.1*cm, style={'fontSize': 8}),
                            ObjectValue(expression='Produccion', left=11.2*cm, style={'fontSize': 8}),
                            ObjectValue(expression='PTer', left=12.4*cm, style={'fontSize': 8}),
                            ObjectValue(expression='Transferencia', left=13.2*cm, style={'fontSize': 8}),
                            ObjectValue(expression='DVP', left=14.7*cm, style={'fontSize': 8}),
                            ObjectValue(expression='Inserv', left=16*cm, style={'fontSize': 8}),
                            ObjectValue(expression='Casco + Produccion + PTer + Transferencia + DVP + Inserv', left=17.3*cm, style={'fontSize': 8, 'fontName': 'Helvetica-Bold'}),] 
                        
                class band_page_header(ReportBand):
                    elements = [
                        SystemField(expression='%(report_title)s', top=0.1*cm, left=0, width=BAND_WIDTH,
                            style={'fontName': 'Helvetica-Bold', 'fontSize': 14, 'alignment': TA_CENTER}),
                        SystemField(expression=u'Página %(page_number)d de %(page_count)d', top=0.1*cm,
                            width=BAND_WIDTH, style={'alignment': TA_RIGHT,'fontSize': 5}),
                        SystemField(expression='Impreso el %(now:%d/%m/%Y )s a las %(now:%H:%M)s', top=0.1*cm,
                            width=BAND_WIDTH, style={'alignment': TA_LEFT,'fontSize': 5}),]
                    if filtro.__len__()!=0:     
                        elements+=[Label(text="Filtro:", top=0.9*cm, left=0.1*cm, style={'fontSize': 5}),]
                    tope=1.2*cm
                    for k in range(filtro.__len__()):
                            elements+=[Label(text=filtro[k], top=tope, left=0.1*cm, style={'fontSize': 5}, width=BAND_WIDTH),]
                            tope=tope+0.3*cm
                        
                    tope=tope+0.3*cm
                    elements += [
                        Label(text="Inicio", top=tope, left=3.1*cm, style={'fontSize': 8, 'fontName': 'Helvetica-Bold'}),
                        Label(text="Ent. ", top=tope, left=4.2*cm, style={'fontSize': 8}),
                        Label(text="Dec. ", top=tope, left=5.3*cm, style={'fontSize': 8}),
                        Label(text="Fact.", top=tope, left=6.4*cm, style={'fontSize': 8}),
                        Label(text="Dev.", top=tope, left=7.5*cm, style={'fontSize': 8}),
                        Label(text="Tot. Sal.", top=tope, left=8.6*cm, style={'fontSize': 8, 'fontName': 'Helvetica-Bold'}),
                        Label(text="Casco", top=tope, left=10.1*cm, style={'fontSize': 8}),
                        Label(text="Prod.", top=tope, left=11.2*cm, style={'fontSize': 8}),
                        Label(text="PT", top=tope, left=12.4*cm, style={'fontSize': 8}),
                        Label(text="Transf.", top=tope, left=13.2*cm, style={'fontSize': 8}),
                        Label(text="Vulca", top=tope, left=14.7*cm, style={'fontSize': 8}),
                        Label(text="Inserv.", top=tope, left=16*cm, style={'fontSize': 8}),
                        Label(text="Tot. Fáb.", top=tope, left=17.3*cm, style={'fontSize': 8, 'fontName': 'Helvetica-Bold'}),
                        Label(text="Salidas", top=tope-0.5*cm, left=5.3*cm, style={'fontSize': 8}),
                        Label(text="Existencia en Fábrica", top=tope-0.5*cm, left=10.1*cm, style={'fontSize': 8}),]

                    height = tope+0.5*cm
                    borders = {'bottom': True}
            
                class band_page_footer(ReportBand):
                    height = 0.5*cm
                    elements = [
                        Label(text='Comerciax', top=0.1*cm),
                        ]
                    borders = {'top': True}                          

                class band_summary(ReportBand):
                    height = 0.5*cm
                    elements = [
                        Label(text='====  Total General ====', style={'fontSize': 6}),
                        ObjectValue(expression='sum(Inicio)', left=3.1*cm, style={'fontSize': 8, 'fontName': 'Helvetica-Bold'}),
                        ObjectValue(expression='sum(Entregados)', left=4.2*cm, style={'fontSize': 8}),
                        ObjectValue(expression='sum(Deco)', left=5.3*cm, style={'fontSize': 8}),
                        ObjectValue(expression='sum(Factura)', left=6.4*cm, style={'fontSize': 8}),
                        ObjectValue(expression='sum(Devoluc)', left=7.5*cm, style={'fontSize': 8}),
                        ObjectValue(expression='sum(Deco) + sum(Factura) + sum(Devoluc)', left=8.6*cm, style={'fontSize': 8, 'fontName': 'Helvetica-Bold'}),
                        ObjectValue(expression='sum(Casco)', left=10.1*cm, style={'fontSize': 8}),
                        ObjectValue(expression='sum(Produccion)', left=11.2*cm, style={'fontSize': 8}),
                        ObjectValue(expression='sum(PTer)', left=12.4*cm, style={'fontSize': 8}),
                        ObjectValue(expression='sum(Transferencia)', left=13.2*cm, style={'fontSize': 8}),
                        ObjectValue(expression='sum(DVP)', left=14.7*cm, style={'fontSize': 8}),
                        ObjectValue(expression='sum(Inserv)', left=16*cm, style={'fontSize': 8}),
                        ObjectValue(expression='sum(Casco) + sum(Produccion) + sum(PTer) + sum(Transferencia) + sum(DVP) + sum(Inserv)', left=17.3*cm, style={'fontSize': 8, 'fontName': 'Helvetica-Bold'}), 
                        ]
                
                groups = [
                     ReportGroup(
                        attribute_name='Organismo',
                        band_header=DetailBand(
                            height=0.4*cm,
                            width = 6.67*cm,
                            elements=[
                                Label(text='>', style={'fontSize': 6}),
                                ObjectValue(expression='Organismo',  left=5,style={'fontSize': 6})
                            ]
                        ),
                        band_footer=ReportBand(
                            height = 0.5*cm,
                            elements = [
                                Label(text='> Total Organismo', style={'fontSize': 6}),
                                ObjectValue(expression='sum(Inicio)', left=3.1*cm, style={'fontSize': 8, 'fontName': 'Helvetica-Bold'}),
                                ObjectValue(expression='sum(Entregados)', left=4.2*cm, style={'fontSize': 8}),
                                ObjectValue(expression='sum(Deco)', left=5.3*cm, style={'fontSize': 8}),
                                ObjectValue(expression='sum(Factura)', left=6.4*cm, style={'fontSize': 8}),
                                ObjectValue(expression='sum(Devoluc)', left=7.5*cm, style={'fontSize': 8}),
                                ObjectValue(expression='sum(Deco) + sum(Factura) + sum(Devoluc)', left=8.6*cm, style={'fontSize': 8, 'fontName': 'Helvetica-Bold'}),
                                ObjectValue(expression='sum(Casco)', left=10.1*cm, style={'fontSize': 8}),
                                ObjectValue(expression='sum(Produccion)', left=11.2*cm, style={'fontSize': 8}),
                                ObjectValue(expression='sum(PTer)', left=12.4*cm, style={'fontSize': 8}),
                                ObjectValue(expression='sum(Transferencia)', left=13.2*cm, style={'fontSize': 8}),
                                ObjectValue(expression='sum(DVP)', left=14.7*cm, style={'fontSize': 8}),
                                ObjectValue(expression='sum(Inserv)', left=16*cm, style={'fontSize': 8}),
                                ObjectValue(expression='sum(Casco) + sum(Produccion) + sum(PTer) + sum(Transferencia) + sum(DVP) + sum(Inserv)', left=17.3*cm, style={'fontSize': 8, 'fontName': 'Helvetica-Bold'}), 
                                ],
                            borders = {'top': True, 'bottom': True, 'fontSize':6, 'fontName': 'Helvetica'}
                        ),
                    ),
                    ReportGroup(
                        attribute_name='Provincia',
                        band_header=DetailBand(
                            height=0.4*cm,
                            width = 6.67*cm,
                            elements=[
                                Label(text='>>', style={'fontSize': 6}),
                                ObjectValue(expression='Provincia', style={'fontSize': 6}, left=0.9*cm)
                            ]
                        ),
                        band_footer=ReportBand(
                            height = 0.4*cm,
                            elements = [
                                Label(text='>> Total Prov.', style={'fontSize': 6}),
                                ObjectValue(expression='sum(Inicio)', left=3.1*cm, style={'fontSize': 8, 'fontName': 'Helvetica-Bold'}),
                                ObjectValue(expression='sum(Entregados)', left=4.2*cm, style={'fontSize': 8}),
                                ObjectValue(expression='sum(Deco)', left=5.3*cm, style={'fontSize': 8}),
                                ObjectValue(expression='sum(Factura)', left=6.4*cm, style={'fontSize': 8}),
                                ObjectValue(expression='sum(Devoluc)', left=7.5*cm, style={'fontSize': 8}),
                                ObjectValue(expression='sum(Deco) + sum(Factura) + sum(Devoluc)', left=8.6*cm, style={'fontSize': 8, 'fontName': 'Helvetica-Bold'}),
                                ObjectValue(expression='sum(Casco)', left=10.1*cm, style={'fontSize': 8}),
                                ObjectValue(expression='sum(Produccion)', left=11.2*cm, style={'fontSize': 8}),
                                ObjectValue(expression='sum(PTer)', left=12.4*cm, style={'fontSize': 8}),
                                ObjectValue(expression='sum(Transferencia)', left=13.2*cm, style={'fontSize': 8}),
                                ObjectValue(expression='sum(DVP)', left=14.7*cm, style={'fontSize': 8}),
                                ObjectValue(expression='sum(Inserv)', left=16*cm, style={'fontSize': 8}),
                                ObjectValue(expression='sum(Casco) + sum(Produccion) + sum(PTer) + sum(Transferencia) + sum(DVP) + sum(Inserv)', left=17.3*cm, style={'fontSize': 8, 'fontName': 'Helvetica-Bold'}), 
                                ],
                            borders = {'top': True, 'bottom': True, 'fontSize':6, 'fontName': 'Helvetica'}
                        ),
                    ),
                    ReportGroup(
                        attribute_name='Cliente',
                        band_header=DetailBand(
                            height=0.4*cm,
                            width = 8*cm,
                            elements=[
                                Label(text='>>>', style={'fontSize': 6}),
                                ObjectValue(expression='Cliente', style={'fontSize': 6}, left=1.5*cm, width = 12*cm)
                            ]
                        ),
                    ),
                          

                ]
        report = Report_1(queryset)
        try:
            fichero = open(pdf_name)
            fichero.close()
        except Exception, e:
            pass
        try:
            report.generate_by(PDFGenerator, pdf_name)
        except Exception, e:
            return 0
        return 2
    def Oferta(self, queryset, encabezados,pdf_file_name):
        cur_dir = os.path.dirname(os.path.abspath(__file__))
#        print cur_dir
        class Report_2(Report):               

            title = 'Oferta'
            class band_detail(ReportBand):

#
#                    # This is a new attribute to force the band width
                    width = 6.67*cm
            
                    # This attribute forces a distance at right side of the band
                    
            
#                    # With this attribute as True, the band will try to align in
#                    # the same line
#                    display_inline = True


                    height = 0.4*cm
                    elements = [
                        ObjectValue(expression = 'casco__producto_salida__codigo',top = 1.8*cm,left=0.1*cm, style={'fontSize': 6}),
                        ObjectValue(expression = 'casco__producto_salida__descripcion',top = 1.8*cm, width=6*cm,left=3*cm, style={'fontSize': 6}),
                        ObjectValue(expression = 'casco__producto_salida__um__descripcion',top = 1.8*cm, left=6.5*cm, style={'fontSize': 6}),
                        ObjectValue(expression = 'cantidad',top = 1.8*cm, left=8*cm, style={'fontSize': 6}),
                        ObjectValue(expression = 'precio_mn',top = 1.8*cm, left=9.5*cm, style={'fontSize': 6}),
                        ObjectValue(expression = 'importecup',top = 1.8*cm, left=11.5*cm, style={'fontSize': 6}),
                        ObjectValue(expression = 'precio_cuc',top = 1.8*cm, left=13.5*cm, style={'fontSize': 6}),
                        ObjectValue(expression = 'importecuc',top = 1.8*cm, left=15.5*cm, style={'fontSize': 6}),

                        ]                      
                
            class band_page_header(ReportBand):
                elements = [
                           
                    Label(text="Oferta:", top= -0.8*cm , left=3*cm, style={'fontSize': 6}),
                    Label(text= encabezados[0]['no_oferta'], top= -0.8*cm , left=3.8*cm, style={'fontSize': 6}),
                    Label(text="Código:", top= -0.8*cm, left=6*cm, style={'fontSize': 6}),
                    Label(text= encabezados[0]['titular_codigo'], top= -0.8*cm , left=6.8*cm, style={'fontSize': 6}),
                    Label(text="Titular:", top= -0.5*cm , left=3*cm, style={'fontSize': 6}),
                    Label(text= encabezados[0]['titular_name'], top= -0.5*cm , left=3.8*cm, style={'fontSize': 6}),
                    Label(text="Dirección:", top= -0.2*cm , left=3*cm, style={'fontSize': 6}),
                    Label(text= encabezados[0]['titular_dir'], top= -0.2*cm , left=4*cm, style={'fontSize': 6}),
                    Label(text="Telef:", top=0.1*cm, left=3*cm, style={'fontSize': 6}),
                    Label(text= encabezados[0]['titular_phone'], top= 0.1*cm , left=3.8*cm, style={'fontSize': 6}),
                    Label(text="Email:", top=0.1*cm, left=8*cm, style={'fontSize': 6}),
                    Label(text= encabezados[0]['titular_email'], top= 0.1*cm , left=8.7*cm, style={'fontSize': 6}),
                    Label(text="Fax:", top=0.1*cm, left=12.5*cm, style={'fontSize': 6}),
                    Label(text= encabezados[0]['titular_fax'], top= 0.1*cm , left=12.9*cm, style={'fontSize': 6}),       
                    
                    Label(text="Sucursal:", top=-0.5*cm, left=13.5*cm, style={'fontSize': 6}),
                    Label(text="Cuenta:", top=-0.2*cm, left=13.5*cm, style={'fontSize': 6}),
                    Label(text="CUP", top=-0.8*cm, left=14.6*cm, style={'fontSize': 6}),
                    Label(text="MLC", top=-0.8*cm, left=16.6*cm, style={'fontSize': 6}),
                    
                    Label(text= encabezados[0]['titular_sucursal_mn'], top=-0.5*cm, left=14.6*cm, style={'fontSize': 6}),
                    Label(text=encabezados[0]['titular_cuenta_mn'], top=-0.2*cm, left=14.6*cm, style={'fontSize': 6}),
                    Label(text=encabezados[0]['titular_cuenta_cuc'], top=-0.2*cm, left=16.6*cm, style={'fontSize': 6}),
                    Label(text=encabezados[0]['titular_sucursal_cuc'], top=-0.5*cm, left=16.6*cm, style={'fontSize': 6}), 
                    
                    
                    #===========================================================
                    # 
                    #===========================================================
                    
                    Label(text="Código:", top= 0.6*cm , left=0.1*cm, style={'fontSize': 6}),
                    Label(text= encabezados[0]['cliente_codigo'], top= 0.6*cm , left=1*cm, style={'fontSize': 6}),
                    
                    Label(text="Cliente:", top= 0.6*cm, left=3.6*cm, style={'fontSize': 6}),
                    Label(text= encabezados[0]['cliente_nombre'], top= 0.6*cm , width= 14*cm, left=4.5*cm, style={'fontSize': 6}),
                    
                    Label(text="Dirección:", top= 1*cm, left=0.1*cm, style={'fontSize': 6}),
                    Label(text= encabezados[0]['cliente_dir'], top= 1*cm , width= 14*cm, left=1.2*cm, style={'fontSize': 6}),
                    Label(text="Telef:", top= 1.4*cm , left=0.1*cm, style={'fontSize': 6}),
                    Label(text= encabezados[0]['cliente_phone'], top= 1.4*cm , left=1*cm, style={'fontSize': 6}),
                    Label(text="Email:", top= 1.4*cm , left=3.5*cm, style={'fontSize': 6}),
                    Label(text= encabezados[0]['cliente_email'], top= 1.4*cm , left=4.2*cm, style={'fontSize': 6}),
                    Label(text="Fax:", top=1.4*cm, left=8*cm, style={'fontSize': 6}),
                    
                    Label(text="Sucursal:", top=1*cm, left=13.5*cm, style={'fontSize': 6}),
                    Label(text="Cuenta:", top=1.3*cm, left=13.5*cm, style={'fontSize': 6}),
                    Label(text="CUP", top=0.7*cm, left=14.6*cm, style={'fontSize': 6}),
                    Label(text="MLC", top=0.7*cm, left=16.6*cm, style={'fontSize': 6}),
                    
                    Label(text= encabezados[0]['contrato_sucursal_mn'], top=1*cm, left=14.6*cm, style={'fontSize': 6}),
                    Label(text=encabezados[0]['contrato_cuenta_mn'], top=1.3*cm, left=14.6*cm, style={'fontSize': 6}),
                    Label(text=encabezados[0]['contrato_cuenta_cuc'], top=1*cm, left=16.6*cm, style={'fontSize': 6}),
                    Label(text=encabezados[0]['contrato_sucursal_cuc'], top=1.3*cm, left=16.6*cm, style={'fontSize': 6}), 
                    
                    #===========================================================
                    # 
                    #===========================================================
                    
#                        Image(left=0*cm, top=0*cm, right=0.5*cm, bottom=0.5*cm,filename=os.path.join(cur_dir, 'logo111.png'))
                    
                    Image(left=-0.3*cm, top=-0.7*cm,
                              filename=os.path.join(cur_dir, 'logo111.png')),
                    ]

                elements+=[Label(text="Código", top=2.5*cm, left=0.1*cm, style={'fontSize':6}),
                Label(text="Descripción", top=2.5*cm, left=3*cm, style={'fontSize':6}),
                Label(text="UM", top=2.5*cm, left=6.5*cm, style={'fontSize': 6}),
                Label(text="Cant.", top=2.5*cm, left=8*cm, style={'fontSize': 6}),
                Label(text="Precio CUP", top=2.5*cm, left=9.3*cm, style={'fontSize': 6}),
                Label(text="Importe CUP", top=2.5*cm, left=11.3*cm, style={'fontSize': 6}),
                Label(text="Precio MLC", top=2.5*cm, left=13.3*cm, style={'fontSize': 6}),
                Label(text="Importe MLC", top=2.5*cm, left=15.3*cm, style={'fontSize': 6}),
                ]
                height = 3+0.5*cm
                borders = {'bottom': True}
        
            class band_page_footer(ReportBand):
                height = 0.5*cm
                elements = [
                    Label(text='___________________________________________________________________________________________________________________________________________________________________', top=-3*cm, left=-0.1*cm, style={'fontSize': 6}),
                    Label(text='Despachador:', top=-2.7*cm, left=-0.1*cm, style={'fontSize': 6}),
                    Label(text='___________________________________', top=-2.8*cm, left=1.8*cm, style={'fontSize': 6}),
                    Label(text='Confeccionado:', top=-2.4*cm, left=-0.1*cm, style={'fontSize': 6}),
#                    Label(text='Confeccionado:', top=-2.4*cm, left=1*cm, style={'fontSize': 6}),
                    Label(text='___________________________________', top=-2.5*cm, left=1.8*cm, style={'fontSize': 6}),
                    Label(text='Anotado:', top=-2.1*cm, left=-0.1*cm, style={'fontSize': 6}),
                    Label(text='___________________________________', top=-2.1*cm, left=1.8*cm, style={'fontSize': 6}),
                    Label(text='Facturado:', top=-2.7*cm, left=7*cm, style={'fontSize': 6}),
                    Label(text=encabezados[0]['pk_user'], top=-2.7*cm, left=8.1*cm, style={'fontSize': 6}),
                    Label(text='Firma:', top=-2.4*cm, left=7*cm, style={'fontSize': 6}),
                    Label(text='___________________________________', top=-2.4*cm, left=8*cm, style={'fontSize': 6}),
                    Label(text= 'Confeccionada el ' + encabezados[0]['fecha_confeccionado'].strftime("%d/%m/%Y"), top=-2.7*cm, left=14.1*cm, style={'fontSize': 6}),
                    Label(text='Impresa el ' + datetime.date.today().strftime("%d/%m/%Y"), top=-2.4*cm, left=14.1*cm, style={'fontSize': 6}),
                    Label(text='Impreso por: ' + encabezados[0]['pk_user'], top=-2.1*cm, left=14.1*cm, style={'fontSize': 6}),
                    Label(text='___________________________________________________________________________________________________________________________________________________________________', top=-1.9*cm, left=-0.1*cm, style={'fontSize': 6}),
                    Label(text='Observaciones:', top=-1.6*cm, left=-0.1*cm, style={'fontSize': 6}),
                    Label(text='___________________________________________________________________________________________________________________________________________________________________', top=-1.5*cm, left=-0.1*cm, style={'fontSize': 6}),
                    Label(text='Transportador:', top=-1.2*cm, left=-0.1*cm, style={'fontSize': 6}),
                    Label(text='___________________________________', top=-1.2*cm, left=1.8*cm, style={'fontSize': 6}),
                    Label(text='CI:', top=-0.9*cm, left=-0.1*cm, style={'fontSize': 6}),
                    Label(text='___________________________________', top=-0.9*cm, left=1.8*cm, style={'fontSize': 6}),
                    Label(text='Licencia:', top=-1.2*cm, left=7*cm, style={'fontSize': 6}),
                    Label(text='___________________________________', top=-1.2*cm, left=8*cm, style={'fontSize': 6}),
                    Label(text='Chapa:', top=-0.9*cm, left=7*cm, style={'fontSize': 6}),
                    Label(text='___________________________________', top=-0.9*cm, left=8*cm, style={'fontSize': 6}),
                    Label(text='Firma:', top=-0.9*cm, left=14.1*cm, style={'fontSize': 6}),
                    Label(text='___________________________________', top=-0.9*cm, left=14.8*cm, style={'fontSize': 6}),
                    Label(text='___________________________________________________________________________________________________________________________________________________________________', top=-0.7*cm, left=-0.1*cm, style={'fontSize': 6}),
                    Label(text='Recibido:', top=-0.4*cm, left=-0.1*cm, style={'fontSize': 6}),
                    Label(text='___________________________________________________________________________________________________________________________________________________________________', top=-0.3*cm, left=-0.1*cm, style={'fontSize': 6}),
                    Label(text='Declaración de conformidad: El producto cumple con garantiza en cumplimiento de la NC 162:2009.', top=0*cm, left=-0.1*cm, style={'fontSize': 6}),
                    Label(text=' el ensayo descrito en la NCISO 7619:2005.', top=0*cm, left=5*cm, style={'fontSize': 6}),
                    Label(text='Elastómeros-Determinación de la dureza de', top=0*cm, left=9.2*cm, style={'fontSize': 6}),
                    Label(text='penetración durante un durómetro de bolsillo que', top=0*cm, left=13.4*cm, style={'fontSize': 6}),
                    Label(text=' Neumáticos Recauchados-Especificaciones. ', top=0.45*cm, left=4.3*cm, style={'fontSize': 6}),
                    ]
                
            groups = [
                 ReportGroup(
                    attribute_name='venta',
                    band_header=DetailBand(
                        height=0.6*cm,
                        elements=[
                            ObjectValue(expression='venta',top = 1.8*cm,style={'fontSize': 6})
                        ]
                    ),
                    band_footer=ReportBand(
                        height = 0.6*cm,
                        elements = [
                            Label(text='Total:',top = 1.8*cm,style={'fontName': 'Helvetica-Bold', 'fontSize': 6, 'alignment': TA_RIGHT}),
                            ObjectValue(expression='sum(importecup)',top = 1.8*cm, left=7.09*cm, style={'fontName': 'Helvetica-Bold', 'fontSize': 6, 'alignment': TA_RIGHT}),
                            ObjectValue(expression='sum(importecuc)',top = 1.8*cm, left=11.09*cm, style={'fontName': 'Helvetica-Bold', 'fontSize': 6, 'alignment': TA_RIGHT}),
                            ],
                        
                    ),
                ),
            ]
            
            class band_summary(ReportBand):
                height = 0.6*cm
                elements = [
                    Label(text='A Pagar:',top = 1.8*cm, style={'fontName': 'Helvetica-Bold', 'fontSize': 6, 'alignment': TA_RIGHT}),
                    ObjectValue(expression='sum(importecup)',top = 1.8*cm, left=7.09*cm, style={'fontName': 'Helvetica-Bold', 'fontSize': 6, 'alignment': TA_RIGHT}),
                    ObjectValue(expression='sum(importecuc)',top = 1.8*cm, left=11.09*cm, style={'fontName': 'Helvetica-Bold', 'fontSize': 6, 'alignment': TA_RIGHT}),
                    ]
        
        
        report = Report_2(queryset)
        try:
            fichero = open(pdf_file_name)
            fichero.close()
        except Exception, e:
            pass
        try:
            report.generate_by(PDFGenerator, pdf_file_name)
        except Exception, e:
            return 0
        return 2
