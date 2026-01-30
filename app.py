import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, Rectangle, Circle, Arrow
from constants import *
from physics import *
from visualization import *
import time

st.set_page_config(page_title="ASD Centurion V7.8", layout="wide")

st.markdown("""
<style>
    [data-testid="stMetricValue"] {
        font-size: 1.8rem !important;
        overflow-wrap: break-word;
        white-space: normal;
    }
    /* Stile per i bottoni zoom compatti */
    div[data-testid="column"] button {
        height: auto;
        padding-top: 5px;
        padding-bottom: 5px;
    }
</style>
""", unsafe_allow_html=True)

# --- INIZIALIZZAZIONE ---
if "physics" not in st.session_state:
    st.session_state.physics = PhysicsEngine()
    st.session_state.last_time = time.time()
    st.session_state.history_x = []
    st.session_state.history_y = []
    st.session_state.update({"p1": 50, "a1": 0, "p2": 50, "a2": 0})

if "zoom_level" not in st.session_state:
    st.session_state.zoom_level = 80.0

# Pivot Point Manuale Session State
if "pp_manual_x" not in st.session_state:
    st.session_state.pp_manual_x = DEFAULT_PP_X
if "pp_manual_y" not in st.session_state:
    st.session_state.pp_manual_y = DEFAULT_PP_Y

def set_engine_state(p1, a1, p2, a2):
    st.session_state.p1, st.session_state.a1 = p1, a1
    st.session_state.p2, st.session_state.a2 = p2, a2

def reset_engines(): 
    set_engine_state(50, 0, 50, 0)
    st.session_state.physics.reset()
    st.session_state.history_x = []
    st.session_state.history_y = []

def full_reset_sim():
    st.session_state.physics.reset()
    st.session_state.history_x = []
    st.session_state.history_y = []
    st.session_state.zoom_level = 80.0
    # Reset anche del Pivot ai default
    reset_pivot_point()

def reset_pivot_point():
    st.session_state.pp_manual_x = DEFAULT_PP_X
    st.session_state.pp_manual_y = DEFAULT_PP_Y

def update_zoom(delta):
    new_zoom = st.session_state.zoom_level + delta
    if new_zoom < 20: new_zoom = 20
    if new_zoom > 300: new_zoom = 300
    st.session_state.zoom_level = new_zoom

