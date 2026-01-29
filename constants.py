import numpy as np

# --- DIMENSIONI & GEOMETRIA ---
G_ACCEL = 9.80665

# Dati Nave
SHIP_LENGTH = 32.50
SHIP_WIDTH = 11.70

# Posizioni Geometriche (Sistema Visuale: Y=Avanti, X=Destra)
POS_THRUSTERS_Y = -12.0
POS_THRUSTERS_X = 2.7
POS_SKEG_Y = 5.0       # Target Pivot per Fast Side Step
POS_STERN_Y = -12.0    

# Parametri Motori
BOLLARD_PULL_PER_ENGINE = 35.0 
MAX_THRUST = 735000.0   # ~75 tonnellate forza

# --- FISICA (Tuning per Max Speed 12.7 kt) ---
SHIP_MASS = 800000.0            
MOMENT_OF_INERTIA = 100000000.0 

# Damping calibrato: 
# F_tot = 1.47M Newton. V_max = 6.5 m/s (12.7kt).
# Coeff = F/V = ~226k
LINEAR_DAMPING_SURGE = 226000.0
LINEAR_DAMPING_SWAY = 650000.0   # Piu alto per deriva laterale
ANGULAR_DAMPING = 40000000.0     # Alto per smorzare oscillazioni

# Offset Fisici (Mapping coordinate)
THRUSTER_X_OFFSET = POS_THRUSTERS_X
THRUSTER_Y_OFFSET = POS_THRUSTERS_Y

# Visualizzazione
SCREEN_WIDTH = 1200
SCREEN_HEIGHT = 800
COLOR_SEA = (20, 30, 40)
