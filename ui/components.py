import html as _h

import folium
import streamlit as st
from folium.plugins import AntPath, Fullscreen
from streamlit_folium import st_folium

LIGHT = dict(bg="#EEF2EF", surface="#FFFFFF", surface2="#F4F7F5", ink="#0D1F26", muted="#56696F",
             line="#D8E0DC", accent="#0A8A6E", accentsoft="#DAF2EA", shadow="rgba(13,31,38,.10)", onaccent="#FFFFFF")
DARK = dict(bg="#081115", surface="#0F1E25", surface2="#142830", ink="#EAF2F0", muted="#93A8AF",
            line="#25404A", accent="#2FD1A6", accentsoft="#123830", shadow="rgba(0,0,0,.5)", onaccent="#04231C")
OPT_COLORS = ["#0A8A6E", "#E39A1F", "#5B7CFA", "#E8552F"]
PREFS = ["Fastest", "Cheapest", "Eco-friendly", "Balanced", "Custom"]
HINTS = {
    "Fastest": "Shortest travel time wins.",
    "Cheapest": "Lowest fare wins.",
    "Eco-friendly": "Lowest CO₂ wins.",
    "Balanced": "Our model weighs time, cost, delays and safety together.",
    "Custom": "Set how much each factor matters to you. Results re-rank as you move the sliders.",
}

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,500;9..144,600&family=Hanken+Grotesk:wght@400;500;600;700&display=swap');
@property --n{syntax:'<integer>';initial-value:0;inherits:false}
html,body,.stApp{font-family:'Hanken Grotesk',sans-serif!important;color:var(--ink)!important}
.stApp{background:var(--bg)!important}
header[data-testid="stHeader"],[data-testid="stSidebar"],[data-testid="stSidebarCollapsedControl"],[data-testid="stToolbar"],[data-testid="stDecoration"],footer,#MainMenu{display:none!important}
.block-container{max-width:1120px!important;padding:1rem 1.25rem 3rem!important}
[data-testid="stVerticalBlock"]{gap:1rem}
.stApp p,.stApp label,.stApp li,.stApp [data-testid="stMarkdownContainer"]{color:var(--ink)}
.stApp label p{color:var(--muted)!important;font-weight:600;font-size:.86rem}

/* ---------- inputs (forced, so they read correctly in both themes) ---------- */
.stApp [data-testid="stTextInputRootElement"],.stApp [data-baseweb="input"],.stApp [data-baseweb="base-input"]{background:var(--surface2)!important;border-radius:12px!important;border:1.5px solid var(--line)!important;min-height:3rem}
.stApp [data-testid="stTextInputRootElement"]:focus-within,.stApp [data-baseweb="input"]:focus-within{border-color:var(--accent)!important;box-shadow:0 0 0 3px var(--accentsoft)!important}
.stApp [data-baseweb="input"] [data-baseweb="base-input"]{border:0!important}
.stApp input{background:transparent!important;color:var(--ink)!important;-webkit-text-fill-color:var(--ink)!important;caret-color:var(--accent);font-size:1rem!important;height:2.9rem}
.stApp input::placeholder{color:var(--muted)!important;-webkit-text-fill-color:var(--muted)!important;opacity:.8}
.stApp [data-testid="InputInstructions"]{display:none}

/* ---------- buttons ---------- */
.stApp button{transition:transform .15s,box-shadow .2s,border-color .2s,background .2s}
.stApp button[kind="primary"],.stApp button[kind="primaryFormSubmit"]{background:var(--accent)!important;color:var(--onaccent)!important;border:0!important;border-radius:12px!important;height:3rem;font-weight:700!important;width:100%;box-shadow:0 8px 20px -8px var(--accent)}
.stApp button[kind="primary"] p,.stApp button[kind="primaryFormSubmit"] p{color:var(--onaccent)!important;font-size:1rem;font-weight:700}
.stApp button[kind="primary"]:hover,.stApp button[kind="primaryFormSubmit"]:hover{transform:translateY(-1px);filter:brightness(1.07)}
.stApp button[kind="secondary"],.stApp button[kind="secondaryFormSubmit"]{background:var(--surface2)!important;border:1px solid var(--line)!important;border-radius:12px!important;color:var(--ink)!important;width:100%;font-weight:600}
.stApp button[kind="secondary"] p,.stApp button[kind="secondaryFormSubmit"] p{color:var(--ink)!important;font-weight:600;font-size:.9rem}
.stApp button[kind="secondary"]:hover,.stApp button[kind="secondaryFormSubmit"]:hover{border-color:var(--accent)!important;transform:translateY(-1px)}
.stApp [data-testid="stForm"]{border:0!important;padding:0!important;background:transparent!important}
[data-testid="stForm"]>:first-child>:has(.st-key-places){order:1}.st-key-go{order:2}[data-testid="stForm"]>:first-child>:has(.st-key-examples){order:3}
.st-key-swap button{height:2.9rem;font-size:1.15rem}
:focus-visible{outline:3px solid var(--accent)!important;outline-offset:2px}

