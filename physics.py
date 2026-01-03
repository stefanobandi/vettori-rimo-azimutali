import numpy as np
import streamlit as st
from constants import *

# --- FUNZIONI DI MANOVRA (LOGICA PULSANTI) ---

def apply_slow_side_step(direction):
    """Configura i motori per una traslazione laterale lenta (Slow Side Step)."""
    pp_y = st.session_state.pp_y
    dy = pp_y - POS_THRUSTERS_Y
    dist_x_calcolo = POS_THRUSTERS_X 
    try:
        alpha_rad = np.arctan2(dist_x_calcolo, dy)
        alpha_deg = np.degrees(alpha_rad)
        
        if direction == "DRITTA":
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
    """Configura i motori per una traslazione laterale aggressiva (Fast Side Step)."""
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
    """Pure Spin: Motori contrapposti."""
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

# --- FISICA V6.5: Intelligent Pivot Shifting ---

def predict_trajectory(F_sx_vec, F_dx_vec, pos_sx, pos_dx, pp_y, total_time=30.0, steps=20):
    """
    Simulazione Fisica con gestione avanzata del Pivot Point.
    Distingue tra manovra di coppia (Pivot B) e manovra laterale (Pivot A).
    """
    dt = 0.2
    n_total_steps = int(total_time / dt)
    record_every = max(1, n_total_steps // steps)
    
    pp_center = np.array([0.0, pp_y])
    
    # 1. Analisi Forze Motori
    F_sx_newton = F_sx_vec * 1000 * G_ACCEL
    F_dx_newton = F_dx_vec * 1000 * G_ACCEL
    
    # Somma Vettoriale (Forza Netta)
    F_net_vec = F_sx_newton + F_dx_newton
    F_net_mag = np.linalg.norm(F_net_vec)
    
    # Somma Scalare (Forza Totale "Spesa")
    F_total_mag = np.linalg.norm(F_sx_newton) + np.linalg.norm(F_dx_newton)
    
    # --- CALCOLO COEFFICIENTI DI MANOVRA ---
    
    # Spin Factor: 1.0 se i motori spingono uno contro l'altro (Coppia Pura)
    #              0.0 se spingono insieme (Traslazione/Avanzamento)
    # Se F_net è basso ma F_total è alto, stiamo ruotando.
    spin_factor = 0.0
    if F_total_mag > 100.0:
        spin_factor = 1.0 - (F_net_mag / F_total_mag)
        spin_factor = np.clip(spin_factor, 0.0, 1.0)
        # Rendiamo la curva più aggressiva: appena c'è un po' di spin, il fattore sale
        spin_factor = spin_factor ** 0.5 

    # Lateral Factor: Quanta parte della forza netta è laterale (Crabbing)
    lateral_factor = 0.0
    if F_net_mag > 100.0:
        lateral_factor = abs(F_net_vec[0]) / F_net_mag
    
    # Forze e Momenti Input
    F_eng_x = F_net_vec[0]
    F_eng_y = F_net_vec[1]
    
    r_sx = pos_sx - pp_center
    M_sx = r_sx[0] * F_sx_newton[1] - r_sx[1] * F_sx_newton[0]
    r_dx = pos_dx - pp_center
    M_dx = r_dx[0] * F_dx_newton[1] - r_dx[1] * F_dx_newton[0]
    M_eng = M_sx + M_dx

    M_VIRT_X = MASS * 1.8  
    M_VIRT_Y = MASS * 1.1  
    
    x, y, heading_deg = 0.0, 0.0, 0.0
    u, v, r = 0.0, 0.0, 0.0 
    
    results = []
    
    for i in range(n_total_steps):
        v_bow_sway = u + (r * Y_BOW_CP)     
        v_stern_sway = u + (r * Y_STERN_CP) 
        
        # --- LOGICA "SKEG GRIP" DINAMICO ---
        
        # 1. Grip Base da Velocità (Avanzamento = Stabilità)
        surge_speed = abs(v)
        base_grip = 0.10 + 0.90 * np.clip(surge_speed / 2.0, 0.0, 1.0)
        
        # 2. Grip Laterale (Crabbing = Skeg deve tenere per fare da perno A)
        # Se spingiamo lateralmente, attiviamo lo Skeg
        lateral_grip = lateral_factor
        
        # Grip preliminare (il massimo tra velocità e richiesta laterale)
        current_grip = max(base_grip, lateral_grip)
        
        # 3. PENALITÀ SPIN (Cruciale per Pivot B)
        # Se stiamo facendo Spin (motori contrapposti), dobbiamo "uccidere" lo Skeg
        # affinché la resistenza dominante diventi quella di Poppa (fissa),
        # spostando il centro di rotazione indietro verso B.
        if spin_factor > 0.6:
            # Se spin factor è alto, riduciamo drasticamente il grip, 
            # indipendentemente da tutto il resto.
            penalty = (1.0 - spin_factor) * 0.1 # Diventa piccolissimo
            current_grip *= penalty
            # Assicuriamoci che non sia zero assoluto per stabilità numerica
            current_grip = max(current_grip, 0.02)
            
        # Parametrizzazione resistenze
        F_drag_surge = -np.sign(v) * K_Y * (v**2)
        
        # Resistenza Prua modulata
        # Spin -> grip basso -> K_bow basso -> Pivot va verso Poppa (B)
        # Crab -> grip alto -> K_bow alto -> Pivot va verso Prua (A)
        F_drag_bow = -np.sign(v_bow_sway) * (K_X_BOW * current_grip) * (v_bow_sway**2)
        
        # Resistenza Poppa (Costante, funge da ancora quando lo Skeg molla)
        F_drag_stern = -np.sign(v_stern_sway) * K_X_STERN * (v_stern_sway**2)
        
        M_drag_rot = -np.sign(r) * K_W * (r**2)
        
        Sum_Fx = F_eng_x + F_drag_bow + F_drag_stern
        Sum_Fy = F_eng_y + F_drag_surge
        
        arm_bow = Y_BOW_CP - pp_y
        arm_stern = Y_STERN_CP - pp_y
        M_res_bow = F_drag_bow * arm_bow       
        M_res_stern = F_drag_stern * arm_stern 
        
        Sum_M = M_eng + M_res_bow + M_res_stern + M_drag_rot
        
        du = Sum_Fx / M_VIRT_X
        dv = Sum_Fy / M_VIRT_Y
        dr = Sum_M / I_Z
        
        u += du * dt
        v += dv * dt
        r += dr * dt
        
        rad = np.radians(heading_deg)
        cos_a, sin_a = np.cos(rad), np.sin(rad)
        dx_w = u * cos_a + v * sin_a 
        dy_w = -u * sin_a + v * cos_a
        
        x += dx_w * dt
        y += dy_w * dt
        heading_deg -= np.degrees(r * dt) 
        
        if i % record_every == 0:
            results.append((x, y, heading_deg))
            
    return results
