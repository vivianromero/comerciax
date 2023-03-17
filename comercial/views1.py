if fact.cliente.comercializadora==True:
        filas=DetalleRC.objects.select_related().filter(rc__cliente__provincia=fact.cliente.provincia,rc__cliente__organismo=fact.cliente.organismo,rc__recepcioncliente_tipo=fact.tipo,casco__estado_actual="PT").order_by('casco_casco.casco_nro')
    else:
        filas=DetalleRC.objects.select_related().filter(rc__cliente=fact.cliente,rc__recepcioncliente_tipo=fact.tipo,casco__estado_actual="PT").order_by('casco_casco.casco_nro')
    
    filas_result=[]
    for a1 in filas:
        filas_result.append({'id_casco':a1.casco.id_casco,'casco_nro':a1.casco.casco_nro,
                             'producto':a1.casco.producto,'producto_salida':a1.casco.producto_salida,
                             'get_cliente':a1.casco.get_cliente})
    if fact.tipo=='O':
        filas1=Casco.objects.select_related().filter(estado_actual="DC").order_by('casco_nro')
        filasxx=Casco.objects.select_related().filter(venta=True,estado_actual="PT").order_by('casco_nro')
            
        for a1 in filas1:
            filas_result.append({'id_casco':a1.id_casco,'casco_nro':a1.casco_nro,
                                 'producto':a1.producto,'producto_salida':a1.producto_salida,
                                 'get_cliente':a1.get_cliente})
        for a1 in filasxx:
            filas_result.append({'id_casco':a1.id_casco,'casco_nro':a1.casco_nro,
                                 'producto':a1.producto,'producto_salida':a1.producto_salida,
                                 'get_cliente':a1.get_cliente})