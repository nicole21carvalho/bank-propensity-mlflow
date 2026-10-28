-- Em que idade a oferta pega melhor?
SELECT
    CASE
        WHEN age < 25 THEN 'até 24'
        WHEN age < 35 THEN '25 a 34'
        WHEN age < 45 THEN '35 a 44'
        WHEN age < 60 THEN '45 a 59'
        ELSE '60 ou mais'
    END                              AS faixa_etaria,
    COUNT(*)                         AS clientes,
    ROUND(100.0 * AVG(contratou), 1) AS taxa_pct
FROM clientes
GROUP BY faixa_etaria
ORDER BY MIN(age);
