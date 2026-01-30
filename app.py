import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, Rectangle, Circle, Arrow
from constants import *
from physics import *
from visualization import *
import time

st.set_page_config(page_title="ASD Centurion V7.8", layout="wide")

st.markdown("""
<style>
    [data-testid="stMetricValue"] {
        font-size: 1.8rem !important;
        overflow-wrap: break-word;
        white-space: normal;
    }
    /* Stile per i bottoni zoom compatti */
    div[data-testid="column"] button {
        height: auto;
        padding-top: 5px;
        padding-bottom: 5px;
    }
</style>
""", unsafe_allow_html=True)

# --- INIZIALIZZAZIONE ---
if "physics" not in st.session_state:
    st.session_state.physics = PhysicsEngine()
    st.session_state.last_time = time.time()
    st.session_state.history_x = []
    st.session_state.history_y = []
    st.session_state.update({"p1": 50, "a1": 0, "p2": 50, "a2": 0})

if "zoom_level" not in st.session_state:
    st.session_state.zoom_level = 80.0

def set_engine_state(p1, a1, p2, a2):
    st.session_state.p1, st.session_state.a1 = p1, a1
    st.session_state.p2, st.session_state.a2 = p2, a2

def reset_engines(): 
    set_engine_state(50, 0, 50, 0)
    st.session_state.physics.reset()
    st.session_state.history_x = []
    st.session_state.history_y = []

def full_reset_sim():
    st.session_state.physics.reset()
    st.session_state.history_x = []
    st.session_state.history_y = []
    st.session_state.zoom_level = 80.0

def update_zoom(delta):
    new_zoom = st.session_state.zoom_level + delta
    if new_zoom < 20: new_zoom = 20
    if new_zoom > 300: new_zoom = 300
    st.session_state.zoom_level = new_zoom

# --- SOLVER FAST SIDE STEP ---
def solve_fast_side_step(mode):
    Y_target = POS_SKEG_Y
    dy = -17.0
    dx_sx = -POS_THRUSTERS_X
    dx_dx = POS_THRUSTERS_X
    
    if mode == "DRITTA":
        p_m, a_m = 50.0, 50.0
        rad_m = np.radians(a_m)
        Fy_m = p_m * np.cos(rad_m)
        Fx_m = p_m * np.sin(rad_m)
        M_m = (dx_sx * Fy_m) - (dy * Fx_m)
        
        Fy_s = -Fy_m
        Fx_s = (M_m + dx_dx * Fy_s) / dy
        
        p_s = np.sqrt(Fx_s**2 + Fy_s**2)
        rad_s = np.arctan2(Fx_s, Fy_s)
        a_s = np.degrees(rad_s) % 360
        set_engine_state(int(p_m), int(a_m), int(p_s), int(a_s))
        
    else: # SINISTRA
        p_m, a_m = 50.0, 310.0
        rad_m = np.radians(a_m)
        Fy_m = p_m * np.cos(rad_m)
        Fx_m = p_m * np.sin(rad_m)
        M_m = (dx_dx * Fy_m) - (dy * Fx_m)
        
        Fy_s = -Fy_m
        Fx_s = (M_m + dx_sx * Fy_s) / dy
        
        p_s = np.sqrt(Fx_s**2 + Fy_s**2)
        rad_s = np.arctan2(Fx_s, Fy_s)
        a_s = np.degrees(rad_s) % 360
        set_engine_state(int(p_s), int(a_s), int(p_m), int(a_m))

def apply_slow_side_step(direction):
    if direction == "DRITTA":
        set_engine_state(50, 10, 50, 170)
    else:
        set_engine_state(50, 190, 50, 350)

def apply_turn_on_the_spot(direction):
    if direction == "DRITTA":
        set_engine_state(50, 330, 50, 210)
    else:
        set_engine_state(50, 150, 50, 30)

def check_wash_hit(origin, wash_vec, target_pos, threshold=2.0):
    wash_len = np.linalg.norm(wash_vec)
    if wash_len < 0.1: return False
    wash_dir = wash_vec / wash_len
    to_target = target_pos - origin
    proj_length = np.dot(to_target, wash_dir)
    if proj_length > 0: 
        perp_dist = np.linalg.norm(to_target - (proj_length * wash_dir))
        return perp_dist < threshold
    return False

def intersect_lines(p1, angle1_deg, p2, angle2_deg):
    th1, th2 = np.radians(90 - angle1_deg), np.radians(90 - angle2_deg)
    v1, v2 = np.array([np.cos(th1), np.sin(th1)]), np.array([np.cos(th2), np.sin(th2)])
    matrix = np.column_stack((v1, -v2))
    if abs(np.linalg.det(matrix)) < 1e-4: return None
    try:
        t = np.linalg.solve(matrix, p2 - p1)[0]
        return p1 + t * v1
    except: return None

# --- HEADER ---
st.markdown("<h1 style='text-align: center;'>⚓ ASD Centurion V7.8 ⚓</h1>", unsafe_allow_html=True)
st.markdown("""
<div style='text-align: center;'>
    <i>per info contattare stefano.bandi22@gmail.com</i>
</div>
""", unsafe_allow_html=True)
st.write("---")

