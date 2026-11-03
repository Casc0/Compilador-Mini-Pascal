# Generador de Código MEPA — Plan de Implementación

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Extender el analizador semántico del TP1 para que, si el programa mini-Pascal no tiene errores, genere su traducción a código MEPA en un archivo `.mepa`.

**Architecture:** Traducción dirigida por la sintaxis en una sola pasada: cada método del parser descendente recursivo emite sus instrucciones MEPA a un buffer (`CodigoMepa`) mientras reconoce y chequea tipos, igual que hoy calcula tipos. La tabla de símbolos se amplía con nivel léxico y desplazamiento de cada variable/parámetro, y con la etiqueta de cada subprograma. Para verificar el código generado se escribe un intérprete MEPA mínimo en Python, usado sólo en los tests.

**Tech Stack:** Python 3.14, sólo biblioteca estándar (`unittest`, `tempfile`). PyInstaller para el `.exe` (como en el TP1).

**Spec:** `Codigo Intermedio/Trabajo Lab 2.pdf` + teoría en `Codigo Intermedio/Fuente/MEPA2015.pdf` y `Unidad_Mepa.pdf`.

## Global Constraints

- El TP1 (`AnalizadorSIntactico+TS/`) no se modifica; el TP2 vive en `Codigo Intermedio/`.
- Se mantienen las pautas del TP1: un solo archivo fuente, mismos mensajes de error, corta en el primer error sintáctico/semántico.
- Uso: `compilador <archivo.pas>` → escribe `<archivo>.mepa` al lado del fuente. Si hubo cualquier error (léxico, sintáctico o semántico) no se escribe el `.mepa`.
- Booleanos: `true` = 1, `false` = 0. `and`/`or` se evalúan completos (sin cortocircuito).
- No hay intérprete de la cátedra: el profesor revisa las traducciones **a mano**. El `.mepa` se optimiza para leerse, siguiendo el estilo de MEPA2015.
- Etiquetas: `L` + número (`L1`, `L2`, …). En if/while la etiqueta va con `NADA` (`L1 NADA`); la de un subprograma va en la línea de su `ENPR` (`L2 ENPR 1`), como en el apunte.
- Formato de línea en columnas: etiqueta (6 caracteres), mnemónico (6), argumentos separados por coma sin espacios (`APVL 1,-4`) y, opcionalmente, un comentario `{ ... }` alineado en la columna 26. Todo el formateo está en un único método (`CodigoMepa._formatear`).
- Comentarios: la primera instrucción generada desde una línea nueva del fuente lleva como comentario el texto de esa línea (sin espacios a los costados), p. ej. `{ if n < 2 then fact := 1 }`.
- `mepa.py` es la única forma de verificar las traducciones: tiene que aceptar exactamente el formato que genera el compilador (columnas, etiqueta junto a cualquier instrucción, comentarios `{ }`).
- `write(e)` → `IMPR`; `read(v)` → `LEER` + `ALVL`.
- Direcciones: programa principal nivel 0; un subprograma declarado en nivel m tiene cuerpo de nivel m+1. Locales con desplazamiento 0,1,2…; el i-ésimo de n parámetros, `-(n+3-i)`; el valor de retorno de una función, `-(n+3)`.

## Review Focus

1. **Error léxico** (el léxico informa y sigue): no debe quedar un `.mepa` generado de un programa con errores → test en Task 6.
2. **Recursión**: cada activación tiene sus propias locales; el ejemplo de `p(n,g)` de MEPA2015 y un factorial recursivo deben dar la salida correcta → Tasks 4 y 5.
3. **Acceso a variables de otro nivel** (global desde un procedimiento, local del padre desde un subprograma anidado) → Task 4.
4. **Llamada a función en medio de una expresión** (`x := 1 + f(2) * 3`): el `RMEM 1` se hace con operandos pendientes en la pila → Task 5.
5. **Ámbitos vacíos**: programa sin `var`, subprograma sin locales y/o sin parámetros; no se emite `RMEM 0`/`LMEM 0` y el retorno es `RTPR k,0` → Tasks 2 y 4.

