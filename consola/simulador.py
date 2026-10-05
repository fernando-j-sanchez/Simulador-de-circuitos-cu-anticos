"""Simulador del Circuito 2 en consola (Python 3, sin dependencias).

Circuito (convención |q0 q1 q2⟩, q0 = bit más significativo):
    1. H sobre q1   2. H sobre q1   3. H sobre q2
    4. Toffoli (q0, q1 -> q2)       5. CZ (q1 -> q2)      6. Medición de q1

Uso:
    python simulador.py            # modo interactivo, paso a paso
    python simulador.py 0 1 +      # estado inicial por argumentos, sin pausas
"""
import cmath
import math
import os
import random
import re
import sys

N, DIM = 3, 8
S2 = 1 / math.sqrt(2)
EPS = 1e-10

H = [[S2, S2], [S2, -S2]]
X = [[0, 1], [1, 0]]
Z = [[1, 0], [0, -1]]

# (nombre, símbolo, objetivo, controles, matriz, operador, regla)
GATES = [
    ("Hadamard", "H", 1, [], H, "U1 = I ⊗ H ⊗ I", "H|0⟩ = |+⟩,  H|1⟩ = |−⟩"),
    ("Hadamard", "H", 1, [], H, "U2 = I ⊗ H ⊗ I", "H·H = I  →  q1 regresa a su valor original"),
    ("Hadamard", "H", 2, [], H, "U3 = I ⊗ I ⊗ H", "H|0⟩ = |+⟩,  H|1⟩ = |−⟩"),
    ("Toffoli (CCNOT)", "CCX", 2, [0, 1], X, "U4 = CCX(q0,q1 → q2)", "|a,b,c⟩ → |a, b, c ⊕ ab⟩"),
    ("Z controlada (CZ)", "CZ", 2, [1], Z, "U5 = I ⊗ CZ(q1 → q2)", "|a,b,c⟩ → (−1)^(bc) |a,b,c⟩"),
]
MEASURED = 1

PRESETS = {"0": (1, 0), "1": (0, 1), "+": (S2, S2), "-": (S2, -S2)}

# ---------------------------------------------------------------- colores
USE_COLOR = sys.stdout.isatty() and os.environ.get("NO_COLOR") is None
if os.name == "nt":
    os.system("")  # habilita secuencias ANSI en la consola de Windows


def _c(code):
    return (lambda t: f"\033[{code}m{t}\033[0m") if USE_COLOR else (lambda t: t)


bold, dim, cyan, yellow, green, red = _c("1"), _c("2"), _c("36"), _c("33;1"), _c("32"), _c("31")


# ---------------------------------------------------------------- álgebra
def bit(i, q):
    return (i >> (N - 1 - q)) & 1


def apply_gate(state, target, controls, m):
    out = list(state)
    tm = 1 << (N - 1 - target)
    for i in range(DIM):
        if i & tm or not all(bit(i, q) for q in controls):
            continue
        j = i | tm
        a0, a1 = state[i], state[j]
        out[i] = m[0][0] * a0 + m[0][1] * a1
        out[j] = m[1][0] * a0 + m[1][1] * a1
    return out


def tensor(q0, q1, q2):
    qs = (q0, q1, q2)
    return [qs[0][bit(i, 0)] * qs[1][bit(i, 1)] * qs[2][bit(i, 2)] for i in range(DIM)]


def qubit_probs(state):
    res = []
    for q in range(N):
        p1 = sum(abs(a) ** 2 for i, a in enumerate(state) if bit(i, q))
        res.append((1 - p1, p1))
    return res


def collapse(state, q, k):
    p = sum(abs(a) ** 2 for i, a in enumerate(state) if bit(i, q) == k)
    if p < EPS:
        return 0.0, None
    s = 1 / math.sqrt(p)
    return p, [a * s if bit(i, q) == k else 0 for i, a in enumerate(state)]


def run_circuit(state):
    states = [state]
    for _, _, t, c, m, _, _ in GATES:
        states.append(apply_gate(states[-1], t, c, m))
    return states


# ---------------------------------------------------------------- formato
KNOWN = [(1, "1"), (S2, "1/√2"), (0.5, "1/2"), (S2 / 2, "1/(2√2)"), (0.25, "1/4")]


def fmt_mag(x):
    for v, t in KNOWN:
        if abs(x - v) < 1e-9:
            return t
    return f"{x:.4f}".rstrip("0").rstrip(".")


def fmt_c(z):
    z = complex(z)
    r, i = abs(z.real) > 1e-9, abs(z.imag) > 1e-9
    if not r and not i:
        return "0"
    if not i:
        return ("−" if z.real < 0 else "") + fmt_mag(abs(z.real))
    if not r:
        m = fmt_mag(abs(z.imag))
        return ("−" if z.imag < 0 else "") + ("" if m == "1" else m) + "i"
    sr = ("−" if z.real < 0 else "") + fmt_mag(abs(z.real))
    return f"({sr} {'−' if z.imag < 0 else '+'} {fmt_mag(abs(z.imag))}i)"


