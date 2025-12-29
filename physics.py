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

# --- FISICA V8.0 ("PINNED BOW LOGIC") ---
# La resistenza laterale non è applicata al centro, ma allo Skeg (Prua).
# Questo blocca la prua e costringe la poppa a ruotare attorno ad essa.

def predict_trajectory(F_sx_vec, F_dx_vec, pos_sx, pos_dx, pp_y, total_time=30.0, steps=20):
    dt = 0.2
    n_total_steps = int(total_time / dt)
    record_every = max(1, n_total_steps // steps)
    
    # Geometria
    point_B_y = POS_THRUSTERS_Y 
    point_A_y = pp_y            
    lever_arm = point_A_y - point_B_y 
    
    # 1. Forze Propulsione (Base)
    F_prop_x = (F_sx_vec[0] + F_dx_vec[0]) * 1000 * 9.81
    F_prop_y = (F_sx_vec[1] + F_dx_vec[1]) * 1000 * 9.81
    
    # Momento Propulsione
    center_B = np.array([0.0, point_B_y])
    r_sx = pos_sx - center_B 
    r_dx = pos_dx - center_B
    
    # Coppia Motori
    M_prop = (r_sx[0]*F_sx_vec[1]*1000*9.81 - r_sx[1]*F_sx_vec[0]*1000*9.81) + \
             (r_dx[0]*F_dx_vec[1]*1000*9.81 - r_dx[1]*F_dx_vec[0]*1000*9.81)
    
    # 2. Inerzia (Masse)
    # Aumentiamo la Massa X per evitare scatti laterali istantanei ("Go-Kart feel")
    VIRTUAL_MASS_X = MASS * 4.0 
    VIRTUAL_MASS_Y = MASS * 1.2
    VIRTUAL_INERTIA = 70000000.0 * 2.0
    
    # Parametri Damping e Skeg
    # SKEG_POS_Y: Dove agisce la resistenza laterale? A Prua (es. +14m dal centro)
    SKEG_POS_Y = 14.0 
    # SKEG_COEFF: Quanto è "dura" l'acqua contro lo skeg? Altissimo.
    SKEG_COEFF = 2500000.0 
    
    DAMP_Y = 25000.0
    DAMP_N = 60000000.0
    
    x, y, heading_deg = 0.0, 0.0, 0.0
    u, v, r = 0.0, 0.0, 0.0
    
    results = []
    
    for i in range(n_total_steps):
        # --- CORREZIONE FISICA V8.0: Resistance at Skeg ---
        
        # 1. Calcolo Velocità Laterale allo SKEG (Prua)
        # La velocità di un punto P su un corpo rigido è: V_p = V_cm + Omega x R_p
        # u = Velocità laterale (Sway) del CM
        # r = Velocità angolare (Yaw Rate)
        # Se ruoto CCW (r > 0), la prua (Y > 0) si muove a Sinistra (-X).
        # Quindi: v_lat_skeg = u + (r * SKEG_POS_Y) ?? 
        # Controlliamo i segni:
        # r positivo (CCW). Skeg a y=+14. Vettoriale r x R = k * j = -i (Sinistra).
        # Quindi vel dovuta a rotazione è negativa.
        # Formula corretta: v_skeg_x = u - (r * SKEG_POS_Y) ??
        # No, in coordinate navali standard (x=avanti, y=destra) è diverso.
        # Nelle nostre coordinate: Y=Avanti, X=Destra. Heading 0.
        # r positivo (rotazione CCW, prua a sinistra).
        # Velocità tangenziale della prua dovuta a r: Direzione Sinistra (X negativo).
        # Quindi v_rot = - r * dist.
        # v_skeg_total_x = u (traslazione) - r * SKEG_POS_Y.
        
        v_skeg_x = u - (r * SKEG_POS_Y)
        
        # 2. Forza Resistenza allo Skeg
        # Si oppone alla velocità locale dello Skeg.
        F_skeg_res_x = - (v_skeg_x * SKEG_COEFF)
        
        # 3. Effetto della Forza Skeg sul CM
        # Aggiunge forza laterale totale
        F_total_x = F_prop_x + F_skeg_res_x
        
        # Aggiunge MOMENTO (Torque)
        # Una forza applicata a Prua (Y positiva) diretta a Sinistra (X negativa)
        # crea un momento CCW (positivo).
        # Momento = r x F. r=(0, Skeg_Y). F=(F_skeg, 0).
        # Cross product 2D: xFy - yFx -> 0 - SKEG_POS_Y * F_skeg_res_x
        M_skeg = - (SKEG_POS_Y * F_skeg_res_x)
        
        # Nota: Se F_skeg è verso sinistra (negativa), -14 * (-F) = Positivo (CCW).
        # Questo è CORRETTO: La resistenza a prua aiuta la rotazione se la poppa spinge.
        
        M_total = M_prop + M_skeg + (F_prop_x * (point_A_y - point_B_y)) # Steering lever
        
        # Resistenza Longitudinale e Rotazionale standard
        Fy_res = -(DAMP_Y * v + 1000.0 * v * abs(v))
        Mn_res = -(DAMP_N * r + 20000000.0 * r * abs(r))
        
        F_total_y = F_prop_y + Fy_res
        M_final = M_total + Mn_res
        
        # Accelerazioni
        du = F_total_x / VIRTUAL_MASS_X
        dv = F_total_y / VIRTUAL_MASS_Y
        dr = M_final / VIRTUAL_INERTIA
        
        u += du * dt
        v += dv * dt
        r += dr * dt
        
        # Integrazione Posizione
        rad = np.radians(heading_deg)
        dx_w = u * np.cos(rad) + v * np.sin(rad)
        dy_w = -u * np.sin(rad) + v * np.cos(rad)
        
        x += dx_w * dt
        y += dy_w * dt
        heading_deg -= np.degrees(r * dt)
        
        if i % record_every == 0:
            results.append((x, y, heading_deg))
            
    return results