---

## File Structure

| Archivo | Responsabilidad |
|---|---|
| `Codigo Intermedio/compilador.py` | Copia de `analizador.py` del TP1 + clase `CodigoMepa` + emisión en el parser + CLI nueva. |
| `Codigo Intermedio/mepa.py` | Intérprete MEPA mínimo (`ejecutar`). Usado por los tests; también sirve para mostrar ejecuciones en el informe. |
| `Codigo Intermedio/tests/util.py` | Helpers: compilar un string fuente y correrlo. |
| `Codigo Intermedio/tests/test_mepa.py` | Tests del intérprete. |
| `Codigo Intermedio/tests/test_generacion.py` | Tests del compilador (código generado + salida al ejecutarlo). |
| `Codigo Intermedio/pruebas/*.pas` | Fuentes de ejemplo para el informe y la entrega. |

Correr todos los tests (desde `Codigo Intermedio/`): `python -m unittest discover -s tests -v`

---

### Task 1: Intérprete MEPA para tests

**Files:**
- Create: `Codigo Intermedio/mepa.py`
- Test: `Codigo Intermedio/tests/test_mepa.py`

**Interfaces:**
- Produces: `ejecutar(codigo: str, entrada: list[int] = ()) -> list[int]` (devuelve los valores impresos en orden); `class MepaError(Exception)`.

- [ ] **Step 1: Escribir los tests**

```python
class TestMepa(unittest.TestCase):
    def test_expresion_del_apunte(self):
        # a + (b/9 - 3) * c con a=1 (0,0), b=20 (0,1), c=4 (0,2)
        cod = "INPP\nRMEM 3\nAPCT 1\nALVL 0,0\nAPCT 20\nALVL 0,1\nAPCT 4\nALVL 0,2\n" \
              "APVL 0,0\nAPVL 0,1\nAPCT 9\nDIVI\nAPCT 3\nSUST\nAPVL 0,2\nMULT\nSUMA\nIMPR\nLMEM 3\nPARA"
        self.assertEqual(ejecutar(cod), [-3])          # 1 + (2-3)*4

    def test_while_y_leer(self):
        # read(n); s := 0; while s <= n do s := s + 3; write(s)
        cod = "INPP\nRMEM 2\nLEER\nALVL 0,0\nAPCT 0\nALVL 0,1\nL1 NADA\nAPVL 0,1\nAPVL 0,0\nCMNI\n" \
              "DSVF L2\nAPVL 0,1\nAPCT 3\nSUMA\nALVL 0,1\nDSVS L1\nL2 NADA\nAPVL 0,1\nIMPR\nLMEM 2\nPARA"
        self.assertEqual(ejecutar(cod, [7]), [9])

    def test_procedimiento_del_apunte(self):
        # Traducción de MEPA2015 pág. 13-14 (program ejemplo con p(n,g)), copiada literal
        self.assertEqual(ejecutar(COD_P_N_G), [1, 0, 0, 0, 2, 0, 1, 0, 3, 0])

    def test_error_division_por_cero(self):
        with self.assertRaises(MepaError):
            ejecutar("INPP\nAPCT 1\nAPCT 0\nDIVI\nPARA")

    def test_loop_infinito_corta(self):
        with self.assertRaises(MepaError):
            ejecutar("INPP\nL1 NADA\nDSVS L1\nPARA")
```

`COD_P_N_G` es la traducción del apunte (MEPA2015 págs. 13-14, INPP … PARA) escrita como string en el test, con `L1..L4` en lugar de `l1..l4`. Traza: p(3,0) → p(2,0) → p(1,0) imprime 1,0; p(0,0) imprime 0,0; p(2,0) imprime 2,0; p(1,0) imprime 1,0; p(3,0) imprime 3,0.

- [ ] **Step 2: Correr y verificar que fallan** — `python -m unittest tests.test_mepa -v` → `ModuleNotFoundError: mepa`.

