# app.py
import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch
from constants import *
from physics import *
from visualization import *

st.set_page_config(page_title="ASD Centurion V5.25", layout="wide")

# --- STATE ---
if "p1" not in st.session_state:
    st.session_state.update({"p1": 50, "a1": 0, "p2": 50, "a2": 0, "pp_x": 0.0, "pp_y": 5.42})

def set_engine_state(p1, a1, p2, a2):
    st.session_state.p1, st.session_state.a1 = p1, a1
    st.session_state.p2, st.session_state.a2 = p2, a2

def reset_engines(): set_engine_state(50, 0, 50, 0)
def reset_pivot(): st.session_state.pp_x, st.session_state.pp_y = 0.0, 5.42

# --- HEADER ---
st.markdown("<h1 style='text-align: center;'>⚓ Rimorchiatore ASD 'CENTURION'</h1>", unsafe_allow_html=True)
st.markdown(f"""
<div style='text-align: center;'>
    <p style='font-size: 18px; margin-bottom: 10px;'>Per informazioni contattare stefano.bandi22@gmail.com</p>
    <b>Dimensioni:</b> 32.50 m x 11.70 m | <b>Bollard Pull:</b> 70 ton | <b>Logica:</b> Ibrida (Intersezione < 50m / Centro Ponderato)
</div>
""", unsafe_allow_html=True)
st.write("---")

# --- SIDEBAR ---
with st.sidebar:
    st.header("Comandi Globali")
    c1, c2 = st.columns(2)
    c1.button("Reset Motori", on_click=reset_engines, type="primary", use_container_width=True)
    c2.button("Reset Pivot Point", on_click=reset_pivot, use_container_width=True)
    st.markdown("---")
    st.markdown("### ↕️ Longitudinali")
    cf1, cf2 = st.columns(2)
    cf1.button("Tutta AVANTI", on_click=set_engine_state, args=(100,0,100,0), use_container_width=True)
    cf2.button("Mezza AVANTI", on_click=set_engine_state, args=(50,0,50,0), use_container_width=True)
    ca1, ca2 = st.columns(2)
    ca1.button("Tutta INDIETRO", on_click=set_engine_state, args=(100,180,100,180), use_container_width=True)
    ca2.button("Mezza INDIETRO", on_click=set_engine_state, args=(50,180,50,180), use_container_width=True)
    st.markdown("---")
    st.markdown("### ↔️ Side Step")
    r1, r2 = st.columns(2)
    r1.button("⬅️ Fast SX", on_click=apply_fast_side_step, args=("SINISTRA",), use_container_width=True)
    r2.button("➡️ Fast DX", on_click=apply_fast_side_step, args=("DRITTA",), use_container_width=True)
    r3, r4 = st.columns(2)
    r3.button("⬅️ Slow SX", on_click=apply_slow_side_step, args=("SINISTRA",), use_container_width=True)
    r4.button("➡️ Slow DX", on_click=apply_slow_side_step, args=("DRITTA",), use_container_width=True)

# --- CALCULATIONS ---
pos_sx, pos_dx = np.array([-POS_THRUSTERS_X, POS_THRUSTERS_Y]), np.array([POS_THRUSTERS_X, POS_THRUSTERS_Y])
pp_pos = np.array([st.session_state.pp_x, st.session_state.pp_y])
ton1, ton2 = (st.session_state.p1/100)*BOLLARD_PULL_PER_ENGINE, (st.session_state.p2/100)*BOLLARD_PULL_PER_ENGINE
rad1, rad2 = np.radians(st.session_state.a1), np.radians(st.session_state.a2)
F_sx, F_dx = np.array([ton1*np.sin(rad1), ton1*np.cos(rad1)]), np.array([ton2*np.sin(rad2), ton2*np.cos(rad2)])

warning_int = check_wash_hit(pos_sx, -F_sx, pos_dx) or check_wash_hit(pos_dx, -F_dx, pos_sx)
eff = 0.8 if warning_int else 1.0
res_u, res_v = (F_sx[0]+F_dx[0])*eff, (F_sx[1]+F_dx[1])*eff
res_ton = np.sqrt(res_u**2 + res_v**2)
M_tm = ((pos_sx-pp_pos)[0]*F_sx[1] - (pos_sx-pp_pos)[1]*F_sx[0] + (pos_dx-pp_pos)[0]*F_dx[1] - (pos_dx-pp_pos)[1]*F_dx[0]) * eff
M_knm = M_tm * G_ACCEL

