import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import PathPatch, FancyArrowPatch
from matplotlib.path import Path

# --- CONFIGURAZIONE PAGINA ---
st.set_page_config(page_title="ASD Centurion V5.35", layout="wide")

# --- COSTANTI FISICHE ---
G_ACCEL = 9.80665  
POS_THRUSTERS_Y = -12.0
POS_THRUSTERS_X = 2.7
BOLLARD_PULL_PER_ENGINE = 35.0 

# --- GESTIONE SESSION STATE ---
if "p1" not in st.session_state:
    st.session_state.update({
        "p1": 50, "a1": 0,
        "p2": 50, "a2": 0,
        "pp_x": 0.0, "pp_y": 5.42
    })

# --- FUNZIONI DI GESTIONE STATO ---
def set_engine_state(p1, a1, p2, a2):
    st.session_state.p1, st.session_state.a1 = p1, a1
    st.session_state.p2, st.session_state.a2 = p2, a2

def reset_engines():
    set_engine_state(50, 0, 50, 0)

def reset_pivot():
    st.session_state.pp_x, st.session_state.pp_y = 0.0, 5.42

# --- SOLUTORI SIDE STEP ---
def apply_slow_side_step(direction):
    dist_long = st.session_state.pp_y - POS_THRUSTERS_Y
    alpha_deg = np.degrees(np.arctan2(POS_THRUSTERS_X, dist_long))
    if direction == "DRITTA":
        set_engine_state(50, int(alpha_deg % 360), 50, int((180 - alpha_deg) % 360))
    else:
        set_engine_state(50, int((180 + alpha_deg) % 360), 50, int((360 - alpha_deg) % 360))

def apply_fast_side_step(direction):
    dist_y = st.session_state.pp_y - POS_THRUSTERS_Y
    if direction == "DRITTA":
        a_drive, p_drive = 45.0, 50.0
        x_int = -POS_THRUSTERS_X + dist_y * np.tan(np.radians(a_drive))
        a_slave = np.degrees(np.arctan2(POS_THRUSTERS_X - x_int, POS_THRUSTERS_Y - st.session_state.pp_y)) % 360
        p_slave = -(p_drive * np.cos(np.radians(a_drive))) / np.cos(np.radians(a_slave))
        set_engine_state(int(p_drive), int(a_drive), int(round(p_slave)), int(round(a_slave)))
    else:
        a_drive, p_drive = 315.0, 50.0
        x_int = POS_THRUSTERS_X + dist_y * np.tan(np.radians(a_drive))
        a_slave = np.degrees(np.arctan2(-POS_THRUSTERS_X - x_int, POS_THRUSTERS_Y - st.session_state.pp_y)) % 360
        p_slave = -(p_drive * np.cos(np.radians(a_drive))) / np.cos(np.radians(a_slave))
        set_engine_state(int(round(p_slave)), int(round(a_slave)), int(p_drive), int(a_drive))

# --- HEADER ---
st.markdown("<h1 style='text-align: center;'>⚓ ASD 'CENTURION' Simulatore</h1>", unsafe_allow_html=True)
st.write("---")

# --- SIDEBAR ---
with st.sidebar:
    st.header("Comandi Globali")
    c1, c2 = st.columns(2)
    c1.button("Reset Motori", on_click=reset_engines, type="primary", use_container_width=True)
    c2.button("Reset Pivot", on_click=reset_pivot, use_container_width=True)
    
    st.markdown("### ↕️ Longitudinali")
    f1, f2 = st.columns(2)
    f1.button("AVANTI", on_click=set_engine_state, args=(50, 0, 50, 0), use_container_width=True)
    f2.button("INDIETRO", on_click=set_engine_state, args=(50, 180, 50, 180), use_container_width=True)

    st.markdown("### ↔️ Side Step")
    s1, s2 = st.columns(2)
    s1.button("⬅️ Fast SX", on_click=apply_fast_side_step, args=("SINISTRA",), use_container_width=True)
    s2.button("➡️ Fast DX", on_click=apply_fast_side_step, args=("DRITTA",), use_container_width=True)
    s3, s4 = st.columns(2)
    s3.button("⬅️ Slow SX", on_click=apply_slow_side_step, args=("SINISTRA",), use_container_width=True)
    s4.button("➡️ Slow DX", on_click=apply_slow_side_step, args=("DRITTA",), use_container_width=True)

# --- CALCOLI ---
pos_sx = np.array([-POS_THRUSTERS_X, POS_THRUSTERS_Y])
pos_dx = np.array([POS_THRUSTERS_X, POS_THRUSTERS_Y])
pp_pos = np.array([st.session_state.pp_x, st.session_state.pp_y])

ton1 = (st.session_state.p1 / 100) * BOLLARD_PULL_PER_ENGINE
ton2 = (st.session_state.p2 / 100) * BOLLARD_PULL_PER_ENGINE
rad1, rad2 = np.radians(st.session_state.a1), np.radians(st.session_state.a2)