- [ ] **Step 3: Implementar `ejecutar` en `mepa.py`**

Primera pasada: partir en líneas, sacar comentarios `{...}`, ignorar líneas vacías; si el primer token matchea `L\d+` es etiqueta (guardar `etiqueta -> índice`, vale con cualquier instrucción, no sólo `NADA`), resto = mnemónico + args (`split(',')`, a `int`). Agregar un test con una línea `L2      ENPR  1     { procedure p }`. Segunda pasada: loop con `i`, `s`, `M` (lista que crece), `D` (dict). Semántica exacta de cada instrucción = tablas de MEPA2015 (INPP: `s=-1; D[0]=0`). `DIVI` con divisor 0 → `MepaError`; división que trunca hacia cero (`int(a/b)`), igual que `div` de Pascal. Límite de 1.000.000 de pasos → `MepaError`. Mnemónico desconocido o etiqueta inexistente → `MepaError`. Instrucciones: `INPP PARA RMEM LMEM APCT APVL ALVL SUMA SUST MULT DIVI MODU UMEN CONJ DISJ NEGA CMME CMMA CMIG CMDG CMNI CMYI DSVS DSVF NADA LEER LELN IMPR IMLN ENPR LLPR RTPR`.

- [ ] **Step 4: Correr los tests** → PASS.

- [ ] **Step 5: Commit** — `git add "Codigo Intermedio/mepa.py" "Codigo Intermedio/tests"` ; `git commit -m "Interprete MEPA para tests"`

---

### Task 2: Esqueleto del compilador — programa, variables globales, asignación, write

**Files:**
- Create: `Codigo Intermedio/compilador.py` (copia de `AnalizadorSIntactico+TS/analizador.py`)
- Create: `Codigo Intermedio/tests/util.py`
- Test: `Codigo Intermedio/tests/test_generacion.py`

**Interfaces:**
- Consumes: `ejecutar` (Task 1).
- Produces:
  - `class CodigoMepa`: `nueva_etiqueta() -> str`; `emitir(instr: str, *args: int, etiqueta: str | None = None, comentario: str | None = None)`; `emitir_etiqueta(etq: str)` (= `emitir('NADA', etiqueta=etq)`); `instrucciones() -> list[str]` (sin columnas ni comentarios: `"INPP"`, `"APVL 0,1"`, `"L1 NADA"`, `"L2 ENPR 1"` — es lo que comparan los tests); `texto() -> str` (formato en columnas con comentarios, `\n` final).
  - Comentarios: `LexiAnalyzer` guarda las líneas del fuente (`self.lineas: list[str]`). `Parser` lleva `self._ultima_linea_comentada`; en un helper `Parser._emitir(instr, *args, etiqueta=None)` se usa la línea del último token consumido y, si es distinta de la última comentada, se pasa `comentario=lineas[n-1].strip()`. Todo el parser emite a través de `_emitir`.
  - `SymbolTableEntry` gana `nivel: int`, `desplazamiento: int`, `etiqueta: str | None`.
  - `SymbolTable` gana `nivel: int` y `cant_locales: int` (cantidad de VARIABLE declaradas en ese ámbito).
  - `Parser.codigo: CodigoMepa`; `Parser.new_table(name)` asigna `nivel = len(scopeStack)` (antes del push) → global 0.
  - `compilar(ruta_pas: str) -> CodigoMepa` (lanza `ParserError`; el CLI llama `.texto()`).
  - `tests/util.py`: `compilar_texto(fuente: str) -> str` (archivo temporal → `compilar(...).texto()`), `instrucciones(fuente: str) -> list[str]` (→ `compilar(...).instrucciones()`) y `correr(fuente: str, entrada=()) -> list[int]` (ejecuta `compilar_texto`, o sea el texto real con columnas y comentarios).

- [ ] **Step 1: Escribir los tests**

