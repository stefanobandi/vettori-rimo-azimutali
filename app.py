import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import PathPatch
from matplotlib.path import Path

# --- Configurazione Pagina ---
st.set_page_config(page_title="ASD Centurion", layout="wide")

# --- Titolo e Intestazione ---
st.title("⚓ Rimorchiatore ASD 'CENTURION'")
st.markdown("""
Simulatore vettoriale per formazione manovra.
**Bollard Pull Max:** 70 tonnellate.
""")

# --- Sidebar: Configurazione Pivot Point ---
st.sidebar.header("📍 Configurazione Pivot Point")
st.sidebar.markdown("Sposta il centro di rotazione (PP) della nave.")

# Limiti basati sulle dimensioni nave: Larghezza 11.7m (±5.85), Lunghezza 32.5m (diciamo ±16m circa)
pp_y = st.sidebar.slider("Posizione Longitudinale (Y)", -16.0, 16.0, 5.42, 0.1, help="Positivo = verso Prua, Negativo = verso Poppa")
pp_x = st.sidebar.slider("Posizione Trasversale (X)", -5.0, 5.0, 0.0, 0.1, help="Spostamento laterale del PP")

# --- Layout a Colonne per i Motori ---
col1, col_mid, col2 = st.columns([1, 0.2, 1])

with col1:
    st.error("### 🔴 Port (Sinistra)")
    # Input grafico simulato con slider
    p1_val = st.slider("Potenza (%)", 0, 100, 50, key="p1")
    a1_val = st.slider("Azimut (°)", 0, 360, 0, key="a1")
    
    # Calcolo Tonnellate
    ton1 = (p1_val / 100) * 35 # 35 ton è la metà di 70 (assumendo 2 motori uguali)
    
    # Visualizzatore a "Orologio" (Plot Matplotlib piccolo)
    fig_gauge1, ax_g1 = plt.subplots(figsize=(2, 2), subplot_kw={'projection': 'polar'})
    ax_g1.set_theta_zero_location('N')
    ax_g1.set_theta_direction(-1)
    ax_g1.set_rticks([])
    ax_g1.set_xticks(np.radians([0, 90, 180, 270]))
    ax_g1.set_xticklabels(['N', 'E', 'S', 'W'], fontsize=8)
    # Freccia indicatrice
    ax_g1.arrow(np.radians(a1_val), 0, 0, 1, color='red', width=0.15, head_width=0, length_includes_head=True)
    ax_g1.set_ylim(0, 1.1)
    ax_g1.grid(False)
    st.pyplot(fig_gauge1, use_container_width=False)
    st.markdown(f"**Spinta:** {ton1:.1f} ton @ {a1_val:03d}°")

with col2:
    st.success("### 🟢 Starboard (Dritta)")
    p2_val = st.slider("Potenza (%)", 0, 100, 50, key="p2")
    a2_val = st.slider("Azimut (°)", 0, 360, 0, key="a2")
    
    ton2 = (p2_val / 100) * 35
    
    fig_gauge2, ax_g2 = plt.subplots(figsize=(2, 2), subplot_kw={'projection': 'polar'})
    ax_g2.set_theta_zero_location('N')
    ax_g2.set_theta_direction(-1)
    ax_g2.set_rticks([])
    ax_g2.set_xticks(np.radians([0, 90, 180, 270]))
    ax_g2.set_xticklabels(['N', 'E', 'S', 'W'], fontsize=8)
    ax_g2.arrow(np.radians(a2_val), 0, 0, 1, color='green', width=0.15, head_width=0, length_includes_head=True)
    ax_g2.set_ylim(0, 1.1)
    ax_g2.grid(False)
    st.pyplot(fig_gauge2, use_container_width=False)
    st.markdown(f"**Spinta:** {ton2:.1f} ton @ {a2_val:03d}°")

# --- Calcoli Vettoriali ---
# Coordinate Propulsori (in metri)
pos_sx = np.array([-2.7, -12.0])
pos_dx = np.array([2.7, -12.0])
pos_center_stern = np.array([0.0, -12.0]) # Punto di applicazione risultante (mezzeria poppa)

# Conversione Angoli in Radianti (Nautici: 0=N, 90=E -> Matematici: X=sin, Y=cos)
rad1 = np.radians(a1_val)
rad2 = np.radians(a2_val)

# Componenti Vettori (X, Y) in Tonnellate
u1 = ton1 * np.sin(rad1) # Componente X (Laterale)
v1 = ton1 * np.cos(rad1) # Componente Y (Longitudinale)

