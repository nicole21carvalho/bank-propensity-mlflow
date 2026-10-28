-- Celular ou telefone fixo?
SELECT
    contact                          AS canal,
    COUNT(*)                         AS clientes,
    ROUND(100.0 * AVG(contratou), 1) AS taxa_pct
FROM clientes
GROUP BY contact
ORDER BY taxa_pct DESC;
