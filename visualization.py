import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import PathPatch
from matplotlib.path import Path
import matplotlib.transforms as mtransforms

def get_hull_path():
    hw, stern, bow_tip, shoulder = 5.85, -16.25, 16.25, 8.0
    return [
        (Path.MOVETO, (-hw, stern)), (Path.LINETO, (hw, stern)), (Path.LINETO, (hw, shoulder)),
        (Path.CURVE4, (hw, 14.0)), (Path.CURVE4, (4.0, bow_tip)), (Path.CURVE4, (0, bow_tip)),    
        (Path.CURVE4, (-4.0, bow_tip)), (Path.CURVE4, (-hw, 14.0)), (Path.CURVE4, (-hw, shoulder)), 
        (Path.LINETO, (-hw, stern)), (Path.CLOSEPOLY, (-hw, stern))
    ]

def draw_static_hull(ax):
    path_data = get_hull_path()
    codes, verts = zip(*path_data)
    ax.add_patch(PathPatch(Path(verts, codes), facecolor='#cccccc', edgecolor='#555555', lw=2, zorder=2))
    
    # Fender
    hw, bow_tip, shoulder = 5.85, 16.25, 8.0
    fender_data = [(Path.MOVETO, (hw, shoulder)), (Path.CURVE4, (hw, 14.0)), (Path.CURVE4, (4.0, bow_tip)), (Path.CURVE4, (0, bow_tip)), (Path.CURVE4, (-4.0, bow_tip)), (Path.CURVE4, (-hw, 14.0)), (Path.CURVE4, (-hw, shoulder))]
    f_codes, f_verts = zip(*fender_data)
    ax.add_patch(PathPatch(Path(f_verts, f_codes), facecolor='none', edgecolor='#333333', lw=8, capstyle='round', zorder=2.5))

def draw_azimuth_circles(ax, pos_sx, pos_dx):
    ax.add_patch(plt.Circle(pos_sx, 2.0, color='black', fill=False, lw=1, ls='--', alpha=0.4, zorder=4))
    ax.add_patch(plt.Circle(pos_dx, 2.0, color='black', fill=False, lw=1, ls='--', alpha=0.4, zorder=4))

def draw_prediction_path(ax, trajectory):
    path_data = get_hull_path()
    codes, verts = zip(*path_data)
    hull_base_path = Path(verts, codes)
    
    for i, (dx, dy, d_angle_deg) in enumerate(trajectory):
        if i == 0: continue
        alpha_val = max(0.04, 0.20 - (i * 0.008))
        # Rotazione corretta (positiva = antioraria)
        tr = mtransforms.Affine2D().rotate_deg(d_angle_deg).translate(dx, dy) + ax.transData
        patch = PathPatch(hull_base_path, facecolor='none', edgecolor='blue', lw=0.8, alpha=alpha_val, zorder=1, transform=tr)
        ax.add_patch(patch)

def draw_wash(ax, pos, angle_deg, power_pct):
    if power_pct < 5: return
    angle_wash_rad = np.radians(angle_deg + 180)
    length = (power_pct / 100) * 22.0 
    w_start, w_end = 2.2, 7.5
    d_vec = np.array([np.sin(angle_wash_rad), np.cos(angle_wash_rad)])
    p_vec = np.array([-d_vec[1], d_vec[0]])
    p1, p2 = pos + p_vec*(w_start/2), pos - p_vec*(w_start/2)
    p3, p4 = pos + (d_vec*length) - p_vec*(w_end/2), pos + (d_vec*length) + p_vec*(w_end/2)
    ax.add_patch(plt.Polygon([p1, p2, p3, p4], facecolor='#00f2ff', alpha=0.25, edgecolor='none', zorder=3))

def draw_propeller(ax, pos, angle_deg, color='black', scale=1.0, is_polar=False):
    angle_rad = np.radians(angle_deg + 90)
    t = np.linspace(0, 2 * np.pi, 60)
    a = 1.6 * scale
    x_base, y_base = (a * np.sin(t) * np.cos(t)) * 0.7, a * np.sin(t)
    c, s = np.cos(-angle_rad), np.sin(-angle_rad)
    x_rot, y_rot = x_base * c - y_base * s, x_base * s + y_base * c
    if is_polar:
        ax.plot(np.arctan2(x_rot, y_rot), np.sqrt(x_rot**2 + y_rot**2), color=color, lw=1.5, zorder=3, alpha=0.5)
    else:
        ax.plot(pos[0] + x_rot, pos[1] + y_rot, color=color, lw=2, zorder=10, alpha=0.8)

def plot_clock(azimuth_deg, color):
    fig, ax = plt.subplots(figsize=(2.2, 2.2), subplot_kw={'projection': 'polar'})
    ax.set_theta_zero_location('N'); ax.set_theta_direction(-1)
    ax.set_yticks([]); ax.set_xticks(np.radians([0, 90, 180, 270]))
    draw_propeller(ax, [0,0], azimuth_deg, color=color, scale=0.15, is_polar=True)
    rad = np.radians(azimuth_deg)
    ax.fill([rad, rad+0.4, rad-0.4, rad], [0.98, 0.15, 0.15, 0.98], color=color, alpha=0.9, zorder=4)
    ax.grid(True, alpha=0.3); fig.patch.set_alpha(0)
    return fig
