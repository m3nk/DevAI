#!/usr/bin/env python3
"""Inject the shared DevAI arcade chrome into every game:

  🕹️ Menu   -> back to the dashboard (../index.html)
  🗑 Clear   -> delete this game's saved data (best scores, settings), then reload

Per game the Clear button removes ONLY that game's localStorage keys (`keys` +
`pref` prefixes) so one game can never wipe another game's records.

Placement is pure CSS (a fixed corner) for most games. Four games draw their own
HUD on the canvas, so for those a script parks the row just below that band,
re-derived from the canvas rect on resize.

Idempotent: re-running replaces the previous block instead of stacking.
"""
import os
import re
import sys

GDIR = "/mnt/datashare/Hermes/Coder/DevAI/games"
HREF = "../index.html"

# keys: exact localStorage keys the game writes (verified from source)
# pref: key prefixes, to catch per-mode variants of the same game's own keys
# corner: tl|tr|bl|br   m: margin px   mb: bottom margin override
# hud:    fraction of the canvas height to drop below (canvas element == playfield)
# fit:    (LW, LH, logical_y) for a full-bleed canvas that letterboxes its playfield
CFG = {
    "snake.html":            dict(corner="tl", keys=["snake.best", "snake.sound", "snake.wrap"],
                                  pref=["snake."]),
    "pong.html":             dict(corner="tl", keys=[], pref=[], fg="#cfeeff",
                                  bd="rgba(34,211,238,.45)"),
    "breakout.html":         dict(corner="tl", hud=0.075, keys=["neonBreakoutHi"],
                                  pref=["neonBreakout"]),
    "memory.html":           dict(corner="tl", keys=["memoryMatch.bestests"],
                                  pref=["memoryMatch."], fg="#cfeeff", bd="rgba(34,211,238,.45)"),
    "flappy.html":           dict(corner="tl", keys=["flappy_best"], pref=["flappy"]),
    "pacman.html":           dict(corner="tl", keys=["pacman-hi"], pref=["pacman"],
                                  fg="#FFE13B", bd="rgba(255,225,59,.5)"),
    "tictactoe.html":        dict(corner="tl", keys=["ttt.scores.v2"], pref=["ttt."],
                                  fg="#cfeeff", bd="rgba(34,211,238,.45)"),
    "neonvanguard.html":     dict(corner="br", keys=[], pref=[]),
    "zombielight.html":      dict(corner="bl", keys=[], pref=[], fg="#cfd3da",
                                  bd="rgba(160,170,190,.4)"),
    # LS_KEY is built at runtime by the game: ['mc','_','his','core','_v1'].join('')
    "missilecommand.html":   dict(corner="tl", fit=(1280, 720, 80), keys=["mc_hiscore_v1"],
                                  pref=["mc_"], fg="#cfe9ff", bd="rgba(102,204,255,.45)"),
    "fruitslicer.html":      dict(corner="bl", keys=["fruitSlicerBest"], pref=["fruitSlicer"]),
    "typingdefense.html":    dict(corner="tl", keys=["typingDefense.bestest"],
                                  pref=["typingDefense."], fg="#8fb3d9", bd="#1e3a5f"),
    "towerdefense.html":     dict(corner="bl", keys=["td_best_wave"], pref=["td_"]),
    "vampsurvivors.html":    dict(corner="bl", mb=46, keys=[], pref=[]),
    "snipergallery.html":    dict(corner="tl", hud=0.11,
                                  keys=["sniperGallery.best", "sniperGallery.mute"],
                                  pref=["sniperGallery."], fg="#c8d4e6", bd="#3a4658"),
    "restaurantrush.html":   dict(corner="tl", hud=0.09, keys=["restaurantrush.best.v1"],
                                  pref=["restaurantrush."], fg="#f7ead8", bd="#57432e",
                                  bg="rgba(30,18,10,.6)"),
    "gasstationtycoon.html": dict(corner="tl",
                                  keys=["gst_best_networth", "gst_best_day", "gst_muted"],
                                  pref=["gst_"]),
    # contra.html letterboxes a 960x540 playfield inside a full-bleed canvas;
    # its own canvas HUD runs to y=44 logical, so park the row just below it.
    "contra.html":           dict(corner="tl", fit=(960, 540, 52),
                                  keys=["contra_hi"], pref=["contra_"],
                                  fg="#d9e6c8", bd="rgba(120,160,90,.45)"),
}

START = "<!-- DEVAI-MENU:BEGIN -->"
END = "<!-- DEVAI-MENU:END -->"


