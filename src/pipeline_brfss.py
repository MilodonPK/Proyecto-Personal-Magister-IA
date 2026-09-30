"""Lectura y preparación de la selección de salud mental de BRFSS 2024.

Las reglas siguen el diccionario de agosto de 2025. No se imputan etiquetas
ni se usan variables derivadas del objetivo como predictores.
"""

import importlib.metadata
import json
import platform
from pathlib import Path

import numpy as np
import pandas as pd

RAIZ = Path(__file__).resolve().parents[1]
RUTA_RAW = RAIZ / "data/raw/brfss_2024_seleccion.csv.gz"
DIR_PROCESSED = RAIZ / "data/processed"
SEMILLA = 42
IDENTIFICADORES = ["_STATE", "SEQNO"]
DISENO = ["_PSU", "_STSTR", "_LLCPWT"]
NUMERICAS = ["_AGE80", "_BMI5", "PHYSHLTH"]
CATEGORICAS = ["SEXVAR", "GENHLTH", "ADDEPEV3", "EXERANY2", "MEDCOST1",
               "EDUCA", "EMPLOY1", "INCOME3", "MARITAL", "SMOKE100", "SMOKDAY2"]
PREDICTORAS = NUMERICAS + CATEGORICAS
OBJETIVO = "malestar_frecuente"
COLUMNAS = ["_STATE", "SEQNO", "_PSU", "_STSTR", "_LLCPWT", "MENTHLTH", "_MENT14D",
            "PHYSHLTH", "GENHLTH", "ADDEPEV3", "EXERANY2", "MEDCOST1", "EDUCA",
            "EMPLOY1", "INCOME3", "MARITAL", "SMOKE100", "SMOKDAY2", "_AGE80", "SEXVAR", "_BMI5"]

# Códigos válidos, «no sabe» y «rechaza». Un 9 puede ser una respuesta válida,
# como en INCOME3; nunca se reemplazan códigos de forma global.
REGLAS = {
    # En las preguntas de días: 88 = ninguno, 77 = no sabe y 99 = rechaza.
    "MENTHLTH": (list(range(1, 31)) + [88], [77], [99]),
    "PHYSHLTH": (list(range(1, 31)) + [88], [77], [99]),
    "GENHLTH": (list(range(1, 6)), [7], [9]),
    "ADDEPEV3": ([1, 2], [7], [9]),
    "EXERANY2": ([1, 2], [7], [9]),
    "MEDCOST1": ([1, 2], [7], [9]),
    "EDUCA": (list(range(1, 7)), [], [9]),
    "EMPLOY1": (list(range(1, 9)), [], [9]),
    "INCOME3": (list(range(1, 12)), [77], [99]),
    "MARITAL": (list(range(1, 7)), [], [9]),
    "SMOKE100": ([1, 2], [7], [9]),
    "SMOKDAY2": ([1, 2, 3], [7], [9]),
    "SEXVAR": ([1, 2], [], []),
    "_MENT14D": ([1, 2, 3], [], [9]),
}

