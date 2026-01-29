import numpy as np

# --- DIMENSIONI & GEOMETRIA ---
G_ACCEL = 9.80665

# Dati Nave Reali
SHIP_LENGTH = 32.50
SHIP_WIDTH = 11.70

# Posizioni Geometriche (V6.62 + V7.1 Physics)
POS_THRUSTERS_Y = -12.0
POS_THRUSTERS_X = 2.7  # Usato per la grafica V6.62
POS_SKEG_Y = 5.0       # V7.1: Punto di resistenza prua
POS_STERN_Y = -12.0    # V7.1: Punto di spinta poppa

# Parametri Motori
BOLLARD_PULL_PER_ENGINE = 35.0 
MAX_THRUST = 750000.0   # Newton (approx 75 ton)

# --- FISICA "HEAVY & STABLE" (V7.1 Tuning) ---
SHIP_MASS = 800000.0            # 800 Tonnellate
MOMENT_OF_INERTIA = 100000000.0 # Altissima inerzia

# Damping (Resistenza Idrodinamica)
LINEAR_DAMPING_SURGE = 50000.0
LINEAR_DAMPING_SWAY = 350000.0  # Alto per effetto Skeg
ANGULAR_DAMPING = 30000000.0    # Alto per stabilità rotta

# Offset propulsori per calcolo fisico (coincidono con grafica)
THRUSTER_X_OFFSET = POS_THRUSTERS_X
THRUSTER_Y_OFFSET = POS_THRUSTERS_Y

# --- VISUALIZZAZIONE ---
SCREEN_WIDTH = 1200
SCREEN_HEIGHT = 800
PIXELS_PER_METER = 10
COLOR_SEA = (20, 30, 40)
