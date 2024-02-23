 CREATE OR REPLACE VIEW balcascovsrecapaux AS 
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
            WHEN 'Rechazado por error revisión'::text THEN 1
            ELSE 0
        END) AS "ER", sum(
        CASE casco_casco.estado_actual
            WHEN 'Rechazado por Entidad Externa'::text THEN 1
            ELSE 0
        END) AS "REE", sum(
        CASE casco_casco.estado_actual
            WHEN 'Transferencia'::text THEN 1
            ELSE 0
        END) AS "Transferencia", sum(
        CASE casco_casco.estado_actual
            WHEN 'Facturado'::text THEN 1
            ELSE 0
        END) AS "Facturado", sum(
        CASE casco_casco.estado_actual
            WHEN 'Casco Rechazado Entregado'::text THEN 1
            ELSE 0
        END) AS "ECR"
   FROM casco_casco
   JOIN admincomerciax_producto ON casco_casco.producto_id::text = admincomerciax_producto.id::text
  WHERE casco_casco.estado_actual::text <> 'Proceso de Producción'::text AND casco_casco.estado_actual::text <> 'Almacén Producción Terminada'::text AND casco_casco.estado_actual::text <> 'Devuelto a Vulca'::text
  GROUP BY admincomerciax_producto.descripcion;