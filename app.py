# app.py
import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch
from constants import *
from physics import *
from visualization import *

st.set_page_config(page_title="ASD Centurion V5.25", layout="wide")

# --- GESTIONE SESSION STATE ---
if "p1" not in st.session_state:
    st.session_state.update({"p1": 50, "a1": 0, "p2": 50, "a2": 0, "pp_x": 0.0, "pp_y": 5.42})

def set_engine_state(p1, a1, p2, a2):
    st.session_state.p1, st.session_state.a1 = p1, a1
    st.session_state.p2, st.session_state.a2 = p2, a2

def reset_engines(): set_engine_state(50, 0, 50, 0)
def reset_pivot(): st.session_state.pp_x, st.session_state.pp_y = 0.0, 5.42

# --- HEADER ---
st.markdown("<h1 style='text-align: center;'>⚓ Rimorchiatore ASD 'CENTURION'</h1>", unsafe_allow_html=True)
st.markdown("""
<div style='text-align: center;'>
    <p style='font-size: 18px; margin-bottom: 10px;'>Per informazioni contattare stefano.bandi22@gmail.com</p>
    <b>Dimensioni:</b> 32.50 m x 11.70 m | <b>Bollard Pull:</b> 70 ton | <b>Logica:</b> Intersezione Vettoriale
</div>
""", unsafe_allow_html=True)
st.write("---")

# --- SIDEBAR ---
with st.sidebar:
    st.header("Comandi Globali")
    col_res1, col_res2 = st.columns(2)
    with col_res1: st.button("Reset Motori", on_click=reset_engines, type="primary", use_container_width=True)
    with col_res2: st.button("Reset Pivot", on_click=reset_pivot, use_container_width=True)
    
    st.markdown("### ↕️ Longitudinali")
    c_f1, c_f2 = st.columns(2)
    with c_f1: st.button("Tutta AVANTI", on_click=set_engine_state, args=(100, 0, 100, 0), use_container_width=True)
    with c_f2: st.button("Mezza AVANTI", on_click=set_engine_state, args=(50, 0, 50, 0), use_container_width=True)
    
    st.markdown("### ↔️ Side Step")
    r1, r2 = st.columns(2)
    with r1: st.button("⬅️ Fast SX", on_click=apply_fast_side_step, args=("SINISTRA",), use_container_width=True)
    with r2: st.button("➡️ Fast DX", on_click=apply_fast_side_step, args=("DRITTA",), use_container_width=True)

# --- CALCOLI ---
pos_sx = np.array([-POS_THRUSTERS_X, POS_THRUSTERS_Y])
pos_dx = np.array([POS_THRUSTERS_X, POS_THRUSTERS_Y])
pp_pos = np.array([st.session_state.pp_x, st.session_state.pp_y])

ton1 = (st.session_state.p1 / 100) * BOLLARD_PULL_PER_ENGINE
ton2 = (st.session_state.p2 / 100) * BOLLARD_PULL_PER_ENGINE
rad1, rad2 = np.radians(st.session_state.a1), np.radians(st.session_state.a2)

u1, v1 = ton1 * np.sin(rad1), ton1 * np.cos(rad1)
u2, v2 = ton2 * np.sin(rad2), ton2 * np.cos(rad2)
F_sx, F_dx = np.array([u1, v1]), np.array([u2, v2])

eff = 0.8 if check_wash_hit(pos_sx, -F_sx, pos_dx) or check_wash_hit(pos_dx, -F_dx, pos_sx) else 1.0
res_u, res_v = (u1 + u2) * eff, (v1 + v2) * eff
res_ton = np.sqrt(res_u**2 + res_v**2)

M_tot = ((pos_sx-pp_pos)[0]*F_sx[1] - (pos_sx-pp_pos)[1]*F_sx[0] + (pos_dx-pp_pos)[0]*F_dx[1] - (pos_dx-pp_pos)[1]*F_dx[0]) * eff

# --- UI LAYOUT ---
col_sx, col_main, col_dx = st.columns([1, 2, 1])

with col_sx:
    st.slider("Potenza SX (%)", 0, 100, key="p1")
    st.slider("Azimut SX (°)", 0, 360, key="a1")
    st.pyplot(plot_clock(st.session_state.a1, 'red'))

with col_dx:
    st.slider("Potenza DX (%)", 0, 100, key="p2")
    st.slider("Azimut DX (°)", 0, 360, key="a2")
    st.pyplot(plot_clock(st.session_state.a2, 'green'))

with col_main:
    with st.expander("📍 Pivot Point"):
        st.slider("Y", -16.0, 16.0, key="pp_y")
        st.slider("X", -5.0, 5.0, key="pp_x")

    fig, ax = plt.subplots(figsize=(8, 10))
    draw_tug_hull(ax)
    
    # Visualizzazione Vettori
    scale = 0.4
    ax.arrow(pos_sx[0], pos_sx[1], u1*scale, v1*scale, color='red', width=0.25)
    ax.arrow(pos_dx[0], pos_dx[1], u2*scale, v2*scale, color='green', width=0.25)
    
    # Risultante
    inter = intersect_lines(pos_sx, st.session_state.a1, pos_dx, st.session_state.a2)
    origin_res = inter if inter is not None else np.array([0, -12])
    ax.arrow(origin_res[0], origin_res[1], res_u*scale, res_v*scale, color='blue', width=0.6, alpha=0.4)
    
    # PP e Rotazione
    ax.scatter(st.session_state.pp_x, st.session_state.pp_y, c='black', s=120)
    if abs(M_tot) > 1:
        p_s = (5, 24) if M_tot > 0 else (-5, 24)
        p_e = (-5, 24) if M_tot > 0 else (5, 24)
        ax.add_patch(FancyArrowPatch(p_s, p_e, connectionstyle="arc3,rad=0.3", arrowstyle="Simple", color='purple'))

    ax.set_xlim(-20, 20); ax.set_ylim(-25, 30); ax.axis('off')
    st.pyplot(fig)

    # Dashboard
    m1, m2, m3 = st.columns(3)
    m1.metric("Tiro Totale", f"{res_ton:.1f} t")
    m2.metric("Direzione", f"{np.degrees(np.arctan2(res_u, res_v))%360:.0f}°")
    m3.metric("Rotazione", "SINISTRA" if M_tot > 2 else "DRITTA" if M_tot < -2 else "STABILE")
