"""Casos del diccionario BRFSS y separación entre ajuste y aplicación."""

from contextlib import contextmanager

import numpy as np
import pandas as pd
import pytest

from src import pipeline_brfss as pb
from scripts.preparar_brfss import extraer


@pytest.fixture
def crudo():
    """Construye ocho registros originales con códigos BRFSS y devuelve el DataFrame de prueba."""
    n = 8
    df = pd.DataFrame({c: np.ones(n) for c in pb.COLUMNAS})
    df["SEQNO"] = [str(2024000001+i) for i in range(n)]
    df["_PSU"] = range(2024000001, 2024000001+n)
    df["_STSTR"] = 11011
    df["_LLCPWT"] = 10.
    df["MENTHLTH"] = [88, 1, 13, 14, 30, 77, 99, np.nan]
    df["_MENT14D"] = [1, 2, 2, 3, 3, 9, 9, 9]
    df["PHYSHLTH"] = [88, 1, 2, 5, 10, 77, 99, np.nan]
    df["_AGE80"] = [20, 30, 40, 50, 60, 70, 80, 80]
    df["_BMI5"] = [2000, 2200, 2400, 2600, np.nan, 3000, 3500, 4000]
    return df


def test_entorno_y_diccionario():
    """Comprueba Python 3.12 y que el diccionario siga el orden de las columnas seleccionadas."""
    assert pb.verificar_entorno()["python"].startswith("3.12")
    assert list(pb.diccionario_variables().variable) == pb.COLUMNAS


def test_carga_no_limpia_codigos(tmp_path, crudo):
    """Comprueba que leer el archivo conserve el código 88 y todos los valores originales."""
    ruta = tmp_path / "datos.csv.gz"
    crudo.to_csv(ruta, index=False)
    pd.testing.assert_frame_equal(pb.cargar_crudo(ruta), pd.read_csv(ruta, dtype={"SEQNO": "str"}))
    assert pb.cargar_crudo(ruta).MENTHLTH.iloc[0] == 88


def test_carga_archivo_faltante(tmp_path):
    """Comprueba que una ruta inexistente produzca un error que indique el archivo faltante."""
    with pytest.raises(pb.ProyectoError, match="Falta"):
        pb.cargar_crudo(tmp_path / "ausente.csv")


def test_carga_esquema_incorrecto(tmp_path):
    """Comprueba que se rechace un CSV con columnas distintas de la selección BRFSS."""
    ruta = tmp_path / "otro.csv"
    ruta.write_text("otra\n1\n")
    with pytest.raises(pb.ProyectoError, match="columnas"):
        pb.cargar_crudo(ruta)


def test_ceros_no_respuesta_y_frontera_objetivo(crudo):
    """Revisa 88 como cero días, 77/99 como ausencias y el corte entre 13 y 14 sin alterar la entrada."""
    original = crudo.copy(deep=True)
    limpio, reporte = pb.limpiar(crudo)
    assert limpio.MENTHLTH.iloc[:5].tolist() == [0, 1, 13, 14, 30]
    assert limpio[pb.OBJETIVO].iloc[:5].tolist() == [0, 0, 0, 1, 1]
    assert limpio[pb.OBJETIVO].iloc[5:].isna().all()
    assert reporte.loc["MENTHLTH", "no_sabe"] == 1
    assert reporte.loc["MENTHLTH", "rechaza_o_sin_respuesta"] == 1
    assert reporte.loc["MENTHLTH", "faltantes_limpios"] == 3
    assert pb.validar_objetivo(limpio)
    pd.testing.assert_frame_equal(crudo, original)


def test_salto_tabaquismo_se_distingue_de_ausencia(crudo):
    """Solo interpreta el vacío de SMOKDAY2 como salto cuando SMOKE100 vale 2."""
    crudo.loc[:3, "SMOKDAY2"] = np.nan
    crudo.loc[:3, "SMOKE100"] = [2, 7, 9, np.nan]
    limpio, reporte = pb.limpiar(crudo)
    assert limpio.SMOKDAY2.iloc[0] == 0
    assert limpio.SMOKDAY2.iloc[1:4].isna().all()
    assert reporte.loc["SMOKDAY2", "salto_identificado"] == 1
    assert reporte.loc["SMOKDAY2", "faltantes_limpios"] == 3


