"""Roda as consultas de `sql/` no SQLite e gera `docs/exploracao.md` com cada pergunta e a resposta."""

import sqlite3
from pathlib import Path

import pandas as pd

from mira.dados import SQLITE_PADRAO, carregar, para_sqlite

RAIZ = Path(__file__).resolve().parents[2]
PASTA_SQL = RAIZ / "sql"
RELATORIO = RAIZ / "docs" / "exploracao.md"


def tabela_markdown(df: pd.DataFrame) -> str:
    """Tabela Markdown simples (o `to_markdown` do pandas exigiria mais uma dependência)."""
    cabecalho = "| " + " | ".join(map(str, df.columns)) + " |"
    separador = "|" + "---|" * len(df.columns)
    linhas = ["| " + " | ".join(map(str, linha)) + " |" for linha in df.itertuples(index=False)]
    return "\n".join([cabecalho, separador, *linhas])


def rodar(caminho_sqlite: Path = SQLITE_PADRAO) -> list[tuple[str, str, pd.DataFrame]]:
    """(arquivo, pergunta, resultado) de cada consulta, na ordem dos arquivos."""
    resultados = []
    with sqlite3.connect(caminho_sqlite) as conexao:
        for arquivo in sorted(PASTA_SQL.glob("*.sql")):
            consulta = arquivo.read_text(encoding="utf-8")
            pergunta = consulta.splitlines()[0].removeprefix("--").strip()
            resultados.append((arquivo.name, pergunta, pd.read_sql_query(consulta, conexao)))
    return resultados


def main() -> None:
    caminho = para_sqlite(carregar())
    partes = [
        "# Exploração em SQL\n",
        "Cada seção é uma consulta de [`sql/`](../sql) rodada na tabela `clientes` (SQLite). "
        "Gerado por `uv run mira-explorar`.\n",
    ]
    for arquivo, pergunta, tabela in rodar(caminho):
        partes.append(f"## {pergunta}\n\n[`{arquivo}`](../sql/{arquivo})\n\n{tabela_markdown(tabela)}\n")
        print(f"\n{pergunta}\n{tabela.to_string(index=False)}")
    RELATORIO.parent.mkdir(parents=True, exist_ok=True)
    RELATORIO.write_text("\n".join(partes), encoding="utf-8")
    print(f"\nRelatório: {RELATORIO}")


if __name__ == "__main__":
    main()
