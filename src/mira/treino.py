"""Treina e compara os modelos, registrando cada um no MLflow, e escolhe o melhor sem olhar o teste.

Uso: uv run mira-treinar   (depois: uv run mlflow ui --backend-store-uri sqlite:///mlflow.db)
"""

import json
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import mlflow
import mlflow.sklearn
import numpy as np
import pandas as pd
import sklearn
from sklearn.base import BaseEstimator, ClassifierMixin
from sklearn.ensemble import HistGradientBoostingClassifier, RandomForestClassifier
from sklearn.inspection import permutation_importance
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, brier_score_loss, roc_auc_score
from sklearn.model_selection import TimeSeriesSplit, train_test_split
from sklearn.pipeline import Pipeline

from mira import graficos
from mira.dados import carregar
from mira.metricas import captura_no_topo, lift_no_topo
from mira.preparo import (
    ALVO,
    CATEGORICAS,
    NUMERICAS,
    criar_variaveis,
    preprocessador,
    separar_por_data,
    separar_x_y,
)

RAIZ = Path(__file__).resolve().parents[2]
EXPERIMENTO = "mira-propensao"
SEMENTE = 42
# Diferença de PR AUC na validação abaixo da qual dois modelos contam como empatados.
EMPATE = 0.005
# O que o modelo salvo precisa para rodar em outro lugar. Declarado aqui em vez de o MLflow adivinhar
# importando o ambiente inteiro (lento e, sem pip no ambiente do uv, impreciso).
REQUISITOS = [f"scikit-learn=={sklearn.__version__}", f"pandas=={pd.__version__}", f"numpy=={np.__version__}"]
# O MLflow salva o modelo com skops, que só carrega tipos declarados confiáveis. Estes dois são as árvores
# da random forest e do gradient boosting, treinadas aqui mesmo; nenhum outro tipo é liberado.
TIPOS_CONFIAVEIS = [
    "sklearn.tree._tree.Tree",
    "sklearn.ensemble._hist_gradient_boosting.predictor.TreePredictor",
]


class RegraDeSegmento(ClassifierMixin, BaseEstimator):
    """Linha de base sem ML: a nota de cada cliente é a taxa histórica de contratação do seu segmento.

    Segmento = resultado da campanha anterior x canal x faixa de juros. É o que uma área comercial faria numa
    planilha. Se o modelo não ganhar disto com folga, não vale o custo de manter um modelo.
    """

    def _segmento(self, x: pd.DataFrame) -> pd.Series:
        juros = pd.cut(x["euribor3m"], [-np.inf, 1, 3, np.inf], labels=["baixo", "medio", "alto"])
        return x["poutcome"].astype(str) + "|" + x["contact"].astype(str) + "|" + juros.astype(str)

    def fit(self, x: pd.DataFrame, y: pd.Series) -> RegraDeSegmento:
        segmentos = self._segmento(x)
        self.taxa_por_segmento_ = y.groupby(segmentos.values).mean().to_dict()
        self.taxa_geral_ = float(y.mean())
        self.classes_ = np.array([0, 1])
        return self

    def predict_proba(self, x: pd.DataFrame) -> np.ndarray:
        taxa = self._segmento(x).map(self.taxa_por_segmento_).fillna(self.taxa_geral_).to_numpy(dtype=float)
        return np.column_stack([1 - taxa, taxa])

    def predict(self, x: pd.DataFrame) -> np.ndarray:
        return (self.predict_proba(x)[:, 1] >= 0.5).astype(int)


@dataclass(frozen=True)
class Candidato:
    nome: str
    descricao: str
    criar: Any  # () -> estimador novo
    parametros: dict[str, Any]


def candidatos() -> list[Candidato]:
    logistica = {"C": 0.5, "max_iter": 3000}
    floresta = {"n_estimators": 300, "min_samples_leaf": 20, "max_features": "sqrt"}
    boosting = {"learning_rate": 0.05, "max_iter": 300, "max_leaf_nodes": 15, "l2_regularization": 1.0}
    return [
        Candidato("regra_de_segmento", "Taxa histórica do segmento (sem ML)", RegraDeSegmento, {}),
        Candidato(
            "regressao_logistica",
            "Regressão logística com variáveis padronizadas",
            lambda: Pipeline(
                [("preparo", preprocessador(escalar=True)), ("modelo", LogisticRegression(**logistica))]
            ),
            logistica,
        ),
        Candidato(
            "random_forest",
            "Floresta aleatória",
            lambda: Pipeline(
                [
                    ("preparo", preprocessador(escalar=False)),
                    ("modelo", RandomForestClassifier(**floresta, n_jobs=-1, random_state=SEMENTE)),
                ]
            ),
            floresta,
        ),
        Candidato(
            "gradient_boosting",
            "Gradient boosting por histogramas",
            lambda: Pipeline(
                [
                    ("preparo", preprocessador(escalar=False)),
                    ("modelo", HistGradientBoostingClassifier(**boosting, random_state=SEMENTE)),
                ]
            ),
            boosting,
        ),
    ]


