import numpy as np
import math
from constants import *

class PhysicsEngine:
    def __init__(self):
        self.reset()

    def reset(self):
        # Stato: [x, y, psi, u, v, r]
        # X,Y=Mondo. Psi=Heading Math (0=Est).
        self.state = np.zeros(6)
        self.state[2] = math.pi / 2 # Prua a Nord (90° Math)
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
            
            # Qui usiamo coord schermo per logica semplice (Y=Long, X=Lat)
            # Ma attenzione: nel physics engine X è Longitudinale
            # Usiamo magnitudo forze
            
            fx_l = left_thrust * math.cos(rad_l)
            fy_l = left_thrust * math.sin(rad_l)
            fx_r = right_thrust * math.cos(rad_r)
            fy_r = right_thrust * math.sin(rad_r)
            
            # Force intent
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

        u = self.state[3] # Surge (Longitudinale)
        v = self.state[4] # Sway (Trasversale)
        r = self.state[5] # Yaw Rate

        # --- CALCOLO FORZE E MOMENTI (BODY FRAME) ---
        # Body Frame Standard: X=Avanti, Y=Destra (Starboard), Z=Giu
        # Angoli input: 0=Avanti, 90=Destra.
        # Physics Engine segue convenzione matematica per rotazione (CCW+)
        # Ma forze seguono Body Frame.
        
        # 1. Converti Input in Forze Locali
        rad_l = math.radians(left_angle)
        rad_r = math.radians(right_angle)

        # Fx = Longitudinale (Avanti +)
        # Fy = Trasversale (Destra +)
        # Input 0 deg -> cos=1, sin=0 -> Fx=1 (Avanti), Fy=0. OK.
        fx_l = left_thrust * math.cos(rad_l)
        fy_l = left_thrust * math.sin(rad_l)
        fx_r = right_thrust * math.cos(rad_r)
        fy_r = right_thrust * math.sin(rad_r)

        X_thrust = fx_l + fx_r
        Y_thrust = fy_l + fy_r

        # 2. Calcolo Momenti (Torque)
        # Posizioni Propulsori nel Body Frame (X=Fwd, Y=Right)
        # SX: x = -12, y = -2.7 (Port)
        # DX: x = -12, y = +2.7 (Stbd)
        
        # Torque = r x F (componente z) = x*Fy - y*Fx
        # Attenzione ai segni!
        # Esempio: SX (y=-2.7) spinge Avanti (Fx=1, Fy=0).
        # Torque = (-12 * 0) - (-2.7 * 1) = +2.7.
        # +2.7 significa rotazione CCW (Antioraria). 
        # MA spinta a sinistra avanti deve girare la nave a destra (CW)!
        # Quindi la formula standard r x F da momento positivo CCW.
        # Noi vogliamo che SX avanti dia momento negativo (CW).
        # Quindi Formula corretta per la nostra convenzione (o invertiamo risultato):
        # M = y*Fx - x*Fy
        # Check SX: (-2.7 * 1) - (-12 * 0) = -2.7 (Negativo -> CW -> Destra). CORRETTO.
        # Check DX: (+2.7 * 1) - (-12 * 0) = +2.7 (Positivo -> CCW -> Sinistra). CORRETTO.
        
        moment_l = (-POS_THRUSTERS_X * fx_l) - (POS_THRUSTERS_Y * fy_l)
        moment_r = (POS_THRUSTERS_X * fx_r) - (POS_THRUSTERS_Y * fy_r)
        N_thrust = moment_l + moment_r

        # 3. Damping
        u_at_pivot = u - (r * pp_y)
        v_at_pivot = v + (r * pp_x)
        
        X_damping = -(LINEAR_DAMPING_SURGE * u_at_pivot)
        Y_damping = -(LINEAR_DAMPING_SWAY * v_at_pivot)
        N_damping_rot = -(ANGULAR_DAMPING * r)
        
        # Momento indotto dal damping (Leva)
        # Applicato al PP.
        # M_induced = y_pp * Fx_damp - x_pp * Fy_damp
        # PP è su asse simmetria (x_pp=0).
        # M = 0 * Fx - pp_y * Fy = -pp_y * Fy.
        # Se pp_y = 5 (Prua) e nave scivola a destra (v>0, Fy<0), 
        # Forza resistente punta a sinistra. Leva positiva.
        # Deve raddrizzare la nave?
        # Check formula Torque standard: x*Fy - y*Fx.
        # Qui usiamo la formula corretta sopra: y*Fx - x*Fy
        # x_pp (longitudinale) = pp_y (variabile nostra). y_pp (laterale) = 0.
        # M = 0 * X_damp - pp_y * Y_damp
        N_damping_induced = -(pp_y * Y_damping)
        
        X_total = X_thrust + X_damping
        Y_total = Y_thrust + Y_damping
        N_total = N_thrust + N_damping_rot + N_damping_induced

        # 4. Integrazione
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

        # 5. World dynamics
        psi = self.state[2]
        c = math.cos(psi)
        s = math.sin(psi)
        
        # Trasformazione velocita locale -> globale
        # Physics psi 0 = Est.
        x_dot = self.state[3] * c - self.state[4] * s
        y_dot = self.state[3] * s + self.state[4] * c

        self.state[0] += x_dot * dt
        self.state[1] += y_dot * dt
        self.state[2] += self.state[5] * dt
        self.state[2] = self.normalize_angle(self.state[2])
