# visualization.py
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import PathPatch
from matplotlib.path import Path

def draw_propeller(ax, pos, angle_deg, color='black', scale=1.0, is_polar=False):
    """Disegna un'elica stilizzata (forma a 8) perpendicolare al vettore."""
    # L'elica deve essere perpendicolare alla spinta, quindi aggiungiamo 90 gradi
    angle_rad = np.radians(angle_deg + 90)
    t = np.linspace(0, 2 * np.pi, 60)
    
    # Forma base a 8
    a = 1.6 * scale
    x_base = (a * np.sin(t) * np.cos(t)) * 0.7
    y_base = a * np.sin(t)
    
    # Rotazione
    c, s = np.cos(-angle_rad), np.sin(-angle_rad)
    x_rot = x_base * c - y_base * s
    y_rot = x_base * s + y_base * c
    
    if is_polar:
        # Conversione in coordinate polari per il plot dell'orologio
        theta = np.arctan2(x_rot, y_rot)
        r = np.sqrt(x_rot**2 + y_rot**2)
        ax.plot(theta, r, color=color, lw=2, zorder=5, alpha=0.8)
    else:
        # Coordinate Cartesiane per il grafico principale
        ax.plot(pos[0] + x_rot, pos[1] + y_rot, color=color, lw=2, zorder=5, alpha=0.8)

def plot_clock(azimuth_deg, color):
    fig, ax = plt.subplots(figsize=(3, 3), subplot_kw={'projection': 'polar'})
    ax.set_theta_zero_location('N')
    ax.set_theta_direction(-1)
    ax.set_yticks([]); ax.set_xticks(np.radians([0, 90, 180, 270]))
    
    # 1. Disegna l'elica al centro dell'orologio (scalata piccola)
    draw_propeller(ax, [0,0], azimuth_deg, color=color, scale=0.15, is_polar=True)
    
    # 2. Disegna il triangolo invertito (base larga al centro, punta all'esterno)
    rad = np.radians(azimuth_deg)
    width = 0.35 # Larghezza della base in radianti
    t_verts = [rad, rad + width, rad - width, rad]
    r_verts = [0.9, 0, 0, 0.9]
    ax.fill(t_verts, r_verts, color=color, alpha=0.6, zorder=4)
    
    ax.grid(True, alpha=0.3)
    fig.patch.set_alpha(0)
    return fig

def draw_static_elements(ax, pos_sx, pos_dx):
    hw, stern, bow_tip, shoulder = 5.85, -16.25, 16.25, 8.0
    path_data = [
        (Path.MOVETO, (-hw, stern)), (Path.LINETO, (hw, stern)), (Path.LINETO, (hw, shoulder)),
        (Path.CURVE4, (hw, 14.0)), (Path.CURVE4, (4.0, bow_tip)), (Path.CURVE4, (0, bow_tip)),    
        (Path.CURVE4, (-4.0, bow_tip)), (Path.CURVE4, (-hw, 14.0)), (Path.CURVE4, (-hw, shoulder)), 
        (Path.LINETO, (-hw, stern)), (Path.CLOSEPOLY, (-hw, stern))
    ]
    codes, verts = zip(*path_data)
    ax.add_patch(PathPatch(Path(verts, codes), facecolor='#cccccc', edgecolor='#555555', lw=2, zorder=1))
    fender_data = [(Path.MOVETO, (hw, shoulder)), (Path.CURVE4, (hw, 14.0)), (Path.CURVE4, (4.0, bow_tip)), (Path.CURVE4, (0, bow_tip)), (Path.CURVE4, (-4.0, bow_tip)), (Path.CURVE4, (-hw, 14.0)), (Path.CURVE4, (-hw, shoulder))]
    f_codes, f_verts = zip(*fender_data)
    ax.add_patch(PathPatch(Path(f_verts, f_codes), facecolor='none', edgecolor='#333333', lw=8, capstyle='round', zorder=2))
    # Cerchi base motori
    ax.add_patch(plt.Circle(pos_sx, 2.0, color='black', fill=False, lw=1, ls='--', alpha=0.3, zorder=2))
    ax.add_patch(plt.Circle(pos_dx, 2.0, color='black', fill=False, lw=1, ls='--', alpha=0.3, zorder=2))
