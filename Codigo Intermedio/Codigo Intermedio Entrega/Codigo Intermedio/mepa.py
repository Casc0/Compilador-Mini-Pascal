# Intérprete de la Máquina de Ejecución para Pascal (MEPA).
# Uso: python mepa.py <archivo.mepa> [valores de entrada para LEER...]
# Muestra cada instrucción ejecutada con el estado de la pila después de ejecutarla.
# Implementa las instrucciones descriptas en el apunte MEPA2015. Lo usamos para verificar
# que el código que genera el compilador hace lo que tiene que hacer.

import re
import sys

MAX_PASOS = 1_000_000

# Cantidad de argumentos de cada instrucción.
ARIDAD = {
    'INPP': 0, 'PARA': 0, 'RMEM': 1, 'LMEM': 1, 'APCT': 1, 'APVL': 2, 'ALVL': 2,
    'SUMA': 0, 'SUST': 0, 'MULT': 0, 'DIVI': 0, 'MODU': 0, 'UMEN': 0,
    'CONJ': 0, 'DISJ': 0, 'NEGA': 0,
    'CMME': 0, 'CMMA': 0, 'CMIG': 0, 'CMDG': 0, 'CMNI': 0, 'CMYI': 0,
    'DSVS': 1, 'DSVF': 1, 'NADA': 0, 'LEER': 0, 'LELN': 0, 'IMPR': 0, 'IMLN': 0,
    'ENPR': 1, 'LLPR': 1, 'RTPR': 2,
}

# Operaciones binarias: M[s-1] := M[s-1] op M[s]; s := s-1
BINARIAS = {
    'SUMA': lambda a, b: a + b,
    'SUST': lambda a, b: a - b,
    'MULT': lambda a, b: a * b,
    'CONJ': lambda a, b: int(a == 1 and b == 1),
    'DISJ': lambda a, b: int(a == 1 or b == 1),
    'CMME': lambda a, b: int(a < b),
    'CMMA': lambda a, b: int(a > b),
    'CMIG': lambda a, b: int(a == b),
    'CMDG': lambda a, b: int(a != b),
    'CMNI': lambda a, b: int(a <= b),
    'CMYI': lambda a, b: int(a >= b),
}


class MepaError(Exception):
    pass


# Devuelve la lista de instrucciones (mnemónico, args, texto, encabezado) y el diccionario
# etiqueta -> índice. Acepta comentarios { ... } y una etiqueta L<n> delante de cualquier instrucción.
# Una línea que sólo tiene un comentario (la línea del fuente) es el encabezado de la instrucción siguiente.
def _cargar(codigo):
    programa, etiquetas = [], {}
    encabezado = None
    for nro, linea in enumerate(codigo.splitlines(), 1):
        comentario = re.search(r'\{[^}]*\}', linea)
        linea = re.sub(r'\{[^}]*\}', '', linea).strip()
        if not linea:
            if comentario:
                encabezado = comentario.group(0)
            continue
        partes = linea.split(None, 1)
        if re.fullmatch(r'L\d+', partes[0]):
            etiquetas[partes[0]] = len(programa)
            partes = partes[1].split(None, 1) if len(partes) > 1 else []
            if not partes:
                raise MepaError(f"línea {nro}: etiqueta sin instrucción")
        instr = partes[0]
        args = [a.strip() for a in partes[1].split(',')] if len(partes) > 1 else []
        if instr not in ARIDAD:
            raise MepaError(f"línea {nro}: instrucción desconocida '{instr}'")
        if len(args) != ARIDAD[instr]:
            raise MepaError(f"línea {nro}: '{instr}' espera {ARIDAD[instr]} argumentos")
        if instr not in ('DSVS', 'DSVF', 'LLPR'):
            try:
                args = [int(a) for a in args]
            except ValueError:
                raise MepaError(f"línea {nro}: argumento no numérico en '{linea}'")
        programa.append((instr, args, ' '.join(linea.split()), encabezado))
        encabezado = None
    return programa, etiquetas


