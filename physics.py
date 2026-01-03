import numpy as np
import streamlit as st
from constants import *

# --- FUNZIONI DI MANOVRA (Invariate) ---
# Copiamo le funzioni di input per non rompere l'interfaccia
def apply_slow_side_step(direction):
    pp_y = st.session_state.pp_y
    dy = pp_y - POS_THRUSTERS_Y
    dist_x_calcolo = POS_THRUSTERS_X 
    try:
        alpha_rad = np.arctan2(dist_x_calcolo, dy)
        alpha_deg = np.degrees(alpha_rad)
        if direction == "DRITTA":
            a1_set, a2_set = alpha_deg, 180 - alpha_deg
        else:
            a1_set, a2_set = 180 + alpha_deg, 360 - alpha_deg
        st.session_state.p1 = 50
        st.session_state.a1 = int(round(a1_set % 360))
        st.session_state.p2 = 50
        st.session_state.a2 = int(round(a2_set % 360))
    except Exception as e:
        st.error(f"Errore calcolo Slow: {e}")

def apply_fast_side_step(direction):
    pp_y = st.session_state.pp_y
    dist_y = pp_y - POS_THRUSTERS_Y 
    try:
        if direction == "DRITTA":
            a_drive, p_drive = 45.0, 50.0
            x_drive, x_slave = -POS_THRUSTERS_X, POS_THRUSTERS_X
            x_int = x_drive + dist_y * np.tan(np.radians(a_drive))
            dx, dy = x_slave - x_int, POS_THRUSTERS_Y - pp_y
            if abs(dy) < 0.01: return
            a_slave = np.degrees(np.arctan2(dx, dy)) % 360
            denom = np.cos(np.radians(a_slave))
            if abs(denom) < 0.001: return
            p_slave = -(p_drive * np.cos(np.radians(a_drive))) / denom
            if p_slave < 0: p_slave = abs(p_slave); a_slave = (a_slave + 180) % 360
            if 1.0 <= p_slave <= 100.0:
                st.session_state.a1, st.session_state.p1 = int(a_drive), int(p_drive)
                st.session_state.a2, st.session_state.p2 = int(round(a_slave)), int(round(p_slave))
                st.toast(f"Fast Dritta: Slave {int(round(p_slave))}%", icon="⚡")
        else: # SINISTRA
            a_drive, p_drive = 315.0, 50.0
            x_drive, x_slave = POS_THRUSTERS_X, -POS_THRUSTERS_X
            x_int = x_drive + dist_y * np.tan(np.radians(a_drive))
            dx, dy = x_slave - x_int, POS_THRUSTERS_Y - pp_y
            if abs(dy) < 0.01: return
            a_slave = np.degrees(np.arctan2(dx, dy)) % 360
            denom = np.cos(np.radians(a_slave))
            if abs(denom) < 0.001: return
            p_slave = -(p_drive * np.cos(np.radians(a_drive))) / denom
            if p_slave < 0: p_slave = abs(p_slave); a_slave = (a_slave + 180) % 360
            if 1.0 <= p_slave <= 100.0:
                st.session_state.a2, st.session_state.p2 = int(a_drive), int(p_drive)
                st.session_state.a1, st.session_state.p1 = int(round(a_slave)), int(round(p_slave))
                st.toast(f"Fast Sinistra: Slave {int(round(p_slave))}%", icon="⚡")
    except Exception as e:
        st.error(f"Errore geometrico: {e}")

def apply_turn_on_the_spot(direction):
    potenza = 50
    if direction == "SINISTRA":
        st.session_state.p1, st.session_state.a1 = potenza, 135
        st.session_state.p2, st.session_state.a2 = potenza, 45
    else:
        st.session_state.p1, st.session_state.a1 = potenza, 315
        st.session_state.p2, st.session_state.a2 = potenza, 225