def test_salto_incompatible_requiere_revision(crudo):
    """Rechaza una respuesta en SMOKDAY2 cuando SMOKE100 indica que esa pregunta se debía omitir."""
    crudo.loc[0, "SMOKE100"] = 2
    with pytest.raises(pb.ProyectoError, match="salto"):
        pb.limpiar(crudo)


def test_nueve_es_valido_en_ingreso(crudo):
    """Comprueba que 9 sea ingreso válido en INCOME3, pero rechazo en EDUCA."""
    crudo.loc[:3, "INCOME3"] = [9, 77, 99, np.nan]
    crudo.loc[0, "EDUCA"] = 9
    limpio, _ = pb.limpiar(crudo)
    assert limpio.INCOME3.iloc[0] == 9
    assert limpio.INCOME3.iloc[1:4].isna().all()
    assert pd.isna(limpio.EDUCA.iloc[0])


@pytest.mark.parametrize("columna,valor", [("MENTHLTH", 31), ("MENTHLTH", 0), ("GENHLTH", 6),
                                         ("INCOME3", 12), ("_BMI5", 10000), ("_AGE80", 81)])
def test_rechaza_valores_no_documentados(crudo, columna, valor):
    """Comprueba que los códigos o valores fuera del dominio de cada columna provoquen un error."""
    crudo.loc[0, columna] = valor
    with pytest.raises(pb.ProyectoError):
        pb.limpiar(crudo)


def test_bmi_decimales_y_edad_topada(crudo):
    """Comprueba que el IMC se divida por 100 y que la edad agrupada en 80 se conserve."""
    limpio, _ = pb.limpiar(crudo)
    assert limpio._BMI5.iloc[0] == 20
    assert limpio._AGE80.iloc[-1] == 80


def test_identificador_compuesto(crudo):
    """Permite repetir SEQNO en otra área, pero rechaza duplicar la pareja de área y secuencia."""
    crudo.loc[1, "SEQNO"] = crudo.loc[0, "SEQNO"]
    crudo.loc[1, "_STATE"] = 2
    pb.limpiar(crudo)
    crudo.loc[1, "_STATE"] = 1
    with pytest.raises(pb.ProyectoError, match="clave"):
        pb.limpiar(crudo)


def test_validacion_detecta_etiqueta_cdc_incompatible(crudo):
    """Detecta una categoría CDC que contradice la etiqueta binaria construida desde los días."""
    limpio, _ = pb.limpiar(crudo)
    limpio.loc[0, "_MENT14D"] = 3
    assert not pb.validar_objetivo(limpio)


def test_auditoria_conserva_discrepancia_que_no_cambia_el_corte_binario(crudo):
    """Registra una diferencia entre cero y 1–13 días aunque no cambie la etiqueta binaria."""
    limpio, _ = pb.limpiar(crudo)
    limpio.loc[0, "_MENT14D"] = 2
    assert pb.validar_objetivo(limpio)
    assert len(pb.auditar_categorias_objetivo(limpio)) == 1
    assert limpio.loc[0, "_MENT14D"] == 2


def test_imputacion_aplica_mediana_de_ajuste_no_de_datos_nuevos(crudo):
    """Imputa con la mediana del ajuste aunque los datos nuevos tengan valores muy distintos."""
    limpio, _ = pb.limpiar(crudo)
    entrenamiento = limpio.iloc[:3]
    parametros = pb.ajustar_preprocesador(entrenamiento)
    nuevos = limpio.iloc[3:5].copy()
    nuevos.loc[nuevos.index[0], "_BMI5"] = 90
    x = pb.aplicar_preprocesador(nuevos, parametros)
    recuperado = x["_BMI5"] * parametros["escalas"]["_BMI5"] + parametros["centros"]["_BMI5"]
    assert recuperado.iloc[1] == pytest.approx(22)
    assert x["_BMI5__faltante"].tolist() == [0, 1]


