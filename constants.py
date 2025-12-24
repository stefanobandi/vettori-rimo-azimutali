G_ACCEL = 9.80665  # Accelerazione gravità
POS_THRUSTERS_Y = -12.0
POS_THRUSTERS_X = 2.7
BOLLARD_PULL_PER_ENGINE = 35.0 # Tonnellate

# --- Parametri di Predizione Movimento (Versione "Dual-Point Physics") ---
MASS = 700000.0  # kg (Dislocamento 700t)

# Coefficienti di resistenza idrodinamica (K = Forza / V^2)
K_Y = 16700.0    # Resistenza longitudinale (invariata)

# NUOVO MODELLO FISICO: Resistenza laterale differenziata
# Questo simula la presenza dello Skeg a prua e dello scafo piatto a poppa
K_X_BOW = 750000.0    # Altissima resistenza laterale a prua (Skeg)
K_X_STERN = 80000.0   # Bassa resistenza laterale a poppa (scivolamento)

# Punti di applicazione delle resistenze laterali (rispetto al centro nave 0,0)
Y_BOW_CP = 14.0       # Centro di pressione prua (avanti)
Y_STERN_CP = -10.0    # Centro di pressione poppa (indietro)

K_W = 0.6e8       # Coefficiente resistenza rotazionale (tarato per nuova fisica)
I_Z = 70000000.0  # Momento d'inerzia polare (fondamentale per effetto volano)
