"""Confere se um treino novo reproduz os resultados publicados no README (CI).

Uso: python -m mira.conferir esperado.json obtido.json
Sementes fixas tornam o treino reprodutível; entre sistemas, só as últimas casas decimais podem mudar.
"""

import json
import sys
from pathlib import Path

TOLERANCIA = 0.01


def diferencas(esperado: dict, obtido: dict, tolerancia: float = TOLERANCIA) -> list[str]:
    problemas = []
    if esperado["escolhido"] != obtido["escolhido"]:
        problemas.append(f"modelo escolhido mudou: {esperado['escolhido']} -> {obtido['escolhido']}")
    for nome, metricas in esperado["modelos"].items():
        for metrica, valor in metricas.items():
            if not isinstance(valor, int | float):
                continue
            novo = obtido["modelos"].get(nome, {}).get(metrica)
            if novo is None or abs(novo - valor) > tolerancia:
                problemas.append(f"{nome}.{metrica}: {valor} -> {novo}")
    return problemas


def main() -> int:
    esperado, obtido = (json.loads(Path(p).read_text(encoding="utf-8")) for p in sys.argv[1:3])
    problemas = diferencas(esperado, obtido)
    for problema in problemas:
        print(problema)
    print("resultados conferem" if not problemas else "resultados diferentes: atualize o README")
    return 1 if problemas else 0


if __name__ == "__main__":
    sys.exit(main())