/* ---------- segmented controls ---------- */
.stApp [data-testid="stButtonGroup"]{gap:.45rem;flex-wrap:wrap}
.stApp [data-testid="stButtonGroup"] button,.stApp button[data-variant="segmented_control"]{background:var(--surface2)!important;border:1px solid var(--line)!important;border-radius:99px!important;padding:.35rem 1rem!important;height:auto;min-height:2.3rem;color:var(--ink)!important}
.stApp [data-testid="stButtonGroup"] button p{color:var(--ink)!important;font-weight:600;font-size:.92rem}
.stApp [data-testid="stButtonGroup"] button[aria-checked="true"]{background:var(--ink)!important;border-color:var(--ink)!important}
.stApp [data-testid="stButtonGroup"] button[aria-checked="true"] p{color:var(--bg)!important}
.stApp [data-testid="stButtonGroup"] [data-testid="stWidgetLabel"]{display:none}
.stApp [data-testid="stButtonGroup"] button:hover{border-color:var(--accent)!important;transform:translateY(-1px)}
.stApp [data-testid="stButtonGroup"] button[kind*="Active"]{background:var(--ink)!important;border-color:var(--ink)!important}
.stApp [data-testid="stButtonGroup"] button[kind*="Active"] p{color:var(--bg)!important}
.stApp div[role="radiogroup"]{gap:.45rem;flex-wrap:wrap}
.stApp div[role="radiogroup"] label{background:var(--surface2);border:1px solid var(--line);border-radius:99px;padding:.35rem 1rem;margin:0}
.stApp div[role="radiogroup"] label>div:first-child{display:none}
.stApp div[role="radiogroup"] label:has(input:checked){background:var(--ink)}
.stApp div[role="radiogroup"] label:has(input:checked) p{color:var(--bg)!important}
[data-testid="stSlider"] [data-testid="stTickBarMin"],[data-testid="stSlider"] [data-testid="stTickBarMax"]{color:var(--muted)!important}
[data-testid="stSlider"] [data-testid="stThumbValue"]{color:var(--ink)!important;font-weight:700}

/* ---------- dark toggle ---------- */
.st-key-dark_mode{position:fixed;top:16px;right:22px;z-index:1000;width:auto!important;background:rgba(6,30,34,.82);backdrop-filter:blur(8px);
 border:1px solid rgba(255,255,255,.18);border-radius:99px;padding:.3rem .9rem .3rem .7rem}
