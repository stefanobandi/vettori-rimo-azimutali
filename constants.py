import numpy as np

# --- CONFIGURAZIONE FISICA NAVALE (V7.1 - Auto Pivot Skeg) ---

# Dimensioni nave (ASD Tug)
SHIP_WIDTH = 12.0
SHIP_LENGTH = 32.0

# Massa e Inerzia
SHIP_MASS = 800000.0     # 800 Tonnellate
MOMENT_OF_INERTIA = 100000000.0  # Alta inerzia

# Posizioni Propulsori (A poppa)
THRUSTER_X_OFFSET = 3.5
THRUSTER_Y_OFFSET = -12.0 # Esattamente sotto la poppa piatta

# Posizioni Chiave Carena (Per calcolo PP)
POS_SKEG_Y = 5.0    # Punto di resistenza prua (Skeg)
POS_STERN_Y = -12.0 # Punto di spinta poppa

# Motori
MAX_THRUST = 750000.0 

# Damping (Resistenze)
LINEAR_DAMPING_SURGE = 50000.0
LINEAR_DAMPING_SWAY = 350000.0   # Molto alto per simulare lo Skeg
ANGULAR_DAMPING = 30000000.0     

# Visualizzazione
SCREEN_WIDTH = 1200
SCREEN_HEIGHT = 800
PIXELS_PER_METER = 10
