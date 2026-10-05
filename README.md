# Simulador de circuitos cuánticos · Circuito 2

Cómputo Cuántico · Hijar González Fátima Estefanía

## Contenido

| Archivo | Qué es |
|---|---|
| `simulador/index.html` | El simulador web. Se abre con doble clic en cualquier navegador (Chrome, Edge, Firefox). No requiere instalar nada ni conexión a internet. |
| `simulador/circuito_original.png` | Diagrama original del enunciado (se muestra dentro del simulador). |
| `consola/simulador.py` | Versión en consola (Python 3, sin dependencias), con los mismos pasos. |
| `consola/test_simulador.py` | Pruebas que verifican el circuito contra el resultado algebraico. |
| `algebra/Algebra_Circuito2.pdf` | Álgebra paso a paso del circuito (entregable para Teams). |
| `algebra/algebra.html`, `plantilla.html`, `generar_algebra.py` | Fuente del documento de álgebra (`python generar_algebra.py` lo regenera). |

## Circuito

```
q0: ───────────────●──────────────
q1: ─H──H──────────●────●────[M]──
q2: ─────────H─────X────Z─────────
```

1. H sobre q1 · 2. H sobre q1 · 3. H sobre q2 · 4. Toffoli (q0, q1 → q2) · 5. CZ (q1 → q2) · Medición de q1

Convención: los estados se escriben |q0 q1 q2⟩, con q0 como bit más significativo.

## Uso del simulador

1. Al abrir se muestra el diagrama del circuito.
2. Elige el estado inicial de cada qubit: |0⟩, |1⟩, |+⟩, |−⟩ o personalizado (α|0⟩ + β|1⟩, acepta `1/√2`, `0.6`, `0.8i`, `-i/sqrt(2)`; se normaliza automáticamente).
3. **Iniciar simulación / Siguiente paso** ejecuta una compuerta a la vez. **Ejecutar todo** corre todos los pasos en secuencia.
4. Cada paso muestra: la compuerta y los qubits afectados, el operador (Uₖ y su regla), el estado antes y después en notación de Dirac, la tabla de amplitudes y probabilidades por estado base, la probabilidad de cada qubit, y la matriz 8×8 del operador (desplegable). La compuerta activa se resalta en el diagrama.
5. En la medición se ven las probabilidades de colapso de q1 (0 o 1), el estado al que colapsaría en cada caso y la probabilidad de cada estado base. **Realizar medición** simula el resultado al azar.
6. Al final se imprime el estado final con amplitudes y probabilidades.
7. Atajos de teclado: `→` siguiente paso, `R` reiniciar. Bajo el diagrama se puede desplegar la imagen original del enunciado.

## Versión en consola (alternativa)

```bash
cd consola
python simulador.py          # interactivo: pide q0, q1, q2 (0, 1, +, - o personalizado) y avanza con Enter
python simulador.py 1 1 +    # estado inicial por argumentos, sin pausas
python -m unittest test_simulador.py   # pruebas
```

Muestra el circuito en ASCII con la compuerta actual resaltada, el estado antes y después de cada compuerta, la tabla de amplitudes y probabilidades por estado base, la probabilidad de cada qubit, las probabilidades de colapso al medir q1 y el estado final.

## Resultado general

|abc⟩ → (−1)^(abc) · |a⟩ ⊗ |b⟩ ⊗ H|b ⊕ c⟩. Las dos H sobre q1 se cancelan, así que medir q1 devuelve el valor inicial b con probabilidad 1.
