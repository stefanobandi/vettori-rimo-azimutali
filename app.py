import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import PathPatch, FancyArrowPatch
from matplotlib.path import Path

# --- CONFIGURAZIONE PAGINA ---
st.set_page_config(page_title="ASD Centurion V5.16", layout="wide")

# --- COSTANTI FISICHE ---
G_ACCEL = 9.80665  # Accelerazione gravità per conversione tm -> kNm

# --- GESTIONE SESSION STATE ---
defaults = {
    "p1": 50, "a1": 0,    # Motore SX
    "p2": 50, "a2": 0,    # Motore DX
    "pp_x": 0.0, "pp_y": 5.42
}

for key, val in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = val

# --- FUNZIONI DI GESTIONE STATO ---
def set_engine_state(p1, a1, p2, a2):
    st.session_state.p1 = p1
    st.session_state.a1 = a1
    st.session_state.p2 = p2
    st.session_state.a2 = a2

def reset_engines():
    st.session_state.p1 = 50
    st.session_state.a1 = 0
    st.session_state.p2 = 50
    st.session_state.a2 = 0

def reset_pivot():
    st.session_state.pp_x = 0.0
    st.session_state.pp_y = 5.42

# --- HEADER ---
st.markdown("<h1 style='text-align: center;'>⚓ Rimorchiatore ASD 'CENTURION'</h1>", unsafe_allow_html=True)
st.markdown("""
<div style='text-align: center;'>
    <p style='font-size: 18px; margin-bottom: 10px;'>Per informazioni contattare <b>stefano.bandi22@gmail.com</b></p>
    <b>Dimensioni:</b> 32.50 m x 11.70 m | <b>Bollard Pull:</b> 70 ton | <b>Logica:</b> Intersezione Vettoriale<br>
    <span style='color: #666; font-size: 0.9em;'>Versione 5.16 (Reset Separati + Custom Vectors)</span>
</div>
""", unsafe_allow_html=True)

st.write("---")

# --- SIDEBAR COMPLETA ---
with st.sidebar:
    st.header("Comandi Globali")
    
    # 1. Reset Separati
    st.markdown("### 🔄 Reset")
    col_res1, col_res2 = st.columns(2)
    with col_res1:
        st.button("Reset Motori", on_click=reset_engines, type="primary", use_container_width=True)
    with col_res2:
        st.button("Reset Pivot", on_click=reset_pivot, use_container_width=True)
    
    st.markdown("---")
    
    # 2. Preset Longitudinali
    st.markdown("### ↕️ Longitudinali")
    col_l1, col_l2 = st.columns(2)
    with col_l1:
        st.button("Tutta AVANTI", on_click=set_engine_state, args=(100, 0, 100, 0), use_container_width=True)
        st.button("Mezza INDIETRO", on_click=set_engine_state, args=(50, 180, 50, 180), use_container_width=True)
    with col_l2:
        st.button("Mezza AVANTI", on_click=set_engine_state, args=(50, 0, 50, 0), use_container_width=True)
        st.button("Tutta INDIETRO", on_click=set_engine_state, args=(100, 180, 100, 180), use_container_width=True)

    st.markdown("---")

    # 3. Preset Laterali (Side Step Custom)
    st.markdown("### ↔️ Traslazioni (Side Step)")
    
    # Slow Side Step DRITTA
    # SX: 009° / 25% | DX: 171° / 25%
    st.button("Slow Side Step DRITTA", on_click=set_engine_state, args=(25, 9, 25, 171), use_container_width=True)
    
    # Slow Side Step SINISTRA (Aggiornato V5.16)
    # SX: 189° / 25% | DX: 351° / 25%
    st.button("Slow Side Step SINISTRA", on_click=set_engine_state, args=(25, 189, 25, 351), use_container_width=True)

# --- CALCOLI FISICI ---
pos_sx = np.array([-2.7, -12.0])
pos_dx = np.array([2.7, -12.0])
pp_pos = np.array([st.session_state.pp_x, st.session_state.pp_y])

# Tonnellate
ton1 = (st.session_state.p1 / 100) * 35
ton2 = (st.session_state.p2 / 100) * 35

# Vettori
rad1, rad2 = np.radians(st.session_state.a1), np.radians(st.session_state.a2)
u1, v1 = ton1 * np.sin(rad1), ton1 * np.cos(rad1)
u2, v2 = ton2 * np.sin(rad2), ton2 * np.cos(rad2)

F_sx = np.array([u1, v1])
F_dx = np.array([u2, v2])

# Risultante
res_u = u1 + u2
res_v = v1 + v2
res_ton = np.sqrt(res_u**2 + res_v**2)

