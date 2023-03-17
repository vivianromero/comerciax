 SELECT admincomerciax_producto.descripcion AS medida, sum(
        CASE casco_casco.estado_actual
            WHEN 'Proceso de Producci�n'::text THEN 1
            ELSE 0
        END) AS "Produccion", sum(
        CASE casco_casco.estado_actual
            WHEN 'Almac�n Producci�n Terminada'::text THEN 1
            ELSE 0
        END) AS "ProduccionT"
   FROM casco_casco
   JOIN admincomerciax_producto ON casco_casco.producto_id::text = admincomerciax_producto.id::text
  WHERE casco_casco.estado_actual::text <> 'Almac�n de Casco'::text AND casco_casco.estado_actual::text <> 'Transferencia'::text AND casco_casco.estado_actual::text <> 'Facturado'::text AND casco_casco.estado_actual::text <> 'Devuelto a Inservible'::text AND casco_casco.estado_actual::text <> 'Devuelto a Vulca'::text AND casco_casco.estado_actual::text <> 'Rechazado por error revisi�n'::text AND casco_casco.estado_actual::text <> 'Rechazado por Entidad Externa'::text AND casco_casco.estado_actual::text <> 'Casco Rechazado Entregado'::text
  GROUP BY admincomerciax_producto.descripcion;

 