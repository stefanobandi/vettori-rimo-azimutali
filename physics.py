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

# --- LOGICA PREDITTIVA "CLASSROOM" (Geometrica A-B) ---
# Obiettivo: Rendere evidente che B (Poppa) ruota attorno ad A (Pivot)
# Downgrade fisico: Usiamo velocità proporzionali alle forze (Aristotelica) invece che F=ma (Newtoniana)
# per avere una risposta immediata e visiva, ideale per la spiegazione in aula.

def predict_trajectory(F_sx, F_dx, pos_sx_local, pos_dx_local, pp_y, total_time=30.0, steps=20):
    dt = 0.5 # Step temporale più ampio per calcolo veloce
    n_steps = int(total_time / dt)
    record_every = max(1, n_steps // steps)
    
    # Stato Iniziale (Coordinate Mondo)
    x, y, heading_deg = 0.0, 0.0, 0.0
    
    # Velocità (Inizialmente 0)
    v_long = 0.0 # Velocità longitudinale (Surge)
    v_rot = 0.0  # Velocità angolare (Rate of Turn)
    
    results = []
    
    # Parametri di "Smorzamento Didattico" (Frizione elevata per stabilizzare il moto)
    # Questi valori rendono il movimento meno "scivoloso" e più "meccanico"
    DRAG_LIN = 0.15 
    DRAG_ROT = 0.25
    FACTOR_FORCE_TO_SPEED = 0.00008 # Scaling per convertire tonnellate in velocità
    FACTOR_MOMENT_TO_ROT = 0.0005   # Scaling per convertire momento in rotazione
    
    for i in range(n_steps):
        # 1. Calcolo Forze Locali
        # Forza Longitudinale Totale (Surge) -> Muove A e B avanti/indietro
        fy_total = (F_sx[1] + F_dx[1]) * 1000 * 9.81
        
        # 2. Calcolo Momento Attorno al Pivot A
        # Il propulsore applica forza in pos_sx/dx.
        # Il braccio di leva è la distanza vettoriale dal Pivot A (0, pp_y) al propulsore.
        pivot_local = np.array([0.0, pp_y])
        
        # Vettori raggio dal Pivot ai propulsori
        r_sx = pos_sx_local - pivot_local
        r_dx = pos_dx_local - pivot_local
        
        # Momento = r cross F (2D: r_x*F_y - r_y*F_x)
        # Nota: Moltiplichiamo per costanti per unità fisiche coerenti
        m_sx = (r_sx[0] * F_sx[1] - r_sx[1] * F_sx[0]) * 1000 * 9.81
        m_dx = (r_dx[0] * F_dx[1] - r_dx[1] * F_dx[0]) * 1000 * 9.81
        total_moment_on_pivot = m_sx + m_dx
        
        # 3. Dinamica Semplificata (Velocità proporzionale alla forza con inerzia smorzata)
        # Aggiornamento Velocità Longitudinale
        v_long += (fy_total * FACTOR_FORCE_TO_SPEED) * dt
        v_long *= (1.0 - DRAG_LIN) # Frizione
        
        # Aggiornamento Velocità di Rotazione (Attorno ad A)
        v_rot += (total_moment_on_pivot * FACTOR_MOMENT_TO_ROT) * dt
        v_rot *= (1.0 - DRAG_ROT) # Frizione rotazionale
        
        # 4. Integrazione Posizione (Geometrica)
        rad = np.radians(heading_deg)
        c, s = np.cos(rad), np.sin(rad)
        
        # A. Spostamento Longitudinale (Lungo l'asse della nave)
        dx_surge = v_long * s * dt
        dy_surge = v_long * c * dt
        
        x += dx_surge
        y += dy_surge
        
        # B. Rotazione "Pura" Attorno al Pivot Corrente
        # In questo modello, la rotazione avviene attorno al punto A (pivot_local trasformato in mondo).
        # Tuttavia, per semplificare la visualizzazione di una traiettoria, ruotiamo l'heading
        # e muoviamo il centro della nave di conseguenza per mantenere il pivot "fermo" lateralmente.
        
        d_theta = np.degrees(v_rot * dt)
        heading_deg -= d_theta # Meno perché rotazione antioraria è positiva in math, ma bussola 0=N, 90=E
        
        # Nota: La rotazione attorno a un punto diverso dal centro geometrico (0,0) implica
        # che il centro geometrico (x,y) si sposti.
        # Spostamento del CG dovuto alla rotazione attorno a PP:
        # Delta_Pos = Rotazione(PP - CG) - (PP - CG)
        # Braccio dal CG (0,0 locale) al PP (0, pp_y locale) = pp_y
        # Se ruoto di d_theta, il CG si sposta lateralmente.
        # Implementazione semplificata: Aggiorniamo solo heading e surge per chiarezza visiva,
        # assumendo che l'occhio segua la sagoma.
        
        if i % record_every == 0:
            results.append((x, y, heading_deg))
            
    return results
