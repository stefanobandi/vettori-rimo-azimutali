import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import PathPatch, FancyArrowPatch
from matplotlib.path import Path

# --- CONFIGURAZIONE PAGINA ---
st.set_page_config(page_title="ASD Centurion V5.25", layout="wide")

# --- COSTANTI FISICHE ---
G_ACCEL = 9.80665  # Accelerazione gravità
POS_THRUSTERS_Y = -12.0
POS_THRUSTERS_X = 2.7
BOLLARD_PULL_PER_ENGINE = 35.0 # Tonnellate

# --- GESTIONE SESSION STATE ---
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

# --- 1. SOLUTORE SLOW SIDE STEP (GEOMETRICO) ---
def apply_slow_side_step(direction):
    pp_y = st.session_state.pp_y
    longitudinal_dist = pp_y - POS_THRUSTERS_Y
    
    try:
        alpha_rad = np.arctan2(POS_THRUSTERS_X, longitudinal_dist)
        alpha_deg = np.degrees(alpha_rad) % 360
        
        if direction == "DRITTA":
            a1_set = alpha_deg
            a2_set = 180 - alpha_deg
        else: # SINISTRA
            a1_set = 180 + alpha_deg
            a2_set = 360 - alpha_deg
            
        st.session_state.p1 = 50
        st.session_state.a1 = int(round(a1_set % 360))
        st.session_state.p2 = 50
        st.session_state.a2 = int(round(a2_set % 360))
    except Exception as e:
        st.error(f"Errore calcolo Slow: {e}")

# --- 2. SOLUTORE FAST SIDE STEP (RICHIESTA UTENTE) ---
def apply_fast_side_step(direction):
    """
    Applica la logica di intersezione vettoriale sul Pivot Point.
    - Dritta: Motore SX (Drive) fisso a 045° / 50%. Calcola DX.
    - Sinistra: Motore DX (Drive) fisso a 315° / 50%. Calcola SX.
    """
    pp_y = st.session_state.pp_y
    dist_y = pp_y - POS_THRUSTERS_Y # Distanza longitudinale tra propulsori e PP
    
    if direction == "DRITTA":
        # Motore SX (Drive) impostato dall'utente
        a_drive = 45.0
        p_drive = 50.0
        x_drive = -POS_THRUSTERS_X
        x_slave = POS_THRUSTERS_X
        
        # 1. Trovo la coordinata X del punto di intersezione sul PP
        x_int = x_drive + dist_y * np.tan(np.radians(a_drive))
        
        # 2. Calcolo l'angolo del motore DX (Slave) affinché la linea d'azione passi per x_int
        dx = x_slave - x_int
        dy = POS_THRUSTERS_Y - pp_y
        a_slave = np.degrees(np.arctan2(dx, dy)) % 360
        
        # 3. Calcolo potenza per annullare la spinta longitudinale (Y)
        p_slave = -(p_drive * np.cos(np.radians(a_drive))) / np.cos(np.radians(a_slave))
        
        # Applica allo stato
        st.session_state.a1, st.session_state.p1 = int(a_drive), int(p_drive)
        st.session_state.a2, st.session_state.p2 = int(round(a_slave)), int(round(p_slave))
        st.toast(f"Fast Dritta calcolato: Slave a {int(round(a_slave))}° con {int(round(p_slave))}%", icon="⚡")

    else: # SINISTRA
        # Motore DX (Drive) impostato simmetricamente a 315°
        a_drive = 315.0
        p_drive = 50.0
        x_drive = POS_THRUSTERS_X
        x_slave = -POS_THRUSTERS_X
        
        x_int = x_drive + dist_y * np.tan(np.radians(a_drive))
        dx = x_slave - x_int
        dy = POS_THRUSTERS_Y - pp_y
        a_slave = np.degrees(np.arctan2(dx, dy)) % 360
        
        p_slave = -(p_drive * np.cos(np.radians(a_drive))) / np.cos(np.radians(a_slave))
        
        st.session_state.a2, st.session_state.p2 = int(a_drive), int(p_drive)
        st.session_state.a1, st.session_state.p1 = int(round(a_slave)), int(round(p_slave))
        st.toast(f"Fast Sinistra calcolato: Slave a {int(round(a_slave))}° con {int(round(p_slave))}%", icon="⚡")

