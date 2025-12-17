import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import PathPatch, FancyArrowPatch
from matplotlib.path import Path

# --- CONFIGURAZIONE PAGINA ---
st.set_page_config(page_title="ASD Centurion V5.25", layout="wide")

# --- COSTANTI FISICHE ---
G_ACCEL = 9.80665
POS_THRUSTERS_Y = -12.0
POS_THRUSTERS_X = 2.7
BOLLARD_PULL_PER_ENGINE = 35.0

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
    st.session_state.p1, st.session_state.a1 = 50, 0
    st.session_state.p2, st.session_state.a2 = 50, 0

def reset_pivot():
    st.session_state.pp_x, st.session_state.pp_y = 0.0, 5.42

# --- 1. SOLUTORE SLOW SIDE STEP (GEOMETRICO) ---
def apply_slow_side_step(direction):
    pp_y = st.session_state.pp_y
    longitudinal_dist = pp_y - POS_THRUSTERS_Y
    try:
        alpha_deg = np.degrees(np.arctan2(POS_THRUSTERS_X, longitudinal_dist))
        if direction == "DRITTA":
            a1_set, a2_set = alpha_deg, 180 - alpha_deg
        else:
            a1_set, a2_set = 180 + alpha_deg, 360 - alpha_deg
        set_engine_state(50, int(round(a1_set % 360)), 50, int(round(a2_set % 360)))
    except Exception as e:
        st.error(f"Errore Slow: {e}")

# --- 2. SOLUTORE FAST SIDE STEP (LOGICA RIGIDA) ---
def apply_fast_side_step(direction):
    pp_y = st.session_state.pp_y
    dist_y = pp_y - POS_THRUSTERS_Y
    
    if direction == "DRITTA":
        a_drive, p_drive = 45.0, 50.0
        x_drive, x_slave = -POS_THRUSTERS_X, POS_THRUSTERS_X
        x_int = x_drive + dist_y * np.tan(np.radians(a_drive))
        dx, dy = x_slave - x_int, POS_THRUSTERS_Y - pp_y
        a_slave = np.degrees(np.arctan2(dx, dy)) % 360
        cos_drive, cos_slave = np.cos(np.radians(a_drive)), np.cos(np.radians(a_slave))
        
        if abs(cos_slave) < 0.001:
            st.error("❌ Geometria impossibile: divisione per zero."); return
        
        p_slave = -(p_drive * cos_drive) / cos_slave
        
        if 0 <= p_slave <= 100:
            st.session_state.p1, st.session_state.a1 = int(p_drive), int(a_drive)
            st.session_state.p2, st.session_state.a2 = int(round(p_slave)), int(round(a_slave))
            st.toast(f"Fast Dritta: Slave {int(round(p_slave))}%", icon="⚡")
        else:
            st.error(f"❌ Nessuna soluzione reale: Potenza DX calcolata ({p_slave:.1f}%) fuori range 0-100.")

    else: # SINISTRA
        a_drive, p_drive = 315.0, 50.0
        x_drive, x_slave = POS_THRUSTERS_X, -POS_THRUSTERS_X
        x_int = x_drive + dist_y * np.tan(np.radians(a_drive))
        dx, dy = x_slave - x_int, POS_THRUSTERS_Y - pp_y
        a_slave = np.degrees(np.arctan2(dx, dy)) % 360
        cos_drive, cos_slave = np.cos(np.radians(a_drive)), np.cos(np.radians(a_slave))
        
        if abs(cos_slave) < 0.001:
            st.error("❌ Geometria impossibile."); return
        
        p_slave = -(p_drive * cos_drive) / cos_slave
        
        if 0 <= p_slave <= 100:
            st.session_state.p2, st.session_state.a2 = int(p_drive), int(a_drive)
            st.session_state.p1, st.session_state.a1 = int(round(p_slave)), int(round(a_slave))
            st.toast(f"Fast Sinistra: Slave {int(round(p_slave))}%", icon="⚡")
        else:
            st.error(f"❌ Nessuna soluzione reale: Potenza SX calcolata ({p_slave:.1f}%) fuori range 0-100.")

# --- CALCOLI FISICI ---
pos_sx = np.array([-POS_THRUSTERS_X, POS_THRUSTERS_Y])
pos_dx = np.array([POS_THRUSTERS_X, POS_THRUSTERS_Y])
pp_pos = np.array([st.session_state.pp_x, st.session_state.pp_y])

ton1 = (st.session_state.p1 / 100) * BOLLARD_PULL_PER_ENGINE
ton2 = (st.session_state.p2 / 100) * BOLLARD_PULL_PER_ENGINE

u1, v1 = ton1 * np.sin(np.radians(st.session_state.a1)), ton1 * np.cos(np.radians(st.session_state.a1))
u2, v2 = ton2 * np.sin(np.radians(st.session_state.a2)), ton2 * np.cos(np.radians(st.session_state.a2))

F_sx, F_dx = np.array([u1, v1]), np.array([u2, v2])