# --- LOGICA ORIGINE RISULTANTE CON SOGLIA 50m ---
inter = intersect_lines(pos_sx, st.session_state.a1, pos_dx, st.session_state.a2)
use_weighted = True
if inter is not None:
    dist_inter = np.linalg.norm(inter)
    if dist_inter <= 50.0: use_weighted = False

# --- LAYOUT GRAFICO ---
col_l, col_c, col_r = st.columns([1, 2, 1])
with col_l:
    st.slider("Potenza SX (%)", 0, 100, key="p1")
    st.metric("Spinta SX", f"{ton1:.1f} t")
    st.slider("Azimut SX (°)", 0, 360, key="a1")
    st.pyplot(plot_clock(st.session_state.a1, 'red'))
with col_r:
    st.slider("Potenza DX (%)", 0, 100, key="p2")
    st.metric("Spinta DX", f"{ton2:.1f} t")
    st.slider("Azimut DX (°)", 0, 360, key="a2")
    st.pyplot(plot_clock(st.session_state.a2, 'green'))

with col_c:
    with st.expander("📍 Configurazione Pivot Point", expanded=True):
        st.slider("Longitudinale (Y)", -16.0, 16.0, key="pp_y")
        st.slider("Trasversale (X)", -5.0, 5.0, key="pp_x")

    fig, ax = plt.subplots(figsize=(8, 10))
    draw_static_elements(ax, pos_sx, pos_dx)
    
    if not use_weighted:
        origin_res = inter
        ax.plot([pos_sx[0], inter[0]], [pos_sx[1], inter[1]], 'r--', lw=1, alpha=0.3)
        ax.plot([pos_dx[0], inter[0]], [pos_dx[1], inter[1]], 'g--', lw=1, alpha=0.3)
    else:
        if (ton1 + ton2) > 0.1:
            w_x = (ton1 * pos_sx[0] + ton2 * pos_dx[0]) / (ton1 + ton2)
            origin_res = np.array([w_x, POS_THRUSTERS_Y])
        else:
            origin_res = np.array([0.0, POS_THRUSTERS_Y])

    sc = 0.4
    ax.arrow(pos_sx[0], pos_sx[1], F_sx[0]*sc, F_sx[1]*sc, fc='red', ec='red', width=0.25, zorder=4)
    ax.arrow(pos_dx[0], pos_dx[1], F_dx[0]*sc, F_dx[1]*sc, fc='green', ec='green', width=0.25, zorder=4)
    ax.arrow(origin_res[0], origin_res[1], res_u*sc, res_v*sc, fc='blue', ec='blue', width=0.6, alpha=0.4, zorder=4)
    
    ax.scatter(st.session_state.pp_x, st.session_state.pp_y, c='black', s=120, zorder=10)
    if abs(M_tm) > 1:
        p_s, p_e = (5, 24) if M_tm > 0 else (-5, 24), (-5, 24) if M_tm > 0 else (5, 24)
        style = "Simple, tail_width=2, head_width=10, head_length=10"
        ax.add_patch(FancyArrowPatch(p_s, p_e, connectionstyle=f"arc3,rad={0.3 if M_tm>0 else -0.3}", arrowstyle=style, color='purple', alpha=0.8, zorder=5))

    # MODIFICA QUI: Allargata la visuale (zoom out)
    ax.set_xlim(-28, 28); ax.set_ylim(-45, 38); ax.set_aspect('equal'); ax.axis('off')
    st.pyplot(fig)

    st.markdown("### 📊 Analisi Dinamica")
    if warning_int: st.error("⚠️ THRUSTER INTERFERENCE: Spinta ridotta del 20%.")
    m1, m2, m3 = st.columns(3)
    m1.metric("Tiro Totale", f"{res_ton:.1f} t")
    m2.metric("Direzione", f"{np.degrees(np.arctan2(res_u, res_v))%360:.0f}°")
    m3.metric("Rotazione", "SINISTRA" if M_tm > 2 else "DRITTA" if M_tm < -2 else "STABILE", delta=f"{abs(M_knm):.0f} kNm", delta_color="off")
