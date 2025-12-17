import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import PathPatch, FancyArrowPatch, Rectangle
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

# --- 2. SOLUTORE FAST SIDE STEP (CORRETTO) ---
def apply_fast_side_step(direction):
    pp_y = st.session_state.pp_y
    dist_y = pp_y - POS_THRUSTERS_Y
    
    try:
        if direction == "DRITTA":
            a_drive, p_drive = 45.0, 50.0
            x_drive, x_slave = -POS_THRUSTERS_X, POS_THRUSTERS_X
            x_int = x_drive + dist_y * np.tan(np.radians(a_drive))
            dx, dy = x_slave - x_int, POS_THRUSTERS_Y - pp_y
            a_slave = np.degrees(np.arctan2(dx, dy)) % 360
            
            cos_slave = np.cos(np.radians(a_slave))
            if abs(cos_slave) < 0.001: raise ValueError("Angolo Slave critico (90°/270°)")
            
            p_slave = -(p_drive * np.cos(np.radians(a_drive))) / cos_slave
            
            if 1 <= p_slave <= 100:
                st.session_state.a1, st.session_state.p1 = int(a_drive), int(p_drive)
                st.session_state.a2, st.session_state.p2 = int(round(a_slave)), int(round(p_slave))
            else:
                st.error(f"Impossibile Fast Dritta: Potenza Slave richiesta {int(p_slave)}% (fuori range 1-100%)")

        else: # SINISTRA
            a_drive, p_drive = 315.0, 50.0
            x_drive, x_slave = POS_THRUSTERS_X, -POS_THRUSTERS_X
            x_int = x_drive + dist_y * np.tan(np.radians(a_drive))
            dx, dy = x_slave - x_int, POS_THRUSTERS_Y - pp_y
            a_slave = np.degrees(np.arctan2(dx, dy)) % 360
            
            cos_slave = np.cos(np.radians(a_slave))
            if abs(cos_slave) < 0.001: raise ValueError("Angolo Slave critico")
            
            p_slave = -(p_drive * np.cos(np.radians(a_drive))) / cos_slave
            
            if 1 <= p_slave <= 100:
                st.session_state.a2, st.session_state.p2 = int(a_drive), int(p_drive)
                st.session_state.a1, st.session_state.p1 = int(round(a_slave)), int(round(p_slave))
            else:
                st.error(f"Impossibile Fast Sinistra: Potenza Slave richiesta {int(p_slave)}% (fuori range 1-100%)")
                
    except Exception as e:
        st.error(f"Errore geometrico: Pivot Point troppo vicino ai motori.")

# --- HEADER ---
st.markdown("<h1 style='text-align: center;'>⚓ Rimorchiatore ASD 'CENTURION'</h1>", unsafe_allow_html=True)
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
    row_fast1, row_fast2 = st.columns(2)
    with row_fast1: st.button("⬅️ Fast SINISTRA", on_click=apply_fast_side_step, args=("SINISTRA",), use_container_width=True)
    with row_fast2: st.button("➡️ Fast DRITTA", on_click=apply_fast_side_step, args=("DRITTA",), use_container_width=True)
    row_slow1, row_slow2 = st.columns(2)
    with row_slow1: st.button("⬅️ Slow SINISTRA", on_click=apply_slow_side_step, args=("SINISTRA",), use_container_width=True)
    with row_slow2: st.button("➡️ Slow DRITTA", on_click=apply_slow_side_step, args=("DRITTA",), use_container_width=True)

# --- CALCOLI FISICI ---
pos_sx = np.array([-POS_THRUSTERS_X, POS_THRUSTERS_Y])
pos_dx = np.array([POS_THRUSTERS_X, POS_THRUSTERS_Y])
pp_pos = np.array([st.session_state.pp_x, st.session_state.pp_y])

ton1 = (st.session_state.p1 / 100) * BOLLARD_PULL_PER_ENGINE
ton2 = (st.session_state.p2 / 100) * BOLLARD_PULL_PER_ENGINE

rad1, rad2 = np.radians(st.session_state.a1), np.radians(st.session_state.a2)
u1, v1 = ton1 * np.sin(rad1), ton1 * np.cos(rad1)
u2, v2 = ton2 * np.sin(rad2), ton2 * np.cos(rad2)

F_sx, F_dx = np.array([u1, v1]), np.array([u2, v2])

# Interferenza
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

if check_wash_hit(pos_sx, -F_sx, pos_dx) or check_wash_hit(pos_dx, -F_dx, pos_sx):
    efficiency_factor, warning_interference = 0.8, True

res_u, res_v = (u1 + u2) * efficiency_factor, (v1 + v2) * efficiency_factor
res_ton = np.sqrt(res_u**2 + res_v**2)
Total_Moment_tm = ((pos_sx-pp_pos)[0]*F_sx[1] - (pos_sx-pp_pos)[1]*F_sx[0] + (pos_dx-pp_pos)[0]*F_dx[1] - (pos_dx-pp_pos)[1]*F_dx[0]) * efficiency_factor

