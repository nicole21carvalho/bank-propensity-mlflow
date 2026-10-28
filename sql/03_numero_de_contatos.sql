-- Insistir funciona? Taxa de contratação pelo número de ligações nesta campanha.
SELECT
    CASE
        WHEN campaign = 1 THEN '1'
        WHEN campaign = 2 THEN '2'
        WHEN campaign = 3 THEN '3'
        WHEN campaign <= 5 THEN '4 a 5'
        ELSE '6 ou mais'
    END                              AS ligacoes,
    COUNT(*)                         AS clientes,
    ROUND(100.0 * AVG(contratou), 1) AS taxa_pct
FROM clientes
GROUP BY ligacoes
ORDER BY MIN(campaign);
