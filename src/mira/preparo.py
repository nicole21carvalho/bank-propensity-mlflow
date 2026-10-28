"""Do arquivo às variáveis do modelo, sem deixar a resposta vazar para dentro delas."""

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder, StandardScaler

ALVO = "contratou"

# `duration` é a duração da ligação: só existe depois de ligar, e quem fica muito tempo na linha quase sempre
# contrata. Com ela o modelo "acerta" sem servir para nada (a própria UCI recomenda descartar).
VAZAMENTO = ["duration"]

CATEGORICAS = [
    "job",
    "marital",
    "education",
    "default",
    "housing",
    "loan",
    "contact",
    "month",
    "day_of_week",
    "poutcome",
]
NUMERICAS = [
    "age",
    "campaign",
    "previous",
    "emp_var_rate",
    "cons_price_idx",
    "cons_conf_idx",
    "euribor3m",
    "nr_employed",
    "contatado_antes",
    "dias_desde_contato",
]

# pdays = 999 quer dizer "nunca contatado antes": não é um número de dias, é outra informação.
NUNCA_CONTATADO = 999


def criar_variaveis(df: pd.DataFrame) -> pd.DataFrame:
    """Variáveis que um analista criaria antes de ligar para o cliente, nada que dependa da ligação."""
    saida = df.drop(columns=VAZAMENTO, errors="ignore").copy()
    nunca = saida["pdays"] == NUNCA_CONTATADO
    saida["contatado_antes"] = (~nunca).astype(int)
    # Sem contato anterior não há "dias desde": 0 com a marca acima, e não 999 puxando a escala.
    saida["dias_desde_contato"] = np.where(nunca, 0, saida["pdays"])
    return saida.drop(columns=["pdays"])


def separar_por_data(df: pd.DataFrame, fracao_teste: float = 0.2) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Treino com o passado, teste com o futuro: o modelo é julgado como seria usado, nas campanhas seguintes.

    Uma divisão aleatória misturaria ligações de 2010 no treino de um modelo avaliado em 2008.
    """
    ordenado = df.sort_values("ordem")
    corte = int(len(ordenado) * (1 - fracao_teste))
    return ordenado.iloc[:corte], ordenado.iloc[corte:]


def separar_x_y(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series]:
    return df[CATEGORICAS + NUMERICAS], df[ALVO]


def preprocessador(escalar: bool) -> ColumnTransformer:
    """One-hot nas categorias; padronização nos números quando o modelo é sensível à escala (regressão)."""
    numericas = StandardScaler() if escalar else "passthrough"
    return ColumnTransformer(
        [
            # Saída densa: o gradient boosting do scikit-learn não aceita matriz esparsa (são ~60 colunas).
            (
                "categoricas",
                OneHotEncoder(handle_unknown="ignore", min_frequency=20, sparse_output=False),
                CATEGORICAS,
            ),
            ("numericas", numericas, NUMERICAS),
        ],
        verbose_feature_names_out=False,
    )
