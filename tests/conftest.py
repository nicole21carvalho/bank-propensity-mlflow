"""Dados sintéticos com o mesmo formato da base da UCI: testes rápidos e sem internet."""

import numpy as np
import pandas as pd
import pytest

from mira.preparo import CATEGORICAS

VALORES = {
    "job": ["admin.", "blue-collar", "technician", "retired", "student"],
    "marital": ["married", "single", "divorced"],
    "education": ["high.school", "university.degree", "basic.9y"],
    "default": ["no", "unknown"],
    "housing": ["no", "yes"],
    "loan": ["no", "yes"],
    "contact": ["cellular", "telephone"],
    "month": ["may", "jun", "jul", "aug", "nov"],
    "day_of_week": ["mon", "tue", "wed", "thu", "fri"],
    "poutcome": ["nonexistent", "failure", "success"],
}


@pytest.fixture(scope="session")
def clientes() -> pd.DataFrame:
    """1.200 clientes em ordem de data; quem teve sucesso antes e foi contatado por celular contrata mais."""
    gerador = np.random.default_rng(7)
    n = 1200
    df = pd.DataFrame({coluna: gerador.choice(VALORES[coluna], n) for coluna in CATEGORICAS})
    df.insert(0, "ordem", range(n))
    df["age"] = gerador.integers(18, 90, n)
    df["duration"] = gerador.integers(0, 2000, n)
    df["campaign"] = gerador.integers(1, 10, n)
    df["pdays"] = np.where(df["poutcome"] == "nonexistent", 999, gerador.integers(0, 30, n))
    df["previous"] = np.where(df["poutcome"] == "nonexistent", 0, gerador.integers(1, 5, n))
    df["emp_var_rate"] = gerador.normal(0, 1.5, n)
    df["cons_price_idx"] = gerador.normal(93.5, 0.5, n)
    df["cons_conf_idx"] = gerador.normal(-40, 4, n)
    df["euribor3m"] = gerador.uniform(0.6, 5, n)
    df["nr_employed"] = gerador.normal(5150, 60, n)
    chance = 0.05 + 0.5 * (df["poutcome"] == "success") + 0.1 * (df["contact"] == "cellular")
    df["contratou"] = (gerador.uniform(0, 1, n) < chance).astype(int)
    return df
