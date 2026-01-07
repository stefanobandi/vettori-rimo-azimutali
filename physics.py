import numpy as np
import streamlit as st
from constants import *

# --- FUNZIONI DI MANOVRA (Invariate) ---
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
    if direction == "DRITTA": # Rotazione Oraria
        st.session_state.p1, st.session_state.a1 = potenza, 330
        st.session_state.p2, st.session_state.a2 = potenza, 210
    else: # SINISTRA (Rotazione Antioraria)
        st.session_state.p1, st.session_state.a1 = potenza, 150
        st.session_state.p2, st.session_state.a2 = potenza, 30

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

# --- FISICA: BRICK ON ICE V3.2 (Full Pivot Physics) ---
def predict_trajectory(total_surge_n, total_sway_n, total_torque_nm, pp_x_offset=0.0, pp_y_offset=0.0, total_time=30.0, steps=20):
    """
    Simula il moto integrando nel Body Frame.
    V3.2: Calcola Damping Laterale E Longitudinale nel punto esatto del Pivot (X, Y).
    Risolve bug di segno e include l'effetto di leva laterale.
    """
    dt = 0.2
    n_total_steps = int(total_time / dt)
    record_every = max(1, n_total_steps // steps)
    
    # Stato Iniziale (Body Frame)
    u, v, r = 0.0, 0.0, 0.0
    x_world, y_world, head_world = 0.0, 0.0, 0.0
    results = []
    
    for i in range(n_total_steps):
        
        # 1. Calcolo Velocità Locale al Pivot Point (Cinematica Rigorosa)
        # V_pp = V_cg + omega x r_pp
        # omega = (0, 0, r), r_pp = (x, y, 0)
        # Cross product: (-r*y, r*x, 0)
        
        # Velocità Sway al PP: v - r*y
        v_at_pp_x = v - (r * pp_y_offset)
        
        # Velocità Surge al PP: u + r*x
        v_at_pp_y = u + (r * pp_x_offset)

        # 2. Calcolo Resistenze (Damping) applicate al Pivot Point
        # Freno laterale (basato sulla velocità laterale locale)
        F_drag_sway = -DAMP_LINEAR_X * v_at_pp_x
        
        # Freno longitudinale (basato sulla velocità longitudinale locale)
        # Nota: Usiamo lo stesso coeff DAMP_Y globale, ma applicato localmente
        F_drag_surge = -DAMP_LINEAR_Y * v_at_pp_y
        
        # 3. Momenti Indotti dal Damping
        # Una forza applicata in un punto decentrato crea un momento (Torque = r x F)
        # Torque = x*Fy - y*Fx
        M_induced = (pp_x_offset * F_drag_surge) - (pp_y_offset * F_drag_sway)

        # Freno rotazionale puro
        M_drag_yaw = -DAMP_ANGULAR * r
        
        # 4. Somma Forze Totali e Momenti
        F_tot_surge = total_surge_n + F_drag_surge
        F_tot_sway  = total_sway_n + F_drag_sway
        M_tot_yaw   = total_torque_nm + M_drag_yaw + M_induced
        
        # 5. Legge di Newton
        acc_u = F_tot_surge / MASS
        acc_v = F_tot_sway / MASS
        acc_r = M_tot_yaw / INERTIA
        
        # 6. Integrazione
        u += acc_u * dt
        v += acc_v * dt
        r += acc_r * dt
        
        # 7. World Frame
        rad_h = np.radians(head_world)
        cos_h, sin_h = np.cos(rad_h), np.sin(rad_h)
        
        vx_world = v * cos_h + u * sin_h
        vy_world = -v * sin_h + u * cos_h
        
        x_world += vx_world * dt
        y_world += vy_world * dt
        head_world -= np.degrees(r * dt) 
        
        if i % record_every == 0:
            results.append((x_world, y_world, head_world))
            
    return results
