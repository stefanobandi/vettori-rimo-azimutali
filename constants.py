G_ACCEL = 9.80665  # Accelerazione gravità
POS_THRUSTERS_Y = -12.0
POS_THRUSTERS_X = 2.7
BOLLARD_PULL_PER_ENGINE = 35.0 # Tonnellate

# --- Parametri di Predizione Movimento (Versione "Dual-Point Physics V2") ---
MASS = 700000.0  # kg (Dislocamento 700t)

# Coefficienti di resistenza idrodinamica (K = Forza / V^2)
K_Y = 16700.0    # Resistenza longitudinale

# NUOVO MODELLO FISICO: Resistenza laterale differenziata
# Skeg a prua molto "pesante" nell'acqua, poppa piatta "scivolosa"
K_X_BOW = 850000.0    # Aumentato per bloccare meglio la prua
K_X_STERN = 60000.0   # Diminuito per far scodare meglio la poppa

# Punti di applicazione delle resistenze laterali (rispetto al centro nave 0,0)
Y_BOW_CP = 14.0       # Centro di pressione prua
Y_STERN_CP = -10.0    # Centro di pressione poppa

K_W = 0.6e8       # Coefficiente resistenza rotazionale
I_Z = 60000000.0  # Momento d'inerzia leggermente ridotto per maggiore reattività
