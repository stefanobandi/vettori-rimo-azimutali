import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch
from constants import *
from physics import *
from visualization import *
import time

st.set_page_config(page_title="ASD Centurion V7.1", layout="wide")

st.markdown("""
<style>
    [data-testid="stMetricValue"] {
        font-size: 1.8rem !important;
        overflow-wrap: break-word;
        white-space: normal;
    }
    @media (max-width: 640px) {
        [data-testid="stMetricValue"] { font-size: 1.2rem !important; }
        [data-testid="stMetricLabel"] { font-size: 0.8rem !important; }
    }
</style>
""", unsafe_allow_html=True)

# --- INIZIALIZZAZIONE V7.1 ---
if "physics" not in st.session_state:
    st.session_state.physics = PhysicsEngine()
    st.session_state.last_time = time.time()
    st.session_state.history_x = []
    st.session_state.history_y = []
    # Stati motori
    st.session_state.update({"p1": 50, "a1": 0, "p2": 50, "a2": 0})

def set_engine_state(p1, a1, p2, a2):
    st.session_state.p1, st.session_state.a1 = p1, a1
    st.session_state.p2, st.session_state.a2 = p2, a2

def reset_engines(): 
    set_engine_state(50, 0, 50, 0)
    st.session_state.physics.reset()
    st.session_state.history_x = []
    st.session_state.history_y = []

# --- FUNZIONI PRESET V6.62 ---
def apply_slow_side_step(direction):
    # Logica V7.1 per Slow: 170/10 vs 350/190
    if direction == "DRITTA":
        set_engine_state(50, 10, 50, 170)
    else:
        set_engine_state(50, 350, 50, 190)

def apply_fast_side_step(direction):
    if direction == "DRITTA":
        set_engine_state(50, 45, 50, 325) # Approx
    else:
        set_engine_state(50, 315, 50, 35)

def apply_turn_on_the_spot(direction):
    if direction == "DRITTA":
        set_engine_state(50, 330, 50, 210)
    else:
        set_engine_state(50, 30, 50, 150)

def check_wash_hit(origin, wash_vec, target_pos, threshold=2.0):
    wash_len = np.linalg.norm(wash_vec)
    if wash_len < 0.1: return False
    wash_dir = wash_vec / wash_len
    to_target = target_pos - origin
    proj_length = np.dot(to_target, wash_dir)
    if proj_length > 0: 
        perp_dist = np.linalg.norm(to_target - (proj_length * wash_dir))
        return perp_dist < threshold
    return False

def intersect_lines(p1, angle1_deg, p2, angle2_deg):
    th1, th2 = np.radians(90 - angle1_deg), np.radians(90 - angle2_deg)
    v1, v2 = np.array([np.cos(th1), np.sin(th1)]), np.array([np.cos(th2), np.sin(th2)])
    matrix = np.column_stack((v1, -v2))
    if abs(np.linalg.det(matrix)) < 1e-4: return None
    try:
        t = np.linalg.solve(matrix, p2 - p1)[0]
        return p1 + t * v1
    except: return None

# --- HEADER AGGIORNATO ---
st.markdown("<h1 style='text-align: center;'>⚓ Rimorchiatore ASD Centurion ⚓</h1>", unsafe_allow_html=True)
st.markdown(f"""
<div style='text-align: center;'>
    <p style='font-size: 14px; margin-bottom: 5px;'>Per informazioni contattare stefano.bandi22@gmail.com</p>
    <b>Versione:</b> 7.1 (Auto-Pivot Physics) <br>
    <b>Bollard Pull:</b> 70 ton | <b>Lungh:</b> {int(SHIP_LENGTH)}m | <b>Largh:</b> {int(SHIP_WIDTH)}m
</div>
""", unsafe_allow_html=True)
st.write("---")