# --- HEADER ---
st.markdown("<h1 style='text-align: center;'>⚓ Rimorchiatore ASD 'CENTURION'</h1>", unsafe_allow_html=True)
st.markdown("""
<div style='text-align: center;'>
    <p style='font-size: 18px; margin-bottom: 10px;'>Simulatore Didattico Vettoriale</p>
    <b>Dimensioni:</b> 32.50 m x 11.70 m | <b>Bollard Pull:</b> 70 ton<br>
    <span style='color: #666; font-size: 0.9em;'>Versione 5.25 (Fast Side Step Physics Solver)</span>
</div>
""", unsafe_allow_html=True)

st.write("---")

# --- SIDEBAR COMPLETA ---
with st.sidebar:
    st.header("Comandi Globali")
    col_res1, col_res2 = st.columns(2)
    with col_res1: st.button("Reset Motori", on_click=reset_engines, type="primary", use_container_width=True)
    with col_res2: st.button("Reset Pivot", on_click=reset_pivot, use_container_width=True)
    st.markdown("---")
    
    st.markdown("### ↕️ Longitudinali")
    col_fwd1, col_fwd2 = st.columns(2)
    with col_fwd1: st.button("Tutta AVANTI", on_click=set_engine_state, args=(100, 0, 100, 0), use_container_width=True)
    with col_fwd2: st.button("Mezza AVANTI", on_click=set_engine_state, args=(50, 0, 50, 0), use_container_width=True)
    col_aft1, col_aft2 = st.columns(2)
    with col_aft1: st.button("Tutta INDIETRO", on_click=set_engine_state, args=(100, 180, 100, 180), use_container_width=True)
    with col_aft2: st.button("Mezza INDIETRO", on_click=set_engine_state, args=(50, 180, 50, 180), use_container_width=True)
    st.markdown("---")

    st.markdown("### ↔️ Traslazioni (Side Step)")
    h1, h2 = st.columns(2)
    h1.markdown("<div style='text-align: center; color: #ff4b4b;'><b>Verso SX</b></div>", unsafe_allow_html=True)
    h2.markdown("<div style='text-align: center; color: #4CAF50;'><b>Verso DX</b></div>", unsafe_allow_html=True)

    row_fast1, row_fast2 = st.columns(2)
    with row_fast1:
        st.button("⬅️ Fast SINISTRA", on_click=apply_fast_side_step, args=("SINISTRA",), use_container_width=True)
    with row_fast2:
        st.button("➡️ Fast DRITTA", on_click=apply_fast_side_step, args=("DRITTA",), use_container_width=True)

    row_slow1, row_slow2 = st.columns(2)
    with row_slow1:
        st.button("⬅️ Slow SINISTRA", on_click=apply_slow_side_step, args=("SINISTRA",), use_container_width=True)
    with row_slow2:
        st.button("➡️ Slow DRITTA", on_click=apply_slow_side_step, args=("DRITTA",), use_container_width=True)

# --- CALCOLI FISICI ---
pos_sx = np.array([-POS_THRUSTERS_X, POS_THRUSTERS_Y])
pos_dx = np.array([POS_THRUSTERS_X, POS_THRUSTERS_Y])
pp_pos = np.array([st.session_state.pp_x, st.session_state.pp_y])

ton1 = (st.session_state.p1 / 100) * BOLLARD_PULL_PER_ENGINE
ton2 = (st.session_state.p2 / 100) * BOLLARD_PULL_PER_ENGINE

rad1, rad2 = np.radians(st.session_state.a1), np.radians(st.session_state.a2)
u1, v1 = ton1 * np.sin(rad1), ton1 * np.cos(rad1)
u2, v2 = ton2 * np.sin(rad2), ton2 * np.cos(rad2)

F_sx = np.array([u1, v1])
F_dx = np.array([u2, v2])

# Controllo interferenza
efficiency_factor = 1.0
warning_interference = False
def check_wash_hit(origin, wash_vec, target_pos, threshold=2.0):
    wash_len = np.linalg.norm(wash_vec)
    if wash_len < 0.1: return False
    wash_dir = wash_vec / wash_len
    to_target = target_pos - origin
    proj_length = np.dot(to_target, wash_dir)
    if proj_length > 0: 
        perp_dist = np.linalg.norm(to_target - (proj_length * wash_dir))
        if perp_dist < threshold: return True
    return False

wash_sx = -F_sx
wash_dx = -F_dx
if check_wash_hit(pos_sx, wash_sx, pos_dx) or check_wash_hit(pos_dx, wash_dx, pos_sx):
    efficiency_factor = 0.8
    warning_interference = True

res_u = (u1 + u2) * efficiency_factor
res_v = (v1 + v2) * efficiency_factor
res_ton = np.sqrt(res_u**2 + res_v**2)

