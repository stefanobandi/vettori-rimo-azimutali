import math

# --- CONFIGURAZIONE GEOMETRICA RIMORCHIATORE ---
# Coordinate locali rispetto al centro geometrico (0,0)
# Assumiamo Y positivo verso la prua, Y negativo verso la poppa.

# PUNTO A: Skeg (il perno per le virate in avanzamento e crabbing)
# Posizionato a poppa estrema
PIVOT_A_Y = -25.0 

# PUNTO B: Centro Propulsori (il perno per le rotazioni pure)
# Posizionato tra i due azimuthali come indicato (X=0, Y=-12)
PIVOT_B_Y = -12.0

# Posizione laterale dei propulsori (distanza dal centro asse longitudinale)
PROP_OFFSET_X = 6.0  

def calculate_new_position(x, y, heading, az_l, pwr_l, az_r, pwr_r, dt=0.1):
    """
    Calcola la nuova posizione (x, y, heading) applicando la logica del 
    Doppio Pivot Point (Skeg vs Propulsori).
    """
    
    # 1. Conversione input in radianti e scala 0-1
    rad_l = math.radians(az_l)
    rad_r = math.radians(az_r)
    p_l = pwr_l / 100.0
    p_r = pwr_r / 100.0
    
    # 2. Calcolo Vettori di Spinta Locali (Local Frame)
    # Fx = spinta laterale, Fy = spinta longitudinale
    thrust_l_x = p_l * math.sin(rad_l)
    thrust_l_y = p_l * math.cos(rad_l)
    
    thrust_r_x = p_r * math.sin(rad_r)
    thrust_r_y = p_r * math.cos(rad_r)
    
    # Forza Totale Locale
    total_force_x = thrust_l_x + thrust_r_x
    total_force_y = thrust_l_y + thrust_r_y
    
    # 3. Logica di Selezione del Pivot Point
    # Calcoliamo la differenza angolare tra i due propulsori per capire la manovra
    angle_diff = abs(az_l - az_r)
    if angle_diff > 180:
        angle_diff = 360 - angle_diff
        
    # Identificazione Scenario: Rotazione Pura (Pure Spin)
    # Se la differenza è circa 180 gradi (es. 0 e 180), usiamo il punto B.
    # Usiamo un range di tolleranza (es. tra 160 e 200 gradi).
    is_pure_spin = False
    if 160 <= angle_diff <= 200:
        is_pure_spin = True
        
    # Selezione Coordinate Pivot attivo
    if is_pure_spin:
        # Scenario 2: Rotazione sul posto -> Perno B (Tra i propulsori)
        current_pivot_y = PIVOT_B_Y
    else:
        # Scenario 1 (Avanzamento) e 3 (Crabbing) -> Perno A (Skeg)
        current_pivot_y = PIVOT_A_Y

    # 4. Calcolo del Momento (Torque)
    # Il momento dipende dalla distanza tra il punto di applicazione della forza (i motori)
    # e il punto di rotazione (il Pivot attuale).
    
    # Braccio di leva Y: Distanza longitudinale tra i motori (B) e il pivot attivo.
    # Se Pivot è B, lever_arm_y = 0. Se Pivot è A, lever_arm_y = (-12) - (-25) = +13.
    lever_arm_y = PIVOT_B_Y - current_pivot_y
    
    # Torque Motore Sinistro (posizionato a -PROP_OFFSET_X, PIVOT_B_Y)
    # Momento = F_y * dist_x - F_x * dist_y
    # Nota sui segni: una forza Y positiva a sinistra (X negativa) crea rotazione oraria (+) o antioraria?
    # Qui usiamo la convenzione standard: X destra, Y su.
    # Posizione SX: (-6, -12). Pivot: (0, current_pivot_y).
    # Vettore r (braccio) = Posizione_Motore - Posizione_Pivot
    rx_l = -PROP_OFFSET_X - 0
    ry_l = lever_arm_y  # PIVOT_B_Y - current_pivot_y
    
    # Prodotto vettoriale 2D (r cross F) = rx * Fy - ry * Fx
    torque_l = (rx_l * thrust_l_y) - (ry_l * thrust_l_x)
    
    # Torque Motore Destro (posizionato a +PROP_OFFSET_X, PIVOT_B_Y)
    rx_r = PROP_OFFSET_X - 0
    ry_r = lever_arm_y
    
    torque_r = (rx_r * thrust_r_y) - (ry_r * thrust_r_x)
    
    total_torque = torque_l + torque_r
    
    # 5. Effetti Aggiuntivi per Realismo (Drift e Resistenza Skeg)
    
    # Se usiamo lo Skeg (Pivot A), l'avanzamento crea stabilità direzionale,
    # ma se c'è una componente laterale forte (Crabbing 90°), lo skeg resiste e fa ruotare la barca.
    if not is_pure_spin:
        # Amplifichiamo l'effetto rotatorio se c'è spinta laterale mentre si fa perno a poppa
        # Questo aiuta nello Scenario 3 (90°/90°) a far ruotare attorno allo skeg
        total_torque += total_force_x * 0.8 

    # 6. Applicazione del Movimento
    
    # Fattori di velocità (da calibrare a piacere)
    SPEED_FACTOR = 3.0
    ROTATION_FACTOR = 4.0
    
    if is_pure_spin:
        # La rotazione sul posto è solitamente più reattiva
        ROTATION_FACTOR *= 1.5

    # Delta nel sistema locale
    local_dx = total_force_x * SPEED_FACTOR * dt
    local_dy = total_force_y * SPEED_FACTOR * dt
    delta_theta = total_torque * ROTATION_FACTOR * dt
    
    # 7. Trasformazione in Coordinate Globali
    # Heading in gradi, convertiamo in radianti per la matrice di rotazione
    # Assumiamo Heading 0° = Nord (Y+), 90° = Est (X+)
    rad_h = math.radians(heading)
    sin_h = math.sin(rad_h)
    cos_h = math.cos(rad_h)
    
    # Rotazione vettore spostamento
    # Se H=0 (Nord): global_x = local_x, global_y = local_y
    # Se H=90 (Est): global_x = local_y, global_y = -local_x (dipende dalla convenzione assi)
    # Formula standard navigazione (X=Est, Y=Nord, H=0 su Y):
    global_dx = (local_dx * cos_h) + (local_dy * sin_h)
    global_dy = (local_dy * cos_h) - (local_dx * sin_h)
    
    # Aggiornamento stato
    new_x = x + global_dx
    new_y = y + global_dy
    new_heading = (heading + delta_theta) % 360
    
    return new_x, new_y, new_heading