with st.sidebar:
    st.header("Comandi Globali")
    c1, c2 = st.columns(2)
    c1.button("Reset Motori", on_click=reset_engines, type="primary", use_container_width=True)
    c2.button("Reset Sim", on_click=st.session_state.physics.reset, use_container_width=True)
    st.markdown("---")
    show_wash = st.checkbox("Visualizza Scia (Propeller Wash)", value=True)
    # QUI LA MAGIA: Interruttore Statico/Dinamico
    show_prediction = st.checkbox("Predizione Movimento (Simulazione)", value=False)
    show_construction = st.checkbox("Costruzione Vettoriale", value=False)
    st.markdown("---")
    st.markdown("### ↕️ Longitudinali")
    cf1, cf2 = st.columns(2)
    cf1.button("⬆️ Tutta AVANTI", on_click=set_engine_state, args=(100,0,100,0), use_container_width=True)
    cf2.button("🔼 Mezza AVANTI", on_click=set_engine_state, args=(50,0,50,0), use_container_width=True)
    ca1, ca2 = st.columns(2)
    ca1.button("⬇️ Tutta INDIETRO", on_click=set_engine_state, args=(100,180,100,180), use_container_width=True)
    ca2.button("🔽 Mezza INDIETRO", on_click=set_engine_state, args=(50,180,50,180), use_container_width=True)
    st.markdown("---")
    st.markdown("### ↔️ Side Step")
    r1, r2 = st.columns(2)
    r1.button("⬅️ Fast SX", on_click=apply_fast_side_step, args=("SINISTRA",), use_container_width=True)
    r2.button("➡️ Fast DX", on_click=apply_fast_side_step, args=("DRITTA",), use_container_width=True)
    r3, r4 = st.columns(2)
    r3.button("⬅️ Slow SX", on_click=apply_slow_side_step, args=("SINISTRA",), use_container_width=True)
    r4.button("➡️ Slow DX", on_click=apply_slow_side_step, args=("DRITTA",), use_container_width=True)
    st.markdown("---")
    st.markdown("### 🔄 Turning on the Spot")
    ts1, ts2 = st.columns(2)
    ts1.button("🔄 Ruota SX", on_click=apply_turn_on_the_spot, args=("SINISTRA",), use_container_width=True)
    ts2.button("🔄 Ruota DX", on_click=apply_turn_on_the_spot, args=("DRITTA",), use_container_width=True)

pos_sx, pos_dx = np.array([-POS_THRUSTERS_X, POS_THRUSTERS_Y]), np.array([POS_THRUSTERS_X, POS_THRUSTERS_Y])

# CALCOLI STATICI V6.62 (Per vettori e tabella)
ton1_set = (st.session_state.p1/100)*BOLLARD_PULL_PER_ENGINE
ton2_set = (st.session_state.p2/100)*BOLLARD_PULL_PER_ENGINE
rad1, rad2 = np.radians(st.session_state.a1), np.radians(st.session_state.a2)

F_sx_eff_v = np.array([ton1_set*np.sin(rad1), ton1_set*np.cos(rad1)])
F_dx_eff_v = np.array([ton2_set*np.sin(rad2), ton2_set*np.cos(rad2)])

wash_sx_hits_dx = check_wash_hit(pos_sx, -F_sx_eff_v, pos_dx)
wash_dx_hits_sx = check_wash_hit(pos_dx, -F_dx_eff_v, pos_sx)
eff_sx, eff_dx = (0.8 if wash_dx_hits_sx else 1.0), (0.8 if wash_sx_hits_dx else 1.0)

F_sx_eff = F_sx_eff_v * eff_sx
F_dx_eff = F_dx_eff_v * eff_dx
ton1_eff, ton2_eff = ton1_set * eff_sx, ton2_set * eff_dx

res_u_total = (F_sx_eff[0] + F_dx_eff[0])
res_v_total = (F_sx_eff[1] + F_dx_eff[1])
res_ton = np.sqrt(res_u_total**2 + res_v_total**2)
direzione_nautica = np.degrees(np.arctan2(res_u_total, res_v_total)) % 360

# Intersezione vettori
inter = intersect_lines(pos_sx, st.session_state.a1, pos_dx, st.session_state.a2)
use_weighted = True
if inter is not None:
    if np.linalg.norm(inter) <= 50.0: use_weighted = False

# --- LOGICA SIMULAZIONE V7.1 ---
pp_y_auto = 0.0 # Default visualization
if show_prediction:
    # Calcolo DT
    current_time = time.time()
    dt = current_time - st.session_state.last_time
    st.session_state.last_time = current_time
    if dt > 0.1: dt = 0.1

    # Conversione Input per Physics Engine
    thrust_l = (st.session_state.p1 / 100.0) * MAX_THRUST
    thrust_r = (st.session_state.p2 / 100.0) * MAX_THRUST
    
    # Update Fisica
    st.session_state.physics.update(dt, thrust_l, st.session_state.a1, thrust_r, st.session_state.a2)
    
    # Store History
    state = st.session_state.physics.state
    st.session_state.history_x.append(state[0])
    st.session_state.history_y.append(state[1])
    if len(st.session_state.history_x) > 300:
        st.session_state.history_x.pop(0)
        st.session_state.history_y.pop(0)
        
    pp_y_auto = st.session_state.physics.current_pp_y

else:
    # Modalità Statica: Reset e Calcolo PP istantaneo solo per visualizzazione
    st.session_state.physics.reset()
    thrust_l = (st.session_state.p1 / 100.0) * MAX_THRUST
    thrust_r = (st.session_state.p2 / 100.0) * MAX_THRUST
    pp_y_auto = st.session_state.physics.calculate_dynamic_pivot(thrust_l, st.session_state.a1, thrust_r, st.session_state.a2)