# Funzione per trovare l'intersezione reale dei flussi
def get_intersection(p1, a1, p2, a2):
    th1, th2 = np.radians(90-a1), np.radians(90-a2)
    v1_vec = np.array([np.cos(th1), np.sin(th1)])
    v2_vec = np.array([np.cos(th2), np.sin(th2)])
    det = v1_vec[0]*(-v2_vec[1]) - (-v2_vec[0])*v1_vec[1]
    if abs(det) < 1e-3: return None
    t = ((p2[0]-p1[0])*(-v2_vec[1]) - (-v2_vec[0])*(p2[1]-p1[1])) / det
    return p1 + t * v1_vec

inter_pt = get_intersection(pos_sx, st.session_state.a1, pos_dx, st.session_state.a2)
origin_res = inter_pt if inter_pt is not None else np.array([0.0, -12.0])

res_u, res_v = u1 + u2, v1 + v2
res_ton = np.sqrt(res_u**2 + res_v**2)

# Momenti
M_sx = (pos_sx[0] - pp_pos[0]) * v1 - (pos_sx[1] - pp_pos[1]) * u1
M_dx = (pos_dx[0] - pp_pos[0]) * v2 - (pos_dx[1] - pp_pos[1]) * u2
Total_Moment_tm = M_sx + M_dx

# --- LAYOUT ---
st.markdown("<h1 style='text-align: center;'>⚓ ASD Centurion V5.25</h1>", unsafe_allow_html=True)

with st.sidebar:
    st.header("Comandi Globali")
    if st.button("Reset Totale", type="primary", use_container_width=True):
        reset_engines(); reset_pivot()
    st.markdown("---")
    st.markdown("### ↔️ Side Step")
    c1, c2 = st.columns(2)
    c1.button("⬅️ Fast SX", on_click=apply_fast_side_step, args=("SINISTRA",), use_container_width=True)
    c2.button("➡️ Fast DX", on_click=apply_fast_side_step, args=("DRITTA",), use_container_width=True)
    st.markdown("---")
    c3, c4 = st.columns(2)
    c3.button("⬅️ Slow SX", on_click=apply_slow_side_step, args=("SINISTRA",), use_container_width=True)
    c4.button("➡️ Slow DX", on_click=apply_slow_side_step, args=("DRITTA",), use_container_width=True)

col_sx, col_center, col_dx = st.columns([1, 2, 1], gap="medium")

with col_sx:
    st.markdown("### PORT (SX)")
    st.slider("Potenza SX (%)", 0, 100, step=1, key="p1")
    st.slider("Azimut SX (°)", 0, 360, step=1, key="a1")

with col_dx:
    st.markdown("### STBD (DX)")
    st.slider("Potenza DX (%)", 0, 100, step=1, key="p2")
    st.slider("Azimut DX (°)", 0, 360, step=1, key="a2")

with col_center:
    st.slider("Pivot Point Y", -16.0, 16.0, step=0.1, key="pp_y")
    
    fig, ax = plt.subplots(figsize=(7, 9))
    hw, stern, bow = 5.85, -16.25, 16.25
    rect = plt.Rectangle((-hw, stern), hw*2, bow-stern, color='#dddddd', edgecolor='#333333', lw=2, zorder=1)
    ax.add_patch(rect)
    
    # Pivot Point
    ax.scatter(st.session_state.pp_x, st.session_state.pp_y, c='black', s=150, zorder=10)
    ax.text(st.session_state.pp_x+0.8, st.session_state.pp_y, "PIVOT", fontweight='bold')

    # TRATTEGGI DI PROIEZIONE
    if inter_pt is not None and abs(inter_pt[1]) < 60:
        ax.plot([pos_sx[0], inter_pt[0]], [pos_sx[1], inter_pt[1]], color='red', linestyle='--', lw=0.8, alpha=0.5)
        ax.plot([pos_dx[0], inter_pt[0]], [pos_dx[1], inter_pt[1]], color='green', linestyle='--', lw=0.8, alpha=0.5)

    # VETTORI
    sc = 0.4
    ax.arrow(pos_sx[0], pos_sx[1], u1*sc, v1*sc, head_width=1, fc='red', ec='red', zorder=5)
    ax.arrow(pos_dx[0], pos_dx[1], u2*sc, v2*sc, head_width=1, fc='green', ec='green', zorder=5)
    
    # VETTORE RISULTANTE (Ancorato all'intersezione)
    if res_ton > 0.1:
        ax.arrow(origin_res[0], origin_res[1], res_u*sc, res_v*sc, head_width=1.5, fc='blue', ec='blue', alpha=0.6, zorder=4, width=0.4)

    ax.set_xlim(-22, 22); ax.set_ylim(-25, 25); ax.set_aspect('equal'); ax.axis('off')
    st.pyplot(fig); plt.close(fig)

    # Dashboard
    m1, m2, m3 = st.columns(3)
    m1.metric("Tiro Totale", f"{res_ton:.1f} t")
    m2.metric("Direzione", f"{np.degrees(np.arctan2(res_u, res_v))%360:.0f}°")
    m3.metric("Momento", f"{Total_Moment_tm:.1f} tm")