# --- SOLVER FAST SIDE STEP (CORRETTO V7.8) ---
def solve_fast_side_step(mode):
    # Logica: Applicare spinta laterale e calcolare la correzione longitudinale (Fx)
    # per azzerare il momento sul Pivot Point manuale attuale.
    
    pp_x = st.session_state.pp_manual_x
    pp_y = st.session_state.pp_manual_y
    
    # 1. Definiamo la spinta laterale desiderata (Base 50%)
    thrust_base = 50.0 
    
    # Direzione laterale pura (+1 Right, -1 Left)
    sign = 1.0 if mode == "DRITTA" else -1.0
    
    # Componente Fy (Sway) generata da entrambi i motori (entrambi spingono di lato)
    # Ipotizziamo Fy_totale distribuita 50/50
    Fy_single = thrust_base * sign # 50% tonnellaggio in direzione
    
    # 2. Calcolo del Momento generato dalla sola spinta laterale
    # Momento = Fy * Braccio_Longitudinale
    # Braccio = (Pos_Motori_Y - Pivot_Y)
    # Nota: Se motori sono a -12 e Pivot a +5, braccio è -17.
    # Fy positivo (dx) * Braccio negativo (-17) = Momento Negativo (Rotazione Oraria/DX)
    arm_y = POS_THRUSTERS_Y - pp_y
    
    M_sway_sx = (pos_sx[0] - pp_x) * 0 - (arm_y) * Fy_single # Cross product r x F (Fx=0 qui)
    M_sway_dx = (pos_dx[0] - pp_x) * 0 - (arm_y) * Fy_single
    M_tot_sway = M_sway_sx + M_sway_dx
    
    # 3. Dobbiamo generare un Momento opposto usando Fx (Surge)
    # M_correction = - M_tot_sway
    # Usiamo una coppia: SX spinge/tira, DX tira/spinge.
    # Braccio X = Distanza laterale dal Pivot
    arm_x_sx = pos_sx[0] - pp_x # circa -2.7
    arm_x_dx = pos_dx[0] - pp_x # circa +2.7
    
    # Vogliamo Fx_sx e Fx_dx tali che:
    # (arm_x_sx * Fx_sx) - (arm_y * 0) + (arm_x_dx * Fx_dx) - (arm_y * 0) = - M_tot_sway
    # Assumiamo Fx_sx = -Fx_dx (Coppia pura) -> Fx_sx = F_corr, Fx_dx = -F_corr
    # arm_x_sx * F_corr + arm_x_dx * (-F_corr) = - M_tot_sway
    # F_corr * (arm_x_sx - arm_x_dx) = - M_tot_sway
    
    denom = (arm_x_sx - arm_x_dx) # circa -5.4
    if abs(denom) < 0.1: denom = -0.1
    
    F_corr_sx = - M_tot_sway / denom
    F_corr_dx = - F_corr_sx
    
    # 4. Ricomposizione vettori (Fy, Fx) -> (Potenza, Angolo)
    # SX Engine
    vec_sx = np.array([F_corr_sx, Fy_single])
    pow_sx = np.linalg.norm(vec_sx)
    ang_sx = np.degrees(np.arctan2(vec_sx[0], vec_sx[1])) % 360 # atan2(x, y) per azimuth nautico
    
    # DX Engine
    vec_dx = np.array([F_corr_dx, Fy_single])
    pow_dx = np.linalg.norm(vec_dx)
    ang_dx = np.degrees(np.arctan2(vec_dx[0], vec_dx[1])) % 360
    
    # Normalizzazione se la potenza supera 100%
    max_p = max(pow_sx, pow_dx)
    if max_p > 100:
        scale = 100.0 / max_p
        pow_sx *= scale
        pow_dx *= scale
        # Nota: scalando riduciamo anche la Fy, quindi il side step sarà più lento, ma bilanciato.

    set_engine_state(int(pow_sx), int(ang_sx), int(pow_dx), int(ang_dx))


def apply_slow_side_step(direction):
    if direction == "DRITTA":
        set_engine_state(50, 45, 50, 135) # Configurazione a V per spinta laterale + stabilità
    else:
        set_engine_state(50, 315, 50, 225)

def apply_turn_on_the_spot(direction):
    if direction == "DRITTA":
        set_engine_state(50, 330, 50, 210) # Rotazione pura
    else:
        set_engine_state(50, 150, 50, 30)

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

# --- HEADER ---
st.markdown("<h1 style='text-align: center;'>⚓ ASD Centurion V7.8 ⚓</h1>", unsafe_allow_html=True)
st.markdown("""
<div style='text-align: center;'>
    <i>per info contattare stefano.bandi22@gmail.com</i>
</div>
""", unsafe_allow_html=True)
st.write("---")

