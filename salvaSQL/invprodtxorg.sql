         SELECT invprodtxorg_aux.siglas_organismo, 0 AS mayor, count(*) AS menor
           FROM invprodtxorg_aux
          WHERE invprodtxorg_aux.dias <= 45
          GROUP BY invprodtxorg_aux.siglas_organismo
UNION 
         SELECT invprodtxorg_aux.siglas_organismo, count(*) AS mayor, 0 AS menor
           FROM invprodtxorg_aux
          WHERE invprodtxorg_aux.dias >= 45
          GROUP BY invprodtxorg_aux.siglas_organismo;