.stApp .st-key-dark_mode label p,.stApp .st-key-dark_mode [data-testid="stWidgetLabel"] p{color:#fff!important;font-size:.82rem;font-weight:600}

/* ---------- hero ---------- */
.hero{position:relative;overflow:hidden;border-radius:28px;padding:1.5rem 2.6rem 7rem;color:#fff;
 background:radial-gradient(120% 140% at 85% 0%,#14625F 0%,#0C3B41 45%,#082329 100%)}
.hero-nav{display:flex;align-items:center;gap:.6rem;flex-wrap:wrap;margin-bottom:3rem;padding-right:8.5rem;position:relative;z-index:2}
.brand{font-weight:700;font-size:1.05rem;margin-right:auto;display:flex;align-items:center;gap:.6rem;color:#fff}
.brand i{width:28px;height:28px;border-radius:9px;background:#2FD1A6;display:grid;place-items:center}
.brand i::after{content:"";width:12px;height:12px;border:3px solid #062F2B;border-radius:50%}
.chip{font-size:.78rem;padding:.32rem .75rem;border-radius:99px;background:rgba(255,255,255,.1);display:flex;align-items:center;gap:.45rem;color:#D8EDEA}
.chip b{width:7px;height:7px;border-radius:50%;background:#2FD1A6;box-shadow:0 0 0 0 rgba(47,209,166,.7);animation:ping 2.2s infinite}
.chip.bad b{background:#FF6B4A;animation:none}
@keyframes ping{70%{box-shadow:0 0 0 7px rgba(47,209,166,0)}100%{box-shadow:0 0 0 0 rgba(47,209,166,0)}}
.hero-copy{position:relative;z-index:2;max-width:23em}
.hero h1{font-family:'Fraunces',serif;font-weight:600;font-size:clamp(2.2rem,4.6vw,3.6rem);line-height:1.04;margin:0 0 1rem;color:#fff!important;letter-spacing:-.01em}
.hero p{font-size:1.08rem;line-height:1.55;color:#C3DDD9!important;margin:0}
.hero svg{position:absolute;right:-20px;top:64px;width:min(600px,58%);pointer-events:none}
.route{stroke-dasharray:1;stroke-dashoffset:1;animation:draw 2.4s .3s ease-out forwards}
@keyframes draw{to{stroke-dashoffset:0}}
.dest{transform-origin:560px 90px;animation:pulse 2.4s 2.6s infinite}
@keyframes pulse{0%{opacity:.9;transform:scale(1)}100%{opacity:0;transform:scale(3)}}

/* ---------- search card ---------- */
.st-key-search{margin-top:-4.6rem;position:relative;z-index:3;background:var(--surface);border:1px solid var(--line);
 border-radius:22px;padding:1.5rem 1.6rem 1.3rem;box-shadow:0 22px 50px -12px var(--shadow);margin-left:1.4rem;width:calc(100% - 2.8rem)!important}
.st-key-rankbar{background:var(--surface);border:1px solid var(--line);border-radius:18px;padding:1rem 1.4rem 1.2rem;box-shadow:0 8px 24px -10px var(--shadow)}
.rk-label{font-weight:700;font-size:.95rem;margin:0 0 .5rem}.hint{font-size:.9rem;color:var(--muted)!important;margin:.5rem 0 0}
.st-key-toolbar{padding:.2rem 0}

/* ---------- ticket ---------- */
.ticket{display:grid;grid-template-columns:1fr 240px;background:var(--surface);border:1px solid var(--line);border-radius:24px;
 box-shadow:0 20px 44px -16px var(--shadow);overflow:hidden;animation:rise .55s cubic-bezier(.2,.8,.2,1)}
@keyframes rise{from{opacity:0;transform:translateY(14px)}}
.t-main{padding:1.9rem 2.1rem}
.t-stub{padding:1.6rem 1.2rem;border-left:2px dashed var(--line);display:flex;flex-direction:column;align-items:center;justify-content:center;text-align:center;background:var(--surface2);gap:.8rem;position:relative}
.t-stub::before,.t-stub::after{content:"";position:absolute;left:-13px;width:24px;height:24px;border-radius:50%;background:var(--bg);border:1px solid var(--line)}
.t-stub::before{top:-13px}.t-stub::after{bottom:-13px}
.pill{display:inline-block;background:var(--accentsoft);color:var(--accent)!important;font-weight:700;font-size:.8rem;padding:.28rem .75rem;border-radius:99px}
.pill.mute{background:var(--surface2);color:var(--muted)!important;border:1px solid var(--line)}
.t-main h2{font-family:'Fraunces',serif;font-weight:600;font-size:2.4rem;margin:.75rem 0 .15rem;color:var(--ink)!important;display:flex;align-items:center;gap:.7rem;flex-wrap:wrap}
.t-main h2 svg{width:30px;height:30px;stroke:var(--accent);fill:none;stroke-width:1.8}
.t-route{color:var(--muted)!important;font-weight:600;margin-bottom:.8rem}
.why{max-width:40em;line-height:1.55;margin:0 0 1rem;font-size:1.02rem}
.badges{display:flex;flex-wrap:wrap;gap:.45rem;margin-bottom:1.5rem}
.bd{font-size:.8rem;font-weight:600;padding:.25rem .65rem;border-radius:8px;background:var(--surface2);border:1px solid var(--line);color:var(--muted)!important}
.bd.win{background:var(--accentsoft);border-color:transparent;color:var(--accent)!important}
.stats{display:flex;flex-wrap:wrap;gap:1.3rem 2.4rem}
.stat>span{display:block;font-size:.8rem;color:var(--muted)!important;font-weight:600}
.stat small{display:block;font-size:.76rem;color:var(--muted)!important;margin-top:.1rem}
.stat b{font-family:'Fraunces',serif;font-size:1.75rem;font-weight:600;color:var(--ink)!important;font-variant-numeric:tabular-nums}
.cnt{--n:var(--to);counter-reset:num var(--n);animation:count 1.1s .1s cubic-bezier(.2,.7,.2,1) backwards}
.cnt{font-style:normal}.cnt::after{content:counter(num)}
.stat .u{font-family:'Hanken Grotesk',sans-serif;font-size:.95rem;font-weight:600;color:var(--muted)!important;margin-left:.15rem}
@keyframes count{from{--n:0}}
.ring{--p:0;width:120px;height:120px;border-radius:50%;background:conic-gradient(var(--accent) calc(var(--p)*1%),var(--line) 0);display:grid;place-items:center;position:relative;animation:ringin 1.2s cubic-bezier(.2,.7,.2,1)}
@property --p{syntax:'<number>';initial-value:0;inherits:true}
@keyframes ringin{from{--p:0}}
.ring::after{content:"";position:absolute;inset:11px;background:var(--surface2);border-radius:50%}
.ring b{position:relative;z-index:1;font-family:'Fraunces',serif;font-size:1.7rem;color:var(--ink)!important}
.t-stub small{color:var(--muted)!important;line-height:1.4}

/* ---------- map ---------- */
.st-key-mapcard{background:var(--surface);border:1px solid var(--line);border-radius:24px;padding:1.3rem 1.3rem .5rem;box-shadow:0 14px 34px -14px var(--shadow)}
.st-key-mapcard iframe{border-radius:16px;border:1px solid var(--line)}
.sec{font-family:'Fraunces',serif;font-size:1.5rem;font-weight:600;margin:.4rem 0 .15rem;color:var(--ink)!important}
.sec-sub{color:var(--muted)!important;margin:0 0 .6rem;font-size:.95rem}

/* ---------- comparison ---------- */
.lanes{background:var(--surface);border:1px solid var(--line);border-radius:22px;padding:.4rem 1.3rem;box-shadow:0 14px 34px -14px var(--shadow)}
.lane{display:grid;grid-template-columns:1.7fr 1fr 1fr 1fr;gap:1rem;align-items:center;padding:1rem 0;border-bottom:1px solid var(--line);transition:background .2s}
.lane:last-child{border:0}.lane.head{font-size:.8rem;font-weight:600;color:var(--muted)!important;padding:.8rem 0}
.lane:not(.head):hover{background:var(--surface2);margin:0 -1.3rem;padding:1rem 1.3rem}
.lm{display:flex;align-items:center;gap:.55rem;font-weight:700;flex-wrap:wrap}
.rk{width:26px;height:26px;border-radius:50%;display:grid;place-items:center;font-size:.8rem;font-weight:700;color:#fff;flex:none}
.lc span{font-weight:600;font-size:.95rem}.lc i{display:block;height:6px;border-radius:9px;background:var(--line);margin-top:.4rem;position:relative}
.lc i::after{content:"";position:absolute;inset:0;width:var(--w);border-radius:9px;background:var(--muted);opacity:.55;transform-origin:left;animation:grow .9s cubic-bezier(.2,.7,.2,1)}
.lc i.best::after{background:var(--accent);opacity:1}
@keyframes grow{from{transform:scaleX(0)}}
.lane.win{background:linear-gradient(90deg,var(--accentsoft),transparent)}

/* ---------- radar ---------- */
.radar{background:var(--surface);border:1px solid var(--line);border-radius:22px;padding:1rem 1.2rem 1.2rem;box-shadow:0 14px 34px -14px var(--shadow);height:100%}
.radar svg{width:100%;max-width:340px;display:block;margin:0 auto}
.radar .pl{transition:opacity .2s,stroke-width .2s;cursor:pointer}
.radar .ax{stroke:var(--line);fill:none}.radar text{fill:var(--muted);font:600 11px 'Hanken Grotesk',sans-serif}
.legend{display:flex;flex-wrap:wrap;gap:.4rem .5rem;justify-content:center;margin-top:.4rem}
.lg{font-size:.82rem;font-weight:600;padding:.25rem .65rem;border-radius:99px;border:1px solid var(--line);display:flex;align-items:center;gap:.4rem;cursor:pointer}
.lg i{width:9px;height:9px;border-radius:50%}
.radar .note{text-align:center;font-size:.8rem;color:var(--muted)!important;margin:.5rem 0 0}

/* ---------- misc ---------- */
.callout{background:var(--surface);border:1px solid var(--line);border-left:5px solid #E8552F;border-radius:16px;padding:1.2rem 1.5rem}
.callout b{display:block;margin-bottom:.2rem}
.skel{background:var(--surface);border:1px solid var(--line);border-radius:24px;padding:2rem;display:grid;gap:.9rem}
.skel i{display:block;height:16px;border-radius:9px;background:linear-gradient(90deg,var(--line) 20%,var(--surface2) 40%,var(--line) 60%);background-size:250% 100%;animation:sweep 1.3s linear infinite}
.skel i:first-child{height:36px;width:40%}.skel i:nth-child(2){width:70%}.skel i:nth-child(3){width:55%}
.skel span{font-weight:600;color:var(--muted)!important}
@keyframes sweep{to{background-position:-250% 0}}
.facts{display:grid;grid-template-columns:repeat(3,1fr);gap:1rem}
.fact{padding:1.2rem 1.3rem;border-radius:18px;background:var(--surface);border:1px solid var(--line);transition:transform .2s,border-color .2s}
.fact:hover{transform:translateY(-3px);border-color:var(--accent)}
.fact b{display:block;margin-bottom:.3rem;font-size:1.02rem}.fact span{color:var(--muted)!important;font-size:.93rem;line-height:1.5}
.fact svg{width:26px;height:26px;stroke:var(--accent);fill:none;stroke-width:1.8;margin-bottom:.6rem}
.foot{text-align:center;color:var(--muted)!important;font-size:.85rem;margin-top:2rem}
.stApp [data-testid="stDownloadButton"] button{background:var(--surface)!important;border:1px solid var(--line)!important;color:var(--ink)!important;border-radius:12px!important;font-weight:600}
.stApp [data-testid="stDownloadButton"] button p{color:var(--ink)!important}
.lm svg{width:20px;height:20px;stroke:var(--ink);fill:none;stroke-width:1.8}

@media(max-width:860px){.ticket{grid-template-columns:1fr}.t-stub{border-left:0;border-top:2px dashed var(--line)}.t-stub::before,.t-stub::after{display:none}
 .lane{grid-template-columns:1fr 1fr}.lane.head{display:none}.hero svg{opacity:.22;width:90%}.hero{padding:1.2rem 1.4rem 6.5rem}.hero-copy{max-width:none}
 .facts{grid-template-columns:1fr}.st-key-search{margin-left:0;width:100%!important}}
@media(prefers-reduced-motion:reduce){*{animation:none!important;transition:none!important}.route{stroke-dashoffset:0}.mover{display:none}}
</style>
"""

ICON = {
    "road": '<svg viewBox="0 0 24 24"><path d="M8 3 5 21M16 3l3 18M12 4v3m0 4v3m0 4v2"/></svg>',
    "rail": '<svg viewBox="0 0 24 24"><rect x="6" y="3" width="12" height="13" rx="3"/><path d="M6 11h12M9 20l-2 2M15 20l2 2"/></svg>',
    "flight": '<svg viewBox="0 0 24 24"><path d="M17.8 19.2 16 11l3.5-3.5C21 6 21.5 4 21 3c-1-.5-3 0-4.5 1.5L13 8 4.8 6.2c-.5-.1-.9.1-1.1.5l-.3.5c-.2.5-.1 1 .3 1.3L9 12l-2 3H4l-1 1 3 2 2 3 1-1v-3l3-2 3.5 5.3c.3.4.8.5 1.3.3l.5-.2c.4-.3.6-.7.5-1.2z"/></svg>',
}


def html(s):
    st.markdown(" ".join(l.strip() for l in s.strip().splitlines() if l.strip()), unsafe_allow_html=True)


def esc(x):
    return _h.escape(str(x))


def inject_css(dark):
    p = DARK if dark else LIGHT
    st.markdown("<style>:root{" + "".join(f"--{k}:{v};" for k, v in p.items()) + "}</style>" + CSS, unsafe_allow_html=True)


def short(place):
    return str(place).split(",")[0].strip()


def fmt_time(hr):
    m = round(hr * 60)
    return f"{m} min" if m < 60 else f"{m // 60} h {m % 60:02d} min"


def money(v):
    return f"&#36;{v:,.2f}"


def cnt(v, suffix="", dec=0):
    r = round(v, dec)
    frac = f".{r:.{dec}f}".split(".")[-1] if dec else ""
    u = f'<span class="u">{suffix}</span>' if suffix else ""
    return f'<em class="cnt" style="--to:{int(r)}"></em>{"." + frac if dec else ""}{u}'


def mode_icons(mode):
    return "".join(ICON["flight" if "Flight" in p else "rail" if "Rail" in p else "road"] for p in mode.split("+"))


# --------------------------------------------------------------- ranking
def rank_options(cands, pref, weights=(5, 5, 5)):
    if pref == "Fastest":
        return sorted(cands, key=lambda c: c["travel_time_hr"])
    if pref == "Cheapest":
        return sorted(cands, key=lambda c: c["travel_cost"])
    if pref == "Eco-friendly":
        return sorted(cands, key=lambda c: c["carbon_emission"])
    if pref == "Custom":
        keys = ("travel_time_hr", "travel_cost", "carbon_emission")
        lo = {k: min(c[k] for c in cands) for k in keys}
        hi = {k: max(c[k] for c in cands) for k in keys}
        tot = sum(weights) or 1

        def cost_of(c):
            return sum(w * ((c[k] - lo[k]) / ((hi[k] - lo[k]) or 1)) for w, k in zip(weights, keys)) / tot
        return sorted(cands, key=cost_of)
    return sorted(cands, key=lambda c: c["score"], reverse=True)


# --------------------------------------------------------------- hero
def render_hero(status):
    ok_m, ok_g = status["model_loaded"], status["graph_loaded"]
    chips = (f'<span class="chip {"" if ok_m else "bad"}"><b></b>{"Model ready" if ok_m else "Model missing"}</span>'
             f'<span class="chip {"" if ok_g else "bad"}"><b></b>'
             + (f'{status["graph_nodes"]:,} road nodes loaded' if ok_g else "Road graph missing") + "</span>")
    html(f"""
    <section class="hero">
      <div class="hero-nav"><div class="brand"><i></i>Multimodal Transport</div>{chips}</div>
      <div class="hero-copy">
        <h1>Choose what matters. We'll find the route.</h1>
        <p>Compare road, rail and air across Central America by travel time, cost and carbon, then get one clear recommendation.</p>
      </div>
      <svg viewBox="0 0 640 340" aria-hidden="true">
        <g fill="none" stroke="rgba(255,255,255,.1)" stroke-width="1.5" transform="rotate(-16 320 170)">
          <ellipse cx="330" cy="170" rx="70" ry="42"/><ellipse cx="330" cy="170" rx="120" ry="76"/>
          <ellipse cx="330" cy="170" rx="175" ry="112"/><ellipse cx="330" cy="170" rx="235" ry="150"/><ellipse cx="330" cy="170" rx="300" ry="190"/>
        </g>
        <path id="rt" class="route" pathLength="1" d="M110 270 C 210 290, 250 150, 340 175 S 470 70, 560 90" fill="none" stroke="#2FD1A6" stroke-width="4" stroke-linecap="round"/>
        <circle cx="110" cy="270" r="9" fill="#fff"/>
        <circle class="dest" cx="560" cy="90" r="9" fill="#2FD1A6"/>
        <circle cx="560" cy="90" r="9" fill="#2FD1A6" stroke="#fff" stroke-width="3"/>
        <circle class="mover" r="6" fill="#fff"><animateMotion dur="6s" begin="2.5s" repeatCount="indefinite"><mpath href="#rt"/></animateMotion></circle>
      </svg>
    </section>""")


def render_empty():
    a = '<svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/></svg>'
    b = '<svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="9"/><path d="M14.5 9.5c-.5-.8-1.400-1.200-2.500-1.200-1.500 0-2.500.7-2.500 1.800 0 2.600 5 1.100 5 3.800 0 1.100-1 1.800-2.600 1.800-1.200 0-2.100-.4-2.700-1.200M12 6.500v2M12 15.700v2"/></svg>'
    c = '<svg viewBox="0 0 24 24"><path d="M5 19c8 0 14-6 14-14-8 0-14 6-14 14zM5 19c2-5 6-8 10-9"/></svg>'
    html(f"""
    <div class="facts">
      <div class="fact">{a}<b>Travel time</b><span>Door-to-door duration for each option, including transfers.</span></div>
      <div class="fact">{b}<b>Cost</b><span>Estimated fare per traveller in US dollars.</span></div>
      <div class="fact">{c}<b>Carbon</b><span>Kilograms of CO₂, so you can see the climate impact.</span></div>
    </div>""")


def skeleton_html():
    return '<div class="skel"><span>Finding your route…</span><i></i><i></i><i></i></div>'


def render_callout(title, body):
    html(f'<div class="callout"><b>{esc(title)}</b>{esc(body)}</div>')


# --------------------------------------------------------------- ticket
def explain(opt, ranked, pref):
    pos = ranked.index(opt)
    others = [c for c in ranked if c is not opt]
    if pos > 0:
        return f"Ranked #{pos + 1} of {len(ranked)} for {pref.lower()}. {ranked[0]['mode']} is the top pick."
    if pref == "Fastest" and others:
        d = min(o["travel_time_hr"] for o in others) - opt["travel_time_hr"]
        if d > 0:
            return f"Saves about {fmt_time(d)} compared with the next fastest option."
    if pref == "Cheapest" and others:
        d = min(o["travel_cost"] for o in others) - opt["travel_cost"]
        if d > 0:
            return f"Costs {money(d)} less per person than the next cheapest option."
    if pref == "Eco-friendly" and others:
        d = min(o["carbon_emission"] for o in others) - opt["carbon_emission"]
        if d > 0:
            return f"Emits {d:.2f} kg less CO₂ than the next cleanest option."
    if pref == "Custom":
        return "Comes out on top for the mix of time, cost and carbon you set."
    return f"Scores {opt['score_pct']:.0f}% for how well it balances travel time, cost, delays and safety."


def badges(opt, cands):
    t0 = min(c["travel_time_hr"] for c in cands)
    c0 = min(c["travel_cost"] for c in cands)
    e0 = min(c["carbon_emission"] for c in cands)
    out = []
    if opt["travel_time_hr"] == t0:
        out.append('<span class="bd win">Fastest</span>')
    else:
        out.append(f'<span class="bd">+{fmt_time(opt["travel_time_hr"] - t0)} vs fastest</span>')
    if opt["travel_cost"] == c0:
        out.append('<span class="bd win">Cheapest</span>')
    else:
        out.append(f'<span class="bd">+{money(opt["travel_cost"] - c0)} vs cheapest</span>')
    if opt["carbon_emission"] == e0:
        out.append('<span class="bd win">Lowest carbon</span>')
    else:
        out.append(f'<span class="bd">+{opt["carbon_emission"] - e0:.2f} kg vs greenest</span>')
    return "".join(out)


def time_html(hr):
    m = round(hr * 60)
    if m < 60:
        return cnt(m, " min")
    return cnt(m // 60, " h ") + cnt(m % 60, " min")


def render_ticket(opt, ranked, src, dst, pref, travellers):
    is_best = opt is ranked[0]
    pill = (f'<span class="pill">Recommended for {esc(pref.lower())}</span>' if is_best
            else f'<span class="pill mute">Option ranked #{ranked.index(opt) + 1}</span>')
    total = opt["travel_cost"] * travellers
    cost_sub = f"<small>{money(opt['travel_cost'])} per person</small>" if travellers > 1 else ""
    cost_lab = "Cost" if travellers == 1 else f"Cost for {travellers}"
    stats = [("Travel time", time_html(opt["travel_time_hr"]), ""),
             (cost_lab, "&#36;" + cnt(total, dec=2), cost_sub),
             ("Carbon per person", cnt(opt["carbon_emission"], " kg", 2), ""),
             ("Distance", cnt(opt["distance_km"], " km", 1), ""),
             ("Transfers", cnt(opt["transfers"]), "")]
    cells = "".join(f'<div class="stat"><span>{k}</span><b>{v}</b>{s}</div>' for k, v, s in stats)
    html(f"""
    <section class="ticket">
      <div class="t-main">
        {pill}
        <h2>{mode_icons(opt['mode'])}{esc(opt['mode'])}</h2>
        <div class="t-route">{esc(short(src))} to {esc(short(dst))}</div>
        <p class="why">{explain(opt, ranked, pref)}</p>
        <div class="badges">{badges(opt, ranked)}</div>
        <div class="stats">{cells}</div>
      </div>
      <div class="t-stub">
        <div class="ring" style="--p:{opt['score_pct']:.0f}"><b>{opt['score_pct']:.0f}%</b></div>
        <small>Suitability score from the Random Forest model</small>
      </div>
    </section>""")


# --------------------------------------------------------------- map
def render_map(src_geo, dst_geo, coords, dark, view_key):
    a = (src_geo["latitude"], src_geo["longitude"])
    b = (dst_geo["latitude"], dst_geo["longitude"])
    line = list(coords) if coords and len(coords) > 1 else [a, b]
    if len(line) > 1500:
        step = len(line) // 1500 + 1
        line = line[::step] + [line[-1]]
    m = folium.Map(location=[(a[0] + b[0]) / 2, (a[1] + b[1]) / 2], zoom_start=10, control_scale=True, tiles=None)
    # Key-free tile sources (Carto's basemaps now demand an API key, so they are not used).
    osm = "https://tile.openstreetmap.org/{z}/{x}/{y}.png"
    osm_attr = "&copy; OpenStreetMap contributors"
    esri = "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
    m.get_root().header.add_child(folium.Element(
        "<style>.tiles-soft{filter:saturate(.65) brightness(1.04)}"
        ".tiles-dark{filter:invert(1) hue-rotate(180deg) brightness(.92) contrast(.88) saturate(.7)}</style>"))
    layers = [("Streets", osm, osm_attr, "tiles-soft", 19), ("Dark", osm, osm_attr, "tiles-dark", 19),
              ("Satellite", esri, "Imagery &copy; Esri, Maxar, Earthstar Geographics", "", 18)]
    layers.sort(key=lambda t: t[0] != ("Dark" if dark else "Streets"))
    for i, (name, url, attr, cls, zmax) in enumerate(layers):
        folium.TileLayer(url, name=name, attr=attr, max_zoom=zmax, className=cls, show=(i == 0)).add_to(m)
    folium.LayerControl(collapsed=True, position="topright").add_to(m)
    Fullscreen(position="topleft").add_to(m)
    folium.PolyLine(line, color="#000000", weight=10, opacity=.18).add_to(m)
    AntPath(line, color="#0A8A6E" if not dark else "#2FD1A6", pulse_color="#FFFFFF", weight=5, delay=1400, dash_array=[12, 22]).add_to(m)
    for pt, label, colour, txt in ((a, short(src_geo["place"]), "#0D1F26", "A"), (b, short(dst_geo["place"]), "#0A8A6E", "B")):
        pin = (f'<div style="width:34px;height:34px;border-radius:50%;background:{colour};color:#fff;font:700 15px sans-serif;'
               f'display:grid;place-items:center;border:3px solid #fff;box-shadow:0 3px 10px rgba(0,0,0,.35)">{txt}</div>')
        folium.Marker(pt, icon=folium.DivIcon(html=pin, icon_size=(34, 34), icon_anchor=(17, 17)),
                      tooltip=folium.Tooltip(esc(label), permanent=True, direction="top", offset=(0, -18))).add_to(m)
    pts = line + [a, b]
    m.fit_bounds([[min(p[0] for p in pts), min(p[1] for p in pts)], [max(p[0] for p in pts), max(p[1] for p in pts)]], padding=(40, 40))
    with st.container(key="mapcard"):
        html('<div class="sec" style="margin-top:0">Your route</div><p class="sec-sub">Shortest path on the road network. Use the layer button to switch map styles.</p>')
        st_folium(m, height=440, returned_objects=[], key=view_key, use_container_width=True)


# --------------------------------------------------------------- compare + radar
def render_compare(ranked, best_mode, colors):
    keys = ("travel_time_hr", "travel_cost", "carbon_emission")
    lo = {k: min(c[k] for c in ranked) for k in keys}
    hi = {k: (max(c[k] for c in ranked) or 1) for k in keys}

    def cell(c, k, text):
        w = max(8, c[k] / hi[k] * 100)
        return f'<div class="lc"><span>{text}</span><i class="{"best" if c[k] == lo[k] else ""}" style="--w:{w:.0f}%"></i></div>'

    rows = '<div class="lane head"><div>Option, best first</div><div>Time</div><div>Cost per person</div><div>Carbon</div></div>'
    for i, c in enumerate(ranked):
        win = " win" if c["mode"] == best_mode else ""
        rows += (f'<div class="lane{win}"><div class="lm"><span class="rk" style="background:{colors[c["mode"]]}">{i + 1}</span>'
                 f'{mode_icons(c["mode"])}{esc(c["mode"])}</div>'
                 + cell(c, "travel_time_hr", fmt_time(c["travel_time_hr"])) + cell(c, "travel_cost", money(c["travel_cost"]))
                 + cell(c, "carbon_emission", f'{c["carbon_emission"]:.2f} kg') + "</div>")
    html('<div class="sec">All options compared</div><p class="sec-sub">Green bars mark the best value in each column.</p>')
    html(f'<div class="lanes">{rows}</div>')


def render_radar(cands, colors):
    import math
    keys = ("travel_time_hr", "travel_cost", "carbon_emission")
    lo = {k: min(c[k] for c in cands) for k in keys}
    hi = {k: max(c[k] for c in cands) for k in keys}
    cx, cy, R = 150, 128, 88
    ang = [-90, 30, 150]

    def pt(r, i):
        a = math.radians(ang[i])
        return cx + r * math.cos(a), cy + r * math.sin(a)

    grid = "".join('<polygon class="ax" points="' + " ".join(f"{pt(R * f, i)[0]:.1f},{pt(R * f, i)[1]:.1f}" for i in range(3)) + '"/>' for f in (.33, .66, 1))
    spokes = "".join(f'<line class="ax" x1="{cx}" y1="{cy}" x2="{pt(R, i)[0]:.1f}" y2="{pt(R, i)[1]:.1f}"/>' for i in range(3))
    labels = (f'<text x="{cx}" y="{cy - R - 12}" text-anchor="middle">Speed</text>'
              f'<text x="{pt(R, 1)[0] + 8:.0f}" y="{pt(R, 1)[1] + 16:.0f}" text-anchor="end">Low cost</text>'
              f'<text x="{pt(R, 2)[0] - 8:.0f}" y="{pt(R, 2)[1] + 16:.0f}" text-anchor="start">Low carbon</text>')
    polys, legend, css = "", "", ""
    for n, c in enumerate(cands):
        r = [R * (1 - 0.78 * (c[k] - lo[k]) / ((hi[k] - lo[k]) or 1)) for k in keys]
        p = " ".join(f"{pt(r[i], i)[0]:.1f},{pt(r[i], i)[1]:.1f}" for i in range(3))
        col = colors[c["mode"]]
        polys += f'<polygon class="pl pl{n}" points="{p}" fill="{col}" fill-opacity=".18" stroke="{col}" stroke-width="2.5" stroke-linejoin="round"><title>{esc(c["mode"])}</title></polygon>'
        legend += f'<span class="lg lg{n}"><i style="background:{col}"></i>{esc(c["mode"])}</span>'
        css += (f'.radar:has(.lg{n}:hover) .pl:not(.pl{n}),.radar:has(.pl{n}:hover) .pl:not(.pl{n}){{opacity:.12}}'
                f'.radar:has(.lg{n}:hover) .pl{n},.radar:has(.pl{n}:hover) .pl{n}{{fill-opacity:.4;stroke-width:4}}')
    html(f"""
    <style>{css}</style>
    <div class="sec">Trade-offs</div><p class="sec-sub">Hover an option to isolate it.</p>
    <div class="radar">
      <svg viewBox="0 0 300 250" role="img" aria-label="Radar chart comparing speed, cost and carbon">{grid}{spokes}{labels}{polys}</svg>
      <div class="legend">{legend}</div>
      <p class="note">Further out is better on every axis.</p>
    </div>""")


def render_footer():
    html('<div class="foot">Built with Python, NetworkX, scikit-learn and OpenStreetMap data.</div>')