DESCRIPCIONES = {
    "_STATE": "Código de área de encuesta; parte de la clave del registro",
    "SEQNO": "Número de secuencia; se identifica el registro junto con _STATE",
    "_PSU": "Unidad primaria de muestreo; se conserva para análisis del diseño",
    "_STSTR": "Estrato de muestreo",
    "_LLCPWT": "Ponderador final de la encuesta; no es una variable predictora",
    "MENTHLTH": "Días de mala salud mental autorreportada en los últimos 30 días",
    "_MENT14D": "Clasificación CDC: 1 = cero días; 2 = 1–13; 3 = 14–30; 9 = sin respuesta válida",
    "PHYSHLTH": "Días de mala salud física en los últimos 30 días",
    "GENHLTH": "Salud general: 1 excelente, 2 muy buena, 3 buena, 4 regular, 5 mala",
    "ADDEPEV3": "Alguna vez le comunicaron un trastorno depresivo: 1 sí, 2 no; autorreporte",
    "EXERANY2": "Actividad física fuera del trabajo durante el último mes: 1 sí, 2 no",
    "MEDCOST1": "No pudo consultar a un médico por costo en los últimos 12 meses: 1 sí, 2 no",
    "EDUCA": "Nivel educativo: 1 sin escolaridad/kínder; 2 grados 1–8; 3 grados 9–11; 4 secundaria; 5 estudios superiores 1–3 años; 6 estudios superiores 4+ años",
    "EMPLOY1": "Situación laboral: 1 empleado; 2 independiente; 3 desempleo 1+ años; 4 desempleo <1 año; 5 hogar; 6 estudiante; 7 jubilado; 8 incapaz de trabajar",
    "INCOME3": "Ingreso anual del hogar: tramos 1 <10 mil; 2 10–<15 mil; 3 15–<20 mil; 4 20–<25 mil; 5 25–<35 mil; 6 35–<50 mil; 7 50–<75 mil; 8 75–<100 mil; 9 100–<150 mil; 10 150–<200 mil; 11 200 mil o más USD",
    "MARITAL": "Estado civil: 1 casado; 2 divorciado; 3 viudo; 4 separado; 5 nunca casado; 6 pareja no casada",
    "SMOKE100": "Ha fumado al menos 100 cigarrillos en su vida: 1 sí, 2 no",
    "SMOKDAY2": "Frecuencia actual entre quienes fumaron 100 cigarrillos: 1 diaria; 2 algunos días; 3 no fuma. En limpio, 0 indica salto por SMOKE100=2, no ausencia de consumo actual",
    "_AGE80": "Edad imputada por CDC y agrupada en 80 para 80 años o más",
    "SEXVAR": "Sexo registrado en el archivo: 1 masculino, 2 femenino",
    "_BMI5": "IMC calculado por CDC, con dos decimales implícitos; se divide por 100 en F2",
}


class ProyectoError(ValueError):
    """Entrada incompatible con las reglas documentadas del proyecto."""


def verificar_entorno(paquetes=("numpy", "pandas", "matplotlib", "seaborn")):
    """Recibe nombres de paquetes y devuelve sus versiones junto con la de Python.
    Sirve para comprobar y registrar el entorno de los cuadernos.
    """
    try:
        return {"python": platform.python_version(), **{p: importlib.metadata.version(p) for p in paquetes}}
    except importlib.metadata.PackageNotFoundError as error:
        raise ProyectoError(f"Falta una dependencia: {error}") from error


def cargar_crudo(ruta=RUTA_RAW):
    """Recibe la ruta del CSV de la selección y devuelve un DataFrame validado.
    Lee los códigos originales sin recodificar respuestas ni retirar registros.
    """
    ruta = Path(ruta)
    if not ruta.exists():
        raise ProyectoError("Falta la selección BRFSS. Ejecute scripts/preparar_brfss.py con el archivo XPT.")
    df = pd.read_csv(ruta, dtype={"SEQNO": "str"}, float_precision="round_trip")
    if list(df.columns) != COLUMNAS:
        raise ProyectoError("Las columnas no coinciden con la selección documentada de BRFSS.")
    return df


def diccionario_variables():
    """No recibe argumentos y devuelve un DataFrame con las variables y sus reglas.
    Documenta el papel de cada columna y sus códigos de no respuesta.
    """
    filas = []
    for c in COLUMNAS:
        rol = ("identificador" if c in IDENTIFICADORES else "diseño muestral" if c in DISENO
               else "origen del objetivo" if c == "MENTHLTH" else "validación del objetivo" if c == "_MENT14D"
               else "predictora numérica" if c in NUMERICAS else "predictora categórica")
        regla = REGLAS.get(c)
        filas.append({"variable": c, "rol": rol, "descripcion": DESCRIPCIONES[c],
                      "codigos_validos": str(regla[0]) if regla else "Ver descripción y diccionario CDC",
                      "no_sabe": str(regla[1]) if regla else "[]",
                      "rechaza_o_sin_respuesta": str(regla[2]) if regla else "[]"})
    return pd.DataFrame(filas)


