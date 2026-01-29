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
# 70 tonnellate totali = 35 ton per motore
BOLLARD_PULL_PER_ENGINE = 35.0 
MAX_THRUST = 343233.0   # 35,000 kg * 9.80665 = ~343kN

# --- FISICA (Tuning 12.7 kt) ---
SHIP_MASS = 800000.0            
MOMENT_OF_INERTIA = 100000000.0 

# Calcolo Damping:
# Forza Totale = 2 * 343,233 = 686,466 N
# Velocità Target = 12.7 kt = 6.53 m/s
# Damping = F / V = 686466 / 6.53 = ~105,125
LINEAR_DAMPING_SURGE = 105125.0
LINEAR_DAMPING_SWAY = 350000.0   # 3.5x Surge (Deriva limitata dallo Skeg)
ANGULAR_DAMPING = 40000000.0     

# Offset
THRUSTER_X_OFFSET = POS_THRUSTERS_X
THRUSTER_Y_OFFSET = POS_THRUSTERS_Y

# Visualizzazione
SCREEN_WIDTH = 1200
SCREEN_HEIGHT = 800
COLOR_SEA = (20, 30, 40)
