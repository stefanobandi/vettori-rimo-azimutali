import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import PathPatch, FancyArrowPatch
from matplotlib.path import Path

# --- CONFIGURAZIONE PAGINA ---
st.set_page_config(page_title="ASD Centurion V5.18", layout="wide")

# --- COSTANTI FISICHE ---
G_ACCEL = 9.80665  # Accelerazione gravità per conversione tm -> kNm

# --- GESTIONE SESSION STATE ---
# Inizializza le variabili se non esistono
defaults = {
    "p1": 50, "a1": 0,    # Motore SX
    "p2": 50, "a2": 0,    # Motore DX
    "pp_x": 0.0, "pp_y": 5.42 # Pivot Point
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
    <p style='font-size: 18px; margin-bottom: 10px;'>Simulatore Didattico Vettoriale</p>
    <b>Dimensioni:</b> 32.50 m x 11.70 m | <b>Bollard Pull:</b> 70 ton<br>
    <span style='color: #666; font-size: 0.9em;'>Versione 5.18 (Full Side Step Suite + Physics Upgrade)</span>
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
    
    col_ss1, col_ss2 = st.columns(2)
    
    with col_ss1:
        st.markdown("**Verso SINISTRA**")
        # Fast Sinistra: SX 145° (50%) | DX 315° (58%)
        st.button("⚡ Fast SINISTRA", on_click=set_engine_state, args=(50, 145, 58, 315), use_container_width=True)
        # Slow Sinistra (50%): SX 189° | DX 351°
        st.button("🐢 Slow SINISTRA", on_click=set_engine_state, args=(50, 189, 50, 351), use_container_width=True)

    with col_ss2:
        st.markdown("**Verso DRITTA**")
        # Fast Dritta: SX 045° (58%) | DX 215° (50%)
        st.button("⚡ Fast DRITTA", on_click=set_engine_state, args=(58, 45, 50, 215), use_container_width=True)
        # Slow Dritta (50%): SX 009° | DX 171°
        st.button("🐢 Slow DRITTA", on_click=set_engine_state, args=(50, 9, 50, 171), use_container_width=True)

# --- CALCOLI FISICI ---
pos_sx = np.array([-2.7, -12.0])
pos_dx = np.array([2.7, -12.0])
pp_pos = np.array([st.session_state.pp_x, st.session_state.pp_y])

# Tonnellate base
ton1 = (st.session_state.p1 / 100) * 35
ton2 = (st.session_state.p2 / 100) * 35

# Vettori base
rad1, rad2 = np.radians(st.session_state.a1), np.radians(st.session_state.a2)
u1, v1 = ton1 * np.sin(rad1), ton1 * np.cos(rad1)
u2, v2 = ton2 * np.sin(rad2), ton2 * np.cos(rad2)

F_sx = np.array([u1, v1])
F_dx = np.array([u2, v2])

# --- LOGICA INTERFERENZA (NEW) ---
# Controlliamo se la scia di un motore colpisce l'altro
efficiency_factor = 1.0
warning_interference = False

def check_wash_hit(origin, wash_vec, target_pos, threshold=2.0):
    wash_len = np.linalg.norm(wash_vec)
    if wash_len < 0.1: return False
    
    wash_dir = wash_vec / wash_len
    to_target = target_pos - origin
    
    # Proiezione
    proj_length = np.dot(to_target, wash_dir)
    
    if proj_length > 0: # Il target è "a valle"
        perp_dist = np.linalg.norm(to_target - (proj_length * wash_dir))
        if perp_dist < threshold:
            return True
    return False

# Wash (flusso) va in direzione opposta alla spinta
wash_sx = -F_sx
wash_dx = -F_dx

hit_sx_to_dx = check_wash_hit(pos_sx, wash_sx, pos_dx)
hit_dx_to_sx = check_wash_hit(pos_dx, wash_dx, pos_sx)

if hit_sx_to_dx or hit_dx_to_sx:
    efficiency_factor = 0.8 # Perdita del 20%
    warning_interference = True

# --- RISULTANTE E MOMENTI ---
# Applichiamo l'efficienza
res_u = (u1 + u2) * efficiency_factor
res_v = (v1 + v2) * efficiency_factor
res_ton = np.sqrt(res_u**2 + res_v**2)

# Momento (applicando l'efficienza anche qui)
r_sx = pos_sx - pp_pos
r_dx = pos_dx - pp_pos

M_sx_tm = (r_sx[0] * F_sx[1] - r_sx[1] * F_sx[0]) * efficiency_factor
M_dx_tm = (r_dx[0] * F_dx[1] - r_dx[1] * F_dx[0]) * efficiency_factor

Total_Moment_tm = M_sx_tm + M_dx_tm
Total_Moment_knm = Total_Moment_tm * G_ACCEL

# --- CALCOLO INTERSEZIONE ---
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

# --- LAYOUT VISIVO ---
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

# === PORT (SX) ===
with col_sx:
    st.markdown("<h3 style='text-align: center; color: #ff4b4b;'>PORT (SX)</h3>", unsafe_allow_html=True)
    st.slider("Potenza SX (%)", 0, 100, step=1, key="p1")
    st.metric("Spinta SX", f"{ton1:.1f} t")
    st.slider("Azimut SX (°)", 0, 360, step=1, key="a1")
    fig_sx = plot_clock(st.session_state.a1, 'red')
    st.pyplot(fig_sx, use_container_width=False)
    plt.close(fig_sx)

# === STBD (DX) ===
with col_dx:
    st.markdown("<h3 style='text-align: center; color: #4CAF50;'>STBD (DX)</h3>", unsafe_allow_html=True)
    st.slider("Potenza DX (%)", 0, 100, step=1, key="p2")
    st.metric("Spinta DX", f"{ton2:.1f} t")
    st.slider("Azimut DX (°)", 0, 360, step=1, key="a2")
    fig_dx = plot_clock(st.session_state.a2, 'green')
    st.pyplot(fig_dx, use_container_width=False)
    plt.close(fig_dx)

# === CENTER (GRAFICA) ===
with col_center:
    with st.expander("📍 Configurazione Pivot Point", expanded=True):
        c1, c2 = st.columns(2)
        with c1: st.slider("Longitudinale (Y)", -16.0, 16.0, step=0.1, key="pp_y")
        with c2: st.slider("Trasversale (X)", -5.0, 5.0, step=0.1, key="pp_x")

    fig, ax = plt.subplots(figsize=(8, 10))
    
    # 1. DISEGNO SCAFO & FENDER
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
    
    # Fender
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

    # 2. FRECCIA MOMENTO (ROTATION)
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

    # 3. MOTORI E RISULTANTE
    scale = 0.4
    ax.arrow(pos_sx[0], pos_sx[1], u1*scale, v1*scale, head_width=1.2, fc='red', ec='red', width=0.25, alpha=0.8, zorder=4)
    ax.arrow(pos_dx[0], pos_dx[1], u2*scale, v2*scale, head_width=1.2, fc='green', ec='green', width=0.25, alpha=0.8, zorder=4)

    # Risultante
    ax.scatter(origin_res[0], origin_res[1], c='blue', s=40, marker='x', zorder=4)
    ax.arrow(origin_res[0], origin_res[1], res_u*scale, res_v*scale, head_width=2.0, head_length=2.0, fc='blue', ec='blue', width=0.6, alpha=0.4, zorder=4)

    # Linee tratteggiate per l'origine della forza (se Intersezione)
    if logic_used == "C (Intersezione)" and abs(origin_res[1]) < 40:
        ax.plot([pos_sx[0], origin_res[0]], [pos_sx[1], origin_res[1]], 'r--', lw=1, alpha=0.3)
        ax.plot([pos_dx[0], origin_res[0]], [pos_dx[1], origin_res[1]], 'g--', lw=1, alpha=0.3)

    # 4. VISUALIZZAZIONE BRACCIO DI LEVA (NEW)
    if res_ton > 1.0:
        rv_norm = np.array([res_u, res_v]) / (np.linalg.norm([res_u, res_v]) + 1e-6)
        pp_to_origin = origin_res - pp_pos
        projection_len = np.dot(pp_to_origin, rv_norm)
        closest_point_on_line = origin_res - (projection_len * rv_norm)
        
        lever_arm_vec = closest_point_on_line - pp_pos
        lever_arm_len = np.linalg.norm(lever_arm_vec)
        
        if lever_arm_len > 0.1:
            # Linea viola del braccio
            ax.plot([pp_pos[0], closest_point_on_line[0]], 
                    [pp_pos[1], closest_point_on_line[1]], 
                    color='purple', linestyle='--', linewidth=1.5, zorder=3)
            
            # Etichetta con sfondo
            mid_x = (pp_pos[0] + closest_point_on_line[0]) / 2
            mid_y = (pp_pos[1] + closest_point_on_line[1]) / 2
            ax.text(mid_x, mid_y, f" {lever_arm_len:.1f}m ", 
                    color='purple', fontsize=9, fontweight='bold', 
                    bbox=dict(facecolor='white', alpha=0.8, edgecolor='none', pad=1))
            
            # Estensione retta d'azione
            back_point = origin_res - rv_norm * 20
            fwd_point = origin_res + rv_norm * 20
            ax.plot([back_point[0], fwd_point[0]], [back_point[1], fwd_point[1]], 
                    color='blue', linestyle=':', alpha=0.2, linewidth=1)

    ax.set_xlim(-20, 20); ax.set_ylim(-25, 30); ax.set_aspect('equal'); ax.axis('off') 
    st.pyplot(fig)
    plt.close(fig)
    
    # 5. Analisi Dinamica e Warning
    st.markdown("### 📊 Analisi Dinamica")
    
    # WARNING BOX
    if warning_interference:
        st.error("⚠️ THRUSTER INTERFERENCE: I flussi si incrociano! Spinta ridotta del 20%.")
    
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