def resumen_calidad(df):
    """Recibe un DataFrame y devuelve un diccionario de dimensiones y recuentos.
    Cuenta vacíos y duplicados antes de interpretar los códigos de no respuesta.
    """
    return {"filas": len(df), "columnas": len(df.columns), "ausencias_sas": int(df.isna().sum().sum()),
            "filas_duplicadas": int(df.duplicated().sum()),
            "claves_duplicadas": int(df.duplicated(IDENTIFICADORES).sum())}


def limpiar(df):
    """Recibe la selección original y devuelve dos DataFrames: datos limpios y reporte.
    Interpreta los códigos y registra el motivo de las ausencias, sin imputar
    ni eliminar filas. Un código no documentado provoca un error.
    """
    if list(df.columns) != COLUMNAS:
        raise ProyectoError("Esquema BRFSS incorrecto.")
    if df[IDENTIFICADORES].isna().any().any() or df.duplicated(IDENTIFICADORES).any():
        raise ProyectoError("La clave (_STATE, SEQNO) está incompleta o repetida; requiere revisión.")
    resultado = df.copy()
    reporte = []
    for c, (validos, no_sabe, rechaza) in REGLAS.items():
        s = pd.to_numeric(df[c], errors="raise")
        invalidos = s.notna() & ~s.isin(validos + no_sabe + rechaza)
        if invalidos.any():
            raise ProyectoError(f"Códigos no documentados en {c}: {s[invalidos].unique().tolist()}")
        # Los códigos de no respuesta (77/99 en días) pasan a NaN según cada columna.
        resultado[c] = s.where(s.isin(validos))
        reporte.append({"variable": c, "ausente_archivo": int(s.isna().sum()),
                        "no_sabe": int(s.isin(no_sabe).sum()), "rechaza_o_sin_respuesta": int(s.isin(rechaza).sum()),
                        "salto_identificado": 0})
    for c in ["MENTHLTH", "PHYSHLTH"]:
        # 88 significa «ningún día»: es un cero observado, no un dato ausente.
        resultado[c] = resultado[c].replace(88, 0)
    # SMOKE100=2 omite la pregunta siguiente; ese vacío es un salto del cuestionario.
    salto = df["SMOKE100"].eq(2) & df["SMOKDAY2"].isna()
    if (df["SMOKE100"].eq(2) & df["SMOKDAY2"].notna()).any():
        raise ProyectoError("SMOKDAY2 respondido pese a SMOKE100=2; revisar el salto.")
    # La categoría 0 identifica el salto; no afirma que la persona no fume actualmente.
    resultado.loc[salto, "SMOKDAY2"] = 0
    for fila in reporte:
        if fila["variable"] == "SMOKDAY2":
            fila["salto_identificado"] = int(salto.sum())
    for c, minimo, maximo in [("_AGE80", 18, 80), ("_BMI5", 1, 9999)]:
        s = df[c]
        if (s.notna() & (~s.between(minimo, maximo) | s.ne(s.round()))).any():
            raise ProyectoError(f"Valores fuera del dominio documentado en {c}.")
        reporte.append({"variable": c, "ausente_archivo": int(s.isna().sum()), "no_sabe": 0,
                        "rechaza_o_sin_respuesta": 0, "salto_identificado": 0})
    # CDC guarda el IMC con dos decimales implícitos: 2744 representa 27,44.
    resultado["_BMI5"] = resultado["_BMI5"] / 100
    resultado[OBJETIVO] = (resultado["MENTHLTH"] >= 14).astype("Int8").mask(resultado["MENTHLTH"].isna())
    reporte = pd.DataFrame(reporte).set_index("variable")
    reporte["faltantes_limpios"] = resultado[reporte.index].isna().sum()
    return resultado, reporte


def validar_objetivo(limpio):
    """Recibe los datos limpios y devuelve True si la etiqueta coincide con CDC.
    Contrasta el corte de 14 días y comprueba también las ausencias.
    """
    publicado = limpio["_MENT14D"].eq(3).astype("Int8").mask(limpio["_MENT14D"].isna())
    # CSV recupera una etiqueta con ausencias como float64; se comparan
    # valores y ausencias, sin exigir el dtype Int8 usado en memoria en F2.
    observado = limpio[OBJETIVO]
    coincide = publicado.eq(observado).fillna(False) | (publicado.isna() & observado.isna())
    return bool(coincide.all())


