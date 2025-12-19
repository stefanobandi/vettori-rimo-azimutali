# visualization.py
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import PathPatch
from matplotlib.path import Path

def plot_clock(azimuth_deg, color):
    fig, ax = plt.subplots(figsize=(3, 3), subplot_kw={'projection': 'polar'})
    ax.set_theta_zero_location('N')
    ax.set_theta_direction(-1)
    ax.set_yticks([]); ax.set_xticks(np.radians([0, 90, 180, 270]))
    ax.arrow(np.radians(azimuth_deg), 0, 0, 0.9, color=color, width=0.15, head_width=0, length_includes_head=True)
    ax.grid(True, alpha=0.3)
    fig.patch.set_alpha(0)
    return fig

def draw_propeller(ax, pos, angle_deg, color='black'):
    """Disegna un'elica stilizzata (forma a 8) ruotata secondo l'azimut."""
    angle_rad = np.radians(angle_deg)
    t = np.linspace(0, 2 * np.pi, 60)
    
    # Parametri per la forma a 8 (lemniscata stilizzata)
    a = 1.6 
    x_base = (a * np.sin(t) * np.cos(t)) * 0.7
    y_base = a * np.sin(t)
    
    # Rotazione (0° è prua/alto, rotazione oraria)
    c, s = np.cos(-angle_rad), np.sin(-angle_rad)
    x_rot = x_base * c - y_base * s
    y_rot = x_base * s + y_base * c
    
    ax.plot(pos[0] + x_rot, pos[1] + y_rot, color=color, lw=2, zorder=5, alpha=0.8)

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