def ket(i):
    return f"|{i:03b}⟩"


def ket_str(state):
    out = ""
    for i, a in enumerate(state):
        if abs(a) ** 2 < EPS:
            continue
        co = fmt_c(a)
        neg = co.startswith("−")
        co = co[1:] if neg else co
        co = "" if co == "1" else co
        out += ((" − " if neg else " + ") if out else ("−" if neg else "")) + co + ket(i)
    return out or "0"


def pct(p):
    return f"{max(0.0, min(1.0, p)) * 100:6.2f}%"


def bar(p, width=20):
    n = round(max(0.0, min(1.0, p)) * width)
    return cyan("█" * n) + dim("·" * (width - n))


# ---------------------------------------------------------------- circuito ASCII
COLS = [
    ("─────", "──H──", "─────"),
    ("─────", "──H──", "─────"),
    ("─────", "─────", "──H──"),
    ("──●──", "──●──", "──X──"),
    ("─────", "──●──", "──Z──"),
    ("─────", "─[M]─", "─────"),
]


def circuit_ascii(current=None, done=0):
    lines = []
    for q in range(N):
        row = f"  q{q}: ─"
        for k, col in enumerate(COLS):
            seg = col[q]
            if k == current:
                seg = yellow(seg)
            elif k < done:
                seg = green(seg)
            row += seg + "─"
        lines.append(row + "─")
        if q < N - 1:
            gap = "        "
            for k in range(len(COLS)):
                v = "  │   " if (k == 3) or (k == 4 and q == 1) else "      "
                gap += yellow(v) if k == current else v
            lines.append(gap)
    nums = "        " + "".join(f"  {('M' if k == 5 else k + 1)}   " for k in range(len(COLS)))
    lines.append(dim(nums))
    return "\n".join(lines)


# ---------------------------------------------------------------- entrada
def parse_complex(src):
    s = src.strip().replace(" ", "").replace("√", "sqrt").replace("−", "-").replace(",", ".")
    s = s.replace("i", "j")
    if not s or not re.fullmatch(r"[0-9.+\-*/()jsqrt]+", s):
        raise ValueError("expresión no válida")
    s = re.sub(r"sqrt(\d*\.?\d+)", r"sqrt(\1)", s)  # √2 → sqrt(2)
    s = re.sub(r"(?<![0-9.)])j", "1j", s)
    s = re.sub(r"([0-9.)])\s*(sqrt|\()", r"\1*\2", s)
    val = eval(s, {"__builtins__": {}}, {"sqrt": cmath.sqrt})
    return complex(val)


def ask_qubit(q):
    while True:
        r = input(f"  q{q} [0 / 1 / + / - / c=personalizado] (Enter = 0): ").strip().lower() or "0"
        r = r.replace("−", "-")
        if r in PRESETS:
            return PRESETS[r], {"0": "|0⟩", "1": "|1⟩", "+": "|+⟩", "-": "|−⟩"}[r]
        if r == "c":
            try:
                a = parse_complex(input("     α = "))
                b = parse_complex(input("     β = "))
            except Exception as e:  # noqa: BLE001
                print(red(f"     Valor no válido ({e}). Ejemplos: 1/√2, 0.6, 0.8i, -i/sqrt(2)"))
                continue
            n = abs(a) ** 2 + abs(b) ** 2
            if n < EPS:
                print(red("     α y β no pueden ser ambos 0."))
                continue
            a, b = a / math.sqrt(n), b / math.sqrt(n)
            if abs(n - 1) > 1e-6:
                print(dim("     (se normalizó para que |α|² + |β|² = 1)"))
            return (a, b), f"({fmt_c(a)}|0⟩ + {fmt_c(b)}|1⟩)"
        print(red("     Opción no válida."))


def preset_from_arg(a):
    a = a.replace("−", "-")
    if a not in PRESETS:
        raise SystemExit(f"Estado '{a}' no válido. Usa 0, 1, + o -.")
    return PRESETS[a], {"0": "|0⟩", "1": "|1⟩", "+": "|+⟩", "-": "|−⟩"}[a]


# ---------------------------------------------------------------- presentación
def header(t):
    print("\n" + bold("═" * 64) + "\n" + bold(t) + "\n" + bold("═" * 64))