def check_wash_hit(origin, wash_vec, target_pos, threshold=2.0):
    wash_len = np.linalg.norm(wash_vec)
    if wash_len < 0.1: return False
    wash_dir = wash_vec / wash_len
    to_target = target_pos - origin
    proj_length = np.dot(to_target, wash_dir)
    if proj_length > 0: 
        perp_dist = np.linalg.norm(to_target - (proj_length * wash_dir))
        return perp_dist < threshold
    return False

def intersect_lines(p1, angle1_deg, p2, angle2_deg):
    th1, th2 = np.radians(90 - angle1_deg), np.radians(90 - angle2_deg)
    v1, v2 = np.array([np.cos(th1), np.sin(th1)]), np.array([np.cos(th2), np.sin(th2)])
    matrix = np.column_stack((v1, -v2))
    if abs(np.linalg.det(matrix)) < 1e-4: return None
    try:
        t = np.linalg.solve(matrix, p2 - p1)[0]
        return p1 + t * v1
    except: return None

# --- FISICA SPERIMENTALE: "BRICK ON ICE" ---
# Concetto: Il Pivot Point impostato dall'utente DIVENTA il Baricentro matematico.
# Nessuna resistenza idrodinamica complessa. Solo F=ma e Torque=I*alpha.

def predict_trajectory(F_sx_vec, F_dx_vec, pos_sx, pos_dx, pp_y, total_time=30.0, steps=20):
    dt = 0.2
    n_total_steps = int(total_time / dt)
    record_every = max(1, n_total_steps // steps)
    
    # IL CUORE DELL'IDEA:
    # Definiamo che il centro di massa del sistema è ESATTAMENTE dove hai messo il Pivot Point.
    # Quindi tutti i momenti sono calcolati rispetto a questo punto.
    center_of_mass = np.array([0.0, pp_y])
    
    # Forze in Newton
    F_sx_n = F_sx_vec * 1000 * G_ACCEL
    F_dx_n = F_dx_vec * 1000 * G_ACCEL
    
    # 1. Forza Risultante (Lineare)
    # Questa sposta il mattone nello spazio
    F_net = F_sx_n + F_dx_n
    
    # 2. Momento Torcente (Rotazionale)
    # Calcolato rigorosamente rispetto al Pivot Point (che ora è il CM)
    r_sx = pos_sx - center_of_mass
    M_sx = r_sx[0] * F_sx_n[1] - r_sx[1] * F_sx_n[0]
    
    r_dx = pos_dx - center_of_mass
    M_dx = r_dx[0] * F_dx_n[1] - r_dx[1] * F_dx_n[0]
    
    Total_Torque = M_sx + M_dx

    # Parametri "Mattone"
    MASS_BRICK = 700000.0  
    INERTIA_BRICK = 80000000.0 
    
    # Stato Iniziale
    x, y, heading_deg = 0.0, 0.0, 0.0
    u, v, r = 0.0, 0.0, 0.0 
    
    results = []
    
    for i in range(n_total_steps):
        
        # Accelerazioni (Legge di Newton F=ma)
        du = F_net[0] / MASS_BRICK
        dv = F_net[1] / MASS_BRICK
        dr = Total_Torque / INERTIA_BRICK
        
        # Aggiornamento Velocità
        u += du * dt
        v += dv * dt
        r += dr * dt
        
        # Attrito "Ghiaccio" (Damping lineare semplice)
        # Serve solo a non far schizzare via il mattone all'infinito
        u *= 0.95
        v *= 0.95
        r *= 0.90 # Frena la rotazione un po' di più
        
        # Integrazione Posizione
        rad = np.radians(heading_deg)
        cos_a, sin_a = np.cos(rad), np.sin(rad)
        
        # Ruotiamo il vettore velocità nel mondo
        dx_w = u * cos_a + v * sin_a 
        dy_w = -u * sin_a + v * cos_a
        
        x += dx_w * dt
        y += dy_w * dt
        heading_deg -= np.degrees(r * dt) 
        
        if i % record_every == 0:
            results.append((x, y, heading_deg))
            
    return results
