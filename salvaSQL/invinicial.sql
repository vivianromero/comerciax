        (SELECT casco_invalmacencasco.medida_id, casco_invalmacencasco.mes, casco_invalmacencasco.year, casco_invalmacencasco.almacen + casco_invalmacencasco.dvp + casco_invalmacencasco.dip + casco_invalmacencasco.er + casco_invalmacencasco.ree AS inicialcasco
                   FROM casco_invalmacencasco
        UNION ALL 
                 SELECT casco_invalmacenprod.medida_id, casco_invalmacenprod.mes, casco_invalmacenprod.year, casco_invalmacenprod.produccion AS inicialcasco
                   FROM casco_invalmacenprod)
UNION ALL 
         SELECT casco_invalmacenprodterm.medida_id, casco_invalmacenprodterm.mes, casco_invalmacenprodterm.year, casco_invalmacenprodterm.pt AS inicialcasco
           FROM casco_invalmacenprodterm;