# --- LAYOUT PRINCIPALE ---
col_l, col_c, col_r = st.columns([1.2, 2.6, 1.2])

with col_l:
    st.slider("Potenza SX", 0, 100, key="p1", format="%d%%")
    st.metric("Spinta SX", f"{ton1_eff:.1f} t")
    st.slider("Azimuth SX", 0, 360, key="a1", format="%03d°")
    st.pyplot(plot_clock(st.session_state.a1, 'red'))
    
with col_r:
    st.slider("Potenza DX", 0, 100, key="p2", format="%d%%")
    st.metric("Spinta DX", f"{ton2_eff:.1f} t")
    st.slider("Azimuth DX", 0, 360, key="a2", format="%03d°")
    st.pyplot(plot_clock(st.session_state.a2, 'green'))

with col_c:
    with st.expander("📍 Pivot Point (Auto Logic V7.1)", expanded=True):
        st.metric("Posizione PP (Auto)", f"Y = {pp_y_auto:.2f} m")
    
    if wash_dx_hits_sx:
        st.error("⚠️ ATTENZIONE: Flusso DX investe SX -> Perdita 20% spinta SX")
    if wash_sx_hits_dx:
        st.error("⚠️ ATTENZIONE: Flusso SX investe DX -> Perdita 20% spinta DX")

    fig, ax = plt.subplots(figsize=(10, 12))
    
    # GESTIONE VIEWPORT E STATO
    if show_prediction:
        state = st.session_state.physics.state
        # CONVERSIONE ANGOLO: Math (0=Est, CCW) -> Visual (0=Nord, CW)
        # Physics 0 = Est. Visual 0 = Nord. 
        # Visual = 90 - Math.
        math_angle_deg = np.degrees(state[2])
        draw_heading = 90 - math_angle_deg
        
        draw_x = state[0]
        draw_y = state[1]
        
        # Scia
        if len(st.session_state.history_x) > 1:
            ax.plot(st.session_state.history_x, st.session_state.history_y, color='#64C8FF', linewidth=1.5, alpha=0.6)
            
        # Centra su nave
        window = 60
        ax.set_xlim(draw_x - window, draw_x + window)
        ax.set_ylim(draw_y - window, draw_y + window)
        
        # Disegna Nave Dinamica
        draw_hull_silhouette(ax, draw_x, draw_y, draw_heading, alpha=0.9)
        
        # Disegna Pivot Point
        # Devo trasformarlo in coordinate mondo visuali
        # PP è relativo alla nave (0, pp_y_auto).
        tr = Affine2D().rotate_deg(-draw_heading).translate(draw_x, draw_y) + ax.transData
        pp_circle = plt.Circle((0, pp_y_auto), radius=0.8, color='yellow', zorder=15)
        pp_circle.set_transform(tr)
        ax.add_patch(pp_circle)

    else:
        # Modalità Statica V6.62
        draw_x, draw_y, draw_heading = 0, 0, 0
        ax.set_xlim(-30, 30)
        ax.set_ylim(-40, 35)
        
        # Disegna Nave Statica
        draw_static_elements(ax, pos_sx, pos_dx)
        
        # Disegna Pivot Statico
        ax.scatter(0, pp_y_auto, c='black', s=120, zorder=15, label="Pivot Point")
        
        # Vettori e Costruzione (Solo in statico)
        origin_res = inter if not use_weighted else np.array([(ton1_eff * pos_sx[0] + ton2_eff * pos_dx[0]) / (ton1_eff + ton2_eff + 0.001), POS_THRUSTERS_Y])
        sc = 0.7
        
        if not show_construction:
            ax.plot([pos_sx[0], origin_res[0]], [pos_sx[1], origin_res[1]], 'r--', lw=1, alpha=0.3)
            ax.plot([pos_dx[0], origin_res[0]], [pos_dx[1], origin_res[1]], 'g--', lw=1, alpha=0.3)
        else:
            if inter is not None:
                v_sx_len = np.linalg.norm(F_sx_eff)*sc; v_dx_len = np.linalg.norm(F_dx_eff)*sc
                ax.arrow(inter[0], inter[1], F_sx_eff[0]*sc, F_sx_eff[1]*sc, fc='red', ec='red', width=0.08, head_width=min(0.3, v_sx_len*0.4), head_length=min(0.4, v_sx_len*0.5), alpha=0.3, zorder=6, length_includes_head=True)
                ax.arrow(inter[0], inter[1], F_dx_eff[0]*sc, F_dx_eff[1]*sc, fc='green', ec='green', width=0.08, head_width=min(0.3, v_dx_len*0.4), head_length=min(0.4, v_dx_len*0.5), alpha=0.3, zorder=6, length_includes_head=True)
                pSX_tip = inter + F_sx_eff*sc; pDX_tip = inter + F_dx_eff*sc; pRES_tip = inter + np.array([res_u_total, res_v_total])*sc
                ax.plot([pSX_tip[0], pRES_tip[0]], [pSX_tip[1], pRES_tip[1]], color='gray', ls='--', lw=1.0, alpha=0.8, zorder=5)
                ax.plot([pDX_tip[0], pRES_tip[0]], [pDX_tip[1], pRES_tip[1]], color='gray', ls='--', lw=1.0, alpha=0.8, zorder=5)
                ax.plot([pos_sx[0], inter[0]], [pos_sx[1], inter[1]], 'r:', lw=1, alpha=0.4); ax.plot([pos_dx[0], inter[0]], [pos_dx[1], inter[1]], 'g:', lw=1, alpha=0.4)
                
        ax.arrow(pos_sx[0], pos_sx[1], F_sx_eff[0]*sc, F_sx_eff[1]*sc, fc='red', ec='red', width=0.15, head_width=min(0.5, np.linalg.norm(F_sx_eff)*sc*0.4), head_length=min(0.7, np.linalg.norm(F_sx_eff)*sc*0.5), zorder=4, alpha=0.7, length_includes_head=True)
        ax.arrow(pos_dx[0], pos_dx[1], F_dx_eff[0]*sc, F_dx_eff[1]*sc, fc='green', ec='green', width=0.15, head_width=min(0.5, np.linalg.norm(F_dx_eff)*sc*0.4), head_length=min(0.7, np.linalg.norm(F_dx_eff)*sc*0.5), zorder=4, alpha=0.7, length_includes_head=True)
        
        if res_ton > 0.1:
            v_res_len = res_ton * sc
            ax.arrow(origin_res[0], origin_res[1], res_u_total*sc, res_v_total*sc, fc='blue', ec='blue', width=0.3, head_width=min(0.8, v_res_len*0.4), head_length=min(1.2, v_res_len*0.5), alpha=0.7, zorder=8, length_includes_head=True)

    # Disegna elementi comuni
    if show_wash:
        # In dinamico non disegniamo wash per ora per pulizia, o potremmo aggiungerlo
        # Manteniamo wash statico visualizzato sempre relativo alla nave
        # Per semplicità lo mostriamo solo in statico o dovremmo trasformarlo
        if not show_prediction:
            draw_wash(ax, pos_sx, st.session_state.a1, st.session_state.p1)
            draw_wash(ax, pos_dx, st.session_state.a2, st.session_state.p2)
            
    # Draw Props (in statico sono fissi, in dinamico non li disegniamo sulla silhouette blu per ora)
    if not show_prediction:
        draw_propeller(ax, pos_sx, st.session_state.a1, color='red')
        draw_propeller(ax, pos_dx, st.session_state.a2, color='green')

    ax.set_aspect('equal')
    ax.axis('off')
    st.pyplot(fig)
    
    if show_prediction:
        st.markdown("<p style='color: blue; text-align: center; font-weight: bold;'>Simulazione Fisica V7.1 Attiva</p>", unsafe_allow_html=True)
        time.sleep(0.05)
        st.rerun()

