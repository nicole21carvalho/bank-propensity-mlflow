# Exploração em SQL

Cada seção é uma consulta de [`sql/`](../sql) rodada na tabela `clientes` (SQLite). Gerado por `uv run mira-explorar`.

## Quantos clientes foram contatados e quantos contrataram: a linha de base de qualquer modelo.

[`01_taxa_geral.sql`](../sql/01_taxa_geral.sql)

| clientes | contrataram | taxa_pct |
|---|---|---|
| 41188 | 4640 | 11.3 |

## Quem já contratou numa campanha anterior volta a contratar?

[`02_campanha_anterior.sql`](../sql/02_campanha_anterior.sql)

| resultado_anterior | clientes | taxa_pct |
|---|---|---|
| success | 1373 | 65.1 |
| failure | 4252 | 14.2 |
| nonexistent | 35563 | 8.8 |

## Insistir funciona? Taxa de contratação pelo número de ligações nesta campanha.

[`03_numero_de_contatos.sql`](../sql/03_numero_de_contatos.sql)

| ligacoes | clientes | taxa_pct |
|---|---|---|
| 1 | 17642 | 13.0 |
| 2 | 10570 | 11.5 |
| 3 | 5341 | 10.7 |
| 4 a 5 | 4250 | 8.7 |
| 6 ou mais | 3385 | 5.5 |

## Em que idade a oferta pega melhor?

[`04_faixa_etaria.sql`](../sql/04_faixa_etaria.sql)

| faixa_etaria | clientes | taxa_pct |
|---|---|---|
| até 24 | 1068 | 24.0 |
| 25 a 34 | 13686 | 12.2 |
| 35 a 44 | 13500 | 8.7 |
| 45 a 59 | 11741 | 9.2 |
| 60 ou mais | 1193 | 39.6 |

## Celular ou telefone fixo?

[`05_canal.sql`](../sql/05_canal.sql)

| canal | clientes | taxa_pct |
|---|---|---|
| cellular | 26144 | 14.7 |
| telephone | 15044 | 5.2 |

## O cenário econômico pesa? Taxa de contratação pela Euribor de 3 meses no dia do contato.

[`06_juros_e_contratacao.sql`](../sql/06_juros_e_contratacao.sql)

| euribor_3m | clientes | taxa_pct |
|---|---|---|
| abaixo de 1% | 3890 | 45.7 |
| 1% a 3% | 9608 | 15.9 |
| 3% ou mais | 27690 | 4.8 |
