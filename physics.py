import numpy as np
import streamlit as st
from constants import POS_THRUSTERS_X, POS_THRUSTERS_Y, MASS

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
            denom = np.cos(np.radians(a_slave))
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

# --- LOGICA PREDITTIVA GEOMETRICA CON INERZIA ---
def predict_trajectory(F_sx, F_dx, pos_sx_local, pos_dx_local, pp_y, total_time=30.0, steps=20):
    dt = 0.2  # Step temporale più fine per integrare meglio l'accelerazione
    n_steps = int(total_time / dt)
    record_every = max(1, n_steps // steps)
    
    # Stato Iniziale
    center_pos = np.array([0.0, 0.0])
    heading_deg = 0.0
    
    # Velocità accumulate (Inizialmente zero)
    v_surge = 0.0 
    v_sway = 0.0  
    v_rot = 0.0   
    
    results = []
    
    # --- COSTANTI FISICHE "CAPTAIN'S FEEL" ---
    # Masse virtuali elevate per simulare il ritardo (Inerzia)
    M_SURGE = 800.0   # Tonnellate virtuali longitudinali
    M_SWAY = 1500.0   # Tonnellate virtuali laterali (più difficile spostare acqua di lato)
    I_ROT = 60000.0   # Inerzia rotazionale
    
    # Resistenza dell'acqua (Drag) - Più basso è, più la nave mantiene l'abbrivio
    DRAG_SURGE = 0.02 
    DRAG_SWAY = 0.08  # Frena prima lateralmente
    DRAG_ROT = 0.05   # Frena la rotazione gradualmente
    
    # Il Pivot Point è definito localmente sull'asse Y della nave
    pivot_local_dist = pp_y 
    
    for i in range(n_steps):
        # 1. Calcolo Forze (Newton)
        f_y_total = (F_sx[1] + F_dx[1]) * 1000 * 9.81  # Forza Longitudinale
        f_x_total = (F_sx[0] + F_dx[0]) * 1000 * 9.81  # Forza Laterale
        
        # 2. Calcolo Momento su Pivot A
        r_sx = np.array([pos_sx_local[0], pos_sx_local[1] - pp_y])
        r_dx = np.array([pos_dx_local[0], pos_dx_local[1] - pp_y])
        
        m_sx = (r_sx[0] * F_sx[1] - r_sx[1] * F_sx[0]) * 1000 * 9.81
        m_dx = (r_dx[0] * F_dx[1] - r_dx[1] * F_dx[0]) * 1000 * 9.81
        total_moment = m_sx + m_dx
        
        # 3. ACCELERAZIONE (F = ma -> a = F/m)
        acc_surge = f_y_total / M_SURGE
        acc_sway = f_x_total / M_SWAY
        acc_rot = total_moment / I_ROT
        
        # 4. INTEGRAZIONE VELOCITÀ (V = V0 + a*t) - Qui sta l'inerzia!
        v_surge += acc_surge * dt
        v_sway += acc_sway * dt
        v_rot += acc_rot * dt
        
        # 5. APPLICAZIONE DRAG (Resistenza idrodinamica)
        v_surge *= (1.0 - DRAG_SURGE)
        v_sway *= (1.0 - DRAG_SWAY)
        v_rot *= (1.0 - DRAG_ROT)
        
        # 6. Applicazione Movimento Geometrico (Pivot Logic)
        
        # A. Rotazione RIGIDA attorno al Pivot A
        rad_h = np.radians(heading_deg)
        # Posizione attuale del pivot nel mondo
        to_pivot = np.array([-np.sin(rad_h), np.cos(rad_h)]) * pivot_local_dist
        current_pivot_pos = center_pos + to_pivot
        
        # Ruota heading
        d_theta = np.degrees(v_rot * dt)
        heading_deg -= d_theta 
        
        # Ricalcola centro basandosi sul nuovo angolo (Pivot rimane fermo nella rotazione pura)
        rad_new = np.radians(heading_deg)
        from_pivot_to_center = np.array([np.sin(rad_new), -np.cos(rad_new)]) * pivot_local_dist
        center_pos = current_pivot_pos + from_pivot_to_center
        
        # B. Traslazione Lineare (Surge & Sway muovono tutto il sistema)
        c, s = np.cos(rad_new), np.sin(rad_new)
        
        # Proiezione velocità locali su assi mondo
        dx_world = (v_surge * s + v_sway * c) * dt
        dy_world = (v_surge * c - v_sway * s) * dt
        
        center_pos[0] += dx_world
        center_pos[1] += dy_world
        
        if i % record_every == 0:
            results.append((center_pos[0], center_pos[1], heading_deg))
            
    return results
