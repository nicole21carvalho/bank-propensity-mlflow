"""Base Bank Marketing (UCI): download conferido por SHA-256, leitura e cópia num banco SQLite.

Moro, S., Rita, P. e Cortez, P. (2014). Bank Marketing. UCI Machine Learning Repository.
https://doi.org/10.24432/C5K306 · licença CC BY 4.0.
"""

import hashlib
import io
import sqlite3
import urllib.request
import zipfile
from pathlib import Path

import pandas as pd

URL = "https://archive.ics.uci.edu/static/public/222/bank+marketing.zip"
SHA256 = "e0bf5f5de5b846e2f18e9d90606637267d46dfa260e0f17bb12e605db5efbeb4"
ARQUIVO_INTERNO = ("bank-additional.zip", "bank-additional/bank-additional-full.csv")

PASTA_DADOS = Path(__file__).resolve().parents[2] / "dados"
ZIP_PADRAO = PASTA_DADOS / "bank+marketing.zip"
SQLITE_PADRAO = PASTA_DADOS / "clientes.sqlite"

# Nomes sem ponto: viram colunas de tabela SQL sem aspas.
RENOMEAR = {
    "emp.var.rate": "emp_var_rate",
    "cons.price.idx": "cons_price_idx",
    "cons.conf.idx": "cons_conf_idx",
    "nr.employed": "nr_employed",
}


class ArquivoAlterado(Exception):
    """O arquivo baixado não é o que este projeto conferiu: outro conteúdo, outros resultados."""


def baixar(destino: Path = ZIP_PADRAO) -> Path:
    """Baixa a base (se ainda não estiver aqui) e confere o SHA-256 antes de usar."""
    if not destino.exists():
        destino.parent.mkdir(parents=True, exist_ok=True)
        with urllib.request.urlopen(URL, timeout=60) as resposta:
            destino.write_bytes(resposta.read())
    obtido = hashlib.sha256(destino.read_bytes()).hexdigest()
    if obtido != SHA256:
        raise ArquivoAlterado(
            f"SHA-256 {obtido} diferente do esperado {SHA256}: apague {destino} e baixe de novo"
        )
    return destino


def carregar(zip_externo: Path = ZIP_PADRAO) -> pd.DataFrame:
    """Lê as 41.188 ligações, em ordem de data (maio de 2008 a novembro de 2010), como estão no arquivo."""
    externo, interno = ARQUIVO_INTERNO
    with zipfile.ZipFile(baixar(zip_externo)) as z, zipfile.ZipFile(io.BytesIO(z.read(externo))) as zi:
        df = pd.read_csv(io.BytesIO(zi.read(interno)), sep=";")
    df = df.rename(columns=RENOMEAR)
    # A ordem do arquivo é a ordem do tempo: guardar a posição permite dividir treino e teste por data.
    df.insert(0, "ordem", range(len(df)))
    df["contratou"] = (df.pop("y") == "yes").astype(int)
    return df


def para_sqlite(df: pd.DataFrame, caminho: Path = SQLITE_PADRAO) -> Path:
    """Grava a tabela `clientes` num SQLite, para a exploração em SQL."""
    caminho.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(caminho) as conexao:
        df.to_sql("clientes", conexao, if_exists="replace", index=False)
    return caminho
