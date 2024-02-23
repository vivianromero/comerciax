 SELECT admincomerciax_producto.descripcion AS medida, 
	sum(CASE casco_casco.estado_actual WHEN 'Almac�n Producci�n Terminada'::text THEN 1 ELSE 0 END) AS "ProduccionT"
  FROM casco_casco inner join  admincomerciax_producto on casco_casco.producto_id::text = admincomerciax_producto.id::text
  WHERE casco_casco.estado_actual <> 'Almac�n de Casco' and 
	casco_casco.estado_actual <> 'Proceso de Producci�n' and 
	casco_casco.estado_actual <> 'Transferencia' and
	casco_casco.estado_actual <> 'Facturado' and 
	casco_casco.estado_actual <> 'Devuelto a Inservible' and 
	casco_casco.estado_actual <> 'Devuelto a Vulca' and 
	casco_casco.estado_actual <> 'Rechazado por error revisi�n' and 
	casco_casco.estado_actual <> 'Rechazado por Entidad Externa' and 
	casco_casco.estado_actual <> 'Casco Rechazado Entregado'
  GROUP BY admincomerciax_producto.descripcion;


 