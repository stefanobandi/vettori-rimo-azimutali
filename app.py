import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import PathPatch, FancyArrowPatch
from matplotlib.path import Path
import pandas as pd

# --- CONFIGURAZIONE PAGINA ---
st.set_page_config(page_title="ASD Centurion V5.5", layout="wide")

# --- GESTIONE SESSION STATE ---
defaults = {
    "p1": 50.0, "a1": 0.0,    # Motore SX
    "p2": 50.0, "a2": 0.0,    # Motore DX
    "pp_x": 0.0, "pp_y": 5.42 # Pivot Point default
}

for key, val in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = val

# --- FUNZIONI DI CALLBACK ---
def update_from_slider(key):
    st.session_state[key] = st.session_state[f"{key}_slider"]

def update_from_input(key):
    st.session_state[key] = st.session_state[f"{key}_input"]

def reset_engines():
    st.session_state.p1 = 50.0
    st.session_state.a1 = 0.0
    st.session_state.p2 = 50.0
    st.session_state.a2 = 0.0
    # Update manuale per sicurezza UI
    if 'p1_slider' in st.session_state: st.session_state.p1_slider = 50.0
    if 'p1_input' in st.session_state: st.session_state.p1_input = 50.0
    if 'p2_slider' in st.session_state: st.session_state.p2_slider = 50.0
    if 'p2_input' in st.session_state: st.session_state.p2_input = 50.0

def reset_pivot():
    st.session_state.pp_x = 0.0
    st.session_state.pp_y = 5.42
    if 'pp_x_slider' in st.session_state: st.session_state.pp_x_slider = 0.0
    if 'pp_x_input' in st.session_state: st.session_state.pp_x_input = 0.0
    if 'pp_y_slider' in st.session_state: st.session_state.pp_y_slider = 5.42
    if 'pp_y_input' in st.session_state: st.session_state.pp_y_input = 5.42

# --- WIDGET CUSTOM (Slider + Input Numerico) ---
def render_control(label, key, min_val, max_val, step=1.0):
    c1, c2 = st.columns([3, 1])
    with c1:
        st.slider(
            label, 
            min_value=float(min_val), 
            max_value=float(max_val), 
            step=step,
            key=f"{key}_slider", 
            value=float(st.session_state[key]),
            on_change=update_from_slider,
            args=(key,)
        )
    with c2:
        st.number_input(
            "Valore", 
            min_value=float(min_val), 
            max_value=float(max_val), 
            step=step,
            key=f"{key}_input", 
            value=float(st.session_state[key]),
            on_change=update_from_input,
            args=(key,),
            label_visibility="hidden"
        )

# --- SIDEBAR ---
with st.sidebar:
    st.header("⚙️ Controlli Sistema")
    
    st.subheader("Reset")
    c_res1, c_res2 = st.columns(2)
    with c_res1:
        st.button("M. Motori", on_click=reset_engines, type="primary", use_container_width=True)
    with c_res2:
        st.button("P. Pivot", on_click=reset_pivot, use_container_width=True)
    
    st.divider()
    st.markdown("### Manovre Rapide")
    if st.button("Avanti Tutta", use_container_width=True):
        st.session_state.p1 = 80.0; st.session_state.a1 = 0.0
        st.session_state.p
