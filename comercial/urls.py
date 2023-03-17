from django.conf.urls.defaults import *
from comerciax.comercial.views import *
from django.views.generic import create_update

# Uncomment the next two lines to enable the admin:


urlpatterns = patterns('comerciax.comercial.views',
    
    #############################################################
    #             CONCILIACION X ORG X PROVINCIA                #
    ############################################################# 
    url(r'^rpt/concixorgprov', 'concixorgprov', name='concixorgprov'),
    url(r'^rpt/formconcixorgprov', 'formconcixorgprov', name='formconcixorgprov'),
    
    #############################################################
    #                CONCILIACION X CLIENTE                     #
    ############################################################# 
    url(r'^rpt/concixcliente', 'concixcliente', name='concixcliente'),
    url(r'^rpt/formconcixcliente', 'formconcixcliente', name='formconcixcliente'),
    
    #############################################################
    #        SERVICIO DE RECAPE A ORGANOS DE LA DEFENSA         #
    ############################################################# 
    url(r'^rpt/orgfarmin', 'recapfarmin', name='recapfarmin'),
    url(r'^rpt/formorgfarmin', 'formorgfarmin', name='formorgfarmin'),
    
    #############################################################
    #        INV Producto terminado por organismo y edades      #
    ############################################################# 
    url(r'^rpt/invptxorgedad', 'invptxorgedad', name='invptxorgedad'),
    
     
    #############################################################
    #               CIERRE DEL MES                              #
    #############################################################
    url(r'^cierre/cerrarmes$', 'cerrarmes', name='cerrarmes'),
    url(r'^cierre/balcvsrec$', 'balacvsrecap_sincierre', name='balacvsrecap_sincierre'),
    url(r'^cierre/formbalacvsrecap', 'formbalacvsrecap', name='formbalacvsrecap'),  #este es para el balance que esta en la BD
    url(r'^ajax/cerrarmescomerc/(?P<mes>[a-zA-Z0-9-]{0,40})/(?P<year>[a-zA-Z0-9-]{0,40})/', 'cerrarmescomerc',name='cerrarmescomerc'),

    #############################################################
    #                     OFERTAS                               #
    #############################################################                
    url(r'^oferta/index', 'oferta_index',name='oferta_index'),
    url(r'^oferta/add', 'oferta_add', name='ofertaadd'),
    url(r'^oferta/view/(?P<idof>[a-zA-Z0-9-]{0,40})/', 'oferta_view',name='oferta_view'),
    url(r'^ajax/oferta_del/(?P<idof>[a-zA-Z0-9-]{0,40})/$', 'oferta_del', name='oferta_del'),
    url(r'^oferta/edit/(?P<idof>[a-zA-Z0-9-]{0,40})/', 'oferta_edit',name='oferta_edit'),
    url(r'^ajax/get-ofer-list/$', 'get_ofer_list', name = 'get_ofer_list'),
#    url(r'^oferta/veroferta/(?P<idoferta>[a-zA-Z0-9-]{0,40})/', 'veroferta',name='veroferta'),
    url(r'^oferta/veroferta/(?P<idoferta>[a-zA-Z0-9-]{0,40})/(?P<haycup>\d+)/(?P<haycuc>\d+)/(?P<espdf>\d+)/', 'veroferta',name='veroferta'),
    
                 ########################
                 #      DETALLES        #
                 ########################
    
    url(r'^detalle_ofer/add/(?P<idof>[a-zA-Z0-9-]{0,40})/', 'detalleOfer_add',name='detalleOfer_add'),
    url(r'^ajax/detalle_ofer/delete/(?P<idof>[a-zA-Z0-9-]{0,40})/(?P<idcasco>[a-zA-Z0-9-]{0,40})/', 'detalleOfer_delete',name='detalleOfer_delete'),
    url(r'^ajax/detalle_ofer/delete/$', 'detalleOfer_delete',name='detalleOfer_delete2'),
    url(r'^ajax/ofertadetalle/view/(?P<idof>[a-zA-Z0-9-]{0,40})/(?P<idfa>[a-zA-Z0-9-]{0,40})/', 'ofertadetalle_view',name='ofertadetalle_view'),
    url(r'^ajax/viewdetalleoferta/$','ofertadetalle_view' , name='ofertadetalle_view2'),
    url(r'^ajax/detalle_ofer/list/(?P<idprod>[a-zA-Z0-9-]{0,40})/(?P<idof>[a-zA-Z0-9-]{0,40})/$', 'detalleOferCliente_list',name='detalleOferCliente_list'),
    url(r'^ajax/detalle_ofer/list/$', 'detalleFactCliente_list', name='detalleOferCliente_list2'),
    
    #############################################################
    #                     FACTURAS PARTICULAR                   #
    ############################################################# 
                   
    url(r'^facturapart/index', 'facturapart_index',name='facturapart_index'),
    url(r'^facturapart/add', 'facturapart_add', name='facturapartadd'),
    url(r'^facturapart/view/(?P<idfa>[a-zA-Z0-9-]{0,40})/', 'facturapart_view',name='facturapart_view'),
    url(r'^ajax/facturapart_cancelar/(?P<idfa>[a-zA-Z0-9-]{0,40})/$', 'facturapart_cancelar', name='facturapart_cancelar'),
    url(r'^facturapart/edit/(?P<idfa>[a-zA-Z0-9-]{0,40})/', 'facturapart_edit',name='facturapart_edit'),
    url(r'^ajax/get-factpart-list/$', 'get_factpart_list', name = 'get_factpart_list'),
    url(r'^ajax/obtener_particular/(?P<idcl>[a-zA-Z0-9-]{0,40})/', 'obtener_particular', name = 'obtener_particular'),
    url(r'^ajax/obtener_particular/$', 'obtener_particular', name = 'obtener_particular2'),
    url(r'^oferta/verfacturapart/(?P<idfactura>[a-zA-Z0-9-]{0,40})/(?P<haycup>\d+)/(?P<haycuc>\d+)/(?P<cantcascos>\d+)/', 'verfacturapart',name='verfacturapart'),
    
    url(r'^ajax/facturapart_del/(?P<idfa>[a-zA-Z0-9-]{0,40})/$', 'facturapart_del', name='facturapart_del'),
    url(r'^facturapart/imprimir/(?P<idfa>[a-zA-Z0-9-]{0,40})/', 'facturapart_imprimir',name='facturapart_imprimir'),
    #url(r'^ajax/factura_confirmar/(?P<idfa>[a-zA-Z0-9-]{0,40})/(?P<impcuc>[$0-9-.]{0,10})/(?P<impcup>[$0-9-.]{0,10})/$', 'factura_confirmar', name='factura_confirmar'),
    url(r'^ajax/facturapart_confirmar/(?P<idfa>[a-zA-Z0-9-]{0,40})/$', 'facturapart_confirmar', name='facturapart_confirmar'),

            ########################
            #      DETALLES        #
            ########################
    
    url(r'^detalle_facturapart/add/(?P<idfa>[a-zA-Z0-9-]{0,40})/', 'detalleFacturapart_add',name='detalleFacturapart_add'),

    url(r'^ajax/detalle_facturapart/delete/(?P<idfa>[a-zA-Z0-9-]{0,40})/(?P<idcasco>[a-zA-Z0-9-]{0,40})/', 'detalleFacturapart_delete',name='detalleFacturapart_delete'),
    
    url(r'^ajax/detalle_facturapart/delete/$', 'detalleFacturapart_delete',name='detalleFacturapart_delete2'),
    
    url(r'^ajax/detalle_facturapart/list/(?P<idfa>[a-zA-Z0-9-]{0,40})/$', 'detalle_facturapart_list',name='detalle_facturapart_list'),
    url(r'^ajax/detalle_facturapart/list/$', 'detalle_facturapart_list', name='detalle_facturapart_list2'),    
    
    url(r'^detalle_facturapart/edit/(?P<idfa>[a-zA-Z0-9-]{0,40})/(?P<idcasco>[a-zA-Z0-9-]{0,40})/', 'detalleFacturaPart_edit',name='detalleFacturaPart_edit'),
    
    url(r'^detalle_facturapart/edit/$', 'detalleFacturaPart_edit',name='detalleFacturaPart_edit2'),
   #############################################################
   #                     FACTURAS EXT                          #
   ############################################################# 
                   
    url(r'^facturaext/index', 'facturaext_index',name='facturaext_index'),
    url(r'^facturaext/add', 'facturaext_add', name='facturaextadd'),
    url(r'^facturaext/view/(?P<idfa>[a-zA-Z0-9-]{0,40})/', 'facturaext_view',name='facturaext_view'),
    url(r'^ajax/facturaext_cancelar/(?P<idfa>[a-zA-Z0-9-]{0,40})/$', 'facturaext_cancelar', name='facturaext_cancelar'),
    url(r'^facturaext/edit/(?P<idfa>[a-zA-Z0-9-]{0,40})/', 'facturaext_edit',name='facturaext_edit'),
    url(r'^ajax/get-factext-list/$', 'get_factext_list', name = 'get_factext_list'),
    
    url(r'^ajax/facturaext_del/(?P<idfa>[a-zA-Z0-9-]{0,40})/$', 'facturaext_del', name='facturaext_del'),
    #url(r'^ajax/factura_confirmar/(?P<idfa>[a-zA-Z0-9-]{0,40})/(?P<impcuc>[$0-9-.]{0,10})/(?P<impcup>[$0-9-.]{0,10})/$', 'factura_confirmar', name='factura_confirmar'),
    url(r'^ajax/facturaext_confirmar/(?P<idfa>[a-zA-Z0-9-]{0,40})/$', 'facturaext_confirmar', name='facturaext_confirmar'),
    
    #############################################################
    #                     FACTURAS                               #
    ############################################################# 
                   
    url(r'^factura/index', 'factura_index',name='factura_index'),
    url(r'^factura/add', 'factura_add', name='facturaadd'),
    url(r'^factura/view/(?P<idfa>[a-zA-Z0-9-]{0,40})/', 'factura_view',name='factura_view'),
    url(r'^ajax/factura_cancelar/(?P<idfa>[a-zA-Z0-9-]{0,40})/$', 'factura_cancelar', name='factura_cancelar'),
    url(r'^factura/edit/(?P<idfa>[a-zA-Z0-9-]{0,40})/', 'factura_edit',name='factura_edit'),
    url(r'^ajax/get-fact-list/$', 'get_fact_list', name = 'get_fact_list'),
    url(r'^ajax/obtener_transp/(?P<idcl>[a-zA-Z0-9-]{0,40})/', 'obtener_transp', name = 'obtener_transp'),
    url(r'^ajax/obtener_transp/$', 'obtener_transp', name = 'obtener_transp2'),
    url(r'^oferta/verfactura/(?P<idfactura>[a-zA-Z0-9-]{0,40})/(?P<haycup>\d+)/(?P<haycuc>\d+)/(?P<cantcascos>\d+)/', 'verfactura',name='verfactura'),
    
    url(r'^ajax/factura_del/(?P<idfa>[a-zA-Z0-9-]{0,40})/$', 'factura_del', name='factura_del'),
    url(r'^factura/imprimir/(?P<idfa>[a-zA-Z0-9-]{0,40})/', 'factura_imprimir',name='factura_imprimir'),
    #url(r'^ajax/factura_confirmar/(?P<idfa>[a-zA-Z0-9-]{0,40})/(?P<impcuc>[$0-9-.]{0,10})/(?P<impcup>[$0-9-.]{0,10})/$', 'factura_confirmar', name='factura_confirmar'),
    url(r'^ajax/factura_confirmar/(?P<idfa>[a-zA-Z0-9-]{0,40})/$', 'factura_confirmar', name='factura_confirmar'),
                 ########################
                 #      DETALLES        #
                 ########################
    
    url(r'^detalle_factura/add/(?P<idfa>[a-zA-Z0-9-]{0,40})/', 'detalleFactura_add',name='detalleFactura_add'),
    url(r'detalle_factura/addofer/(?P<idfa>[a-zA-Z0-9-]{0,40})/', 'detalleFactura_addofer',name='detalleFactura_addofer'),
    url(r'^ajax/ofertadetalle_view/(?P<idof>[a-zA-Z0-9-]{0,40})/','ofertadetalle_view' , name='ofertadetalle_view'),

    url(r'^ajax/detalle_factura/delete/(?P<idfa>[a-zA-Z0-9-]{0,40})/(?P<idcasco>[a-zA-Z0-9-]{0,40})/', 'detalleFactura_delete',name='detalleFactura_delete'),
    
    url(r'^ajax/detalle_factura/delete/$', 'detalleFactura_delete',name='detalleFactura_delete2'),
    
    url(r'^ajax/detalle_factura/list/(?P<idfa>[a-zA-Z0-9-]{0,40})/$', 'detalle_factura_list',name='detalle_factura_list'),
    url(r'^ajax/detalle_factura/list/$', 'detalle_factura_list', name='detalle_factura_list2'),
    
    url(r'^detalle_factura/edit/(?P<idfa>[a-zA-Z0-9-]{0,40})/(?P<idcasco>[a-zA-Z0-9-]{0,40})/', 'detalleFactura_edit',name='detalleFactura_edit'),
    
    url(r'^detalle_factura/edit/$', 'detalleFactura_edit',name='detalleFactura_edit2'),
    
    url(r'^ajax/detalle_factura/list/(?P<idprod>[a-zA-Z0-9-]{0,40})/(?P<idfa>[a-zA-Z0-9-]{0,40})/$', 'detalleFactCliente_list',name='detalleFactCliente_list'),
    url(r'^ajax/detalle_factura/list/$', 'detalleFactCliente_list', name='detalleFactCliente_list2'),
    
    url(r'^ajax/detalle_facturapart/list/(?P<idprod>[a-zA-Z0-9-]{0,40})/(?P<idfa>[a-zA-Z0-9-]{0,40})/$', 'detalleFactPart_list',name='detalleFactPart_list'),
    url(r'^ajax/detalle_facturapart/list/$', 'detalleFactPart_list', name='detalleFactPart_list2'),
    
#   #############################################################
    #                     PAGOS EFECTIVO Entidades               #
    ############################################################# 
                   
    url(r'^pagoefect/index', 'pagoefect_index',name='pagoefect_index'),
    url(r'^pagoefect/add', 'pagoefect_add', name='pagoefectadd'),
    url(r'^pagoefect/view/(?P<idpa>[a-zA-Z0-9-]{0,40})/', 'pagoefect_view',name='pagoefect_view'),
    url(r'^pagoefect/view/$', 'pagoefect_view', name='pagoefect_view2'),
    url(r'^pagoefect/edit/(?P<idpa>[a-zA-Z0-9-]{0,40})/', 'pagoefect_edit',name='pagoefect_edit'),
    url(r'^ajax/get-pagoefect-list/$', 'get_pagoefect_list', name = 'get_pagoefect_list'),
    
    url(r'^ajax/pagoefect_del/(?P<idpa>[a-zA-Z0-9-]{0,40})/$', 'pagoefect_del', name='pagoefect_del'),
    
                 ########################
                 #      DETALLES        #
                 ########################
    
    url(r'^detalle_pago/add/(?P<idpa>[a-zA-Z0-9-]{0,40})/', 'detallePago_add',name='detallePago_add'),
     url(r'^ajax/detalle_pago/delete/(?P<idpa>[a-zA-Z0-9-]{0,40})/(?P<idpag>[a-zA-Z0-9-]{0,40})/', 'detallePago_delete',name='detallePago_delete'),
    
    url(r'^ajax/detalle_pago/delete/$', 'detallePago_delete',name='detallePago_delete2'),
    
#     #############################################################
    #                     PAGOS EFECTIVO PARTICULARES               #
    ############################################################# 
                   
    url(r'^pagoefectpart/index', 'pagoefectpart_index',name='pagoefectpart_index'),
    url(r'^pagoefectpart/add', 'pagoefectpart_add', name='pagoefectpartadd'),
    url(r'^pagoefectpart/view/(?P<idpa>[a-zA-Z0-9-]{0,40})/', 'pagoefectpart_view',name='pagoefectpart_view'),
    url(r'^pagoefectpart/view/$', 'pagoefectpart_view', name='pagoefectpart_view2'),
    url(r'^pagoefectpart/edit/(?P<idpa>[a-zA-Z0-9-]{0,40})/', 'pagoefectpart_edit',name='pagoefectpart_edit'),
    url(r'^ajax/get-pagoefectpart-list/$', 'get_pagoefectpart_list', name = 'get_pagoefectpart_list'),
    
    url(r'^ajax/pagoefectpart_del/(?P<idpa>[a-zA-Z0-9-]{0,40})/$', 'pagoefectpart_del', name='pagoefectpart_del'),
    
                 ########################
                 #      DETALLES        #
                 ########################
    
    url(r'^detalle_pagopart/add/(?P<idpa>[a-zA-Z0-9-]{0,40})/', 'detallePagopart_add',name='detallePagopart_add'),
     url(r'^ajax/detalle_pagopart/delete/(?P<idpa>[a-zA-Z0-9-]{0,40})/(?P<idpag>[a-zA-Z0-9-]{0,40})/', 'detallePagopart_delete',name='detallePagopart_delete'),
    
    url(r'^ajax/detalle_pagopart/delete/$', 'detallePagopart_delete',name='detallePagopart_delete2'),    
    
    #############################################################
    #                     PAGOS OTROS                          #
    ############################################################# 
                   
    url(r'^pagootros/add', 'pagootros_add', name='pagootrosadd'),
    url(r'^pagootros/view/(?P<idpa>[a-zA-Z0-9-]{0,40})/', 'pagootros_view',name='pagootros_view'),
    url(r'^pagootros/view/$', 'pagootros_view',name='pagootros_view2'),
    url(r'^pagootros/edit/(?P<idpa>[a-zA-Z0-9-]{0,40})/', 'pagootros_edit',name='pagootros_edit'),
    
    #url(r'^ajax/pagootros_del/(?P<idpa>[a-zA-Z0-9-]{0,40})/$', 'pagootros_del', name='pagootros_del'),

                 ########################
                 #      DETALLES        #
                 ########################
    
    url(r'^detalle_pagootro/add/(?P<idpa>[a-zA-Z0-9-]{0,40})/', 'detallePagootro_add',name='detallePagootro_add'),
    
    #############################################################
    #                     REGISTRO DE CLIENTES                   #
    #############################################################   
    url(r'^regcontratos', 'regcontratos', name='regcontratos'), 
    
    #===========================================================================
    #   CONTRATOS POR FECHA DE VENCIMIENTO
    #===========================================================================
    url(r'^contratosvencimiento', 'contratosvencimiento', name='contratosvencimiento'),
    
    #############################################################
    #                        CASCOS X CLIENTES                  #
    #############################################################   
    url(r'^cascosxcliente', 'cascosxcliente', name='cascosxcliente'), 
    
    #############################################################
    #                        TRAZABILIDAD DE CASCOS             #
    #############################################################   
    url(r'^cascostraza', 'cascostraza', name='cascostraza'), 

    #############################################################
    #              CASCOS PARA LA VENTA                         #
    #############################################################   
    url(r'^cascosventa', 'cascosventa', name='cascosventa'), 
    
    #############################################################
    #              CASCOS POR ESTADO                            #
    #############################################################   
    url(r'^cascosestado', 'cascosestado', name='cascosestado'), 
    
    #############################################################
    #              CASCOS PT POR EDAD                           #
    #############################################################   
    url(r'^cascosptedad', 'cascosptedad', name='cascosptedad'), 
    
    #############################################################
    #              CASCOS PT POR EDAD                           #
    #############################################################   
    url(r'^cascosptcantidad', 'cascosptcantidad', name='cascosptcantidad'), 
    
    #############################################################
    #                      PLAZOS EN FABRICA                 #
    #############################################################   
    url(r'^plazoscasco', 'plazoscasco', name='plazoscasco'), 
    url(r'^plazosfabricaall_pdf/', 'plazosfabricaall_pdf', name='plazosfabricaall_pdf'),  
    #############################################################
    #              TRANSFERENCIAS ENVIADAS                          #
    #############################################################   
    url(r'^transfenviadas', 'transfenviadas', name='transfenviadas'), 
    #############################################################
    #              REGISTRO DE FACTURAS                         #
    #############################################################   
    url(r'^regfacturas', 'regfacturas', name='regfacturas'), 
    #############################################################
    #              FACTURAS X CLIENTES                          #
    #############################################################   
    url(r'^factcliente', 'factcliente', name='factcliente'), 

    #############################################################
    #              FACTURAS X COBRAR                            #
    #############################################################   
    url(r'^factcobrar', 'factcobrar', name='factcobrar'),
    
    
    #############################################################
    #              REGISTRO DE COBROS                           #
    #############################################################   
    url(r'^regcobros', 'regcobros', name='regcobros'),
    
    #############################################################
    #              VENTAS DE DECOMISOS                           #
    #############################################################  
    url(r'^ventas_decomiso', 'ventas_decomiso', name='ventas_decomiso'),
    
    
    url(r'^invfisicoall_pdf/', 'invfisicoall_pdf', name='invfisicoall_pdf'),
    
    url(r'^ajax/verificaemail/list/', 'verificaemail',name='verificaemail'),
    url(r'^ajax/verificaemail/list/$', 'verificaemail', name='verificaemail2'),
    
    #===========================================================================
    # MOVIMIENTO DE CASCOS
    #===========================================================================
    url(r'^movcascos', 'movcascos', name='movcascos'),
    
    #===========================================================================
    # REPORTE DE PLANES
    #===========================================================================
    url(r'^repplanes', 'repplanes', name='repplanes'),
    
    #===========================================================================
    # REPORTE DE CUMPLIM. DEL PLAN
    #===========================================================================
    url(r'^repcumpplanes', 'repcumpplanes', name='repcumpplanes'),
    
    #===========================================================================
    # CONCILIACION
    #===========================================================================
     url(r'^conciliacion', 'conciliacion', name='conciliacion'), 
     
    #===========================================================================
    # SERVICIOS A CLIENTES
    #===========================================================================
     url(r'^servclient', 'servclient', name='servclient'), 
)
