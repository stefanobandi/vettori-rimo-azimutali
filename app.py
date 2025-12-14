import streamlit as st
import numpy as np
import matplotlib.pyplot as plt

# --- Configurazione Pagina ---
st.set_page_config(page_title="Simulatore ASD", layout="centered")

st.title("⚓ Simulatore Vettoriale ASD")
st.markdown("Strumento didattico per la formazione sui propulsori azimutali.")

# --- Colonna Sinistra (Input Dati) ---
col1, col2 = st.columns(2)

with col1:
    st.markdown("### 🔴 Sinistra (Port)")
    deg1 = st.slider("Azimut SX (°)", 0, 360, 0, key="a1")
    pow1 = st.slider("Potenza SX (%)", 0, 100, 50, key="p1")

with col2:
    st.markdown("### 🟢 Dritta (Stbd)")
    deg2 = st.slider("Azimut DX (°)", 0, 360, 0, key="a2")
    pow2 = st.slider("Potenza DX (%)", 0, 100, 50, key="p2")

# --- Calcoli Matematici ---
# Conversione in radianti
rad1 = np.radians(deg1)
rad2 = np.radians(deg2)

# Calcolo componenti (U=X, V=Y)
# Nota: In Matplotlib 'quiver', se usiamo angles='xy', la direzione segue gli assi standard.
# Per simulare la bussola (0° in alto, 90° a destra):
# X = sin(angolo), Y = cos(angolo)
u1 = pow1 * np.sin(rad1)
v1 = pow1 * np.cos(rad1)

u2 = pow2 * np.sin(rad2)
v2 = pow2 * np.cos(rad2)

# Vettore Risultante
res_u = u1 + u2
res_v = v1 + v2
res_pow = np.sqrt(res_u**2 + res_v**2)

# --- Visualizzazione Grafica ---
st.divider()
fig, ax = plt.subplots(figsize=(6, 6))

# Cerchio del rimorchiatore e assi
circle = plt.Circle((0, 0), 10, color='gray', fill=False, linestyle='--')
ax.add_artist(circle)
ax.axhline(0, color='black', linewidth=0.5, alpha=0.5)
ax.axvline(0, color='black', linewidth=0.5, alpha=0.5)

# Disegno Vettori
# 1. Motore Sinistra (ROSSO)
ax.quiver(0, 0, u1, v1, angles='xy', scale_units='xy', scale=1, 
          color='red', label='Sinistra', width=0.015, alpha=0.8)

# 2. Motore Dritta (VERDE)
ax.quiver(0, 0, u2, v2, angles='xy', scale_units='xy', scale=1, 
          color='green', label='Dritta', width=0.015, alpha=0.8)

# 3. Risultante (BLU SPESSA)
ax.quiver(0, 0, res_u, res_v, angles='xy', scale_units='xy', scale=1, 
          color='blue', label='Risultante', width=0.030) # Width raddoppiata

# Impostazioni Assi
ax.set_xlim(-200, 200)
ax.set_ylim(-200, 200)
ax.set_aspect('equal')
ax.grid(True, linestyle=':', alpha=0.6)

# Etichette Bussola
ax.text(0, 185, "PRUA (0°)", ha='center', weight='bold')
ax.text(185, 0, "90°", va='center')
ax.text(0, -195, "180°", ha='center')
ax.text(-190, 0, "270°", va='center')

# Legenda fissa in basso a destra
ax.legend(loc='lower right')

# Rimuovi i numeri dagli assi (più pulito per la formazione)
ax.set_xticklabels([])
ax.set_yticklabels([])

st.pyplot(fig)

# Pannello informativo finale
st.success(f"**Risultante:** {res_pow:.1f} % (Teorica)")
