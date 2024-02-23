 SELECT admincomerciax_producto.descripcion AS medida, sum(
        CASE casco_casco.estado_actual
            WHEN 'Almacén de Casco'::text THEN 1
            ELSE 0
        END) AS almacen, sum(
        CASE casco_casco.estado_actual
            WHEN 'Devuelto a Inservible'::text THEN 1
            ELSE 0
        END) AS dip, sum(
        CASE casco_casco.estado_actual
            WHEN 'Devuelto a Vulca'::text THEN 1
            ELSE 0
        END) AS dvp, sum(
        CASE casco_casco.estado_actual
            WHEN 'Rechazado por error revisión'::text THEN 1
            ELSE 0
        END) AS er, sum(
        CASE casco_casco.estado_actual
            WHEN 'Rechazado por Entidad Externa'::text THEN 1
            ELSE 0
        END) AS ree
   FROM casco_casco
   JOIN admincomerciax_producto ON casco_casco.producto_id::text = admincomerciax_producto.id::text
  WHERE casco_casco.estado_actual::text <> 'Proceso de Producción'::text AND casco_casco.estado_actual::text <> 'Almacén Producción Terminada'::text AND casco_casco.estado_actual::text <> 'Transferencia'::text AND casco_casco.estado_actual::text <> 'Facturado'::text AND casco_casco.estado_actual::text <> 'Casco Rechazado Entregado'::text
  GROUP BY admincomerciax_producto.descripcion;

 