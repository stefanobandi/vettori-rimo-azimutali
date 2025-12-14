import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import PathPatch
from matplotlib.path import Path

# --- GESTIONE SESSION STATE (Memoria) ---
# Inizializziamo le variabili se non esistono
defaults = {
    "p1": 50, "a1": 0,    # Motore SX
    "p2": 50, "a2": 0,    # Motore DX
    "pp_x": 0.0, "pp_y": 5.42 # Pivot Point
}

for key, val in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = val

# Funzioni di Callback per i Reset
def reset_engines():
    st.session_state.p1 = 50
    st.session_state.a1 = 0
    st.session_state.p2 = 50
    st.session_state.a2 = 0

def reset_pp():
    st.session_state.pp_x = 0.0
    st.session_state.pp_y = 5.42

# --- Configurazione Pagina ---
st.set_page_config(page_title="ASD Centurion V3", layout="wide")

# --- Titolo ---
st.title("⚓ Rimorchiatore ASD 'CENTURION'")
st.markdown("**Bollard Pull Max:** 70 tonnellate | **Logica Vettoriale:** Intersezione Linee di Spinta")

# --- Sidebar: Configurazione Pivot Point ---
with st.sidebar:
    st.header("📍 Pivot Point")
    st.button("Reset PP", on_click=reset_pp)
    # Gli slider leggono/scrivono direttamente in session_state tramite la key
    pp_y = st.slider("Longitudinale (Y)", -16.0, 16.0, key="pp_y", help="Positivo = Prua")
    pp_x = st.slider("Trasversale (X)", -5.0, 5.0, key="pp_x")

# --- Funzioni di Calcolo Matematico ---
def intersect_lines(p1, angle1_deg, p2, angle2_deg):
    """
    Trova l'intersezione tra due vettori partendo da p1 e p2 con angoli dati.
    Ritorna (x, y) intersezione, oppure None se paralleli.
    """
    # Converti in radianti matematici (0 a destra, antiorario)
    # Nautico: 0=Nord(Y+), 90=Est(X+) -> Math: 0=X+, 90=Y+
    # Conversione: Math = 90 - Nautico
    th1 = np.radians(90 - angle1_deg)
    th2 = np.radians(90 - angle2_deg)
    
    # Vettori direttori
    v1 = np.array([np.cos(th1), np.sin(th1)])
    v2 = np.array([np.cos(th2), np.sin(th2)])
    
    # Risoluzione sistema lineare
    # P1 + t*v1 = P2 + u*v2  --> t*v1 - u*v2 = P2 - P1
    # Matrice A = [v1, -v2]
    matrix = np.column_stack((v1, -v2))
    delta = p2 - p1
    
    # Determinante (se vicino a 0, sono paralleli)
    det = np.linalg.det(matrix)
    if abs(det) < 1e-4:
        return None # Paralleli
        
    # Risolvi per t e u
    params = np.linalg.solve(matrix, delta)
    t = params[0]
    
    # Punto intersezione = P1 + t*v1
    intersection = p1 + t * v1
    return intersection

# --- Layout Comandi Motori ---
col_res, col1, col2 = st.columns([0.2, 1, 1])

with col_res:
    st.write("") # Spaziatore
    st.write("")
    st.button("🔄 RESET MOTORI", on_click=reset_engines, type="primary")

with col1:
    st.markdown("### 🔴 Port (SX)")
    st.slider("Potenza (%)", 0, 100, key="p1")
    st.slider("Azimut (°)", 0, 360, key="a1")
    
    ton1 = (st.session_state.p1 / 100) * 35
    
    # Orologio SX
    fig_g1, ax_g1 = plt.subplots(figsize=(2, 2), subplot_kw={'projection': 'polar'})
    ax_g1.set_theta_zero_location('N')
    ax_g1.set_theta_direction(-1)
    ax_g1.set_yticks([])
    ax_g1.set_xticks(np.radians([0, 90, 180, 270]))
    ax_g1.set_xticklabels(['0', '90', '180', '270'], fontsize=9)
    ax_g1.arrow(np.radians(st.session_state.a1), 0, 0, 0.9, color='red', width=0.15, head_width=0, length_includes_head=True)
    ax_g1.grid(True, alpha=0.3)
    st.pyplot(fig_g1, use_container_width=False)
    st.caption(f"**{ton1:.1f} ton** @ {st.session_state.a1}°")

with col2:
    st.markdown("### 🟢 Starboard (DX)")
    st.slider("Potenza (%)", 0, 100, key="p2")
    st.slider("Azimut (°)", 0, 360, key="a2")
    
    ton2 = (st.session_state.p2 / 100) * 35
    
    # Orologio DX
    fig_g2, ax_g2 = plt.subplots(figsize=(2, 2), subplot_kw={'projection': 'polar'})
    ax_g2.set_theta_zero_location('N')
    ax_g2.set_theta_direction(-1)
    ax_g2.set_yticks([])
    ax_g2.set_xticks(np.radians([0, 90, 180, 270]))
    ax_g2.set_xticklabels(['0', '90', '180', '270'], fontsize=9)
    ax_g2.arrow(np.radians(st.session_state.a2), 0, 0, 0.9, color='green', width=0.15, head_width=0, length_includes_head=True)
    ax_g2.grid(True, alpha=0.3)
    st.pyplot(fig_g2, use_container_width=False)
    st.caption(f"**{ton2:.1f} ton** @ {st.session_state.a2}°")

# --- CALCOLI FISICI ---
pos_sx = np.array([-2.7, -12.0])
pos_dx = np.array([2.7, -12.0])

# Vettori Componenti
rad1 = np.radians(st.session_state.a1)
rad2 = np.radians(st.session_state.a2)

