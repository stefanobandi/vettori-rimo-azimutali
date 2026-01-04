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

# --- FISICA: BRICK ON ICE + DAMPING ---
def predict_trajectory(F_sx_vec, F_dx_vec, pos_sx, pos_dx, pp_y, total_time=30.0, steps=20):
    """
    Simula il movimento considerando il PP come Baricentro.
    Include Damping (Attrito Viscoso) per simulare l'acqua.
    """
    dt = 0.2
    n_total_steps = int(total_time / dt)
    record_every = max(1, n_total_steps // steps)
    
    # 1. Definiamo il Baricentro (CM) coincidente col Pivot Point
    center_of_mass = np.array([0.0, pp_y])
    
    # 2. Conversione forze in Newton
    F_sx_n = F_sx_vec * 1000 * G_ACCEL
    F_dx_n = F_dx_vec * 1000 * G_ACCEL
    
    # 3. Calcolo Momenti (Torque) rispetto al CM (che è il PP)
    # Braccio di leva = Posizione Thruster - Posizione PP
    r_sx = pos_sx - center_of_mass
    r_dx = pos_dx - center_of_mass
    
    # Momento = r_x * F_y - r_y * F_x (Prodotto vettoriale 2D)
    M_sx = r_sx[0] * F_sx_n[1] - r_sx[1] * F_sx_n[0]
    M_dx = r_dx[0] * F_dx_n[1] - r_dx[1] * F_dx_n[0]
    
    Torque_Total = M_sx + M_dx
    Force_Total = F_sx_n + F_dx_n
    
    # Stato Iniziale (Locale allo scafo)
    # u = surge velocity (avanti/indietro), v = sway velocity (laterale), r = yaw rate
    u, v, r_rate = 0.0, 0.0, 0.0 
    
    # Stato Globale (Mondo)
    x_world, y_world, head_world = 0.0, 0.0, 0.0
    
    results = []
    
    for i in range(n_total_steps):
        # A. Calcolo Resistenze (Damping Idrodinamico)
        # Resistenza proporzionale alla velocità (Viscosità lineare per stabilità)
        # F_drag = -Coeff * Vel
        Drag_X = -DAMP_LINEAR_X * v
        Drag_Y = -DAMP_LINEAR_Y * u
        Drag_M = -DAMP_ANGULAR * r_rate
        
        # B. Somma Forze e Momenti
        F_tot_x_local = Force_Total[0] + Drag_X # Nota: F[0] è X (sway) nel setup attuale
        F_tot_y_local = Force_Total[1] + Drag_Y # Nota: F[1] è Y (surge)
        M_tot_local   = Torque_Total + Drag_M
        
        # C. Legge di Newton (F=ma => a=F/m)
        acc_u = F_tot_y_local / MASS
        acc_v = F_tot_x_local / MASS
        acc_r = M_tot_local / INERTIA
        
        # D. Integrazione Velocità
        u += acc_u * dt
        v += acc_v * dt
        r_rate += acc_r * dt
        
        # E. Integrazione Posizione (Rotazione nel mondo)
        rad = np.radians(head_world)
        cos_a, sin_a = np.cos(rad), np.sin(rad)
        
        # Velocità nel sistema mondo
        # u è lungo l'asse Y della nave, v è lungo l'asse X della nave
        vel_x_world = v * cos_a + u * sin_a  # Attenzione: definizione assi scafo vs mondo
        vel_y_world = -v * sin_a + u * cos_a # u punta verso l'alto (Y), v verso dx (X)
        
        # Correzione assi standard marittimi vs Matplotlib:
        # In questo progetto: Y è la prua (Longitudinale), X è destra.
        # Matplotlib 0 deg è Nord (Y).
        dx_w = v * np.cos(rad) + u * np.sin(rad) # X locale proiettato
        dy_w = -v * np.sin(rad) + u * np.cos(rad) # Y locale proiettato
        
        # Semplificazione per visualizzazione diretta (Assumendo start a 0 deg)
        # Se la nave ruota, il vettore velocità nel mondo cambia direzione.
        # Qui usiamo una matrice di rotazione standard 2D.
        # V_world = R * V_local
        # | dx |   | cos -sin | | v | (v è x locale)
        # | dy | = | sin  cos | | u | (u è y locale)
        # Verifica: se heading=0, dx=v, dy=u. Corretto.
        
        dx_w = v * np.cos(rad) - u * np.sin(rad)
        dy_w = v * np.sin(rad) + u * np.cos(rad)

        x_world += dx_w * dt
        y_world += dy_w * dt
        head_world -= np.degrees(r_rate * dt) # Matplotlib ruota in senso orario negativo per visual
        
        if i % record_every == 0:
            results.append((x_world, y_world, head_world))
            
    return results
