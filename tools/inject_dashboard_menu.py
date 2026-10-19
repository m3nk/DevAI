#!/usr/bin/env python3
"""Inject a 'back to dashboard' pill into every DevAI arcade game.

Placement is pure CSS (a fixed corner) for most games. Four games draw their own
HUD on the canvas, so for those a tiny script parks the pill just below that band,
re-derived from the canvas rect on resize (a fraction of the canvas height, since
the canvas itself is contain-fit).

Idempotent: re-running replaces the previous snippet instead of stacking.
"""
import os
import re
import sys

GDIR = "/mnt/datashare/Hermes/Coder/DevAI/games"
HREF = "../index.html"

# corner: tl|tr|bl|br   m: margin px   mb: bottom margin override
# hud:    fraction of the canvas height to drop below (canvas element == playfield)
# fit:    (LW, LH, logical_y) for a full-bleed canvas that letterboxes its playfield
CFG = {
    "snake.html":            dict(corner="tl"),
    "pong.html":             dict(corner="tl", fg="#cfeeff", bd="rgba(34,211,238,.45)"),
    "breakout.html":         dict(corner="tl", hud=0.075),
    "memory.html":           dict(corner="tl", fg="#cfeeff", bd="rgba(34,211,238,.45)"),
    "flappy.html":           dict(corner="tl"),
    "pacman.html":           dict(corner="tl", fg="#FFE13B", bd="rgba(255,225,59,.5)"),
    "tictactoe.html":        dict(corner="tl", fg="#cfeeff", bd="rgba(34,211,238,.45)"),
    "neonvanguard.html":     dict(corner="br"),
    "zombielight.html":      dict(corner="bl", fg="#cfd3da", bd="rgba(160,170,190,.4)"),
    "missilecommand.html":   dict(corner="tl", fit=(1280, 720, 80), fg="#cfe9ff",
                                  bd="rgba(102,204,255,.45)"),
    "fruitslicer.html":      dict(corner="bl"),
    "typingdefense.html":    dict(corner="tl", fg="#8fb3d9", bd="#1e3a5f"),
    "towerdefense.html":     dict(corner="bl"),
    "vampsurvivors.html":    dict(corner="bl", mb=46),
    "snipergallery.html":    dict(corner="tl", hud=0.11, fg="#c8d4e6", bd="#3a4658"),
    "restaurantrush.html":   dict(corner="tl", hud=0.09, fg="#f7ead8", bd="#57432e",
                                  bg="rgba(30,18,10,.6)"),
    "gasstationtycoon.html": dict(corner="tl"),
}

START = "<!-- DEVAI-MENU:BEGIN -->"
END = "<!-- DEVAI-MENU:END -->"


