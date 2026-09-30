# Salud mental autorreportada en BRFSS 2024

Soy Fernando Toro Carrasco y este es mi proyecto individual para MCDI500, Programación para la Ciencia de Datos, del Magíster en Ciencia de Datos e IA de la UNAB.

**Docente:** Omar Iván Salinas Silva.

En este trabajo busco responder una pregunta: **¿qué características de salud, condiciones de vida y hábitos se relacionan con reportar al menos 14 días de mala salud mental durante los últimos 30 días?** Para estudiarla uso la encuesta BRFSS 2024 de los CDC. Trabajo con lo que las personas declararon en la encuesta, por lo que no interpreto esta respuesta como un diagnóstico clínico.

Al revisar el archivo XPT encontré **457.670 filas y 301 columnas**. Seleccioné 21 columnas relacionadas con el análisis y conservé todas las filas. La página oficial indica 345 variables, pero esa cifra no coincide con el archivo que recibí. Dejé registrada la diferencia en `docs/fuente_brfss.json`, junto con la huella SHA-256 que permite identificar la versión que utilicé.

## Qué quiero analizar

- **P1. ¿Qué problemas de calidad tienen los datos?** Reviso los valores ausentes, las respuestas omitidas, los saltos del cuestionario y las inconsistencias. También compruebo que la combinación `(_STATE, SEQNO)` identifique cada registro sin repetirse.
- **P2. ¿Qué variables muestran mayores diferencias entre quienes reportan 14 o más días de mala salud mental y quienes reportan menos?** Comparo las tres variables numéricas mediante la diferencia estandarizada de medias y las categóricas mediante V de Cramér. Presento ambos resultados por separado e indico cuántas respuestas utilicé en cada cálculo.
- **P3. ¿Qué tan relacionadas están las variables numéricas entre sí?** Calculo la correlación de Spearman y uso `|ρ| ≥ 0,80` como criterio exploratorio para revisar relaciones fuertes. Además, distingo las dependencias que ya vienen dadas por el cuestionario.

Dejé las decisiones de limpieza y transformación en la metodología. Por ahora analizo la muestra sin aplicar ponderadores, así que no tomo sus porcentajes como estimaciones de toda la población ni sus asociaciones como causas. Conservé `_LLCPWT`, `_STSTR` y `_PSU` por si más adelante incorporo el diseño muestral al análisis.

## Cómo va el proyecto

En esta versión presento el trabajo hasta F2: la definición del problema, la revisión de la fuente y la preparación exploratoria de los datos. Dejé ambos cuadernos ejecutados, con sus resultados guardados.

| Fase | Contenido | Estado |
|---|---|---|
| F1 | Problema, fuente, entorno y descripción sin limpieza | [Notebook ejecutado](F1/F1_Definicion.ipynb) |
| F2 | Recodificación, revisión de faltantes, asociaciones y preparación exploratoria | [Notebook ejecutado](F2/F2_Preprocesamiento.ipynb) |

Organicé los archivos de esta manera para separar los cuadernos, las funciones y los datos:

```text
F1/ y F2/                     notebooks y salidas
src/pipeline_brfss.py          reglas, métricas y preprocesamiento
scripts/preparar_brfss.py      extracción por bloques desde XPT o ZIP
tests/                        pruebas (sin necesidad del XPT completo)
data/raw/                     selección original comprimida, excluida de Git
data/processed/               CSV regenerables y parámetros JSON
docs/                         fuente, diccionario, decisiones y reportes compactos
.github/workflows/ci.yml       comprobaciones y ejecución desde la fuente oficial
```

## Cómo preparo el entorno y los datos

Uso Python 3.12 y las versiones de las bibliotecas que dejé en `requirements.txt`. Para crear el entorno y reunir las dependencias, ejecuto estos comandos desde la carpeta del proyecto. Leo el formato XPT con Python, por lo que no necesito instalar SAS.

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Trabajo en macOS. Para activar el mismo entorno en Windows, el comando es `.venv\Scripts\activate`.

