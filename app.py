import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import PathPatch, FancyArrowPatch
from matplotlib.path import Path

# --- GESTIONE SESSION STATE (Memoria) ---
defaults = {
    "p1": 50, "a1": 0,    # Motore SX
    "p2": 50, "a2": 0,    # Motore DX
    "pp_x": 0.0, "pp_y": 5.42 # Pivot Point default
}

for key, val in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = val

# Funzioni di Callback
def reset_engines():
    st.session_state.p1 = 50
    st.session_state.a1 = 0
    st.session_state.p2 = 50
    st.session_state.a2 = 0

def reset_pp():
    st.session_state.pp_x = 0.0
    st.session_state.pp_y = 5.42

# --- Configurazione Pagina ---
st.set_page_config(page_title="ASD Centurion V4", layout="wide")

# --- Titolo e Dati Nave ---
st.title("⚓ Rimorchiatore ASD 'CENTURION'")
st.markdown("""
**Dimensioni:** 32.50 m x 11.70 m | **Bollard Pull:** 70 ton | **Logica:** Intersezione Vettoriale
""")

# --- Sidebar: Configurazione Pivot Point ---
with st.sidebar:
    st.header("📍 Pivot Point")
    st.button("Reset PP", on_click=reset_pp)
    pp_y = st.slider("Longitudinale (Y)", -16.0, 16.0, key="pp_y", help="Positivo = Prua")
    pp_x = st.slider("Trasversale (X)", -5.0, 5.0, key="pp_x")

# --- Funzioni Matematiche ---
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

# --- Layout Comandi Motori ---
col_res, col1, col2 = st.columns([0.2, 1, 1])

with col_res:
    st.write("") 
    st.write("")
    st.button("🔄 RESET", on_click=reset_engines, type="primary")

with col1:
    st.markdown("### 🔴 Port (SX)")
    st.slider("Potenza (%)", 0, 100, key="p1")
    # Calcolo immediato tonnellate
    ton1 = (st.session_state.p1 / 100) * 35
    st.markdown(f"**Spinta: {ton1:.1f} ton**") # Visualizzazione richiesta n.2
    
    st.slider("Azimut (°)", 0, 360, key="a1")
    
    # Orologio SX
    fig_g1, ax_g1 = plt.subplots(figsize=(2, 2), subplot_kw={'projection': 'polar'})
    ax_g1.set_theta_zero_location('N')
    ax_g1.set_theta_direction(-1)
    ax_g1.set_yticks([])
    ax_g1.set_xticks(np.radians([0, 90, 180, 270]))
    ax_g1.set_xticklabels(['0', '90', '180', '270'], fontsize=8)
    ax_g1.arrow(np.radians(st.session_state.a1), 0, 0, 0.9, color='red', width=0.15, head_width=0, length_includes_head=True)
    ax_g1.grid(True, alpha=0.3)
    st.pyplot(fig_g1, use_container_width=False)

with col2:
    st.markdown("### 🟢 Starboard (DX)")
    st.slider("Potenza (%)", 0, 100, key="p2")
    ton2 = (st.session_state.p2 / 100) * 35
    st.markdown(f"**Spinta: {ton2:.1f} ton**") # Visualizzazione richiesta n.2
    
    st.slider("Azimut (°)", 0, 360, key="a2")
    
    # Orologio DX
    fig_g2, ax_g2 = plt.subplots(figsize=(2, 2), subplot_kw={'projection': 'polar'})
    ax_g2.set_theta_zero_location('N')
    ax_g2.set_theta_direction(-1)
    ax_g2.set_yticks([])
    ax_g2.set_xticks(np.radians([0, 90, 180, 270]))
    ax_g2.set_xticklabels(['0', '90', '180', '270'], fontsize=8)
    ax_g2.arrow(np.radians(st.session_state.a2), 0, 0, 0.9, color='green', width=0.15, head_width=0, length_includes_head=True)
    ax_g2.grid(True, alpha=0.3)
    st.pyplot(fig_g2, use_container_width=False)

# --- CALCOLI FISICI ---
pos_sx = np.array([-2.7, -12.0])
pos_dx = np.array([2.7, -12.0])
pp_pos = np.array([st.session_state.pp_x, st.session_state.pp_y])

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

