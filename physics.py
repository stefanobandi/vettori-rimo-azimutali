import numpy as np
import math
from constants import *

class PhysicsEngine:
    def __init__(self):
        self.reset()

    def reset(self):
        # Stato: [x, y, psi, u, v, r]
        # x, y: Posizione nel mondo
        # psi: Heading (pi/2 = 90° = Nord visivo)
        # u: Velocità Longitudinale (Surge, + = Avanti)
        # v: Velocità Trasversale (Sway, + = Dritta)
        # r: Velocità Rotazione (Yaw rate)
        self.state = np.zeros(6)
        self.state[2] = math.pi / 2 
        self.current_pp_y = DEFAULT_PP_Y 
        self.pivot_mode = "MANUAL" 

    def normalize_angle(self, angle):
        return angle % (2 * math.pi)

    def calculate_dynamic_pivot(self, left_thrust, left_angle_deg, right_thrust, right_angle_deg):
        return DEFAULT_PP_Y

    def update(self, dt, left_thrust, left_angle, right_thrust, right_angle, pp_x, pp_y):
        self.current_pp_y = pp_y 
        
        u = self.state[3] # Surge (Avanti)
        v = self.state[4] # Sway (Dritta)
        r = self.state[5] # Yaw Rate

        # --- 1. CALCOLO FORZE NEL SISTEMA NAVE (BODY FRAME) ---
        # Azimuth 0° = Prua (Surge +)
        # Azimuth 90° = Dritta (Sway +)
        # Formule:
        # F_surge = T * cos(angle)
        # F_sway  = T * sin(angle)
        
        rad_l = math.radians(left_angle)
        rad_r = math.radians(right_angle)

        # Motore SX
        surge_l = left_thrust * math.cos(rad_l)
        sway_l  = left_thrust * math.sin(rad_l)
        
        # Motore DX
        surge_r = right_thrust * math.cos(rad_r)
        sway_r  = right_thrust * math.sin(rad_r)

        # Totali Forza Scafo
        X_force_body = surge_l + surge_r # Totale Avanti/Indietro
        Y_force_body = sway_l + sway_r   # Totale Laterale

        # --- 2. CALCOLO MOMENTO ---
        # Coordinate motori rispetto al centro (0,0)
        # SX: x = -2.7, y = -12.0
        # DX: x = +2.7, y = -12.0
        # Momento = x * F_surge - y * F_sway (Attenzione ai segni cartesiani nave)
        # In sistema nave standard: x è avanti, y è dritta? 
        # Noi usiamo: Y_geom è longitudinale, X_geom è laterale.
        # Braccio X (Laterale) * Forza Y (Longitudinale) - Braccio Y (Longitudinale) * Forza X (Laterale)
        
        # Momento SX
        # Posizione SX: (-POS_THRUSTERS_X, POS_THRUSTERS_Y) -> (-2.7, -12.0)
        # F_long = surge_l, F_lat = sway_l
        # Cross product 2D: r_x * F_y - r_y * F_x (dove qui x=lat, y=long)
        # M = pos_x * Surge - pos_y * Sway
        m_l = (-POS_THRUSTERS_X * surge_l) - (POS_THRUSTERS_Y * sway_l)
        
        # Momento DX
        m_r = (POS_THRUSTERS_X * surge_r) - (POS_THRUSTERS_Y * sway_r)
        
        N_moment_total = m_l + m_r

        # --- 3. DAMPING (RESISTENZE) ---
        # Calcolate sulle velocità locali relative al Pivot Point
        # u_p = u - r * dist_y
        # v_p = v + r * dist_x
        # PP Coordinates relative to CG (0,0)
        
        u_at_pivot = u - (r * pp_y)
        v_at_pivot = v + (r * pp_x)
        
        F_damping_surge = -(QUADRATIC_DAMPING_SURGE * u_at_pivot * abs(u_at_pivot))
        F_damping_sway  = -(QUADRATIC_DAMPING_SWAY * v_at_pivot * abs(v_at_pivot))
        N_damping_rot   = -(ANGULAR_DAMPING * r)
        
        # Momento indotto dalla resistenza laterale applicata nel PP
        # M_induced = pp_x * F_damp_surge - pp_y * F_damp_sway
        N_induced = (pp_x * F_damping_surge) - (pp_y * F_damping_sway)
        
        # --- 4. INTEGRAZIONE (BODY FRAME) ---
        X_tot = X_force_body + F_damping_surge
        Y_tot = Y_force_body + F_damping_sway
        N_tot = N_moment_total + N_damping_rot + N_induced
        
        u_dot = X_tot / SHIP_MASS
        v_dot = Y_tot / SHIP_MASS
        r_dot = N_tot / MOMENT_OF_INERTIA
        
        self.state[3] += u_dot * dt
        self.state[4] += v_dot * dt
        self.state[5] += r_dot * dt

        # Smorzamento attrito statico
        if abs(self.state[3]) < 0.001: self.state[3] = 0
        if abs(self.state[4]) < 0.001: self.state[4] = 0
        if abs(self.state[5]) < 0.0001: self.state[5] = 0

        # --- 5. CONVERSIONE IN WORLD FRAME (PER MOVIMENTO) ---
        # psi è l'heading rispetto all'asse X matematico (Est).
        # Se psi = 90 (Nord):
        # Surge (u) deve andare a Nord (+Y world)
        # Sway (v) deve andare a Est (+X world)
        
        psi = self.state[2]
        c = math.cos(psi)
        s = math.sin(psi)
        
        # Matrice di rotazione:
        # x_dot = u * cos(psi) + v * cos(psi - 90)  [v è a destra di u]
        #       = u * cos(psi) + v * sin(psi)
        # y_dot = u * sin(psi) + v * sin(psi - 90)
        #       = u * sin(psi) - v * cos(psi)
        
        x_dot_world = u * c + v * s
        y_dot_world = u * s - v * c
        
        self.state[0] += x_dot_world * dt
        self.state[1] += y_dot_world * dt
        self.state[2] += self.state[5] * dt # Aggiorna Heading
        self.state[2] = self.normalize_angle(self.state[2])
