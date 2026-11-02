import unittest

from util import compilar_texto, instrucciones, correr


class TestPrograma(unittest.TestCase):
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

    def test_booleanos_globales(self):
        self.assertEqual(correr("program p; var b: boolean; begin b := true; write(b) end."), [1])

    def test_comentario_con_linea_fuente(self):
        texto = compilar_texto("program p;\nvar a: integer;\nbegin\n  a := 1\nend.")
        self.assertIn("{ a := 1 }", texto)
        self.assertEqual(texto.count("{ a := 1 }"), 1)   # sólo en la primera instrucción de esa línea

    def test_texto_lo_entiende_el_interprete(self):
        self.assertEqual(correr("program p;\nbegin\n  write(2 + 3)\nend."), [5])


class TestExpresiones(unittest.TestCase):
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
        for expr, esperado in self.casos:
            with self.subTest(expr=expr):
                self.assertEqual(correr(f"program p; begin write({expr}) end."), esperado)

    def test_signo_aplica_al_primer_termino(self):
        self.assertEqual(instrucciones("program p; begin write(-2 * 3 + 1) end.")[1:-2],
                         ["APCT 2", "APCT 3", "MULT", "UMEN", "APCT 1", "SUMA"])


class TestSentencias(unittest.TestCase):
    def test_read_if_while(self):
        fuente = """program p; var n, s: integer;
        begin read(n); s := 0;
          while s <= n do s := s + 3;
          if s > 10 then write(1) else write(0);
          if s = 9 then write(s)
        end."""
        self.assertEqual(correr(fuente, [7]), [0, 9])

    def test_if_codigo_exacto(self):
        self.assertEqual(instrucciones("program p; begin if true then write(1) else write(2) end."), [
            "INPP", "APCT 1", "DSVF L1", "APCT 1", "IMPR",
            "DSVS L2", "L1 NADA", "APCT 2", "IMPR", "L2 NADA", "PARA"])

    def test_while_codigo_exacto(self):
        self.assertEqual(instrucciones("program p; begin while false do write(1) end."), [
            "INPP", "L1 NADA", "APCT 0", "DSVF L2", "APCT 1", "IMPR", "DSVS L1", "L2 NADA", "PARA"])


# Programa de MEPA2015 pág. 12, adaptado a la gramática: sin el ';' antes de else
# y write(n); write(g) porque write acepta una sola expresión.
FUENTE_P_N_G = """program ejemplo;
var k: integer;
procedure p(n: integer; g: integer);
var h: integer;
begin
  if n < 2 then h := g + n
  else begin
    h := g;
    p(n - 1, h);
    k := h;
    p(n - 2, g)
  end;
  write(n);
  write(g)
end;
begin
  k := 0;
  p(3, k)
end.
"""


class TestProcedimientos(unittest.TestCase):
    def test_procedimiento_del_apunte(self):
        self.assertEqual(correr(FUENTE_P_N_G), [1, 0, 0, 0, 2, 0, 1, 0, 3, 0])

    def test_misma_traduccion_que_el_apunte(self):
        from test_mepa import COD_P_N_G
        esperado = [' '.join(l.split()) for l in COD_P_N_G.splitlines() if l.strip()]
        self.assertEqual(instrucciones(FUENTE_P_N_G), esperado)

    def test_parametros_desplazamiento_negativo(self):
        cod = instrucciones("program p; procedure q(a, b: integer); begin write(a - b) end; begin q(5, 2) end.")
        self.assertIn("APVL 1,-4", cod)   # a, i=1, n=2
        self.assertIn("APVL 1,-3", cod)   # b
        self.assertIn("RTPR 1,2", cod)

    def test_procedimiento_sin_params_ni_locales(self):
        fuente = "program p; var x: integer; procedure q; begin x := x + 1 end; begin x := 0; q; q; write(x) end."
        self.assertEqual(correr(fuente), [2])
        cod = instrucciones(fuente)
        self.assertIn("RTPR 1,0", cod)
        self.assertNotIn("RMEM 0", cod)

    def test_anidado_accede_al_padre_y_global(self):
        fuente = """program p; var g: integer;
        procedure a; var x: integer;
          procedure b; begin x := x + g end;
        begin x := 10; b; write(x) end;
        begin g := 5; a end."""
        self.assertEqual(correr(fuente), [15])
        self.assertIn("ALVL 1,0", instrucciones(fuente))   # x desde b (nivel 2) se direcciona con nivel 1

    def test_read_en_parametro(self):
        fuente = "program p; procedure q(a: integer); begin read(a); write(a) end; begin q(0) end."
        self.assertEqual(correr(fuente, [42]), [42])


class TestFunciones(unittest.TestCase):
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
        cod = instrucciones("program p; function f(a, b: integer): integer; begin f := a end; begin write(f(1, 2)) end.")
        self.assertIn("ALVL 1,-5", cod)   # -(2+3)
        self.assertIn("RTPR 1,2", cod)

    def test_llamada_reserva_lugar_antes_de_los_argumentos(self):
        cod = instrucciones("program p; function f(a: integer): integer; begin f := a end; begin write(f(7)) end.")
        i = cod.index("L1 NADA")
        self.assertEqual(cod[i + 1:i + 5], ["RMEM 1", "APCT 7", "LLPR L2", "IMPR"])

    def test_funcion_booleana(self):
        fuente = """program p;
        function par(n: integer): boolean; begin par := n / 2 * 2 = n end;
        begin if par(4) and not par(3) then write(1) else write(0) end."""
        self.assertEqual(correr(fuente), [1])


if __name__ == "__main__":
    unittest.main()
