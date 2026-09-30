# Documentación del avance F1–F2

Reúno aquí la fuente, las decisiones y los resultados que respaldan el avance descrito en el README del proyecto. Las cifras de las tablas proceden de los cuadernos; no las ajusto manualmente para hacerlas coincidir con el informe.

| Archivo | Qué contiene | De dónde sale |
|---|---|---|
| [fuente_brfss.json](fuente_brfss.json) | Identificación del XPT, sus 301 columnas, selección de 21 variables y huellas SHA-256 | `scripts/preparar_brfss.py` |
| [diccionario_variables.csv](diccionario_variables.csv) | Definiciones y códigos de las 21 columnas seleccionadas | F1 §7.3; `diccionario_variables()` |
| [metadatos_fase1.json](metadatos_fase1.json) | Dimensiones de la selección, entorno y seis comprobaciones | F1 §9 |
| [reporte_calidad_f2.csv](reporte_calidad_f2.csv) | Ausencias, no respuesta y saltos por variable | F2 §2; `limpiar()` |
| [discrepancias_objetivo.csv](discrepancias_objetivo.csv) | Cuatro diferencias entre días declarados y categoría CDC | F2 §2.4; `auditar_categorias_objetivo()` |
| [diferencias_numericas.csv](diferencias_numericas.csv) | Diferencias estandarizadas de medias y casos válidos por grupo | F2 §3.1 |
| [asociaciones_categoricas.csv](asociaciones_categoricas.csv) | V de Cramér y número de respuestas válidas | F2 §3.2 |
| [correlaciones_numericas.csv](correlaciones_numericas.csv) | Spearman, tamaño de cada par y comparación con el umbral de 0,80 | F2 §4 |
| [bitacora_decisiones.md](bitacora_decisiones.md) | Decisiones de F1 y F2, motivos y alternativas | Desarrollo del análisis |
| [respuesta_observaciones_omar.md](respuesta_observaciones_omar.md) | Cómo incorporé las observaciones del profesor en este avance | Revisión de F1 y F2 |
| [informe_s1/informe_s1.md](informe_s1/informe_s1.md) | Informe del avance en formato editable de texto | Evidencias de F1 y F2 |
| [informe_s1/f1_s01_entregable.docx](informe_s1/f1_s01_entregable.docx) | Versión Word del mismo informe; el nombre del archivo se conserva | Mismo contenido del informe Markdown |

## Comprobación de las cifras

Al revisar esta documentación contrasté las tablas con los cálculos sobre la selección original. El conjunto limpio conserva **457.670 filas**; **449.514** tienen objetivo observado y **8.156** quedan sin etiqueta. Las cuatro discrepancias registradas no cambian la clasificación con el corte de 14 días. También comprobé que las 16 filas del anexo de calidad coincidan con `reporte_calidad_f2.csv`.

El diccionario corresponde a las 21 columnas de entrada. La variable `malestar_frecuente` se construye en F2, por lo que la versión limpia tiene 22 columnas. La versión analítica tiene 73: 67 predictores codificados, dos campos de identificación, tres del diseño muestral y el objetivo. En `../data/processed/parametros_transformacion.json` quedan los parámetros exploratorios y los ocho controles de F2.

## Alcance de esta entrega

La carpeta [f3/](f3/) conserva los resultados y las decisiones de la fase preparada para una entrega posterior. No la incluyo como evidencia del avance F1–F2. Sus decisiones están en su propia bitácora, separadas de la del avance actual.

En el informe todavía falta incorporar la **figura del mapa conceptual**. La sección VIII contiene una tabla que relaciona conceptos y evidencias, pero no la presento como si fuera esa figura. Este pendiente está señalado tanto en Markdown como en Word.
