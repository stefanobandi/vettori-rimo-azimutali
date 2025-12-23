G_ACCEL = 9.80665  # Accelerazione gravità
POS_THRUSTERS_Y = -12.0
POS_THRUSTERS_X = 2.7
BOLLARD_PULL_PER_ENGINE = 35.0 # Tonnellate

# --- Parametri di Predizione Movimento (Versione "Precision") ---
MASS = 700000.0  # kg (Dislocamento 700t)
# Coefficienti di resistenza idrodinamica (K = Forza / V^2)
# Tarati su: 12.5 kn (6.4 m/s) max avanti e ~2 kn (1.0 m/s) max laterale
K_Y = 16700.0    # Resistenza longitudinale
K_X = 645000.0   # Resistenza trasversale (molto più alta)
K_W = 1.2e8      # Resistenza rotazionale (smorzamento momento)
I_Z = 70000000.0 # Momento d'inerzia polare stimato (kg*m^2)
