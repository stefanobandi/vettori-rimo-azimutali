import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import PathPatch, FancyArrowPatch, Rectangle, Circle
from matplotlib.path import Path

# --- CONFIGURAZIONE PAGINA ---
st.set_page_config(page_title="ASD Centurion V5.8", layout="wide")

# --- GESTIONE SESSION STATE (Memoria) ---
defaults = {
    "p1": 50, "a1": 0,    # Motore SX
    "p2": 50, "a2": 0,    # Motore DX
    "pp_x": 0.0, "pp_y": 5.42 # Pivot Point default
}

for key, val in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = val

# --- FUNZIONI DI RESET SEPARATE ---
def reset_engines():
    st.session_state.p1 = 50
    st.session_state.a1 = 0
    st.session_state.p2 = 50
    st.session_state.a2 = 0

def reset_pivot():
    st.session_state.pp_x = 0.0
    st.session_state.pp_y = 5.42

# --- TITOLO E HEADER ---
st.markdown("<h1 style='text-align: center;'>⚓ Rimorchiatore ASD 'CENTURION'</h1>", unsafe_allow_html=True)
st.markdown("""
<div style='text-align: center;'>
    <b>Dimensioni:</b> 32.50 m x 11.70 m | <b>Bollard Pull:</b> 70 ton | <b>Logica:</b> Intersezione Vettoriale<br>
    <span style='color: #666; font-size: 0.9em;'>Simulatore V5.8 - Grafica migliorata</span>
</div>
""", unsafe_allow_html=True)

st.write("---")

# --- SIDEBAR (Reset Separati) ---
with st.sidebar:
    st.header("Comandi Globali")
    
    st.markdown("### 🔄 Reset")
    st.button("Reset Motori", on_click=reset_engines, type="primary", use_container_width=True)
    st.button("Reset Pivot Point", on_click=reset_pivot, use_container_width=True)
    
    st.info("Usa i tasti sopra per riportare i valori ai parametri di default.")

# --- CALCOLI FISICI ---
pos_sx = np.array([-2.7, -12.0])
pos_dx = np.array([2.7, -12.0])
pp_pos = np.array([st.session_state.pp_x, st.session_state.pp_y])

# Calcolo Tonnellate
ton1 = (st.session_state.p1 / 100) * 35
ton2 = (st.session_state.p2 / 100) * 35

# Vettori Componenti
rad1, rad2 = np.radians(st.session_state.a1), np.radians(st.session_state.a2)
u1, v1 = ton1 * np.sin(rad1), ton1 * np.cos(rad1)
u2, v2 = ton2 * np.sin(rad2), ton2 * np.cos(rad2)

# Vettori Forza
F_sx = np.array([u1, v1])
F_dx = np.array([u2, v2])

# Risultante Totale
res_u = u1 + u2
res_v = v1 + v2
res_ton = np.sqrt(res_u**2 + res_v**2)

# Calcolo Momento
r_sx = pos_sx - pp_pos
r_dx = pos_dx - pp_pos
M_sx = r_sx[0] * F_sx[1] - r_sx[1] * F_sx[0]
M_dx = r_dx[0] * F_dx[1] - r_dx[1] * F_dx[0]
Total_Moment = M_sx + M_dx

# Logica Punto Applicazione
def intersect_lines(p1, angle1_deg, p2, angle2_deg):
    th1 = np.radians(90 - angle1_deg)
    th2 = np.radians(90 - angle2_deg)
    v1 = np.array([np.cos(th1), np.sin(th1)])
    v2 = np.array([np.cos(th2), np.sin(th2)])
    matrix = np.column_stack((v1, -v2))
    delta = p2 - p1
    if abs(np.linalg.det(matrix)) < 1e-4:
        return None
    t = np.linalg.solve(matrix, delta)[0]
    return p1 + t * v1

intersection = None
if ton1 > 0.1 and ton2 > 0.1:
    intersection = intersect_lines(pos_sx, st.session_state.a1, pos_dx, st.session_state.a2)

origin_res = np.array([0.0, -12.0])
logic_used = "B (Default)"

if intersection is not None and np.linalg.norm(intersection - np.array([0, -12])) < 80:
    origin_res = intersection
    logic_used = "C (Intersezione)"