def print_table(before, after):
    print(f"  {'Base':<7}{'Amp. antes':>14}{'Amp. después':>16}   Prob. después")
    for i in range(DIM):
        changed = abs(complex(before[i]) - complex(after[i])) > 1e-9
        line = f"  {ket(i):<7}{fmt_c(before[i]):>14}{fmt_c(after[i]):>16}   {bar(abs(after[i]) ** 2)} {pct(abs(after[i]) ** 2)}"
        print(yellow("▸") + line[1:] if changed else line)


def print_qprobs(state):
    print("  Probabilidad de cada qubit:")
    for q, (p0, p1) in enumerate(qubit_probs(state)):
        print(f"    q{q}:  P(|0⟩) = {pct(p0)}   P(|1⟩) = {pct(p1)}")


def pause(interactive):
    if interactive:
        input(dim("\n  [Enter] para continuar..."))


def main(argv):
    interactive = len(argv) == 0
    header("SIMULADOR DE CIRCUITOS CUÁNTICOS · Circuito 2\nCómputo Cuántico · Hijar González Fátima Estefanía")
    print("\nCircuito a simular (3 qubits, 5 compuertas + medición):\n")
    print(circuit_ascii())
    print(dim("\n  Convención: |q0 q1 q2⟩, q0 es el bit más significativo."))

    if interactive:
        print("\nIngresa el estado inicial de cada qubit:")
        qs = [ask_qubit(q) for q in range(N)]
    else:
        if len(argv) != 3:
            raise SystemExit("Uso: python simulador.py [q0 q1 q2]   (cada uno: 0, 1, + o -)")
        qs = [preset_from_arg(a) for a in argv]

    psi = tensor(*(v for v, _ in qs))
    print("\n  |ψ0⟩ = " + " ⊗ ".join(lbl for _, lbl in qs))
    print("       = " + bold(ket_str(psi)))
    states = run_circuit(psi)
    pause(interactive)

    sub = "₀₁₂₃₄₅"
    for k, (name, sym, t, ctrl, _, op, rule) in enumerate(GATES):
        header(f"Paso {k + 1} de 6 · {name} ({sym})")
        print(circuit_ascii(current=k, done=k) + "\n")
        aff = (f"control {', '.join(f'q{c}' for c in ctrl)} · " if ctrl else "") + f"objetivo q{t}"
        print(f"  Qubits afectados: {aff}")
        print(f"  Operador: {op}")
        print(f"  Regla:    {rule}")
        print(f"  |ψ{sub[k + 1]}⟩ = U{sub[k + 1]} |ψ{sub[k]}⟩\n")
        print(f"  Antes   |ψ{sub[k]}⟩ = {ket_str(states[k])}")
        print(f"  Después |ψ{sub[k + 1]}⟩ = " + bold(ket_str(states[k + 1])) + "\n")
        print_table(states[k], states[k + 1])
        print()
        print_qprobs(states[k + 1])
        pause(interactive)

    final = states[-1]
    header("Paso 6 de 6 · Medición de q1")
    print(circuit_ascii(current=5, done=5) + "\n")
    print(f"  Estado antes de medir |ψ₅⟩ = {ket_str(final)}\n")
    print("  ¿A qué estado puede colapsar y con qué probabilidad?")
    outcomes = [collapse(final, MEASURED, k) for k in (0, 1)]
    for k, (p, st) in enumerate(outcomes):
        dest = ket_str(st) if st else dim("imposible (probabilidad 0)")
        print(f"    q1 = {k}:  P = {pct(p)}   →  {dest}")
    print("\n  Probabilidad de colapso por estado base:")
    for i, a in enumerate(final):
        p = abs(a) ** 2
        print(f"    {ket(i)}  {bar(p)} {pct(p)}   (q1 = {bit(i, MEASURED)})")

    k = 0 if random.random() < outcomes[0][0] else 1
    p, st = outcomes[k]
    print("\n  " + yellow(f"Medición simulada: q1 = {k} (probabilidad {pct(p).strip()})"))
    print(f"  Estado colapsado: {ket_str(st)}")

    header("ESTADO FINAL")
    print(circuit_ascii(done=6) + "\n")
    print("  |ψ₅⟩ = " + bold(ket_str(final)) + "\n")
    print(f"  {'Base':<7}{'Amplitud':>14}{'Decimal':>22}   Probabilidad")
    for i, a in enumerate(final):
        a = complex(a)
        dec = f"{a.real:+.4f} {'−' if a.imag < 0 else '+'} {abs(a.imag):.4f}i"
        print(f"  {ket(i):<7}{fmt_c(a):>14}{dec:>22}   {bar(abs(a) ** 2)} {pct(abs(a) ** 2)}")
    print(f"\n  Suma de probabilidades = {sum(abs(a) ** 2 for a in final):.6f}\n")
    print_qprobs(final)
    print()


if __name__ == "__main__":
    try:
        main(sys.argv[1:])
    except (KeyboardInterrupt, EOFError):
        print("\nSimulación cancelada.")
