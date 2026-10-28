import json
from pathlib import Path

import mlflow
import pandas as pd
import pytest

from mira.treino import EXPERIMENTO, RegraDeSegmento, escolher, treinar


@pytest.fixture(scope="module")
def tmp_path(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """Uma pasta para o módulo todo: o treino (o passo lento) roda uma vez só para todos os testes."""
    return tmp_path_factory.mktemp("treino")


@pytest.fixture(scope="module")
def resumo(clientes: pd.DataFrame, tmp_path: Path) -> dict:
    return treinar(clientes, raiz=tmp_path, dobras=3, salvar_graficos=True)


def test_registra_os_quatro_modelos_no_mlflow_e_marca_o_escolhido(resumo: dict, tmp_path: Path) -> None:
    mlflow.set_tracking_uri(f"sqlite:///{(tmp_path / 'mlflow.db').as_posix()}")
    todas = mlflow.search_runs(experiment_names=[EXPERIMENTO])
    comparacao = todas["tags.tipo"] == "comparacao"
    execucoes = todas[~comparacao]
    assert set(execucoes["tags.mlflow.runName"]) == set(resumo["modelos"])
    escolhidas = execucoes[execucoes["tags.escolhido"] == "sim"]
    assert list(escolhidas["tags.mlflow.runName"]) == [resumo["escolhido"]]
    assert (execucoes["tags.vazamento_removido"] == "duration").all()
    # A divisão aleatória fica registrada só como comparação, com o nome do modelo escolhido.
    assert list(todas[comparacao]["tags.mlflow.runName"]) == [f"{resumo['escolhido']}_divisao_aleatoria"]
    assert set(resumo["divisao_aleatoria"]) >= {"roc_auc", "pr_auc", "captura_top20"}


def test_o_escolhido_vem_da_validacao_e_nao_do_teste(resumo: dict) -> None:
    validacao = {nome: m["pr_auc_validacao"] for nome, m in resumo["modelos"].items()}
    assert resumo["escolhido"] == escolher(validacao)


def test_quem_valida_melhor_ganha() -> None:
    assert escolher({"regressao_logistica": 0.50, "random_forest": 0.60}) == "random_forest"


def test_no_empate_tecnico_fica_o_mais_simples() -> None:
    validacao = {"regressao_logistica": 0.0849, "random_forest": 0.0850, "gradient_boosting": 0.07}
    assert escolher(validacao) == "regressao_logistica"


def test_modelos_aprendem_o_padrao_dos_dados_sinteticos(resumo: dict) -> None:
    for nome, metricas in resumo["modelos"].items():
        assert metricas["roc_auc"] > 0.6, nome
        assert 0 <= metricas["captura_top20"] <= 1


def test_gera_os_graficos_e_o_resumo(resumo: dict, tmp_path: Path) -> None:
    assert (tmp_path / "docs" / "img" / "curva-de-ganho.png").stat().st_size > 0
    assert (tmp_path / "docs" / "img" / "importancia.png").stat().st_size > 0
    salvo = json.loads((tmp_path / "docs" / "resultados.json").read_text(encoding="utf-8"))
    assert salvo["escolhido"] == resumo["escolhido"]
    assert "duration" not in salvo["importancia"]


def test_regra_de_segmento_usa_a_taxa_geral_para_segmento_novo(clientes: pd.DataFrame) -> None:
    regra = RegraDeSegmento().fit(clientes, clientes["contratou"])
    novo = clientes.head(1).assign(poutcome="nunca-visto")
    assert regra.predict_proba(novo)[0, 1] == pytest.approx(clientes["contratou"].mean())
