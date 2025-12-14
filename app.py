import streamlit as st
import numpy as np
import plotly.graph_objects as go

# --- CONFIGURAZIONE PAGINA ---
st.set_page_config(page_title="ASD Centurion V6.0", layout="wide")

# --- GESTIONE SESSION STATE ---
defaults = {
    "p1": 50, "a1": 0,    # Motore SX
    "p2": 50, "a2": 0,    # Motore DX
    "pp_x": 0.0, "pp_y": 5.42, # Pivot Point default
    "a1_control": "0° (Avanti)",
    "a2_control": "0° (Avanti)"
}

for key, val in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = val

# Mapping per i controlli Azimut semplificati
AZIMUT_OPTIONS = {
    "0° (Avanti)": 0, "45°": 45, "90° (Trasv.)": 90, "135°": 135, 
    "180° (Indietro)": 180, "225°": 225, "270°": 270, "315°": 315, 
    "Custom": None
}

# --- FUNZIONI DI RESET ---
def reset_engines():
    st.session_state.p1 = 50
    st.session_state.a1 = 0
    st.session_state.p2 = 50
    st.session_state.a2 = 0
    st.session_state.a1_control = "0° (Avanti)"
    st.session_state.a2_control = "0° (Avanti)"

def reset_pivot():
    st.session_state.pp_x = 0.0
    st.session_state.pp_y = 5.42

# --- HEADER ---
st.markdown("<h1 style='text-align: center; color: #2E86C1;'>⚓ ASD 'CENTURION' V6.0</h1>", unsafe_allow_html=True)
st.markdown("<h4 style='text-align: center; color: #566573;'>Simulatore Interattivo Plotly</h4>", unsafe_allow_html=True)
st.write("---")

# --- SIDEBAR CONTROLLI ---
with st.sidebar:
    st.header("⚙️ Plancia Comandi")
    
    # Reset
    c1, c2 = st.columns(2)
    with c1: st.button("Reset Motori", on_click=reset_engines, type="primary", use_container_width=True)
    with c2: st.button("Reset PP", on_click=reset_pivot, use_container_width=True)
    
    st.markdown("---")
    
    # PORT
    st.markdown("### 🔴 PORT (SX)")
    a1_opt = st.selectbox("Azimut SX", list(AZIMUT_OPTIONS.keys()), key="a1_control")
    if AZIMUT_OPTIONS[a1_opt] is not None:
        st.session_state.a1 = AZIMUT_OPTIONS[a1_opt]
    else:
        st.slider("Fine Tuning SX", 0, 360, key="a1", label_visibility="collapsed")
    st.slider("Potenza SX %", 0, 100, key="p1")
    
    st.markdown("---")
    
    # STBD
    st.markdown("### 🟢 STBD (DX)")
    a2_opt = st.selectbox("Azimut DX", list(AZIMUT_OPTIONS.keys()), key="a2_control")
    if AZIMUT_OPTIONS[a2_opt] is not None:
        st.session_state.a2 = AZIMUT_OPTIONS[a2_opt]
    else:
        st.slider("Fine Tuning DX", 0, 360, key="a2", label_visibility="collapsed")
    st.slider("Potenza DX %", 0, 100, key="p2")

    st.markdown("---")
    st.markdown("### 📍 Pivot Point")
    st.slider("Longitudinale (Y)", -16.0, 16.0, step=0.5, key="pp_y")
    st.slider("Trasversale (X)", -5.0, 5.0, step=0.5, key="pp_x")

# --- CALCOLI FISICI ---
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

# Momenti
r_sx = pos_sx - pp_pos
r_dx = pos_dx - pp_pos
M_sx = r_sx[0] * v1 - r_sx[1] * u1 
M_dx = r_dx[0] * v2 - r_dx[1] * u2
Total_Moment = M_sx + M_dx

# Risultante Totale
res_u = u1 + u2
res_v = v1 + v2
res_ton = np.sqrt(res_u**2 + res_v**2)

# Calcolo Punto di Applicazione
origin_res = np.array([0.0, -12.0])
logic_used = "B (Media Ponderata)"

def intersect(p1, ang1, p2, ang2):
    th1, th2 = np.radians(90-ang1), np.radians(90-ang2)
    v1_vec = np.array([np.cos(th1), np.sin(th1)])
    v2_vec = np.array([np.cos(th2), np.sin(th2)])
    mat = np.column_stack((v1_vec, -v2_vec))
    if abs(np.linalg.det(mat)) < 1e-3: return None
    t = np.linalg.solve(mat, p2 - p1)[0]
    return p1 + t * v1_vec

