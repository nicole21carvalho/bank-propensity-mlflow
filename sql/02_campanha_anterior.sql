-- Quem já contratou numa campanha anterior volta a contratar?
SELECT
    poutcome                         AS resultado_anterior,
    COUNT(*)                         AS clientes,
    ROUND(100.0 * AVG(contratou), 1) AS taxa_pct
FROM clientes
GROUP BY poutcome
ORDER BY taxa_pct DESC;
