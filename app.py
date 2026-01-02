import streamlit as st
import time
import pandas as pd
import physics
import visualization

# --- CONFIGURAZIONE PAGINA ---
st.set_page_config(
    page_title="Simulatore Rimorchiatore Azimuthale",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- INIZIALIZZAZIONE SESSION STATE ---
# Inizializziamo tutte le variabili di stato necessarie per la simulazione
if 'x' not in st.session_state:
    st.session_state.x = 0.0
if 'y' not in st.session_state:
    st.session_state.y = 0.0
if 'heading' not in st.session_state:
    st.session_state.heading = 0.0
if 'az_l' not in st.session_state:
    st.session_state.az_l = 0
if 'pwr_l' not in st.session_state:
    st.session_state.pwr_l = 0
if 'az_r' not in st.session_state:
    st.session_state.az_r = 0
if 'pwr_r' not in st.session_state:
    st.session_state.pwr_r = 0
if 'pivot_mode' not in st.session_state:
    st.session_state.pivot_mode = "Standard"
if 'history' not in st.session_state:
    st.session_state.history = []

# --- FUNZIONI DI CALLBACK E LOGICA ---

def reset_simulation():
    """Resetta completamente lo stato della simulazione."""
    st.session_state.x = 0.0
    st.session_state.y = 0.0
    st.session_state.heading = 0.0
    st.session_state.az_l = 0
    st.session_state.pwr_l = 0
    st.session_state.az_r = 0
    st.session_state.pwr_r = 0
    st.session_state.history = []
    st.session_state.pivot_mode = "N/A"

def update_manual_inputs():
    """Callback per aggiornare lo stato quando si usano gli slider manuali."""
    # Le variabili sono già legate agli slider tramite 'key', 
    # questa funzione serve se vogliamo logiche aggiuntive al cambio valore.
    pass

def apply_fast_side_step(direction):
    """
    Imposta i motori per una traslazione laterale (Crabbing).
    Configurazione: Motori a 90° o 270°, Potenza alta.
    """
    power = 75
    if direction == "SINISTRA":
        # Spinta verso sinistra: Azimuth deve spingere verso dritta (o viceversa in base alla convenzione)
        # Assumendo 0=Nord, 90=Est. Per andare a Ovest (270), spingiamo verso 270.
        st.session_state.az_l = 270
        st.session_state.az_r = 270
    elif direction == "DESTRA":
        # Spinta verso Est
        st.session_state.az_l = 90
        st.session_state.az_r = 90
    
    st.session_state.pwr_l = power
    st.session_state.pwr_r = power

def apply_rotation(direction):
    """
    Imposta i motori per una rotazione pura sul posto (Pure Spin).
    Configurazione: Motori contrapposti (0° vs 180°).
    """
    power = 60
    if direction == "ORARIO":
        # Motore SX avanti (0°), Motore DX indietro (180°) -> Coppia oraria
        st.session_state.az_l = 0
        st.session_state.az_r = 180
    elif direction == "ANTIORARIO":
        # Motore SX indietro (180°), Motore DX avanti (0°) -> Coppia antioraria
        st.session_state.az_l = 180
        st.session_state.az_r = 0
        
    st.session_state.pwr_l = power
    st.session_state.pwr_r = power

def apply_forward():
    """Imposta i motori per avanzamento rettilineo standard."""
    st.session_state.az_l = 0
    st.session_state.az_r = 0
    st.session_state.pwr_l = 50
    st.session_state.pwr_r = 50

def apply_combined_maneuver():
    """Esempio di manovra complessa: avanzamento con virata (15°/15°)."""
    st.session_state.az_l = 15
    st.session_state.az_r = 15
    st.session_state.pwr_l = 75
    st.session_state.pwr_r = 75

# --- INTERFACCIA UTENTE: SIDEBAR ---

with st.sidebar:
    st.header("🎛️ Pannello di Controllo")
    
    st.markdown("### Propulsore Sinistro (Port)")
    col_l1, col_l2 = st.columns(2)
    with col_l1:
        st.metric("Azimuth SX", f"{st.session_state.az_l}°")
    with col_l2:
        st.metric("Potenza SX", f"{st.session_state.pwr_l}%")
        
    st.slider("Orientamento SX", 0, 360, key="az_l", on_change=update_manual_inputs)
    st.slider("Manetta SX", 0, 100, key="pwr_l", on_change=update_manual_inputs)
    
    st.markdown("---")
    
    st.markdown("### Propulsore Destro (Starboard)")
    col_r1, col_r2 = st.columns(2)
    with col_r1:
        st.metric("Azimuth DX", f"{st.session_state.az_r}°")
    with col_r2:
        st.metric("Potenza DX", f"{st.session_state.pwr_r}%")
        
    st.slider("Orientamento DX", 0, 360, key="az_r", on_change=update_manual_inputs)
    st.slider("Manetta DX", 0, 100, key="pwr_r", on_change=update_manual_inputs)
    
    st.markdown("---")
    st.button("🔴 RESET TO ZERO", on_click=reset_simulation, use_container_width=True, type="primary")

# --- CALCOLO FISICO (LOOP) ---

# Parametri temporali
dt = 0.1 

# Eseguiamo il calcolo fisico con il modulo aggiornato
new_x, new_y, new_h = physics.calculate_new_position(
    st.session_state.x, 
    st.session_state.y, 
    st.session_state.heading, 
    st.session_state.az_l, 
    st.session_state.pwr_l, 
    st.session_state.az_r, 
    st.session_state.pwr_r,
    dt=dt
)

# Determina la modalità pivot per visualizzazione (Logica UI)
# Replichiamo la logica di physics.py solo per dare feedback all'utente
angle_diff = abs(st.session_state.az_l - st.session_state.az_r)
if angle_diff > 180: angle_diff = 360 - angle_diff

pivot_display = "⚓ Skeg (Poppa)"
pivot_color = "blue"

if 160 <= angle_diff <= 200:
    pivot_display = "⚙️ Centro Propulsori (Spin)"
    pivot_color = "orange"

# Aggiornamento stato
st.session_state.x = new_x
st.session_state.y = new_y
st.session_state.heading = new_h
st.session_state.pivot_mode = pivot_display

# Aggiornamento storico (limitato agli ultimi 100 punti per performance)
st.session_state.history.append({'x': new_x, 'y': new_y})
if len(st.session_state.history) > 1000:
    st.session_state.history.pop(0)

# --- INTERFACCIA UTENTE: MAIN AREA ---

st.title("🚢 Simulatore ASD Tug")

# Tab per organizzare la vista
tab1, tab2 = st.tabs(["Visualizzazione Grafica", "Dati Telemetrici"])

with tab1:
    # Riga per i comandi rapidi (Sopra al grafico per accesso veloce)
    st.subheader("Manovre Rapide (Preset)")
    
    c1, c2, c3, c4, c5 = st.columns(5)
    
    with c1:
        st.button("⬅️ Crab SX", on_click=apply_fast_side_step, args=("SINISTRA",), use_container_width=True)
    with c2:
        st.button("➡️ Crab DX", on_click=apply_fast_side_step, args=("DESTRA",), use_container_width=True)
    with c3:
        st.button("🔄 Spin SX", on_click=apply_rotation, args=("ANTIORARIO",), use_container_width=True)
    with c4:
        st.button("🔃 Spin DX", on_click=apply_rotation, args=("ORARIO",), use_container_width=True)
    with c5:
        st.button("⬆️ Avanti (15°)", on_click=apply_combined_maneuver, use_container_width=True)

    st.divider()

    # Area Grafico
    col_graph, col_info = st.columns([3, 1])
    
    with col_info:
        st.markdown(f"**Pivot Point Attivo:**")
        st.markdown(f":{pivot_color}[**{pivot_display}**]")
        st.markdown("---")
        st.markdown(f"**Heading:** {int(st.session_state.heading)}°")
        st.markdown(f"**Pos X:** {st.session_state.x:.1f}")
        st.markdown(f"**Pos Y:** {st.session_state.y:.1f}")

    with col_graph:
        # Chiamata al modulo di visualizzazione
        fig = visualization.draw_simulation(
            st.session_state.x, 
            st.session_state.y, 
            st.session_state.heading,
            st.session_state.az_l,
            st.session_state.az_r
        )
        st.plotly_chart(fig, use_container_width=True)
        
    st.caption("Il grafico mostra la posizione e l'orientamento del rimorchiatore. La freccia verde indica la prua.")

with tab2:
    st.subheader("Analisi Vettoriale")
    st.write("Dettaglio delle forze applicate e coordinate.")
    
    # Creiamo un piccolo dataframe per lo stato attuale
    data = {
        "Parametro": ["X", "Y", "Heading", "Azimuth SX", "Power SX", "Azimuth DX", "Power DX", "Pivot Mode"],
        "Valore": [
            f"{st.session_state.x:.2f}",
            f"{st.session_state.y:.2f}",
            f"{st.session_state.heading:.1f}°",
            f"{st.session_state.az_l}°",
            f"{st.session_state.pwr_l}%",
            f"{st.session_state.az_r}°",
            f"{st.session_state.pwr_r}%",
            st.session_state.pivot_mode
        ]
    }
    df = pd.DataFrame(data)
    st.dataframe(df, use_container_width=True)
    
    st.subheader("Note di Debug")
    st.text(f"Delta Time Simulation: {dt}s")
    st.text(f"Logic Engine: Physics v2 (Dynamic Pivot)")