def avaliar(y: pd.Series, nota: np.ndarray) -> dict[str, float]:
    """Ordenação (AUCs), calibração (Brier) e o que importa para a campanha (captura e lift no topo)."""
    return {
        "roc_auc": roc_auc_score(y, nota),
        "pr_auc": average_precision_score(y, nota),
        "brier": brier_score_loss(y, nota),
        "captura_top10": captura_no_topo(y, nota, 0.10),
        "captura_top20": captura_no_topo(y, nota, 0.20),
        "lift_top10": lift_no_topo(y, nota, 0.10),
    }


def validacao_temporal(candidato: Candidato, x: pd.DataFrame, y: pd.Series, dobras: int = 5) -> float:
    """PR AUC média em janelas que avançam no tempo, só com o treino: é por ela que o modelo é escolhido."""
    resultados = []
    for indice_treino, indice_validacao in TimeSeriesSplit(n_splits=dobras).split(x):
        y_validacao = y.iloc[indice_validacao]
        if y_validacao.nunique() < 2:
            continue
        modelo = candidato.criar().fit(x.iloc[indice_treino], y.iloc[indice_treino])
        resultados.append(
            average_precision_score(y_validacao, modelo.predict_proba(x.iloc[indice_validacao])[:, 1])
        )
    return float(np.mean(resultados))


def escolher(validacao: dict[str, float], empate: float = EMPATE) -> str:
    """O de melhor validação; num empate técnico (diferença menor que `empate`), o mais simples deles.

    Parcimônia: entre modelos que acertam igual, o mais simples é mais fácil de explicar, de manter e de
    auditar, e a escolha não vira por uma diferença de arredondamento entre computadores.
    """
    melhor = max(validacao.values())
    empatados = [nome for nome in validacao if melhor - validacao[nome] < empate]
    return min(empatados, key=lambda nome: [c.nome for c in candidatos()].index(nome))


def comparar_com_divisao_aleatoria(candidato: Candidato, df: pd.DataFrame) -> dict[str, float]:
    """O mesmo modelo julgado com treino e teste sorteados, como em muito tutorial: quanto o número engana.

    Fica registrado no MLflow só como comparação; não participa da escolha do modelo.
    """
    treino, teste = train_test_split(
        criar_variaveis(df), test_size=0.2, random_state=SEMENTE, stratify=df[ALVO]
    )
    x_treino, y_treino = separar_x_y(treino)
    x_teste, y_teste = separar_x_y(teste)
    metricas = avaliar(y_teste, candidato.criar().fit(x_treino, y_treino).predict_proba(x_teste)[:, 1])
    with mlflow.start_run(run_name=f"{candidato.nome}_divisao_aleatoria"):
        mlflow.set_tags(
            {"tipo": "comparacao", "divisao": "aleatoria (otimista: o teste mistura passado e futuro)"}
        )
        mlflow.log_metrics(metricas)
    return {k: round(float(v), 4) for k, v in metricas.items()}


def configurar_mlflow(raiz: Path) -> str:
    mlflow.set_tracking_uri(f"sqlite:///{(raiz / 'mlflow.db').as_posix()}")
    if mlflow.get_experiment_by_name(EXPERIMENTO) is None:
        mlflow.create_experiment(EXPERIMENTO, artifact_location=(raiz / "mlartifacts").as_uri())
    mlflow.set_experiment(EXPERIMENTO)
    return EXPERIMENTO


