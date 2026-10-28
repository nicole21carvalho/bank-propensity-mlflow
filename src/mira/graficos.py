"""Gráficos do relatório: curva de ganho e importância das variáveis."""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # sem janela: roda no CI e em servidor

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from mira.metricas import curva_de_ganho

NOMES = {
    "regra_de_segmento": "Regra de segmento (sem ML)",
    "regressao_logistica": "Regressão logística",
    "random_forest": "Random forest",
    "gradient_boosting": "Gradient boosting",
}
CORES = {
    "regra_de_segmento": "#94a3b8",
    "regressao_logistica": "#2563eb",
    "random_forest": "#16a34a",
    "gradient_boosting": "#c2410c",
}


def ganho(y: pd.Series, notas: dict[str, np.ndarray], destino: Path) -> Path:
    """Fração das contratações alcançada contatando os clientes da maior para a menor nota."""
    destino.parent.mkdir(parents=True, exist_ok=True)
    figura, eixo = plt.subplots(figsize=(7, 4.2), dpi=130)
    eixo.plot([0, 100], [0, 100], linestyle="--", color="#cbd5e1", label="Lista aleatória")
    for nome, nota in notas.items():
        x, alcance = curva_de_ganho(y, nota)
        eixo.plot(x * 100, alcance * 100, linewidth=2.2, color=CORES.get(nome), label=NOMES.get(nome, nome))
    captura = curva_de_ganho(y, notas[list(notas)[-1]])[1][20] * 100
    eixo.axvline(20, color="#e2e8f0", linewidth=1)
    eixo.annotate(
        f"{captura:.0f}% das contratações\nnos 20% de maior nota",
        xy=(20, captura),
        xytext=(32, captura - 18),
        arrowprops={"arrowstyle": "->", "color": "#475569"},
        fontsize=9,
        color="#334155",
    )
    eixo.set_xlabel("Clientes contatados, da maior para a menor nota (%)")
    eixo.set_ylabel("Contratações alcançadas (%)")
    eixo.set_xlim(0, 100)
    eixo.set_ylim(0, 100)
    eixo.grid(alpha=0.25)
    eixo.legend(loc="lower right", fontsize=9, frameon=False)
    eixo.spines[["top", "right"]].set_visible(False)
    figura.tight_layout()
    figura.savefig(destino)
    plt.close(figura)
    return destino


# Os nomes da base (em inglês) com o que cada um quer dizer, para o gráfico se explicar sozinho.
ROTULOS = {
    "contatado_antes": "Já foi contatado antes",
    "dias_desde_contato": "Dias desde o último contato",
    "month": "Mês do contato",
    "day_of_week": "Dia da semana do contato",
    "nr_employed": "Nº de empregados (economia)",
    "cons_price_idx": "Índice de preços ao consumidor",
    "cons_conf_idx": "Índice de confiança do consumidor",
    "emp_var_rate": "Variação do emprego",
    "euribor3m": "Euribor 3 meses (juros)",
    "poutcome": "Resultado da campanha anterior",
    "contact": "Canal (celular ou fixo)",
    "job": "Profissão",
    "age": "Idade",
    "campaign": "Ligações nesta campanha",
    "previous": "Contatos em campanhas anteriores",
    "education": "Escolaridade",
    "marital": "Estado civil",
    "default": "Crédito em atraso",
    "housing": "Financiamento imobiliário",
    "loan": "Empréstimo pessoal",
}


def importancia(ranking: pd.Series, destino: Path) -> Path:
    """Quanto a PR AUC cai quando cada variável é embaralhada (importância por permutação, no teste)."""
    destino.parent.mkdir(parents=True, exist_ok=True)
    ordenado = ranking.sort_values()
    figura, eixo = plt.subplots(figsize=(7, 4.2), dpi=130)
    rotulos = [ROTULOS.get(nome, nome) for nome in ordenado.index]
    eixo.barh(rotulos, ordenado.to_numpy(), color="#2563eb")
    eixo.set_xlabel("Queda da PR AUC ao embaralhar a variável")
    eixo.grid(axis="x", alpha=0.25)
    eixo.spines[["top", "right"]].set_visible(False)
    figura.tight_layout()
    figura.savefig(destino)
    plt.close(figura)
    return destino