r_sx = pos_sx - pp_pos
r_dx = pos_dx - pp_pos
M_sx_tm = (r_sx[0] * F_sx[1] - r_sx[1] * F_sx[0]) * efficiency_factor
M_dx_tm = (r_dx[0] * F_dx[1] - r_dx[1] * F_dx[0]) * efficiency_factor
Total_Moment_tm = M_sx_tm + M_dx_tm
Total_Moment_knm = Total_Moment_tm * G_ACCEL

# Centro di spinta (Intersezione o Ponderata)
def intersect_lines(p1, angle1_deg, p2, angle2_deg):
    th1 = np.radians(90 - angle1_deg)
    th2 = np.radians(90 - angle2_deg)
    v1 = np.array([np.cos(th1), np.sin(th1)])
    v2 = np.array([np.cos(th2), np.sin(th2)])
    matrix = np.column_stack((v1, -v2))
    delta = p2 - p1
    if abs(np.linalg.det(matrix)) < 1e-4: return None
    t = np.linalg.solve(matrix, delta)[0]
    return p1 + t * v1

intersection = None
if ton1 > 0.1 and ton2 > 0.1:
    intersection = intersect_lines(pos_sx, st.session_state.a1, pos_dx, st.session_state.a2)

origin_res = np.array([0.0, -12.0])
if intersection is not None:
    origin_res = intersection
elif ton1 + ton2 > 0.1:
    w_x = (ton1 * pos_sx[0] + ton2 * pos_dx[0]) / (ton1 + ton2)
    origin_res = np.array([w_x, -12.0])

# --- LAYOUT VISIVO ---
col_sx, col_center, col_dx = st.columns([1, 2, 1], gap="medium")

def plot_clock(azimuth_deg, color):
    fig, ax = plt.subplots(figsize=(3, 3), subplot_kw={'projection': 'polar'})
    ax.set_theta_zero_location('N')
    ax.set_theta_direction(-1)
    ax.set_yticks([]); ax.set_xticks(np.radians([0, 90, 180, 270]))
    ax.set_xticklabels(['0', '90', '180', '270'])
    ax.arrow(np.radians(azimuth_deg), 0, 0, 0.9, color=color, width=0.15, head_width=0, length_includes_head=True)
    ax.grid(True, alpha=0.3)
    fig.patch.set_alpha(0)
    return fig

with col_sx:
    st.markdown("<h3 style='text-align: center; color: #ff4b4b;'>PORT (SX)</h3>", unsafe_allow_html=True)
    st.slider("Potenza SX (%)", 0, 100, step=1, key="p1")
    st.metric("Spinta SX", f"{ton1:.1f} t")
    st.slider("Azimut SX (°)", 0, 360, step=1, key="a1")
    fig_sx = plot_clock(st.session_state.a1, 'red')
    st.pyplot(fig_sx, use_container_width=False); plt.close(fig_sx)

with col_dx:
    st.markdown("<h3 style='text-align: center; color: #4CAF50;'>STBD (DX)</h3>", unsafe_allow_html=True)
    st.slider("Potenza DX (%)", 0, 100, step=1, key="p2")
    st.metric("Spinta DX", f"{ton2:.1f} t")
    st.slider("Azimut DX (°)", 0, 360, step=1, key="a2")
    fig_dx = plot_clock(st.session_state.a2, 'green')
    st.pyplot(fig_dx, use_container_width=False); plt.close(fig_dx)

