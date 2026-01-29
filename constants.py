import numpy as np

# --- DIMENSIONI & GEOMETRIA ---
G_ACCEL = 9.80665

# Dati Nave
SHIP_LENGTH = 32.50
SHIP_WIDTH = 11.70

# Posizioni Geometriche
POS_THRUSTERS_Y = -12.0
POS_THRUSTERS_X = 2.7
POS_SKEG_Y = 5.0       # Target per Fast Side Step
POS_STERN_Y = -12.0    

# Parametri Motori
BOLLARD_PULL_PER_ENGINE = 35.0 
MAX_THRUST = 735000.0   # ~75 tonnellate forza

# --- FISICA (Tuning 12.7 kt) ---
SHIP_MASS = 800000.0            
MOMENT_OF_INERTIA = 100000000.0 

# Calcolo Damping per V_max = 12.7 kt (6.5 m/s)
# F_tot = 2 * MAX_THRUST = 1,470,000 N
# Damping = F / V = 1,470,000 / 6.5 = ~226,000
LINEAR_DAMPING_SURGE = 226000.0
LINEAR_DAMPING_SWAY = 650000.0   # Più alto per deriva laterale
ANGULAR_DAMPING = 30000000.0    

# Offset
THRUSTER_X_OFFSET = POS_THRUSTERS_X
THRUSTER_Y_OFFSET = POS_THRUSTERS_Y

# Visualizzazione
SCREEN_WIDTH = 1200
SCREEN_HEIGHT = 800
COLOR_SEA = (20, 30, 40)