def auditar_categorias_objetivo(limpio):
    """Recibe los datos limpios y devuelve un DataFrame con las discrepancias.
    Compara los días declarados con las tres categorías CDC sin corregir la fuente.
    """
    dias = limpio["MENTHLTH"]
    categorias = pd.Series(np.select([dias.eq(0), dias.between(1, 13), dias.between(14, 30)],
                                    [1., 2., 3.], default=np.nan), index=limpio.index)
    publicado = limpio["_MENT14D"].astype(float)
    coincide = categorias.eq(publicado) | (categorias.isna() & publicado.isna())
    tabla = limpio.loc[~coincide, IDENTIFICADORES + ["MENTHLTH", "_MENT14D", OBJETIVO]].copy()
    tabla["categoria_desde_dias"] = categorias.loc[~coincide]
    return tabla


def diferencias_estandarizadas(df):
    """Recibe datos limpios con objetivo y devuelve una tabla ordenada por abs(d).
    Para P2 calcula (media del grupo 1 − media del grupo 0) / desviación
    combinada, usando los casos válidos de cada variable numérica.
    """
    filas = []
    for c in NUMERICAS:
        a = df.loc[df[OBJETIVO].eq(1).fillna(False), c].dropna()
        b = df.loc[df[OBJETIVO].eq(0).fillna(False), c].dropna()
        if min(len(a), len(b)) < 2:
            raise ProyectoError("Se necesitan al menos dos valores por grupo para comparar medias.")
        combinada = np.sqrt(((len(a)-1)*a.var() + (len(b)-1)*b.var()) / (len(a)+len(b)-2))
        d = (a.mean()-b.mean()) / combinada if combinada > 0 else np.nan
        filas.append({"variable": c, "n_1": len(a), "n_0": len(b), "media_1": a.mean(),
                      "media_0": b.mean(), "d": d, "abs_d": abs(d)})
    return pd.DataFrame(filas).sort_values(["abs_d", "variable"], ascending=[False, True])


def asociacion_categorica(df):
    """Recibe datos limpios con objetivo y devuelve una tabla con V de Cramér y n.
    Compara las asociaciones categóricas de P2 sin corrección de sesgo,
    excluyendo las respuestas ausentes en cada cruce.
    """
    filas = []
    for c in CATEGORICAS:
        tabla = pd.crosstab(df[c], df[OBJETIVO])
        n = int(tabla.to_numpy().sum())
        dim = min(tabla.shape) - 1
        if n == 0 or dim < 1:
            v = np.nan
        else:
            observado = tabla.to_numpy(dtype=float)
            esperado = np.outer(observado.sum(axis=1), observado.sum(axis=0)) / n
            chi2 = ((observado-esperado)**2 / esperado).sum()
            v = np.sqrt(chi2 / (n*dim))
        filas.append({"variable": c, "n_valido": n, "v_cramer": v})
    return pd.DataFrame(filas).sort_values(["v_cramer", "variable"], ascending=[False, True])


def pares_correlacion(df, umbral=0.80):
    """Recibe datos limpios y un umbral; devuelve una tabla de Spearman por pares.
    Responde P3 con las tres variables numéricas e indica qué pares alcanzan
    el umbral en valor absoluto y cuántos casos válidos usa cada uno.
    """
    if not 0 <= umbral <= 1:
        raise ProyectoError("El umbral debe estar entre 0 y 1.")
    filas = []
    for i, a in enumerate(NUMERICAS):
        for b in NUMERICAS[i+1:]:
            par = df[[a, b]].dropna()
            rho = par.rank(method="average").corr().loc[a, b]
            filas.append({"variable_a": a, "variable_b": b, "rho": rho,
                          "n_par": len(par), "supera_umbral": bool(abs(rho) >= umbral)})
    return pd.DataFrame(filas)