Mi fuente es **2024 BRFSS Data (SAS Transport Format)**, disponible en la [página oficial](https://www.cdc.gov/brfss/annual_data/annual_2024.html). El script de preparación acepta tanto el ZIP como el XPT descomprimido. En estos ejemplos reemplazo la ruta por la ubicación del archivo:

```bash
python scripts/preparar_brfss.py "/ruta/LLCP2024XPT.zip"
# O, si ya lo descomprimiste:
python scripts/preparar_brfss.py "/ruta/LLCP2024.XPT"
```

También dejé una opción para descargar y preparar los datos en un solo paso:

```bash
python scripts/preparar_brfss.py --descargar
```

Un detalle de mi copia local: el nombre del XPT termina con un espacio después de `.XPT`. Al pasar esa ruta al script tengo que conservar el espacio dentro de las comillas; el autocompletado de la terminal también permite hacerlo.

Como el XPT ocupa aproximadamente 1 GB, lo leo por bloques. Guardo las 21 columnas seleccionadas en `data/raw/brfss_2024_seleccion.csv.gz`, manteniendo todos los registros y los códigos originales. En `docs/fuente_brfss.json` registro el tamaño, las columnas y las huellas de ambos archivos. Si vuelvo a descargar la fuente y CDC la ha modificado, tendré que revisar esas diferencias y las conclusiones. Para procesar el ZIP también necesito espacio temporal para descomprimirlo.

## Cómo ejecuto los cuadernos

Abro Jupyter desde la raíz del repositorio:

```bash
jupyter lab
```

Ejecuto F1 y después F2, usando *Restart Kernel and Run All Cells* en cada cuaderno. Así compruebo que no dependan de variables que hayan quedado de una ejecución anterior. Para hacer lo mismo desde la terminal y correr las pruebas, uso:

```bash
python -m nbconvert --to notebook --execute --inplace --ExecutePreprocessor.timeout=600 F1/F1_Definicion.ipynb
python -m nbconvert --to notebook --execute --inplace --ExecutePreprocessor.timeout=600 F2/F2_Preprocesamiento.ipynb
python -m pytest -q
```

Para comprobar las funciones uso ejemplos pequeños cuyo resultado conozco, incluyendo la interpretación de los códigos, el manejo de faltantes y la aplicación de las transformaciones. También reviso que los cuadernos tengan sus salidas guardadas en orden y sin errores. Dejé configurada la integración continua para descargar la fuente y ejecutar F1 y F2 desde cero. Si los datos cambian, igualmente tengo que revisar el texto y las conclusiones: que el código termine sin errores no asegura que lo escrito siga vigente.

## Lo que encontré al preparar los datos en F2

Conservé las 457.670 filas en la versión limpia. Al revisar los códigos del cuestionario, tuve que tratar cada columna según su significado:

- Interpreté `88` como cero días y `77/99` como no respuesta en las preguntas sobre días de mala salud.
- Mantuve el código `9` como ingreso válido en `INCOME3`. Este caso muestra por qué no puedo reemplazar un mismo código en toda la base.
- Identifiqué **258.956 saltos** de `SMOKDAY2` que dependen de la respuesta anterior. No los traté como respuestas sobre consumo actual.
- Registré **cuatro discrepancias** entre los días de mala salud mental y la categoría publicada por CDC. Ninguna modifica la clasificación con el corte de 14 días.
- Dejé los **8.156 casos sin respuesta al objetivo** en la versión limpia. Los excluí de la versión analítica porque no corresponde completar esa etiqueta como si fuera una respuesta observada.

Guardé los siguientes archivos para poder revisar los resultados y repetir el proceso. En la última columna indico cuáles incluyo en Git:

| Archivo | Contenido | Git |
|---|---|---|
| `data/processed/brfss_limpio.csv.gz` | 457.670 filas y 22 columnas; códigos interpretados y faltantes conservados | No |
| `data/processed/brfss_analitico.csv.gz` | 449.514 filas y 73 columnas: 67 predictores codificados, objetivo, dos campos de identificación y tres del diseño | No |
| `data/processed/parametros_transformacion.json` | Medianas, centros, escalas, categorías y lista exacta de predictores | Sí |
| `docs/reporte_calidad_f2.csv` | Ausencias y códigos de no respuesta por variable | Sí |
| `docs/discrepancias_objetivo.csv` | Las cuatro discrepancias detectadas | Sí |
| `docs/diferencias_numericas.csv` | Diferencias estandarizadas y denominadores | Sí |
| `docs/asociaciones_categoricas.csv` | V de Cramér y número de respuestas utilizadas | Sí |
| `docs/correlaciones_numericas.csv` | Spearman y casos válidos por par | Sí |

Entre las variables numéricas, encontré la mayor diferencia estandarizada en los días de mala salud física (`d ≈ 0,922`). Entre las categóricas, el antecedente depresivo autorreportado tuvo la mayor V de Cramér (`≈ 0,377`). Con estos resultados describo asociaciones en la muestra. El alcance de esta entrega llega a la preparación y la exploración de los datos.

En F2 calculé los parámetros de preparación sobre el conjunto analítico completo para explorar los datos. Para una evaluación posterior tendré que volver a la versión limpia, separar las muestras y ajustar esos parámetros solo con entrenamiento, sin reutilizar los calculados sobre todo el conjunto. Dejé la lista de entradas en `predictores_salida` del JSON, excluyendo los identificadores, las variables del diseño muestral y las que definen directamente la etiqueta.

## Documentación del análisis

En la [bitácora](docs/bitacora_decisiones.md) explico las decisiones del análisis. También dejé un [diccionario de variables](docs/diccionario_variables.csv) para consultar el significado de las columnas de BRFSS y sus códigos.

## Cómo nombro mis commits

Uso el formato `prefijo: descripción breve` para que el historial permita reconocer qué cambié en cada commit. Mantengo estos cinco prefijos:

| Prefijo | Cuándo lo uso | Ejemplo de mensaje |
|---|---|---|
| `feat:` | Agrego una funcionalidad al proyecto | `feat: agregar la recodificación de variables BRFSS` |
| `fix:` | Corrijo un error en el código o en su comportamiento | `fix: validar el objetivo después de leer el CSV` |
| `docs:` | Actualizo explicaciones, instrucciones o documentación | `docs: explicar cómo ejecutar F2 en el README` |
| `test:` | Agrego o ajusto pruebas | `test: comprobar los códigos de no respuesta` |
| `chore:` | Hago tareas de mantenimiento, configuración o dependencias | `chore: actualizar las dependencias del proyecto` |

Elijo el prefijo según el propósito principal del cambio y procuro que la descripción diga qué hice, evitando mensajes como «cambios varios».

## Fuente de los datos

Utilicé los datos y la documentación oficial de los CDC:

Centers for Disease Control and Prevention. (2025). *Behavioral Risk Factor Surveillance System: 2024 Survey Data and Documentation*. [Datos oficiales](https://www.cdc.gov/brfss/annual_data/annual_2024.html), [diccionario de códigos](https://www.cdc.gov/brfss/annual_data/2024/zip/codebook24_llcp-v2-508.zip) y [variables calculadas](https://www.cdc.gov/brfss/annual_data/2024/pdf/2024-calculated-variables-version4-508.pdf).

Aunque trabajé con el archivo público original, algunas variables ya vienen calculadas o imputadas por CDC. Por eso distingo ese procesamiento de las transformaciones que hice en el proyecto y documento ambas cosas en los cuadernos.