# Intersezione
def intersect_lines(p1, a1, p2, a2):
    th1, th2 = np.radians(90-a1), np.radians(90-a2)
    v1, v2 = np.array([np.cos(th1), np.sin(th1)]), np.array([np.cos(th2), np.sin(th2)])
    m = np.column_stack((v1, -v2))
    if abs(np.linalg.det(m)) < 1e-4: return None
    return p1 + np.linalg.solve(m, p2 - p1)[0] * v1

intersection = intersect_lines(pos_sx, st.session_state.a1, pos_dx, st.session_state.a2) if ton1 > 0.1 and ton2 > 0.1 else None
origin_res = intersection if intersection is not None else np.array([(ton1*pos_sx[0] + ton2*pos_dx[0])/(ton1+ton2+1e-6), -12.0])

# --- LAYOUT VISIVO ---
col_s, col_c, col_d = st.columns([1, 2, 1], gap="medium")

with col_s:
    st.slider("Potenza SX (%)", 0, 100, key="p1")
    st.slider("Azimut SX (°)", 0, 360, key="a1")
    st.metric("Spinta SX", f"{ton1:.1f} t")

with col_d:
    st.slider("Potenza DX (%)", 0, 100, key="p2")
    st.slider("Azimut DX (°)", 0, 360, key="a2")
    st.metric("Spinta DX", f"{ton2:.1f} t")

with col_c:
    with st.expander("📍 Pivot Point", expanded=True):
        st.slider("Longitudinale (Y)", -16.0, 16.0, step=0.1, key="pp_y")
        st.slider("Trasversale (X)", -5.0, 5.0, step=0.1, key="pp_x")

    fig, ax = plt.subplots(figsize=(8, 10))
    hw, stern, bow, sh = 5.85, -16.25, 16.25, 8.0
    hull_path = Path([(-hw,stern),(hw,stern),(hw,sh),(hw,14),(4,bow),(0,bow),(-4,bow),(-hw,14),(-hw,sh),(-hw,stern)], [1,2,2,4,4,4,4,4,2,2])
    ax.add_patch(PathPatch(hull_path, facecolor='#cccccc', edgecolor='#555555', lw=2, zorder=1))
    
    # Cerchi Azimutali (Nero, r=2m)
    ax.add_patch(plt.Circle(pos_sx, 2.0, color='black', fill=False, lw=1.5, alpha=0.6, zorder=2))
    ax.add_patch(plt.Circle(pos_dx, 2.0, color='black', fill=False, lw=1.5, alpha=0.6, zorder=2))

    # --- RAPPRESENTAZIONE ELICA (POD) ---
    for pos, ang in [(pos_sx, rad1), (pos_dx, rad2)]:
        # Rettangolo nero centrato che ruota con l'azimut
        rect = Rectangle((-0.4, -1.0), 0.8, 2.0, color='black', alpha=0.8, zorder=5)
        t = plt.transforms.Affine2D().rotate_deg_around(0, 0, -np.degrees(ang)) + plt.transforms.Affine2D().translate(*pos) + ax.transData
        rect.set_transform(t)
        ax.add_patch(rect)

    # Prolungamenti
    if intersection is not None:
        ax.plot([pos_sx[0], intersection[0]], [pos_sx[1], intersection[1]], color='red', linestyle='--', lw=1.2, alpha=0.3, zorder=3)
        ax.plot([pos_dx[0], intersection[0]], [pos_dx[1], intersection[1]], color='green', linestyle='--', lw=1.2, alpha=0.3, zorder=3)

    # Vettori
    scale = 0.4
    ax.arrow(pos_sx[0], pos_sx[1], u1*scale, v1*scale, head_width=1.2, fc='red', ec='red', width=0.25, zorder=6)
    ax.arrow(pos_dx[0], pos_dx[1], u2*scale, v2*scale, head_width=1.2, fc='green', ec='green', width=0.25, zorder=6)
    ax.arrow(origin_res[0], origin_res[1], res_u*scale, res_v*scale, head_width=2.0, fc='blue', ec='blue', width=0.6, alpha=0.4, zorder=4)

    ax.scatter(st.session_state.pp_x, st.session_state.pp_y, c='black', s=120, zorder=10)
    ax.set_xlim(-20, 20); ax.set_ylim(-25, 30); ax.set_aspect('equal'); ax.axis('off')
    st.pyplot(fig); plt.close(fig)
    
    # Dashboard
    if warning_interference: st.error("⚠️ INTERFERENZA: Spinta ridotta.")
    m1, m2, m3 = st.columns(3)
    m1.metric("Spinta", f"{res_ton:.1f} t")
    m2.metric("Direzione", f"{np.degrees(np.arctan2(res_u, res_v)) % 360:.0f}°")
    rot = "STABILE" if abs(Total_Moment_tm) < 2.0 else ("SINISTRA" if Total_Moment_tm > 0 else "DRITTA")
    m3.metric("Rotazione", rot, delta=f"{abs(Total_Moment_tm * G_ACCEL):.0f} kNm", delta_color="off")
