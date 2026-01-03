import numpy as np
import streamlit as st
from constants import *

# --- FUNZIONI DI MANOVRA (LOGICA PULSANTI) ---

def apply_slow_side_step(direction):
    """
    Configura i motori per una traslazione laterale lenta (Slow Side Step).
    Calcola l'angolo necessario affinché le linee di spinta convergano sul Pivot Point attuale.
    """
    pp_y = st.session_state.pp_y
    dy = pp_y - POS_THRUSTERS_Y
    dist_x_calcolo = POS_THRUSTERS_X 
    try:
        alpha_rad = np.arctan2(dist_x_calcolo, dy)
        alpha_deg = np.degrees(alpha_rad)
        
        if direction == "DRITTA":
            # Motori spingono verso destra, ma inclinati per bilanciare il momento
            a1_set, a2_set = alpha_deg, 180 - alpha_deg
        else: # SINISTRA
            a1_set, a2_set = 180 + alpha_deg, 360 - alpha_deg
            
        st.session_state.p1 = 50
        st.session_state.a1 = int(round(a1_set % 360))
        st.session_state.p2 = 50
        st.session_state.a2 = int(round(a2_set % 360))
        
    except Exception as e:
        st.error(f"Errore calcolo Slow: {e}")

def apply_fast_side_step(direction):
    """
    Configura i motori per una traslazione laterale aggressiva (Fast Side Step).
    Usa la logica Drive/Slave per massimizzare la spinta laterale.
    """
    pp_y = st.session_state.pp_y
    dist_y = pp_y - POS_THRUSTERS_Y 
    try:
        if direction == "DRITTA":
            # Drive (SX) spinge a 45°, Slave (DX) compensa
            a_drive, p_drive = 45.0, 50.0
            x_drive, x_slave = -POS_THRUSTERS_X, POS_THRUSTERS_X
            
            # Calcolo geometrico intersezione
            x_int = x_drive + dist_y * np.tan(np.radians(a_drive))
            dx, dy = x_slave - x_int, POS_THRUSTERS_Y - pp_y
            
            if abs(dy) < 0.01: return
            a_slave = np.degrees(np.arctan2(dx, dy)) % 360
            
            denom = np.cos(np.radians(a_slave))
            if abs(denom) < 0.001: return
            
            p_slave = -(p_drive * np.cos(np.radians(a_drive))) / denom
            
            # Gestione potenza negativa
            if p_slave < 0:
                p_slave = abs(p_slave)
                a_slave = (a_slave + 180) % 360

            if 1.0 <= p_slave <= 100.0:
                st.session_state.a1, st.session_state.p1 = int(a_drive), int(p_drive)
                st.session_state.a2, st.session_state.p2 = int(round(a_slave)), int(round(p_slave))
                st.toast(f"Fast Dritta: Slave {int(round(p_slave))}%", icon="⚡")
                
        else: # SINISTRA
            # Drive (DX) spinge a 315°, Slave (SX) compensa
            a_drive, p_drive = 315.0, 50.0
            x_drive, x_slave = POS_THRUSTERS_X, -POS_THRUSTERS_X
            
            x_int = x_drive + dist_y * np.tan(np.radians(a_drive))
            dx, dy = x_slave - x_int, POS_THRUSTERS_Y - pp_y
            
            if abs(dy) < 0.01: return
            a_slave = np.degrees(np.arctan2(dx, dy)) % 360
            
            denom = np.cos(np.radians(a_drive))
            if abs(denom) < 0.001: return
            
            p_slave = -(p_drive * np.cos(np.radians(a_drive))) / denom
            
            # Gestione potenza negativa
            if p_slave < 0:
                p_slave = abs(p_slave)
                a_slave = (a_slave + 180) % 360
            
            if 1.0 <= p_slave <= 100.0:
                st.session_state.a2, st.session_state.p2 = int(a_drive), int(p_drive)
                st.session_state.a1, st.session_state.p1 = int(round(a_slave)), int(round(p_slave))
                st.toast(f"Fast Sinistra: Slave {int(round(p_slave))}%", icon="⚡")
                
    except Exception as e:
        st.error(f"Errore geometrico: {e}")

def apply_turn_on_the_spot(direction):
    """
    Configura i motori per una rotazione pura sul posto (Pure Spin).
    Motori in opposizione (Push/Pull) per creare coppia massima.
    """
    potenza = 50
    if direction == "SINISTRA":
        # Rotazione Antioraria
        st.session_state.p1, st.session_state.a1 = potenza, 135 # SX Tira indietro-sx
        st.session_state.p2, st.session_state.a2 = potenza, 45  # DX Spinge avanti-dx
    else:
        # Rotazione Oraria
        st.session_state.p1, st.session_state.a1 = potenza, 315 # SX Spinge avanti-sx
        st.session_state.p2, st.session_state.a2 = potenza, 225 # DX Tira indietro-dx

