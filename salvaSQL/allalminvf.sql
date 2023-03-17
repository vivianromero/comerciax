 SELECT *
 FROM 
      public.allalminvfaux

UNION ALL

    SELECT
          'Total' as "medida" ,
      SUM(allalminvfaux."Casco"),
      SUM(allalminvfaux."DIP"),
      SUM(allalminvfaux."DVP"),
      SUM(allalminvfaux."ER"),
      SUM(allalminvfaux."REE"),
      SUM(allalminvfaux."Produccion"),
      SUM(allalminvfaux."ProduccionT")
    FROM 
      public.allalminvfaux