# Momento
r_sx = pos_sx - pp_pos
r_dx = pos_dx - pp_pos

M_sx_tm = r_sx[0] * F_sx[1] - r_sx[1] * F_sx[0]
M_dx_tm = r_dx[0] * F_dx[1] - r_dx[1] * F_dx[0]
Total_Moment_tm = M_sx_tm + M_dx_tm
Total_Moment_knm = Total_Moment_tm * G_ACCEL

# Intersezione
def intersect_lines(p1, angle1_deg, p2, angle2_deg):
    th1 = np.radians(90 - angle1_deg)
    th2 = np.radians(90 - angle2_deg)
    v1 = np.array([np.cos(th1), np.sin(th1)])
    v2 = np.array([np.cos(th2), np.sin(th2)])
    matrix = np.column_stack((v1, -v2))
    delta = p2 - p1
    if abs(np.linalg.det(matrix)) < 1e-4:
        return None
    t = np.linalg.solve(matrix, delta)[0]
    return p1 + t * v1

intersection = None
if ton1 > 0.1 and ton2 > 0.1:
    intersection = intersect_lines(pos_sx, st.session_state.a1, pos_dx, st.session_state.a2)

origin_res = np.array([0.0, -12.0])
logic_used = "B (Default)"

if intersection is not None and np.linalg.norm(intersection - np.array([0, -12])) < 80:
    origin_res = intersection
    logic_used = "C (Intersezione)"
elif ton1 + ton2 > 0.1:
    w_x = (ton1 * pos_sx[0] + ton2 * pos_dx[0]) / (ton1 + ton2)
    origin_res = np.array([w_x, -12.0])
    logic_used = "B (Media)"

# --- LAYOUT ---
col_sx, col_center, col_dx = st.columns([1, 2, 1], gap="medium")

def plot_clock(azimuth_deg, color):
    fig, ax = plt.subplots(figsize=(3, 3), subplot_kw={'projection': 'polar'})
    ax.set_theta_zero_location('N')
    ax.set_theta_direction(-1)
    ax.set_yticks([])
    ax.set_xticks(np.radians([0, 90, 180, 270]))
    ax.set_xticklabels(['0', '90', '180', '270'])
    ax.arrow(np.radians(azimuth_deg), 0, 0, 0.9, color=color, width=0.15, head_width=0, length_includes_head=True)
    ax.grid(True, alpha=0.3)
    fig.patch.set_alpha(0)
    return fig

# === PORT ===
with col_sx:
    st.markdown("<h3 style='text-align: center; color: #ff4b4b;'>PORT (SX)</h3>", unsafe_allow_html=True)
    st.slider("Potenza SX (%)", 0, 100, step=1, key="p1")
    st.metric("Spinta SX", f"{ton1:.1f} t")
    st.slider("Azimut SX (°)", 0, 360, step=1, key="a1")
    fig_sx = plot_clock(st.session_state.a1, 'red')
    st.pyplot(fig_sx, use_container_width=False)
    plt.close(fig_sx)

# === STBD ===
with col_dx:
    st.markdown("<h3 style='text-align: center; color: #4CAF50;'>STBD (DX)</h3>", unsafe_allow_html=True)
    st.slider("Potenza DX (%)", 0, 100, step=1, key="p2")
    st.metric("Spinta DX", f"{ton2:.1f} t")
    st.slider("Azimut DX (°)", 0, 360, step=1, key="a2")
    fig_dx = plot_clock(st.session_state.a2, 'green')
    st.pyplot(fig_dx, use_container_width=False)
    plt.close(fig_dx)

