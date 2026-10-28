import pandas as pd

from mira.preparo import NUMERICAS, VAZAMENTO, criar_variaveis, preprocessador, separar_por_data, separar_x_y


def test_a_duracao_da_ligacao_nunca_chega_ao_modelo(clientes: pd.DataFrame) -> None:
    preparado = criar_variaveis(clientes)
    x, _ = separar_x_y(preparado)
    assert not set(VAZAMENTO) & set(preparado.columns)
    assert "duration" not in x.columns
    assert "contratou" not in x.columns


def test_999_em_pdays_vira_nunca_contatado_e_nao_999_dias(clientes: pd.DataFrame) -> None:
    preparado = criar_variaveis(clientes)
    nunca = clientes["pdays"] == 999
    assert (preparado.loc[nunca, "contatado_antes"] == 0).all()
    assert (preparado.loc[nunca, "dias_desde_contato"] == 0).all()
    assert (preparado.loc[~nunca, "contatado_antes"] == 1).all()
    assert preparado["dias_desde_contato"].max() < 999


def test_o_teste_e_o_futuro_do_treino(clientes: pd.DataFrame) -> None:
    treino, teste = separar_por_data(clientes.sample(frac=1, random_state=1), fracao_teste=0.25)
    assert treino["ordem"].max() < teste["ordem"].min()
    assert len(teste) == 300
    assert not set(treino.index) & set(teste.index)


def test_preprocessador_gera_uma_coluna_por_categoria_mais_as_numericas(clientes: pd.DataFrame) -> None:
    x, _ = separar_x_y(criar_variaveis(clientes))
    matriz = preprocessador(escalar=True).fit_transform(x)
    assert matriz.shape[0] == len(x)
    assert matriz.shape[1] > len(NUMERICAS)
