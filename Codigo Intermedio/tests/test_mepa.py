import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mepa import ejecutar, MepaError

# Traducción del programa con p(n,g) de MEPA2015 (págs. 13-14), con L1..L4 en lugar de l1..l4.
COD_P_N_G = """
        INPP
        RMEM  1
        DSVS  L1
L2      ENPR  1
        RMEM  1
        APVL  1,-4
        APCT  2
        CMME
        DSVF  L3
        APVL  1,-3
        APVL  1,-4
        SUMA
        ALVL  1,0
        DSVS  L4
L3      NADA
        APVL  1,-3
        ALVL  1,0
        APVL  1,-4
        APCT  1
        SUST
        APVL  1,0
        LLPR  L2
        APVL  1,0
        ALVL  0,0
        APVL  1,-4
        APCT  2
        SUST
        APVL  1,-3
        LLPR  L2
L4      NADA
        APVL  1,-4
        IMPR
        APVL  1,-3
        IMPR
        LMEM  1
        RTPR  1,2
L1      NADA
        APCT  0
        ALVL  0,0
        APCT  3
        APVL  0,0
        LLPR  L2
        LMEM  1
        PARA
"""


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
        # Traza: p(3,0) -> p(2,0) -> p(1,0) imprime 1,0; p(0,0) imprime 0,0; p(2,0) imprime 2,0;
        # p(1,0) imprime 1,0; p(3,0) imprime 3,0.
        self.assertEqual(ejecutar(COD_P_N_G), [1, 0, 0, 0, 2, 0, 1, 0, 3, 0])

    def test_columnas_y_comentarios(self):
        cod = "        INPP                { program p; }\n" \
              "        DSVS  L1\n" \
              "L2      ENPR  1             { procedure q; }\n" \
              "        APCT  5\n" \
              "        IMPR\n" \
              "        RTPR  1,0\n" \
              "\n" \
              "L1      NADA\n" \
              "        LLPR  L2            { q }\n" \
              "        PARA"
        self.assertEqual(ejecutar(cod), [5])

    def test_negacion_y_division_trunca_hacia_cero(self):
        cod = "INPP\nAPCT 7\nUMEN\nAPCT 2\nDIVI\nIMPR\nAPCT 1\nNEGA\nIMPR\nPARA"
        self.assertEqual(ejecutar(cod), [-3, 0])

    def test_error_division_por_cero(self):
        with self.assertRaises(MepaError):
            ejecutar("INPP\nAPCT 1\nAPCT 0\nDIVI\nPARA")

    def test_loop_infinito_corta(self):
        with self.assertRaises(MepaError):
            ejecutar("INPP\nL1 NADA\nDSVS L1\nPARA")

    def test_instruccion_desconocida(self):
        with self.assertRaises(MepaError):
            ejecutar("INPP\nFRUTA\nPARA")

    def test_etiqueta_inexistente(self):
        with self.assertRaises(MepaError):
            ejecutar("INPP\nDSVS L9\nPARA")


if __name__ == "__main__":
    unittest.main()