elif ton1 + ton2 > 0.1:
    w_x = (ton1 * pos_sx[0] + ton2 * pos_dx[0]) / (ton1 + ton2)
    origin_res = np.array([w_x, -12.0])
    logic_used = "B (Media)"


# --- LAYOUT A COLONNE (PLANCIA) ---
col_sx, col_center, col_dx = st.columns([1, 2, 1], gap="medium")

# Helper Grafico Orologio (Semplice)
def plot_clock(azimuth_deg, color):
    fig, ax = plt.subplots(figsize=(3, 3), subplot_kw={'projection': 'polar'})
    ax.set_theta_zero_location('N')
    ax.set_theta_direction(-1)
    ax.set_yticks([])
    ax.set_xticks(np.radians([0, 90, 180, 270]))
    ax.set_xticklabels(['0', '90', '180', '270'])
    ax.arrow(np.radians(azimuth_deg), 0, 0, 0.9, color=color, width=0.15, head_width=0, length_includes_head=True)
    ax.grid(True, alpha=0.3)
    fig.patch.set_alpha(0)
    return fig

# ================= COLONNA SINISTRA (PORT) =================
with col_sx:
    st.markdown("<h3 style='text-align: center; color: #ff4b4b;'>PORT (SX)</h3>", unsafe_allow_html=True)
    
    st.slider("Potenza SX (%)", 0, 100, step=1, key="p1")
    st.metric("Spinta SX", f"{ton1:.1f} t")
    
    st.slider("Azimut SX (°)", 0, 360, step=1, key="a1")
    
    # Orologio SX
    st.pyplot(plot_clock(st.session_state.a1, 'red'), use_container_width=False)


# ================= COLONNA DESTRA (STARBOARD) =================
with col_dx:
    st.markdown("<h3 style='text-align: center; color: #4CAF50;'>STBD (DX)</h3>", unsafe_allow_html=True)
    
    st.slider("Potenza DX (%)", 0, 100, step=1, key="p2")
    st.metric("Spinta DX", f"{ton2:.1f} t")
    
    st.slider("Azimut DX (°)", 0, 360, step=1, key="a2")
    
    # Orologio DX
    st.pyplot(plot_clock(st.session_state.a2, 'green'), use_container_width=False)


