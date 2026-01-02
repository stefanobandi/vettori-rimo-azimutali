import numpy as np

# --- DIMENSIONI & GEOMETRIA ---
G_ACCEL = 9.80665  # Accelerazione gravità
POS_THRUSTERS_Y = -12.0
POS_THRUSTERS_X = 2.7
BOLLARD_PULL_PER_ENGINE = 35.0 # Tonnellate

# --- FISICA V6.2 (Dual Point Skeg Logic) ---
MASS = 700000.0  # kg (Dislocamento 700t)

# Resistenza Longitudinale (Surge)
# Resistenza all'avanzamento classico
K_Y = 16000.0      

# --- NUOVI PARAMETRI RESISTENZA LATERALE DIFFERENZIATA ---
# Questi valori definiscono il comportamento "Perno su A" vs "Perno su B"

# Resistenza Laterale PRUA (Skeg)
# Valore ALTISSIMO: Simula la deriva che "taglia" l'acqua. 
# Impedisce alla prua di scarrocciare lateralmente.
K_X_BOW = 950000.0     

# Resistenza Laterale POPPA (Scafo piatto/Pod)
# Valore MEDIO: La poppa deve scivolare se spinta dai motori (90°), 
# ma deve fare resistenza se ruotiamo sul posto (000°/180°).
K_X_STERN = 120000.0   

# Coordinate dei Centri di Pressione (rispetto al centro nave 0,0)
# Definiscono dove agiscono le resistenze dell'acqua
Y_BOW_CP = 13.0       # Lo Skeg è molto a prua
Y_STERN_CP = -11.0    # La resistenza di poppa è vicino ai propulsori

# Resistenza Rotazionale Pura (Attrito dell'acqua che frena la rotazione)
# CALIBRATO: Aumentato a 6.0e8 per limitare ROT a ~6°/s con piena potenza (Sea Trials)
K_W = 6.0e8        
I_Z = 90000000.0  # Momento d'inerzia (Aumentato leggermente per massa 700t)
