-- O cenário econômico pesa? Taxa de contratação pela Euribor de 3 meses no dia do contato.
SELECT
    CASE
        WHEN euribor3m < 1 THEN 'abaixo de 1%'
        WHEN euribor3m < 3 THEN '1% a 3%'
        ELSE '3% ou mais'
    END                              AS euribor_3m,
    COUNT(*)                         AS clientes,
    ROUND(100.0 * AVG(contratou), 1) AS taxa_pct
FROM clientes
GROUP BY euribor_3m
ORDER BY MIN(euribor3m);
