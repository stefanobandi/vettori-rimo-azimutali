import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import PathPatch, FancyArrowPatch, Circle
from matplotlib.path import Path

# --- CONFIGURAZIONE PAGINA ---
st.set_page_config(page_title="ASD Centurion V7.0", layout="wide")

# --- GESTIONE SESSION STATE ---
defaults = {
    "p1": 50, "a1": 0,    # Motore SX
    "p2": 50, "a2": 0,    # Motore DX
    "pp_x": 0.0, "pp_y": 5.42 # Pivot Point default
}

for key, val in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = val

# --- FUNZIONI DI RESET ---
def reset_engines():
    st.session_state.p1 = 50
    st.session_state.a1 = 0
    st.session_state.p2 = 50
    st.session_state.a2 = 0

def reset_pivot():
    st.session_state.pp_x = 0.0
    st.session_state.pp_y = 5.42

# --- STYLE GRAFICO (FUNZIONE OROLOGI) ---
def plot_clock_sidebar(azimuth_deg, color, title):
    # Crea un piccolo orologio polare
    fig, ax = plt.subplots(figsize=(2.5, 2.5), subplot_kw={'projection': 'polar'})
    
    # Sfondo trasparente per integrarsi con Streamlit
    fig.patch.set_alpha(0)
    ax.set_facecolor('#f0f2f6') # Grigio chiarissimo interno
    
    # Impostazioni bussola (Nord in alto, senso orario)
    ax.set_theta_zero_location('N')
    ax.set_theta_direction(-1)
    
    # Rimuovi etichette radiali (i cerchi concentrici)
    ax.set_yticklabels([])
    ax.set_xticks(np.radians([0, 45, 90, 135, 180, 225, 270, 315]))
    ax.set_xticklabels(['N', '', 'E', '', 'S', '', 'W', ''], fontsize=8, color='#555')
    
    # Disegna la lancetta (Freccia)
    ax.arrow(np.radians(azimuth_deg), 0, 0, 0.85, 
             color=color, width=0.15, head_width=0, 
             length_includes_head=True, alpha=0.9)
    
    # Titolo piccolo
    plt.title(f"{title}\n{azimuth_deg}°", y=-0.2, fontsize=10, color=color, weight='bold')
    return fig

# --- HEADER ---
st.markdown("""
    <h1 style='text-align: center; color: #004488;'>⚓ ASD 'CENTURION' V7.0</h1>
    <p style='text-align: center; color: #666;'>Simulatore Vettoriale di Manovra</p>
    <hr>
    """, unsafe_allow_html=True)

# --- CALCOLI FISICI (Invariati) ---
pos_sx = np.array([-2.7, -12.0])
pos_dx = np.array([2.7, -12.0])
pp_pos = np.array([st.session_state.pp_x, st.session_state.pp_y])

# Tonnellate
ton1 = (st.session_state.p1 / 100) * 35
ton2 = (st.session_state.p2 / 100) * 35

# Vettori
rad1, rad2 = np.radians(st.session_state.a1), np.radians(st.session_state.a2)
u1, v1 = ton1 * np.sin(rad1), ton1 * np.cos(rad1)
u2, v2 = ton2 * np.sin(rad2), ton2 * np.cos(rad2)

F_sx = np.array([u1, v1])
F_dx = np.array([u2, v2])

# Risultante
res_u = u1 + u2
res_v = v1 + v2
res_ton = np.sqrt(res_u**2 + res_v**2)

# Momento
r_sx = pos_sx - pp_pos
r_dx = pos_dx - pp_pos
M_sx = r_sx[0] * F_sx[1] - r_sx[1] * F_sx[0]
M_dx = r_dx[0] * F_dx[1] - r_dx[1] * F_dx[0]
Total_Moment = M_sx + M_dx

# Intersezione
def intersect_lines(p1, angle1_deg, p2, angle2_deg):
    th1 = np.radians(90 - angle1_deg)
    th2 = np.radians(90 - angle2_deg)
    v1 = np.array([np.cos(th1), np.sin(th1)])
    v2 = np.array([np.cos(th2), np.sin(th2)])
    matrix = np.column_stack((v1, -v2))
    delta = p2 - p1
    if abs(np.linalg.det(matrix)) < 1e-4: return None
    t = np.linalg.solve(matrix, delta)[0]
    return p1 + t * v1