with col_center:
    with st.expander("📍 Configurazione Pivot Point", expanded=True):
        c1, c2 = st.columns(2)
        with c1: st.slider("Longitudinale (Y)", -16.0, 16.0, step=0.1, key="pp_y")
        with c2: st.slider("Trasversale (X)", -5.0, 5.0, step=0.1, key="pp_x")

    fig, ax = plt.subplots(figsize=(8, 10))
    hw = 5.85; stern = -16.25; bow_tip = 16.25; shoulder = 8.0
    path_data = [
        (Path.MOVETO, (-hw, stern)), (Path.LINETO, (hw, stern)), (Path.LINETO, (hw, shoulder)),
        (Path.CURVE4, (hw, 14.0)), (Path.CURVE4, (4.0, bow_tip)), (Path.CURVE4, (0, bow_tip)),    
        (Path.CURVE4, (-4.0, bow_tip)), (Path.CURVE4, (-hw, 14.0)), (Path.CURVE4, (-hw, shoulder)), 
        (Path.LINETO, (-hw, stern)), (Path.CLOSEPOLY, (-hw, stern))
    ]
    codes, verts = zip(*path_data)
    ax.add_patch(PathPatch(Path(verts, codes), facecolor='#cccccc', edgecolor='#555555', lw=2, zorder=1))
    
    # Fender
    fender_data = [(Path.MOVETO, (hw, shoulder)), (Path.CURVE4, (hw, 14.0)), (Path.CURVE4, (4.0, bow_tip)), (Path.CURVE4, (0, bow_tip)), (Path.CURVE4, (-4.0, bow_tip)), (Path.CURVE4, (-hw, 14.0)), (Path.CURVE4, (-hw, shoulder))]
    f_codes, f_verts = zip(*fender_data)
    ax.add_patch(PathPatch(Path(f_verts, f_codes), facecolor='none', edgecolor='#333333', lw=8, capstyle='round', zorder=2))

    # --- AGGIUNTA: CERCHI AZIMUTALI (Diametro 2m -> Raggio 1m) ---
    circle_sx = plt.Circle(pos_sx, 1.0, color='red', fill=False, lw=1, ls='-', alpha=0.5, zorder=2)
    circle_dx = plt.Circle(pos_dx, 1.0, color='green', fill=False, lw=1, ls='-', alpha=0.5, zorder=2)
    ax.add_patch(circle_sx)
    ax.add_patch(circle_dx)

    # --- AGGIUNTA: PROLUNGAMENTI CHE SI FERMANO ALL'INTERSEZIONE ---
    if intersection is not None:
        ax.plot([pos_sx[0], intersection[0]], [pos_sx[1], intersection[1]], color='red', linestyle='--', lw=1.2, alpha=0.4, zorder=3)
        ax.plot([pos_dx[0], intersection[0]], [pos_dx[1], intersection[1]], color='green', linestyle='--', lw=1.2, alpha=0.4, zorder=3)

    # PP
    ax.scatter(st.session_state.pp_x, st.session_state.pp_y, c='black', s=120, zorder=10)
    ax.text(st.session_state.pp_x + 0.6, st.session_state.pp_y, "PP", fontsize=11, weight='bold', zorder=10)

    # Arco Rotazione
    if abs(Total_Moment_tm) > 1:
        arc_color = '#800080'; arrow_y_pos = 24.0 
        p_start = (5.0, arrow_y_pos) if Total_Moment_tm > 0 else (-5.0, arrow_y_pos)
        p_end = (-5.0, arrow_y_pos) if Total_Moment_tm > 0 else (5.0, arrow_y_pos)
        connection = "arc3,rad=0.3" if Total_Moment_tm > 0 else "arc3,rad=-0.3"
        style = f"Simple, tail_width={min(3, abs(Total_Moment_tm)/50)}, head_width=8, head_length=8"
        ax.add_patch(FancyArrowPatch(posA=p_start, posB=p_end, connectionstyle=connection, arrowstyle=style, color=arc_color, alpha=0.8, zorder=5))

    # Vettori Motori
    scale = 0.4
    ax.arrow(pos_sx[0], pos_sx[1], u1*scale, v1*scale, head_width=1.2, fc='red', ec='red', width=0.25, alpha=0.8, zorder=4)
    ax.arrow(pos_dx[0], pos_dx[1], u2*scale, v2*scale, head_width=1.2, fc='green', ec='green', width=0.25, alpha=0.8, zorder=4)

    # Vettore Risultante
    ax.arrow(origin_res[0], origin_res[1], res_u*scale, res_v*scale, head_width=2.0, head_length=2.0, fc='blue', ec='blue', width=0.6, alpha=0.4, zorder=4)

    ax.set_xlim(-20, 20); ax.set_ylim(-25, 30); ax.set_aspect('equal'); ax.axis('off') 
    st.pyplot(fig); plt.close(fig)
    
    # Dashboard
    st.markdown("### 📊 Analisi Dinamica")
    if warning_interference: st.error("⚠️ THRUSTER INTERFERENCE: Spinta ridotta del 20%.")
    
    m1, m2, m3 = st.columns(3)
    deg_res = np.degrees(np.arctan2(res_u, res_v)) % 360
    m1.metric("Tiro Totale", f"{res_ton:.1f} t")
    m2.metric("Direzione", f"{deg_res:.0f}°")
    
    dir_rot = "STABILE"
    if abs(Total_Moment_tm) > 2.0: dir_rot = "SINISTRA" if Total_Moment_tm > 0 else "DRITTA"
    m3.metric("Rotazione", dir_rot, delta=f"{abs(Total_Moment_knm):.0f} kNm", delta_color="off")
