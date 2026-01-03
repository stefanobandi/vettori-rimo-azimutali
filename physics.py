import numpy as np
import streamlit as st
from constants import *

# --- FUNZIONI DI MANOVRA (LOGICA PULSANTI) ---
# Nessuna modifica logica qui, solo copia-incolla delle funzioni esistenti funzionanti

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

# --- FISICA V6.6: Correct CG Calculation & Pivot Shift ---

def predict_trajectory(F_sx_vec, F_dx_vec, pos_sx, pos_dx, pp_y, total_time=30.0, steps=20):
    """
    Simulazione Fisica V6.6.
    Calcoli eseguiti sul Baricentro (0,0).
    Il Pivot Point emerge naturalmente dal bilanciamento delle resistenze (Drag).
    """
    dt = 0.2
    n_total_steps = int(total_time / dt)
    record_every = max(1, n_total_steps // steps)
    
    # IMPORTANTE: I calcoli fisici si fanno rispetto al Baricentro (0,0), non al PP utente.
    cg_center = np.array([0.0, 0.0])
    
    # 1. Analisi Forze Motori (Newton)
    F_sx_n = F_sx_vec * 1000 * G_ACCEL
    F_dx_n = F_dx_vec * 1000 * G_ACCEL
    
    # Somma Vettoriale (Forza Netta sul CG)
    F_net_vec = F_sx_n + F_dx_n
    
    # --- RILEVAMENTO MANOVRA (Logic State) ---
    F_total_power = np.linalg.norm(F_sx_n) + np.linalg.norm(F_dx_n)
    F_net_mag = np.linalg.norm(F_net_vec)
    
    # Spin Ratio: 1.0 = Motori totalmente contrapposti (Rotazione Pura)
    spin_ratio = 0.0
    if F_total_power > 100.0:
        spin_ratio = 1.0 - (F_net_mag / F_total_power)
        spin_ratio = np.clip(spin_ratio, 0.0, 1.0) ** 2  # Esponenziale per rendere netta la distinzione
        
    # Lateral Ratio: 1.0 = Spinta laterale pura (Crabbing)
    lateral_ratio = 0.0
    if F_total_power > 100.0:
        lateral_ratio = abs(F_net_vec[0]) / F_total_power

    # 2. Momento Motori rispetto al CG (0,0)
    # Braccio leva fisso: i motori sono a POS_THRUSTERS_Y (-12.0)
    # M = rx * Fy - ry * Fx
    r_sx = pos_sx - cg_center
    M_sx = r_sx[0] * F_sx_n[1] - r_sx[1] * F_sx_n[0]
    r_dx = pos_dx - cg_center
    M_dx = r_dx[0] * F_dx_n[1] - r_dx[1] * F_dx_n[0]
    M_eng = M_sx + M_dx

    # Masse inerziali
    M_VIRT_X = MASS * 1.8  
    M_VIRT_Y = MASS * 1.1  
    
    # Stato Iniziale
    x, y, heading_deg = 0.0, 0.0, 0.0
    u, v, r = 0.0, 0.0, 0.0 
    
    results = []
    
    for i in range(n_total_steps):
        v_bow_sway = u + (r * Y_BOW_CP)     
        v_stern_sway = u + (r * Y_STERN_CP) 
        
        # --- GESTIONE PIVOT POINT TRAMITE RESISTENZE ---
        
        # Scenario 1: SPIN PURO (000°/180°) -> Pivot su B (Poppa)
        # Per spostare il pivot a poppa, la poppa deve fare da "ancora" e la prua deve scivolare.
        # Strategia: Alta resistenza Poppa, Bassissima resistenza Prua.
        if spin_ratio > 0.6:
            # Siamo in rotazione. Skeg "trasparente".
            K_bow_eff = K_X_BOW * 0.05 
            K_stern_eff = K_X_STERN * 2.5 # Aumento artificiale poppa per arretrare il pivot
        
        # Scenario 2: CRABBING (090°/090°) -> Pivot su A (Prua/Skeg)
        # La prua deve bloccare lo scarroccio, la poppa deve ruotare spinta dai motori.
        # Strategia: Altissima resistenza Prua (Muro), Bassa resistenza Poppa.
        elif lateral_ratio > 0.6:
            K_bow_eff = K_X_BOW * 10.0 # Muro Skeg
            K_stern_eff = K_X_STERN * 0.5 # Poppa scivola
            
        # Scenario 3: AVANZAMENTO MISTO
        else:
            # Comportamento standard: Skeg lavora in funzione della velocità
            surge_speed = abs(v)
            grip = 0.2 + 0.8 * np.clip(surge_speed/3.0, 0.0, 1.0)
            K_bow_eff = K_X_BOW * grip
            K_stern_eff = K_X_STERN
            
        # Calcolo Forze Resistenti (Drag)
        F_drag_surge = -np.sign(v) * K_Y * (v**2)
        F_drag_bow = -np.sign(v_bow_sway) * K_bow_eff * (v_bow_sway**2)
        F_drag_stern = -np.sign(v_stern_sway) * K_stern_eff * (v_stern_sway**2)
        M_drag_rot = -np.sign(r) * K_W * (r**2)
        
        # Somma Forze (rispetto CG)
        Sum_Fx = F_net_vec[0] + F_drag_bow + F_drag_stern
        Sum_Fy = F_net_vec[1] + F_drag_surge
        
        # Somma Momenti (rispetto CG)
        # Nota: Y_BOW_CP e Y_STERN_CP sono già coordinate relative a CG (0,0)
        M_res_bow = F_drag_bow * Y_BOW_CP       
        M_res_stern = F_drag_stern * Y_STERN_CP 
        
        Sum_M = M_eng + M_res_bow + M_res_stern + M_drag_rot
        
        # Integrazione
        du = Sum_Fx / M_VIRT_X
        dv = Sum_Fy / M_VIRT_Y
        dr = Sum_M / I_Z
        
        u += du * dt
        v += dv * dt
        r += dr * dt
        
        # Posizione Mondo
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