with st.sidebar:
    st.header("Comandi Globali")
    
    c1, c2 = st.columns(2)
    c1.button("Reset Motori", on_click=reset_engines, type="primary", use_container_width=True)
    c2.button("Reset Sim", on_click=full_reset_sim, use_container_width=True)
    
    st.markdown("---")
    
    st.markdown("### 👁️ Visualizzazione")
    show_wash = st.checkbox("Mostra Propeller Wash", value=True)
    show_prediction = st.checkbox("Predizione Movimento (BETA)", value=False)
    
    st.markdown("**Regolazione Zoom:**")
    z1, z2, z3 = st.columns([1, 1, 2])
    z1.button("➕", on_click=update_zoom, args=(-10,), help="Zoom In", use_container_width=True)
    z2.button("➖", on_click=update_zoom, args=(10,), help="Zoom Out", use_container_width=True)
    z3.metric("Raggio", f"{int(st.session_state.zoom_level)} m", label_visibility="collapsed")
    
    # Checkbox Costruzione Vettoriale (Default False)
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
    r1.button("⬅️ Fast SX", on_click=solve_fast_side_step, args=("SINISTRA",), use_container_width=True)
    r2.button("➡️ Fast DX", on_click=solve_fast_side_step, args=("DRITTA",), use_container_width=True)
    r3, r4 = st.columns(2)
    r3.button("⬅️ Slow SX", on_click=apply_slow_side_step, args=("SINISTRA",), use_container_width=True)
    r4.button("➡️ Slow DX", on_click=apply_slow_side_step, args=("DRITTA",), use_container_width=True)
    st.markdown("---")
    st.markdown("### 🔄 Turning on the Spot")
    ts1, ts2 = st.columns(2)
    ts1.button("🔄 Ruota SX", on_click=apply_turn_on_the_spot, args=("SINISTRA",), use_container_width=True)
    ts2.button("🔄 Ruota DX", on_click=apply_turn_on_the_spot, args=("DRITTA",), use_container_width=True)

pos_sx, pos_dx = np.array([-POS_THRUSTERS_X, POS_THRUSTERS_Y]), np.array([POS_THRUSTERS_X, POS_THRUSTERS_Y])

# CALCOLI VETTORIALI
ton1_set = (st.session_state.p1/100)*BOLLARD_PULL_PER_ENGINE
ton2_set = (st.session_state.p2/100)*BOLLARD_PULL_PER_ENGINE
rad1, rad2 = np.radians(st.session_state.a1), np.radians(st.session_state.a2)

F_sx_eff_v = np.array([ton1_set*np.sin(rad1), ton1_set*np.cos(rad1)])
F_dx_eff_v = np.array([ton2_set*np.sin(rad2), ton2_set*np.cos(rad2)])

wash_sx_hits_dx = check_wash_hit(pos_sx, -F_sx_eff_v, pos_dx)
wash_dx_hits_sx = check_wash_hit(pos_dx, -F_dx_eff_v, pos_sx)
eff_sx, eff_dx = (0.8 if wash_dx_hits_sx else 1.0), (0.8 if wash_sx_hits_dx else 1.0)

F_sx_eff = F_sx_eff_v * eff_sx
F_dx_eff = F_dx_eff_v * eff_dx
ton1_eff, ton2_eff = ton1_set * eff_sx, ton2_set * eff_dx

res_u_total = (F_sx_eff[0] + F_dx_eff[0])
res_v_total = (F_sx_eff[1] + F_dx_eff[1])
res_ton = np.sqrt(res_u_total**2 + res_v_total**2)
direzione_nautica = np.degrees(np.arctan2(res_u_total, res_v_total)) % 360

inter = intersect_lines(pos_sx, st.session_state.a1, pos_dx, st.session_state.a2)
use_weighted = True
if inter is not None:
    if np.linalg.norm(inter) <= 50.0: use_weighted = False
    
origin_res = inter if not use_weighted else np.array([(ton1_eff * pos_sx[0] + ton2_eff * pos_dx[0]) / (ton1_eff + ton2_eff + 0.001), POS_THRUSTERS_Y])

# --- UPDATE FISICA ---
pp_y_auto = 0.0
if show_prediction:
    current_time = time.time()
    dt = current_time - st.session_state.last_time
    st.session_state.last_time = current_time
    if dt > 0.1: dt = 0.1

    thrust_l = (st.session_state.p1 / 100.0) * MAX_THRUST
    thrust_r = (st.session_state.p2 / 100.0) * MAX_THRUST
    st.session_state.physics.update(dt, thrust_l, st.session_state.a1, thrust_r, st.session_state.a2)
    
    state = st.session_state.physics.state
    st.session_state.history_x.append(state[0])
    st.session_state.history_y.append(state[1])
    if len(st.session_state.history_x) > 1000:
        st.session_state.history_x.pop(0)
        st.session_state.history_y.pop(0)
    pp_y_auto = st.session_state.physics.current_pp_y
else:
    st.session_state.physics.reset()
    st.session_state.last_time = time.time() 
    thrust_l = (st.session_state.p1 / 100.0) * MAX_THRUST
    thrust_r = (st.session_state.p2 / 100.0) * MAX_THRUST
    pp_y_auto = st.session_state.physics.calculate_dynamic_pivot(thrust_l, st.session_state.a1, thrust_r, st.session_state.a2)

# --- LAYOUT GUI ---
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
    with st.expander("📍 Pivot Point (Auto Logic V7.6)", expanded=True):
        st.metric("Posizione PP (Auto)", f"Y = {pp_y_auto:.2f} m")
    
    if wash_dx_hits_sx:
        st.error("⚠️ ATTENZIONE: Flusso DX investe SX -> Perdita 20% spinta SX")
    if wash_sx_hits_dx:
        st.error("⚠️ ATTENZIONE: Flusso SX investe DX -> Perdita 20% spinta DX")

    fig, ax = plt.subplots(figsize=(10, 12))
    ax.set_facecolor(COLOR_SEA) 
    
    # Wash 
    if show_wash:
        draw_wash(ax, pos_sx, st.session_state.a1, st.session_state.p1)
        draw_wash(ax, pos_dx, st.session_state.a2, st.session_state.p2)
    
    # Nave e Scafo