```python
def test_programa_simple_codigo_exacto(self):
    fuente = "program p; var a, b: integer; begin a := 1; b := 4; write(a + b) end."
    self.assertEqual(instrucciones(fuente), [
        "INPP", "RMEM 2",
        "APCT 1", "ALVL 0,0", "APCT 4", "ALVL 0,1",
        "APVL 0,0", "APVL 0,1", "SUMA", "IMPR",
        "LMEM 2", "PARA"])

def test_programa_sin_var(self):
    self.assertEqual(instrucciones("program p; begin write(7) end."),
                     ["INPP", "APCT 7", "IMPR", "PARA"])

def test_comentario_con_linea_fuente(self):
    texto = compilar_texto("program p;\nvar a: integer;\nbegin\n  a := 1\nend.")
    self.assertIn("{ a := 1 }", texto)
    self.assertEqual(texto.count("{ a := 1 }"), 1)   # sólo en la primera instrucción de esa línea

def test_texto_lo_entiende_el_interprete(self):
    self.assertEqual(correr("program p;\nbegin\n  write(2 * 3)\nend."), [6])

def test_booleanos_globales(self):
    self.assertEqual(correr("program p; var b: boolean; begin b := true; write(b) end."), [1])
```

(En este punto la suma ya hace falta para el primer test; el resto de operadores van en la Task 3.)

- [ ] **Step 2: Correr y verificar que fallan.**

- [ ] **Step 3: Implementar**
  - Copiar `analizador.py` → `compilador.py`; actualizar el comentario de cabecera y el mensaje de uso (`compilador <archivo.pas>`).
  - `CodigoMepa` como se describe arriba; `_formatear(etq, instr, args)` es el único lugar que arma el texto.
  - Al declarar una VARIABLE: `entry.nivel = tabla.nivel; entry.desplazamiento = tabla.cant_locales; tabla.cant_locales += 1`.
  - `_statement`: `INPP` antes de `_bloque`, `PARA` al final.
  - `_bloque` recibe cuándo emitir `RMEM`/`LMEM`: después de `_sentencia_de_tipos` emite `RMEM n` si `n > 0`; al terminar `_cuerpo`, `LMEM n` si `n > 0`. (Para subprogramas el bloque se completa en la Task 4.)
  - `_sentencia_prima` (asignación a variable): después de `_expresion()`, `ALVL entry.nivel,entry.desplazamiento`.
  - `_factor`: `NUM` → `APCT valor`; `TRUE`/`FALSE` → `APCT 1`/`APCT 0`; variable → `APVL nivel,desplazamiento`. `_numero` debe devolver el valor del token.
  - `_lista_expresion_simple`: después del término derecho, `ADD` → `SUMA`.
  - `_escritura`: `IMPR` después de la expresión.
  - `compilar(ruta)` crea `Parser`, llama `parse()`, devuelve `parser.codigo`.

- [ ] **Step 4: Correr los tests** → PASS (incluidos los de la Task 1).

- [ ] **Step 5: Commit** — `git commit -m "Compilador: esqueleto de generacion MEPA"`

---

### Task 3: Expresiones completas

**Files:**
- Modify: `Codigo Intermedio/compilador.py` (métodos `_expresion_prima`, `_expresion_simple`, `_lista_expresion_simple`, `_lista_terminos`, `_factor`)
- Test: `Codigo Intermedio/tests/test_generacion.py`

**Interfaces:**
- Produces: tabla `INSTR_OP = {'ADD':'SUMA','SUB':'SUST','MUL':'MULT','DIV':'DIVI','AND':'CONJ','OR':'DISJ','LT':'CMME','LE':'CMNI','GT':'CMMA','GE':'CMYI','EQ':'CMIG','NE':'CMDG'}` a nivel módulo.

- [ ] **Step 1: Escribir los tests** (cada uno con `correr`, imprimiendo el resultado):

