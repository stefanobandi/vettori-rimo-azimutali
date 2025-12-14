import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import PathPatch, FancyArrowPatch
from matplotlib.path import Path
import pandas as pd

# --- CONFIGURAZIONE PAGINA ---
st.set_page_config(page_title="ASD Centurion V5.4", layout="wide")

# --- GESTIONE SESSION STATE ---
defaults = {
    "p1": 50.0, "a1": 0.0,    # Motore SX
    "p2": 50.0, "a2": 0.0,    # Motore DX
    "pp_x": 0.0, "pp_y": 5.42 # Pivot Point default
}

for key, val in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = val

# --- FUNZIONI DI CALLBACK PER LA SINCRONIZZAZIONE ---
def update_from_slider(key):
    st.session_state[key] = st.session_state[f"{key}_slider"]

def update_from_input(key):
    st.session_state[key] = st.session_state[f"{key}_input"]

# --- FUNZIONI DI RESET SEPARATE ---
def reset_engines():
    st.session_state.p1 = 50.0
    st.session_state.a1 = 0.0
    st.session_state.p2 = 50.0
    st.session_state.a2 = 0.0
    # Aggiorna i widget se esistono nello state
    if 'p1_slider' in st.session_state: st.session_state.p1_slider = 50.0
    if 'p1_input' in st.session_state: st.session_state.p1_input = 50.0
    if 'p2_slider' in st.session_state: st.session_state.p2_slider = 50.0
    if 'p2_input' in st.session_state: st.session_state.p2_input = 50.0
    # Azimut non serve resettarlo a 0 forzatamente nei widget se lo state è aggiornato

def reset_pivot():
    st.session_state.pp_x = 0.0
    st.session_state.pp_y = 5.42
    if 'pp_x_slider' in st.session_state: st.session_state.pp_x_slider = 0.0
    if 'pp_x_input' in st.session_state: st.session_state.pp_x_input = 0.0
    if 'pp_y_slider' in st.session_state: st.session_state.pp_y_slider = 5.42
    if 'pp_y_input' in st.session_state: st.session_state.pp_y_input = 5.42

# --- COMPONENTE GRAFICO CUSTOM: SLIDER + INPUT ---
def render_control(label, key, min_val, max_val, step=1.0):
    c1, c2 = st.columns([3, 1])
    with c1:
        st.slider(
            label, 
            min_value=float(min_val), 
            max_value=float(max_val), 
            step=step,
            key=f"{key}_slider", 
            value=float(st.session_state[key]),
            on_change=update_from_slider,
            args=(key,)
        )
    with c2:
        st.number_input(
            "Valore", 
            min_value=float(min_val), 
            max_value=float(max_val), 
            step=step,
            key=f"{key}_input", 
            value=float(st.session_state[key]),
            on_change=update_from_input,
            args=(key,),
            label_visibility="hidden"
        )

# --- HEADER ---
st.markdown("<h1 style='text-align: center;'>⚓ Rimorchiatore ASD 'CENTURION' V5.4</h1>", unsafe_allow_html=True)

# --- SIDEBAR: RESET E PRESET ---
with st.sidebar:
    st.header("⚙️ Controlli Sistema")
    
    st.subheader("Reset")
    c_res1, c_res2 = st.columns(2)
    with c_res1:
        st.button("M. Motori", on_click=reset_engines, type="primary", use_container_width=True)
    with c_res2:
        st.button("P. Pivot", on_click=reset_pivot, use_container_width=True)
    
    st.info("Usa i tasti sopra per resettare separatamente i propulsori o il Pivot Point.")
    
    st.divider()
    st.markdown("### Manovre Rapide")
    if st.button("Avanti Tutta", use_container_width=True):
        st.session_state.p1 = 80.0; st.session_state.a1 = 0.0
        st.session_state.p2 = 80.0; st.session_state.a2 = 0.0
        st.rerun()

    if st.button("Crabbing DX", use_container_width=True):
        st.session_state.p1 = 60.0; st.session_state.a1 = 90.0
        st.session_state.p2 = 60.0; st.session_state.a2 = 90.0
        st.rerun()

    if st.button("Rotazione Oraria", use_container_width=True):
        st.session_state.p1 = 50.0; st.session_state.a1 = 0.0
        st.session_state.p2 = 50.0; st.session_state.a2 = 180.0
        st.rerun()

# --- CALCOLI FISICI ---
pos_sx = np.array([-2.7, -12.0])
pos_dx = np.array([2.7, -12.0])
pp_pos = np.array([st.session_state.pp_x, st.session_state.pp_y])

# Calcolo Tonnellate
ton1 = (st.session_state.p1 / 100) * 35
ton2 = (st.session_state.p2 / 100) * 35

rad1, rad2 = np.radians(st.session_state.a1), np.radians(st.session_state.a2)
u1, v1 = ton1 * np.sin(rad1), ton1 * np.cos(rad1)
u2, v2 = ton2 * np.sin(rad2), ton2 * np.cos(rad2)

F_sx = np.array([u1, v1])
F_dx = np.array([u2, v2])

res_u = u1 + u2
res_v = v1 + v2
res_ton = np.sqrt(res_u**2 + res_v**2)

# Momento
r_sx = pos_sx - pp_pos
r_dx = pos_dx - pp_pos
M_sx = r_sx[0] * F_sx[1] - r_sx[1] * F_sx[0]
M_dx = r_dx[0] * F_dx[1] - r_dx[1] * F_dx[0]
Total_Moment = M_sx + M_dx

# Punto Applicazione
def intersect_lines(p1, angle1_deg, p2, angle2_deg):
    th1 = np.radians(90 - angle1_deg)
    th2 = np.radians(90 - angle2_deg)
    dir1 = np.array([np.cos(th1), np.sin(th1)])
    dir2 = np.array([np.cos(th2), np.sin(th2)])
    matrix = np.column_stack((dir1, -dir2))
    delta = p2 - p1
    if abs(np.linalg.det(matrix)) < 1e-3: return None
    t = np.linalg.solve(matrix, delta)[0]
    return p1 + t * dir1

intersection = None
if ton1 > 0.1 and ton2 > 0.1:
    intersection = intersect_lines(pos_sx, st.session_state.a1, pos_dx, st.session_state.a2)

origin_res = np.array([0.0, -12.0])
logic_used = "Centro"

if intersection is not None and np.linalg.norm(intersection - np.array([0, -12])) < 60:
    origin_res = intersection
    logic_used = "Intersezione"
elif ton1 + ton2 > 0.1:
    w_x = (ton1 * pos_sx[0] + ton2 * pos_dx[0]) / (ton1 + ton2)
    origin_res = np.array([w_x, -12.0])

# --- LAYOUT PLANCIA ---
col_sx, col_center, col_dx = st.columns(
