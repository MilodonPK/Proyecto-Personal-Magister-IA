# Registro de decisiones — BRFSS 2024

En esta bitácora explico las decisiones que tomé en F1 y F2. Las cifras corresponden a la versión registrada en `fuente_brfss.json` y a los resultados de ambos cuadernos.

| Decisión | Fundamento | Alternativa considerada | Evidencia |
|---|---|---|---|
| Elegir BRFSS 2024 | Fuente oficial, 457.670 respuestas y códigos reales de no respuesta y saltos que permiten estudiar la calidad de los datos | Trabajar con una selección ya depurada que no permita revisar los códigos originales | F1 §7; `fuente_brfss.json` |
| Conservar una selección de 21 columnas y todas las filas | Incluye las variables de análisis y las necesarias para identificar registros y preservar el diseño; limita el costo de lectura posterior | Cargar las 301 columnas en cada notebook, aunque muchas no corresponden al alcance | Script de preparación y manifiesto |
| Registrar la versión efectiva | El XPT contiene 301 columnas, frente a las 345 anunciadas en la página | Dar por cierta la cifra anunciada sin revisar el archivo | `fuente_brfss.json`; F1 §7 |
| Mantener F1 descriptiva | Conserva el alcance validado por el profesor | Recodificar o imputar antes de documentar los datos | F1 completo; F2 §2 |
| Definir el objetivo como al menos 14 días de mala salud mental | Corresponde a una categoría CDC y permite formular una pregunta central verificable | Presentar la etiqueta como diagnóstico clínico o elegir el corte buscando mejores resultados | Diccionario CDC; F1 §1 |
| Declarar métricas antes del análisis | Diferencia estandarizada para numéricas; V de Cramér para categóricas; Spearman para pares numéricos | Ordenar variables por impresiones visuales o mezclar métricas distintas | F1 §2; F2 §§3–4 |
| Usar 0,80 como umbral exploratorio de Spearman | Señala relaciones fuertes para revisar; no es un límite universal ni autoriza eliminar variables | Seleccionar automáticamente predictores por un umbral fijo | F2 §4 |
| Identificar registros mediante área y secuencia | La secuencia puede repetirse entre áreas; la clave compuesta no se repite en la selección | Eliminar registros que comparten secuencia o respuestas | F2 §1 |
| Interpretar los códigos por columna | 88 son cero días en MENTHLTH; 9 es ingreso válido en INCOME3, pero rechazo en EDUCA | Reemplazar 7, 9, 77 o 99 en todas las columnas | F2 §2.1; pruebas de códigos |
| Distinguir salto de cuestionario y ausencia | 258.956 vacíos de SMOKDAY2 corresponden a SMOKE100=2 | Imputar la frecuencia actual de consumo en todos los vacíos o interpretarlos como «nunca fuma» | F2 §2.3 |
| Recuperar los decimales del IMC | _BMI5 almacena dos decimales implícitos | Tratar valores como 2744 como si fueran un IMC sin escala | Diccionario; `limpiar` |
| Conservar la edad tal como la publica CDC | _AGE80 está imputada por CDC y agrupa a las personas de 80 años o más | Describirla como edad exacta no imputada | Diccionario; F1 §2 |
| Registrar cuatro diferencias entre días y categoría | Las discrepancias afectan cero frente a 1–13 días; la etiqueta binaria coincide en todos los casos | Alterar el archivo original para que ambas columnas coincidan | `discrepancias_objetivo.csv`; F2 §2.4 |
| No imputar el objetivo | 8.156 casos carecen de respuesta interpretable; se conservan en la versión limpia | Convertir la ausencia en clase 0 o imputar una respuesta de salud mental | F2 §§2.4 y 5 |
| Calcular asociaciones antes de imputar | Cada tabla informa su número de respuestas válidas; la imputación no debe aparentar información observada | Comparar grupos como si los valores imputados fueran respuestas originales | F2 §3 |
| Usar mediana e indicador de ausencia en numéricas | Es una preparación exploratoria que mantiene información sobre faltantes; mediana del IMC = 27,44 y de días de salud física = 0 | Eliminar todos los casos incompletos o imputar sin señalarlo | F2 §5; JSON |
| Usar una categoría de no respuesta y one-hot | Evita imponer distancias iguales a códigos de ingreso o educación; categorías fijadas por diccionario | Codificar categorías nominales como una escala continua | F2 §5 |
| Escalar solo las tres variables numéricas | Deja dispersión comparable; los indicadores one-hot conservan 0/1 | Escalar identificadores, ponderadores o todos los códigos del cuestionario | F2 §§5–6 |
| Excluir MENTHLTH y _MENT14D de predictores | Ambas determinan directamente la etiqueta | Entrenar con una transformación del objetivo entre las entradas | JSON y pruebas de separación de columnas |
| Conservar diseño muestral y limitar la interpretación | Los resultados actuales son descriptivos de la muestra sin ponderar | Presentar los porcentajes muestrales como prevalencias poblacionales | F1 §1; F2 §3 |
| No versionar microdatos grandes | El XPT ocupa aproximadamente 1 GB; selección y resultados se regeneran con script y notebooks | Subir todos los archivos al repositorio | `.gitignore`, README y CI |
