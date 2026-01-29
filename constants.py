import numpy as np

# --- DIMENSIONI & GEOMETRIA ---
G_ACCEL = 9.80665

# Dati Nave
SHIP_LENGTH = 32.50
SHIP_WIDTH = 11.70

# Posizioni Geometriche
POS_THRUSTERS_Y = -12.0
POS_THRUSTERS_X = 2.7
POS_SKEG_Y = 5.0       
POS_STERN_Y = -12.0    

# Parametri Motori
BOLLARD_PULL_PER_ENGINE = 35.0 
MAX_THRUST = 343233.0   # 35 ton -> Newton

# --- FISICA (Tuning Quadratica 12.7 kt) ---
SHIP_MASS = 800000.0            
MOMENT_OF_INERTIA = 100000000.0 

# Calcolo Drag Quadratico: F = C * v^2
# V_max = 12.7 kt = 6.53 m/s
# F_tot = 686,466 N
# C_surge = 686466 / (6.53^2) = ~16,100
QUADRATIC_DAMPING_SURGE = 16100.0

# La resistenza laterale è molto più alta (5-8 volte) per via dello Skeg
QUADRATIC_DAMPING_SWAY = 120000.0

# Resistenza Rotazionale (mista per stabilità)
ANGULAR_DAMPING = 40000000.0     

# Offset
THRUSTER_X_OFFSET = POS_THRUSTERS_X
THRUSTER_Y_OFFSET = POS_THRUSTERS_Y

# Visualizzazione (Light Mode per contrasto Nero)
SCREEN_WIDTH = 1200
SCREEN_HEIGHT = 800
COLOR_SEA = '#B0C4DE' # LightSteelBlue
