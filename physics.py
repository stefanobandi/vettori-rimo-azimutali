import numpy as np
import math
from constants import *

class PhysicsEngine:
    def __init__(self):
        self.reset()

    def reset(self):
        # Stato: [x, y, psi, u, v, r]
        # x, y: Posizione Mondo
        # psi: Angolo Prua (0=Nord, CW+)
        # u: Surge (Avanti/Indietro)
        # v: Sway (Destra/Sinistra)
        # r: Yaw Rate
        self.state = np.zeros(6)
        self.current_pp_y = 0.0 
        self.pivot_mode = "INIT" 

    def normalize_angle(self, angle):
        return angle % (2 * math.pi)

    def calculate_dynamic_pivot(self, left_thrust, left_angle_deg, right_thrust, right_angle_deg):
        """
        Calcola la posizione Y del Pivot Point (V7.1 Logic).
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
            
            # Calcolo Componenti Forze
            rad_l = math.radians(left_angle_deg)
            rad_r = math.radians(right_angle_deg)
            
            # Nota: In questo sistema locale:
            # X = Longitudinale (Prua/Poppa)
            # Y = Trasversale (Dritta/Sinistra)
            # 0 gradi = Prua
            fx_l = left_thrust * math.cos(rad_l)
            fy_l = left_thrust * math.sin(rad_l)
            fx_r = right_thrust * math.cos(rad_r)
            fy_r = right_thrust * math.sin(rad_r)
            
            # Analisi Intenzione
            sway_force_net = abs(fy_l + fy_r)
            twist_force_net = abs(fx_l - fx_r)
            
            total_force = sway_force_net + twist_force_net
            
            if total_force < 1000.0: 
                return 2.0 # Default neutro
            
            # Ratio (Chi vince?)
            # 1.0 = Puro Sway (Vince Skeg -> Prua)
            # 0.0 = Puro Twist (Vince Motore -> Poppa)
            ratio = sway_force_net / (total_force + 0.1)
            
            calculated_y = POS_STERN_Y + (POS_SKEG_Y - POS_STERN_Y) * ratio
            return calculated_y

    def update(self, dt, left_thrust, left_angle, right_thrust, right_angle):
        # 1. Pivot Point Dinamico
        pp_y = self.calculate_dynamic_pivot(left_thrust, left_angle, right_thrust, right_angle)
        self.current_pp_y = pp_y 
        pp_x = 0.0 

        u = self.state[3]
        v = self.state[4]
        r = self.state[5]

        # --- FORZE MOTORI ---
        # Conversione Angoli: Input 0° = Nord (Avanti).
        # Math: 0° = Est.
        # Adattiamo le componenti:
        # Fx (Longitudinale) = Thrust * cos(angle)
        # Fy (Trasversale) = Thrust * sin(angle)
        
        rad_l = math.radians(left_angle)
        rad_r = math.radians(right_angle)

        fx_l = left_thrust * math.cos(rad_l)
        fy_l = left_thrust * math.sin(rad_l)
        fx_r = right_thrust * math.cos(rad_r)
        fy_r = right_thrust * math.sin(rad_r)

        X_thrust = fx_l + fx_r
        Y_thrust = fy_l + fy_r

        # Momento Motori
        # Braccio X * Forza Y - Braccio Y * Forza X
        # SX: (-offset, -12)
        # DX: (+offset, -12)
        moment_l = (-THRUSTER_X_OFFSET * fy_l) - (THRUSTER_Y_OFFSET * fx_l)
        moment_r = (THRUSTER_X_OFFSET * fy_r) - (THRUSTER_Y_OFFSET * fx_r)
        
        # Correzione Segno Momento:
        # Una spinta a Dritta (+Y) a Poppa (-Y_pos) deve creare rotazione Antioraria (Prua a Sx)?
        # -12 * +F = negativo. 
        # Verifichiamo standard: +Momento = Rotazione Oraria (Nautico) o Antioraria (Math)?
        # Math: CCW è positivo.
        # Se spingo a Dritta a poppa, la prua va a Sinistra (CCW).
        # Calcolo: -(-12) * F_pos = +12F. Positivo = CCW. OK.
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

        # Integrazione
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

        # Posizione Globale
        # psi: Heading. Math convenzione (0=Est, CCW+). 
        # Ma noi usiamo 0=Nord per input.
        # Manteniamo psi come angolo matematico standard rispetto al nord ruotato?
        # Semplifichiamo: psi è l'angolo di prua rispetto al Nord (0). CW (Orario) è Positivo?
        # NO, in fisica `r` (Yaw Rate) positivo è CCW solitamente.
        # Invertiamo il segno di r_dot per l'aggiornamento heading se vogliamo visualizzazione Nautica (CW+)
        # OPPURE manteniamo standard Math (CCW+) e invertiamo solo in visualizzazione.
        # Manteniamo Math Standard (CCW+) nel motore fisico.
        
        psi = self.state[2]
        c = math.cos(psi)
        s = math.sin(psi)
        
        # Nota: Qui assumiamo 0 = Nord, Y = Nord, X = Est.
        # x_dot = u * sin(psi) + v * cos(psi) ?
        # Standard Marine Body to NED:
        # North_dot = u * cos(psi) - v * sin(psi)
        # East_dot  = u * sin(psi) + v * cos(psi)
        # Assumendo psi=0 (Nord).
        
        # Rotazione vettoriale standard 2D
        x_dot = self.state[3] * s + self.state[4] * c # Componente Est
        y_dot = self.state[3] * c - self.state[4] * s # Componente Nord

        self.state[0] += x_dot * dt
        self.state[1] += y_dot * dt
        self.state[2] += self.state[5] * dt # CCW positivo
        self.state[2] = self.normalize_angle(self.state[2])