# === CENTER ===
with col_center:
    with st.expander("📍 Configurazione Pivot Point", expanded=True):
        c1, c2 = st.columns(2)
        with c1: st.slider("Longitudinale (Y)", -16.0, 16.0, step=0.1, key="pp_y")
        with c2: st.slider("Trasversale (X)", -5.0, 5.0, step=0.1, key="pp_x")

    fig, ax = plt.subplots(figsize=(8, 10))
    
    # 1. DISEGNO SCAFO & FENDER (V5.13 Design)
    hw = 5.85; stern = -16.25; bow_tip = 16.25; shoulder = 8.0

    path_data = [
        (Path.MOVETO, (-hw, stern)),
        (Path.LINETO, (hw, stern)),
        (Path.LINETO, (hw, shoulder)),
        (Path.CURVE4, (hw, 14.0)), (Path.CURVE4, (4.0, bow_tip)), (Path.CURVE4, (0, bow_tip)),    
        (Path.CURVE4, (-4.0, bow_tip)), (Path.CURVE4, (-hw, 14.0)), (Path.CURVE4, (-hw, shoulder)), 
        (Path.LINETO, (-hw, stern)), (Path.CLOSEPOLY, (-hw, stern))
    ]
    codes, verts = zip(*path_data)
    patch = PathPatch(Path(verts, codes), facecolor='#cccccc', edgecolor='#555555', lw=2, zorder=1)
    ax.add_patch(patch)
    
    # Fender (Solo contorno spesso)
    fender_data = [
        (Path.MOVETO, (hw, shoulder)),
        (Path.CURVE4, (hw, 14.0)), (Path.CURVE4, (4.0, bow_tip)), (Path.CURVE4, (0, bow_tip)),   
        (Path.CURVE4, (-4.0, bow_tip)), (Path.CURVE4, (-hw, 14.0)), (Path.CURVE4, (-hw, shoulder)), 
    ]
    f_codes, f_verts = zip(*fender_data)
    fender_patch = PathPatch(Path(f_verts, f_codes), facecolor='none', edgecolor='#333333', lw=8, capstyle='round', zorder=2)
    ax.add_patch(fender_patch)

    # Pivot Point
    ax.scatter(st.session_state.pp_x, st.session_state.pp_y, c='black', s=120, zorder=10)
    ax.text(st.session_state.pp_x + 0.6, st.session_state.pp_y, "PP", fontsize=11, weight='bold', zorder=10)

    # 2. FRECCIA MOMENTO
    if abs(Total_Moment_tm) > 1:
        arc_color = '#800080'
        arrow_y_pos = 24.0 
        
        if Total_Moment_tm > 0:
            p_start = (5.0, arrow_y_pos); p_end = (-5.0, arrow_y_pos); connection = "arc3,rad=0.3"
        else:
            p_start = (-5.0, arrow_y_pos); p_end = (5.0, arrow_y_pos); connection = "arc3,rad=-0.3" 

        style = f"Simple, tail_width={min(3, abs(Total_Moment_tm)/50)}, head_width=8, head_length=8"
        ax.add_patch(FancyArrowPatch(posA=p_start, posB=p_end, connectionstyle=connection, 
                                     arrowstyle=style, color=arc_color, alpha=0.8, zorder=5))
        
        rot_label = "ROT. SX" if Total_Moment_tm > 0 else "ROT. DX"
        ax.text(0, arrow_y_pos + 3.0, rot_label, ha='center', color=arc_color, fontweight='bold', fontsize=12)

    # Motori
    scale = 0.4
    ax.arrow(pos_sx[0], pos_sx[1], u1*scale, v1*scale, head_width=1.2, fc='red', ec='red', width=0.25, alpha=0.8, zorder=4)
    ax.arrow(pos_dx[0], pos_dx[1], u2*scale, v2*scale, head_width=1.2, fc='green', ec='green', width=0.25, alpha=0.8, zorder=4)

    # Risultante
    ax.scatter(origin_res[0], origin_res[1], c='blue', s=40, marker='x', zorder=4)
    ax.arrow(origin_res[0], origin_res[1], res_u*scale, res_v*scale, head_width=2.0, head_length=2.0, fc='blue', ec='blue', width=0.6, alpha=0.4, zorder=4)

    if logic_used == "C (Intersezione)" and abs(origin_res[1]) < 40:
        ax.plot([pos_sx[0], origin_res[0]], [pos_sx[1], origin_res[1]], 'r--', lw=1, alpha=0.3)
        ax.plot([pos_dx[0], origin_res[0]], [pos_dx[1], origin_res[1]], 'g--', lw=1, alpha=0.3)

    ax.set_xlim(-20, 20); ax.set_ylim(-25, 30); ax.set_aspect('equal'); ax.axis('off') 
    st.pyplot(fig)
    plt.close(fig)
    
    # 3. Analisi Dinamica
    st.markdown("### 📊 Analisi Dinamica")
    m1, m2, m3 = st.columns(3)
    
    deg_res = np.degrees(np.arctan2(res_u, res_v))
    if deg_res < 0: deg_res += 360
    
    m1.metric("Tiro Totale", f"{res_ton:.1f} t")
    m2.metric("Direzione", f"{deg_res:.0f}°")
    
    dir_rot = "STABILE"
    if abs(Total_Moment_tm) > 2.0:
        dir_rot = "SINISTRA" if Total_Moment_tm > 0 else "DRITTA"
    
    delta_str = f"{abs(Total_Moment_knm):.0f} kNm / {abs(Total_Moment_tm):.1f} tm"
    m3.metric("Rotazione", dir_rot, delta=delta_str, delta_color="off")
