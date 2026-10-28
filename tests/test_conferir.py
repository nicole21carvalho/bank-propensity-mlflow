from mira.conferir import diferencas

ESPERADO = {"escolhido": "a", "modelos": {"a": {"pr_auc": 0.50, "descricao": "x"}, "b": {"pr_auc": 0.40}}}


def test_variacao_pequena_entre_sistemas_passa() -> None:
    obtido = {"escolhido": "a", "modelos": {"a": {"pr_auc": 0.505, "descricao": "y"}, "b": {"pr_auc": 0.399}}}
    assert diferencas(ESPERADO, obtido) == []


def test_metrica_que_mudou_de_verdade_e_apontada() -> None:
    obtido = {"escolhido": "a", "modelos": {"a": {"pr_auc": 0.45}, "b": {"pr_auc": 0.40}}}
    assert diferencas(ESPERADO, obtido) == ["a.pr_auc: 0.5 -> 0.45"]


def test_troca_do_modelo_escolhido_e_apontada() -> None:
    obtido = {"escolhido": "b", "modelos": ESPERADO["modelos"]}
    assert "modelo escolhido mudou: a -> b" in diferencas(ESPERADO, obtido)
