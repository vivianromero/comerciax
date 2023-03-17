 SELECT 
      admincomerciax_contrato.contrato_nro, 
      admincomerciax_cliente.id, 
      admincomerciax_cliente.codigo, 
      admincomerciax_cliente.nombre, 
      admincomerciax_contrato.fecha_vigencia, 
      admincomerciax_contrato.fecha_vencimiento, 
      admincomerciax_contrato.cerrado, 
      admincomerciax_contrato.preciomn, 
      admincomerciax_contrato.preciocostomn, 
      admincomerciax_contrato.preciocuc, 
      admincomerciax_contrato.preciocostocuc, 
      admincomerciax_contrato.para_la_venta, 
      date_part('day'::text, admincomerciax_contrato.fecha_vencimiento::timestamp with time zone - now())::integer AS dias
   FROM admincomerciax_contrato, admincomerciax_cliente
   WHERE admincomerciax_cliente.id::text = admincomerciax_contrato.cliente_id::text;                          