import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import PathPatch, FancyArrowPatch
from matplotlib.path import Path
import pandas as pd

# --- CONFIGURAZIONE PAGINA ---
st.set_page_config(page_title="ASD Centurion V5.4", layout="wide")

# --- GESTIONE SESSION STATE ---
# Definiamo i valori di default
defaults = {
    "p1": 50.0, "a1": 0.0,    # Motore SX
    "p2": 50.0, "a2": 0.0,    # Motore DX
    "pp_x": 0.0, "pp_y": 5.42 # Pivot Point default
}

# Inizializzazione State
for key, val in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = val

# --- FUNZIONI DI CALLBACK PER LA SINCRONIZZAZIONE ---
# Queste funzioni servono a tenere allineati slider e casella di testo
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
    # Forziamo l'aggiornamento dei widget 'figli' se esistono
    if 'p1_slider' in st.session_state: st.session_state.p1_slider = 50.0
    if 'p1_input' in st.session_state: st.session_state.p1_input = 50.0
    # (Ripetere per gli altri se necessario, ma Streamlit gestisce il binding al rerun)

def reset_pivot():
    st.session_state.pp_x = 0.0
    st.session_state.pp_y = 5.42

# --- COMPONENTE GRAFICO CUSTOM: SLIDER + INPUT ---
def render_control(label, key, min_val, max_val, step=1.0, help_txt=None):
    """Crea una riga con Slider e Number Input sincronizzati"""
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
            args=(key,),
            help=help_txt
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
            label_visibility="hidden" # Nasconde l'etichetta ridondante
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
    # Definiamo i preset direttamente qui con lambda o funzioni locali
    if st.button("Avanti Tutta", use_container_width=True):
        st.session_state.p1, st.session_state.a1 = 80.0, 0.0
        st.session_state.p2, st.session_state.a2 = 80.0, 0.0
    if st.button("Crabbing DX", use_container_width=True):
        st.session_state.p1, st.session_state.a1 = 60.0, 90.0
        st.session_state.p2, st.session_state.a2 = 60.0, 90.0
    if st.button("Rotazione Oraria", use_container_width=True):
        st.session_state.p1, st.session_state.a1 = 50.0, 0.0
        st.session_state.p2, st.session_state.a2 = 50.0, 180.0

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
col_sx, col_center, col_dx = st.columns([1, 2.2, 1], gap="small")

# Helper per orologi
def plot_azimuth_clock(angle, color):
    fig, ax = plt.subplots(figsize=(2, 2), subplot_kw={'projection': 'polar'})
    ax.set_theta_zero_location('N')
    ax.set_theta_direction(-1)
    ax.set_yticks([])
    ax.set_xticks(np.radians([0, 90, 180, 270]))
    ax.set_xticklabels([])
    ax.spines['polar'].set_visible(False)
    ax.grid(True, alpha=0.2)
    ax.arrow(np.radians(angle), 0, 0, 0.9, color=color, width=0.18, head_width=0, length_includes_head=True)
    fig.patch.set_alpha(0)
    return fig

# === COLONNA SX ===
with col_sx:
    st.markdown("<h4 style='text-align: center; color: #d32f2f;'>PORT (SX)</h4>", unsafe_allow_html=True)
    render_control("Potenza %", "p1", 0, 100, 1.0)
    render_control("Azimut °", "a1", 0, 360, 1.0)
    st.pyplot(plot_azimuth_clock(st.session_state.a1, '#d32f2f'), use_container_width=False)
    st.metric("Spinta SX", f"{ton1:.1f} t")

# === COLONNA DX ===
with col_dx:
    st.markdown("<h4 style='text-align: center; color: #388e3c;'>STBD (DX)</h4>", unsafe_allow_html=True)
    render_control("Potenza %", "p2", 0, 100, 1.0)
    render_control("Azimut °", "a2", 0, 360, 1.0)
    st.pyplot(plot_azimuth_clock(st.session_state.a2, '#388e3c'), use_container_width=False)
    st.metric("Spinta DX", f"{ton2:.1f} t")

# === COLONNA CENTRALE ===
with col_center:
    # 1. Grafico
    fig, ax = plt.subplots(figsize=(6, 8))
    
    # Scafo
    hw = 5.85; stern = -16.25; bow = 16.25; shld = 5.0
    verts = [(-hw, stern), (hw, stern), (hw, shld), (0, bow), (-hw, shld), (-hw, stern)]
    codes = [Path.MOVETO, Path.LINETO, Path.LINETO, Path.CURVE3, Path.CURVE3, Path.LINETO]
    patch = PathPatch(Path(verts, codes), facecolor='#ececec', edgecolor='#333', lw=2, zorder=1)
    ax.add_patch(patch)
    
    # Pivot Point
    ax.plot(st.session_state.pp_x, st.session_state.pp_y, 'ko', markersize=8, zorder=10)
    ax.text(st.session_state.pp_x + 1, st.session_state.pp_y, "PP", fontsize=10, fontweight='bold')

    # Vettori
    scale = 0.35
    ax.arrow(pos_sx[0], pos_sx[1], u1*scale, v1*scale, head_width=1.5, fc='#d32f2f', ec='#d32f2f', alpha=0.7, zorder=5)
    ax.arrow(pos_dx[0], pos_dx[1], u2*scale, v2*scale, head_width=1.5, fc='#388e3c', ec='#388e3c', alpha=0.7, zorder=5)

    if res_ton > 0.1:
        ax.scatter(origin_res[0], origin_res[1], c='blue', marker='x', s=50, zorder=6)
        ax.arrow(origin_res[0], origin_res[1], res_u*scale, res_v*scale, head_width=2.5, fc='blue', ec='blue', alpha=0.4, zorder=4)
        if logic_used
