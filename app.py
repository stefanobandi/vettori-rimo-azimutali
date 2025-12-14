import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import PathPatch, FancyArrowPatch
from matplotlib.path import Path

# --- CONFIGURAZIONE PAGINA ---
st.set_page_config(page_title="ASD Centurion V5.11", layout="wide")

# --- GESTIONE SESSION STATE ---
defaults = {
    "p1": 50, "a1": 0,    # Motore SX
    "p2": 50, "a2": 0,    # Motore DX
    "pp_x": 0.0, "pp_y": 5.42 # Pivot Point default
}

for key, val in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = val

# --- FUNZIONI DI RESET ---
def reset_engines():
    st.session_state.p1 = 50
    st.session_state.a1 = 0
    st.session_state.p2 = 50
    st.session_state.a2 = 0

def reset_pivot():
    st.session_state.pp_x = 0.0
    st.session_state.pp_y = 5.42

# --- FUNZIONE OROLOGIO (POLAR PLOT) ---
def plot_clock(azimuth_deg, color, label):
    # Crea un piccolo grafico polare
    fig, ax = plt.subplots(figsize=(2.5, 2.5), subplot_kw={'projection': 'polar'})
    ax.set_theta_zero_location('N') # Nord in alto
    ax.set_theta_direction(-1)      # Senso orario
    
    # Rimuove le scritte inutili per pulizia
    ax.set_yticklabels([])
    ax.set_xticks(np.radians([0, 90, 180, 270]))
    ax.set_xticklabels(['N', 'E', 'S', 'W'], fontsize=8)
    
    # Freccia indicatrice
    ax.arrow(np.radians(azimuth_deg), 0, 0, 0.9, color=color, width=0.15, 
             head_width=0, length_includes_head=True)
    
    # Stile
    ax.grid(True, alpha=0.3)
    fig.patch.set_alpha(0) # Sfondo trasparente
    
    return fig

# --- HEADER ---
st.markdown("<h1 style='text-align: center; color: #2c3e50;'>⚓ Rimorchiatore ASD 'CENTURION' V5.11</h1>", unsafe_allow_html=True)
st.markdown("<h4 style='text-align: center; color: #7f8c8d;'>Simulazione Vettoriale (Matplotlib Engine)</h4>", unsafe_allow_html=True)
st.write("---")

# --- SIDEBAR (CONTROLLI E OROLOGI) ---
with st.sidebar:
    st.header("Comandi")
    
    # Reset
    c1, c2 = st.columns(2)
    with c1: st.button("Reset Motori", on_click=reset_engines, type="primary", use_container_width=True)
    with c2: st.button("Reset PP", on_click=reset_pivot, use_container_width=True)
    
    st.markdown("---")
    
    # --- PORT (SX) ---
    st.markdown("<h3 style='color: #d63031; text-align: center;'>PORT (SX)</h3>", unsafe_allow_html=True)
    # Slider
    st.slider("Azimut SX", 0, 360, key="a1")
    st.slider("Potenza SX %", 0, 100, key="p1")
    # Orologio SX
    st.pyplot(plot_clock(st.session_state.a1, '#d63031', "SX"), use_container_width=False)
    
    st.markdown("---")
    
    # --- STBD (DX) ---
    st.markdown("<h3 style='color: #27ae60; text-align: center;'>STBD (DX)</h3>", unsafe_allow_html=True)
    # Slider
    st.slider("Azimut DX", 0, 360, key="a2")
    st.slider("Potenza DX %", 0, 100, key="p2")
    # Orologio DX
    st.pyplot(plot_clock(st.session_state.a2, '#27ae60', "DX"), use_container_width=False)
    
    st.markdown("---")
    
    # --- PIVOT POINT ---
    st.markdown("### 📍 Config. Pivot Point")
    st.slider("Longitudinale (Y)", -16.0, 16.0, step=0.5, key="pp_y")
    st.slider("Trasversale (X)", -5.0, 5.0, step=0.5, key="pp_x")


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
M_sx = r_sx[0] * F_sx[1] - r_sx[1] * F_sx[0]
M_dx = r_dx[0] * F_dx[1] - r_dx[1] * F_dx[0]
Total_Moment = M_sx + M_dx

# Intersezione (Logica Vettoriale)
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

# --- GRAFICA CENTRALE (MATPLOTLIB) ---
col_main = st.container()