def ajustar_preprocesador(df):
    """Recibe un DataFrame de ajuste y devuelve un diccionario de parámetros.
    Estima medianas, centros y escalas sin consultar el objetivo. En F2 sirve
    para explorar; en F3 recibe solo entrenamiento. Las categorías son fijas
    y proceden del diccionario de variables.
    """
    if df.empty:
        raise ProyectoError("No se puede ajustar con cero filas.")
    x = df[NUMERICAS].astype(float)
    if np.isinf(x.to_numpy()).any():
        raise ProyectoError("Hay valores infinitos.")
    mediana = x.median()
    if mediana.isna().any():
        raise ProyectoError("No se puede estimar la mediana de una columna completamente vacía.")
    completo = x.fillna(mediana)
    escala = completo.std(ddof=0)
    # Una columna constante queda en cero, sin dividir por cero.
    escala = escala.mask(escala.eq(0), 1.)
    categorias = {c: [str(v) for v in REGLAS[c][0]] + ["Sin_respuesta"] for c in CATEGORICAS}
    # Incluye el salto identificado en la limpieza como categoría distinta de la ausencia.
    categorias["SMOKDAY2"].insert(0, "0")
    return {"medianas": mediana.to_dict(), "centros": completo.mean().to_dict(),
            "escalas": escala.to_dict(), "categorias": categorias,
            "numericas": NUMERICAS, "categoricas": CATEGORICAS}


def aplicar_preprocesador(df, parametros):
    """Recibe datos y parámetros ya ajustados; devuelve un DataFrame de predictores.
    Imputa, escala y codifica con esas reglas, sin volver a estimarlas.
    """
    piezas = []
    for c in parametros["numericas"]:
        s = df[c].astype(float)
        if np.isinf(s.to_numpy()).any():
            raise ProyectoError(f"Valores infinitos en {c}.")
        piezas.append(pd.DataFrame({c: (s.fillna(parametros["medianas"][c])-parametros["centros"][c]) / parametros["escalas"][c],
                                    c + "__faltante": s.isna().astype("uint8")}, index=df.index))
    for c in parametros["categoricas"]:
        s = df[c]
        if (s.notna() & s.ne(s.round())).any():
            raise ProyectoError(f"Categoría no entera en {c}.")
        etiquetas = s.astype("Int64").astype("string").fillna("Sin_respuesta")
        if not etiquetas.isin(parametros["categorias"][c]).all():
            raise ProyectoError(f"Categorías desconocidas en {c}.")
        cat = pd.Series(pd.Categorical(etiquetas, categories=parametros["categorias"][c]), index=df.index, name=c)
        piezas.append(pd.get_dummies(cat, prefix=c, prefix_sep="__", dtype="uint8"))
    return pd.concat(piezas, axis=1)


def construir_analitico(limpio):
    """Recibe los datos limpios y devuelve el DataFrame analítico y sus parámetros.
    Prepara la exploración de F2 con los casos que tienen etiqueta, sin modificar
    la entrada, donde se conservan los casos sin respuesta al objetivo.
    """
    validos = limpio.loc[limpio[OBJETIVO].notna()].copy()
    parametros = ajustar_preprocesador(validos)
    x = aplicar_preprocesador(validos, parametros)
    analitico = pd.concat([validos[IDENTIFICADORES + DISENO + [OBJETIVO]], x], axis=1)
    parametros.update({"alcance": "Exploración F2; reajustar solo en entrenamiento para evaluar modelos",
                       "filas_entrada": len(limpio), "filas_con_objetivo": len(validos),
                       "filas_sin_objetivo": int(limpio[OBJETIVO].isna().sum()),
                       "predictores_salida": list(x.columns)})
    return analitico, parametros


def guardar_json(datos, ruta):
    """Recibe datos serializables y una ruta; escribe un JSON y devuelve None.
    Guarda parámetros o indicadores en UTF-8, sin admitir valores NaN.
    """
    ruta = Path(ruta)
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_text(json.dumps(datos, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")
