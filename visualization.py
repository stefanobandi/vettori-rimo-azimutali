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

def draw_static_elements(ax, pos_sx, pos_dx, rad1, rad2):
    # Scafo
    hw, stern, bow_tip, shoulder = 5.85, -16.25, 16.25, 8.0
    path_data = [
        (Path.MOVETO, (-hw, stern)), (Path.LINETO, (hw, stern)), (Path.LINETO, (hw, shoulder)),
        (Path.CURVE4, (hw, 14.0)), (Path.CURVE4, (4.0, bow_tip)), (Path.CURVE4, (0, bow_tip)),    
        (Path.CURVE4, (-4.0, bow_tip)), (Path.CURVE4, (-hw, 14.0)), (Path.CURVE4, (-hw, shoulder)), 
        (Path.LINETO, (-hw, stern)), (Path.CLOSEPOLY, (-hw, stern))
    ]
    codes, verts = zip(*path_data)
    ax.add_patch(PathPatch(Path(verts, codes), facecolor='#cccccc', edgecolor='#555555', lw=2, zorder=1))
    
    # Fender
    fender_data = [(Path.MOVETO, (hw, shoulder)), (Path.CURVE4, (hw, 14.0)), (Path.CURVE4, (4.0, bow_tip)), (Path.CURVE4, (0, bow_tip)), (Path.CURVE4, (-4.0, bow_tip)), (Path.CURVE4, (-hw, 14.0)), (Path.CURVE4, (-hw, shoulder))]
    f_codes, f_verts = zip(*fender_data)
    ax.add_patch(PathPatch(Path(f_verts, f_codes), facecolor='none', edgecolor='#333333', lw=8, capstyle='round', zorder=2))

    # Cerchi Azimutali (I "pezzi" che mancavano)
    ax.add_patch(plt.Circle(pos_sx, 2.0, color='black', fill=False, lw=1.5, ls='-', alpha=0.6, zorder=2))
    ax.add_patch(plt.Circle(pos_dx, 2.0, color='black', fill=False, lw=1.5, ls='-', alpha=0.6, zorder=2))

    # Suggerimento eliche
    ax.plot([pos_sx[0], pos_sx[0] + 2.0 * np.sin(rad1)], [pos_sx[1], pos_sx[1] + 2.0 * np.cos(rad1)], color='black', lw=2, zorder=3)
    ax.plot([pos_dx[0], pos_dx[0] + 2.0 * np.sin(rad2)], [pos_dx[1], pos_dx[1] + 2.0 * np.cos(rad2)], color='black', lw=2, zorder=3)
