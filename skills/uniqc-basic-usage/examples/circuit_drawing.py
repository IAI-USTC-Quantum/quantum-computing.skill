"""Circuit drawing with the uniqc >= 0.1.1 rendering engine.

One layout core feeds seven output modes: text (self-developed ASCII /
Unicode art, no pyqpanda3), svg, png, mpl, latex (quantikz source), html,
and interactive (click-to-inspect). Entry points: ``Circuit.draw(mode, ...)``,
``uniqc.visualization.render(...)``, ``print(circuit)``, Jupyter inline SVG
(``_repr_svg_``), and the CLI ``uniqc draw <file>``.

text / svg / latex / html run on core dependencies; png / mpl additionally
need ``pip install unified-quantum[visualization]`` (matplotlib).
"""

from __future__ import annotations

import math

from uniqc import Circuit
from uniqc.visualization import render


def demo_circuit() -> Circuit:
    c = Circuit(3)
    c.h(0)
    c.cnot(0, 1)
    c.cz(0, 2)
    c.rx(1, math.pi / 2)
    c.swap(1, 2)
    with c.dagger():
        c.t(2)
    c.measure(0, 1, 2)
    return c


def main() -> None:
    c = demo_circuit()

    # 1) Terminal text art: print(circuit) == render(c, "text")
    #    (fold pinned so the output does not depend on terminal width)
    print(c.draw("text", fold=0))
    print(c.draw("text", charset="unicode", show_clbits=True, fold=0))

    # 2) Vector / LaTeX / HTML strings (also accept filename= to save)
    svg: str = render(c, mode="svg", style="quantikz")
    tikz: str = c.draw("latex")          # quantikz source, paper-ready
    page: str = render(c, mode="html", filename="circuit.html")
    print(f"svg={len(svg)} chars, latex={len(tikz)} lines, html={len(page)} chars")

    # 3) Interactive page: click a gate to inspect it
    interactive = c.draw("interactive", style="modern")
    print("interactive page:", len(interactive), "chars")

    # 4) Raster / matplotlib Figure need the [visualization] extra
    try:
        png = c.draw("png")
        print("png ok:", png[:4] == b"\x89PNG")
    except ImportError as exc:  # pragma: no cover - optional dep
        print(f"png skipped ({exc}); pip install unified-quantum[visualization]")

    # 5) Same engine from the shell: uniqc draw bell.originir -m svg -o bell.svg


if __name__ == "__main__":
    main()
