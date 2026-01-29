import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, PathPatch, Rectangle, Circle, Polygon, Arrow
from matplotlib.path import Path
from matplotlib.transforms import Affine2D
import time
from constants import *
from physics import *

st.set_page_config(page_title="ASD Centurion V7.1", layout="wide")

# CSS Personalizzato V6.62
st.markdown("""
<style>
    [data-testid="stMetricValue"] {
        font-size: 1.8rem !important;
        overflow-wrap: break-word;
        white-space: normal;
    }
</style>
""", unsafe_allow_html=True)

# --- INIZIALIZZAZIONE ---
if "physics" not in st.session_state:
    st.session_state.physics = PhysicsEngine()
    st.session_state.last_time = time.time()
    st.session_state.history_x = []
    st.session_state.history_y = []
    # Valori di default
    st.session_state.p1 = 50
    st.session_state.a1 = 0
    st.session_state.p2 = 50
    st.session_state.a2 = 0

# --- FUNZIONI UTILITY (Visualizzazione) ---
def plot_clock(azimuth_deg, color):
    fig, ax = plt.subplots(figsize=(2.2, 2.2), subplot_kw={'projection': 'polar'})
    ax.set_theta_zero_location('N')
    ax.set_theta_direction(-1) # Senso Orario per la bussola
    ax.set_yticks([]); ax.set_xticks(np.radians([0, 90, 180, 270]))
    
    rad = np.radians(azimuth_deg)
    ax.arrow(rad, 0, 0, 0.9, width=0.1, head_width=0.3, head_length=0.2, fc=color, ec='black')
    fig.patch.set_alpha(0)
    return fig

# --- FUNZIONI DI MANOVRA (Preset V6.62) ---
def set_engine_state(p1, a1, p2, a2):
    st.session_state.p1, st.session_state.a1 = p1, a1
    st.session_state.p2, st.session_state.a2 = p2, a2

def reset_simulation():
    set_engine_state(50, 0, 50, 0)
    st.session_state.physics.reset()
    st.session_state.history_x = []
    st.session_state.history_y = []

def apply_fast_side_step(direction):
    if direction == "DRITTA": # Verso destra
        # DX spinge, SX insegue
        set_engine_state(50, 45, 50, 325) # Approx geometrico rapido
    else:
        set_engine_state(50, 315, 50, 35)

def apply_slow_side_step(direction):
    if direction == "DRITTA": # V7.1 Richiesta specifica (170/10)
        set_engine_state(50, 10, 50, 170)
    else:
        set_engine_state(50, 350, 50, 190)

def apply_turn_on_the_spot(direction):
    if direction == "DRITTA": # CW
        set_engine_state(50, 330, 50, 210) # V7.1 Preset
    else: # CCW
        set_engine_state(50, 30, 50, 150)

# --- HEADER ---
st.markdown("<h1 style='text-align: center;'>⚓ ASD Centurion V7.1 ⚓</h1>", unsafe_allow_html=True)
st.markdown("<div style='text-align: center;'><b>Auto Pivot & Dynamics</b></div>", unsafe_allow_html=True)
st.write("---")

# --- SIDEBAR ---
with st.sidebar:
    st.header("Comandi Globali")
    if st.button("Reset Totale", type="primary", use_container_width=True):
        reset_simulation()
    
    st.markdown("---")
    # IL CHECKBOX CRITICO
    simulate_motion = st.checkbox("Attiva Simulazione Movimento", value=False)
    show_wash = st.checkbox("Visualizza Scia (Wash)", value=True)
    
    st.markdown("---")
    st.markdown("### ↕️ Longitudinali")
    c1, c2 = st.columns(2)
    c1.button("⬆️ Avanti", on_click=set_engine_state, args=(80,0,80,0), use_container_width=True)
    c2.button("⬇️ Indietro", on_click=set_engine_state, args=(80,180,80,180), use_container_width=True)
    
    st.markdown("### ↔️ Trasversali")
    r1, r2 = st.columns(2)
    r1.button("⬅️ Slow SX", on_click=apply_slow_side_step, args=("SINISTRA",), use_container_width=True)
    r2.button("➡️ Slow DX", on_click=apply_slow_side_step, args=("DRITTA",), use_container_width=True)
    
    st.markdown("### 🔄 Rotazione")
    t1, t2 = st.columns(2)
    t1.button("🔄 Ruota SX", on_click=apply_turn_on_the_spot, args=("SINISTRA",), use_container_width=True)
    t2.button("🔄 Ruota DX", on_click=apply_turn_on_the_spot, args=("DRITTA",), use_container_width=True)

