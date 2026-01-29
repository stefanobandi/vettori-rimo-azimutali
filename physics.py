import numpy as np
import math
from constants import *

class PhysicsEngine:
    def __init__(self):
        self.reset()

    def reset(self):
        # Stato: [x, y, psi, u, v, r]
        # psi: Heading Math (0=Est, CCW+)
        self.state = np.zeros(6)
        self.state[2] = math.pi / 2 # Parte puntando a Nord (90° Math)
        self.current_pp_y = 0.0 
        self.pivot_mode = "INIT" 

    def normalize_angle(self, angle):
        return angle % (2 * math.pi)

    def calculate_dynamic_pivot(self, left_thrust, left_angle_deg, right_thrust, right_angle_deg):
        u = self.state[3]
        u_kn = u * 1.94384 
        
        # CASO 1: NAVIGAZIONE (V > 1 kn)
        if u_kn > 1.0:
            self.pivot_mode = "SKEG (AVANTI)"
            return POS_SKEG_Y 
        elif u_kn < -1.0:
            self.pivot_mode = "SKEG (INDIETRO)"
            return 3.0 
            
        # CASO 2: MANOVRA (V < 1 kn)
        else:
            self.pivot_mode = "FORCE LOGIC"
            
            rad_l = math.radians(left_angle_deg)
            rad_r = math.radians(right_angle_deg)
            
            fx_l = left_thrust * math.cos(rad_l)
            fy_l = left_thrust * math.sin(rad_l)
            fx_r = right_thrust * math.cos(rad_r)
            fy_r = right_thrust * math.sin(rad_r)
            
            sway_force_net = abs(fy_l + fy_r)
            twist_force_net = abs(fx_l - fx_r)
            
            total_force = sway_force_net + twist_force_net
            if total_force < 1000.0: return 2.0 
            
            ratio = sway_force_net / (total_force + 0.1)
            calculated_y = POS_STERN_Y + (POS_SKEG_Y - POS_STERN_Y) * ratio
            return calculated_y

    def update(self, dt, left_thrust, left_angle, right_thrust, right_angle):
        pp_y = self.calculate_dynamic_pivot(left_thrust, left_angle, right_thrust, right_angle)
        self.current_pp_y = pp_y 
        pp_x = 0.0 

        u = self.state[3]
        v = self.state[4]
        r = self.state[5]

        rad_l = math.radians(left_angle)
        rad_r = math.radians(right_angle)

        fx_l = left_thrust * math.cos(rad_l)
        fy_l = left_thrust * math.sin(rad_l)
        fx_r = right_thrust * math.cos(rad_r)
        fy_r = right_thrust * math.sin(rad_r)

        X_thrust = fx_l + fx_r
        Y_thrust = fy_l + fy_r

        # Momento (r x F) -> CCW+
        moment_l = (-POS_THRUSTERS_X * fy_l) - (POS_THRUSTERS_Y * fx_l)
        moment_r = (POS_THRUSTERS_X * fy_r) - (POS_THRUSTERS_Y * fx_r)
        N_thrust = moment_l + moment_r

        # Damping
        u_at_pivot = u - (r * pp_y)
        v_at_pivot = v + (r * pp_x)
        
        X_damping = -(LINEAR_DAMPING_SURGE * u_at_pivot)
        Y_damping = -(LINEAR_DAMPING_SWAY * v_at_pivot)
        N_damping_rot = -(ANGULAR_DAMPING * r)
        
        N_damping_induced = (pp_x * Y_damping) - (pp_y * X_damping)
        
        X_total = X_thrust + X_damping
        Y_total = Y_thrust + Y_damping
        N_total = N_thrust + N_damping_rot + N_damping_induced

        # Integrazione
        u_dot = X_total / SHIP_MASS
        v_dot = Y_total / SHIP_MASS
        r_dot = N_total / MOMENT_OF_INERTIA

        self.state[3] += u_dot * dt
        self.state[4] += v_dot * dt
        self.state[5] += r_dot * dt
        
        if abs(self.state[3]) < 0.001: self.state[3] = 0
        if abs(self.state[4]) < 0.001: self.state[4] = 0
        if abs(self.state[5]) < 0.0001: self.state[5] = 0

        psi = self.state[2]
        c = math.cos(psi)
        s = math.sin(psi)
        
        # Physics usa Math Angle (0=Est, CCW+)
        x_dot = self.state[3] * c - self.state[4] * s
        y_dot = self.state[3] * s + self.state[4] * c

        self.state[0] += x_dot * dt
        self.state[1] += y_dot * dt
        self.state[2] += self.state[5] * dt
        self.state[2] = self.normalize_angle(self.state[2])