intersection = None
if ton1 > 0.1 and ton2 > 0.1:
    intersection = intersect_lines(pos_sx, st.session_state.a1, pos_dx, st.session_state.a2)

origin_res = np.array([0.0, -12.0])
logic_used = "Baricentro (B)"

if intersection is not None and np.linalg.norm(intersection - np.array([0, -12])) < 80:
    origin_res = intersection
    logic_used = "Intersezione (C)"
elif ton1 + ton2 > 0.1:
    w_x = (ton1 * pos_sx[0] + ton2 * pos_dx[0]) / (ton1 + ton2)
    origin_res = np.array([w_x, -12.0])
    logic_used = "Media Ponderata (B)"

# --- LAYOUT INTERFACCIA ---
# Usiamo 3 colonne come piaceva a te all'inizio, ma più moderne
col_L, col_C, col_R = st.columns([1.2, 3, 1.2])

# === COLONNA SINISTRA (PORT) ===
with col_L:
    st.markdown("<div style='background-color: #ffe6e6; padding: 10px; border-radius: 10px; border: 2px solid #ffcccc;'>", unsafe_allow_html=True)
    st.markdown("<h3 style='text-align: center; color: #cc0000; margin: 0;'>PORT</h3>", unsafe_allow_html=True)
    
    # Orologio SX
    st.pyplot(plot_clock_sidebar(st.session_state.a1, '#cc0000', "Azimut"), use_container_width=True)
    
    st.slider("Azimut", 0, 360, key="a1", label_visibility="collapsed")
    st.markdown("---")
    st.slider("Potenza %", 0, 100, key="p1")
    st.metric("Spinta SX", f"{ton1:.1f} t")
    st.markdown("</div>", unsafe_allow_html=True)
    
    st.write("") # Spazio
    st.button("Reset Motori", on_click=reset_engines, use_container_width=True)


# === COLONNA DESTRA (STBD) ===
with col_R:
    st.markdown("<div style='background-color: #e6ffe6; padding: 10px; border-radius: 10px; border: 2px solid #ccffcc;'>", unsafe_allow_html=True)
    st.markdown("<h3 style='text-align: center; color: #006600; margin: 0;'>STBD</h3>", unsafe_allow_html=True)
    
    # Orologio DX
    st.pyplot(plot_clock_sidebar(st.session_state.a2, '#006600', "Azimut"), use_container_width=True)
    
    st.slider("Azimut ", 0, 360, key="a2", label_visibility="collapsed")
    st.markdown("---")
    st.slider("Potenza % ", 0, 100, key="p2")
    st.metric("Spinta DX", f"{ton2:.1f} t")
    st.markdown("</div>", unsafe_allow_html=True)

    st.write("") # Spazio
    st.button("Reset PP", on_click=reset_pivot, use_container_width=True)