# --- LAYOUT PRINCIPALE ---
col_l, col_c, col_r = st.columns([1.2, 2.6, 1.2])

with col_l:
    st.slider("Potenza SX", 0, 100, key="p1")
    st.slider("Azimuth SX", 0, 360, key="a1")
    st.pyplot(plot_clock(st.session_state.a1, 'red'))

with col_r:
    st.slider("Potenza DX", 0, 100, key="p2")
    st.slider("Azimuth DX", 0, 360, key="a2")
    st.pyplot(plot_clock(st.session_state.a2, 'green'))

# --- LOGICA SIMULAZIONE ---
if simulate_motion:
    # Calcolo DT
    current_time = time.time()
    dt = current_time - st.session_state.last_time
    st.session_state.last_time = current_time
    if dt > 0.1: dt = 0.1

    # Conversione Input
    thrust_l = (st.session_state.p1 / 100.0) * MAX_THRUST
    thrust_r = (st.session_state.p2 / 100.0) * MAX_THRUST
    
    # Update Fisica
    st.session_state.physics.update(dt, thrust_l, st.session_state.a1, thrust_r, st.session_state.a2)
    
    # Store History
    state = st.session_state.physics.state
    st.session_state.history_x.append(state[0])
    st.session_state.history_y.append(state[1])
    if len(st.session_state.history_x) > 300:
        st.session_state.history_x.pop(0)
        st.session_state.history_y.pop(0)
else:
    # Se fermo, resetta la posizione visiva al centro ma mantieni gli input
    st.session_state.physics.reset() # Reset velocità/posizione
    # Calcoliamo comunque il Pivot Point staticamente per mostrarlo
    dummy_phys = PhysicsEngine()
    thrust_l = (st.session_state.p1 / 100.0) * MAX_THRUST
    thrust_r = (st.session_state.p2 / 100.0) * MAX_THRUST
    st.session_state.physics.calculate_dynamic_pivot(thrust_l, st.session_state.a1, thrust_r, st.session_state.a2)


