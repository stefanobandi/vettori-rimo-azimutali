import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.transforms import Affine2D
import time
from physics import PhysicsEngine
from constants import *

# Inizializzazione Sessione
if 'physics' not in st.session_state:
    st.session_state.physics = PhysicsEngine()
    st.session_state.last_time = time.time()
    st.session_state.history_x = []
    st.session_state.history_y = []

st.set_page_config(layout="wide", page_title="ASD Physics Check")

st.title("⚓ ASD Centurion: Manual Physics Check")
st.markdown("**Verifica Fisica:** Logica Pivot Dinamico (Skeg vs Force Mix)")

col_controls, col_viz = st.columns([1, 2])

with col_controls:
    st.subheader("⚙️ Comandi Manuali")
    
    # Rimosso il selettore preset per focus manuale assoluto
    st.info("Usa gli slider per testare la risposta fisica.")

    col_p1, col_p2 = st.columns(2)
    with col_p1:
        st.write("**Port (SX)**")
        p_l = st.slider("Power %", 0, 100, 0, key="pl")
        a_l = st.slider("Angle °", 0, 360, 0, step=10, key="al")
    with col_p2:
        st.write("**Stbd (DX)**")
        p_r = st.slider("Power %", 0, 100, 0, key="pr")
        a_r = st.slider("Angle °", 0, 360, 0, step=10, key="ar")

    if st.button("Reset Totale"):
        st.session_state.physics = PhysicsEngine()
        st.session_state.history_x = []
        st.session_state.history_y = []

# --- LOOP FISICO ---
current_time = time.time()
dt = current_time - st.session_state.last_time
st.session_state.last_time = current_time
if dt > 0.1: dt = 0.1

thrust_l_newton = (p_l / 100.0) * MAX_THRUST
thrust_r_newton = (p_r / 100.0) * MAX_THRUST

# Update
st.session_state.physics.update(dt, thrust_l_newton, a_l, thrust_r_newton, a_r)

# Recupera dati per UI
state = st.session_state.physics.state
pp_y = st.session_state.physics.current_pp_y
mode = st.session_state.physics.pivot_mode

# Traccia
st.session_state.history_x.append(state[0])
st.session_state.history_y.append(state[1])
if len(st.session_state.history_x) > 500:
    st.session_state.history_x.pop(0)
    st.session_state.history_y.pop(0)

# --- VISUALIZZAZIONE ---
with col_viz:
    fig, ax = plt.subplots(figsize=(10, 10))
    ax.set_facecolor('#141E28')
    
    cx, cy = state[0], state[1]
    window = 80
    ax.set_xlim(cx - window, cx + window)
    ax.set_ylim(cy - window, cy + window)
    ax.set_aspect('equal')
    ax.grid(True, color='#2A3B4C', linestyle='--', alpha=0.5)

    # Scia azzurra
    ax.plot(st.session_state.history_x, st.session_state.history_y, color='#64C8FF', linewidth=1, alpha=0.6)

    # Matrice Trasformazione Nave
    tr = Affine2D().rotate(-state[2]).translate(cx, cy) + ax.transData

    # Corpo Nave
    hull = patches.Rectangle((-SHIP_WIDTH/2, -SHIP_LENGTH/2), SHIP_WIDTH, SHIP_LENGTH, color='#464646', zorder=2)
    hull.set_transform(tr)
    ax.add_patch(hull)
    
    # Prua
    bow = patches.Polygon([(-SHIP_WIDTH/2, SHIP_LENGTH/2), (SHIP_WIDTH/2, SHIP_LENGTH/2), (0, SHIP_LENGTH/2 + 4)], color='#505050', zorder=2)
    bow.set_transform(tr)
    ax.add_patch(bow)

    # Disegna Skeg (Area Blu a Prua - Visual Reference)
    skeg_area = patches.Rectangle((-0.5, POS_SKEG_Y-1), 1, 2, color='blue', alpha=0.5, zorder=3)
    skeg_area.set_transform(tr)
    ax.add_patch(skeg_area)

    # Vettori Propulsori
    def draw_thruster(x_local, y_local, angle_deg, thrust_pct, color):
        if thrust_pct == 0: return
        vec_len = (thrust_pct / 100.0) * 15
        angle_rad = np.radians(angle_deg)
        # In matplotlib arrow, dx/dy sono offsets
        dx = vec_len * np.sin(angle_rad)
        dy = vec_len * np.cos(angle_rad)
        arrow = patches.Arrow(x_local, y_local, dx, dy, width=2, color=color, zorder=4)
        arrow.set_transform(tr)
        ax.add_patch(arrow)

    draw_thruster(-THRUSTER_X_OFFSET, THRUSTER_Y_OFFSET, a_l, p_l, '#FF3232')
    draw_thruster(THRUSTER_X_OFFSET, THRUSTER_Y_OFFSET, a_r, p_r, '#32FF32')

    # PIVOT POINT MARKER (Giallo)
    # Questo è il punto che si muove in base alla logica
    pp_marker = patches.Circle((0, pp_y), radius=0.8, color='#FFFF00', zorder=5)
    pp_marker.set_transform(tr)
    ax.add_patch(pp_marker)

    # DATI IN SOVRAIMPRESSIONE
    sog_kn = np.sqrt(state[3]**2 + state[4]**2) * 1.94
    info_text = (
        f"SOG: {sog_kn:.1f} kn\n"
        f"HDG: {np.degrees(state[2]):.1f}°\n"
        f"ROT: {np.degrees(state[5]):.2f} °/s\n\n"
        f"PIVOT Y: {pp_y:.1f} m\n"
        f"LOGIC: {mode}"
    )
    ax.text(cx - window + 5, cy + window - 5, info_text, 
            color='white', fontsize=11, family='monospace', 
            bbox=dict(facecolor='black', alpha=0.6))

    st.pyplot(fig)
    time.sleep(0.05)
    st.rerun()
