import numpy as np
import math
from constants import *

class PhysicsEngine:
    def __init__(self):
        self.reset()

    def reset(self):
        # Stato: [x, y, psi, u, v, r]
        # x, y: Mondo
        # psi: Heading Math (0=Est, CCW+)
        self.state = np.zeros(6)
        # Imposta heading iniziale a 90 gradi Math (Prua a Nord)
        self.state[2] = math.pi / 2 
        self.current_pp_y = 0.0 
        self.pivot_mode = "INIT" 

    def normalize_angle(self, angle):
        return angle % (2 * math.pi)

    def calculate_dynamic_pivot(self, left_thrust, left_angle_deg, right_thrust, right_angle_deg):
        """
        Calcola Pivot Point V7.1:
        - V > 1kn: Skeg (Prua)
        - V < 1kn: Contesa Forze (Skeg vs Motori)
        """
        u = self.state[3]
        u_kn = u * 1.94384 
        
        # --- CASO 1: NAVIGAZIONE (V > 1 kn) ---
        if u_kn > 1.0:
            self.pivot_mode = "SKEG (AVANTI)"
            return POS_SKEG_Y 
        elif u_kn < -1.0:
            self.pivot_mode = "SKEG (INDIETRO)"
            return 3.0 
            
        # --- CASO 2: MANOVRA (V < 1 kn) ---
        else:
            self.pivot_mode = "FORCE LOGIC"
            
            rad_l = math.radians(left_angle_deg)
            rad_r = math.radians(right_angle_deg)
            
            # Componenti locali (X=Prua, Y=Dritta)
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
        # 1. Pivot Point
        pp_y = self.calculate_dynamic_pivot(left_thrust, left_angle, right_thrust, right_angle)
        self.current_pp_y = pp_y 
        pp_x = 0.0 

        u = self.state[3]
        v = self.state[4]
        r = self.state[5]

        # --- FORZE (System: X=Prua, Y=Dritta) ---
        rad_l = math.radians(left_angle)
        rad_r = math.radians(right_angle)

        fx_l = left_thrust * math.cos(rad_l)
        fy_l = left_thrust * math.sin(rad_l)
        fx_r = right_thrust * math.cos(rad_r)
        fy_r = right_thrust * math.sin(rad_r)

        X_thrust = fx_l + fx_r
        Y_thrust = fy_l + fy_r

        # Momento (r x F) -> CCW+
        # Motori a Y = -12. 
        # Spinta a Dritta (+Fy) a poppa genera rotazione oraria della nave?
        # No, spinta laterale a poppa fa ruotare la prua dalla parte opposta.
        # Spinta DX a poppa -> Poppa va a DX -> Prua va a SX (CCW).
        # Math: Torque = x*Fy - y*Fx.
        # SX: (-2.7, -12). DX: (2.7, -12).
        moment_l = (-POS_THRUSTERS_X * fy_l) - (POS_THRUSTERS_Y * fx_l)
        moment_r = (POS_THRUSTERS_X * fy_r) - (POS_THRUSTERS_Y * fx_r)
        N_thrust = moment_l + moment_r

        # --- DAMPING ---
        u_at_pivot = u - (r * pp_y)
        v_at_pivot = v + (r * pp_x)
        
        X_damping = -(LINEAR_DAMPING_SURGE * u_at_pivot)
        Y_damping = -(LINEAR_DAMPING_SWAY * v_at_pivot)
        N_damping_rot = -(ANGULAR_DAMPING * r)
        
        N_damping_induced = (pp_x * Y_damping) - (pp_y * X_damping)
        
        X_total = X_thrust + X_damping
        Y_total = Y_thrust + Y_damping
        N_total = N_thrust + N_damping_rot + N_damping_induced

        # --- INTEGRAZIONE ---
        u_dot = X_total / SHIP_MASS
        v_dot = Y_total / SHIP_MASS
        r_dot = N_total / MOMENT_OF_INERTIA

        self.state[3] += u_dot * dt
        self.state[4] += v_dot * dt
        self.state[5] += r_dot * dt
        
        # Deadband
        if abs(self.state[3]) < 0.001: self.state[3] = 0
        if abs(self.state[4]) < 0.001: self.state[4] = 0
        if abs(self.state[5]) < 0.0001: self.state[5] = 0

        # World Pos (Math Angle)
        psi = self.state[2]
        c = math.cos(psi)
        s = math.sin(psi)
        
        # Rotazione vettori velocità locale -> globale
        # u è lungo asse X locale (Heading), v lungo asse Y locale (+90 deg)
        # x_dot = u * cos(psi) - v * sin(psi)
        # y_dot = u * sin(psi) + v * cos(psi)
        x_dot = self.state[3] * c - self.state[4] * s
        y_dot = self.state[3] * s + self.state[4] * c

        self.state[0] += x_dot * dt
        self.state[1] += y_dot * dt
        self.state[2] += self.state[5] * dt
        self.state[2] = self.normalize_angle(self.state[2])