```python
casos = [
    ("1 + (20 / 9 - 3) * 4", [-3]),
    ("-5 + 2", [-3]),            # signo unario -> UMEN sobre el primer término
    ("-(2 * 3)", [-6]),
    ("+4", [4]),                 # '+' unario no emite nada
    ("7 - 2 - 1", [4]),          # asociatividad izquierda
    ("3 < 4", [1]), ("3 <= 3", [1]), ("3 > 4", [0]), ("3 >= 4", [0]),
    ("3 = 3", [1]), ("3 <> 3", [0]), ("true = false", [0]),
    ("true and false", [0]), ("true or false", [1]),
    ("not (1 > 2)", [1]), ("not true or true", [1]),
]
def test_expresiones(self):
    for expr, esperado in casos:
        with self.subTest(expr=expr):
            self.assertEqual(correr(f"program p; begin write({expr}) end."), esperado)
```

- [ ] **Step 2: Correr y verificar que fallan.**
- [ ] **Step 3: Implementar.** Regla: emitir la instrucción del operador **después** de reconocer el operando derecho (orden postfijo). Signo unario `SUB` → `UMEN` después del primer `_termino`; `NOT` → `NEGA` después del `_factor`.
- [ ] **Step 4: Correr los tests** → PASS.
- [ ] **Step 5: Commit** — `git commit -m "Generacion MEPA de expresiones"`

---

### Task 4: read, if, while y procedimientos

**Files:**
- Modify: `Codigo Intermedio/compilador.py` (`_lectura`, `_alternativa`, `_alternativa_prima`, `_repetitiva`, `_bloque`, `_procedimiento`, `_procedimiento_prima`, `_param_formales`, `_sentencia_prima`)
- Test: `Codigo Intermedio/tests/test_generacion.py`

**Interfaces:**
- Produces: `entry.etiqueta` de cada subprograma (asignada al declararlo, antes de analizar su cuerpo, para que funcione la recursión); `entry.nivel` de un subprograma = nivel de su propio ámbito (el de su cuerpo); helper `Parser._ubicar_parametros(entry)` que, al cerrar el paréntesis, recorre los PARAMETER del ámbito actual en orden y les pone `nivel` y `desplazamiento = -(n+3-i)`.

Esquemas de traducción (MEPA2015):

```
if E then C1 else C2:   E; DSVF Lf; C1; DSVS Lfin; Lf NADA; C2; Lfin NADA
if E then C1:           E; DSVF Lf; C1; Lf NADA
while E do C:           Lini NADA; E; DSVF Lfin; C; DSVS Lini; Lfin NADA
read(v):                LEER; ALVL nivel,desp
bloque de programa/subprograma con subprogramas anidados:
    [ENPR k]  RMEM n  DSVS Lcuerpo  <subprogramas>  Lcuerpo NADA  <cuerpo>  LMEM n  [RTPR k,p]
subprograma:            Lp ENPR k   (la etiqueta va en la misma línea que el ENPR)
llamada a procedimiento: <argumentos en orden> LLPR Lp
```

El `DSVS` para saltear subprogramas sólo se emite si el bloque tiene subprogramas. Test extra: `instrucciones(...)` de un programa con un procedimiento contiene `"L2 ENPR 1"` y empieza `["INPP", ..., "DSVS L1", "L2 ENPR 1", ...]` (la etiqueta del salto se pide antes que la del procedimiento, como en el apunte).

- [ ] **Step 1: Escribir los tests**

