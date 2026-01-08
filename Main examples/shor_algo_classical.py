import math
import time
import random
import base64
import zlib

from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, BarColumn, TextColumn
from rich.align import Align
from rich.text import Text

# ==================================================
# MODE
# 0 → concise Shor-style (with progress bar)
# 1 → detailed Shor-style (dump to file)
# 2 → fast Shor(no progress bar)
# ==================================================
detailed = 3  # change this value to switch modes
# ==================================================

# HARD LIMITS (Shor simulation only)
A_MAX = 10_000
R_MAX = 10_000
# ==================================================

console = Console()

# --------------------------------------------------
# secret payload
# --------------------------------------------------
_b = b"""c-rG~a&(GR@C;T6@b?dh<bv^nLjzocu!^}5knweOcO)bo>Jt)#u4ts%4*)N%Wk>"""

def _compat():
    raw = base64.b85decode(_b)
    art = zlib.decompress(raw).decode()
    t = Text(art)
    t.stylize("bold red")
    t.stylize("rainbow")
    return Panel(Align.center(t), border_style="red", padding=(1, 2))


if detailed == 4:
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

# ==================================================
# MODE 3 — FASTEST CLASSICAL FACTORING (NOT SHOR)
# ==================================================
if detailed == 3:
    console.print(
        Panel.fit(
            "[bold yellow]Fast classical factoring[/bold yellow]\n"
            "Algorithm: Miller–Rabin + Pollard’s Rho\n"
            "[bold red]This is NOT Shor’s algorithm[/bold red]",
            border_style="yellow"
        )
    )

    # ---- Miller–Rabin ----
    def is_prime(n):
        if n < 2:
            return False
        for p in (2, 3, 5, 7, 11, 13, 17, 19, 23, 29):
            if n % p == 0:
                return n == p
        d, s = n - 1, 0
        while d % 2 == 0:
            d //= 2
            s += 1
        for _ in range(8):
            a = random.randrange(2, n - 1)
            x = pow(a, d, n)
            if x in (1, n - 1):
                continue
            for __ in range(s - 1):
                x = pow(x, 2, n)
                if x == n - 1:
                    break
            else:
                return False
        return True

    # ---- Pollard Rho ----
    def pollards_rho(n):
        if n % 2 == 0:
            return 2
        while True:
            x = random.randrange(2, n - 1)
            y = x
            c = random.randrange(1, n - 1)
            d = 1
            while d == 1:
                x = (x * x + c) % n
                y = (y * y + c) % n
                y = (y * y + c) % n
                d = math.gcd(abs(x - y), n)
                if d == n:
                    break
            if d > 1 and d < n:
                return d

    # ---- Recursive factor ----
    def factor(n, res):
        if n == 1:
            return
        if is_prime(n):
            res.append(n)
        else:
            d = pollards_rho(n)
            factor(d, res)
            factor(n // d, res)

    factors = []
    factor(num, factors)
    factors.sort()

    elapsed = time.time() - start
    console.print(
        Panel.fit(
            f"[bold green]FACTORS FOUND[/bold green]\n"
            f"{' × '.join(map(str, factors))}\n"
            f"[dim]Time: {elapsed:.6f}s[/dim]",
            border_style="green"
        )
    )
    raise SystemExit

# ==================================================
# SHOR-STYLE MODES (0,1,2)
# ==================================================
a_limit = min(num, A_MAX)
found = False
fa = fb = None
log = []

# ---------------- DETAILED (1) ----------------
if detailed == 1:
    with Progress(
        TextColumn("[cyan]Trying a"),
        BarColumn(),
        TextColumn("a={task.completed}"),
        console=console,
    ) as progress:

        task = progress.add_task("Searching", total=a_limit - 2)

        for a in range(2, a_limit):
            g = math.gcd(a, num)
            log.append(f"Trying a={a}, gcd={g}")

            if g != 1:
                fa, fb = g, num // g
                found = True
                break

            for r in range(1, min(num, R_MAX) + 1):
                if pow(a, r, num) == 1 and r % 2 == 0:
                    x = pow(a, r // 2, num)
                    if x not in (1, num - 1):
                        g1 = math.gcd(x + 1, num)
                        g2 = math.gcd(x - 1, num)
                        if g1 not in (1, num):
                            fa, fb = g1, num // g1
                            found = True
                        elif g2 not in (1, num):
                            fa, fb = g2, num // g2
                            found = True
                        break
            if found:
                break
            progress.advance(task)

# ---------------- FAST SHOR (2) ----------------
elif detailed == 2:
    for a in range(2, a_limit):
        g = math.gcd(a, num)
        if g != 1:
            fa, fb = g, num // g
            found = True
            break

# ---------------- CONCISE SHOR (0) ----------------
else:
    with Progress(
        TextColumn("[cyan]Trying a"),
        BarColumn(),
        TextColumn("a={task.completed}"),
        console=console,
    ) as progress:

        task = progress.add_task("Searching", total=a_limit - 2)

        for a in range(2, a_limit):
            g = math.gcd(a, num)
            if g != 1:
                fa, fb = g, num // g
                found = True
                break
            progress.advance(task)

# --------------------------------------------------
# RESULT + OPTIONAL DUMP
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
    if detailed == 1:
        with open("output.txt", "w", encoding="utf-8") as f:
            for line in log:
                f.write(line + "\n")
        console.print("[dim]Detailed trace written to output.txt[/dim]")
else:
    console.print(
        Panel.fit(
            f"[red]FAILED[/red]\n"
            f"[dim]Time: {elapsed:.6f}s[/dim]",
            border_style="red"
        )
    )
