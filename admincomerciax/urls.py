from django.conf.urls.defaults import *
from comerciax.admincomerciax.views import *

urlpatterns = patterns('comerciax.admincomerciax.views',
    # Example:
    # (r'^comerciax/', include('comerciax.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    # (r'^admin/doc/', include('django.contrib.admindocs.urls')),
   

    url(r'^usuario/excel', 'createexcel', name='createexcel'),
    url(r'^usuario/article', 'article', name='article'),
    url(r'^reporte1/index', 'reporte1', name='reporte1'),
    url(r'^reporte1/pdfcliente', 'pdfcliente', name='pdfcliente'),
    url(r'^ajax/repotcliente/$', 'reportcliente', name='reportcliente'),
    
    url(r'^usuario/index', 'usuario', name='usuario'),
    url(r'^usuario/add', 'adduser', name='adduser'),
    url(r'^usuario/puser', 'puser', name='puser'),
    url(r'^usuario/viewperfil/(?P<idusuario>[a-zA-Z0-9-$]{0,40})/', 'viewperfil', name='viewperfil'),
    
    url(r'^usuario/view/(?P<idusuario>[a-zA-Z0-9-$]{0,40})/', 'viewusuario', name='viewusuario'),
    url(r'^usuario/view/$', 'viewusuario', name='viewusuario2'),
    
    url(r'^grupo/index', 'grupo', name='grupo'),
    url(r'^grupo/add', 'addgrupo', name='addgrupo'),
    url(r'^grupo/pgrupo', 'pgrupo', name='pgrupo'),
    url(r'^grupo/view/(?P<idgrupo>[a-zA-Z0-9-$]{0,40})/', 'viewgrupo', name='viewgrupo'),
    url(r'^grupo/view/$', 'viewgrupo', name='viewgrupo2'),

    # Uncomment the next line to enable the admin:
    # (r'^admin/', include(admin.site.urls)),
    url(r'^provincia/index', 'provincia', name='provincia'),
    url(r'^provincia/add', 'addprovincia', name='addprovincia'),
    url(r'^provincia/view/(?P<idprov>[a-zA-Z0-9-]{0,40})/', 'viewprovincia', name='viewprovincia'),
    url(r'^provincia/view/$', 'viewprovincia', name='viewprovincia2'),
    
    url(r'^organismo/index', 'organismo', name='organismo'),
    url(r'^organismo/add', 'addorganismo', name='addorganismo'),
    url(r'^organismo/view/(?P<idorg>[a-zA-Z0-9-]{0,40})/', 'vieworganismo', name='vieworganismo'),
    url(r'^organismo/view/$', 'vieworganismo', name='vieworganismo2'),
    url(r'^organismo/unionadd/(?P<idorg>[a-zA-Z0-9-]{0,40})/', 'unionadd', name='unionadd'),
    
    url(r'^sucursal/index', 'sucursal', name='sucursal'),
    url(r'^sucursal/add', 'addsucursal', name='addsucursal'),
    url(r'^sucursal/view/(?P<idsuc>[a-zA-Z0-9-]{0,40})/', 'viewsucursal', name='viewsucursal'),
    url(r'^sucursal/view/$', 'viewsucursal', name='viewsucursal2'),
    
    url(r'^area/index', 'area', name='area'),
    url(r'^area/add', 'addarea', name='addarea'),
    url(r'^area/view/(?P<idarea>[a-zA-Z0-9-]{0,40})/', 'viewarea', name='viewarea'),
    url(r'^area/view/$', 'viewarea', name='viewarea2'),
    
    url(r'^causar/index', 'causar', name='causar'),
    url(r'^causar/add', 'addcausar', name='addcausar'),
    url(r'^causar/view/(?P<idcausar>[a-zA-Z0-9-]{0,40})/', 'viewcausar', name='viewcausar'),
    url(r'^causar/view/$', 'viewcausar', name='viewcausar2'),
    
    url(r'^unidadm/index', 'unidadm', name='unidadm'),
    url(r'^unidadm/add', 'addunidadm', name='addunidadm'),
    url(r'^unidadm/view/(?P<idunidadm>[a-zA-Z0-9-]{0,40})/', 'viewunidadm', name='viewunidadm'),
    url(r'^unidadm/view/$', 'viewunidadm', name='viewunidadm2'),
    
    url(r'^formap/index', 'formap', name='formap'),
    url(r'^formap/add', 'addformap', name='addformap'),
    url(r'^formap/view/(?P<idformap>[a-zA-Z0-9-]{0,40})/', 'viewformap', name='viewformap'),
    url(r'^formap/view/$', 'viewformap', name='viewformap2'),
    
    url(r'^moneda/index', 'moneda', name='moneda'),
    url(r'^moneda/add', 'addmoneda', name='addmoneda'),
    url(r'^moneda/view/(?P<idmoneda>[a-zA-Z0-9-]{0,40})/', 'viewmoneda', name='viewmoneda'),
    url(r'^moneda/view/$', 'viewmoneda', name='viewmoneda2'),
    
    url(r'^producto/index', 'producto', name='producto'),
    url(r'^producto/add', 'addproducto', name='addproducto'),
    url(r'^producto/view/(?P<idproducto>[a-zA-Z0-9-]{0,40})/', 'viewproducto', name='viewproducto'),
    url(r'^producto/view/$', 'viewproducto', name='viewproducto2'),
    
    url(r'^empresa/index', 'empresa', name='empresa'),
    url(r'^empresa/add', 'addempresa', name='addempresa'),
    url(r'^empresa/view/(?P<idempresa>[a-zA-Z0-9-]{0,40})/', 'viewempresa', name='viewempresa'),
    url(r'^empresa/view/$', 'viewempresa', name='viewempresa2'),
    
    url(r'^cliente/index', 'cliente', name='cliente'),
    url(r'^cliente/add', 'addcliente', name='addcliente'),
    url(r'^cliente/view/(?P<idcliente>[a-zA-Z0-9-]{0,40})/', 'viewcliente', name='viewcliente'),
    url(r'^cliente/view/$', 'viewcliente', name='viewcliente2'),
    url(r'^cliente/contratoadd/(?P<idcliente>[a-zA-Z0-9-]{0,40})/', 'contratoadd', name='contratoadd'),
    url(r'^cliente/contratoexiste/(?P<idcliente>[a-zA-Z0-9-]{0,40})/', 'contratoexiste', name='contratoexiste'),
    url(r'^cliente/viewcontrato/(?P<idcliente>[a-zA-Z0-9-]{0,40})/(?P<idcontrato>[a-zA-Z0-9-]{0,40})/', 'viewcontrato', name='viewcontrato'),
    url(r'^cliente/viewcontrato/$', 'viewcontrato', name='viewcontrato2'),
    url(r'^cliente/viewcontratoselecc/(?P<idcliente>[a-zA-Z0-9-]{0,40})/(?P<idcontrato>[a-zA-Z0-9-]{0,40})/', 'viewcontratoselecc', name='viewcontratoselecc'),
    url(r'^cliente/viewcontratoselecc/$', 'viewcontratoselecc', name='viewcontratoselecc2'),
    
    
    url(r'^planes/index', 'planes', name='planes'),
    url(r'^ajax/get-planes-list/$', 'get_planes_list', name='get_planes_list'),
    url(r'^planes/view/(?P<idcont>[a-zA-Z0-9-]{0,40})/', 'viewplan', name='viewplan'),
    url(r'^planes/view/$', 'viewplan', name='viewplan2'),
    url(r'^planescont/view/(?P<idcontcli>[a-zA-Z0-9-]{0,40})/', 'planesadd', name='planesadd'),
    url(r'^ver_fecha/$', 'ver_fecha', name='ver_fecha'),
    url(r'^ajax/obteneranos/list/(?P<idcont>[a-zA-Z0-9-]{0,40})/(?P<tipo>[a-zA-Z0-9-]{0,40})/', 'obteneranos_list', name='obteneranos_list'),
    url(r'^ajax/obteneranos/list/$', 'obteneranos_list', name='obteneranos_list2'),
    
    url(r'^planes/planedit/(?P<idplan>[a-zA-Z0-9-]{0,40})/(?P<idcliente>[a-zA-Z0-9-]{0,40})/$', 'planedit', name='planedit'),
    url(r'^planes/planedit/$', 'planedit', name='planedit2'),
    
    url(r'^planes/plandel/(?P<idplan>[a-zA-Z0-9-]{0,40})/(?P<idcont>[a-zA-Z0-9-]{0,40})/$', 'plandel', name='plandel'),
    url(r'^planes/plandel/$', 'plandel', name='plandel2'),
    
    url(r'^ajax/get_datosplan/$', 'get_datosplan', name='get_datosplan2'),
    url(r'^ajax/get_datosplan/(?P<idcont>[a-zA-Z0-9-]{0,40})/(?P<idano>[a-zA-Z0-9-]{0,40})/', 'get_datosplan', name='get_datosplan'),
    
    url(r'^cliente/repadd/(?P<idcliente>[a-zA-Z0-9-]{0,40})/(?P<idcont>[a-zA-Z0-9-]{0,40})/', 'repadd', name='repadd'),
    url(r'^cliente/transadd/(?P<idcliente>[a-zA-Z0-9-]{0,40})/(?P<idcont>[a-zA-Z0-9-]{0,40})/', 'transadd', name='transadd'),
    
    #estos patrones son asi, porque fue la unica forma que encontre que funcionara para hacerle referencia desde template
    url(r'^grupo/edit/(?P<idgrupo>[a-zA-Z0-9-]{0,40})/$', 'editgrupo', name='editgrupo'),
    url(r'^usuario/edit/(?P<idusuario>[a-zA-Z0-9-]{0,40})/$', 'editusuario', name='editusuario'),
    url(r'^usuario/changepassword/(?P<idusuario>[a-zA-Z0-9-]{0,40})/$', 'changepassword', name='changepassword'),
    url(r'^usuario/editperfil/(?P<idusuario>[a-zA-Z0-9-]{0,40})/$', 'editperfil', name='editperfil'),
    url(r'^usuario/changepassperfil/(?P<idusuario>[a-zA-Z0-9-]{0,40})/$', 'changepassperfil', name='changepassperfil'),
    
    url(r'^provincia/edit/(?P<idprov>[a-zA-Z0-9-]{0,40})/$', 'editprovincia', name='editprovincia'),
    url(r'^organismo/edit/(?P<idorg>[a-zA-Z0-9-]{0,40})/$', 'editorganismo', name='editorganismo'),
    url(r'^sucursal/edit/(?P<idsuc>[a-zA-Z0-9-]{0,40})/$', 'editsucursal', name='editsucursal'),
    url(r'^area/edit/(?P<idarea>[a-zA-Z0-9-]{0,40})/$', 'editarea', name='editarea'),
    url(r'^causar/edit/(?P<idcausar>[a-zA-Z0-9-]{0,40})/$', 'editcausar', name='editcausar'),
    url(r'^unidadm/edit/(?P<idunidadm>[a-zA-Z0-9-]{0,40})/$', 'editunidadm', name='editunidadm'),
    url(r'^formap/edit/(?P<idformap>[a-zA-Z0-9-]{0,40})/$', 'editformap', name='editformap'),
    url(r'^moneda/edit/(?P<idmoneda>[a-zA-Z0-9-]{0,40})/$', 'editmoneda', name='editmoneda'),
    url(r'^producto/edit/(?P<idproducto>[a-zA-Z0-9-]{0,40})/$', 'editproducto', name='editproducto'),
    url(r'^empresa/edit/(?P<idempresa>[a-zA-Z0-9-]{0,40})/$', 'editempresa', name='editempresa'),
    url(r'^cliente/edit/(?P<idcliente>[a-zA-Z0-9-]{0,40})/$', 'editcliente', name='editcliente'),
    
    url(r'^cliente/contratoedit/(?P<idcon>[a-zA-Z0-9-]{0,40})/(?P<idcliente>[a-zA-Z0-9-]{0,40})/', 'contratoedit', name='contratoedit'),
#    url(r'^cliente/contratoedit/$', 'contratoedit', name='contratoedit2'),
    
    url(r'^cliente/repedit/(?P<idcont>[a-zA-Z0-9-]{0,40})/(?P<idcliente>[a-zA-Z0-9-]{0,40})/(?P<idrep>[a-zA-Z0-9-]{0,40})/$', 'repedit', name='repedit'),
    url(r'^cliente/repedit/$', 'repedit', name='repedit2'),
    url(r'^cliente/transedit/(?P<idcont>[a-zA-Z0-9-]{0,40})/(?P<idcliente>[a-zA-Z0-9-]{0,40})/(?P<idtrans>[a-zA-Z0-9-]{0,40})/$', 'transedit', name='transedit'),
    url(r'^cliente/transedit/$', 'transedit', name='transedit2'),
    
    url(r'^ajax/delgrupo/(?P<idgrupo>[a-zA-Z0-9-]{0,40})/$', 'delgrupo', name='delgrupo'), 
    url(r'^ajax/delusuario/(?P<idusuario>[a-zA-Z0-9-]{0,40})/$', 'delusuario', name='delusuario'),
    url(r'^ajax/delprovincia/(?P<idprov>[a-zA-Z0-9-]{0,40})/$', 'delprovincia', name='delprovincia'),
    url(r'^ajax/get-provincias-list/$', 'get_provincias_list', name='get_provincias_list'),
    url(r'^ajax/delorganismo/(?P<idorg>[a-zA-Z0-9-]{0,40})/$', 'delorganismo', name='delorganismo'),
    url(r'^ajax/get-organismo-list/$', 'get_organismo_list', name='get_organismo_list'),
    url(r'^ajax/delsucursal/(?P<idsuc>[a-zA-Z0-9-]{0,40})/$', 'delsucursal', name='delsucursal'),
    url(r'^ajax/get-sucursal-list/$', 'get_sucursal_list', name='get_sucursal_list'),
    url(r'^ajax/delarea/(?P<idarea>[a-zA-Z0-9-]{0,40})/$', 'delarea', name='delarea'),
    url(r'^ajax/get-area-list/$', 'get_area_list', name='get_area_list'),
    url(r'^ajax/delcausar/(?P<idcausar>[a-zA-Z0-9-]{0,40})/$', 'delcausar', name='delcausar'),
    url(r'^ajax/get-causar-list/$', 'get_causar_list', name='get_causar_list'),
    url(r'^ajax/delunidadm/(?P<idunidadm>[a-zA-Z0-9-]{0,40})/$', 'delunidadm', name='delunidadm'),
    url(r'^ajax/get-unidadm-list/$', 'get_unidadm_list', name='get_unidadm_list'),
    url(r'^ajax/delformap/(?P<idformap>[a-zA-Z0-9-]{0,40})/$', 'delformap', name='delformap'),
    url(r'^ajax/get-formap-list/$', 'get_formap_list', name='get_formap_list'),
    url(r'^ajax/delmoneda/(?P<idmoneda>[a-zA-Z0-9-]{0,40})/$', 'delmoneda', name='delmoneda'),
    url(r'^ajax/get-moneda-list/$', 'get_moneda_list', name='get_moneda_list'),
    url(r'^ajax/delproducto/(?P<idproducto>[a-zA-Z0-9-]{0,40})/$', 'delproducto', name='delproducto'),
    url(r'^ajax/get-producto-list/$', 'get_producto_list', name='get_producto_list'),
    url(r'^ajax/delempresa/(?P<idempresa>[a-zA-Z0-9-]{0,40})/$', 'delempresa', name='delempresa'),
    url(r'^ajax/get-empresa-list/$', 'get_empresa_list', name='get_empresa_list'),
    url(r'^ajax/delcliente/(?P<idcliente>[a-zA-Z0-9-]{0,40})/$', 'delcliente', name='delcliente'),
    url(r'^ajax/get-cliente-list/$', 'get_cliente_list', name='get_cliente_list'),
    url(r'^ajax/contratodel/(?P<idcontrato>[a-zA-Z0-9-]{0,40})/(?P<idcliente>[a-zA-Z0-9-]{0,40})/$', 'contratodel', name='contratodel'),
    url(r'^ajax/contratocancel/(?P<idcontrato>[a-zA-Z0-9-]{0,40})/(?P<idcliente>[a-zA-Z0-9-]{0,40})/$', 'contratocancel', name='contratocancel'),
    url(r'^ajax/repdel/(?P<idcont>[a-zA-Z0-9-]{0,40})/(?P<idcliente>[a-zA-Z0-9-]{0,40})/(?P<idrep>[a-zA-Z0-9-]{0,40})/$', 'repdel', name='repdel'),
    url(r'^ajax/repdel/$', 'repdel', name='repdel2'),
    url(r'^ajax/transdel/(?P<idcont>[a-zA-Z0-9-]{0,40})/(?P<idcliente>[a-zA-Z0-9-]{0,40})/(?P<idtrans>[a-zA-Z0-9-]{0,40})/$', 'transdel', name='transdel'),
    url(r'^ajax/transdel/$', 'transdel', name='transdel2'),
    url(r'^ajax/delunion/(?P<idorg>[a-zA-Z0-9-]{0,40})/(?P<idunion>[a-zA-Z0-9-]{0,40})/', 'delunion', name='delunion'),
    url(r'^ajax/delunion/$', 'delunion', name='delunion2'),
    
    url(r'^ajax/get_uniones/$', 'get_uniones', name='get_uniones2'),
    url(r'^ajax/get_uniones/(?P<idorg>[a-zA-Z0-9-]{0,40})/', 'get_uniones', name='get_uniones'),
    
    url(r'^ajax/get-grupo-list/$', 'get_grupo_list', name='get_grupo_list'),
    url(r'^ajax/get-usuario-list/$', 'get_usuario_list', name='get_usuario_list'),
    
     #############################################################
    #       CONFIG DE ORG. CON NRO DE CASCO INDEPEND.           #
    #############################################################  
       
    url(r'^confignrocasco/index', 'confignrocasco_index',name='confignrocasco_index'),
    url(r'^confignrocasco/add', 'confignrocasco_add', name='confignrocasco_add'),
    url(r'^confignrocasco/view/(?P<idconf>[a-zA-Z0-9-]{0,40})/', 'confignrocasco_view',name='confignrocasco_view'),
    url(r'^ajax/confignrocasco_del/(?P<idconf>[a-zA-Z0-9-]{0,40})/', 'confignrocasco_del',name='confignrocasco_del'),
    url(r'^ajax/get-cnroc-list/$', 'get_cnroc_list', name = 'get_cnroc_list'),
    
    url(r'^eliminar_casco', 'eliminar_casco', name='eliminar_casco'),
    url(r'^eliminar_ocioso', 'eliminar_ocioso', name='eliminar_ocioso'),
    url(r'^ocioso_casco', 'ocioso_casco', name='ocioso_casco'),
    url(r'^config_smtp', 'config_smtp', name='config_smtp'),
    
    url(r'^ajax/detalleeliminar_list/list/(?P<idcli>[a-zA-Z0-9-]{0,40})/(?P<tipo>[a-zA-Z0-9-]{0,40})/$', 'detalleeliminar_list',name='detalleeliminar_list'),
    url(r'^ajax/detalleeliminar_list/list/$', 'detalleeliminar_list', name='detalleeliminar_list2'),
    
    url(r'^ajax/detalleocioso_list/list/(?P<idcli>[a-zA-Z0-9-]{0,40})/$', 'detalleocioso_list',name='detalleocioso_list'),
    url(r'^ajax/detalleocioso_list/list/$', 'detalleocioso_list', name='detalleocioso_list2'),
)
