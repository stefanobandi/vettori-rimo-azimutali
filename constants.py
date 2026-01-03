import numpy as np

# --- DIMENSIONI & GEOMETRIA ---
G_ACCEL = 9.80665
POS_THRUSTERS_Y = -12.0
POS_THRUSTERS_X = 2.7
BOLLARD_PULL_PER_ENGINE = 35.0 

# --- FISICA V6.5 (Adaptive Pivot Logic) ---
MASS = 700000.0 

# Resistenza Longitudinale
# Mantiene la velocità sotto controllo durante le manovre
K_Y = 25000.0       

# --- RESISTENZE LATERALI BASE ---
# Questi sono i valori "di crociera".
# Vengono modificati dinamicamente in physics.py in base alla manovra.

# Resistenza Prua Base (Skeg)
K_X_BOW = 500000.0     

# Resistenza Poppa (Scafo)
# Costante. È il nostro riferimento fisso.
K_X_STERN = 120000.0    

# Coordinate Centri di Pressione
Y_BOW_CP = 13.0       
Y_STERN_CP = -11.0    

# Resistenza Rotazionale (Rotational Damping)
# Calibrato per 180 gradi in 30 sec a piena potenza
K_W = 5.0e7         
I_Z = 65000000.0
