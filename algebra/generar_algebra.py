"""Genera algebra.html: el desarrollo algebraico del Circuito 2 para las 8 entradas base."""
import math
from pathlib import Path

S = 1 / math.sqrt(2)


def bit(i, q):
    return (i >> (2 - q)) & 1


def apply(state, target, controls, m):
    out = list(state)
    tm = 1 << (2 - target)
    for i in range(8):
        if i & tm or not all(bit(i, q) for q in controls):
            continue
        j = i | tm
        a0, a1 = state[i], state[j]
        out[i] = m[0][0] * a0 + m[0][1] * a1
        out[j] = m[1][0] * a0 + m[1][1] * a1
    return out


H = [[S, S], [S, -S]]
X = [[0, 1], [1, 0]]
Z = [[1, 0], [0, -1]]
GATES = [(1, [], H), (1, [], H), (2, [], H), (2, [0, 1], X), (2, [1], Z)]


def ket_str(st):
    nz = [(i, a) for i, a in enumerate(st) if abs(a) > 1e-9]
    if len(nz) == 1:
        i, a = nz[0]
        return ("−" if a < 0 else "") + f"|{i:03b}⟩"
    body = ""
    for k, (i, a) in enumerate(nz):
        sign = "−" if a < 0 else "+"
        body += (("−" if a < 0 else "") if k == 0 else f" {sign} ") + f"|{i:03b}⟩"
    return f"(1/√2)({body})"


rows = []
for x in range(8):
    st = [1.0 if i == x else 0.0 for i in range(8)]
    states = [st]
    for t, c, m in GATES:
        st = apply(st, t, c, m)
        states.append(st)
    p1 = sum(abs(a) ** 2 for i, a in enumerate(st) if bit(i, 1))
    rows.append((x, [ket_str(s) for s in states], p1))

tbody = "\n".join(
    f"<tr><td>|{x:03b}⟩</td>" + "".join(f"<td>{k}</td>" for k in ks[1:])
    + f"<td>P(0) = {1 - p1:.0%}<br>P(1) = {p1:.0%}</td></tr>"
    for x, ks, p1 in rows
)

html = Path(__file__).with_name("plantilla.html").read_text(encoding="utf-8").replace("{{TABLA}}", tbody)
Path(__file__).with_name("algebra.html").write_text(html, encoding="utf-8")
print("algebra.html generado")