def snippet(name):
    c = CFG[name]
    corner, m = c.get("corner", "tl"), c.get("m", 10)
    mb = c.get("mb", m)
    horiz = "right:%dpx" % m if corner[1] == "r" else "left:%dpx" % m
    vert = "bottom:%dpx" % mb if corner[0] == "b" else "top:%dpx" % m
    vars_ = []
    for k, css in (("bg", "--da-bg"), ("fg", "--da-fg"), ("bd", "--da-bd")):
        if c.get(k):
            vars_.append(f"{css}:{c[k]}")
    tint = ("#devai-home{" + ";".join(vars_) + "}") if vars_ else ""

    fit = c.get("fit")
    cfg_js = "{hud:%s,fitW:%s,fitH:%s,fitY:%s}" % (
        c.get("hud", 0), fit[0] if fit else 0, fit[1] if fit else 0, fit[2] if fit else 0)
    # only canvas-HUD games need a script; the rest are pure CSS and resize-proof
    if not fit and not c.get("hud"):
        script = ""
    else:
        script = f"""<script>
(function(){{
  var P=document.getElementById('devai-home'),CFG={cfg_js},t;
  function place(){{
    if(!P)return;
    var vw=window.innerWidth,vh=window.innerHeight,c=document.querySelector('canvas');
    var cr=c?c.getBoundingClientRect():{{x:0,y:0,width:vw,height:vh}};
    var h=P.offsetHeight||28,y;
    if(CFG.fitW){{
      // playfield is contain-fit INSIDE a full-bleed canvas: map logical y to the screen
      var f=Math.min(cr.width/CFG.fitW,cr.height/CFG.fitH);
      y=cr.y+(cr.height-CFG.fitH*f)/2+CFG.fitY*f+6;
    }}else{{
      y=cr.y+cr.height*CFG.hud+6;
    }}
    P.style.top=Math.round(Math.max(4,Math.min(y,vh-h-4)))+'px';
    P.style.bottom='auto';
  }}
  // never schedule with requestAnimationFrame: a background tab receives zero frames
  function queue(){{clearTimeout(t);t=setTimeout(place,50);}}
  window.addEventListener('resize',queue);
  window.addEventListener('orientationchange',function(){{setTimeout(place,150);}});
  document.addEventListener('visibilitychange',function(){{if(!document.hidden)place();}});
  if(window.ResizeObserver&&c0()){{try{{new ResizeObserver(queue).observe(c0());}}catch(e){{}}}}
  function c0(){{return document.querySelector('canvas');}}
  place();setTimeout(place,300);
  if(document.readyState!=='complete')window.addEventListener('load',function(){{place();setTimeout(place,300);}});
}})();
</script>"""

    return f"""{START}
<style>
  #devai-home{{position:fixed;z-index:2147483000;{horiz};{vert};
    display:inline-flex;align-items:center;gap:6px;padding:6px 12px;border-radius:999px;
    white-space:nowrap;font:600 12px/1 "Segoe UI",system-ui,-apple-system,sans-serif;
    letter-spacing:.4px;text-decoration:none;color:var(--da-fg,#dfe6f5);
    background:var(--da-bg,rgba(10,14,24,.62));border:1px solid var(--da-bd,rgba(108,140,255,.45));
    box-shadow:0 4px 14px rgba(0,0,0,.35);backdrop-filter:blur(6px);-webkit-backdrop-filter:blur(6px);
    opacity:.72;transition:opacity .15s ease,transform .15s ease,background .15s ease;
    user-select:none;-webkit-user-select:none;touch-action:manipulation;cursor:pointer}}
  #devai-home:hover,#devai-home:focus-visible{{opacity:1;transform:translateY(-1px);
    background:var(--da-bgh,rgba(28,38,68,.92))}}
  #devai-home:active{{transform:translateY(0)}}
  #devai-home .da-i{{font-size:14px;line-height:1}}
  @media (max-width:560px){{#devai-home{{padding:8px 11px}}}}
  {tint}
</style>
<a id="devai-home" href="{HREF}" title="Back to the DevAI Arcade dashboard &#8212; pick another game"><span class="da-i">&#127918;</span><span class="da-t">Menu</span></a>
{script}
{END}
"""


def inject(name, dry=False):
    p = os.path.join(GDIR, name)
    s = open(p, encoding="utf-8").read()
    s = re.sub(re.escape(START) + r"[\s\S]*?" + re.escape(END) + r"\n?", "", s)
    m = re.search(r"<body[^>]*>", s, re.I)
    if not m:
        raise SystemExit("no <body> in " + name)
    out = s[: m.end()] + "\n" + snippet(name) + s[m.end():]
    if not dry:
        open(p, "w", encoding="utf-8").write(out)
    return out


def main():
    on_disk = {f for f in os.listdir(GDIR) if f.endswith(".html")}
    if set(CFG) ^ on_disk:
        print("CONFIG/GAMES MISMATCH:", set(CFG) ^ on_disk, file=sys.stderr)
        sys.exit(1)
    for name in sorted(CFG):
        before = open(os.path.join(GDIR, name), encoding="utf-8").read()
        out = inject(name)
        ok = out.count(START) == 1 and out.count('id="devai-home"') == 1 and "../index.html" in out
        print(("OK  " if ok else "FAIL"), f"{name:24s} {len(before):6d} -> {len(out):6d}",
              "js" if "<script>" in snippet(name) else "css")
    print("total:", len(CFG))


if __name__ == "__main__":
    main()
