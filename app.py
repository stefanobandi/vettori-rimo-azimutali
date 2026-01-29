import streamlit as st
import numpy as np
import time
from physics import calculate_physics_step, calculate_forces
from visualization import render_radar_view
from constants import DT

# --- CONFIGURAZIONE PAGINA ---
st.set_page_config(page_title="ASD Centurion V7.7", layout="wide")

# --- INIZIALIZZAZIONE SESSION STATE ---
if 'state' not in st.session_state:
    # [u, v, r, x, y, psi]
    st.session_state.state = np.zeros(6)
if 'history' not in st.session_state:
    st.session_state.history = []
if 'last_time' not in st.session_state:
    st.session_state.last_time = time.time()
if 'p1' not in st.session_state: st.session_state.p1 = 0
if 'a1' not in st.session_state: st.session_state.a1 = 0
if 'p2' not in st.session_state: st.session_state.p2 = 0
if 'a2' not in st.session_state: st.session_state.a2 = 0
# NUOVO: Zoom default a 80m
if 'zoom_level' not in st.session_state: 
    st.session_state.zoom_level = 80.0

# --- FUNZIONI DI UTILITY ---
def reset_simulation():
    st.session_state.state = np.zeros(6)
    st.session_state.history = []  # NUOVO: Cancella la scia storica
    st.session_state.p1 = 0
    st.session_state.p2 = 0
    st.session_state.a1 = 0
    st.session_state.a2 = 0

def update_zoom(delta):
    # Delta positivo = Zoom Out (aumenta raggio), Delta negativo = Zoom In
    new_zoom = st.session_state.zoom_level + delta
    if new_zoom < 20: new_zoom = 20
    if new_zoom > 300: new_zoom = 300
    st.session_state.zoom_level = new_zoom

def solve_fast_sidestep(direction):
    # Solver Matematico per Fast Sidestep (Momento nullo su Skeg)
    # Target: No avanzamento, No rotazione, Solo traslazione pura
    if direction == "left":
        # Master: SX a 145° / Slave: DX deve bilanciare
        st.session_state.p1 = 50
        st.session_state.a1 = 145
        st.session_state.p2 = 58  # Calcolato dal solver
        st.session_state.a2 = 315
    else: # right
        # Master: DX a 215° / Slave: SX deve bilanciare
        st.session_state.p2 = 50
        st.session_state.a2 = 215
        st.session_state.p1 = 58
        st.session_state.a1 = 45

# --- SIDEBAR ---
with st.sidebar:
    st.header("🎮 Controlli Nave")
    
    # Sezione Reset e Zoom
    st.subheader("Sistema")
    col_sys1, col_sys2, col_sys3 = st.columns([2, 1, 1])
    with col_sys1:
        st.button("⚠️ RESET SIM", on_click=reset_simulation, type="primary", use_container_width=True)
    with col_sys2:
        st.button("🔍+", on_click=update_zoom, args=(-10,), help="Zoom In (Avvicina)", use_container_width=True)
    with col_sys3:
        st.button("🔍-", on_click=update_zoom, args=(10,), help="Zoom Out (Allontana)", use_container_width=True)
    
    st.metric("Zoom Attuale", f"{int(st.session_state.zoom_level)} m")
    
    st.markdown("---")
    
    # Sezione Solver (Bottoni Rapidi)
    st.subheader("⚡ Smart Solvers")
    st.markdown("Autopilot vettoriale")
    
    c1, c2 = st.columns(2)
    with c1:
        st.button("🦀 Fast SX", on_click=solve_fast_sidestep, args=("left",), use_container_width=True)
        st.button("🐢 Slow SX", on_click=lambda: [st.session_state.update({'p1':50, 'a1':190, 'p2':50, 'a2':350})], use_container_width=True)
        st.button("🔄 Turn SX", on_click=lambda: [st.session_state.update({'p1':50, 'a1':150, 'p2':50, 'a2':30})], use_container_width=True)
    with c2:
        st.button("🦀 Fast DX", on_click=solve_fast_sidestep, args=("right",), use_container_width=True)
        st.button("🐢 Slow DX", on_click=lambda: [st.session_state.update({'p1':50, 'a1':10, 'p2':50, 'a2':170})], use_container_width=True)
        st.button("🔄 Turn DX", on_click=lambda: [st.session_state.update({'p1':50, 'a1':330, 'p2':50, 'a2':210})], use_container_width=True)

    st.markdown("---")
    st.markdown("### ⚙️ Motori Manuali")
    
    # Controlli Manuali
    st.session_state.p1 = st.slider("Port Power %", 0, 100, st.session_state.p1)
    st.session_state.a1 = st.slider("Port Azimuth", 0, 360, st.session_state.a1)
    
    st.session_state.p2 = st.slider("Stbd Power %", 0, 100, st.session_state.p2)
    st.session_state.a2 = st.slider("Stbd Azimuth", 0, 360, st.session_state.a2)

# --- LOOP DI SIMULAZIONE ---
# Calcolo dt reale per fluidità
current_time = time.time()
real_dt = current_time - st.session_state.last_time
st.session_state.last_time = current_time

# Limite fisico del time step per stabilità numerica
sim_dt = min(real_dt, 0.1) 

# Step Fisico
new_state = calculate_physics_step(
    st.session_state.state,
    st.session_state.p1, st.session_state.a1,
    st.session_state.p2, st.session_state.a2,
    DT  # Usiamo DT fisso da costanti per coerenza fisica, oppure sim_dt per real-time
)
st.session_state.state = new_state

# Aggiornamento Storico (ogni 5 frame circa per performance o sempre)
st.session_state.history.append(new_state[3:5])
if len(st.session_state.history) > 500: # Taglia la coda se troppo lunga
    st.session_state.history.pop(0)

# --- LAYOUT PRINCIPALE ---
col_main, col_data = st.columns([3, 1])

with col_main:
    # Render Radar View (Passiamo lo zoom dinamico)
    fig = render_radar_view(
        st.session_state.state,
        st.session_state.history,
        st.session_state.p1, st.session_state.a1,
        st.session_state.p2, st.session_state.a2,
        zoom_radius=st.session_state.zoom_level
    )
    st.pyplot(fig, use_container_width=True)

with col_data:
    st.markdown("### 📊 Telemetria")
    
    u, v, r = st.session_state.state[0], st.session_state.state[1], st.session_state.state[2]
    speed_kn = np.sqrt(u**2 + v**2) * 1.94384
    rot_deg = np.degrees(r) * 60 # gradi al minuto
    
    st.metric("SOG (Speed)", f"{speed_kn:.1f} kn")
    st.metric("ROT (Turn Rate)", f"{rot_deg:.1f} °/min")
    
    # Calcolo forze attuali per display
    FX, FY, N, _, _ = calculate_forces(st.session_state.state, 
                                    st.session_state.p1, st.session_state.a1, 
                                    st.session_state.p2, st.session_state.a2)
    
    st.markdown("---")
    st.markdown("**Forces (Ship Ref)**")
    st.text(f"Fx (Long): {FX/1000:.1f} kN")
    st.text(f"Fy (Lat) : {FY/1000:.1f} kN")
    st.text(f"Momento  : {N/1000:.0f} kNm")

# Rerun automatico per animazione fluida
time.sleep(0.05)
st.rerun()
