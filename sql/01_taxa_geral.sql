-- Quantos clientes foram contatados e quantos contrataram: a linha de base de qualquer modelo.
SELECT
    COUNT(*)                         AS clientes,
    SUM(contratou)                   AS contrataram,
    ROUND(100.0 * AVG(contratou), 1) AS taxa_pct
FROM clientes;
