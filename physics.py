import numpy as np
import math

# --- COSTANTI FISICHE (Replica per sicurezza se non presenti in constants.py) ---
# Se constants.py le ha già, queste verranno sovrascritte o usate localmente
POS_THRUSTERS_X = 6.0    # Distanza laterale propulsori
POS_THRUSTERS_Y = -12.0  # Posizione longitudinale propulsori (Punto B)
POS_SKEG_Y = -25.0       # Posizione Skeg (Punto A)

def intersect_lines(p1, a1, p2, a2):
    """
    Calcola l'intersezione tra due vettori forza (usato per la grafica vettoriale).
    """
    rad1, rad2 = np.radians(a1), np.radians(a2)
    v1 = np.array([np.sin(rad1), np.cos(rad1)])
    v2 = np.array([np.sin(rad2), np.cos(rad2)])
    
    # Sistema lineare per trovare intersezione: p1 + t*v1 = p2 + u*v2
    # t*v1 - u*v2 = p2 - p1
    A = np.array([[v1[0], -v2[0]], [v1[1], -v2[1]]])
    b = p2 - p1
    
    try:
        x = np.linalg.solve(A, b)
        t, u = x[0], x[1]
        # Ritorniamo il punto se l'intersezione avviene "avanti" ai vettori (opzionale)
        return p1 + t * v1
    except np.linalg.LinAlgError:
        return None # Linee parallele

def check_wash_hit(emitter_pos, vector, target_pos, threshold=2.0):
    """
    Verifica se il flusso di un motore colpisce l'altro.
    """
    # Vettore dal motore emettitore al motore bersaglio
    to_target = target_pos - emitter_pos
    dist = np.linalg.norm(to_target)
    if dist < 0.1: return False
    
    # Normalizzazione
    vec_norm = vector / (np.linalg.norm(vector) + 0.0001)
    to_target_norm = to_target / dist
    
    # Prodotto scalare: se è vicino a 1, sono allineati
    alignment = np.dot(vec_norm, to_target_norm)
    
    # Se il flusso va verso il target (alignment > 0.9) e siamo vicini
    if alignment > 0.9 and dist < 15.0:
        return True
    return False

def predict_trajectory(F_sx, F_dx, pos_sx, pos_dx, user_pivot_y=None, total_time=30.0):
    """
    Calcola la predizione del movimento applicando la logica del PIVOT DINAMICO.
    Risolve i 3 scenari utente:
    1) Avanzamento (15/15) -> Pivot su Skeg (A)
    2) Spin (0/180) -> Pivot su Propulsori (B)
    3) Crabbing (90/90) -> Pivot su Skeg (A)
    """
    dt = 0.5 # Step temporale per la predizione
    steps = int(total_time / dt)
    
    # Stato iniziale (locale rispetto alla barca all'istante 0)
    # x, y sono 0, heading è 0 (Nord)
    cx, cy, ch = 0.0, 0.0, 0.0
    
    trajectory = []
    
    # Parametri inerziali simulati
    MASS = 500.0  
    MOMENT_OF_INERTIA = 4000.0
    DRAG_LIN = 0.8
    DRAG_ROT = 0.8
    
    # Velocità iniziali
    vx, vy, vomega = 0.0, 0.0, 0.0
    
    # --- ANALISI CONFIGURAZIONE MOTORI PER SCELTA PIVOT ---
    # Ricostruiamo gli angoli dai vettori forza passati (F_sx, F_dx sono vettori [x, y])
    # Nota: F_sx[0] è componente X, F_sx[1] è componente Y
    
    # Calcolo angoli in gradi
    ang_sx = np.degrees(np.arctan2(F_sx[0], F_sx[1])) % 360
    ang_dx = np.degrees(np.arctan2(F_dx[0], F_dx[1])) % 360
    
    angle_diff = abs(ang_sx - ang_dx)
    if angle_diff > 180: angle_diff = 360 - angle_diff
    
    # LOGICA DI SELEZIONE PIVOT (Cuore della richiesta)
    is_pure_spin = False
    
    # Scenario 2: Rotazione Pura (DX 0, SX 180 -> Diff 180)
    if 160 <= angle_diff <= 200:
        is_pure_spin = True
        pivot_y_active = POS_THRUSTERS_Y # Punto B (-12)
    else:
        # Scenario 1 (15/15) e Scenario 3 (90/90)
        # Usiamo lo Skeg come perno
        pivot_y_active = POS_SKEG_Y # Punto A (-25)
        
    # Sovrascrittura manuale se l'utente ha impostato un pivot specifico nella UI (opzionale)
    # Se vuoi forzare la logica automatica, ignora user_pivot_y nella fisica
    
    # Calcolo Forza Totale Locale
    F_tot_x = F_sx[0] + F_dx[0]
    F_tot_y = F_sx[1] + F_dx[1]
    
    # Calcolo Momento (Torque)
    # Il momento dipende dal pivot attivo.
    # Braccio di leva = Distanza tra punto applicazione forza (Motori, Y=-12) e Pivot
    
    # Se Pivot = B (-12), braccio Y = 0.
    # Se Pivot = A (-25), braccio Y = (-12) - (-25) = +13m.
    lever_arm_y = POS_THRUSTERS_Y - pivot_y_active
    
    # Torque generato da SX (Posizione X = -6)
    # T = Fy * dist_x - Fx * dist_y
    # dist_x = -6 - 0 = -6
    t_sx = (F_sx[1] * (-POS_THRUSTERS_X)) - (F_sx[0] * lever_arm_y)
    
    # Torque generato da DX (Posizione X = +6)
    t_dx = (F_dx[1] * (POS_THRUSTERS_X)) - (F_dx[0] * lever_arm_y)
    
    Torque_tot = t_sx + t_dx
    
    # Correzione specifica per Scenario 1 (Avanzamento e Virata)
    # Se non è spin puro, lo Skeg amplifica la virata se c'è componente laterale
    if not is_pure_spin and abs(F_tot_x) > 0.1:
        # Effetto timone passivo dello skeg
        Torque_tot += F_tot_x * 5.0 

    for _ in range(steps):
        # 1. Accelerazione (F = ma -> a = F/m)
        ax = F_tot_x / MASS
        ay = F_tot_y / MASS
        aomega = Torque_tot / MOMENT_OF_INERTIA
        
        # 2. Aggiornamento Velocità
        vx += ax * dt
        vy += ay * dt
        vomega += aomega * dt
        
        # 3. Smorzamento (Drag)
        vx *= DRAG_LIN
        vy *= DRAG_LIN
        vomega *= DRAG_ROT
        
        # 4. Aggiornamento Posizione (Nel sistema locale ruotato)
        # Convertiamo velocità locali in globali in base all'heading attuale
        rad_h = np.radians(ch)
        
        # Rotazione vettori velocità
        # X è Est, Y è Nord (Heading 0 = Nord)
        global_vx = vx * np.cos(rad_h) + vy * np.sin(rad_h)
        global_vy = -vx * np.sin(rad_h) + vy * np.cos(rad_h)
        # Verifica formula:
        # Se H=0 (N), cos=1, sin=0 -> Gvx = vx (Lat), Gvy = vy (Long).
        # Questo assume che vx sia laterale e vy longitudinale. 
        # Nella UI: Y è su (Longitudinale), X è destra (Laterale).
        # Quindi ok.
        
        cx += global_vx * dt
        cy += global_vy * dt
        ch += np.degrees(vomega * dt)
        
        trajectory.append((cx, cy, ch))
        
    return trajectory
