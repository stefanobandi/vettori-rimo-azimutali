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

# --- NUOVA LOGICA FISICA "CAPTAIN'S FEEL" ---
# Semplificata: Y spinge prua, X spinge poppa (rotazione)

def predict_trajectory(f_res_local, m_ton_m, total_time=30.0, steps=20):
    dt = 0.2
    n_total_steps = int(total_time / dt)
    record_every = max(1, n_total_steps // steps)
    
    # Stato iniziale
    x, y, heading_deg = 0.0, 0.0, 0.0
    u, v, r = 0.0, 0.0, 0.0 # Velocità surge (Y), sway (X), yaw rate (Rotazione)

    # Parametri "Sensoriali" (Tarati per simulare 700t in acqua)
    # Massa virtuale aumentata per simulare l'inerzia dell'acqua trascinata
    VIRTUAL_MASS_Y = MASS * 1.2   # Avanzare è "più facile"
    VIRTUAL_MASS_X = MASS * 2.5   # Spostarsi di lato è "molto pesante"
    VIRTUAL_INERTIA = 70000000.0 * 2.0 # Inerzia rotazionale alta
    
    # Smorzamento (Freno idrodinamico)
    # Valori alti impediscono al rimorchiatore di partire a razzo
    DAMPING_SURGE = 25000.0     # Freno avanzamento
    DAMPING_SWAY = 90000.0      # Freno laterale (alto per simulare lo Skeg che resiste)
    DAMPING_YAW = 60000000.0    # Freno rotazione
    
    # Conversione Forze Input
    # f_res_local[1] è la componente Y (Longitudinale)
    # f_res_local[0] è la componente X (Laterale)
    Fx_input = f_res_local[0] * 1000 * 9.81
    Fy_input = f_res_local[1] * 1000 * 9.81
    Mz_input = m_ton_m * 1000 * 9.81

    results = []
    
    for i in range(n_total_steps):
        # 1. Calcolo Forze Smorzanti (Resistenza)
        # Più vai veloce, più l'acqua ti frena (linear + quadratic approximation)
        Fx_drag = -(DAMPING_SWAY * u + 2000.0 * u * abs(u))
        Fy_drag = -(DAMPING_SURGE * v + 1000.0 * v * abs(v))
        Mz_drag = -(DAMPING_YAW * r + 10000000.0 * r * abs(r))
        
        # 2. Equazioni del Moto (F = ma -> a = F/m)
        du = (Fx_input + Fx_drag) / VIRTUAL_MASS_X
        dv = (Fy_input + Fy_drag) / VIRTUAL_MASS_Y
        dr = (Mz_input + Mz_drag) / VIRTUAL_INERTIA
        
        # 3. Aggiornamento Velocità
        u += du * dt # Velocità Laterale (Sway)
        v += dv * dt # Velocità Longitudinale (Surge)
        r += dr * dt # Velocità Rotazione (Yaw rate)
        
        # 4. Aggiornamento Posizione (Nel mondo)
        rad_h = np.radians(heading_deg)
        c, s = np.cos(rad_h), np.sin(rad_h)
        
        # Proiettiamo le velocità locali (u,v) nel sistema mondo (dx, dy)
        # Nota: v è l'asse Y nave (prua), u è l'asse X nave (destra)
        dx_world = u * c + v * s  # Errore comune: qui v è forward (Y), u è side (X)
                                  # Correggiamo rotazione standard:
                                  # X mondo = X_local * cos - Y_local * sin ? No.
                                  # Se heading è 0 (Nord/Alto):
                                  # v (Surge) -> muove su Y mondo
                                  # u (Sway) -> muove su X mondo
        
        # Rotazione vettoriale standard:
        # X_w = u * cos(h) - v * sin(h)  <-- Attenzione al sistema di riferimento grafico
        # Y_w = u * sin(h) + v * cos(h)
        
        # Nel nostro grafico Y è in alto (Prua) e Heading 0 è Nord.
        # u (Sway, laterale destra)
        # v (Surge, avanti)
        
        dx_world = u * np.cos(rad_h) + v * np.sin(rad_h) # Componente X
        dy_world = -u * np.sin(rad_h) + v * np.cos(rad_h) # Componente Y
        
        x += dx_world * dt
        y += dy_world * dt
        heading_deg -= np.degrees(r * dt) # Meno perché rotazione oraria è positiva nei grafici nautici
        
        if i % record_every == 0:
            results.append((x, y, heading_deg))
            
    return results