# Calcolo Momento (Rotazione) rispetto al Pivot Point
# Braccio = Posizione Motore - Posizione PP
r_sx = pos_sx - pp_pos
r_dx = pos_dx - pp_pos

# Momento in 2D (prodotto vettoriale componente Z): r_x * F_y - r_y * F_x
# Segno: + (Antiorario/SX), - (Orario/DX)
M_sx = r_sx[0] * F_sx[1] - r_sx[1] * F_sx[0]
M_dx = r_dx[0] * F_dx[1] - r_dx[1] * F_dx[0]
Total_Moment = M_sx + M_dx

# Logica Punto Applicazione (Intersezione vs Baricentro)
intersection = None
if ton1 > 0.1 and ton2 > 0.1:
    intersection = intersect_lines(pos_sx, st.session_state.a1, pos_dx, st.session_state.a2)

origin_res = np.array([0.0, -12.0]) # Default
logic_used = "B (Default)"

if intersection is not None and np.linalg.norm(intersection - np.array([0, -12])) < 80:
    origin_res = intersection
    logic_used = "C (Intersezione)"
elif ton1 + ton2 > 0.1:
    # Media pesata
    w_x = (ton1 * pos_sx[0] + ton2 * pos_dx[0]) / (ton1 + ton2)
    origin_res = np.array([w_x, -12.0])
    logic_used = "B (Media)"

# --- Visualizzazione Grafico ---
st.divider()
col_graph, col_data = st.columns([2, 1])