# === COLONNA CENTRALE (GRAFICA MIGLIORATA) ===
with col_C:
    # Controlli Pivot compatti in alto
    with st.expander("📍 Posizione Pivot Point", expanded=False):
        c1, c2 = st.columns(2)
        with c1: st.slider("Longitudinale Y", -16.0, 16.0, step=0.5, key="pp_y")
        with c2: st.slider("Trasversale X", -5.0, 5.0, step=0.5, key="pp_x")

    # Inizio Grafico Matplotlib "Evoluto"
    fig, ax = plt.subplots(figsize=(8, 10))
    
    # 1. SFONDO ACQUA (Miglioramento Estetico)
    ax.set_facecolor('#e0f7fa') # Azzurro acqua chiaro
    
    # 2. SCAFO REALISTICO (Preso dalla V6 ma disegnato con Matplotlib)
    hw = 5.85; stern = -16.25; bow_tip = 16.25; shoulder = 5.0
    # Disegno scafo con curve Bezier per renderlo morbido
    verts = [
        (-hw, stern), (hw, stern), (hw, 6.0), # Poppa e fianco dritto
        (0, bow_tip), # Punta
        (-hw, 6.0), (-hw, stern) # Fianco sinistro e chiusura
    ]
    codes = [Path.MOVETO, Path.LINETO, Path.LINETO, Path.CURVE3, Path.CURVE3, Path.LINETO]
    
    # Colore scafo grigio metallico con bordo scuro
    patch = PathPatch(Path(verts, codes), facecolor='#b0c4de', edgecolor='#2c3e50', lw=3, zorder=2)
    ax.add_patch(patch)
    
    # Linea di chiglia tratteggiata
    ax.plot([0, 0], [stern, bow_tip], color='#2c3e50', linestyle='--', alpha=0.3, zorder=2)

    # 3. PIVOT POINT (Evidente)
    ax.scatter(st.session_state.pp_x, st.session_state.pp_y, c='black', s=180, marker='o', edgecolors='white', linewidth=2, zorder=10)
    ax.text(st.session_state.pp_x + 0.8, st.session_state.pp_y, "PP", fontsize=12, weight='bold', zorder=10)

    # 4. FRECCIA MOMENTO (Attorno al PP - Molto più chiara)
    if abs(Total_Moment) > 10:
        arc_color = '#6a0dad' # Viola scuro
        radius = 5.0
        # Definizione arco
        if Total_Moment > 0: # Rotazione SX (Antiorario)
            style = "Simple, tail_width=2, head_width=10, head_length=10"
            connection = f"arc3, rad=0.3" 
            # Disegna arco a sinistra del PP
            arrow = FancyArrowPatch((pp_pos[0]+2, pp_pos[1]+radius), (pp_pos[0]-2, pp_pos[1]+radius),
                                    connectionstyle=connection, arrowstyle=style, color=arc_color, alpha=0.8, zorder=5)
            rot_text = "ROT. SX"
        else: # Rotazione DX (Orario)
            style = "Simple, tail_width=2, head_width=10, head_length=10"
            connection = f"arc3, rad=-0.3"
            # Disegna arco a destra del PP
            arrow = FancyArrowPatch((pp_pos[0]-2, pp_pos[1]+radius), (pp_pos[0]+2, pp_pos[1]+radius),
                                    connectionstyle=connection, arrowstyle=style, color=arc_color, alpha=0.8, zorder=5)
            rot_text = "ROT. DX"
            
        ax.add_patch(arrow)
        ax.text(pp_pos[0], pp_pos[1]+radius+2.5, rot_text, ha='center', color=arc_color, weight='bold', fontsize=11)

    # 5. VETTORI MOTORI
    scale = 0.35
    # SX
    ax.arrow(pos_sx[0], pos_sx[1], u1*scale, v1*scale, head_width=1.5, fc='#cc0000', ec='#cc0000', width=0.4, alpha=0.8, zorder=4)
    # DX
    ax.arrow(pos_dx[0], pos_dx[1], u2*scale, v2*scale, head_width=1.5, fc='#006600', ec='#006600', width=0.4, alpha=0.8, zorder=4)

    # 6. RISULTANTE
    ax.scatter(origin_res[0], origin_res[1], c='#004488', s=60, marker='D', zorder=4) # Diamante blu
    ax.arrow(origin_res[0], origin_res[1], res_u*scale, res_v*scale, head_width=2.5, head_length=2.5, fc='#004488', ec='#004488', width=0.8, alpha=0.6, zorder=4)

    # Linee tratteggiate di proiezione (solo se intersezione)
    if logic_used == "Intersezione (C)":
        ax.plot([pos_sx[0], origin_res[0]], [pos_sx[1], origin_res[1]], color='red', linestyle='--', lw=1, alpha=0.3)
        ax.plot([pos_dx[0], origin_res[0]], [pos_dx[1], origin_res[1]], color='green', linestyle='--', lw=1, alpha=0.3)

    # Limiti grafico fissi
    ax.set_xlim(-20, 20)
    ax.set_ylim(-25, 30)
    ax.set_aspect('equal')
    ax.axis('off') # Rimuovi assi cartesiani brutti
    
    st.pyplot(fig)

    # METRICHE FINALI
    st.markdown("### 📊 Risultati")
    m1, m2, m3 = st.columns(3)
    
    deg_res = np.degrees(np.arctan2(res_u, res_v))
    if deg_res < 0: deg_res += 360
    
    m1.metric("Tiro Totale", f"{res_ton:.1f} t")
    m2.metric("Direzione", f"{deg_res:.0f}°")
    m3.metric("Momento", f"{abs(Total_Moment):.0f} kNm", delta="SX" if Total_Moment > 0 else "DX", delta_color="inverse")
