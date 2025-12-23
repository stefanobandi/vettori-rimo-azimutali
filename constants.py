G_ACCEL = 9.80665  # Accelerazione gravità
POS_THRUSTERS_Y = -12.0
POS_THRUSTERS_X = 2.7
BOLLARD_PULL_PER_ENGINE = 35.0 # Tonnellate (Totale 70t)

# Dati Dinamici per Predizione
MASS = 700000.0  # 700 tonnellate in kg
# Momento d'inerzia stimato
IZ = 0.08 * MASS * (32.5**2 + 11.7**2) 

# Coefficienti di smorzamento (Damping) per velocità limite
DAMPING_LINEAR_X = 110000.0  # Per ~12.5 nodi avanti
DAMPING_LINEAR_Y = 850000.0  # Per ~1.5-2 nodi laterali
DAMPING_ANGULAR = 50000000.0 # Per stabilizzare la rotazione