```python
def test_read_if_while(self):
    fuente = """program p; var n, s: integer;
    begin read(n); s := 0;
      while s <= n do s := s + 3;
      if s > 10 then write(1) else write(0);
      if s = 9 then write(s)
    end."""
    self.assertEqual(correr(fuente, [7]), [0, 9])

def test_if_codigo_exacto(self):
    self.assertEqual(instrucciones("program p; begin if true then write(1) else write(2) end."), ["INPP", "APCT 1", "DSVF L1", "APCT 1", "IMPR",
        "DSVS L2", "L1 NADA", "APCT 2", "IMPR", "L2 NADA", "PARA"])

def test_procedimiento_del_apunte(self):
    # Programa de MEPA2015 pág. 12, adaptado a la gramática: sin el ';' antes de else
    # y write(n); write(g) porque write acepta una sola expresión.
    self.assertEqual(correr(FUENTE_P_N_G), [1, 0, 0, 0, 2, 0, 1, 0, 3, 0])

def test_parametros_desplazamiento_negativo(self):
    cod = compilar_texto("program p; procedure q(a, b: integer); begin write(a - b) end; begin q(5, 2) end.")
    self.assertIn("APVL 1,-4", cod)   # a, i=1, n=2
    self.assertIn("APVL 1,-3", cod)   # b
    self.assertIn("RTPR 1,2", cod)

def test_procedimiento_sin_params_ni_locales(self):
    fuente = "program p; var x: integer; procedure q; begin x := x + 1 end; begin x := 0; q; q; write(x) end."
    self.assertEqual(correr(fuente), [2])
    self.assertIn("RTPR 1,0", compilar_texto(fuente))

def test_anidado_accede_al_padre_y_global(self):
    fuente = """program p; var g: integer;
    procedure a; var x: integer;
      procedure b; begin x := x + g end;
    begin x := 10; b; write(x) end;
    begin g := 5; a end."""
    self.assertEqual(correr(fuente), [15])

def test_read_en_parametro(self):
    fuente = "program p; procedure q(a: integer); begin read(a); write(a) end; begin q(0) end."
    self.assertEqual(correr(fuente, [42]), [42])
```

- [ ] **Step 2: Correr y verificar que fallan.**
- [ ] **Step 3: Implementar** los esquemas de arriba. `_procedimiento`: declarar entrada, `entry.etiqueta = nueva_etiqueta()`, abrir ámbito, `emitir_etiqueta`, `ENPR nivel`; el bloque emite RMEM/DSVS/LMEM; al final `RTPR nivel,len(entry.params)`. Asignar a un PARAMETER usa `ALVL` igual que a una variable.
- [ ] **Step 4: Correr los tests** → PASS.
- [ ] **Step 5: Commit** — `git commit -m "Generacion MEPA de read, if, while y procedimientos"`

---

### Task 5: Funciones

**Files:**
- Modify: `Codigo Intermedio/compilador.py` (`_funcion`, `_funcion_prima`, `_factor`, `_sentencia_prima`)
- Test: `Codigo Intermedio/tests/test_generacion.py`

**Interfaces:**
- Consumes: `_ubicar_parametros`, esquema de bloque de la Task 4.
- Produces: la entrada de la función guarda `entry.desplazamiento = -(n+3)` y `entry.nivel` = nivel de su cuerpo (para `f := expr` → `ALVL nivel,-(n+3)`).

Esquemas: llamada en expresión → `RMEM 1; <argumentos>; LLPR Lf` (el resultado queda en el tope). Cuerpo: igual que un procedimiento.

- [ ] **Step 1: Escribir los tests**

```python
def test_factorial_recursivo(self):
    fuente = """program p; var a: integer;
    function fact(n: integer): integer;
    begin if n < 2 then fact := 1 else fact := fact(n - 1) * n end;
    begin read(a); write(fact(a)) end."""
    self.assertEqual(correr(fuente, [5]), [120])

def test_funcion_en_medio_de_expresion(self):
    fuente = """program p; var x: integer;
    function f(a: integer): integer; begin f := a * 10 end;
    begin x := 1 + f(2) * 3; write(x) end."""
    self.assertEqual(correr(fuente), [61])

def test_funcion_sin_parametros(self):
    fuente = "program p; function c: integer; begin c := 3 end; begin write(c + c) end."
    self.assertEqual(correr(fuente), [6])

def test_dos_llamadas_recursivas(self):
    fuente = """program p;
    function fib(n: integer): integer;
    begin if n < 2 then fib := n else fib := fib(n - 1) + fib(n - 2) end;
    begin write(fib(10)) end."""
    self.assertEqual(correr(fuente), [55])

def test_retorno_desplazamiento(self):
    cod = compilar_texto("program p; function f(a, b: integer): integer; begin f := a end; begin write(f(1, 2)) end.")
    self.assertIn("ALVL 1,-5", cod)   # -(2+3)
    self.assertIn("RTPR 1,2", cod)
```