# --- VISUALIZZAZIONE CENTRALE ---
with col_c:
    # Info Pivot (Sostituisce gli slider manuali rimossi)
    curr_pp_y = st.session_state.physics.current_pp_y
    mode_str = st.session_state.physics.pivot_mode
    st.info(f"📍 Auto-Pivot: {curr_pp_y:.1f}m ({mode_str})")

    fig, ax = plt.subplots(figsize=(10, 12))
    ax.set_facecolor('#141E28')
    
    state = st.session_state.physics.state
    cx, cy = state[0], state[1]
    
    # Viewport
    window = 60
    if not simulate_motion: window = 40
    ax.set_xlim(cx - window, cx + window)
    ax.set_ylim(cy - window, cy + window)
    ax.set_aspect('equal')
    ax.grid(True, color='#2A3B4C', linestyle='--', alpha=0.5)

    # Scia Movimento
    if simulate_motion and len(st.session_state.history_x) > 1:
        ax.plot(st.session_state.history_x, st.session_state.history_y, color='#64C8FF', linewidth=1.5, alpha=0.6)

    # Trasformazione Nave
    # Nota sui segni: physics usa CCW+. Matplotlib rotate usa CCW+.
    # Ma se 0=Nord, dobbiamo ruotare di -angle se angle cresce CCW da Est?
    # physics: state[2] cresce CCW. 0=Nord (per come abbiamo definito dx/dy).
    # Matplotlib standard: 0=Est.
    # Quindi per allineare: rotazione = state[2] + 90 gradi?
    # Proviamo: angle -state[2] (invertito per visualizzazione nautica)
    
    # FIX VISUALIZZAZIONE:
    # Physics ha calcolato x_dot con sin(psi) e y_dot con cos(psi). -> 0 è Nord.
    # Matplotlib 0 è Est.
    # Quindi Heading Matplotlib = Physics_Heading + 90.
    draw_angle = np.degrees(state[2]) + 90
    
    tr = Affine2D().rotate_deg(draw_angle).translate(cx, cy) + ax.transData

    # Scafo
    hull = Rectangle((-SHIP_WIDTH/2, -SHIP_LENGTH/2), SHIP_WIDTH, SHIP_LENGTH, color='#464646', zorder=2)
    hull.set_transform(tr)
    ax.add_patch(hull)
    
    # Prua (Skeg)
    bow = Polygon([(-SHIP_WIDTH/2, SHIP_LENGTH/2), (SHIP_WIDTH/2, SHIP_LENGTH/2), (0, SHIP_LENGTH/2 + 4)], color='#505050', zorder=2)
    bow.set_transform(tr)
    ax.add_patch(bow)
    
    # Propulsori (Vettori)
    def draw_thruster_vec(x_loc, y_loc, angle, power, color):
        if power < 1: return
        length = (power/100)*15
        rad = np.radians(angle)
        # 0=Nord
        dx = length * np.sin(rad)
        dy = length * np.cos(rad)
        
        # Disegna la freccia della forza
        arr = Arrow(x_loc, y_loc, dx, dy, width=2, color=color, zorder=5)
        arr.set_transform(tr)
        ax.add_patch(arr)
        
        # Scia Propulsore (Wash)
        if show_wash:
            wash_len = length * 1.5
            w_dx = -dx * 1.5
            w_dy = -dy * 1.5
            wash = Arrow(x_loc, y_loc, w_dx, w_dy, width=4, color='cyan', alpha=0.3, zorder=1)
            wash.set_transform(tr)
            ax.add_patch(wash)

    draw_thruster_vec(-THRUSTER_X_OFFSET, THRUSTER_Y_OFFSET, st.session_state.a1, st.session_state.p1, 'red')
    draw_thruster_vec(THRUSTER_X_OFFSET, THRUSTER_Y_OFFSET, st.session_state.a2, st.session_state.p2, 'green')

    # Pivot Point
    pp = Circle((0, curr_pp_y), radius=0.8, color='yellow', zorder=10)
    pp.set_transform(tr)
    ax.add_patch(pp)

    # Telemetria Overlay
    if simulate_motion:
        sog = np.sqrt(state[3]**2 + state[4]**2) * 1.94
        rot = np.degrees(state[5])
        ax.text(cx - window + 2, cy + window - 5, 
                f"SOG: {sog:.1f} kn\nROT: {rot:.1f} °/s\nPP: {curr_pp_y:.1f}m", 
                color="white", fontsize=12, bbox=dict(facecolor='black', alpha=0.5))
    else:
        ax.text(cx - window + 2, cy + window - 5, "SIMULAZIONE FERMA\nAttiva checkbox per muovere", 
                color="orange", fontsize=12, bbox=dict(facecolor='black', alpha=0.5))

    ax.axis('off')
    st.pyplot(fig)

    if simulate_motion:
        time.sleep(0.05)
        st.rerun()

# --- DATI TABELLARI ---
st.write("---")
st.subheader("Dati Ingegneristici")
c1, c2, c3 = st.columns(3)
c1.metric("Spinta SX", f"{(st.session_state.p1/100)*BOLLARD_PULL_PER_ENGINE:.1f} t")
c2.metric("Spinta DX", f"{(st.session_state.p2/100)*BOLLARD_PULL_PER_ENGINE:.1f} t")
c3.metric("Pivot Logic", mode_str)