def check_wash_hit(origin, wash_vec, target_pos, threshold=2.0):
    """Calcola se il flusso (wash) di un propulsore colpisce l'altro."""
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
    """Trova il punto di intersezione geometrico delle rette di spinta."""
    th1, th2 = np.radians(90 - angle1_deg), np.radians(90 - angle2_deg)
    v1, v2 = np.array([np.cos(th1), np.sin(th1)]), np.array([np.cos(th2), np.sin(th2)])
    matrix = np.column_stack((v1, -v2))
    if abs(np.linalg.det(matrix)) < 1e-4: return None
    try:
        t = np.linalg.solve(matrix, p2 - p1)[0]
        return p1 + t * v1
    except: return None

# --- FISICA V6.2: Dynamic Skeg & Pivot Logic ---

def predict_trajectory(F_sx_vec, F_dx_vec, pos_sx, pos_dx, pp_y, total_time=30.0, steps=20):
    """
    Simula la traiettoria del rimorchiatore integrando le forze nel tempo.
    Implementa la logica 'Dynamic Skeg' per gestire i diversi pivot point.
    """
    dt = 0.2
    n_total_steps = int(total_time / dt)
    record_every = max(1, n_total_steps // steps)
    
    # Parametri geometrici
    # Pivot Point Center per i momenti (non più 0,0 ma pp_y)
    pp_center = np.array([0.0, pp_y])
    
    # 1. Input Forze Motori (in Newton)
    F_eng_x = (F_sx_vec[0] + F_dx_vec[0]) * 1000 * G_ACCEL 
    F_eng_y = (F_sx_vec[1] + F_dx_vec[1]) * 1000 * G_ACCEL 
    
    # Calcolo Momento Motori (Torque) rispetto al PP (0, pp_y)
    # Braccio leva = Posizione_Motore - Posizione_PP
    # Cross product 2D: r_x * F_y - r_y * F_x
    
    # Motore SX
    r_sx = pos_sx - pp_center
    M_sx = r_sx[0] * (F_sx_vec[1] * 1000 * G_ACCEL) - r_sx[1] * (F_sx_vec[0] * 1000 * G_ACCEL)
    
    # Motore DX
    r_dx = pos_dx - pp_center
    M_dx = r_dx[0] * (F_dx_vec[1] * 1000 * G_ACCEL) - r_dx[1] * (F_dx_vec[0] * 1000 * G_ACCEL)
    
    M_eng = M_sx + M_dx

    # Masse inerziali (Virtual Mass)
    M_VIRT_X = MASS * 1.8  
    M_VIRT_Y = MASS * 1.1  
    
    # Stato Iniziale (Velocità nel sistema nave locale)
    x, y, heading_deg = 0.0, 0.0, 0.0
    u = 0.0 
    v = 0.0 
    r = 0.0 
    
    results = []
    
    for i in range(n_total_steps):
        
        # --- CALCOLO VELOCITÀ LATERALI LOCALI (SWAY) ---
        v_bow_sway = u + (r * Y_BOW_CP)     
        v_stern_sway = u + (r * Y_STERN_CP) 
        
        # --- FORZE IDRODINAMICHE (DAMPING & LIFT) ---
        
        # 1. Fattore "Presa" dello Skeg (Dynamic Skeg Logic)
        surge_speed = abs(v)
        skeg_grip = 0.15 + 0.85 * np.clip(surge_speed / 2.5, 0.0, 1.0)
        
        # 2. Resistenze
        F_drag_surge = -np.sign(v) * K_Y * (v**2)
        F_drag_bow = -np.sign(v_bow_sway) * (K_X_BOW * skeg_grip) * (v_bow_sway**2)
        F_drag_stern = -np.sign(v_stern_sway) * K_X_STERN * (v_stern_sway**2)
        M_drag_rot = -np.sign(r) * K_W * (r**2)
        
        # --- SOMMA FORZE E MOMENTI (Local Frame) ---
        
        Sum_Fx = F_eng_x + F_drag_bow + F_drag_stern
        Sum_Fy = F_eng_y + F_drag_surge
        
        # Totale Momento (Torque) rispetto al PP
        # Bracci di leva per le resistenze (Pos_CP - Pos_PP)
        
        arm_bow = Y_BOW_CP - pp_y
        arm_stern = Y_STERN_CP - pp_y
        
        M_res_bow = F_drag_bow * arm_bow       
        M_res_stern = F_drag_stern * arm_stern 
        
        Sum_M = M_eng + M_res_bow + M_res_stern + M_drag_rot
        
        # --- INTEGRAZIONE NEWTONIANA (Eulero) ---
        du = Sum_Fx / M_VIRT_X
        dv = Sum_Fy / M_VIRT_Y
        dr = Sum_M / I_Z
        
        u += du * dt
        v += dv * dt
        r += dr * dt
        
        # Integrazione Posizione nel Mondo
        rad = np.radians(heading_deg)
        cos_a = np.cos(rad)
        sin_a = np.sin(rad)
        
        dx_w = u * cos_a + v * sin_a 
        dy_w = -u * sin_a + v * cos_a
        
        x += dx_w * dt
        y += dy_w * dt
        heading_deg -= np.degrees(r * dt) 
        
        if i % record_every == 0:
            results.append((x, y, heading_deg))
            
    return results