with st.sidebar:
    st.header("Comandi Globali")
    
    c1, c2 = st.columns(2)
    c1.button("Reset Motori", on_click=reset_engines, type="primary", use_container_width=True)
    c2.button("Reset Sim", on_click=full_reset_sim, use_container_width=True)
    
    st.markdown("---")
    
    st.markdown("### 👁️ Visualizzazione")
    show_wash = st.checkbox("Mostra Propeller Wash", value=True)
    show_prediction = st.checkbox("Predizione Movimento (BETA)", value=False)
    
    st.markdown("**Regolazione Zoom:**")
    z1, z2, z3 = st.columns([1, 1, 2])
    z1.button("➕", on_click=update_zoom, args=(-10,), help="Zoom In", use_container_width=True)
    z2.button("➖", on_click=update_zoom, args=(10,), help="Zoom Out", use_container_width=True)
    z3.metric("Raggio", f"{int(st.session_state.zoom_level)} m", label_visibility="collapsed")
    
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
    r1.button("⬅️ Fast SX", on_click=solve_fast_side_step, args=("SINISTRA",), use_container_width=True)
    r2.button("➡️ Fast DX", on_click=solve_fast_side_step, args=("DRITTA",), use_container_width=True)
    r3, r4 = st.columns(2)
    r3.button("⬅️ Slow SX", on_click=apply_slow_side_step, args=("SINISTRA",), use_container_width=True)
    r4.button("➡️ Slow DX", on_click=apply_slow_side_step, args=("DRITTA",), use_container_width=True)
    st.markdown("---")
    st.markdown("### 🔄 Turning on the Spot")
    ts1, ts2 = st.columns(2)
    ts1.button("🔄 Ruota SX", on_click=apply_turn_on_the_spot, args=("SINISTRA",), use_container_width=True)
    ts2.button("🔄 Ruota DX", on_click=apply_turn_on_the_spot, args=("DRITTA",), use_container_width=True)
    
    st.markdown("---")
    st.markdown("### 📍 Pivot Point Manuale")
    pp_c1, pp_c2 = st.columns(2)
    # Limiti impostati su dimensioni scafo approssimative (W=11.7 -> +/-5.8, L=32.5 -> +/-16.0)
    st.session_state.pp_manual_x = pp_c1.number_input("Pos. X (m)", value=float(st.session_state.pp_manual_x), step=0.1, min_value=-5.8, max_value=5.8)
    st.session_state.pp_manual_y = pp_c2.number_input("Pos. Y (m)", value=float(st.session_state.pp_manual_y), step=0.1, min_value=-16.0, max_value=16.0)
    st.button("Reset PP Default", on_click=reset_pivot_point, use_container_width=True)

pos_sx, pos_dx = np.array([-POS_THRUSTERS_X, POS_THRUSTERS_Y]), np.array([POS_THRUSTERS_X, POS_THRUSTERS_Y])

# CALCOLI VETTORIALI
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

inter = intersect_lines(pos_sx, st.session_state.a1, pos_dx, st.session_state.a2)
use_weighted = True
if inter is not None:
    if np.linalg.norm(inter) <= 50.0: use_weighted = False
    
origin_res = inter if not use_weighted else np.array([(ton1_eff * pos_sx[0] + ton2_eff * pos_dx[0]) / (ton1_eff + ton2_eff + 0.001), POS_THRUSTERS_Y])

# --- UPDATE FISICA ---
if show_prediction:
    current_time = time.time()
    dt = current_time - st.session_state.last_time
    st.session_state.last_time = current_time
    if dt > 0.1: dt = 0.1

    thrust_l = (st.session_state.p1 / 100.0) * MAX_THRUST
    thrust_r = (st.session_state.p2 / 100.0) * MAX_THRUST
    
    st.session_state.physics.update(dt, thrust_l, st.session_state.a1, thrust_r, st.session_state.a2, 
                                    st.session_state.pp_manual_x, st.session_state.pp_manual_y)
    
    state = st.session_state.physics.state
    st.session_state.history_x.append(state[0])
    st.session_state.history_y.append(state[1])
    if len(st.session_state.history_x) > 1000:
        st.session_state.history_x.pop(0)
        st.session_state.history_y.pop(0)
else:
    st.session_state.physics.reset()
    st.session_state.last_time = time.time() 
    st.session_state.physics.current_pp_y = st.session_state.pp_manual_y

