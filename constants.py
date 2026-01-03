import numpy as np

# --- DIMENSIONI & GEOMETRIA ---
G_ACCEL = 9.80665  # Accelerazione gravità
POS_THRUSTERS_Y = -12.0
POS_THRUSTERS_X = 2.7
BOLLARD_PULL_PER_ENGINE = 35.0 # Tonnellate

# --- FISICA V6.3 (Calibrazione Tactical Diameter 90m) ---
MASS = 700000.0  # kg (Dislocamento 700t)

# Resistenza Longitudinale (Surge)
# Aumentata per simulare la perdita di velocità in accostata (Induced Drag)
# Aiuta a mantenere il raggio di virata stretto (45m) senza schizzare via tangente.
K_Y = 22000.0       

# --- PARAMETRI RESISTENZA LATERALE DIFFERENZIATA ---

# Resistenza Laterale PRUA (Skeg)
# AUMENTATA DRASTICAMENTE: Lo Skeg deve fare da perno solido.
# Valore precedente: 950.000 -> Nuovo: 2.500.000
# Questo costringe la prua a stare dentro la curva (Raggio 45m).
K_X_BOW = 2500000.0     

# Resistenza Laterale POPPA (Scafo piatto/Pod)
# Manteniamo un valore medio/basso per permettere alla poppa di derapare 
# spinta dai motori.
K_X_STERN = 120000.0    

# Coordinate dei Centri di Pressione (rispetto al centro nave 0,0)
Y_BOW_CP = 13.0       # Lo Skeg è molto a prua
Y_STERN_CP = -11.0    # La resistenza di poppa è vicino ai propulsori

# Resistenza Rotazionale Pura (Momento smorzante)
# RIDOTTA DRASTICAMENTE: Era il freno a mano tirato.
# Valore precedente: 4.0e8 -> Nuovo: 6.5e7
# Questo permette di raggiungere i 180° in 30 secondi (6 gradi/sec).
K_W = 6.5e7         

# Momento d'inerzia (Effetto volano)
# Leggermente ridotto per rendere la risposta ai comandi più pronta.
I_Z = 65000000.0