F_sx = np.array([ton1 * np.sin(rad1), ton1 * np.cos(rad1)])
F_dx = np.array([ton2 * np.sin(rad2), ton2 * np.cos(rad2)])

# Intersezione (Punto di origine della risultante)
def intersect_lines(p1, a_deg1, p2, a_deg2):
    t1, t2 = np.radians(90-a_deg1), np.radians(90-a_deg2)
    v1, v2 = np.array([np.cos(t1), np.sin(t1)]), np.array([np.cos(t2), np.sin(t2)])
    m = np.column_stack((v1, -v2))
    if abs(np.linalg.det(m)) < 1e-3: return None
    try: return p1 + np.linalg.solve(m, p2 - p1)[0] * v1
    except: return None

intersection = intersect_lines(pos_sx, st.session_state.a1, pos_dx, st.session_state.a2) if (ton1 > 0.5 and ton2 > 0.5) else None
origin_res = intersection if intersection is not None else np.array([(ton1*pos_sx[0]+ton2*pos_dx[0])/(ton1+ton2+1e-6), -12.0])

# Risultante e Momento
res_vec = F_sx + F_dx
res_ton = np.linalg.norm(res_vec)
Total_Moment_tm = (np.cross(pos_sx - pp_pos, F_sx) + np.cross(pos_dx - pp_pos, F_dx))

# --- GRAFICA ---
col_sx, col_main, col_dx = st.columns([1, 2, 1])

with col_sx:
    st.slider("Potenza SX", 0, 100, key="p1")
    st.slider("Azimut SX", 0, 360, key="a1")
    st.metric("Spinta SX", f"{ton1:.1f} t")

with col_dx:
    st.slider("Potenza DX", 0, 100, key="p2")
    st.slider("Azimut DX", 0, 360, key="a2")
    st.metric("Spinta DX", f"{ton2:.1f} t")

with col_main:
    with st.expander("📍 Pivot Point"):
        st.slider("Y (Longitudinale)", -16.0, 16.0, key="pp_y")
        st.slider("X (Trasversale)", -5.0, 5.0, key="pp_x")

    fig, ax = plt.subplots(figsize=(7, 9))
    # Scafo
    hw, s, b, sh = 5.85, -16.25, 16.25, 8.0
    hull = Path([(-hw,s),(hw,s),(hw,sh),(hw,14),(4,b),(0,b),(-4,b),(-hw,14),(-hw,sh),(-hw,s)], 
                [1,2,2,4,4,4,4,4,2,2])
    ax.add_patch(PathPatch(hull, facecolor='#ddd', edgecolor='#555', lw=2))
    
    # --- MODIFICA RICHIESTA: LINEE D'AZIONE ALL'INTERSEZIONE ---
    if intersection is not None:
        # Linea SX -> Intersezione
        ax.plot([pos_sx[0], intersection[0]], [pos_sx[1], intersection[1]], 
                color='red', linestyle='--', lw=1.5, alpha=0.4, zorder=2)
        # Linea DX -> Intersezione
        ax.plot([pos_dx[0], intersection[0]], [pos_dx[1], intersection[1]], 
                color='green', linestyle='--', lw=1.5, alpha=0.4, zorder=2)
        # Punto di incrocio
        ax.scatter(intersection[0], intersection[1], color='blue', s=30, marker='o', alpha=0.6, zorder=5)

    # Disegno Vettori (Scala 0.4)
    sc = 0.4
    ax.arrow(pos_sx[0], pos_sx[1], F_sx[0]*sc, F_sx[1]*sc, head_width=1, fc='red', ec='red', alpha=0.9, zorder=4)
    ax.arrow(pos_dx[0], pos_dx[1], F_dx[0]*sc, F_dx[1]*sc, head_width=1, fc='green', ec='green', alpha=0.9, zorder=4)
    ax.arrow(origin_res[0], origin_res[1], res_vec[0]*sc, res_vec[1]*sc, head_width=1.5, fc='blue', ec='blue', alpha=0.5, zorder=4)
    
    ax.scatter(st.session_state.pp_x, st.session_state.pp_y, c='black', s=100, zorder=10)
    ax.set_xlim(-20, 20); ax.set_ylim(-25, 30); ax.set_aspect('equal'); ax.axis('off')
    st.pyplot(fig); plt.close(fig)

    # Dashboard
    m1, m2, m3 = st.columns(3)
    m1.metric("Spinta Totale", f"{res_ton:.1f} t")
    m2.metric("Direzione", f"{np.degrees(np.arctan2(res_vec[0], res_vec[1])) % 360:.0f}°")
    rot = "STABILE" if abs(Total_Moment_tm) < 2 else ("SINISTRA" if Total_Moment_tm > 0 else "DRITTA")
    m3.metric("Rotazione", rot, delta=f"{abs(Total_Moment_tm * G_ACCEL):.0f} kNm")