def js_list(items):
    return "[" + ",".join('"%s"' % i for i in items) + "]"


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
    tint = ("#devai-tools{" + ";".join(vars_) + "}") if vars_ else ""

    keys, pref = c.get("keys", []), c.get("pref", [])
    stored = bool(keys or pref)
    title_clear = ("Delete this game&#39;s saved data (%s) from this browser"
                   % ", ".join(keys)) if stored else \
                  "Delete this game&#39;s saved data &#8212; this game keeps none right now"

    fit = c.get("fit") or (0, 0, 0)
    cfg_js = "{hud:%s,fitW:%s,fitH:%s,fitY:%s}" % (c.get("hud", 0), fit[0], fit[1], fit[2])

    return f"""{START}
<style>
  #devai-tools{{position:fixed;z-index:2147483000;{horiz};{vert};display:flex;gap:8px;
    align-items:center;flex-wrap:wrap;max-width:calc(100vw - 20px)}}
  #devai-tools a,#devai-tools button{{display:inline-flex;align-items:center;gap:6px;
    padding:6px 12px;border-radius:999px;white-space:nowrap;
    font:600 12px/1 "Segoe UI",system-ui,-apple-system,sans-serif;letter-spacing:.4px;
    text-decoration:none;color:var(--da-fg,#dfe6f5);
    background:var(--da-bg,rgba(10,14,24,.62));border:1px solid var(--da-bd,rgba(108,140,255,.45));
    box-shadow:0 4px 14px rgba(0,0,0,.35);backdrop-filter:blur(6px);-webkit-backdrop-filter:blur(6px);
    opacity:.72;transition:opacity .15s ease,transform .15s ease,background .15s ease,color .15s ease;
    user-select:none;-webkit-user-select:none;touch-action:manipulation;cursor:pointer;
    -webkit-appearance:none;appearance:none;font-family:inherit}}
  #devai-tools a:hover,#devai-tools button:hover,#devai-tools a:focus-visible,
  #devai-tools button:focus-visible{{opacity:1;transform:translateY(-1px);
    background:var(--da-bgh,rgba(28,38,68,.92))}}
  #devai-tools a:active,#devai-tools button:active{{transform:translateY(0)}}
  #devai-tools .da-i{{font-size:14px;line-height:1}}
  #devai-clear.arm{{opacity:1;color:#ffd9d9;border-color:rgba(255,107,107,.85);
    background:rgba(96,20,26,.82)}}
  #devai-clear.done{{opacity:1;color:#d6ffe9;border-color:rgba(61,220,151,.8);
    background:rgba(16,68,48,.85)}}
  @media (max-width:560px){{#devai-tools a,#devai-tools button{{padding:8px 11px}}}}
  {tint}
</style>
<div id="devai-tools">
  <a id="devai-home" href="{HREF}" title="Back to the DevAI Arcade dashboard &#8212; pick another game"><span class="da-i">&#127918;</span><span class="da-t">Menu</span></a>
  <button id="devai-clear" type="button" title="{title_clear}"><span class="da-i">&#128465;</span><span class="da-t">Clear</span></button>
</div>
<script>
(function(){{
  var T=document.getElementById('devai-tools'),B=document.getElementById('devai-clear'),
      CFG={cfg_js},KEYS={js_list(keys)},PREF={js_list(pref)},t,armT,armed=0;

  /* ---- keep these controls' events out of the game's own input handlers ----
     NB: stopPropagation() in the window CAPTURE phase also prevents the target's
     own listeners, so the button's action must run here, not on the button.
     (The Menu link still navigates: that is a default action, not a listener.) */
  ['pointerdown','mousedown','mouseup','pointerup','dblclick','touchstart','touchend','contextmenu']
    .forEach(function(ev){{window.addEventListener(ev,function(e){{
      if(T&&T.contains(e.target))e.stopPropagation();
    }},true);}});
  window.addEventListener('click',function(e){{
    if(!T||!T.contains(e.target))return;
    e.stopPropagation();
    var b=e.target.closest?e.target.closest('#devai-clear'):null;
    if(b)clearClicked();
  }},true);
  // Space/Enter on a focused control must not shoot/flap/place a tower
  ['keydown','keyup'].forEach(function(ev){{window.addEventListener(ev,function(e){{
    if(T&&T.contains(document.activeElement)&&(e.key===' '||e.key==='Enter'))e.stopPropagation();
  }},true);}});

  /* ---- clear this game's saved data ---- */
  function label(html){{B.innerHTML=html;}}
  function disarm(){{armed=0;clearTimeout(armT);B.classList.remove('arm');
    label('<span class="da-i">&#128465;</span><span class="da-t">Clear</span>');}}
  function wipe(){{
    var gone=[];
    try{{
      var all=[];
      for(var i=0;i<localStorage.length;i++){{var k=localStorage.key(i);if(k)all.push(k);}}
      all.forEach(function(k){{
        var hit=KEYS.indexOf(k)>=0;
        if(!hit)for(var j=0;j<PREF.length;j++)if(k.indexOf(PREF[j])===0){{hit=true;break;}}
        if(hit){{try{{localStorage.removeItem(k);gone.push(k);}}catch(e){{}}}}
      }});
    }}catch(e){{}}
    return gone;
  }}
  function lockWrites(){{
    // Some games re-save from memory on pagehide/timer; without this the keys
    // we just deleted come back to life on the reload.
    try{{ Storage.prototype.setItem=function(){{/* dropped: cleared this session */}}; }}catch(e){{}}
  }}
  function clearClicked(){{
    if(!armed){{
      armed=1;B.classList.add('arm');
      label('<span class="da-i">&#9888;</span><span class="da-t">Sure?</span>');
      armT=setTimeout(disarm,3500);
      return;
    }}
    clearTimeout(armT);
    var gone=wipe();
    B.classList.remove('arm');B.classList.add('done');
    label(gone.length?'<span class="da-i">&#10003;</span><span class="da-t">Cleared '+gone.length+'</span>'
                     :'<span class="da-i">&#8709;</span><span class="da-t">Nothing saved</span>');
    if(gone.length){{ lockWrites(); setTimeout(function(){{location.reload();}},700); }}
    else setTimeout(disarm,1500);
  }}

  /* ---- placement: games that paint their HUD on the canvas park below it ---- */
  function place(){{
    if(!T||(!CFG.hud&&!CFG.fitW))return;
    var vw=window.innerWidth,vh=window.innerHeight,c=document.querySelector('canvas');
    var cr=c?c.getBoundingClientRect():{{x:0,y:0,width:vw,height:vh}};
    var h=T.offsetHeight||28,y;
    if(CFG.fitW){{
      // playfield is contain-fit INSIDE a full-bleed canvas: map logical y to the screen
      var f=Math.min(cr.width/CFG.fitW,cr.height/CFG.fitH);
      y=cr.y+(cr.height-CFG.fitH*f)/2+CFG.fitY*f+6;
    }}else{{
      y=cr.y+cr.height*CFG.hud+6;
    }}
    T.style.top=Math.round(Math.max(4,Math.min(y,vh-h-4)))+'px';
    T.style.bottom='auto';
  }}
  // never schedule with requestAnimationFrame: a background tab receives zero frames
  function queue(){{clearTimeout(t);t=setTimeout(place,50);}}
  window.addEventListener('resize',queue);
  window.addEventListener('orientationchange',function(){{setTimeout(place,150);}});
  document.addEventListener('visibilitychange',function(){{if(!document.hidden)place();}});
  function c0(){{return document.querySelector('canvas');}}
  if(window.ResizeObserver&&c0()){{try{{new ResizeObserver(queue).observe(c0());}}catch(e){{}}}}
  place();setTimeout(place,300);
  if(document.readyState!=='complete')window.addEventListener('load',function(){{place();setTimeout(place,300);}});
}})();
</script>
{END}
"""