# Contenido de la pila del fondo al tope ('?' si la posición no tiene valor), con una
# marca |Dk| donde apunta D[k] para cada subprograma activo.
def _mostrar_pila(M, D, s, activos):
    marcas = {}
    for k in sorted(set(activos)):
        marcas.setdefault(D[k], []).append(f"|D{k}|")
    partes = []
    for pos in range(s + 2):
        partes += marcas.get(pos, [])
        if pos <= s:
            partes.append(str(M[pos]) if pos in M else '?')
    return ' '.join(partes)


# Ejecuta el código y devuelve la lista de valores impresos.
# Si se pasa 'traza', se la llama con una línea de texto por cada instrucción ejecutada.
def ejecutar(codigo, entrada=(), traza=None):
    programa, etiquetas = _cargar(codigo)
    entrada = list(entrada)
    salida = []
    M, D = {}, {}
    i, s = 0, -1
    activos = []        # niveles de los subprogramas en ejecución, para la traza

    def registrar(texto, impreso=None):
        if traza is None:
            return
        linea = f"{texto:<16}{_mostrar_pila(M, D, s, activos)}".rstrip()
        if impreso is not None:
            linea += f"   => imprime {impreso}"
        traza(linea)

    def destino(etq):
        if etq not in etiquetas:
            raise MepaError(f"etiqueta inexistente '{etq}'")
        return etiquetas[etq]

    def leer(pos):
        if pos not in M:
            raise MepaError(f"lectura de una posición sin valor: M[{pos}]")
        return M[pos]

    for _ in range(MAX_PASOS):
        if not 0 <= i < len(programa):
            raise MepaError("el programa terminó sin PARA")
        instr, args, texto, encabezado = programa[i]
        if traza is not None and encabezado:
            traza(encabezado)
        i += 1
        impreso = None
        match instr:
            case 'INPP':
                s = -1
                D[0] = 0
            case 'PARA':
                registrar(texto)
                return salida
            case 'RMEM':
                s += args[0]
            case 'LMEM':
                s -= args[0]
            case 'APCT':
                s += 1
                M[s] = args[0]
            case 'APVL':
                s += 1
                M[s] = leer(D[args[0]] + args[1])
            case 'ALVL':
                M[D[args[0]] + args[1]] = leer(s)
                s -= 1
            case op if op in BINARIAS:
                M[s - 1] = BINARIAS[op](leer(s - 1), leer(s))
                s -= 1
            case 'DIVI' | 'MODU':
                if leer(s) == 0:
                    raise MepaError("división por cero")
                a, b = leer(s - 1), leer(s)
                M[s - 1] = int(a / b) if instr == 'DIVI' else a - int(a / b) * b
                s -= 1
            case 'UMEN':
                M[s] = -leer(s)
            case 'NEGA':
                M[s] = 1 - leer(s)
            case 'DSVS':
                i = destino(args[0])
            case 'DSVF':
                if leer(s) == 0:
                    i = destino(args[0])
                s -= 1
            case 'NADA':
                pass
            case 'LEER' | 'LELN':
                if not entrada:
                    raise MepaError("no quedan valores de entrada para LEER")
                s += 1
                M[s] = entrada.pop(0)
            case 'IMPR' | 'IMLN':
                impreso = leer(s)
                salida.append(impreso)
                s -= 1
            case 'ENPR':
                s += 1
                M[s] = D.get(args[0], 0)
                D[args[0]] = s + 1
                activos.append(args[0])
            case 'LLPR':
                s += 1
                M[s] = i
                i = destino(args[0])
            case 'RTPR':
                D[args[0]] = leer(s)
                i = leer(s - 1)
                s -= args[1] + 2
                activos.pop()   # las llamadas se anidan: se cierra la última que entró
        registrar(texto, impreso)
    raise MepaError(f"se superaron los {MAX_PASOS} pasos (¿loop infinito?)")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Utilizar el comando: python mepa.py <archivo.mepa> [valores de entrada...]")
        sys.exit(1)
    try:
        with open(sys.argv[1]) as f:
            codigo = f.read()
        ejecutar(codigo, [int(v) for v in sys.argv[2:]], traza=print)
    except MepaError as e:
        print(f"Error de ejecución MEPA: {e}")
        sys.exit(1)
