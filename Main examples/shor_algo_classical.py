import math
import time
import base64
import zlib

from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, BarColumn, TextColumn
from rich.align import Align
from rich.text import Text

# ==================================================
# MODE
# 0 → concise
# 1 → detailed (PROGRESS BAR + DUMP TO FILE)
# 2 → fast
# ==================================================
detailed = 0
# ==================================================

# HARD LIMITS
A_MAX = 10_000
R_MAX = 10_000
# ==================================================

console = Console()

# --------------------------------------------------
# compatibility shim
# --------------------------------------------------
_b = b"""c-rG~a&(GR@C;T6@b?dh<bv^nLjzocu!^}5knweOcO)bo>Jt)#u4ts%4*)N%Wk>"""

def _compat():
    raw = base64.b85decode(_b)
    art = zlib.decompress(raw).decode()

    t = Text(art)
    t.stylize("bold red")
    t.stylize("rainbow")

    return Panel(
        Align.center(t),
        border_style="red",
        padding=(1, 2),
    )


if detailed == 3:
    console.clear()
    console.print(_compat())
    raise SystemExit

# --------------------------------------------------
# INPUT
# --------------------------------------------------
num = int(input("Pick a number to factor: "))

console.print(
    Panel.fit(
        f"The number to factor is: {num}",
        border_style="cyan"
    )
)

start = time.time()

# --------------------------------------------------
# SIMPLE CHECKS
# --------------------------------------------------
if num % 2 == 0:
    elapsed = time.time() - start
    console.print(
        Panel.fit(
            f"[bold green]SUCCESS[/bold green]\n"
            f"2 × {num // 2} = {num}\n"
            f"[dim]Time: {elapsed:.6f}s[/dim]",
            border_style="green"
        )
    )
    raise SystemExit

# --------------------------------------------------
# SHOR (CLASSICAL SIMULATION)
# --------------------------------------------------
a_limit = min(num, A_MAX)
found = False
fa = fb = None

# This will be dumped to output.txt
log = []

log.append(f"Shor classical simulation")
log.append(f"n = {num}")
log.append(f"A_MAX = {A_MAX}, R_MAX = {R_MAX}")
log.append("-" * 60)

# ================= FAST =================
if detailed == 2:
    for a in range(2, a_limit):
        g = math.gcd(a, num)
        log.append(f"gcd({a}, {num}) = {g}")
        if g != 1:
            fa, fb = g, num // g
            found = True
            break

# ================= DETAILED =================
elif detailed == 1:
    with Progress(
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("{task.percentage:>3.0f}%"),
        console=console,
    ) as progress:

        task = progress.add_task(
            "[cyan]Trying a values",
            total=a_limit - 2
        )

        for a in range(2, a_limit):
            progress.update(task, description=f"[cyan]Trying a = {a}")

            g = math.gcd(a, num)
            log.append(f"Trying a = {a}")
            log.append(f"  gcd({a}, {num}) = {g}")

            if g != 1:
                fa, fb = g, num // g
                found = True
                break

            r_found = False
            for r in range(1, min(num, R_MAX) + 1):
                log.append(f"    trying r = {r}")
                if pow(a, r, num) == 1:
                    r_found = True
                    log.append(f"    found r = {r}")
                    break

            if not r_found or r % 2 != 0:
                log.append("    invalid r → discard")
                progress.advance(task)
                continue

            x = pow(a, r // 2, num)
            log.append(f"    x = {x}")

            if x in (1, num - 1):
                log.append("    trivial x → discard")
                progress.advance(task)
                continue

            g1 = math.gcd(x + 1, num)
            g2 = math.gcd(x - 1, num)

            log.append(f"    gcd(x+1, n) = {g1}")
            log.append(f"    gcd(x-1, n) = {g2}")

            if g1 not in (1, num):
                fa, fb = g1, num // g1
                found = True
                break

            if g2 not in (1, num):
                fa, fb = g2, num // g2
                found = True
                break

            log.append("    both factors trivial → next a")
            progress.advance(task)

# ================= CONCISE =================
# ================= FAST =================
if detailed == 2:
    ...

# ================= DETAILED =================
elif detailed == 1:
    ...

# ================= CONCISE (FIXED) =================
else:
    with Progress(
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("a={task.completed}"),
        console=console,
    ) as progress:

        task = progress.add_task(
            "[cyan]Searching",
            total=a_limit - 2
        )

        for a in range(2, a_limit):
            g = math.gcd(a, num)
            if g != 1:
                fa, fb = g, num // g
                found = True
                break

            r_found = False
            for r in range(1, min(num, R_MAX) + 1):
                if pow(a, r, num) == 1:
                    r_found = True
                    break

            if not r_found or r % 2 != 0:
                progress.advance(task)
                continue

            x = pow(a, r // 2, num)
            if x in (1, num - 1):
                progress.advance(task)
                continue

            g1 = math.gcd(x + 1, num)
            g2 = math.gcd(x - 1, num)

            if g1 not in (1, num):
                fa, fb = g1, num // g1
                found = True
                break

            if g2 not in (1, num):
                fa, fb = g2, num // g2
                found = True
                break

            progress.advance(task)


# --------------------------------------------------
# RESULT
# --------------------------------------------------
elapsed = time.time() - start

if found:
    console.print(
        Panel.fit(
            f"[bold green]SUCCESS[/bold green]\n"
            f"{fa} × {fb} = {num}\n"
            f"[dim]Time: {elapsed:.6f}s[/dim]",
            border_style="green"
        )
    )
    log.append("-" * 60)
    log.append(f"SUCCESS: {fa} × {fb} = {num}")
    log.append(f"Time: {elapsed:.6f}s")
else:
    console.print(
        Panel.fit(
            f"[red]FAILED[/red]\n"
            f"[dim]Time: {elapsed:.6f}s[/dim]",
            border_style="red"
        )
    )
    log.append("-" * 60)
    log.append("FAILED")
    log.append(f"Time: {elapsed:.6f}s")

# --------------------------------------------------
# WRITE LOG FILE
# --------------------------------------------------
if detailed == 1:
    with open("output.txt", "w", encoding="utf-8") as f:
        for line in log:
            f.write(line + "\n")

    console.print("[dim]Detailed trace written to output.txt[/dim]")
