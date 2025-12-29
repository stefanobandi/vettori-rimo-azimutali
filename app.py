import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch
from constants import *
from physics import *
from visualization import *

st.set_page_config(page_title="ASD Centurion V6.0", layout="wide")

st.markdown("""
<style>
    [data-testid="stMetricValue"] {
        font-size: 1.8rem !important;
        overflow-wrap: break-word;
        white-space: normal;
    }
    @media (max-width: 640px) {
        [data-testid="stMetricValue"] { font-size: 1.2rem !important; }
        [data-testid="stMetricLabel"] { font-size: 0.8rem !important; }
    }
</style>
""", unsafe_allow_html=True)

if "p1" not in st.session_state:
    st.session_state.update({"p1": 50, "a1": 0, "p2": 50, "a2": 0, "pp_x": 0.0, "pp_y": 5.30})

def set_engine_state(p1, a1, p2, a2):
    st.session_state.p1, st.session_state.a1 = p1, a1
    st.session_state.p2, st.session_state.a2 = p2, a2

def reset_engines(): set_engine_state(50, 0, 50, 0)
def reset_pivot(): st.session_state.pp_x, st.session_state.pp_y = 0.0, 5.30

st.markdown("<h1 style='text-align: center;'>⚓ Rimorchiatore ASD 'CENTURION' ⚓</h1>", unsafe_allow_html=True)
st.markdown(f"""
<div style='text-align: center;'>
    <p style='font-size: 14px; margin-bottom: 5px;'>Per informazioni contattare stefano.bandi22@gmail.com</p>
    <b>Dimensioni:</b> 32.50 m x 11.70 m | <b>Bollard Pull:</b> 70 ton | <b>Fisica:</b> Modello A (Pivot) & B (Poppa)
</div>
""", unsafe_allow_html=True)
st.write("---")

with st.sidebar:
    st.header("Comandi Globali")
    c1, c2 = st.columns(2)
    c1.button("Reset Motori", on_click=reset_engines, type="primary", use_container_width=True)
    c2.button("Reset Target PP", on_click=reset_pivot, use_container_width=True)
    st.markdown("---")
    show_wash = st.checkbox("Visualizza Scia (Wash)", value=True)
    show_prediction = st.checkbox("Predizione Movimento (30s)", value=True)
    show_construction = st.checkbox("Costruzione Vettoriale", value=False)
    st.markdown("---")
    st.markdown("### ↕️ Longitudinali")
    cf1, cf2 = st.columns(2)
    cf1.button("⬆️ Tutta AVANTI", on_click=set_engine_state, args=(100,0,100,0), use_container_width=True)
    cf2.button("🔼 Mezza AVANTI", on_click=set_engine_state, args=(50,0,50,0), use_container_width=True)
    ca1, ca2 = st.columns(2)
    ca1.button("⬇️ Tutta INDIETRO", on_click=set_engine_state, args=(100,180,100,180), use_container_width=True)
    ca2.button("🔽 Mezza INDIETRO", on_click=set_engine_state, args=(50,180,50,180), use_container_width=True)
    st.markdown("---")
    st.markdown("### ↔️ Side Step")
    r1, r2 = st.columns(2)
    r1.button("⬅️ Fast SX", on_click=apply_fast_side_step, args=("SINISTRA",), use_container_width=True)
    r2.button("➡️ Fast DX", on_click=apply_fast_side_step, args=("DRITTA",), use_container_width=True)
    r3, r4 = st.columns(2)
    r3.button("⬅️ Slow SX", on_click=apply_slow_side_step, args=("SINISTRA",), use_container_width=True)
    r4.button("➡️ Slow DX", on_click=apply_slow_side_step, args=("DRITTA",), use_container_width=True)
    st.markdown("---")
    st.markdown("### 🔄 Turning on the Spot")
    ts1, ts2 = st.columns(2)
    ts1.button("🔄 Ruota SX", on_click=apply_turn_on_the_spot, args=("SINISTRA",), use_container_width=True)
    ts2.button("🔄 Ruota DX", on_click=apply_turn_on_the_spot, args=("DRITTA",), use_container_width=True)

pos_sx, pos_dx = np.array([-POS_THRUSTERS_X, POS_THRUSTERS_Y]), np.array([POS_THRUSTERS_X, POS_THRUSTERS_Y])
pp_pos = np.array([st.session_state.pp_x, st.session_state.pp_y])
cg_pos = np.array([0.0, 0.0]) 

ton1_set = (st.session_state.p1/100)*BOLLARD_PULL_PER_ENGINE
ton2_set = (st.session_state.p2/100)*BOLLARD_PULL_PER_ENGINE
rad1, rad2 = np.radians(st.session_state.a1), np.radians(st.session_state.a2)

# Vettori forza teorici
F_sx_eff_v = np.array([ton1_set*np.sin(rad1), ton1_set*np.cos(rad1)])
F_dx_eff_v = np.array([ton2_set*np.sin(rad2), ton2_set*np.cos(rad2)])

# Calcolo intersezioni scia (Wash Hit)
wash_sx_hits_dx = check_wash_hit(pos_sx, -F_sx_eff_v, pos_dx)
wash_dx_hits_sx = check_wash_hit(pos_dx, -F_dx_eff_v, pos_sx)
eff_sx, eff_dx = (0.8 if wash_dx_hits_sx else 1.0), (0.8 if wash_sx_hits_dx else 1.0)

