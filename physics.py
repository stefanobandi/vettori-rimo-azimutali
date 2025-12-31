import numpy as np
import streamlit as st
from constants import *

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
            if 1.0 <= p_slave <= 100.0:
                st.session_state.a1, st.session_state.p1 = int(a_drive), int(p_drive)
                st.session_state.a2, st.session_state.p2 = int(round(a_slave)), int(round(p_slave))
                st.toast(f"Fast Dritta: Slave {int(round(p_slave))}%", icon="⚡")
        else:
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

# --- FISICA V6.1: Dual Point Resistance Model ---
# Calcola le forze separatamente su Skeg (Prua) e Poppa basandosi
# sulle loro velocità locali. 

def predict_trajectory(F_sx_vec, F_dx_vec, pos_sx, pos_dx, pp_y, total_time=30.0, steps=20):
    dt = 0.2
    n_total_steps = int(total_time / dt)
    record_every = max(1, n_total_steps // steps)
    
    # Parametri geometrici per il calcolo dei momenti motore
    center_B = np.array([0.0, POS_THRUSTERS_Y]) # Punto medio tra propulsori (approx)
    
    # 1. Input Forze Motori (in Newton)
    # Converto da Tonnellate a Newton (1t ~ 9810 N)
    F_eng_x = (F_sx_vec[0] + F_dx_vec[0]) * 1000 * G_ACCEL
    F_eng_y = (F_sx_vec[1] + F_dx_vec[1]) * 1000 * G_ACCEL
    
    # Calcolo Momento Motori (Torque) rispetto al baricentro (0,0)
    # Nota: pos_sx e pos_dx sono coordinate rispetto a (0,0)
    M_eng = (pos_sx[0] * F_sx_vec[1] - pos_sx[1] * F_sx_vec[0]) + \
            (pos_dx[0] * F_dx_vec[1] - pos_dx[1] * F_dx_vec[0])
    M_eng = M_eng * 1000 * G_ACCEL

    # Masse inerziali aumentate (Added Mass effect)
    M_VIRT_X = MASS * 1.1  # Poca massa aggiunta longitudinale
    M_VIRT_Y = MASS * 1.8  # Molta massa aggiunta laterale (spostare acqua di lato è dura)
    
    # Stato Iniziale
    x, y, heading_deg = 0.0, 0.0, 0.0
    u, v, r = 0.0, 0.0, 0.0 # Surge, Sway, Yaw rate
    
    results = []
    
    for i in range(n_total_steps):
        
        # --- CALCOLO VELOCITÀ LOCALI ---
        # Velocità laterale locale a Prua (Skeg) e Poppa
        # v_local = v_baricentro + (velocità_rotazione * distanza_dal_centro)
        v_bow_lat = v + (r * Y_BOW_CP)
        v_stern_lat = v + (r * Y_STERN_CP)
        
        # --- FORZE IDRODINAMICHE (DAMPING) ---
        # Resistenza = -K * v * |v|
        
        # 1. Resistenza Longitudinale (Scafo)
        F_drag_long = -np.sign(u) * K_Y * (u**2)
        
        # 2. Resistenza Laterale PRUA (Skeg Effect)
        F_drag_bow = -np.sign(v_bow_lat) * K_X_BOW * (v_bow_lat**2)
        
        # 3. Resistenza Laterale POPPA (Stern Effect)
        F_drag_stern = -np.sign(v_stern_lat) * K_X_STERN * (v_stern_lat**2)
        
        # 4. Resistenza Rotazionale (Rotational Damping)
        M_drag_rot = -np.sign(r) * K_W * (r**2)
        
        # --- SOMMA FORZE E MOMENTI ---
        
        # Totale Surge (X)
        Sum_Fx = F_eng_x + F_drag_long
        
        # Totale Sway (Y) - Somma spinte motori e resistenze locali
        Sum_Fy = F_eng_y + F_drag_bow + F_drag_stern
        
        # Totale Momento (N)
        # Il momento delle resistenze è: Forza * Braccio
        M_res_bow = F_drag_bow * Y_BOW_CP
        M_res_stern = F_drag_stern * Y_STERN_CP
        
        Sum_M = M_eng + M_res_bow + M_res_stern + M_drag_rot
        
        # --- INTEGRAZIONE NEWTONIANA ---
        du = Sum_Fx / M_VIRT_X
        dv = Sum_Fy / M_VIRT_Y
        dr = Sum_M / I_Z
        
        u += du * dt
        v += dv * dt
        r += dr * dt
        
        # Integrazione Posizione nel Mondo
        rad = np.radians(heading_deg)
        # Ruota il vettore velocità dal sistema nave al sistema mondo
        dx_w = u * np.cos(rad) + v * np.sin(rad)
        dy_w = -u * np.sin(rad) + v * np.cos(rad)
        
        x += dx_w * dt
        y += dy_w * dt
        heading_deg -= np.degrees(r * dt) # Sottrai perché r positivo è antiorario (matematico), bussola è oraria
        
        if i % record_every == 0:
            results.append((x, y, heading_deg))
            
    return results
