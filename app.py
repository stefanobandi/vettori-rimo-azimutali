# app.py
import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch
from constants import *
from physics import *
from visualization import *

st.set_page_config(page_title="ASD Centurion V5.25", layout="wide")

# CSS Injection per evitare il troncamento del testo nelle metriche su mobile
st.markdown("""
<style>
    [data-testid="stMetricValue"] {
        font-size: 1.8rem !important;
        overflow-wrap: break-word;
        white-space: normal;
    }
    @media (max-width: 640px) {
        [data-testid="stMetricValue"] {
            font-size: 1.2rem !important;
        }
        [data-testid="stMetricLabel"] {
            font-size: 0.8rem !important;
        }
    }
</style>
""", unsafe_allow_html=True)

if "p1" not in st.session_state:
    st.session_state.update({"p1": 50, "a1": 0, "p2": 50, "a2": 0, "pp_x": 0.0, "pp_y": 5.42})

def set_engine_state(p1, a1, p2, a2):
    st.session_state.p1, st.session_state.a1 = p1, a1
    st.session_state.p2, st.session_state.a2 = p2, a2

def reset_engines(): set_engine_state(50, 0, 50, 0)
def reset_pivot(): st.session_state.pp_x, st.session_state.pp_y = 0.0, 5.42

st.markdown("<h1 style='text-align: center;'>⚓ Rimorchiatore ASD 'CENTURION'</h1>", unsafe_allow_html=True)
st.markdown(f"""
<div style='text-align: center;'>
    <p style='font-size: 14px; margin-bottom: 5px;'>Per informazioni contattare stefano.bandi22@gmail.com</p>
    <b>Bollard Pull:</b> 70 ton | <b>Logica:</b> Ibrida
</div>
""", unsafe_allow_html=True)
st.write("---")

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

pos_sx, pos_dx = np.array([-POS_THRUSTERS_X, POS_THRUSTERS_Y]), np.array([POS_THRUSTERS_X, POS_THRUSTERS_Y])
pp_pos = np.array([st.session_state.pp_x, st.session_state.pp_y])

ton1_set = (st.session_state.p1/100)*BOLLARD_PULL_PER_ENGINE
ton2_set = (st.session_state.p2/100)*BOLLARD_PULL_PER_ENGINE
rad1, rad2 = np.radians(st.session_state.a1), np.radians(st.session_state.a2)
F_sx_set = np.array([ton1_set*np.sin(rad1), ton1_set*np.cos(rad1)])
F_dx_set = np.array([ton2_set*np.sin(rad2), ton2_set*np.cos(rad2)])

wash_sx_hits_dx = check_wash_hit(pos_sx, -F_sx_set, pos_dx)
wash_dx_hits_sx = check_wash_hit(pos_dx, -F_dx_set, pos_sx)

eff_sx = 0.8 if wash_dx_hits_sx else 1.0
eff_dx = 0.8 if wash_sx_hits_dx else 1.0

F_sx_eff = F_sx_set * eff_sx
F_dx_eff = F_dx_set * eff_dx
ton1_eff = ton1_set * eff_sx
ton2_eff = ton2_set * eff_dx

res_u, res_v = (F_sx_eff[0] + F_dx_eff[0]), (F_sx_eff[1] + F_dx_eff[1])
res_ton = np.sqrt(res_u**2 + res_v**2)
direzione_nautica = np.degrees(np.arctan2(res_u, res_v)) % 360

M_tm = ((pos_sx-pp_pos)[0]*F_sx_eff[1] - (pos_sx-pp_pos)[1]*F_sx_eff[0] + 
        (pos_dx-pp_pos)[0]*F_dx_eff[1] - (pos_dx-pp_pos)[1]*F_dx[0])
M_knm = M_tm * G_ACCEL

inter = intersect_lines(pos_sx, st.session_state.a1, pos_dx, st.session_state.a2)
use_weighted = True
if inter is not None:
    if np.linalg.norm(inter) <= 50.0: use_weighted = False

