import os
import sys

import pandas as pd
import streamlit as st

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from ui.utils import check_system_status, calculate_route_recommendation
from ui.components import (
    PREFS, HINTS, OPT_COLORS, html, inject_css, render_hero, render_empty, skeleton_html, render_callout,
    rank_options, render_ticket, render_map, render_compare, render_radar, render_footer,
)

st.set_page_config(page_title="Multimodal Transport", page_icon="🚆", layout="wide", initial_sidebar_state="collapsed")

st.session_state.setdefault("src", "Guatemala City")
st.session_state.setdefault("dst", "Antigua Guatemala")
st.session_state.setdefault("result", None)


def swap_places():
    st.session_state.src, st.session_state.dst = st.session_state.dst, st.session_state.src


def use_example(a, b):
    st.session_state.src, st.session_state.dst = a, b


def fsb(target, label, **kw):
    """Full-width form button that works across Streamlit versions."""
    try:
        return target.form_submit_button(label, width="stretch", **kw)
    except TypeError:
        return target.form_submit_button(label, use_container_width=True, **kw)


def choice(label, options, key, default=None, fmt=None):
    """Pill selector (falls back to radio on older Streamlit versions)."""
    if hasattr(st, "segmented_control"):
        kw = {"format_func": fmt} if fmt else {}
        return st.segmented_control(label, options, default=default, key=key, label_visibility="collapsed", **kw)
    kw = {"format_func": fmt} if fmt else {}
    return st.radio(label, options, index=options.index(default) if default in options else 0, key=key,
                    horizontal=True, label_visibility="collapsed", **kw)


dark = st.session_state.get("dark_mode", False)
inject_css(dark)
st.toggle("Dark mode", key="dark_mode")
render_hero(check_system_status())

# ------------------------------------------------------------ search
go = False
with st.container(key="search"):
    with st.form("search_form", border=False):
        # The main button comes first in the page so that pressing Enter in a field runs the search
        # (browsers pick the first submit button). CSS `order` puts it back below the fields visually.
        go = fsb(st, "Find my route", type="primary", key="go")
        with st.container(key="places"):
            c1, c2, c3 = st.columns([10, 1.3, 10], vertical_alignment="bottom")
            c1.text_input("From", key="src", placeholder="City or address")
            fsb(c2, "⇄", key="swap", on_click=swap_places, help="Swap start and destination")
            c3.text_input("To", key="dst", placeholder="City or address")
        with st.container(key="examples"):
            st.markdown('<p class="hint" style="margin:.2rem 0 0">Try one of these</p>', unsafe_allow_html=True)
            e1, e2, e3 = st.columns(3)
            fsb(e1, "Guatemala City to Antigua", key="ex1", on_click=use_example, args=("Guatemala City", "Antigua Guatemala"))
            fsb(e2, "Guatemala City to Quetzaltenango", key="ex2", on_click=use_example, args=("Guatemala City", "Quetzaltenango"))
            fsb(e3, "Guatemala City to Puerto Barrios", key="ex3", on_click=use_example, args=("Guatemala City", "Puerto Barrios"))

# ------------------------------------------------------------ rank bar (live)
with st.container(key="rankbar"):
    html('<p class="rk-label">What matters most?</p>')
    pref = choice("What matters most?", PREFS, "pref", default="Balanced") or "Balanced"
    html(f'<p class="hint">{HINTS[pref]}</p>')
    weights = (5, 5, 5)
    if pref == "Custom":
        w1, w2, w3 = st.columns(3)
        weights = (w1.slider("Speed", 0, 10, 5, key="w_time"), w2.slider("Low cost", 0, 10, 5, key="w_cost"),
                   w3.slider("Low carbon", 0, 10, 5, key="w_co2"))

# ------------------------------------------------------------ compute
slot = st.empty()
if go:
    if not st.session_state.src.strip() or not st.session_state.dst.strip():
        st.session_state.result = {"error": "Enter both a starting point and a destination."}
    else:
        slot.markdown(skeleton_html(), unsafe_allow_html=True)
        res = calculate_route_recommendation(st.session_state.src.strip(), st.session_state.dst.strip(), "Balanced")
        st.session_state.result = res
        if isinstance(res, dict) and res.get("success"):
            st.session_state.pop("inspect", None)
            st.toast(f"Route found: {res['src_geo']['place'].split(',')[0]} to {res['dst_geo']['place'].split(',')[0]}", icon="✅")
    slot.empty()

# ------------------------------------------------------------ results
res = st.session_state.result
if not res:
    render_empty()
elif "error" in res:
    render_callout("We couldn't plan that trip", f"{res['error']} Check the spelling, or add the country, for example “Antigua, Guatemala”.")
elif res.get("success"):
    cands = res["candidates"]
    colors = {c["mode"]: OPT_COLORS[i % len(OPT_COLORS)] for i, c in enumerate(cands)}
    ranked = rank_options(cands, pref, weights)
    best = ranked[0]

    # Jump the "viewing" pill to the new winner whenever the ranking changes.
    sig = (pref, weights, best["mode"], id(res))
    if st.session_state.get("_sig") != sig:
        st.session_state["_sig"] = sig
        st.session_state["inspect"] = best["mode"]

    with st.container(key="toolbar"):
        t1, t2 = st.columns([3, 1.4], vertical_alignment="bottom")
        with t1:
            html('<p class="rk-label" style="margin-bottom:.4rem">Viewing</p>')
            modes = [c["mode"] for c in ranked]
            picked = choice("Viewing", modes, "inspect", default=None,
                            fmt=lambda m: f"★ {m}" if m == best["mode"] else m) or best["mode"]
        with t2:
            travellers = st.slider("Travellers", 1, 8, 1, key="travellers")
    opt = next(c for c in ranked if c["mode"] == picked)

    render_ticket(opt, ranked, res["src_geo"]["place"], res["dst_geo"]["place"], pref, travellers)
    render_map(res["src_geo"], res["dst_geo"], res["route_coords"], dark, f"map_{int(dark)}_{st.session_state.src}_{st.session_state.dst}")

    left, right = st.columns([1.65, 1])
    with left:
        render_compare(ranked, best["mode"], colors)
    with right:
        render_radar(cands, colors)

    df = pd.DataFrame({
        "Option": [c["mode"] for c in ranked], "Distance (km)": [c["distance_km"] for c in ranked],
        "Time (h)": [c["travel_time_hr"] for c in ranked], "Cost (USD)": [c["travel_cost"] for c in ranked],
        "Carbon (kg CO2)": [c["carbon_emission"] for c in ranked], "Transfers": [c["transfers"] for c in ranked],
        "Score (%)": [c["score_pct"] for c in ranked],
    })
    st.download_button("Download comparison as CSV", df.to_csv(index=False).encode("utf-8"), "route_comparison.csv", "text/csv")

render_footer()
