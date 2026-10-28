"""Métricas que o time comercial entende: quanto das contratações a lista de oferta alcança."""

import numpy as np
from numpy.typing import ArrayLike


def _ordenar(y: ArrayLike, nota: ArrayLike) -> np.ndarray:
    """O alvo na ordem da nota, da maior para a menor (empates mantêm a ordem original)."""
    y_arr = np.asarray(y)
    ordem = np.argsort(-np.asarray(nota, dtype=float), kind="stable")
    return y_arr[ordem]


def captura_no_topo(y: ArrayLike, nota: ArrayLike, fracao: float) -> float:
    """Que parte de todas as contratações está entre os `fracao` clientes com maior nota.

    Com fracao=0.2: "oferecendo só para os 20% de maior nota, alcançamos X% de quem contrataria".
    Sem modelo (lista aleatória), a captura esperada é a própria fração.
    """
    ordenado = _ordenar(y, nota)
    total = ordenado.sum()
    if total == 0:
        return 0.0
    topo = max(1, round(len(ordenado) * fracao))
    return float(ordenado[:topo].sum() / total)


def lift_no_topo(y: ArrayLike, nota: ArrayLike, fracao: float) -> float:
    """Quantas vezes a taxa de contratação do topo supera a taxa geral (1,0 = igual a escolher ao acaso)."""
    return captura_no_topo(y, nota, fracao) / fracao


def curva_de_ganho(y: ArrayLike, nota: ArrayLike, pontos: int = 101) -> tuple[np.ndarray, np.ndarray]:
    """Fração de clientes contatados (x) contra fração das contratações alcançadas (y)."""
    ordenado = _ordenar(y, nota)
    acumulado = np.concatenate([[0], np.cumsum(ordenado)]) / max(1, ordenado.sum())
    x = np.linspace(0, 1, pontos)
    indices = np.round(x * len(ordenado)).astype(int)
    return x, acumulado[indices]