# --- LAYOUT GUI ---
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
    if wash_dx_hits_sx:
        st.error("⚠️ ATTENZIONE: Flusso DX investe SX -> Perdita 20% spinta SX")
    if wash_sx_hits_dx:
        st.error("⚠️ ATTENZIONE: Flusso SX investe DX -> Perdita 20% spinta DX")

    fig, ax = plt.subplots(figsize=(10, 12))
    ax.set_facecolor(COLOR_SEA) 
    
    # Wash 
    if show_wash:
        draw_wash(ax, pos_sx, st.session_state.a1, st.session_state.p1)
        draw_wash(ax, pos_dx, st.session_state.a2, st.session_state.p2)
    
    # Nave e Scafo
    draw_static_elements(ax, pos_sx, pos_dx)
    
    # Pivot Point Visual (MANUALE)
    ax.scatter(st.session_state.pp_manual_x, st.session_state.pp_manual_y, c='yellow', s=150, zorder=20, edgecolors='black', label="Pivot")
    
    # VETTORI DI FORZA (Solid)
    sc = 0.7 
    ax.arrow(pos_sx[0], pos_sx[1], F_sx_eff[0]*sc, F_sx_eff[1]*sc, fc='red', ec='red', width=0.15, head_width=min(0.5, np.linalg.norm(F_sx_eff)*sc*0.4), head_length=min(0.7, np.linalg.norm(F_sx_eff)*sc*0.5), zorder=25, alpha=0.9, length_includes_head=True)
    ax.arrow(pos_dx[0], pos_dx[1], F_dx_eff[0]*sc, F_dx_eff[1]*sc, fc='green', ec='green', width=0.15, head_width=min(0.5, np.linalg.norm(F_dx_eff)*sc*0.4), head_length=min(0.7, np.linalg.norm(F_dx_eff)*sc*0.5), zorder=25, alpha=0.9, length_includes_head=True)
    
    # Vettore Risultante (BLU)
    if res_ton > 0.1:
        v_res_len = res_ton * sc
        ax.arrow(origin_res[0], origin_res[1], res_u_total*sc, res_v_total*sc, fc='blue', ec='blue', width=0.3, head_width=min(0.8, v_res_len*0.4), head_length=min(1.2, v_res_len*0.5), alpha=0.7, zorder=26, length_includes_head=True)

    # COSTRUZIONE VETTORIALE (MODIFICATA V7.8)
    if show_construction and inter is not None and res_ton > 0.1:
        ax.plot([pos_sx[0], inter[0]], [pos_sx[1], inter[1]], color='red', linestyle='--', linewidth=1.5, alpha=0.5, zorder=23)
        ax.plot([pos_dx[0], inter[0]], [pos_dx[1], inter[1]], color='green', linestyle='--', linewidth=1.5, alpha=0.5, zorder=23)

        tip_sx_trans = inter + F_sx_eff * sc
        tip_dx_trans = inter + F_dx_eff * sc

        ax.arrow(inter[0], inter[1], F_sx_eff[0]*sc, F_sx_eff[1]*sc, color='red', ls='--', lw=1.5, alpha=0.6, head_width=0, zorder=24)
        ax.arrow(inter[0], inter[1], F_dx_eff[0]*sc, F_dx_eff[1]*sc, color='green', ls='--', lw=1.5, alpha=0.6, head_width=0, zorder=24)

        pRES_tip = inter + np.array([res_u_total, res_v_total]) * sc
        ax.plot([tip_sx_trans[0], pRES_tip[0]], [tip_sx_trans[1], pRES_tip[1]], color='green', linestyle='--', linewidth=2.0, alpha=0.8, zorder=24)
        ax.plot([tip_dx_trans[0], pRES_tip[0]], [tip_dx_trans[1], pRES_tip[1]], color='red', linestyle='--', linewidth=2.0, alpha=0.8, zorder=24)
    
    if show_prediction:
        state = st.session_state.physics.state
        ship_x, ship_y = state[0], state[1]
        ship_heading = state[2]
        
        rot_angle = -(ship_heading - np.pi/2)
        c, s = np.cos(rot_angle), np.sin(rot_angle)
            
        if len(st.session_state.history_x) > 1:
            hx = np.array(st.session_state.history_x)
            hy = np.array(st.session_state.history_y)
            dx = hx - ship_x
            dy = hy - ship_y
            tx = dx * c - dy * s
            ty = dx * s + dy * c
            ax.plot(tx, ty, color='#333333', linewidth=2, alpha=0.4, zorder=0)

        grid_spacing = 50.0 
        view_radius = st.session_state.zoom_level * 2.5 
        
        offset_x = ship_x % grid_spacing
        offset_y = ship_y % grid_spacing
        
        nx = int(view_radius / grid_spacing) + 2
        x_range = np.linspace(-view_radius, view_radius, nx * 2)
        y_range = np.linspace(-view_radius, view_radius, nx * 2)
        gx, gy = np.meshgrid(x_range, y_range)
        
        gx -= offset_x
        gy -= offset_y
        
        gx_r = gx * c - gy * s
        gy_r = gx * s + gy * c
        
        ax.scatter(gx_r, gy_r, c='black', s=20, alpha=0.5, zorder=0)

        math_deg = np.degrees(ship_heading)
        naut_hdg = (90 - math_deg) % 360
        speed_kn = np.sqrt(state[3]**2 + state[4]**2) * 1.94
        rot_deg_min = np.degrees(state[5]) * 60
        
        info_text = (
            f"Pr : {naut_hdg:05.1f}°\n"
            f"V  : {speed_kn:5.1f} kn\n"
            f"RoT: {rot_deg_min:5.1f} °/m"
        )
        
        ax.text(-st.session_state.zoom_level*0.9, st.session_state.zoom_level*0.75, info_text, 
                color='black', fontsize=12, family='monospace', fontweight='bold',
                bbox=dict(facecolor='white', alpha=0.8, edgecolor='black'))
        
        zoom = st.session_state.zoom_level
        ax.set_xlim(-zoom, zoom)
        ax.set_ylim(-zoom, zoom)
        
    else:
        draw_propeller(ax, pos_sx, st.session_state.a1, color='red')
        draw_propeller(ax, pos_dx, st.session_state.a2, color='green')
        
        ax.set_xlim(-30, 30)
        ax.set_ylim(-40, 40)

    ax.set_aspect('equal')
    ax.axis('off')
    st.pyplot(fig)
    
    if show_prediction:
        time.sleep(0.05)
        st.rerun()

