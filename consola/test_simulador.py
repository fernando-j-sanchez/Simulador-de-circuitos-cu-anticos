"""Pruebas: python -m unittest test_simulador.py (desde la carpeta consola/)."""
import math
import unittest

import simulador as sim

S2 = 1 / math.sqrt(2)


def expected(a, b, c):
    """Resultado cerrado: |abc⟩ → (−1)^(abc) · |a⟩ ⊗ |b⟩ ⊗ H|b ⊕ c⟩."""
    sign = -1 if a & b & c else 1
    d = b ^ c
    out = [0.0] * 8
    out[(a << 2) | (b << 1)] = sign * S2
    out[(a << 2) | (b << 1) | 1] = sign * S2 * (-1 if d else 1)
    return out


class TestCircuito2(unittest.TestCase):
    def test_entradas_base(self):
        for x in range(8):
            a, b, c = (x >> 2) & 1, (x >> 1) & 1, x & 1
            psi = [1.0 if i == x else 0.0 for i in range(8)]
            final = sim.run_circuit(psi)[-1]
            for got, exp in zip(final, expected(a, b, c)):
                self.assertAlmostEqual(complex(got), exp)

    def test_medicion_q1_devuelve_b(self):
        for x in range(8):
            b = (x >> 1) & 1
            final = sim.run_circuit([1.0 if i == x else 0.0 for i in range(8)])[-1]
            p, _ = sim.collapse(final, 1, b)
            self.assertAlmostEqual(p, 1.0)

    def test_norma_con_superposicion(self):
        psi = sim.tensor((S2, S2), (0.6, 0.8j), (S2, -S2))
        for st in sim.run_circuit(psi):
            self.assertAlmostEqual(sum(abs(a) ** 2 for a in st), 1.0)

    def test_parse_complex(self):
        self.assertAlmostEqual(sim.parse_complex("1/√2"), S2)
        self.assertAlmostEqual(sim.parse_complex("0.8i"), 0.8j)
        self.assertAlmostEqual(sim.parse_complex("-i/sqrt(2)"), -1j * S2)
        with self.assertRaises(Exception):
            sim.parse_complex("__import__('os')")

    def test_ket_str(self):
        self.assertEqual(sim.ket_str([0, 0, 0, 0, 0, 0, 1, 0]), "|110⟩")
        self.assertEqual(sim.ket_str([S2, -S2, 0, 0, 0, 0, 0, 0]), "1/√2|000⟩ − 1/√2|001⟩")


if __name__ == "__main__":
    unittest.main()
