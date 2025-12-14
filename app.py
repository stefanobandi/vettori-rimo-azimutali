import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import PathPatch, FancyArrowPatch
from matplotlib.path import Path
import pandas as pd

# --- CONFIGURAZIONE PAGINA ---
st.set_page_config(page_title="ASD Centurion V5.5", layout="wide")

# --- GESTIONE SESSION STATE ---
defaults = {
    "p1": 50.0, "a1": 0.0,    # Motore SX
    "p2": 50.0, "a2": 0.0,    # Motore DX
    "pp_x": 0.0, "pp_y": 5.42 # Pivot Point default
}

for key, val in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = val

# --- FUNZIONI DI CALLBACK ---
def update_from_slider(key):
    st.session_state[key] = st.session_state[f"{key}_slider"]

def update_from_input(key):
    st.session_state[key] = st.session_state[f"{key}_input"]

def reset_engines():
    st.session_state.p1 = 50.0
    st.session_state.a1 = 0.0
    st.session_state.p2 = 50.0
    st.session_state.a2 = 0.0
    # Update manuale per sicurezza UI
    if 'p1_slider' in st.session_state: st.session_state.p1_slider = 50.0
    if 'p1_input' in st.session_state: st.session_state.p1_input = 50.0
    if 'p2_slider' in st.session_state: st.session_state.p2_slider = 50.0
    if 'p2_input' in st.session_state: st.session_state.p2_input = 50.0

def reset_pivot():
    st.session_state.pp_x = 0.0
    st.session_state.pp_y = 5.42
    if 'pp_x_slider' in st.session_state: st.session_state.pp_x_slider = 0.0
    if 'pp_x_input' in st.session_state: st.session_state.pp_x_input = 0.0
    if 'pp_y_slider' in st.session_state: st.session_state.pp_y_slider = 5.42
    if 'pp_y_input' in st.session_state: st.session_state.pp_y_input = 5.42

# --- WIDGET CUSTOM (Slider + Input Numerico) ---
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

# --- SIDEBAR ---
with st.sidebar:
    st.header("⚙️ Controlli Sistema")
    
    st.subheader("Reset")
    c_res1, c_res2 = st.columns(2)
    with c_res1:
        st.button("M. Motori", on_click=reset_engines, type="primary", use_container_width=True)
    with c_res2:
        st.button("P. Pivot", on_click=reset_pivot, use_container_width=True)
    
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

# --- HEADER ---
st.markdown("<h1 style='text-align: center;'>⚓ Rimorchiatore ASD 'CENTURION' V5.5</h1>", unsafe_allow_html=True)

# --- CALCOLI FISICI ---
pos_sx = np.array([-2.7, -12.0])
pos_dx = np.array([2.7, -12.0])
pp_pos = np.array([st.session_state.pp_x, st.session_state.pp_y])

# Tonnellate
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

# Intersezione Vettoriale
def intersect_lines(p1, angle1_deg, p2, angle2_deg):
    th1 = np.radians(90 - angle1_deg)
    th2 = np.radians(90 - angle2_deg)
    dir1 = np.array([np.cos(th1), np.sin(th1)])
    dir2 = np.array([np.cos(th2), np.sin(th2)])
    matrix = np.column_stack((dir1, -dir2))
    delta = p2 - p1
    if abs(np.linalg.det(matrix)) < 1e-3: 
        return None
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
    [1, 2.2, 1], 
    gap="small"
)

# Helper Grafico per Orologi
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
    # Grafico Matplotlib
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

    # Vettori Motori
    scale = 0.35
    ax.arrow(pos_sx[0], pos_sx[1], u1*scale, v1*scale, head_width=1.5, fc='#d32f2f', ec='#d32f2f', alpha=0.7, zorder=5)
    ax.arrow(pos_dx[0], pos_dx[1], u2*scale, v2*scale, head_width=1.5, fc='#388e3c', ec='#388e3c', alpha=0.7, zorder=5)

    # Vettore Risultante
    if res_ton > 0.1:
        ax.scatter(origin_res[0], origin_res[1], c='blue', marker='x', s=50, zorder=6)
        ax.arrow(origin_res[0], origin_res[1], res_u*scale, res_v*scale, head_width=2.5, fc='blue', ec='blue', alpha=0.4, zorder=4)
        
        if logic_used == "Intersezione":
            ax.plot([pos_sx[0], origin_res[0]], [pos_sx[1], origin_res[1]], 'r:', alpha=0.3)
            ax.plot([pos_dx[0], origin_res[0]], [pos_dx[1], origin_res[1]], 'g:', alpha=0.3)

    # Momento
    if abs(Total_Moment) > 20:
        arc_col = '#9c27b0'
        sign = 1 if Total_Moment > 0 else -1
        style = f"Simple, tail_width=2, head_width=8, head_length=8"
        conn_style = f"arc3,rad={0.4 * sign}"
        
        p_start = (st.session_state.pp_x, st.session_state.pp_y - 8)
        p_end = (st.session_state.pp_x, st.session_state.pp_y + 8)
        
        if sign < 0: 
            p_start, p_end = p_end, p_start
            
        arrow = FancyArrowPatch(p_start, p_end, connectionstyle=conn_style, arrowstyle=style, color=arc_col, alpha=0.6, zorder=3)
        ax.add_patch(arrow)

    ax.set_xlim(-25, 25); ax.set_ylim(-30, 30); ax.axis('off')
    st.pyplot(fig)

    # Dati Numerici
    st.markdown("### 📊 Analisi Forze")
    c_data1, c_data2 = st.columns(2)
    c_data1.metric("Risultante Totale", f"{res_ton:.1f} t")
    c_data2.metric("Momento (Yaw)", f"{abs(Total_Moment):.0f} kNm", 
                   delta="Sinistra" if Total_Moment > 0 else "Dritta" if Total_Moment < -20 else "Neutro")

    # Controlli Pivot Point
    with st.expander("📍 Configurazione Pivot Point", expanded=True):
        render_control("Longitudinale Y (Prua/Poppa)", "pp_y", -16.0, 16.0, 0.5)
        render_control("Trasversale X (Dritta/Sinistra)", "pp_x", -5.0, 5.0, 0.5)