col_l, col_c, col_r = st.columns([1, 2, 1])
with col_l:
    st.slider("Potenza SX (%)", 0, 100, key="p1")
    st.metric("Spinta SX", f"{ton1_eff:.1f} t")
    st.slider("Azimut SX (°)", 0, 360, key="a1")
    st.pyplot(plot_clock(st.session_state.a1, 'red'))
with col_r:
    st.slider("Potenza DX (%)", 0, 100, key="p2")
    st.metric("Spinta DX", f"{ton2_eff:.1f} t")
    st.slider("Azimut DX (°)", 0, 360, key="a2")
    st.pyplot(plot_clock(st.session_state.a2, 'green'))

with col_c:
    with st.expander("📍 Pivot Point", expanded=True):
        st.slider("Long. (Y)", -16.0, 16.0, key="pp_y")
    fig, ax = plt.subplots(figsize=(8, 10))
    draw_static_elements(ax, pos_sx, pos_dx)
    draw_propeller(ax, pos_sx, st.session_state.a1, color='red')
    draw_propeller(ax, pos_dx, st.session_state.a2, color='green')
    
    if not use_weighted:
        origin_res = inter
        ax.plot([pos_sx[0], inter[0]], [pos_sx[1], inter[1]], 'r--', lw=1, alpha=0.3)
        ax.plot([pos_dx[0], inter[0]], [pos_dx[1], inter[1]], 'g--', lw=1, alpha=0.3)
    else:
        spinta_totale = (ton1_eff + ton2_eff)
        w_x = (ton1_eff * pos_sx[0] + ton2_eff * pos_dx[0]) / spinta_totale if spinta_totale > 0.1 else 0.0
        origin_res = np.array([w_x, POS_THRUSTERS_Y])

    sc = 0.4
    ax.arrow(pos_sx[0], pos_sx[1], F_sx_eff[0]*sc, F_sx_eff[1]*sc, fc='red', ec='red', width=0.25, zorder=4)
    ax.arrow(pos_dx[0], pos_dx[1], F_dx_eff[0]*sc, F_dx_eff[1]*sc, fc='green', ec='green', width=0.25, zorder=4)
    ax.arrow(origin_res[0], origin_res[1], res_u*sc, res_v*sc, fc='blue', ec='blue', width=0.6, alpha=0.4, zorder=4)
    ax.scatter(st.session_state.pp_x, st.session_state.pp_y, c='black', s=120, zorder=10)
    if abs(M_tm) > 1:
        p_s, p_e = (5, 24) if M_tm > 0 else (-5, 24), (-5, 24) if M_tm > 0 else (5, 24)
        ax.add_patch(FancyArrowPatch(p_s, p_e, connectionstyle=f"arc3,rad={0.3 if M_tm>0 else -0.3}", arrowstyle="Simple, tail_width=2, head_width=10, head_length=10", color='purple', alpha=0.8, zorder=5))

    ax.set_xlim(-28, 28); ax.set_ylim(-45, 38); ax.set_aspect('equal'); ax.axis('off')
    st.pyplot(fig)
    st.markdown("### 📊 Analisi Dinamica")
    
    if wash_sx_hits_dx: st.error("⚠️ DX in scia SX (-20%)")
    if wash_dx_hits_sx: st.error("⚠️ SX in scia DX (-20%)")
    
    m1, m2, m3 = st.columns(3)
    m1.metric("Tiro Tot.", f"{res_ton:.1f} t")
    m2.metric("Dir.", f"{direzione_nautica:.0f}°")
    
    # Valore di rotazione abbreviato per sicurezza mobile
    rot_val = "SINISTRA" if M_tm > 2 else "DRITTA" if M_tm < -2 else "STABILE"
    m3.metric("Rotazione", rot_val, delta=f"{abs(M_tm):.1f} tm", delta_color="off")
