import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from compilador import compilar
from mepa import ejecutar


def _compilar(fuente):
    with tempfile.TemporaryDirectory() as d:
        ruta = os.path.join(d, "prueba.pas")
        with open(ruta, "w") as f:
            f.write(fuente)
        return compilar(ruta)


# Código MEPA tal como se escribe en el .mepa (columnas y comentarios).
def compilar_texto(fuente):
    return _compilar(fuente).texto()


# Instrucciones sin formato ni comentarios: "APVL 0,1", "L1 NADA", "L2 ENPR 1".
def instrucciones(fuente):
    return _compilar(fuente).instrucciones()


# Compila y ejecuta el texto generado; devuelve lo que imprime el programa.
def correr(fuente, entrada=()):
    return ejecutar(compilar_texto(fuente), entrada)
