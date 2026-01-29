import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Polygon, PathPatch, FancyArrowPatch, Circle
from matplotlib.path import Path
from constants import L_SHIP, B_SHIP

def draw_hull(ax, color='white'): # MODIFICATO: Default white
    # Coordinate Scafo ASD
    # Prua verso l'alto (Y positivo) nel sistema locale nave
    hw = B_SHIP / 2.0  # Half Width
    l = L_SHIP        # Length
    
    # Punti chiave (x, y) - Origine a mezza nave
    bow = 16.25
    stern = -16.25
    shoulder = 10.0
    
    path_data = [
        (Path.MOVETO, (0, bow)),          # Punta prua
        (Path.CURVE4, (hw, shoulder)),    # Curva spalla dritta
        (Path.CURVE4, (hw, stern)),       # Fianco dritto fino a poppa
        (Path.LINETO, (hw, stern)),       # Angolo poppa dritta
        (Path.LINETO, (-hw, stern)),      # Specchio di poppa
        (Path.LINETO, (-hw, stern)),      # Angolo poppa sinistra
        (Path.CURVE4, (-hw, shoulder)),   # Fianco sinistro
        (Path.CURVE4, (0, bow)),          # Chiusura a prua
        (Path.CLOSEPOLY, (0, bow))
    ]
    
    codes, verts = zip(*path_data)
    path = Path(verts, codes)
    
    # Scafo solido
    patch = PathPatch(path, facecolor=color, edgecolor='black', lw=2, zorder=5)
    ax.add_patch(patch)
    
    # Dettaglio Fender (Prua)
    fender_y = np.linspace(shoulder, bow, 20)
    # Semplice arco per il fender
    ax.plot([-hw]*len(fender_y), fender_y, 'k-', lw=3, zorder=6) # Fender SX semplificato
    ax.plot([hw]*len(fender_y), fender_y, 'k-', lw=3, zorder=6)  # Fender DX semplificato
    
    # Skeg (Poppa)
    ax.plot([0, 0], [stern, stern + 5], 'k-', lw=2, zorder=6) # Linea centrale skeg

def render_radar_view(state, history, p1, a1, p2, a2, zoom_radius=80):
    # Setup Plot
    fig, ax = plt.subplots(figsize=(10, 10))
    ax.set_aspect('equal')
    
    # Sfondo Mare
    ax.set_facecolor('#B0C4DE') # LightSteelBlue
    
    # Limiti visuale (Zoom dinamico)
    ax.set_xlim(-zoom_radius, zoom_radius)
    ax.set_ylim(-zoom_radius, zoom_radius)
    
    # --- 1. DISEGNO GRIGLIA INFINITA (Moving Grid) ---
    # La nave è ferma al centro (0,0). La griglia si muove opposta alla nave.
    # State contiene posizione assoluta (x, y) e heading (psi)
    ship_x, ship_y, psi = state[3], state[4], state[5]
    
    # Creiamo una griglia di punti nel mondo assoluto
    grid_spacing = 40 # metri
    
    # Calcoliamo offset visivo
    # Vogliamo vedere i punti attorno alla nave, quindi (ship_x // spacing)
    start_x = (ship_x // grid_spacing) * grid_spacing - zoom_radius * 2
    end_x = start_x + zoom_radius * 4
    start_y = (ship_y // grid_spacing) * grid_spacing - zoom_radius * 2
    end_y = start_y + zoom_radius * 4
    
    x_points = np.arange(start_x, end_x, grid_spacing)
    y_points = np.arange(start_y, end_y, grid_spacing)
    XX, YY = np.meshgrid(x_points, y_points)
    
    # Trasformiamo i punti della griglia nel sistema di riferimento locale della nave
    # X_local = (X_world - X_ship) * cos(psi) + (Y_world - Y_ship) * sin(psi)
    # Y_local = -(X_world - X_ship) * sin(psi) + (Y_world - Y_ship) * cos(psi)
    
    dX = XX - ship_x
    dY = YY - ship_y
    
    local_X = dX * np.cos(psi) + dY * np.sin(psi)
    local_Y = -dX * np.sin(psi) + dY * np.cos(psi)
    
    # Disegna Griglia (Punti Neri)
    ax.scatter(local_X, local_Y, c='black', s=10, alpha=0.3, zorder=1)
    
    # --- 2. SCIA (HISTORY) ---
    if len(history) > 1:
        hist_arr = np.array(history)
        h_x = hist_arr[:, 0]
        h_y = hist_arr[:, 1]
        
        # Trasforma anche la scia in coordinate locali attuali
        dh_x = h_x - ship_x
        dh_y = h_y - ship_y
        
        hist_loc_x = dh_x * np.cos(psi) + dh_y * np.sin(psi)
        hist_loc_y = -dh_x * np.sin(psi) + dh_y * np.cos(psi)
        
        ax.plot(hist_loc_x, hist_loc_y, 'r-', lw=1.5, alpha=0.6, zorder=2)

    # --- 3. DISEGNO NAVE (Fissa al centro, prua Nord) ---
    draw_hull(ax, color='white') # Qui applicato il bianco
    
    # Thrusters Vectors
    # Posizioni relative dei motori (V7 Constants: Y=-12, X=+-2.7)
    tx_sx, ty_sx = -2.7, -12.0
    tx_dx, ty_dx = 2.7, -12.0
    
    # Calcolo vettori spinta (già nel sistema nave)
    # P1 (SX)
    t1 = (p1 / 100.0) * 15 # Lunghezza grafica
    rad1 = np.radians(a1)
    vx1 = t1 * np.sin(rad1)
    vy1 = t1 * np.cos(rad1)
    
    # P2 (DX)
    t2 = (p2 / 100.0) * 15
    rad2 = np.radians(a2)
    vx2 = t2 * np.sin(rad2)
    vy2 = t2 * np.cos(rad2)
    
    # Frecce NERE (Contrasto alto)
    if p1 > 0:
        ax.arrow(tx_sx, ty_sx, vx1, vy1, head_width=2, color='black', width=0.5, zorder=10)
    if p2 > 0:
        ax.arrow(tx_dx, ty_dx, vx2, vy2, head_width=2, color='black', width=0.5, zorder=10)
        
    # Risultante (Somma geometrica approssimata per visualizzazione)
    res_x = vx1 + vx2
    res_y = vy1 + vy2
    # Disegna risultante dal centro massa (approssimato a 0,0 per pulizia)
    if np.hypot(res_x, res_y) > 1:
        ax.arrow(0, 0, res_x, res_y, head_width=3, color='blue', alpha=0.5, width=0.8, zorder=9)

    # Rimuovi assi cartesiani per look "Radar"
    ax.axis('off')
    
    # Bussola Nord (Fissa in alto a destra rispetto al plot, ma indica il Nord vero)
    # Se la nave ruota verso DX (psi aumenta), il Nord relativo ruota verso SX
    # Visualizziamo un indicatore "N" che ruota attorno al centro
    north_dist = zoom_radius * 0.8
    n_loc_x = 0 * np.cos(psi) + north_dist * np.sin(psi) # Nord mondo è (0, Y)
    n_loc_y = -0 * np.sin(psi) + north_dist * np.cos(psi)
    
    ax.text(n_loc_x, n_loc_y, "N", color='black', fontsize=14, fontweight='bold', ha='center', va='center', zorder=20)
    # Freccetta verso il Nord
    ax.arrow(0, 0, n_loc_x*0.9, n_loc_y*0.9, color='black', alpha=0.1, zorder=0)

    return fig
