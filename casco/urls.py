from django.conf.urls.defaults import *
from comerciax.casco.views import *
from django.views.generic import create_update

# Uncomment the next two lines to enable the admin:




urlpatterns = patterns('comerciax.casco.views',

                         
    #############################################################
    #               INVENTARIO                                  #
    #############################################################                
    #url(r'^inventario/index', 'invcierre', name='inventario'),
    
    url(r'^inventario/invf/', 'invfisicoall', name='invfall'),
    url(r'^inventario/balcvsrec', 'balacvsrecap', name='balcvsrec'),
    
    url(r'^inventario/almc', 'invcierrealmc', name='almc'),
    url(r'^inventario/almp', 'invcierrealmp', name='almp'),
    url(r'^inventario/cerrarmp', 'cerrar_mesalmprod', name='cerrar_mesalmprod'),
    url(r'^inventario/cerrarmc', 'cerrar_mesalmcasco', name='cerrar_mesalmcasco'),
    url(r'^ajax/repotclientemio/$', 'reportclientemio', name='reportclientemio'),
                    # ALMACEN DE CASCO #
    url(r'^inventario/cerraralmc', 'cerrar_mes_almc', name='cerrar_mes_almc'),
    url(r'^ajax/datoscierrealmc/$', 'datoscierrealmc', name='datoscierrealmc'),

    #############################################################
    #               RECEPCION CLIENTE                           #
    #############################################################                
    url(r'^recepcioncliente/index', 'recepcioncliente_index',name='rc_index'),
    url(r'^recepcioncliente/add', 'recepcioncliente_add', name='recepcionclienteadd'),
    url(r'^recepcioncliente/view/(?P<idrc>[a-zA-Z0-9-]{0,40})/', 'recepcioncliente_view',name='rc_view'),
    url(r'^ajax/recepcioncliente_del/(?P<idrc>[a-zA-Z0-9-]{0,40})/$', 'recepcioncliente_del', name='recepcioncliente_del'),
    url(r'^recepcioncliente/edit/(?P<idrc>[a-zA-Z0-9-]{0,40})/', 'recepcioncliente_edit',name='rc_edit'),
    url(r'^ajax/get-rc-list/$', 'get_rc_list', name = 'get_rc_list'),
    
    url(r'^ajax/obtenercontrato/list/(?P<idcliente>[a-zA-Z0-9-]{0,40})/(?P<fecha>[a-zA-Z0-9-]{0,40})', 'obtenercontrato_list',name='obtenercontrato_list'),
    url(r'^ajax/obtenercontrato/list/$', 'obtenercontrato_list', name='obtenercontrato_list2'),
    
    url(r'^ajax/tienecontrato/list/(?P<idcliente>[a-zA-Z0-9-]{0,40})/(?P<fecha>[a-zA-Z0-9-]{0,40})', 'tiene_cuentas_por_cobrar',name='tiene_cuentas_por_cobrar'),
    url(r'^ajax/tienecontrato/list/$', 'tiene_cuentas_por_cobrar', name='tienecontrato_list2'),
    
    url(r'^ajax/obtenerclientes/list/(?P<idorganismo>[a-zA-Z0-9-]{0,40})/(?P<idprovincia>[a-zA-Z0-9-]{0,40})/(?P<tipocliente>[a-zA-Z0-9-]{0,40})/', 'obtenerclientes_list',name='obtenerclientes_list'),
    url(r'^ajax/obtenerclientes/list/$', 'obtenerclientes_list', name='obtenerclientes_list2'),
    
                 ########################
                 #      DETALLES        #
                 ########################
    
    url(r'^detalle_rc/add/(?P<idrc>[a-zA-Z0-9-]{0,40})/', 'detalleRC_add',name='detalleRC_add'),
    url(r'^ajax/detalle_rc/delete/(?P<idcasco>[a-zA-Z0-9-]{0,40})/(?P<idrc>[a-zA-Z0-9-]{0,40})/', 'detalleRC_delete',name='detalleRC_delete'),
    url(r'^detalle_rc/edit/(?P<idcasco>[a-zA-Z0-9-]{0,40})/(?P<idrc>[a-zA-Z0-9-]{0,40})/', 'detalleRC_edit',name='detalleRC_edit'),
    
    url(r'^ajax/detalle_rc/delete/$', 'detalleRC_delete',name='detalleRC_delete2'),
    url(r'^detalle_rc/edit/$', 'detalleRC_edit',name='detalleRC_edit2'),
    
    #===========================================================================
    # RECEPCION A PARTICULARES
    #===========================================================================
    url(r'^recepcionparticulares/index', 'recepcionparticulares_index',name='rp_index'),
    url(r'^recepcionparticulares/add', 'recepcionparticulares_add', name='recepcionparticularesadd'),
    url(r'^ajax/get-rp-list/$', 'get_rp_list', name = 'get_rp_list'),
    url(r'^recepcionparticulares/view/(?P<idrp>[a-zA-Z0-9-]{0,40})/', 'recepcionparticulares_view',name='rp_view'),
    url(r'^recepcionparticulares/edit/(?P<idrp>[a-zA-Z0-9-]{0,40})/', 'recepcionparticulares_edit',name='rp_edit'),
    url(r'^ajax/recepcionparticular_del/(?P<idrp>[a-zA-Z0-9-]{0,40})/$', 'recepcionparticular_del', name='recepcionparticular_del'),
    
                 ########################
                 #      DETALLES        #
                 ########################
    
    url(r'^detalle_rp/add/(?P<idrp>[a-zA-Z0-9-]{0,40})/', 'detalleRP_add',name='detalleRP_add'),
    url(r'^ajax/detalle_rp/delete/(?P<idcasco>[a-zA-Z0-9-]{0,40})/(?P<idrp>[a-zA-Z0-9-]{0,40})/', 'detalleRP_delete',name='detalleRP_delete'),
    url(r'^detalle_rp/edit/(?P<idcasco>[a-zA-Z0-9-]{0,40})/(?P<idrp>[a-zA-Z0-9-]{0,40})/', 'detalleRP_edit',name='detalleRP_edit'),
    
    url(r'^ajax/detalle_rp/delete/$', 'detalleRP_delete',name='detalleRP_delete2'),
    url(r'^detalle_rp/edit/$', 'detalleRP_edit',name='detalleRP_edit2'), 
    url(r'^ajax/detalle_rp/delete/$', 'detalleRP_delete',name='detalleRP_delete2'),   
    
    #############################################################
    #               RECEPCION CLIENTE EXTERNO                   #
    #############################################################                
    url(r'^recepcionclienteext/index', 'recepcionclienteext_index',name='rcext_index'),
    url(r'^recepcionclienteext/add', 'recepcionclienteext_add', name='recepcionclienteextadd'),
    url(r'^recepcionclienteext/view/(?P<idrc>[a-zA-Z0-9-]{0,40})/', 'recepcionclienteext_view',name='recepcionclienteext_view'),
    url(r'^ajax/recepcionclienteext_del/(?P<idrc>[a-zA-Z0-9-]{0,40})/$', 'recepcionclienteext_del', name='recepcionclienteext_del'),
    url(r'^recepcionclienteext/edit/(?P<idrc>[a-zA-Z0-9-]{0,40})/', 'recepcionclienteext_edit',name='rcext_edit'),
    url(r'^ajax/get-rcext-list/$', 'get_rcext_list', name = 'get_rcext_list'),

                ########################
                #      DETALLES        #
                ########################
    
    url(r'^detalleext_rc/add/(?P<idrc>[a-zA-Z0-9-]{0,40})/', 'detalleRCext_add',name='detalleRCext_add'),
    url(r'^ajax/detalleext_rc/delete/(?P<idcasco>[a-zA-Z0-9-]{0,40})/(?P<idrc>[a-zA-Z0-9-]{0,40})/', 'detalleRCext_delete',name='detalleRCext_delete'),
    url(r'^detalle_rcext/edit/(?P<idrc>[a-zA-Z0-9-]{0,40})/(?P<idcasco>[a-zA-Z0-9-]{0,40})/', 'detalleRCext_edit',name='detalleRCext_edit'),
     url(r'^ajax/detalleext_rc/delete/$', 'detalleRCext_delete',name='detalleRCext_delete2'),
    url(r'^detalle_rcext/edit/$', 'detalleRCext_edit',name='detalleRCext_edit2'),
    
     #############################################################
    #               ENTREGA DE VULCA A PRODUCCION                #
    #############################################################
    url(r'^cascovp/index', 'cascovp_index',name='cascovp_index'),
    url(r'^cascovp/add', 'cascovp_add', name='cascovp_add'),
    url(r'^cascovp/edit/(?P<idvp>[a-zA-Z0-9-]{0,40})/', 'cascovp_edit',name='cascovp_edit'),
    url(r'^cascovp/view/(?P<idvp>[a-zA-Z0-9-]{0,40})/', 'cascovp_view',name='cascovp_view'),
    url(r'^ajax/cascovp_del/(?P<idvp>[a-zA-Z0-9-]{0,40})/$', 'cascovp_del', name='cascovp_del'),
    url(r'^ajax/get-vp-list/$', 'get_vp_list', name = 'get_vp_list'),
   
                 ########################
                 #      DETALLES        #
                 ########################
    url(r'^detalle_vp/add/(?P<idvp>[a-zA-Z0-9-]{0,40})/', 'detalleVP_add',name='detalleVP_add'),
    url(r'^ajax/detalle_vp/delete/(?P<idvp>[a-zA-Z0-9-]{0,40})/(?P<idcasco>[a-zA-Z0-9-]{0,40})/', 'detalleVP_delete',name='detalleVP_delete'),
    url(r'^ajax/detalle_vp/delete/$', 'detalleVP_delete', name='detalleVP_delete2'),
    
    #############################################################
    #               ENTREGA DE CASCO A PRODUCCION               #
    #############################################################
    url(r'^cascocc/index', 'cascocc_index',name='cascocc_index'),
    url(r'^cascocc/add', 'cascocc_add', name='cascocc_add'),
    url(r'^cascocc/edit/(?P<idcp>[a-zA-Z0-9-]{0,40})/', 'cascocc_edit',name='cascocc_edit'),
    url(r'^cascocc/view/(?P<idcp>[a-zA-Z0-9-]{0,40})/', 'cascocc_view',name='cascocc_view'),
    url(r'^ajax/cascocc_del/(?P<idcp>[a-zA-Z0-9-]{0,40})/$', 'cascocc_del', name='cascocc_del'),
    url(r'^ajax/get-cc-list/$', 'get_cc_list', name = 'get_cc_list'),
   
                 ########################
                 #      DETALLES        #
                 ########################
                 
    url(r'^detalle_cc/add/(?P<idcp>[a-zA-Z0-9-]{0,40})/', 'detalleCC_add',name='detalleCC_add'),
    url(r'^ajax/detalle_cc/delete/(?P<idcp>[a-zA-Z0-9-]{0,40})/(?P<idcasco>[a-zA-Z0-9-]{0,40})/', 'detalleCC_delete',name='detalleCC_delete'),
    url(r'^ajax/detalle_cc/delete/$', 'detalleCC_delete', name='detalleCC_delete2'),
    url(r'^ajax/detalle_cc/list/(?P<idprod>[a-zA-Z0-9-]{0,40})/(?P<estado>[a-zA-Z0-9-]{0,40})/(?P<ocioso>[a-zA-Z0-9-]{0,40})/$', 'detalleCC_list',name='detalleCC_list'),
    url(r'^ajax/detalle_cc/list/$', 'detalleCC_list', name='detalleCC_list2'),
    url(r'^ajax/detalle_transf/list/(?P<idprod>[a-zA-Z0-9-]{0,40})/(?P<estado>[a-zA-Z0-9-]{0,40})/(?P<clienteext>[a-zA-Z0-9-]{0,40})/$', 'detalleTrans_list',name='detalleTrans_list'),
    url(r'^ajax/detalle_transf/list/$', 'detalleTrans_list', name='detalleTrans_list2'),  
    url(r'^ajax/detalle_dev/list/(?P<idprod>[a-zA-Z0-9-]{0,40})/(?P<estado>[a-zA-Z0-9-]{0,40})/(?P<idcliente>[a-zA-Z0-9-]{0,40})/$', 'detalleDev_list',name='detalleDev_list'),
    url(r'^ajax/detalle_dev/list/$', 'detalleDev_list', name='detalleDev_list2'),  
    
    #############################################################
    #       ENTREGA DE CASCO DE PRODUCCION A INSERVIBLE         #
    #############################################################
    url(r'^cascodip/index', 'cascodip_index',name='cascodip_index'),
    url(r'^cascodip/add', 'cascodip_add', name='cascodip_add'),
    url(r'^cascodip/edit/(?P<iddip>[a-zA-Z0-9-]{0,40})/', 'cascodip_edit',name='cascodip_edit'),
    url(r'^cascodip/view/(?P<iddip>[a-zA-Z0-9-]{0,40})/', 'cascodip_view',name='cascodip_view'),
    url(r'^ajax/cascodip_del/(?P<iddip>[a-zA-Z0-9-]{0,40})/$', 'cascodip_del', name='cascodip_del'),
    url(r'^ajax/get-dip-list/$', 'get_dip_list', name = 'get_dip_list'),
    
                 ########################
                 #      DETALLES        #
                 ########################
                 
    url(r'^detalle_dip/add/(?P<iddip>[a-zA-Z0-9-]{0,40})/', 'detalleDIP_add',name='detalleDIP_add'),
    url(r'^ajax/detalle_dip/delete/(?P<iddip>[a-zA-Z0-9-]{0,40})/(?P<idcasco>[a-zA-Z0-9-]{0,40})/', 'detalleDIP_delete',name='detalleDIP_delete'),
    url(r'^detalle_dip/edit/(?P<iddip>[a-zA-Z0-9-]{0,40})/(?P<idcasco>[a-zA-Z0-9-]{0,40})/', 'detalleDIP_edit',name='detalleDIP_edit'),
    
    url(r'^ajax/detalle_dip/delete/$', 'detalleDIP_delete',name='detalleDIP_delete2'),
    url(r'^detalle_dip/edit/$', 'detalleDIP_edit',name='detalleDIP_edit2'),

    #############################################################
    #       ENTREGA DE CASCO DE PRODUCCION A VULCA              #
    #############################################################
    
    url(r'^cascodvp/index', 'cascodvp_index',name='cascodvp_index'),
    url(r'^cascodvp/add', 'cascodvp_add', name='cascodvp_add'),
    url(r'^cascodvp/edit/(?P<iddvp>[a-zA-Z0-9-]{0,40})/', 'cascodvp_edit',name='cascodvp_edit'),
    url(r'^cascodvp/view/(?P<iddvp>[a-zA-Z0-9-]{0,40})/', 'cascodvp_view',name='cascodvp_view'),
    url(r'^ajax/cascodvp_del/(?P<iddvp>[a-zA-Z0-9-]{0,40})/$', 'cascodvp_del', name='cascodvp_del'),
    url(r'^ajax/get-dvp-list/$', 'get_dvp_list', name = 'get_dvp_list'),
                 ########################
                 #      DETALLES        #
                 ########################
    url(r'^detalle_dvp/add/(?P<iddvp>[a-zA-Z0-9-]{0,40})/', 'detalleDVP_add',name='detalleDVP_add'),
    url(r'^ajax/detalle_dvp/delete/(?P<iddvp>[a-zA-Z0-9-]{0,40})/(?P<idcasco>[a-zA-Z0-9-]{0,40})/', 'detalleDVP_delete',name='detalleDVP_delete'),
        
    url(r'^ajax/detalle_dvp/delete/$', 'detalleDVP_delete',name='detalleDVP_delete2'),
    
    #############################################################
    #               TRANSFERENCIA DE CASCO A ENTIDADES EXT      #
    #############################################################                
    url(r'^trans/index', 'trans_index',name='tc_index'),
    url(r'^trans/add', 'trans_add', name='transadd'),
    url(r'^trans/view/(?P<idtc>[a-zA-Z0-9-]{0,40})/', 'trans_view',name='tc_view'),
    url(r'^ajax/trans_del/(?P<idtc>[a-zA-Z0-9-]{0,40})/$', 'trans_del', name='trans_del'),
    url(r'^trans/edit/(?P<idtc>[a-zA-Z0-9-]{0,40})/', 'trans_edit',name='tc_edit'),
    url(r'^ajax/get-tc-list/$', 'get_tc_list', name = 'get_tc_list'),
    
                 ########################
                 #      DETALLES        #
                 ########################
    
    url(r'^detalle_tc/add/(?P<idtc>[a-zA-Z0-9-]{0,40})/', 'detalleTC_add',name='detalleTC_add'),
    url(r'^ajax/detalle_tc/delete/(?P<idtc>[a-zA-Z0-9-]{0,40})/(?P<idcasco>[a-zA-Z0-9-]{0,40})/', 'detalleTC_delete',name='detalleTC_delete'),
    
    url(r'^ajax/detalle_tc/delete/$', 'detalleTC_delete',name='detalleTC_delete2'),

    #############################################################
    #       RECHAZAR CASCSO POR ERROR EN REVISION               #
    #############################################################
    url(r'^cascoer/index', 'cascoer_index',name='cascoer_index'),
    url(r'^cascoer/add', 'cascoer_add', name='cascoer_add'),
    url(r'^cascoer/view/(?P<ider>[a-zA-Z0-9-]{0,40})/', 'cascoer_view',name='cascoer_view'),
    url(r'^cascoer/edit/(?P<ider>[a-zA-Z0-9-]{0,40})/', 'cascoer_edit',name='cascoer_edit'),
    url(r'^ajax/cascoer_del/(?P<ider>[a-zA-Z0-9-]{0,40})/$', 'cascoer_del', name='cascoer_del'),
    url(r'^ajax/get-er-list/$', 'get_er_list', name = 'get_er_list'),
                 ########################
                 #      DETALLES        #
                 ########################
    url(r'^detalle_er/add/(?P<ider>[a-zA-Z0-9-]{0,40})/', 'detalleER_add',name='detalleER_add'),
    url(r'^ajax/detalle_er/delete/(?P<ider>[a-zA-Z0-9-]{0,40})/(?P<idcasco>[a-zA-Z0-9-]{0,40})/', 'detalleER_delete',name='detalleER_delete'),
    url(r'^detalle_er/edit/(?P<ider>[a-zA-Z0-9-]{0,40})/(?P<idcasco>[a-zA-Z0-9-]{0,40})/', 'detalleER_edit',name='detalleER_edit'),
    
    url(r'^ajax/detalle_er/delete/$', 'detalleER_delete',name='detalleER_delete2'),
    url(r'^detalle_er/edit/$', 'detalleER_edit',name='detalleER_edit2'),

    #############################################################
    #               ENTREGA DE CASCOS RECHAZADOS                #
    #############################################################
    url(r'^cascocr/index', 'cascocr_index',name='cascocr_index'),
    url(r'^cascocr/add', 'cascocr_add', name='cascocr_add'),
    url(r'^cascocr/edit/(?P<idcr>[a-zA-Z0-9-]{0,40})/', 'cascocr_edit',name='cascocr_edit'),
    url(r'^cascocr/view/(?P<idcr>[a-zA-Z0-9-]{0,40})/', 'cascocr_view',name='cascocr_view'),
    url(r'^ajax/cascocr_del/(?P<idcr>[a-zA-Z0-9-]{0,40})/$', 'cascocr_del', name='cascocr_del'),
    url(r'^ajax/get-cr-list/$', 'get_cr_list', name = 'get_cr_list'),
   
                 ########################
                 #      DETALLES        #
                 ########################
    url(r'^detalle_cr/add/(?P<idcr>[a-zA-Z0-9-]{0,40})/', 'detalleCR_add',name='detalleCR_add'),
    url(r'^ajax/detalle_cr/delete/(?P<idcr>[a-zA-Z0-9-]{0,40})/(?P<idcasco>[a-zA-Z0-9-]{0,40})/', 'detalleCR_delete',name='detalleCR_delete'),
    url(r'^ajax/detalle_cr/delete/$', 'detalleCR_delete', name='detalleCR_delete2'),

    #############################################################
    #              DEVOLUCION DE CASCOS                         #
    #############################################################
    url(r'^cascodcc/index', 'cascodcc_index',name='cascodcc_index'),
    url(r'^cascodcc/add', 'cascodcc_add', name='cascodcc_add'),
    url(r'^cascodcc/edit/(?P<iddcc>[a-zA-Z0-9-]{0,40})/', 'cascodcc_edit',name='cascodcc_edit'),
    url(r'^cascodcc/view/(?P<iddcc>[a-zA-Z0-9-]{0,40})/', 'cascodcc_view',name='cascodcc_view'),
    url(r'^ajax/cascodcc_del/(?P<iddcc>[a-zA-Z0-9-]{0,40})/$', 'cascodcc_del', name='cascodcc_del'),
    url(r'^ajax/get-dcc-list/$', 'get_dcc_list', name = 'get_dcc_list'),
   
                 ########################
                 #      DETALLES        #
                 ########################
    url(r'^detalle_dcc/add/(?P<iddcc>[a-zA-Z0-9-]{0,40})/(?P<idcliente>[a-zA-Z0-9-]{0,40})/', 'detalleDCC_add',name='detalleDCC_add'),
    url(r'^ajax/detalle_dcc/delete/(?P<iddcc>[a-zA-Z0-9-]{0,40})/(?P<idcasco>[a-zA-Z0-9-]{0,40})/', 'detalleDCC_delete',name='detalleDCC_delete'),
    url(r'^ajax/detalle_dcc/delete/$', 'detalleDCC_delete', name='detalleDCC_delete2'),


    #############################################################
    #       ENTREGA DE CASCO A PRODUCCION TERMINADA             #
    #############################################################
    url(r'^cascopt/index', 'cascopt_index',name='cascopt_index'),
    url(r'^cascopt/add', 'cascopt_add', name='cascopt_add'),
    url(r'^cascopt/edit/(?P<idpt>[a-zA-Z0-9-]{0,40})/', 'cascopt_edit',name='cascopt_edit'),
    url(r'^cascopt/view/(?P<idpt>[a-zA-Z0-9-]{0,40})/', 'cascopt_view',name='cascopt_view'),
    url(r'^ajax/cascopt_del/(?P<idpt>[a-zA-Z0-9-]{0,40})/$', 'cascopt_del', name='cascopt_del'),
    url(r'^ajax/get-pt-list/$', 'get_pt_list', name = 'get_pt_list'),
                 ########################
                 #      DETALLES        #
                 ########################
    url(r'^detalle_pt/add/(?P<idpt>[a-zA-Z0-9-]{0,40})/', 'detallePT_add',name='detallePT_add'),
    url(r'^ajax/detalle_pt/delete/(?P<idpt>[a-zA-Z0-9-]{0,40})/(?P<idcasco>[a-zA-Z0-9-]{0,40})/', 'detallePT_delete',name='detallePT_delete'),
        
    url(r'^ajax/detalle_pt/delete/$', 'detallePT_delete',name='detallePT_delete2'),
    
    #############################################################
    #               RECEPC PT DE ENT. EXTERNAS                  #
    #############################################################                
    url(r'^ptexternos/index', 'ptexternos_index',name='ptexternos_index'),
    url(r'^ptexternos/add', 'ptexternos_add', name='ptexternos_add'),
    url(r'^ptexternos/view/(?P<idpte>[a-zA-Z0-9-]{0,40})/', 'ptexternos_view',name='ptexternos_view'),
    url(r'^ajax/ptexternos_del/(?P<idpte>[a-zA-Z0-9-]{0,40})/$', 'ptexternos_del', name='ptexternos_del'),
    url(r'^ptexternos/edit/(?P<idpte>[a-zA-Z0-9-]{0,40})/', 'ptexternos_edit',name='ptexternos_edit'),
    url(r'^ajax/get-rept-list/$', 'get_rept_list', name = 'get_rept_list'),
    
                 ########################
                 #      DETALLES        #
                 ########################
    
    url(r'^detalle_pte/add/(?P<idpte>[a-zA-Z0-9-]{0,40})/', 'detallePTE_add',name='detallePTE_add'),
    url(r'^ajax/detalle_pte/delete/(?P<idpte>[a-zA-Z0-9-]{0,40})/(?P<idcasco>[a-zA-Z0-9-]{0,40})/', 'detallePTE_delete',name='detallePTE_delete'),
    url(r'^ajax/detalle_pte/delete/$', 'detallePTE_delete',name='detallePTE_delete2'),
    url(r'^detalle_pte/edit/(?P<idpte>[a-zA-Z0-9-]{0,40})/(?P<idcasco>[a-zA-Z0-9-]{0,40})/', 'detallePTE_edit',name='detallePTE_edit'),
    url(r'^detalle_pte/edit/$', 'detallePTE_edit',name='detallePTE_edit2'),
    
    #############################################################
    #               RECEPC RECHAZ. DE ENT. EXTERNAS             #
    ############################################################# 
                   
    url(r'^rechaexternos/index', 'rechaexternos_index',name='rechaexternos_index'),
    url(r'^rechaexternos/add', 'rechaexternos_add', name='rechaexternos_add'),
    url(r'^rechaexternos/view/(?P<idrre>[a-zA-Z0-9-]{0,40})/', 'rechaexternos_view',name='rechaexternos_view'),
    url(r'^ajax/rechaexternos_del/(?P<idrre>[a-zA-Z0-9-]{0,40})/$', 'rechaexternos_del', name='rechaexternos_del'),
    url(r'^rechaexternos/edit/(?P<idrre>[a-zA-Z0-9-]{0,40})/', 'rechaexternos_edit',name='rechaexternos_edit'),
    url(r'^ajax/get-rere-list/$', 'get_rere_list', name = 'get_rere_list'),
    
                 ########################
                 #      DETALLES        #
                 ########################
    
#    url(r'^detalle_rre/add/(?P<idrre>[a-zA-Z0-9-]{0,40})/', 'detalleRRE_add',name='detalleRRE_add'),
#    url(r'^ajax/detalle_rre/delete/(?P<idcasco>[a-zA-Z0-9-]{0,40})/(?P<idrre>[a-zA-Z0-9-]{0,40})/', 'detalleRRE_delete',name='detalleRRE_delete'),
#    url(r'^ajax/detalle_rre/delete/$', 'detalleRRE_delete',name='detalleRRE_delete2'),
#    url(r'^detalle_rre/edit/(?P<idcasco>[a-zA-Z0-9-]{0,40})/(?P<idrre>[a-zA-Z0-9-]{0,40})/', 'detalleRRE_edit',name='detalleRRE_edit'),
#    url(r'^detalle_rre/edit/$', 'detalleRRE_edit',name='detalleRRE_edit2'),
    
    url(r'^detalle_rre/add/(?P<idrre>[a-zA-Z0-9-]{0,40})/', 'detalleRRE_add',name='detalleRRE_add'),
    url(r'^ajax/detalle_rre/delete/(?P<idcasco>[a-zA-Z0-9-]{0,40})/(?P<idrre>[a-zA-Z0-9-]{0,40})/', 'detalleRRE_delete',name='detalleRRE_delete'),
    url(r'^detalle_rre/edit/(?P<idcasco>[a-zA-Z0-9-]{0,40})/(?P<idrre>[a-zA-Z0-9-]{0,40})/', 'detalleRRE_edit',name='detalleRRE_edit'),
    
    url(r'^ajax/detalle_rre/delete/$', 'detalleRRE_delete',name='detalleRRE_delete2'),
    url(r'^detalle_rre/edit/$', 'detalleRRE_edit',name='detalleRRE_edit2'),
    #############################################################
    #               RECEPC CASCO. DE ENT. EXTERNAS    TRANSF. NO ACEPTADA #
    ############################################################# 
                   
    url(r'^cascoexternos/index', 'cascoexternos_index',name='cascoexternos_index'),
    url(r'^cascoexternos/add', 'cascoexternos_add', name='cascoexternos_add'),
    url(r'^cascoexternos/view/(?P<idrce>[a-zA-Z0-9-]{0,40})/', 'cascoexternos_view',name='cascoexternos_view'),
    url(r'^ajax/cascoexternos_del/(?P<idrce>[a-zA-Z0-9-]{0,40})/$', 'cascoexternos_del', name='cascoexternos_del'),
    url(r'^cascoexternos/edit/(?P<idrce>[a-zA-Z0-9-]{0,40})/', 'cascoexternos_edit',name='cascoexternos_edit'),
    url(r'^ajax/get-reca-list/$', 'get_reca_list', name = 'get_reca_list'),
    
                 ########################
                 #      DETALLES        #
                 ########################
    
    url(r'^detalle_rce/add/(?P<idrce>[a-zA-Z0-9-]{0,40})/', 'detalleRCE_add',name='detalleRCE_add'),
    url(r'^ajax/detalle_rce/delete/(?P<idcasco>[a-zA-Z0-9-]{0,40})/(?P<idrce>[a-zA-Z0-9-]{0,40})/', 'detalleRCE_delete',name='detalleRCE_delete'),
    url(r'^ajax/detalle_rce/delete/$', 'detalleRCE_delete',name='detalleRCE_delete2'),
    url(r'^detalle_rce/edit/(?P<idcasco>[a-zA-Z0-9-]{0,40})/(?P<idrce>[a-zA-Z0-9-]{0,40})/', 'detalleRCE_edit',name='detalleRCE_edit'),
    url(r'^detalle_rce/edit/$', 'detalleRCE_edit',name='detalleRCE_edit2'),
    
    #############################################################
    #                     DECOMISAR CASCOS                      #
    #############################################################
    url(r'^cascodc/index', 'cascodc_index',name='cascodc_index'),
    url(r'^cascodc/add', 'cascodc_add', name='cascodc_add'),
    url(r'^cascodc/view/(?P<iddc>[a-zA-Z0-9-]{0,40})/', 'cascodc_view',name='cascodc_view'),
    url(r'^cascodc/edit/(?P<iddc>[a-zA-Z0-9-]{0,40})/', 'cascodc_edit',name='cascodc_edit'),
    url(r'^ajax/cascodc_del/(?P<iddc>[a-zA-Z0-9-]{0,40})/$', 'cascodc_del', name='cascodc_del'),
    url(r'^ajax/get-dc-list/$', 'get_dc_list', name = 'get_dc_list'),
                 ########################
                 #      DETALLES        #
                 ########################
    url(r'^detalle_dc/add/(?P<iddc>[a-zA-Z0-9-]{0,40})/', 'detalleDC_add',name='detalleDC_add'),
    url(r'^ajax/detalle_dc/delete/(?P<iddc>[a-zA-Z0-9-]{0,40})/(?P<idcasco>[a-zA-Z0-9-]{0,40})/', 'detalleDC_delete',name='detalleDC_delete'),
    
    url(r'^ajax/detalle_dc/delete/$', 'detalleDC_delete',name='detalleDC_delete2'),
    
    url(r'^ajax/detalle_dc/list/(?P<idprod>[a-zA-Z0-9-]{0,40})/(?P<iddc>[a-zA-Z0-9-]{0,40})/', 'detalleDC_list',name='detalleDC_list'),
    url(r'^ajax/detalle_dc/list/$', 'detalleDC_list', name='detalleDC_list2'),
   
       
)
