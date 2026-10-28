import numpy as np
import pytest

from mira.metricas import captura_no_topo, curva_de_ganho, lift_no_topo

Y = np.array([1, 0, 0, 1, 0, 0, 0, 0, 0, 0])


def test_modelo_perfeito_captura_tudo_no_topo() -> None:
    nota = Y.astype(float)
    assert captura_no_topo(Y, nota, 0.2) == 1.0
    assert lift_no_topo(Y, nota, 0.2) == pytest.approx(5.0)


def test_nota_invertida_nao_captura_nada_no_topo() -> None:
    assert captura_no_topo(Y, 1 - Y, 0.2) == 0.0


def test_metade_no_topo() -> None:
    nota = np.array([0.9, 0.8, 0.1, 0.2, 0.3, 0.1, 0.1, 0.1, 0.1, 0.1])
    assert captura_no_topo(Y, nota, 0.2) == 0.5


def test_sem_contratacao_nenhuma_a_captura_e_zero() -> None:
    assert captura_no_topo(np.zeros(5), np.arange(5), 0.4) == 0.0


def test_curva_de_ganho_vai_de_zero_a_um_sem_descer() -> None:
    x, alcance = curva_de_ganho(Y, np.linspace(1, 0, len(Y)), pontos=11)
    assert alcance[0] == 0.0
    assert alcance[-1] == 1.0
    assert np.all(np.diff(alcance) >= 0)
    assert len(x) == 11
