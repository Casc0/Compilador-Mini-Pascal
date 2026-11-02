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


if __name__ == "__main__":
    unittest.main()