with col_main:
    # Creazione Figura
    fig, ax = plt.subplots(figsize=(8, 10))
    
    # 1. DISEGNO SCAFO (Migliorato V5.11)
    # Punti scafo più dettagliati rispetto alla V5.10
    hw = 5.85; stern = -16.25; bow_tip = 16.25
    verts = [
        (-hw, stern), (hw, stern), # Poppa
        (hw, 5.0), # Fianco dritto
        (0, bow_tip), # Punta Prua
        (-hw, 5.0), # Fianco sinistro
        (-hw, stern) # Chiusura
    ]
    codes = [Path.MOVETO, Path.LINETO, Path.LINETO, Path.CURVE3, Path.CURVE3, Path.LINETO]
    patch = PathPatch(Path(verts, codes), facecolor='#dcdde1', edgecolor='#2f3640', lw=2, zorder=1)
    ax.add_patch(patch)
    
    # Pivot Point
    ax.scatter(st.session_state.pp_x, st.session_state.pp_y, c='black', s=150, zorder=10)
    ax.text(st.session_state.pp_x + 0.7, st.session_state.pp_y, "PP", fontsize=12, weight='bold', zorder=10)

    # 2. FRECCIA MOMENTO (Attorno al PP)
    if abs(Total_Moment) > 10:
        arc_color = '#8e44ad' # Viola
        moment_sign = np.sign(Total_Moment) # +1 SX, -1 DX
        
        # Disegno arco che mostra la rotazione
        style = f"Simple, tail_width=2, head_width=10, head_length=8"
        
        # Se rotazione a sinistra (antiorario), la freccia va su a destra del PP
        if Total_Moment > 0:
            p_start = (pp_pos[0] + 5, pp_pos[1] - 2)
            p_end = (pp_pos[0] + 5, pp_pos[1] + 2)
            connection = "arc3,rad=-0.5" # Curva verso sinistra
            rot_label = "ROT. SX"
        else:
            p_start = (pp_pos[0] - 5, pp_pos[1] - 2)
            p_end = (pp_pos[0] - 5, pp_pos[1] + 2)
            connection = "arc3,rad=0.5" # Curva verso destra
            rot_label = "ROT. DX"
            
        ax.add_patch(FancyArrowPatch(posA=p_start, posB=p_end,
                                     connectionstyle=connection, 
                                     arrowstyle=style, color=arc_color, alpha=0.8, zorder=5))
        
        ax.text(0, 20, rot_label, ha='center', color=arc_color, fontweight='bold', fontsize=14)

    # Motori
    scale = 0.4
    ax.arrow(pos_sx[0], pos_sx[1], u1*scale, v1*scale, head_width=1.2, fc='#d63031', ec='#d63031', width=0.3, alpha=0.8, zorder=4)
    ax.arrow(pos_dx[0], pos_dx[1], u2*scale, v2*scale, head_width=1.2, fc='#27ae60', ec='#27ae60', width=0.3, alpha=0.8, zorder=4)

    # Risultante
    ax.scatter(origin_res[0], origin_res[1], c='#2980b9', s=50, marker='D', zorder=4)
    ax.arrow(origin_res[0], origin_res[1], res_u*scale, res_v*scale, head_width=2.0, fc='#2980b9', ec='#2980b9', width=0.6, alpha=0.5, zorder=4)

    # Linee di proiezione (solo se intersezione)
    if logic_used == "C (Intersezione)" and abs(origin_res[1]) < 40:
        ax.plot([pos_sx[0], origin_res[0]], [pos_sx[1], origin_res[1]], 'r--', lw=1, alpha=0.2)
        ax.plot([pos_dx[0], origin_res[0]], [pos_dx[1], origin_res[1]], 'g--', lw=1, alpha=0.2)

    ax.set_xlim(-20, 20); ax.set_ylim(-25, 30); ax.set_aspect('equal'); ax.axis('off') 
    st.pyplot(fig)
    
    # 3. METRICHE
    st.markdown("### 📊 Risultato Dinamico")
    m1, m2, m3 = st.columns(3)
    
    deg_res = np.degrees(np.arctan2(res_u, res_v))
    if deg_res < 0: deg_res += 360
    
    m1.metric("Tiro Totale", f"{res_ton:.1f} t")
    m2.metric("Direzione", f"{deg_res:.0f}°")
    
    dir_rot = "STABILE"
    if abs(Total_Moment) > 20:
        dir_rot = "SINISTRA" if Total_Moment > 0 else "DRITTA"
    
    m3.metric("Rotazione", dir_rot, delta=f"{abs(Total_Moment):.0f} kNm", delta_color="off")
