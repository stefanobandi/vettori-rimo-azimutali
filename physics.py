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

# --- FISICA ORIGINALE V6.0 (Ripristinata) ---
# Questa logica usa Newton (F=ma) + Correzione Skeg.
# È la più stabile per simulare un corpo rigido in acqua.

def predict_trajectory(F_sx_vec, F_dx_vec, pos_sx, pos_dx, pp_y, total_time=30.0, steps=20):
    dt = 0.2
    n_total_steps = int(total_time / dt)
    record_every = max(1, n_total_steps // steps)
    
    # Parametri Modello
    point_B_y = POS_THRUSTERS_Y # -12.0
    point_A_y = pp_y            # 5.30 default (o variabile)
    
    # Braccio di Leva
    lever_arm = point_A_y - point_B_y 
    
    # 1. Calcolo Forza Totale X e Y
    F_total_x = (F_sx_vec[0] + F_dx_vec[0]) * 1000 * 9.81
    F_total_y = (F_sx_vec[1] + F_dx_vec[1]) * 1000 * 9.81
    
    # 2. Calcolo Momenti
    center_B = np.array([0.0, point_B_y])
    r_sx = pos_sx - center_B 
    r_dx = pos_dx - center_B
    
    # Momento Puro su B (Coppia dei motori)
    M_pure_B = (r_sx[0]*F_sx_vec[1]*1000*9.81 - r_sx[1]*F_sx_vec[0]*1000*9.81) + \
               (r_dx[0]*F_dx_vec[1]*1000*9.81 - r_dx[1]*F_dx_vec[0]*1000*9.81)
               
    # Momento da Leva (Steering effect)
    M_lever = F_total_x * lever_arm
    M_total = M_pure_B + M_lever

    # Inerzia e Masse Virtuali (Per simulare 700t)
    VIRTUAL_MASS_X = MASS * 2.0
    VIRTUAL_MASS_Y = MASS * 1.2
    VIRTUAL_INERTIA = 70000000.0 * 1.5
    
    # Smorzamento (Resistenza idrodinamica)
    DAMP_X = 80000.0
    DAMP_Y = 25000.0
    DAMP_N = 60000000.0
    
    # Stato Iniziale
    x, y, heading_deg = 0.0, 0.0, 0.0
    u, v, r = 0.0, 0.0, 0.0
    
    results = []
    
    for i in range(n_total_steps):
        # Calcolo Resistenza (Proporzionale alla velocità)
        Fx_res = -(DAMP_X * u + 5000.0 * u * abs(u))
        Fy_res = -(DAMP_Y * v + 1000.0 * v * abs(v))
        Mn_res = -(DAMP_N * r + 20000000.0 * r * abs(r))
        
        # --- EFFETTO SKEG (Il segreto della stabilità) ---
        # Quando la nave ruota (r), lo skeg a prua resiste lateralmente.
        # Questo crea una forza che si oppone allo scarroccio della poppa durante la rotazione.
        Fx_skeg_lift = r * 950000.0 
        
        # Accelerazioni (F = ma)
        du = (F_total_x + Fx_res + Fx_skeg_lift) / VIRTUAL_MASS_X
        dv = (F_total_y + Fy_res) / VIRTUAL_MASS_Y
        dr = (M_total + Mn_res) / VIRTUAL_INERTIA
        
        u += du * dt
        v += dv * dt
        r += dr * dt
        
        # Integrazione Posizione
        rad = np.radians(heading_deg)
        # Velocità rispetto al mondo
        dx_w = u * np.cos(rad) + v * np.sin(rad)
        dy_w = -u * np.sin(rad) + v * np.cos(rad)
        
        x += dx_w * dt
        y += dy_w * dt
        heading_deg -= np.degrees(r * dt)
        
        if i % record_every == 0:
            results.append((x, y, heading_deg))
            
    return results