if ton1 > 1 and ton2 > 1:
    inter = intersect(pos_sx, st.session_state.a1, pos_dx, st.session_state.a2)
    if inter is not None and np.linalg.norm(inter - np.array([0,-12])) < 60:
        origin_res = inter
        logic_used = "C (Intersezione Vettori)"
    elif (ton1+ton2) > 0:
         origin_res = np.array([(ton1*pos_sx[0] + ton2*pos_dx[0])/(ton1+ton2), -12.0])

# --- COSTRUZIONE GRAFICO PLOTLY ---
fig = go.Figure()

# 1. SCAFO
hull_x = [-5.85, 5.85, 5.85, 4.0, 0, -4.0, -5.85, -5.85]
hull_y = [-16.25, -16.25, 5.0, 14.0, 16.25, 14.0, 5.0, -16.25]

fig.add_trace(go.Scatter(
    x=hull_x, y=hull_y,
    fill="toself",
    fillcolor="rgba(200, 200, 200, 0.5)",
    line=dict(color="#404040", width=3),
    name="Scafo Centurion",
    hoverinfo="skip"
))

# Linea centrale
fig.add_trace(go.Scatter(x=[0,0], y=[-16, 16], mode="lines", 
    line=dict(color="black", width=1, dash="dash"), hoverinfo="skip", showlegend=False))

# 2. PIVOT POINT
fig.add_trace(go.Scatter(
    x=[pp_pos[0]], y=[pp_pos[1]],
    mode='markers+text',
    marker=dict(symbol='circle-dot', size=18, color='black', line=dict(width=2, color='white')),
    text=["<b>PP</b>"], textposition="top center",
    name="Pivot Point",
    hoverinfo="x+y"
))

# 3. VETTORI MOTORI
scale = 0.4
def add_vector(fig, start, u, v, color, name, val_ton):
    end_x = start[0] + u * scale
    end_y = start[1] + v * scale
    fig.add_trace(go.Scatter(
        x=[start[0], end_x], y=[start[1], end_y],
        mode='lines',
        line=dict(color=color, width=6),
        name=name,
        hovertemplate=f"<b>{name}</b><br>Spinta: {val_ton:.1f} t<extra></extra>"
    ))
    fig.add_annotation(
        x=end_x, y=end_y,
        ax=start[0], ay=start[1],
        xref="x", yref="y", axref="x", ayref="y",
        showarrow=True, arrowhead=2, arrowsize=1.5, arrowwidth=2, arrowcolor=color
    )

add_vector(fig, pos_sx, u1, v1, "red", "Motore SX", ton1)
add_vector(fig, pos_dx, u2, v2, "green", "Motore DX", ton2)

# 4. RISULTANTE
add_vector(fig, origin_res, res_u, res_v, "blue", "RISULTANTE", res_ton)
fig.add_trace(go.Scatter(
    x=[origin_res[0]], y=[origin_res[1]],
    mode='markers', marker=dict(symbol='diamond', size=12, color='blue'),
    name="Punto Applicazione", hovertemplate=f"Logica: {logic_used}<extra></extra>"
))

# 5. VISUALIZZAZIONE MOMENTO
if abs(Total_Moment) > 10:
    color_rot = "purple"
    fig.add_annotation(
        x=0, y=26,
        text=f"ROTAZIONE: {'SINISTRA' if Total_Moment > 0 else 'DRITTA'}",
        showarrow=False,
        font=dict(size=16, color="white"),
        bgcolor=color_rot,
        bordercolor=color_rot,
        borderwidth=2,
        borderpad=4,
        opacity=0.9
    )

# --- LAYOUT ESTETICO ---
fig.update_layout(
    width=700, height=800,
    xaxis=dict(range=[-25, 25], showgrid=True, visible=False),
    yaxis=dict(range=[-30, 35], showgrid=True, visible=False, scaleanchor="x", scaleratio=1),
    plot_bgcolor='aliceblue',
    margin=dict(l=20, r=20, t=20, b=20),
    showlegend=True,
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
)

# --- VISUALIZZAZIONE PRINCIPALE ---
c_main = st.container()
with c_main:
    st.plotly_chart(fig, use_container_width=True)

# --- METRICHE ---
st.write("### 📊 Dati Real-Time")
m1, m2, m3 = st.columns(3)
deg_res = np.degrees(np.arctan2(res_u, res_v))
if deg_res < 0: deg_res += 360

m1.metric("Tiro Totale", f"{res_ton:.1f} t", border=True)
m2.metric("Direzione", f"{deg_res:.0f}°", border=True)
m3.metric("Momento (Rotazione)", f"{abs(Total_Moment):.0f} kNm", 
          delta="SX" if Total_Moment > 0 else "DX", delta_color="normal", border=True)
