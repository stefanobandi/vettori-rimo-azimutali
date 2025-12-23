G_ACCEL = 9.80665  # Accelerazione gravità
POS_THRUSTERS_Y = -12.0
POS_THRUSTERS_X = 2.7
BOLLARD_PULL_PER_ENGINE = 35.0 # Tonnellate

# Dati Dinamici per Predizione
MASS = 700000.0  # 700 tonnellate in kg
# Momento d'inerzia stimato per un corpo di 32.5m x 11.7m
IZ = 0.08 * MASS * (32.5**2 + 11.7**2) 

# Coefficienti di smorzamento (Damping) per raggiungere le velocità limite indicate
# Calcolati per equilibrare la spinta massima alle velocità di regime
DAMPING_LINEAR_X = 110000.0  # Per ~12.5 nodi avanti
DAMPING_LINEAR_Y = 850000.0  # Per ~1.5-2 nodi laterali (resistenza molto maggiore)
DAMPING_ANGULAR = 50000000.0 # Per stabilizzare la rotazione