def inject(name, dry=False):
    p = os.path.join(GDIR, name)
    s = open(p, encoding="utf-8").read()
    # replace the block and any blank lines around it with a single newline, so
    # repeated runs are byte-for-byte stable (no newline creep)
    s = re.sub(r"\n*[ \t]*" + re.escape(START) + r"[\s\S]*?" + re.escape(END) + r"[ \t]*\n*",
               "\n", s)
    m = re.search(r"<body[^>]*>", s, re.I)
    if not m:
        raise SystemExit("no <body> in " + name)
    out = s[: m.end()] + "\n" + snippet(name) + "\n" + s[m.end():]
    if not dry:
        open(p, "w", encoding="utf-8").write(out)
    return out


def main():
    on_disk = {f for f in os.listdir(GDIR) if f.endswith(".html")}
    if set(CFG) ^ on_disk:
        print("CONFIG/GAMES MISMATCH:", set(CFG) ^ on_disk, file=sys.stderr)
        sys.exit(1)
    # a prefix must never be able to clear another game's keys
    for a in CFG:
        for b in CFG:
            if a == b:
                continue
            for p in CFG[b].get("pref", []):
                for k in CFG[a].get("keys", []):
                    if k.startswith(p):
                        raise SystemExit(f"prefix collision: {b}:{p} would clear {a}:{k}")
    for name in sorted(CFG):
        before = len(open(os.path.join(GDIR, name), encoding="utf-8").read())
        out = inject(name)
        n = len(CFG[name].get("keys", []))
        ok = (out.count(START) == 1 and out.count('id="devai-home"') == 1
              and out.count('id="devai-clear"') == 1 and HREF in out)
        print(("OK  " if ok else "FAIL"), f"{name:24s} {before:6d} -> {len(out):6d}",
              f"{n} key{'s' if n != 1 else ''}",
              "js+css" if (CFG[name].get("hud") or CFG[name].get("fit")) else "css")
    print("total:", len(CFG))


if __name__ == "__main__":
    main()
