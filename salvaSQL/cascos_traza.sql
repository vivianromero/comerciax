SELECT 
                              casco_trazabilidadcasco.estado, 
                              casco_trazabilidadcasco.nro, 
                              casco_doc.tipo_doc, 
                              casco_doc.fecha_doc, 
                              casco_doc.fecha_operacion, 
                              casco_casco.casco_nro, 
                              casco_casco.producto_id, 
                              casco_casco.producto_salida_id, 
                              admincomerciax_cliente.codigo, 
                              admincomerciax_cliente.nombre, 
                              casco_recepcioncliente.cliente_id,
                              casco_doc.id_doc
                            FROM 
                              public.casco_trazabilidadcasco, 
                              public.casco_doc, 
                              public.casco_casco, 
                              public.casco_detallerc, 
                              public.casco_recepcioncliente, 
                              public.admincomerciax_cliente
                            WHERE 
                              casco_trazabilidadcasco.doc_id = casco_doc.id_doc AND
                              casco_trazabilidadcasco.casco_id = casco_casco.id_casco AND
                              casco_detallerc.casco_id = casco_trazabilidadcasco.casco_id AND
                              casco_detallerc.rc_id = casco_recepcioncliente.doc_recepcioncliente_id AND
                              casco_recepcioncliente.cliente_id = admincomerciax_cliente.id