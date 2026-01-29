import numpy as np
import math
from constants import *

class PhysicsEngine:
    def __init__(self):
        # Stato: [x, y, psi, u, v, r]
        self.state = np.zeros(6)
        
        # Stato calcolato del Pivot Point (per visualizzazione e debugging)
        self.current_pp_y = 0.0 
        self.current_pp_x = 0.0
        self.pivot_mode = "INIT" # "SKEG" o "FORCE"

    def normalize_angle(self, angle):
        return angle % (2 * math.pi)

    def calculate_dynamic_pivot(self, left_thrust, left_angle_deg, right_thrust, right_angle_deg):
        """
        Determina la posizione del Pivot Point (PP) basandosi su:
        1. Velocità (Regime Idrodinamico vs Manovra)
        2. Bilanciamento Forze (Regime Manovra < 1kn)
        """
        u = self.state[3]
        u_kn = u * 1.94384
        
        # --- 1. REGIME IDRODINAMICO (Velocità > 1.0 kn) ---
        if u_kn > 1.0:
            # Avanti veloce: Lo Skeg domina assolutamente
            self.pivot_mode = "SKEG (FWD)"
            return 0.0, POS_SKEG_Y # +5.0m
            
        elif u_kn < -1.0:
            # Indietro veloce: Lo Skeg guida ancora la stabilità (prua segue)
            # Ma il centro di resistenza arretra leggermente
            self.pivot_mode = "SKEG (BWD)"
            return 0.0, 3.0 # +3.0m
            
        # --- 2. REGIME MANOVRA / STATICO (< 1.0 kn) ---
        else:
            self.pivot_mode = "FORCE MIX"
            # Qui applichiamo la teoria della "Contesa delle Forze"
            
            # Converti angoli in radianti
            rad_l = math.radians(left_angle_deg)
            rad_r = math.radians(right_angle_deg)
            
            # Componenti Forze Motori (Local Frame)
            # X = Longitudinale, Y = Trasversale
            fx_l = left_thrust * math.cos(rad_l)
            fy_l = left_thrust * math.sin(rad_l)
            fx_r = right_thrust * math.cos(rad_r)
            fy_r = right_thrust * math.sin(rad_r)
            
            # Analisi Forze
            # Forza Sway Totale (Valore assoluto combinato - quanto spingiamo di lato?)
            # Usiamo la somma dei valori assoluti per capire l'INTENZIONE di spinta laterale
            force_sway_intent = abs(fy_l) + abs(fy_r)
            
            # Forza Twist (Differenza longitudinale - quanto stiamo ruotando/controstendendo?)
            # Se uno spinge avanti e uno indietro, questo valore esplode
            force_twist_intent = abs(fx_l - fx_r)
            
            # Evitiamo divisioni per zero
            total_intent = force_sway_intent + force_twist_intent
            if total_intent < 100.0: # Motori quasi fermi
                # Default a centro nave o leggermente prua se fermi
                return 0.0, 2.0 
            
            # RATIO: 1.0 = Solo Sway (90/90), 0.0 = Solo Twist (Avanti/Indietro)
            ratio = force_sway_intent / total_intent
            
            # INTERPOLAZIONE
            # Se Ratio = 1 (90/90) -> PP va sullo SKEG (Prua ferma, poppa ruota) -> Target: POS_SKEG_Y
            # Se Ratio = 0 (Twist) -> PP va sui MOTORI (Rotazione su se stessi) -> Target: POS_STERN_Y
            
            calculated_y = POS_STERN_Y + (POS_SKEG_Y - POS_STERN_Y) * ratio
            
            self.current_pp_y = calculated_y
            return 0.0, calculated_y

    def update(self, dt, left_thrust, left_angle, right_thrust, right_angle):
        
        # 1. Calcola DOVE si trova il Pivot Point in questo istante
        pp_x, pp_y = self.calculate_dynamic_pivot(left_thrust, left_angle, right_thrust, right_angle)
        
        # Salva per visualizzazione
        self.current_pp_x = pp_x
        self.current_pp_y = pp_y

        u = self.state[3]
        v = self.state[4]
        r = self.state[5]

        # --- CALCOLO FORZE MOTORI ---
        rad_l = math.radians(left_angle)
        rad_r = math.radians(right_angle)

        fx_l = left_thrust * math.cos(rad_l)
        fy_l = left_thrust * math.sin(rad_l)
        fx_r = right_thrust * math.cos(rad_r)
        fy_r = right_thrust * math.sin(rad_r)

        X_thrust = fx_l + fx_r
        Y_thrust = fy_l + fy_r

        # Momento Motori (Sempre applicato a POS_STERN_Y = -12.0)
        # Torque = arm * force. Arm is vector from CG to Thruster.
        # Thrusters are at (+- offset, -12)
        moment_l = (-THRUSTER_X_OFFSET * fy_l) - (THRUSTER_Y_OFFSET * fx_l)
        moment_r = (THRUSTER_X_OFFSET * fy_r) - (THRUSTER_Y_OFFSET * fx_r)
        N_thrust = moment_l + moment_r

        # --- DAMPING (APPLICATO AL PIVOT POINT CALCOLATO) ---
        # La resistenza dell'acqua agisce principalmente nel punto PP calcolato.
        
        # Velocità locale nel PP
        u_at_pivot = u - (r * pp_y)
        v_at_pivot = v + (r * pp_x)
        
        # Forze Resistenti
        X_damping = -(LINEAR_DAMPING_SURGE * u_at_pivot)
        Y_damping = -(LINEAR_DAMPING_SWAY * v_at_pivot)
        
        # Momento Resistente Puro (Yaw rate)
        N_damping_rot = -(ANGULAR_DAMPING * r)
        
        # Momento Indotto (Leva del Damping rispetto al CG)
        # Se PP è a prua (pp_y > 0), la resistenza laterale crea un momento che raddrizza la nave
        N_damping_induced = (pp_x * Y_damping) - (pp_y * X_damping)
        
        # Totali
        X_total = X_thrust + X_damping
        Y_total = Y_thrust + Y_damping
        N_total = N_thrust + N_damping_rot + N_damping_induced

        # Integrazione Newton
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

        # Posizione World
        psi = self.state[2]
        c = math.cos(psi)
        s = math.sin(psi)

        x_dot = self.state[3] * c - self.state[4] * s
        y_dot = self.state[3] * s + self.state[4] * c

        self.state[0] += x_dot * dt
        self.state[1] += y_dot * dt
        self.state[2] += self.state[5] * dt
        self.state[2] = self.normalize_angle(self.state[2])
