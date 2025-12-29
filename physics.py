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

# --- NUOVA LOGICA CINEMATICA "STERN-DRIVE" (V7.0) ---
# Concetto:
# 1. B (Poppa) si muove come un punto materiale spinto dalle forze X e Y.
# 2. A (Pivot) ruota attorno a B spinto dal Momento.
# 3. La posizione finale della nave è ricostruita partendo da B e dall'Heading.

def rotate_vec(vec, angle_deg):
    """Ruota un vettore 2D di un certo angolo."""
    rad = np.radians(angle_deg)
    c, s = np.cos(rad), np.sin(rad)
    return np.array([vec[0]*c - vec[1]*s, vec[0]*s + vec[1]*c])

def predict_trajectory(F_sx, F_dx, pos_sx_local, pos_dx_local, pp_y, total_time=30.0, steps=20):
    dt = 0.2
    n_steps = int(total_time / dt)
    record_every = max(1, n_steps // steps)
    
    # OFFSET GEOMETRICI (Costanti Locali)
    # B è a y = -12.0
    # Centro Nave è a y = 0.0
    # Distanza Centro -> B = 12.0m (B è "indietro")
    OFFSET_CENTER_FROM_B = np.array([0.0, 12.0]) 
    
    # Inizializzazione Stato Mondo
    # Partiamo con la nave a (0,0) con Heading 0.
    # Quindi B si trova a (0, -12) nel mondo.
    pos_B_world = np.array([0.0, -12.0])
    heading_deg = 0.0
    
    # Velocità (Accumulatori)
    v_surge_B = 0.0  # Velocità avanti/indietro di B
    v_sway_B = 0.0   # Velocità laterale di B
    v_rot = 0.0      # Velocità rotazione nave (Attorno a B)
    
    results = []
    
    # --- PARAMETRI FISICI ---
    # Masse e Inerzie (Sufficientemente alte per dare "peso")
    M_SURGE = 800.0   
    M_SWAY = 1500.0   # Più difficile spostare di lato
    I_ROT = 60000.0   
    
    # Smorzamento (Drag) - Simula l'acqua che frena
    DRAG_SURGE = 0.03
    DRAG_SWAY = 0.08  # Frena molto lateralmente (Skeg effect implicito)
    DRAG_ROT = 0.05
    
    for i in range(n_steps):
        # 1. CALCOLO FORZE E MOMENTI (Input)
        
        # Forze su B (Poppa)
        # Surge: Somma componenti Y
        F_surge_tot = (F_sx[1] + F_dx[1]) * 1000 * 9.81
        # Sway: Somma componenti X (Queste spostano B lateralmente)
        F_sway_tot = (F_sx[0] + F_dx[0]) * 1000 * 9.81
        
        # Momento Torcente (Che fa ruotare A attorno a B)
        # Usiamo il Pivot Point A come riferimento per la leva "percepita".
        # Leva = Distanza tra A (pp_y) e B (-12.0).
        dist_AB = pp_y - (-12.0)
        
        # Il Momento è generato da:
        # a) Spinta differenziale (Motori uno avanti uno indietro)
        #    Cross product tra posizione motore locale (rispetto a B) e forza
        #    Motore SX è a (-2.7, 0) rispetto a B. DX a (+2.7, 0).
        #    M_diff = r_sx X F_sx + r_dx X F_dx
        #    (In 2D: r_x * F_y - r_y * F_x)
        m_diff = (-2.7 * F_sx[1] - 0 * F_sx[0]) + (2.7 * F_dx[1] - 0 * F_dx[0])
        m_diff *= 1000 * 9.81
        
        # b) Momento generato dalla forza laterale totale (Sway) che fa leva sul pivot A?
        #    L'utente dice: "Spinta laterale X a poppa genera momento facendo leva su A"
        #    Se spingo a destra a poppa, e A è il perno, la nave ruota in senso antiorario.
        #    M_lat = F_sway_tot * dist_AB
        #    Segno: F_sway positiva (dx) -> Rotazione antioraria (positiva).
        #    Nota: Questo è il termine "Steering".
        m_steer = F_sway_tot * dist_AB
        
        M_total = m_diff + m_steer
        
        # 2. DINAMICA (Aggiornamento Velocità con Inerzia)
        acc_surge = F_surge_tot / M_SURGE
        acc_sway = F_sway_tot / M_SWAY
        acc_rot = M_total / I_ROT
        
        v_surge_B += acc_surge * dt
        v_sway_B += acc_sway * dt
        v_rot += acc_rot * dt
        
        # Applicazione Drag
        v_surge_B *= (1.0 - DRAG_SURGE)
        v_sway_B *= (1.0 - DRAG_SWAY)
        v_rot *= (1.0 - DRAG_ROT)
        
        # 3. CINEMATICA (Aggiornamento Posizione)
        
        # A. Muoviamo B (Poppa) nel mondo
        # Ruotiamo il vettore velocità locale (surge, sway) nell'orientamento attuale
        d_pos_B_local = np.array([v_sway_B, v_surge_B]) * dt
        d_pos_B_world = rotate_vec(d_pos_B_local, -heading_deg) # -heading per rotazione matematica std
        
        pos_B_world += d_pos_B_world
        
        # B. Ruotiamo la nave (Cambia heading)
        d_theta = np.degrees(v_rot * dt)
        heading_deg -= d_theta
        
        # C. Ricostruiamo il Centro della Nave per il plotting
        # Il centro è sempre a una distanza fissa e angolo fisso rispetto a B.
        # Vector B -> Center è (0, 12.0) locale.
        vec_B_to_Center_world = rotate_vec(OFFSET_CENTER_FROM_B, -heading_deg)
        pos_Center_world = pos_B_world + vec_B_to_Center_world
        
        if i % record_every == 0:
            results.append((pos_Center_world[0], pos_Center_world[1], heading_deg))
            
    return results
