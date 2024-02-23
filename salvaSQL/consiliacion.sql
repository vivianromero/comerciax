CREATE FUNCTION consiliacion(IN fechainicial date, IN fechafinal date, IN idcliente character varying, OUT cantidad bigint, OUT estado character varying)
  RETURNS SETOF record AS
$BODY$SELECT 
  count(casco_trazabilidadcasco.casco_id),
  casco_trazabilidadcasco.estado
FROM 
  casco_trazabilidadcasco
  inner join casco_doc on casco_trazabilidadcasco.doc_id = casco_doc.id_doc
WHERE 
  casco_trazabilidadcasco.casco_id IN ( SELECT 
                      casco_detallerc.casco_id 
                    FROM 
                      public.casco_recepcioncliente
                      inner join  public.casco_detallerc on casco_detallerc.rc_id = casco_recepcioncliente.doc_recepcioncliente_id
                    WHERE
                      casco_recepcioncliente.cliente_id = $3
                      )
  AND 
   casco_doc.fecha_doc >= $1
  AND
   casco_doc.fecha_doc <= $2
group by 
  casco_trazabilidadcasco.estado$BODY$
  LANGUAGE sql VOLATILE
  COST 100
  ROWS 1000;