u1, v1 = ton1 * np.sin(rad1), ton1 * np.cos(rad1)
u2, v2 = ton2 * np.sin(rad2), ton2 * np.cos(rad2)

res_u = u1 + u2
res_v = v1 + v2
res_ton = np.sqrt(res_u**2 + res_v**2)

# --- DETERMINAZIONE PUNTO DI APPLICAZIONE RISULTANTE ---
# Logica Ibrida: C (Intersezione) con fallback su B (Media Pesata)
origin_res = np.array([0.0, -12.0]) # Default fallback
logic_used = "B (Paralleli/Default)"

# Se c'è spinta da entrambi
if ton1 > 0.1 and ton2 > 0.1:
    intersection = intersect_lines(pos_sx, st.session_state.a1, pos_dx, st.session_state.a2)
    
    if intersection is not None:
        # Controllo distanza (se > 100m è inutile visualizzarlo lì, usiamo B)
        dist_from_stern = np.linalg.norm(intersection - np.array([0, -12]))
        
        if dist_from_stern < 80: # Se interseca entro 80 metri dallo scafo
            origin_res = intersection
            logic_used = "C (Intersezione)"
        else:
            # Fallback B: Media pesata sulla traversa di poppa
            # X = (F1*X1 + F2*X2) / F_tot
            tot_force = ton1 + ton2
            w_x = (ton1 * pos_sx[0] + ton2 * pos_dx[0]) / tot_force
            origin_res = np.array([w_x, -12.0])
            logic_used = "B (Divergenti/Lontani)"
    else:
        # Paralleli -> Fallback B
        tot_force = ton1 + ton2
        w_x = (ton1 * pos_sx[0] + ton2 * pos_dx[0]) / tot_force
        origin_res = np.array([w_x, -12.0])
        logic_used = "B (Paralleli)"
elif ton1 > 0.1:
    origin_res = pos_sx # Solo SX spinge
    logic_used = "Singolo SX"
elif ton2 > 0.1:
    origin_res = pos_dx # Solo DX spinge
    logic_used = "Singolo DX"

# --- Visualizzazione Grafico ---
st.divider()
col_graph, col_data = st.columns([2, 1])

with col_graph:
    fig, ax = plt.subplots(figsize=(8, 10))
    
    # Disegno Scafo
    verts = [(-5.85, -16.25), (5.85, -16.25), (5.85, 10), (0, 16.25), (-5.85, 10), (-5.85, -16.25)]
    codes = [Path.MOVETO, Path.LINETO, Path.LINETO, Path.CURVE3, Path.CURVE3, Path.LINETO]
    patch = PathPatch(Path(verts, codes), facecolor='#e0e0e0', edgecolor='black', lw=2, zorder=1)
    ax.add_patch(patch)

    # Pivot Point
    ax.scatter(st.session_state.pp_x, st.session_state.pp_y, c='black', s=120, zorder=5, marker='o', label="Pivot Point")
    ax.text(st.session_state.pp_x + 0.6, st.session_state.pp_y, "PP", fontsize=10, weight='bold', zorder=5)

    # Motori
    ax.scatter([pos_sx[0], pos_dx[0]], [pos_sx[1], pos_dx[1]], c='gray', s=60, zorder=2)

    # Vettori
    scale = 0.4
    
    # SX e DX (trasparenti se la risultante ci passa sopra)
    ax.arrow(pos_sx[0], pos_sx[1], u1*scale, v1*scale, head_width=1.2, fc='red', ec='red', width=0.25, alpha=0.7, zorder=3)
    ax.arrow(pos_dx[0], pos_dx[1], u2*scale, v2*scale, head_width=1.2, fc='green', ec='green', width=0.25, alpha=0.7, zorder=3)

    # Risultante (Logica Ibrida)
    # Disegniamo il punto di applicazione
    ax.scatter(origin_res[0], origin_res[1], c='blue', s=30, marker='x', zorder=4)
    
    ax.arrow(origin_res[0], origin_res[1], res_u*scale, res_v*scale, 
             head_width=2.0, head_length=2.0, fc='blue', ec='blue', width=0.6, alpha=0.5, zorder=4, label='Risultante')

    # Linee tratteggiate proiezione (solo se Ipotesi C è attiva e siamo nel grafico)
    if logic_used == "C (Intersezione)" and abs(origin_res[1]) < 40:
        ax.plot([pos_sx[0], origin_res[0]], [pos_sx[1], origin_res[1]], 'r--', lw=0.8, alpha=0.4)
        ax.plot([pos_dx[0], origin_res[0]], [pos_dx[1], origin_res[1]], 'g--', lw=0.8, alpha=0.4)

    # Setup Assi
    ax.set_xlim(-30, 30)
    ax.set_ylim(-30, 30)
    ax.set_aspect('equal')
    ax.grid(True, linestyle='--', alpha=0.3)
    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_title("Vista dall'alto (Prua in Alto)", fontsize=10)
    
    st.pyplot(fig)

with col_data:
    st.markdown("### 📊 Analisi Dati")
    st.metric("Tiro Risultante", f"{res_ton:.1f} ton")
    
    # Calcolo Angolo Risultante
    deg_res = np.degrees(np.arctan2(res_u, res_v))
    if deg_res < 0: deg_res += 360
    st.metric("Direzione Spinta", f"{deg_res:.0f}°")
    
    st.info(f"📍 **Punto Applicazione:**\nLogica: {logic_used}\nCoord Y: {origin_res[1]:.1f} m")
    
    st.markdown("""
    ---
    **Legenda:**
    - 🔴 Motore SX
    - 🟢 Motore DX
    - 🔵 Vettore Risultante
    - ⚫ Pivot Point (PP)
    - ✖️ Punto di Applicazione Forza
    """)