# ================= COLONNA CENTRALE (GRAFICA & PP) =================
with col_center:
    # 1. Controlli Pivot Point
    with st.expander("📍 Configurazione Pivot Point", expanded=True):
        c1, c2 = st.columns(2)
        with c1:
            st.slider("Longitudinale (Y)", -16.0, 16.0, step=0.1, key="pp_y", help="Positivo = Verso Prua")
        with c2:
            st.slider("Trasversale (X)", -5.0, 5.0, step=0.1, key="pp_x")

    # 2. Grafico Principale
    fig, ax = plt.subplots(figsize=(8, 10))
    
    # --- DISEGNO SCAFO MIGLIORATO ---
    hw = 5.85       # Half Width
    stern = -16.25  # Y Poppa
    bow_tip = 16.25 # Y Punta Prua
    shoulder = 5.0  # Dove inizia la curva di prua
    
    # 1. Scafo Principale (Deck)
    verts = [
        (-hw, stern), (hw, stern), (hw, shoulder), 
        (0, bow_tip), (-hw, shoulder), (-hw, stern)
    ]
    codes = [Path.MOVETO, Path.LINETO, Path.LINETO, Path.CURVE3, Path.CURVE3, Path.LINETO]
    path = Path(verts, codes)
    # Colore più "navale" (acciaio/blu) e bordo spesso nero per il paracolpi
    hull_patch = PathPatch(path, facecolor='#778899', edgecolor='black', lw=5, zorder=1)
    ax.add_patch(hull_patch)

    # 2. Tuga/Plancia (Superstructure)
    # Un rettangolo semplice per dare volume
    house_width = 7.0
    house_length = 6.0
    house_y_center = -1.0
    # La plancia è bianca/grigio chiaro con bordo più sottile
    wheelhouse = Rectangle((-house_width/2, house_y_center - house_length/2), 
                           house_width, house_length,
                           facecolor='#F0F0F0', edgecolor='#333333', lw=2, zorder=2)
    ax.add_patch(wheelhouse)
    # Aggiungiamo una linea per suggerire le vetrate frontali della plancia
    ax.plot([-2.5, 2.5], [house_y_center + house_length/2 - 1, house_y_center + house_length/2 - 1], 
            color='#333333', lw=2, zorder=3)

    # 3. Verricelli (Winches) - Dettagli tecnici
    # Verricello di prua
    winch_fwd = Circle((0, 10), radius=0.8, facecolor='#555555', edgecolor='black', lw=1, zorder=2)
    ax.add_patch(winch_fwd)
    # Verricello di poppa (spesso doppio su ASD, ne mettiamo uno centrale per semplicità)
    winch_aft = Circle((0, -10), radius=1.0, facecolor='#555555', edgecolor='black', lw=1, zorder=2)
    ax.add_patch(winch_aft)
    
    # --- FINE DISEGNO SCAFO ---

    # Pivot Point
    ax.scatter(st.session_state.pp_x, st.session_state.pp_y, c='black', s=120, zorder=10)
    ax.text(st.session_state.pp_x + 0.6, st.session_state.pp_y, "PP", fontsize=11, weight='bold', zorder=10)

    # Momento (Freccia Viola)
    if abs(Total_Moment) > 10:
        arc_color = '#800080'
        radius = 9.0 
        style = f"Simple, tail_width={min(3, abs(Total_Moment)/200)}, head_width=8, head_length=8"
        
        # Logica per disegnare l'arco a destra o sinistra
        start_x = st.session_state.pp_x + (radius if Total_Moment > 0 else -radius)
        connection = "arc3,rad=.3" if Total_Moment > 0 else "arc3,rad=-.3"
        
        ax.add_patch(FancyArrowPatch((start_x, st.session_state.pp_y - 3), 
                                     (start_x, st.session_state.pp_y + 3),
                                     connectionstyle=connection, 
                                     arrowstyle=style, color=arc_color, alpha=0.8, zorder=5))

    # Motori (Propulsori sotto lo scafo, zorder basso)
    scale = 0.4
    ax.arrow(pos_sx[0], pos_sx[1], u1*scale, v1*scale, head_width=1.2, fc='red', ec='#8B0000', width=0.25, alpha=0.9, zorder=4)
    ax.arrow(pos_dx[0], pos_dx[1], u2*scale, v2*scale, head_width=1.2, fc='green', ec='#006400', width=0.25, alpha=0.9, zorder=4)

    # Risultante
    ax.scatter(origin_res[0], origin_res[1], c='blue', s=40, marker='x', zorder=6)
    ax.arrow(origin_res[0], origin_res[1], res_u*scale, res_v*scale, 
             head_width=2.0, head_length=2.0, fc='blue', ec='#00008B', width=0.6, alpha=0.5, zorder=6)

    # Linee tratteggiate intersezione
    if logic_used == "C (Intersezione)" and abs(origin_res[1]) < 40:
        ax.plot([pos_sx[0], origin_res[0]], [pos_sx[1], origin_res[1]], 'r--', lw=1, alpha=0.3, zorder=3)
        ax.plot([pos_dx[0], origin_res[0]], [pos_dx[1], origin_res[1]], 'g--', lw=1, alpha=0.3, zorder=3)

    # SETUP ASSI
    ax.set_xlim(-20, 20)
    ax.set_ylim(-25, 25)
    ax.set_aspect('equal')
    ax.axis('off') 
    
    st.pyplot(fig)
    
    # 3. Analisi Dinamica
    st.markdown("### 📊 Analisi Dinamica")
    m1, m2, m3 = st.columns(3)
    
    deg_res = np.degrees(np.arctan2(res_u, res_v))
    if deg_res < 0: deg_res += 360
    
    m1.metric("Tiro Totale", f"{res_ton:.1f} t")
    m2.metric("Direzione", f"{deg_res:.0f}°")
    
    dir_rot = "STABILE"
    if abs(Total_Moment) > 20:
        dir_rot = "SINISTRA (Antiorario)" if Total_Moment > 0 else "DRITTA (Orario)"
    
    m3.metric("Rotazione", dir_rot, delta=f"{abs(Total_Moment):.0f} kNm", delta_color="off")
