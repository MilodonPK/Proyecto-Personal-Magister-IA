"""Revisa las salidas guardadas de los notebooks del proyecto.

Los contadores deben ser consecutivos desde 1, las celdas de código deben
tener contenido y ninguna salida debe registrar errores. Estas pruebas
revisan el archivo guardado; no ejecutan sus celdas.
"""

import json
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[1]
NOTEBOOKS = sorted(RAIZ.glob("F*/*.ipynb"))


def test_hay_notebooks_por_verificar():
    """Comprueba que exista al menos un cuaderno en las carpetas de las fases."""
    assert NOTEBOOKS, "No se encontraron notebooks en las carpetas F1, F2, ..."


@pytest.mark.parametrize("ruta", NOTEBOOKS, ids=lambda r: str(r.relative_to(RAIZ)))
def test_notebook_ejecutado_en_orden_y_sin_errores(ruta):
    """Revisa celdas con código, contadores consecutivos y ausencia de errores en el cuaderno guardado."""
    celdas = [c for c in json.loads(ruta.read_text(encoding="utf-8"))["cells"] if c["cell_type"] == "code"]
    vacias = [i for i, c in enumerate(celdas) if not "".join(c["source"]).strip()]
    assert not vacias, f"Celdas de codigo vacias en las posiciones {vacias}"
    contadores = [c["execution_count"] for c in celdas]
    assert contadores == list(range(1, len(celdas) + 1)), f"Contador de ejecucion no correlativo: {contadores}"
    errores = [o.get("ename") for c in celdas for o in c["outputs"] if o["output_type"] == "error"]
    assert not errores, f"Salidas con error: {errores}"