# --- TABELLA TELEMETRIA (Con Pivot Manuale) ---
st.write("---")
st.subheader("📋 Telemetria di Manovra (Pivot Manuale)")

PP_MAN = np.array([st.session_state.pp_manual_x, st.session_state.pp_manual_y])

arm_sx = pos_sx - PP_MAN
arm_dx = pos_dx - PP_MAN

M_sx = arm_sx[0]*F_sx_eff[1] - arm_sx[1]*F_sx_eff[0]
M_dx = arm_dx[0]*F_dx_eff[1] - arm_dx[1]*F_dx_eff[0]
M_tm_PP = M_sx + M_dx
M_knm = M_tm_PP * G_ACCEL

c1, c2, c3, c4 = st.columns(4)
c1.metric("Spinta Risultante", f"{res_ton:.1f} t")
c2.metric("Direzione Spinta", f"{int(direzione_nautica)}°")
c3.metric("Momento (PP)", f"{int(M_tm_PP)} t*m")
c4.metric("Momento (kNm)", f"{int(M_knm)} kNm")

df_engines = pd.DataFrame({
    "Parametro": ["Potenza (%)", "Azimuth (°)", "Spinta Teorica (t)", "Wash Penalty", "Spinta Effettiva (t)"],
    "Propulsore SX": [st.session_state.p1, st.session_state.a1, f"{(ton1_set):.1f}", "SÌ (-20%)" if wash_dx_hits_sx else "NO", f"{ton1_eff:.1f}"],
    "Propulsore DX": [st.session_state.p2, st.session_state.a2, f"{(ton2_set):.1f}", "SÌ (-20%)" if wash_sx_hits_dx else "NO", f"{ton2_eff:.1f}"]
})
st.table(df_engines)