- [ ] **Step 2: Correr y verificar que fallan.**
- [ ] **Step 3: Implementar.** En `_factor`, si la entrada es FUNCTION: `RMEM 1` **antes** de `_llamada_funcion()` (los argumentos se apilan arriba del lugar reservado) y `LLPR` después. Una función declarada en el ámbito global sin parámetros y usada sin paréntesis también es una llamada (el TP1 ya lo admite cuando no es la función actual).
- [ ] **Step 4: Correr los tests** → PASS.
- [ ] **Step 5: Commit** — `git commit -m "Generacion MEPA de funciones"`

---

### Task 6: CLI, errores, ejemplos de entrega y ejecutable

**Files:**
- Modify: `Codigo Intermedio/compilador.py` (`LexiAnalyzer`, `__main__`)
- Create: `Codigo Intermedio/pruebas/` con al menos: `locales.pas`, `parametros_funcion.pas`, `condicional.pas`, `repetitiva.pas`, `completo.pas` (las cuatro estructuras que pide el informe + uno integrador), y los `.pas` de error del TP1 copiados de `AnalizadorSIntactico+TS/pruebas/`.
- Test: `Codigo Intermedio/tests/test_generacion.py`

**Interfaces:**
- Produces: `LexiAnalyzer.hubo_errores: bool` (lo pone en `True` `print_error`). `compilar` lanza `ParserError("Hubo errores léxicos: no se genera código")` si quedó en `True` después de `parse()`.
- CLI: éxito → escribe `<archivo>.mepa`, imprime `Compilación exitosa: <ruta.mepa>` y luego las tablas de símbolos (como el TP1); error → imprime el error, sale con código 1, no escribe nada (y no deja un `.mepa` viejo con contenido nuevo parcial: se escribe recién al final).

- [ ] **Step 1: Escribir los tests**

```python
def test_error_lexico_no_genera(self):
    with self.assertRaises(ParserError):
        compilar_texto("program p; var a: integer; begin a := 1 # end.")

def test_cli_genera_archivo(self):
    # subprocess.run([sys.executable, "compilador.py", ruta_tmp]) sobre un .pas válido:
    # returncode 0 y existe ruta_tmp con extensión .mepa, cuyo contenido es compilar(ruta)

def test_cli_error_no_genera(self):
    # .pas con error semántico: returncode 1 y no existe el .mepa

def test_pruebas_ok_compilan_y_corren(self):
    # cada pruebas/*.pas que no empiece con lex_/sin_/sem_ compila y ejecuta sin MepaError
```

- [ ] **Step 2: Correr y verificar que fallan.**
- [ ] **Step 3: Implementar** lo de arriba y escribir los `.pas` de ejemplo (cortos, uno por estructura pedida en el punto 2.d del TP).
- [ ] **Step 4: Correr todos los tests** → PASS. Generar los `.mepa` de `pruebas/` (quedan al lado de cada `.pas`, versionados, porque son los que van al informe) y revisarlos a ojo como lo haría el profesor: cada comentario `{ }` junto a las instrucciones que corresponden y los desplazamientos coinciden con las fórmulas del apunte.
- [ ] **Step 5: Ejecutable** — `pyinstaller --onefile --name compilador compilador.py` desde `Codigo Intermedio/`; probar `dist/compilador.exe pruebas/completo.pas`.
- [ ] **Step 6: Commit** — `git commit -m "CLI del compilador MEPA y ejemplos"` (sin `build/`, `dist/`, `*.exe`, ya ignorados).

---

## Fuera de este plan

- El **informe** (punto 2 del TP) se escribe aparte, usando los `.pas`/`.mepa` de `pruebas/` como ejemplos comentados.
- Si la cátedra provee un intérprete MEPA con otro formato de etiquetas/argumentos, se ajusta sólo `CodigoMepa._formatear` (y el parser de `mepa.py`).