# Vettori forza effettivi (con penalità)
F_sx_eff = F_sx_eff_v * eff_sx
F_dx_eff = F_dx_eff_v * eff_dx
ton1_eff, ton2_eff = ton1_set * eff_sx, ton2_set * eff_dx

# Risultanti globali (solo per display telemetria)
res_u, res_v = (F_sx_eff[0] + F_dx_eff[0]), (F_sx_eff[1] + F_dx_eff[1])
res_ton = np.sqrt(res_u**2 + res_v**2)
direzione_nautica = np.degrees(np.arctan2(res_u, res_v)) % 360
M_tm_CG = ((pos_sx-cg_pos)[0]*F_sx_eff[1] - (pos_sx-cg_pos)[1]*F_sx_eff[0] + 
           (pos_dx-cg_pos)[0]*F_dx_eff[1] - (pos_dx-cg_pos)[1]*F_dx_eff[0])
M_knm = M_tm_CG * G_ACCEL

# Calcolo intersezione vettori
inter = intersect_lines(pos_sx, st.session_state.a1, pos_dx, st.session_state.a2)
use_weighted = True
if inter is not None:
    if np.linalg.norm(inter) <= 50.0: use_weighted = False

# --- LAYOUT PRINCIPALE ---
col_l, col_c, col_r = st.columns([1.2, 2.6, 1.2])

with col_l:
    st.slider("Potenza SX", 0, 100, key="p1", format="%d%%")
    st.metric("Spinta SX", f"{ton1_eff:.1f} t")
    st.slider("Azimuth SX", 0, 360, key="a1", format="%03d°")
    st.pyplot(plot_clock(st.session_state.a1, 'red'))
    
with col_r:
    st.slider("Potenza DX", 0, 100, key="p2", format="%d%%")
    st.metric("Spinta DX", f"{ton2_eff:.1f} t")
    st.slider("Azimuth DX", 0, 360, key="a2", format="%03d°")
    st.pyplot(plot_clock(st.session_state.a2, 'green'))

with col_c:
    with st.expander("📍 Target Pivot Point (Visual & Auto)", expanded=True):
        pcol1, pcol2 = st.columns(2)
        pcol1.slider("Longitudinale (Y)", -16.0, 16.0, key="pp_y", format="%.2fm")
        pcol2.slider("Laterale (X)", -5.0, 5.0, key="pp_x", format="%.2fm")
    
    if wash_dx_hits_sx:
        st.error("⚠️ ATTENZIONE: Flusso DX investe SX -> Perdita 20% spinta SX")
    if wash_sx_hits_dx:
        st.error("⚠️ ATTENZIONE: Flusso SX investe DX -> Perdita 20% spinta DX")

    fig, ax = plt.subplots(figsize=(10, 12))
    
    # --- PREDIZIONE CON NUOVA LOGICA A-B ---
    traj = []
    if show_prediction:
        # Passiamo le forze singole e le posizioni per calcolare le leve A-B internamente
        traj = predict_trajectory(F_sx_eff, F_dx_eff, pos_sx, pos_dx, st.session_state.pp_y, total_time=30.0)
        for idx, (tx, ty, th) in enumerate(traj):
            alpha = (idx + 1) / (len(traj) + 5) * 0.4
            draw_hull_silhouette(ax, tx, ty, th, alpha=alpha)
            
    draw_static_elements(ax, pos_sx, pos_dx)
    
    if show_wash:
        draw_wash(ax, pos_sx, st.session_state.a1, st.session_state.p1)
        draw_wash(ax, pos_dx, st.session_state.a2, st.session_state.p2)
        
    draw_propeller(ax, pos_sx, st.session_state.a1, color='red')
    draw_propeller(ax, pos_dx, st.session_state.a2, color='green')

    # --- VISUALIZZAZIONE E ZOOM DINAMICO "SQUARE BOX" ---
    ax.set_aspect('equal')
    
    # 1. Raccolta punti d'interesse per il bounding box
    all_x = [-10, 10] # Larghezza minima di base
    all_y = [-20, 20] # Altezza minima di base
    
    # Aggiungi posizioni scafo statico
    all_x.extend([pos_sx[0], pos_dx[0]])
    all_y.extend([pos_sx[1], pos_dx[1]])
    
    # Aggiungi punti della predizione se attiva
    if show_prediction and len(traj) > 0:
        path_x = [t[0] for t in traj]
        path_y = [t[1] for t in traj]
        all_x.extend(path_x)
        all_y.extend(path_y)
    
    # 2. Calcolo Box
    min_x, max_x = min(all_x), max(all_x)
    min_y, max_y = min(all_y), max(all_y)
    
    center_x = (min_x + max_x) / 2
    center_y = (min_y + max_y) / 2
    
    width = max_x - min_x
    height = max_y - min_y
    
    # 3. Logica "Square Box"
    # Trova la dimensione maggiore e aggiungi un margine
    max_dim = max(width, height)
    margin = max_dim * 0.15 # 15% di margine
    span = (max_dim / 2) + margin
    
    # Imposta limiti centrati e quadrati
    ax.set_xlim(center_x - span, center_x + span)
    ax.set_ylim(center_y - span, center_y + span)
    
    # Griglia e assi
    ax.grid(True, linestyle=':', alpha=0.6)
    ax.set_axisbelow(True)
    
    # Rendering finale
    st.pyplot(fig)
