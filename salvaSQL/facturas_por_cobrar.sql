(select  case when princ.factura_nro is NULL
             then sec.factura_nro 
             else princ.factura_nro
         end,
         case when princ.fecha_doc is NULL
             then sec.fecha_doc 
             else princ.fecha_doc 
         end,
         
         case when princ.nombre is NULL
             then sec.nombre
             else princ.nombre
         end,
         COALESCE (princ.precio_cuc,0) as precio_cuc,
                 COALESCE (sec.precio_mn,0) as precio_mn,
         COALESCE (princ.importe_pagado_cuc,0) as importe_pagado_cuc,
         COALESCE (sec.importe_pagado_cup,0) as importe_pagado_cup,
         case when princ.edad is NULL
             then sec.edad1
             else princ.edad
         end,
                 case when princ.confirmada is NULL
             then sec.confirmada1
             else princ.confirmada
         end

from (SELECT DISTINCT

(select sum("public".comercial_pagosfacturas.importe_pagado)
  from "public".comercial_pagosfacturas
  inner join "public".comercial_pagos ON "public".comercial_pagos.id_pago = "public".comercial_pagosfacturas.pagos_id 
  where  "public".comercial_pagosfacturas.facturas_id = "public".comercial_facturas.doc_factura_id and "public".comercial_pagos.tipo_moneda_id = '2') as importe_pagado_cuc,
min("public".comercial_facturas.factura_nro) as factura_nro,
min("public".casco_doc.fecha_doc) as fecha_doc,
min("public".comercial_facturas.confirmada) as confirmada,
min(cast(date_part('day', now()-casco_doc.fecha_doc) as integer)) AS edad,
min(det.precio_cuc) AS precio_cuc,
min("public".comercial_facturas.doc_factura_id),
min("public".admincomerciax_cliente.nombre) as nombre
FROM
"public".comercial_facturas
INNER JOIN (select factura_id, Sum("public".comercial_detallefactura.precio_cuc) as precio_cuc
            from "public".comercial_detallefactura
            GROUP BY factura_id) as det on det.factura_id = "public".comercial_facturas.doc_factura_id
INNER JOIN "public".admincomerciax_cliente ON "public".comercial_facturas.cliente_id = "public".admincomerciax_cliente."id"
INNER JOIN casco_doc ON comercial_facturas.doc_factura_id = casco_doc.id_doc
WHERE "public".comercial_facturas.tipo!='A' 
GROUP BY
"public".comercial_facturas.doc_factura_id) as princ

full join 

(SELECT DISTINCT

 (select sum("public".comercial_pagosfacturas.importe_pagado)
  from "public".comercial_pagosfacturas
  inner join "public".comercial_pagos ON "public".comercial_pagos.id_pago = "public".comercial_pagosfacturas.pagos_id 
  where  "public".comercial_pagosfacturas.facturas_id = "public".comercial_facturas.doc_factura_id and "public".comercial_pagos.tipo_moneda_id = '1') as importe_pagado_cup,
min("public".comercial_facturas.factura_nro) as factura_nro,
min("public".casco_doc.fecha_doc) as fecha_doc,
min("public".comercial_facturas.confirmada) as confirmada1,
min(cast(date_part('day', now()-casco_doc.fecha_doc) as integer)) AS edad1,
min(det.precio_mn) AS precio_mn,
min("public".comercial_facturas.doc_factura_id),
min("public".admincomerciax_cliente.nombre) as nombre
FROM
"public".comercial_facturas
INNER JOIN (select factura_id, Sum("public".comercial_detallefactura.precio_mn) as precio_mn
            from "public".comercial_detallefactura
            GROUP BY factura_id) as det on det.factura_id = "public".comercial_facturas.doc_factura_id
INNER JOIN "public".admincomerciax_cliente ON "public".comercial_facturas.cliente_id = "public".admincomerciax_cliente."id"
INNER JOIN casco_doc ON comercial_facturas.doc_factura_id = casco_doc.id_doc           
WHERE  "public".comercial_facturas.tipo!='A' 
GROUP BY
"public".comercial_facturas.doc_factura_id)  as sec on princ.factura_nro = sec.factura_nro)