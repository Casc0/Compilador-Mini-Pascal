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


if __name__ == "__main__":
    unittest.main()
