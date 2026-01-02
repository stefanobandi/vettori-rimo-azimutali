import numpy as np
import streamlit as st
from constants import *
import math

# --- FUNZIONI DI COMODO PER I PULSANTI ---
# Necessarie per far funzionare i bottoni in app.py

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
            # Configurazione geometrica per crabbing veloce
            a_drive, p_drive = 45.0, 50.0
            x_drive, x_slave = -POS_THRUSTERS_X, POS_THRUSTERS_X
            x_int = x_drive + dist_y * np.tan(np.radians(a_drive))
            dx, dy = x_slave - x_int, POS_THRUSTERS_Y - pp_y
            if abs(dy) < 0.01: return
            a_slave = np.degrees(np.arctan2(dx, dy)) % 360
            denom = np.cos(np.radians(a_slave))
            if abs(denom) < 0.001: return
            p_slave = -(p_drive * np.cos(np.radians(a_drive))) / denom
            
            if 1.0 <= p_slave <= 100.0:
                st.session_state.a1, st.session_state.p1 = int(a_drive), int(p_drive)
                st.session_state.a2, st.session_state.p2 = int(round(a_slave)), int(round(p_slave))
                st.toast(f"Fast Dritta: Slave {int(round(p_slave))}%", icon="⚡")
        else:
            # Sinistra
            a_drive, p_drive = 315.0, 50.0
            x_drive, x_slave = POS_THRUSTERS_X, -POS_THRUSTERS_X
            x_int = x_drive + dist_y * np.tan(np.radians(a_drive))
            dx, dy = x_slave - x_int, POS_THRUSTERS_Y - pp_y
            if abs(dy) < 0.01: return
            a_slave = np.degrees(np.arctan2(dx, dy)) % 360
            denom = np.cos(np.radians(a_drive))
            if abs(denom) < 0.001: return
            p_slave = -(p_drive * np.cos(np.radians(a_drive))) / denom
            
            if 1.0 <= p_slave <= 100.0:
                st.session_state.a2, st.session_state.p2 = int(a_drive), int(p_drive)
                st.session_state.a1, st.session_state.p1 = int(round(a_slave)), int(round(p_slave))
                st.toast(f"Fast Sinistra: Slave {int(round(p_slave))}%", icon="⚡")
    except Exception as e:
        st.error(f"Errore geometrico: {e}")

def apply_turn_on_the_spot(direction):
    potenza = 50
    if direction == "SINISTRA":
        # Rotazione Antioraria
        st.session_state.p1, st.session_state.a1 = potenza, 180
        st.session_state.p2, st.session_state.a2 = potenza, 0
    else:
        # Rotazione Oraria
        st.session_state.p1, st.session_state.a1 = potenza, 0
        st.session_state.p2, st.session_state.a2 = potenza, 180

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

# --- NUOVA LOGICA DI PREDIZIONE (SMART PIVOT) ---

def predict_trajectory(F_sx_vec, F_dx_vec, pos_sx, pos_dx, pp_y, total_time=30.0, steps=20):
    """
    Calcola la traiettoria selezionando dinamicamente il punto di rotazione (Pivot Point)
    in base alla configurazione dei motori.
    """
    dt = 0.5
    n_total_steps = int(total_time / dt)
    record_every = max(1, n_total_steps // steps)
    
    # 1. Analisi Configurazione Motori
    # Ricaviamo gli angoli dai vettori forza passati
    # atan2(x, y) perché Y è l'asse "Nord/Avanti" e X è "Est/Destra"
    ang_sx = np.degrees(np.arctan2(F_sx_vec[0], F_sx_vec[1])) % 360
    ang_dx = np.degrees(np.arctan2(F_dx_vec[0], F_dx_vec[1])) % 360
    
    diff = abs(ang_sx - ang_dx)
    if diff > 180: diff = 360 - diff
    
    # LOGICA DI SELEZIONE PIVOT:
    # Se i motori sono contrapposti (circa 180° di differenza), è uno SPIN PURO.
    # Il pivot deve essere tra i propulsori (Y = -12).
    # Altrimenti (avanzamento, virata, crabbing), il pivot è sullo SKEG (Y = -25).
    
    is_pure_spin = False
    if 160 <= diff <= 200:
        is_pure_spin = True
        pivot_y_active = POS_THRUSTERS_Y # Punto B (-12.0)
    else:
        pivot_y_active = -25.0           # Punto A (Skeg a poppa)

    # 2. Setup Simulazione Semplificata
    # Usiamo una fisica cinematica basata su forze e bracci di leva
    results = []
    
    # Stato iniziale
    x, y, h = 0.0, 0.0, 0.0
    vx, vy, vomega = 0.0, 0.0, 0.0 # Velocità locali
    
    # Parametri Inerziali simulati
    mass = 100.0  # Valore arbitrario per calibrare la velocità visiva
    moment_inertia = 800.0
    drag_lin = 0.85
    drag_rot = 0.80
    
    # Forza Totale (Lineare)
    # Somma vettoriale delle spinte (già scalate in tonnellate nel file app.py)
    # F_sx_vec è [ton_x, ton_y]
    ft_x = F_sx_vec[0] + F_dx_vec[0]
    ft_y = F_sx_vec[1] + F_dx_vec[1]
    
    # Calcolo del Torque (Momento Rotatorio)
    # Il momento dipende da quanto sono lontani i motori dal PIVOT ATTIVO.
    
    # Braccio di leva Y: Distanza tra motori (-12) e Pivot Attivo
    lever_arm_y = POS_THRUSTERS_Y - pivot_y_active
    # Se Pivot è -12 (Spin), lever_arm_y = 0.
    # Se Pivot è -25 (Skeg), lever_arm_y = -12 - (-25) = +13.
    
    # Calcolo momento generato da motore SX (che sta a X = -pos_x)
    # Torque = Fy * dist_x - Fx * dist_y
    # Motore SX: pos_x = -POS_THRUSTERS_X, pos_y = 0 (relativo ai propulsori)
    # Ma il braccio y (dist_y) è lever_arm_y
    
    torque_sx = (F_sx_vec[1] * (-POS_THRUSTERS_X)) - (F_sx_vec[0] * lever_arm_y)
    torque_dx = (F_dx_vec[1] * (POS_THRUSTERS_X)) - (F_dx_vec[0] * lever_arm_y)
    
    total_torque = torque_sx + torque_dx
    
    # Correzione "Effetto Timone" dello Skeg in avanzamento
    # Se stiamo avanzando curvando (es. DX 15 / SX 15), la forza laterale deve creare rotazione
    # perché lo Skeg fa perno.
    if not is_pure_spin and abs(ft_x) > 0.1:
        # Aggiungiamo momento extra basato sulla forza laterale
        total_torque += ft_x * 8.0 

    # Loop temporale
    for i in range(n_total_steps):
        # Accelerazione
        ax = ft_x / mass
        ay = ft_y / mass
        aomega = total_torque / moment_inertia
        
        # Velocità
        vx += ax * dt
        vy += ay * dt
        vomega += aomega * dt
        
        # Drag (attrito)
        vx *= drag_lin
        vy *= drag_lin
        vomega *= drag_rot
        
        # Calcolo spostamento nel mondo (rotazione coordinate)
        rad_h = np.radians(h)
        # X=Est, Y=Nord
        dx_world = vx * np.cos(rad_h) + vy * np.sin(rad_h)
        dy_world = -vx * np.sin(rad_h) + vy * np.cos(rad_h)
        
        x += dx_world * dt
        y += dy_world * dt
        h += np.degrees(vomega * dt)
        
        if i % record_every == 0:
            results.append((x, y, h))
            
    return results