def treinar(
    df: pd.DataFrame, raiz: Path = RAIZ, dobras: int = 5, salvar_graficos: bool = True
) -> dict[str, Any]:
    configurar_mlflow(raiz)
    treino, teste = separar_por_data(criar_variaveis(df))
    x_treino, y_treino = separar_x_y(treino)
    x_teste, y_teste = separar_x_y(teste)
    contexto = {
        "clientes_treino": len(treino),
        "clientes_teste": len(teste),
        "taxa_treino": round(float(y_treino.mean()), 4),
        "taxa_teste": round(float(y_teste.mean()), 4),
    }

    resultados: dict[str, dict[str, Any]] = {}
    execucoes: dict[str, str] = {}  # run_id do MLflow: muda a cada treino, por isso fica fora do resumo salvo
    notas: dict[str, np.ndarray] = {}
    modelos: dict[str, Any] = {}
    for candidato in candidatos():
        with mlflow.start_run(run_name=candidato.nome) as execucao:
            mlflow.set_tags(
                {
                    "descricao": candidato.descricao,
                    "divisao": "temporal: treino = 80% mais antigos, teste = 20% mais recentes",
                    "vazamento_removido": "duration",
                }
            )
            mlflow.log_params({**candidato.parametros, "variaveis": len(CATEGORICAS) + len(NUMERICAS)})
            pr_auc_validacao = validacao_temporal(candidato, x_treino, y_treino, dobras)
            modelo = candidato.criar().fit(x_treino, y_treino)
            nota = modelo.predict_proba(x_teste)[:, 1]
            metricas = {"pr_auc_validacao": pr_auc_validacao, **avaliar(y_teste, nota)}
            mlflow.log_metrics(metricas)
            if salvar_graficos:
                with tempfile.TemporaryDirectory() as pasta:
                    mlflow.log_artifact(
                        str(graficos.ganho(y_teste, {candidato.nome: nota}, Path(pasta) / "ganho.png"))
                    )
            if isinstance(modelo, Pipeline):
                mlflow.sklearn.log_model(
                    modelo,
                    name="modelo",
                    input_example=x_teste.head(3),
                    pip_requirements=REQUISITOS,
                    skops_trusted_types=TIPOS_CONFIAVEIS,
                )
            resultados[candidato.nome] = {
                "descricao": candidato.descricao,
                **{k: round(float(v), 4) for k, v in metricas.items()},
            }
            execucoes[candidato.nome] = execucao.info.run_id
            notas[candidato.nome] = nota
            modelos[candidato.nome] = modelo
            print(
                f"{candidato.nome:22s} validação PR AUC {pr_auc_validacao:.3f} | teste "
                + " ".join(f"{k}={v:.3f}" for k, v in metricas.items() if k != "pr_auc_validacao")
            )

    # Escolha pela validação no passado; o teste só confirma (escolher pelo teste seria se enganar).
    melhor = escolher({nome: m["pr_auc_validacao"] for nome, m in resultados.items()})
    with mlflow.start_run(run_id=execucoes[melhor]):
        mlflow.set_tag("escolhido", "sim")

    comparacao = comparar_com_divisao_aleatoria(next(c for c in candidatos() if c.nome == melhor), df)

    importancias = permutation_importance(
        modelos[melhor],
        x_teste,
        y_teste,
        scoring="average_precision",
        n_repeats=5,
        random_state=SEMENTE,
        n_jobs=1,
    )
    ranking = (
        pd.Series(importancias.importances_mean, index=x_teste.columns).sort_values(ascending=False).head(10)
    )
    if salvar_graficos:
        pasta = raiz / "docs" / "img"
        graficos.ganho(
            y_teste, {n: notas[n] for n in ("regra_de_segmento", melhor)}, pasta / "curva-de-ganho.png"
        )
        graficos.importancia(ranking, pasta / "importancia.png")

    resumo = {
        "contexto": contexto,
        "escolhido": melhor,
        "modelos": resultados,
        "divisao_aleatoria": comparacao,
        "importancia": ranking.round(4).to_dict(),
    }
    (raiz / "docs").mkdir(exist_ok=True)
    (raiz / "docs" / "resultados.json").write_text(
        json.dumps(resumo, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    return resumo


def main() -> None:
    resumo = treinar(carregar())
    c = resumo["contexto"]
    print(
        f"\nTreino: {c['clientes_treino']} clientes ({c['taxa_treino']:.1%} contrataram) | "
        f"teste: {c['clientes_teste']} ({c['taxa_teste']:.1%})"
    )
    print(f"Escolhido pela validação temporal: {resumo['escolhido']}")


if __name__ == "__main__":
    main()
