import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import PathPatch, FancyArrowPatch
from matplotlib.path import Path

# --- CONFIGURAZIONE PAGINA ---
st.set_page_config(page_title="ASD Centurion V5.2", layout="wide")

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
def reset_all():
    st.session_state.p1 = 50
    st.session_state.a1 = 0
    st.session_state.p2 = 50
    st.session_state.a2 = 0
    st.session_state.pp_x = 0.0
    st.session_state.pp_y = 5.42

# --- TITOLO E HEADER ---
st.markdown("<h1 style='text-align: center;'>⚓ Rimorchiatore ASD 'CENTURION'</h1>", unsafe_allow_html=True)
st.markdown("""
<div style='text-align: center;'>
    <b>Dimensioni:</b> 32.50 m x 11.70 m | <b>Bollard Pull:</b> 70 ton | <b>Logica:</b> Intersezione Vettoriale<br>
    <span style='color: #666; font-size: 0.9em;'>Per informazioni contattare: <b>stefano.bandi22@gmail.com</b></span>
</div>
""", unsafe_allow_html=True)

st.write("---")

# --- SIDEBAR (Solo Reset) ---
with st.sidebar:
    st.header("Comandi Globali")
    st.button("🔄 RESET TOTALE", on_click=reset_all, type="primary", use_container_width=True)
    st.info("Premi Reset per riportare motori e Pivot Point alla condizione di default.")

# --- CALCOLI FISICI (Eseguiti prima della grafica) ---
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

# ================= COLONNA SINISTRA (PORT) =================
with col_sx:
    st.markdown("<h3 style='text-align: center; color: #ff4b4b;'>PORT (SX)</h3>", unsafe_allow_html=True)
    
    st.slider("Potenza SX (%)", 0, 100, key="p1")
    st.metric("Spinta SX", f"{ton1:.1f} t")
    
    st.slider("Azimut SX (°)", 0, 360, key="a1")
    
    # Orologio SX
    fig_g1, ax_g1 = plt.subplots(figsize=(3, 3), subplot_kw={'projection': 'polar'})
    ax_g1.set_theta_zero_location('N')
    ax_g1.set_theta_direction(-1)
    ax_g1.set_yticks([])
    ax_g1.set_xticks(np.radians([0, 90, 180, 270]))
    ax_g1.set_xticklabels(['0', '90', '180', '270'])
    ax_g1.arrow(np.radians(st.session_state.a1), 0, 0, 0.9, color='red', width=0.15, head_width=0, length_includes_head=True)
    ax_g1.grid(True, alpha=0.3)
    # Background trasparente per estetica
    fig_g1.patch.set_alpha(0)
    st.pyplot(fig_g1, use_container_width=False)


# ================= COLONNA DESTRA (STARBOARD) =================
with col_dx:
    st.markdown("<h3 style='text-align: center; color: #4CAF50;'>STBD (DX)</h3>", unsafe_allow_html=True)
    
    st.slider("Potenza DX (%)", 0, 100, key="p2")
    st.metric("Spinta DX", f"{ton2:.1f} t")
    
    st.slider("Azimut DX (°)", 0, 360, key="a2")
    
    # Orologio DX
    fig_g2, ax_g2 = plt.subplots(figsize=(3, 3), subplot_kw={'projection': 'polar'})
    ax_g2.set_theta_zero_location('N')
    ax_g2.set_theta_direction(-1)
    ax_g2.set_yticks([])
    ax_g2.set_xticks(np.radians([0, 90, 180, 270]))
    ax_g2.set_xticklabels(['0', '90', '180', '270'])
    ax_g2.arrow(np.radians(st.session_state.a2), 0, 0, 0.9, color='green', width=0.15, head_width=0, length_includes_head=True)
    ax_g2.grid(True, alpha=0.3)
    fig_g2.patch.set_alpha(0)
    st.pyplot(fig_g2, use_container_width=False)


# ================= COLONNA CENTRALE (GRAFICA & PP) =================
with col_center:
    # 1. Controlli Pivot Point (messi sopra il grafico per immediatezza)
    with st.expander("📍 Configurazione Pivot Point", expanded=True):
        c1, c2 = st.columns(2)
        with c1:
            st.slider("Longitudinale (Y)", -16.0, 16.0, key="pp_y", help="Positivo = Verso Prua")
        with c2:
            st.slider("Trasversale (X)", -5.0, 5.0, key="pp_x")

    # 2. Grafico Principale
    fig, ax = plt.subplots(figsize=(8, 10))
    
    # --- DISEGNO SCAFO ---
    hw = 5.85       # Half Width
    stern = -16.25  # Y Poppa
    bow_tip = 16.25 # Y Punta Prua
    shoulder = 5.0  # Dove inizia la curva di prua
    
    verts = [
        (-hw, stern), (hw, stern), (hw, shoulder), 
        (0, bow_tip), (-hw, shoulder), (-hw, stern)
    ]
    codes = [Path.MOVETO, Path.LINETO, Path.LINETO, Path.CURVE3, Path.CURVE3, Path.LINETO]
    path = Path(verts, codes)
    patch = PathPatch(path, facecolor='#cccccc', edgecolor='#404040', lw=3, zorder=1)
    ax.add_patch(patch)
    
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

    # Motori
    scale = 0.4
    ax.arrow(pos_sx[0], pos_sx[1], u1*scale, v1*scale, head_width=1.2, fc='red', ec='red', width=0.25, alpha=0.8, zorder=4)
    ax.arrow(pos_dx[0], pos_dx[1], u2*scale, v2*scale, head_width=1.2, fc='green', ec='green', width=0.25, alpha=0.8, zorder=4)

    # Risultante
    ax.scatter(origin_res[0], origin_res[1], c='blue', s=40, marker='x', zorder=4)
    ax.arrow(origin_res[0], origin_res[1], res_u*scale, res_v*scale, 
             head_width=2.0, head_length=2.0, fc='blue', ec='blue', width=0.6, alpha=0.4, zorder=4)

    # Linee tratteggiate intersezione
    if logic_used == "C (Intersezione)" and abs(origin_res[1]) < 40:
        ax.plot([pos_sx[0], origin_res[0]], [pos_sx[1], origin_res[1]], 'r--', lw=1, alpha=0.3)
        ax.plot([pos_dx[0], origin_res[0]], [pos_dx[1], origin_res[1]], 'g--', lw=1, alpha=0.3)

    # SETUP ASSI
    ax.set_xlim(-20, 20)
    ax.set_ylim(-25, 25)
    ax.set_aspect('equal')
    ax.axis('off') 
    
    st.pyplot(fig)
    
    # 3. Analisi Dinamica (Sotto il grafico, centrata)
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
