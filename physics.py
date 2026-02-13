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
        rad_l = math.radians(left_angle)
        rad_r = math.radians(right_angle)

        surge_l = left_thrust * math.cos(rad_l)
        sway_l  = left_thrust * math.sin(rad_l)
        
        surge_r = right_thrust * math.cos(rad_r)
        sway_r  = right_thrust * math.sin(rad_r)

        X_force_body = surge_l + surge_r
        Y_force_body = sway_l + sway_r

        # --- 2. CALCOLO MOMENTO ---
        m_l = (-POS_THRUSTERS_X * surge_l) - (POS_THRUSTERS_Y * sway_l)
        m_r = (POS_THRUSTERS_X * surge_r) - (POS_THRUSTERS_Y * sway_r)
        N_moment_total = m_l + m_r

        # --- 3. DAMPING (RESISTENZE) ---
        if u >= 0:
            damping_surge = QUADRATIC_DAMPING_SURGE_FORWARD
        else:
            damping_surge = QUADRATIC_DAMPING_SURGE_REVERSE

        F_damping_surge = -(damping_surge * u * abs(u))
        F_damping_sway  = -(QUADRATIC_DAMPING_SWAY * v * abs(v))
        N_damping_rot   = -(ANGULAR_DAMPING * r * abs(r))
        
        N_induced = (pp_x * F_damping_surge) - (pp_y * F_damping_sway)
        
        # --- 4. INTEGRAZIONE (BODY FRAME) ---
        X_tot = X_force_body + F_damping_surge
        Y_tot = Y_force_body + F_damping_sway
        N_tot = N_moment_total + N_damping_rot + N_induced
        
        # Equazioni del moto con termini di Coriolis/centripeti
        u_dot = (X_tot / SHIP_MASS) + (r * v)
        v_dot = (Y_tot / SHIP_MASS) - (r * u)
        r_dot = N_tot / MOMENT_OF_INERTIA
        
        self.state[3] += u_dot * dt
        self.state[4] += v_dot * dt
        self.state[5] += r_dot * dt

        if abs(X_force_body) < 0.1 and abs(self.state[3]) < 0.01: self.state[3] = 0
        if abs(Y_force_body) < 0.1 and abs(self.state[4]) < 0.01: self.state[4] = 0
        if abs(N_moment_total) < 1000 and abs(self.state[5]) < 0.001: self.state[5] = 0


        # --- 5. CONVERSIONE IN WORLD FRAME (PER MOVIMENTO) ---
        psi = self.state[2]
        u_body, v_body = self.state[3], self.state[4]
        c, s = math.cos(psi), math.sin(psi)
        
        x_dot_world = u_body * c - v_body * s
        y_dot_world = u_body * s + v_body * c
        
        self.state[0] += x_dot_world * dt
        self.state[1] += y_dot_world * dt
        self.state[2] += self.state[5] * dt
        self.state[2] = self.normalize_angle(self.state[2])
