import numpy as np

# --- DIMENSIONI & GEOMETRIA ---
G_ACCEL = 9.80665  # Accelerazione gravità
POS_THRUSTERS_Y = -12.0
POS_THRUSTERS_X = 2.7
BOLLARD_PULL_PER_ENGINE = 35.0 # Tonnellate

# --- FISICA V6.2 (Dual Point Skeg Logic) ---
MASS = 700000.0  # kg (Dislocamento 700t)

# Resistenza Longitudinale (Surge)
K_Y = 16000.0      

# --- RESISTENZA LATERALE DIFFERENZIATA ---
# K_X_BOW (Skeg Prua): Deve essere alto per fare da perno.
K_X_BOW = 900000.0     

# K_X_STERN (Scafo Poppa): Deve permettere lo scivolamento.
K_X_STERN = 120000.0   

# Coordinate dei Centri di Pressione
Y_BOW_CP = 13.0       
Y_STERN_CP = -11.0    

# Resistenza Rotazionale Pura 
# CALIBRATO: Valore ottimizzato per rateo di rotazione 6°/s (Sea Trials)
# Se troppo alto blocca la nave, se troppo basso la fa girare come una trottola.
K_W = 3.5e8        

# Inerzia
I_Z = 85000000.0