u2 = ton2 * np.sin(rad2)
v2 = ton2 * np.cos(rad2)

# Risultante Totale
res_u = u1 + u2
res_v = v1 + v2
res_ton = np.sqrt(res_u**2 + res_v**2)

# Calcolo Direzione Risultante (in gradi nautici 0-360)
# arctan2 restituisce radianti matematici (da asse X), dobbiamo convertire
res_angle_rad = np.arctan2(res_u, res_v) 
res_angle_deg = np.degrees(res_angle_rad)
if res_angle_deg < 0:
    res_angle_deg += 360

# --- Visualizzazione Grafico Principale ---
st.divider()
col_graph, col_data = st.columns([2, 1])

with col_graph:
    fig, ax = plt.subplots(figsize=(8, 10))
    
    # 1. Disegno Scafo "Centurion" (32.5 x 11.7)
    # Rettangolo centrale + Prua Arrotondata
    # Coordinate rettangolo (centrato su 0,0 circa)
    half_w = 11.7 / 2
    len_ship = 32.5
    stern_y = -16.25 # Poppa
    bow_y = 16.25    # Prua (punto estremo)
    
    # Disegno scafo stilizzato usando Path per avere la prua tonda
    verts = [
        (-half_w, stern_y), # Poppa sinistra
        (half_w, stern_y),  # Poppa dritta
        (half_w, 10),       # Inizio curvatura prua dritta
        (0, bow_y),         # Punta prua
        (-half_w, 10),      # Inizio curvatura prua sinistra
        (-half_w, stern_y), # Chiudi
    ]
    codes = [Path.MOVETO, Path.LINETO, Path.LINETO, Path.CURVE3, Path.CURVE3, Path.LINETO]
    path = Path(verts, codes)
    patch = PathPatch(path, facecolor='#e0e0e0', edgecolor='black', lw=2)
    ax.add_patch(patch)

    # 2. Pivot Point
    ax.scatter(pp_x, pp_y, color='black', s=150, zorder=10, label="Pivot Point")
    ax.text(pp_x + 0.5, pp_y, "PP", fontsize=10, fontweight='bold')

    # 3. Posizione Motori (Pallini grigi)
    ax.scatter(pos_sx[0], pos_sx[1], color='gray', s=50)
    ax.scatter(pos_dx[0], pos_dx[1], color='gray', s=50)

    # 4. Vettori Spinta
    # Scala: 1 tonnellata = 0.5 unità grafico (per far stare le frecce)
    scale_factor = 0.4 
    
    # SX (Rosso)
    ax.arrow(pos_sx[0], pos_sx[1], u1*scale_factor, v1*scale_factor, 
             head_width=1.5, head_length=1.5, fc='red', ec='red', width=0.3, alpha=0.9)
    
    # DX (Verde)
    ax.arrow(pos_dx[0], pos_dx[1], u2*scale_factor, v2*scale_factor, 
             head_width=1.5, head_length=1.5, fc='green', ec='green', width=0.3, alpha=0.9)

    # Risultante (Blu - Parte dal CENTRO POPPA tra i motori)
    # Nota: alpha=0.5 per trasparenza
    ax.arrow(pos_center_stern[0], pos_center_stern[1], res_u*scale_factor, res_v*scale_factor, 
             head_width=2.5, head_length=2.5, fc='blue', ec='blue', width=0.8, alpha=0.4, label='Risultante')

    # Setup Assi
    ax.set_xlim(-25, 25)
    ax.set_ylim(-30, 30)
    ax.set_aspect('equal')
    ax.grid(True, linestyle='--', alpha=0.3)
    ax.set_title("Vista dall'alto (Prua in alto)", fontsize=10)
    
    # Rimuovi numeri assi
    ax.set_xticks([])
    ax.set_yticks([])
    
    st.pyplot(fig)

with col_data:
    st.markdown("### 📊 Dati Real-Time")
    st.metric(label="Tiro Totale Risultante", value=f"{res_ton:.1f} ton")
    st.metric(label="Direzione Spinta (vs Nord)", value=f"{res_angle_deg:.0f}°")
    
    st.write("---")
    st.markdown("**Analisi Vettoriale:**")
    st.write(f"Componente Longitudinale (Surge): **{res_v:.1f} ton**")
    st.write(f"Componente Trasversale (Sway): **{res_u:.1f} ton**")
    
    st.info("💡 La freccia BLU parte da poppa (dove agiscono i motori). Osserva la distanza tra la freccia blu e il punto PP (nero) per stimare la rotazione.")