def test_preprocesador_no_usa_objetivo_ni_variables_de_diseno(crudo):
    """Verifica predictores finitos sin identificadores, diseño muestral ni variables del objetivo."""
    limpio, _ = pb.limpiar(crudo)
    parametros = pb.ajustar_preprocesador(limpio)
    solo_x = limpio[pb.PREDICTORAS]
    x = pb.aplicar_preprocesador(solo_x, parametros)
    assert not set(x) & set(pb.IDENTIFICADORES + pb.DISENO + ["MENTHLTH", "_MENT14D", pb.OBJETIVO])
    assert not x.isna().any().any()
    assert np.isfinite(x.to_numpy()).all()


def test_categorias_estables_en_nuevas_muestras(crudo):
    """Conserva el esquema al recibir categorías válidas nuevas o ausencias y rechaza las desconocidas."""
    limpio, _ = pb.limpiar(crudo)
    parametros = pb.ajustar_preprocesador(limpio.iloc[:3])
    nuevo = limpio.iloc[[0]].copy()
    nuevo["INCOME3"] = 11
    nuevo["GENHLTH"] = np.nan
    x = pb.aplicar_preprocesador(nuevo, parametros)
    assert x["INCOME3__11"].iloc[0] == 1
    assert x["GENHLTH__Sin_respuesta"].iloc[0] == 1
    assert list(x) == list(pb.aplicar_preprocesador(limpio, parametros))
    nuevo["INCOME3"] = 12
    with pytest.raises(pb.ProyectoError, match="desconocidas"):
        pb.aplicar_preprocesador(nuevo, parametros)


def test_numerica_vacia_no_se_imputa_sin_evidencia(crudo):
    """Rechaza estimar la mediana de una variable numérica completamente vacía."""
    limpio, _ = pb.limpiar(crudo)
    limpio["_BMI5"] = np.nan
    with pytest.raises(pb.ProyectoError, match="vacía"):
        pb.ajustar_preprocesador(limpio)


def test_analitico_excluye_objetivos_ausentes_sin_imputarlos(crudo):
    """Excluye los casos sin etiqueta del analítico y conserva el recuento de esas ausencias."""
    limpio, _ = pb.limpiar(crudo)
    analitico, parametros = pb.construir_analitico(limpio)
    assert len(analitico) == 5
    assert parametros["filas_sin_objetivo"] == 3
    assert analitico[pb.OBJETIVO].tolist() == [0, 0, 0, 1, 1]
    assert "MENTHLTH" not in analitico and "_MENT14D" not in analitico


def test_metricas_en_casos_conocidos():
    """Contrasta diferencia estandarizada, V de Cramér y Spearman con resultados calculables a mano."""
    df = pd.DataFrame({c: [1., 2., 3., 4.] for c in pb.NUMERICAS})
    for c in pb.CATEGORICAS:
        df[c] = [1, 1, 2, 2]
    df[pb.OBJETIVO] = [0, 0, 1, 1]
    assert np.allclose(pb.diferencias_estandarizadas(df).d, 2 / np.sqrt(.5))
    assert np.allclose(pb.asociacion_categorica(df).v_cramer, 1)
    assert np.allclose(pb.pares_correlacion(df).rho, 1)


def test_extraccion_conserva_filas_codigos_y_orden(tmp_path, monkeypatch, crudo):
    """Comprueba que la extracción por bloques conserve filas, códigos y orden en el CSV."""
    @contextmanager
    def leer(*args, **kwargs):
        """Simula read_sas: acepta sus argumentos y cede un iterador de dos bloques del ejemplo."""
        yield iter([crudo.iloc[:3].copy(), crudo.iloc[3:].copy()])
    monkeypatch.setattr(pd, "read_sas", leer)
    fuente = tmp_path / "fuente.xpt"
    fuente.write_bytes(b"fixture de lectura por bloques")
    destino = tmp_path / "seleccion.csv.gz"
    meta = extraer(fuente, destino=destino, manifiesto=tmp_path / "fuente.json")
    restaurado = pb.cargar_crudo(destino)
    pd.testing.assert_frame_equal(restaurado, crudo, check_dtype=False)
    assert meta["filas"] == len(crudo)
    assert meta["columnas_seleccionadas"] == pb.COLUMNAS
