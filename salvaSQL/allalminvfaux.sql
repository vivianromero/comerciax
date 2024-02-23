 SELECT admincomerciax_producto.descripcion AS medida, sum(
        CASE casco_casco.estado_actual
            WHEN 'Almacén de Casco'::text THEN 1
            ELSE 0
        END) AS "Casco", sum(
        CASE casco_casco.estado_actual
            WHEN 'Devuelto a Inservible'::text THEN 1
            ELSE 0
        END) AS "DIP", sum(
        CASE casco_casco.estado_actual
            WHEN 'Devuelto a Vulca'::text THEN 1
            ELSE 0
        END) AS "DVP", sum(
        CASE casco_casco.estado_actual
            WHEN 'Rechazado por error revisión'::text THEN 1
            ELSE 0
        END) AS "ER", sum(
        CASE casco_casco.estado_actual
            WHEN 'Rechazado por Entidad Externa'::text THEN 1
            ELSE 0
        END) AS "REE", sum(
        CASE casco_casco.estado_actual
            WHEN 'Proceso de Producción'::text THEN 1
            ELSE 0
        END) AS "Produccion", sum(
        CASE casco_casco.estado_actual
            WHEN 'Almacén Producción Terminada'::text THEN 1
            ELSE 0
        END) AS "ProduccionT"
   FROM casco_casco
   JOIN admincomerciax_producto ON casco_casco.producto_id::text = admincomerciax_producto.id::text
  WHERE casco_casco.estado_actual::text <> 'Transferencia'::text AND casco_casco.estado_actual::text <> 'Facturado'::text AND casco_casco.estado_actual::text <> 'Casco Rechazado Entregado'::text
  GROUP BY admincomerciax_producto.descripcion;