# --- TABELLA RIEPILOGATIVA ---
st.write("---")
st.subheader("📋 Telemetria di Manovra")

# Momento approssimativo statico
M_tm_PP = ((pos_sx-[0, pp_y_auto])[0]*F_sx_eff[1] - (pos_sx-[0, pp_y_auto])[1]*F_sx_eff[0] + 
           (pos_dx-[0, pp_y_auto])[0]*F_dx_eff[1] - (pos_dx-[0, pp_y_auto])[1]*F_dx_eff[0])
M_knm = M_tm_PP * G_ACCEL

c_data1, c_data2, c_data3, c_data4 = st.columns(4)
with c_data1:
    st.metric("Spinta Risultante", f"{res_ton:.1f} t")
with c_data2:
    st.metric("Direzione Spinta", f"{int(direzione_nautica)}°")
with c_data3:
    st.metric("Momento (PP)", f"{int(M_tm_PP)} t*m", delta_color="off")
with c_data4:
    st.metric("Momento (kNm)", f"{int(M_knm)} kNm")

df_engines = pd.DataFrame({
    "Parametro": ["Potenza (%)", "Azimuth (°)", "Spinta Teorica (t)", "Wash Penalty", "Spinta Effettiva (t)"],
    "Propulsore SX": [st.session_state.p1, st.session_state.a1, f"{(ton1_set):.1f}", "SÌ (-20%)" if wash_dx_hits_sx else "NO", f"{ton1_eff:.1f}"],
    "Propulsore DX": [st.session_state.p2, st.session_state.a2, f"{(ton2_set):.1f}", "SÌ (-20%)" if wash_sx_hits_dx else "NO", f"{ton2_eff:.1f}"]
})
st.table(df_engines)
