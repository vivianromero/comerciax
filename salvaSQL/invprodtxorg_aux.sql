         SELECT admincomerciax_producto.descripcion, casco_doc.fecha_doc, casco_casco.casco_nro, casco_casco.id_casco, date_part('day'::text, now() - casco_doc.fecha_doc::timestamp with time zone)::integer AS dias, admincomerciax_organismo.siglas_organismo
           FROM casco_casco
      JOIN casco_detallept ON casco_detallept.casco_id::text = casco_casco.id_casco::text
   JOIN casco_produccionterminada ON casco_detallept.pt_id::text = casco_produccionterminada.doc_pt_id::text
   JOIN casco_doc ON casco_doc.id_doc::text = casco_produccionterminada.doc_pt_id::text
   JOIN admincomerciax_producto ON casco_casco.producto_salida_id::text = admincomerciax_producto.id::text
   JOIN casco_detallerc ON casco_detallerc.casco_id::text = casco_casco.id_casco::text
   JOIN casco_recepcioncliente ON casco_detallerc.rc_id::text = casco_recepcioncliente.doc_recepcioncliente_id::text
   JOIN admincomerciax_cliente ON casco_recepcioncliente.cliente_id::text = admincomerciax_cliente.id::text
   JOIN admincomerciax_organismo ON admincomerciax_organismo.id::text = admincomerciax_cliente.organismo_id::text
  WHERE casco_casco.estado_actual::text = 'Almacén Producción Terminada'::text AND casco_casco.venta = false
UNION ALL 
         SELECT admincomerciax_producto.descripcion, casco_doc.fecha_doc, casco_casco.casco_nro, casco_casco.id_casco, date_part('day'::text, now() - casco_doc.fecha_doc::timestamp with time zone)::integer AS dias, admincomerciax_organismo.siglas_organismo
           FROM casco_casco
      JOIN casco_detallepte ON casco_detallepte.casco_id::text = casco_casco.id_casco::text
   JOIN casco_ptexternos ON casco_detallepte.doc_pte_id::text = casco_ptexternos.doc_ptexternos_id::text
   JOIN casco_doc ON casco_doc.id_doc::text = casco_ptexternos.doc_ptexternos_id::text
   JOIN admincomerciax_producto ON casco_casco.producto_salida_id::text = admincomerciax_producto.id::text
   JOIN casco_detallerc ON casco_detallerc.casco_id::text = casco_casco.id_casco::text
   JOIN casco_recepcioncliente ON casco_detallerc.rc_id::text = casco_recepcioncliente.doc_recepcioncliente_id::text
   JOIN admincomerciax_cliente ON casco_recepcioncliente.cliente_id::text = admincomerciax_cliente.id::text
   JOIN admincomerciax_organismo ON admincomerciax_organismo.id::text = admincomerciax_cliente.organismo_id::text
  WHERE casco_casco.estado_actual::text = 'Almacén Producción Terminada'::text AND casco_casco.venta = false;