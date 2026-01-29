import numpy as np
import math
from constants import *

class PhysicsEngine:
    def __init__(self):
        # Stato: [x, y, psi, u, v, r]
        self.state = np.zeros(6)
        
        # Variabili per visualizzare il calcolo interno
        self.current_pp_y = 0.0 
        self.pivot_mode = "INIT" 

    def normalize_angle(self, angle):
        return angle % (2 * math.pi)

    def calculate_dynamic_pivot(self, left_thrust, left_angle_deg, right_thrust, right_angle_deg):
        """
        Calcola la posizione Y del Pivot Point.
        Logica:
        - V > 1.0 kn: Idrodinamica (Prua/Skeg)
        - V < 1.0 kn: Contesa di forze (Skeg vs Motori)
        """
        u = self.state[3]
        u_kn = u * 1.94384 # m/s -> nodi
        
        # --- CASO 1: NAVIGAZIONE (V > 1 kn) ---
        if u_kn > 1.0:
            self.pivot_mode = "SKEG (AVANTI)"
            return POS_SKEG_Y # +5.0m
            
        elif u_kn < -1.0:
            self.pivot_mode = "SKEG (INDIETRO)"
            # Anche in retromarcia, la prua profonda fa da "ancora" laterale
            return 3.0 
            
        # --- CASO 2: MANOVRA (V < 1 kn) ---
        else:
            self.pivot_mode = "FORCE LOGIC"
            
            # 1. Calcolo Componenti Forze
            rad_l = math.radians(left_angle_deg)
            rad_r = math.radians(right_angle_deg)
            
            fx_l = left_thrust * math.cos(rad_l)
            fy_l = left_thrust * math.sin(rad_l)
            fx_r = right_thrust * math.cos(rad_r)
            fy_r = right_thrust * math.sin(rad_r)
            
            # 2. Analisi Intenzione
            # Quanta forza laterale NETTA stiamo applicando? (Somma vettoriale Y)
            sway_force_net = abs(fy_l + fy_r)
            
            # Quanta forza rotatoria (TWIST) stiamo applicando? (Differenza X)
            twist_force_net = abs(fx_l - fx_r)
            
            total_force = sway_force_net + twist_force_net
            
            # Se i motori sono a zero o quasi
            if total_force < 1000.0: 
                return 2.0 # Valore neutro di default
            
            # 3. Ratio (Chi vince?)
            # Ratio = 1.0 -> Puro Side Step (Vince lo Skeg, PP a Prua)
            # Ratio = 0.0 -> Puro Twist (Vincono i Motori, PP a Poppa)
            ratio = sway_force_net / (total_force + 0.1)
            
            # 4. Interpolazione Lineare
            # PP = Poppa + (Differenza * Ratio)
            calculated_y = POS_STERN_Y + (POS_SKEG_Y - POS_STERN_Y) * ratio
            
            return calculated_y

    def update(self, dt, left_thrust, left_angle, right_thrust, right_angle):
        
        # 1. Calcola il Pivot Point corrente
        pp_y = self.calculate_dynamic_pivot(left_thrust, left_angle, right_thrust, right_angle)
        self.current_pp_y = pp_y # Salva per visualizzazione
        pp_x = 0.0 # Assumiamo simmetria laterale per ora

        u = self.state[3]
        v = self.state[4]
        r = self.state[5]

        # --- FORZE MOTORI ---
        rad_l = math.radians(left_angle)
        rad_r = math.radians(right_angle)

        fx_l = left_thrust * math.cos(rad_l)
        fy_l = left_thrust * math.sin(rad_l)
        fx_r = right_thrust * math.cos(rad_r)
        fy_r = right_thrust * math.sin(rad_r)

        X_thrust = fx_l + fx_r
        Y_thrust = fy_l + fy_r

        # Momento Motori (Sempre calcolato rispetto al centro geometrico 0,0)
        # I motori sono fisicamente a poppa, quindi generano momento.
        moment_l = (-THRUSTER_X_OFFSET * fy_l) - (THRUSTER_Y_OFFSET * fx_l)
        moment_r = (THRUSTER_X_OFFSET * fy_r) - (THRUSTER_Y_OFFSET * fx_r)
        N_thrust = moment_l + moment_r

        # --- DAMPING (PIVOT AWARE) ---
        # Qui usiamo il PP calcolato per applicare la resistenza nel punto giusto
        
        # Velocità locale nel punto PP
        u_at_pivot = u - (r * pp_y)
        v_at_pivot = v + (r * pp_x)
        
        # Resistenza Lineare (applicata al PP)
        X_damping = -(LINEAR_DAMPING_SURGE * u_at_pivot)
        Y_damping = -(LINEAR_DAMPING_SWAY * v_at_pivot)
        
        # Momento Resistente Rotazionale (Puro)
        N_damping_rot = -(ANGULAR_DAMPING * r)
        
        # Momento Indotto dal Damping (Leva)
        # Se il PP non è al centro (0,0), la resistenza applicata lì crea un momento
        N_damping_induced = (pp_x * Y_damping) - (pp_y * X_damping)
        
        # Somma Totale
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
        
        # Deadband (Stop completo se quasi fermi)
        if abs(self.state[3]) < 0.001: self.state[3] = 0
        if abs(self.state[4]) < 0.001: self.state[4] = 0
        if abs(self.state[5]) < 0.0001: self.state[5] = 0

        # Posizione Globale
        psi = self.state[2]
        c = math.cos(psi)
        s = math.sin(psi)

        x_dot = self.state[3] * c - self.state[4] * s
        y_dot = self.state[3] * s + self.state[4] * c

        self.state[0] += x_dot * dt
        self.state[1] += y_dot * dt
        self.state[2] += self.state[5] * dt
        self.state[2] = self.normalize_angle(self.state[2])
