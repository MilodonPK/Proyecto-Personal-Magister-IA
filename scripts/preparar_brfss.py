"""Extrae columnas de BRFSS sin limpiar, recodificar ni muestrear filas.

Uso: python scripts/preparar_brfss.py '/ruta/LLCP2024.XPT '
     python scripts/preparar_brfss.py --descargar
"""

import argparse
import gzip
import hashlib
import io
import shutil
import sys
import tempfile
import urllib.request
import zipfile
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src import pipeline_brfss as pb

URL = "https://www.cdc.gov/brfss/annual_data/2024/files/LLCP2024XPT.zip"
FUENTE = "https://www.cdc.gov/brfss/annual_data/annual_2024.html"
DICCIONARIO = "https://www.cdc.gov/brfss/annual_data/2024/zip/codebook24_llcp-v2-508.zip"


def sha256(ruta):
    """Recibe la ruta de un archivo y devuelve su huella SHA-256 como texto.
    Permite identificar la versión utilizada sin cargar todo el archivo en memoria.
    """
    with Path(ruta).open("rb") as archivo:
        return hashlib.file_digest(archivo, "sha256").hexdigest()


def extraer(ruta, destino=pb.RUTA_RAW, manifiesto=None, tamano_bloque=25000):
    """Recibe un XPT, un destino CSV, una ruta opcional de manifiesto y tamaño de bloque.
    Escribe la selección comprimida y devuelve un diccionario con su procedencia.
    Conserva todas las filas, su orden y los códigos publicados por CDC.
    """
    ruta, destino = Path(ruta), Path(destino)
    destino.parent.mkdir(parents=True, exist_ok=True)
    temporal = destino.with_suffix(destino.suffix + ".tmp")
    filas, columnas_origen = 0, None
    try:
        with pd.read_sas(ruta, format="xport", chunksize=tamano_bloque, encoding="utf-8") as lector:
            with temporal.open("wb") as archivo, gzip.GzipFile(fileobj=archivo, mode="wb", filename="", mtime=0) as comprimido:
                with io.TextIOWrapper(comprimido, encoding="utf-8", newline="") as texto:
                    for bloque in lector:
                        if columnas_origen is None:
                            columnas_origen = list(bloque.columns)
                        faltan = set(pb.COLUMNAS) - set(bloque.columns)
                        if faltan:
                            raise pb.ProyectoError(f"Faltan columnas en el XPT: {sorted(faltan)}")
                        bloque[pb.COLUMNAS].to_csv(texto, index=False, header=filas == 0, float_format="%.17g")
                        filas += len(bloque)
        if not filas:
            raise pb.ProyectoError("El XPT no contiene registros.")
        temporal.replace(destino)
    finally:
        temporal.unlink(missing_ok=True)
    datos = {"dataset": "BRFSS 2024", "publicador": "Centers for Disease Control and Prevention (CDC)",
             "pagina_fuente": FUENTE, "descarga": URL, "diccionario": DICCIONARIO,
             "archivo_xpt": ruta.name, "bytes_xpt": ruta.stat().st_size, "sha256_xpt": sha256(ruta),
             "filas": filas, "numero_columnas_xpt": len(columnas_origen), "columnas_xpt": columnas_origen,
             "columnas_seleccionadas": pb.COLUMNAS, "sha256_seleccion": sha256(destino),
             "operacion": "Selección de columnas; todas las filas, valores y orden conservados; sin limpieza",
             "nota_version": "La página anuncia 345 variables; el número efectivo se obtiene del XPT recibido."}
    if manifiesto:
        pb.guardar_json(datos, manifiesto)
    return datos


def main():
    """Lee de la terminal una ruta XPT/ZIP o la opción --descargar.
    Prepara la selección y su manifiesto, informa el resultado y devuelve None.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archivo", nargs="?", help="Archivo XPT o ZIP descargado de CDC")
    parser.add_argument("--descargar", action="store_true", help="Descargar el ZIP oficial")
    args = parser.parse_args()
    if bool(args.archivo) == args.descargar:
        parser.error("Indique un archivo o --descargar, pero no ambos.")
    with tempfile.TemporaryDirectory(prefix="brfss_") as carpeta:
        temporal = Path(carpeta)
        entrada = Path(args.archivo) if args.archivo else temporal / "LLCP2024XPT.zip"
        if args.descargar:
            print(f"Descargando {URL}", flush=True)
            with urllib.request.urlopen(URL, timeout=120) as respuesta, entrada.open("wb") as salida:
                shutil.copyfileobj(respuesta, salida)
        if zipfile.is_zipfile(entrada):
            with zipfile.ZipFile(entrada) as z:
                miembros = [n for n in z.namelist() if n.strip().lower().endswith(".xpt")]
                if len(miembros) != 1:
                    raise pb.ProyectoError("Se esperaba un único archivo XPT en el ZIP.")
                xpt = temporal / "LLCP2024.XPT"
                with z.open(miembros[0]) as origen, xpt.open("wb") as salida:
                    shutil.copyfileobj(origen, salida)
        else:
            xpt = entrada
        datos = extraer(xpt, manifiesto=pb.RAIZ / "docs/fuente_brfss.json")
        print(f"Preparadas {datos['filas']:,} filas y {len(pb.COLUMNAS)} columnas; XPT: {datos['numero_columnas_xpt']} columnas.")


if __name__ == "__main__":
    main()
