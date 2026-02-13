import numpy as np

# --- DIMENSIONI & GEOMETRIA ---
G_ACCEL = 9.80665

# Dati Nave
SHIP_LENGTH = 32.50
SHIP_WIDTH = 11.70
MAX_SPEED_FORWARD_KT = 12.8
MAX_SPEED_REVERSE_KT = 12.0

# Posizioni Geometriche
POS_THRUSTERS_Y = -12.0
POS_THRUSTERS_X = 2.7
POS_SKEG_Y = 5.0        
POS_STERN_Y = -12.0     

# Pivot Point Default (Manuale)
DEFAULT_PP_X = 0.0
DEFAULT_PP_Y = 5.3

# Parametri Motori
BOLLARD_PULL_PER_ENGINE = 35.0 
MAX_THRUST = 343233.0   # 35 ton -> Newton

# --- FISICA (Tuning ASD 32m) ---
SHIP_MASS = 600000.0   # Dislocamento operativo (~600t)
                       
# MOMENTO D'INERZIA
# Ridotto drasticamente per permettere rotazioni veloci (180° in 30s)
MOMENT_OF_INERTIA = 12000000.0 

# DAMPING (Resistenze)

# Surge: Resistenza all'avanzamento
QUADRATIC_DAMPING_SURGE_FORWARD = 16100.0  # Per V_max ~12.8kt
QUADRATIC_DAMPING_SURGE_REVERSE = 18000.0  # Per V_max ~12.0kt

# Sway: Resistenza laterale (Skeg profondo)
# Aumentato a 135k per limitare la velocità laterale a ~1.2kt con 5t di spinta
QUADRATIC_DAMPING_SWAY = 135000.0

# Rotazione: Resistenza alla girata
# Ridotto a 18M per permettere al rimorchiatore di prendere giri velocemente
# Benchmark: 75% potenza + 15° azimuth -> rotazione 180° in 30s
ANGULAR_DAMPING = 18000000.0      

# Offset
THRUSTER_X_OFFSET = POS_THRUSTERS_X
THRUSTER_Y_OFFSET = POS_THRUSTERS_Y

# Visualizzazione (Light Mode per contrasto Nero)
SCREEN_WIDTH = 1200
SCREEN_HEIGHT = 800
COLOR_SEA = '#B0C4DE' # LightSteelBlue
