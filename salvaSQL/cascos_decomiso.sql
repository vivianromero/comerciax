SELECT 
            admincomerciax_producto.descripcion, 
            admincomerciax_producto.id,
            casco_doc.fecha_doc, 
            casco_casco.casco_nro, 
        casco_casco.venta,
            casco_casco.estado_actual,
            casco_casco.id_casco,
            cast(date_part('day', now()-casco_doc.fecha_doc) as integer) AS dias,
            admincomerciax_cliente.nombre
        FROM casco_casco
            INNER JOIN casco_detallept ON casco_detallept.casco_id = casco_casco.id_casco
            INNER JOIN casco_produccionterminada ON casco_detallept.pt_id = casco_produccionterminada.doc_pt_id
            INNER JOIN casco_doc ON casco_doc.id_doc = casco_produccionterminada.doc_pt_id
            INNER JOIN admincomerciax_producto ON casco_casco.producto_salida_id = admincomerciax_producto.id
            INNER JOIN casco_detallerc ON casco_detallerc.casco_id = casco_casco.id_casco
            INNER JOIN casco_recepcioncliente ON casco_detallerc.rc_id = casco_recepcioncliente.doc_recepcioncliente_id
            INNER JOIN admincomerciax_cliente ON  casco_recepcioncliente.cliente_id = admincomerciax_cliente.id

        union all
        
        SELECT 
            admincomerciax_producto.descripcion, 
            admincomerciax_producto.id,
            casco_doc.fecha_doc, 
            casco_casco.casco_nro, 
            casco_casco.venta,
            casco_casco.estado_actual,
            casco_casco.id_casco,
            cast(date_part('day', now()-casco_doc.fecha_doc) as integer) AS dias,
            admincomerciax_cliente.nombre
            
        FROM casco_casco
        
            INNER JOIN casco_detallepte ON casco_detallepte.casco_id = casco_casco.id_casco
            INNER JOIN casco_ptexternos ON casco_detallepte.doc_pte_id = casco_ptexternos.doc_ptexternos_id
            INNER JOIN casco_doc ON casco_doc.id_doc = casco_ptexternos.doc_ptexternos_id
            INNER JOIN admincomerciax_producto ON casco_casco.producto_salida_id = admincomerciax_producto.id
            INNER JOIN casco_detallerc ON casco_detallerc.casco_id = casco_casco.id_casco
            INNER JOIN casco_recepcioncliente ON casco_detallerc.rc_id = casco_recepcioncliente.doc_recepcioncliente_id
            INNER JOIN admincomerciax_cliente ON  casco_recepcioncliente.cliente_id = admincomerciax_cliente.id