with col_graph:
    fig, ax = plt.subplots(figsize=(8, 10))
    
    # 1. DISEGNO SCAFO MIGLIORATO (Bezier Curves)
    # Dimensioni: 32.5 x 11.7 -> Half W = 5.85. Poppa = -16.25, Prua = 16.25
    hw = 5.85
    stern = -16.25
    bow = 16.25
    mid_bow = 10.0 # Inizio curvatura prua
    
    verts = [
        (-hw, stern),      # Poppa SX
        (0, stern - 0.5),  # Centro Poppa (leggera curva)
        (hw, stern),       # Poppa DX
        (hw, mid_bow),     # Lato DX dritto fino inizio prua
        (hw, 14),          # Control point curva 1
        (3, bow),          # Control point curva 2
        (0, bow),          # Punta Prua
        (-3, bow),         # Control point curva 3
        (-hw, 14),         # Control point curva 4
        (-hw, mid_bow),    # Lato SX inizio prua
        (-hw, stern)       # Chiudi
    ]
    
    codes = [
        Path.MOVETO,
        Path.CURVE3, # Curva poppa
        Path.CURVE3,
        Path.LINETO, # Lato DX
        Path.CURVE4, # Curva Prua DX complessa
        Path.CURVE4,
        Path.CURVE4, # Punta -> SX
        Path.CURVE4,
        Path.CURVE4,
        Path.LINETO, # Lato SX
        Path.LINETO  # Chiudi
    ]
    
    patch = PathPatch(Path(verts, codes), facecolor='#d9d9d9', edgecolor='#555555', lw=2.5, zorder=1)
    ax.add_patch(patch)
    # Aggiungiamo un ponte (decorativo)
    ax.add_patch(plt.Circle((0, 2), 4, color='white', zorder=2, alpha=0.5))

    # 2. Pivot Point
    ax.scatter(st.session_state.pp_x, st.session_state.pp_y, c='black', s=100, zorder=10)
    ax.text(st.session_state.pp_x + 0.5, st.session_state.pp_y, "PP", fontsize=10, weight='bold', zorder=10)

    # 3. Visualizzazione MOMENTO (Freccia Curva)
    # Solo se c'è un momento significativo (> 10 kNm indicativi)
    if abs(Total_Moment) > 10:
        arc_color = 'purple'
        arc_style = "Simple, tail_width=2, head_width=8, head_length=8"
        # Raggio della freccia curva basato sulla grandezza nave
        radius = 8 
        
        # Definiamo arco: start angle e end angle
        if Total_Moment > 0: # Accosta Sinistra (Antiorario)
            style = f"Simple, tail_width={min(3, abs(Total_Moment)/200)}, head_width=8, head_length=8"
            arrow = FancyArrowPatch((st.session_state.pp_x, st.session_state.pp_y), 
                                    (st.session_state.pp_x, st.session_state.pp_y),
                                    connectionstyle=f"arc3,rad=.5", 
                                    color=arc_color, alpha=0.6, zorder=5,
                                    mutation_scale=20)
            # Matplotlib arc è complicato, usiamo un trucco visuale:
            # Disegniamo un arco di 90 gradi indicativo
            ax.add_patch(FancyArrowPatch((st.session_state.pp_x + radius, st.session_state.pp_y), 
                                         (st.session_state.pp_x, st.session_state.pp_y + radius),
                                         connectionstyle="arc3,rad=.3", 
                                         arrowstyle=style, color='purple', zorder=6))
            ax.text(10, 0, "↺", fontsize=20, color='purple', va='center')
        else: # Accosta Dritta (Orario)
            style = f"Simple, tail_width={min(3, abs(Total_Moment)/200)}, head_width=8, head_length=8"
            ax.add_patch(FancyArrowPatch((st.session_state.pp_x - radius, st.session_state.pp_y), 
                                         (st.session_state.pp_x, st.session_state.pp_y + radius),
                                         connectionstyle="arc3,rad=-.3", 
                                         arrowstyle=style, color='purple', zorder=6))
            ax.text(-15, 0, "↻", fontsize=20, color='purple', va='center')

    # 4. Motori e Vettori
    ax.scatter([pos_sx[0], pos_dx[0]], [pos_sx[1], pos_dx[1]], c='gray', s=60, zorder=3)
    scale = 0.4
    
    ax.arrow(pos_sx[0], pos_sx[1], u1*scale, v1*scale, head_width=1.2, fc='red', ec='red', width=0.25, alpha=0.8, zorder=4)
    ax.arrow(pos_dx[0], pos_dx[1], u2*scale, v2*scale, head_width=1.2, fc='green', ec='green', width=0.25, alpha=0.8, zorder=4)

    # Risultante
    ax.scatter(origin_res[0], origin_res[1], c='blue', s=30, marker='x', zorder=4)
    ax.arrow(origin_res[0], origin_res[1], res_u*scale, res_v*scale, 
             head_width=2.0, head_length=2.0, fc='blue', ec='blue', width=0.6, alpha=0.4, zorder=4)

    if logic_used == "C (Intersezione)" and abs(origin_res[1]) < 40:
        ax.plot([pos_sx[0], origin_res[0]], [pos_sx[1], origin_res[1]], 'r--', lw=0.8, alpha=0.3)
        ax.plot([pos_dx[0], origin_res[0]], [pos_dx[1], origin_res[1]], 'g--', lw=0.8, alpha=0.3)

    ax.set_xlim(-25, 25)
    ax.set_ylim(-25, 25)
    ax.set_aspect('equal')
    ax.grid(True, linestyle='--', alpha=0.2)
    ax.set_axis_off() # Nascondiamo gli assi cartesiani per pulizia
    
    st.pyplot(fig)

with col_data:
    st.markdown("### 📊 Analisi Dinamica")
    st.metric("Tiro Risultante", f"{res_ton:.1f} ton")
    
    deg_res = np.degrees(np.arctan2(res_u, res_v))
    if deg_res < 0: deg_res += 360
    st.metric("Direzione Spinta", f"{deg_res:.0f}°")
    
    st.write("---")
    st.markdown("**Effetto Rotativo (Momento):**")
    
    if abs(Total_Moment) < 50:
        rot_text = "Neutro / Stabile"
        rot_icon = "➖"
    elif Total_Moment > 0:
        rot_text = "Accosta a SINISTRA"
        rot_icon = "↺"
    else:
        rot_text = "Accosta a DRITTA"
        rot_icon = "↻"
    
    st.subheader(f"{rot_icon} {rot_text}")
    st.caption(f"Intensità Momento: {abs(Total_Moment):.0f} kNm (indicativo)")
    
    st.write("---")
    st.caption("Legenda: 🟣 Rotazione | 🔵 Risultante | ⚫ Pivot Point")
