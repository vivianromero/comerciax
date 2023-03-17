SELECT 
                              casco_doc.fecha_doc, 
                              casco_recepcioncliente.recepcioncliente_nro, 
                              admincomerciax_cliente.codigo, 
                              admincomerciax_cliente.nombre, 
                              admincomerciax_cliente.id,
                              casco_casco.casco_nro, 
                              casco_casco.estado_actual, 
                              casco_casco.venta,
                              admincomerciax_producto.descripcion
                            FROM 
                              public.casco_detallerc, 
                              public.casco_recepcioncliente, 
                              public.casco_doc, 
                              public.admincomerciax_cliente, 
                              public.casco_casco, 
                              public.admincomerciax_producto
                            WHERE 
                              casco_detallerc.casco_id = casco_casco.id_casco AND
                              casco_recepcioncliente.doc_recepcioncliente_id = casco_detallerc.rc_id AND
                              casco_recepcioncliente.doc_recepcioncliente_id = casco_doc.id_doc AND
                              casco_recepcioncliente.cliente_id = admincomerciax_cliente.id AND
                              casco_casco.producto_salida_id = admincomerciax_producto.id