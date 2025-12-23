import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import PathPatch
from matplotlib.path import Path

def draw_wash(ax, pos, angle_deg, power_pct):
    if power_pct < 5: return
    angle_wash_rad = np.radians(angle_deg + 180)
    length = (power_pct / 100) * 22.0 
    w_start = 2.2
    w_end = 7.5
    d_vec = np.array([np.sin(angle_wash_rad), np.cos(angle_wash_rad)])
    p_vec = np.array([-d_vec[1], d_vec[0]])
    p1 = pos + p_vec * (w_start / 2)
    p2 = pos - p_vec * (w_start / 2)
    p3 = pos + (d_vec * length) - p_vec * (w_end / 2)
    p4 = pos + (d_vec * length) + p_vec * (w_end / 2)
    verts = [p1, p2, p3, p4]
    ax.add_patch(plt.Polygon(verts, facecolor='#00f2ff', alpha=0.25, edgecolor='none', zorder=1.2))

def draw_propeller(ax, pos, angle_deg, color='black', scale=1.0, is_polar=False):
    angle_rad = np.radians(angle_deg + 90)
    t = np.linspace(0, 2 * np.pi, 60)
    a = 1.6 * scale
    x_base = (a * np.sin(t) * np.cos(t)) * 0.7
    y_base = a * np.sin(t)
    c, s = np.cos(-angle_rad), np.sin(-angle_rad)
    x_rot = x_base * c - y_base * s
    y_rot = x_base * s + y_base * c
    if is_polar:
        theta = np.arctan2(x_rot, y_rot)
        r = np.sqrt(x_rot**2 + y_rot**2)
        ax.plot(theta, r, color=color, lw=1.5, zorder=3, alpha=0.5)
    else:
        ax.plot(pos[0] + x_rot, pos[1] + y_rot, color=color, lw=2, zorder=5, alpha=0.8)

def plot_clock(azimuth_deg, color):
    fig, ax = plt.subplots(figsize=(3, 3), subplot_kw={'projection': 'polar'})
    ax.set_theta_zero_location('N')
    ax.set_theta_direction(-1)
    ax.set_yticks([]); ax.set_xticks(np.radians([0, 90, 180, 270]))
    draw_propeller(ax, [0,0], azimuth_deg, color=color, scale=0.15, is_polar=True)
    rad = np.radians(azimuth_deg)
    inner_r, outer_r, half_width = 0.15, 0.98, 0.4
    t_verts = [rad, rad + half_width, rad - half_width, rad]
    r_verts = [outer_r, inner_r, inner_r, outer_r]
    ax.fill(t_verts, r_verts, color=color, alpha=0.9, zorder=4, edgecolor='black', lw=0.5)
    ax.plot([rad, rad], [inner_r, outer_r], color='white', lw=1.2, alpha=0.7, zorder=5)
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
    ax.add_patch(plt.Circle(pos_sx, 2.0, color='black', fill=False, lw=1, ls='--', alpha=0.2, zorder=2))
    ax.add_patch(plt.Circle(pos_dx, 2.0, color='black', fill=False, lw=1, ls='--', alpha=0.2, zorder=2))
