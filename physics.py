import numpy as np
import math
from constants import *

class PhysicsEngine:
    def __init__(self):
        self.reset()

    def reset(self):
        # Stato: [x, y, psi, u, v, r]
        self.state = np.zeros(6)
        self.state[2] = math.pi / 2  # Heading iniziale (Nord nel sistema cartesiano visuale)
        self.current_pp_y = DEFAULT_PP_Y 
        self.pivot_mode = "MANUAL" 

    def normalize_angle(self, angle):
        return angle % (2 * math.pi)

    def calculate_dynamic_pivot(self, left_thrust, left_angle_deg, right_thrust, right_angle_deg):
        # Metodo mantenuto per compatibilità, non usato in modalità manuale
        return DEFAULT_PP_Y

    def update(self, dt, left_thrust, left_angle, right_thrust, right_angle, pp_x, pp_y):
        self.current_pp_y = pp_y 
        
        u = self.state[3] # Surge velocity
        v = self.state[4] # Sway velocity
        r = self.state[5] # Yaw rate

        # --- SCOMPOSIZIONE FORZE (SISTEMA NAUTICO) ---
        # 0° = Nord (+Y), 90° = Est (+X)
        # Fx = T * sin(theta)
        # Fy = T * cos(theta)
        
        rad_l = math.radians(left_angle)
        rad_r = math.radians(right_angle)

        fx_l = left_thrust * math.sin(rad_l)
        fy_l = left_thrust * math.cos(rad_l)
        
        fx_r = right_thrust * math.sin(rad_r)
        fy_r = right_thrust * math.cos(rad_r)

        X_thrust = fx_l + fx_r
        Y_thrust = fy_l + fy_r
        
        # --- CALCOLO MOMENTO (Cross Product: x*Fy - y*Fx) ---
        # Posizione Motori rispetto al centro geometrico (0,0)
        # SX: x = -2.7, y = -12.0
        # DX: x = +2.7, y = -12.0
        
        # Momento SX
        pos_lx = -POS_THRUSTERS_X
        pos_ly = POS_THRUSTERS_Y
        moment_l = (pos_lx * fy_l) - (pos_ly * fx_l)
        
        # Momento DX
        pos_rx = POS_THRUSTERS_X
        pos_ry = POS_THRUSTERS_Y
        moment_r = (pos_rx * fy_r) - (pos_ry * fx_r)
        
        N_thrust = moment_l + moment_r

        # --- DAMPING QUADRATICO ---
        # Velocità locali al Pivot Point manuale
        # u_p = u - r*y_p
        # v_p = v + r*x_p
        u_at_pivot = u - (r * pp_y)
        v_at_pivot = v + (r * pp_x)
        
        X_damping = -(QUADRATIC_DAMPING_SURGE * u_at_pivot * abs(u_at_pivot))
        Y_damping = -(QUADRATIC_DAMPING_SWAY * v_at_pivot * abs(v_at_pivot))
        
        # Damping Rotazionale Puro
        N_damping_rot = -(ANGULAR_DAMPING * r)
        
        # Momento Indotto dalla resistenza laterale (Leva = Distanza PP dal CG)
        # Cross Product della forza di damping applicata nel PP
        # M_induced = x_pp * Y_damp - y_pp * X_damp
        N_damping_induced = (pp_x * Y_damping) - (pp_y * X_damping)
        
        X_total = X_thrust + X_damping
        Y_total = Y_thrust + Y_damping
        N_total = N_thrust + N_damping_rot + N_damping_induced

        # Integrazione Newton-Eulero
        u_dot = X_total / SHIP_MASS
        v_dot = Y_total / SHIP_MASS
        r_dot = N_total / MOMENT_OF_INERTIA

        self.state[3] += u_dot * dt
        self.state[4] += v_dot * dt
        self.state[5] += r_dot * dt
        
        # Deadband / Attrito statico simulato
        if abs(self.state[3]) < 0.001: self.state[3] = 0
        if abs(self.state[4]) < 0.001: self.state[4] = 0
        if abs(self.state[5]) < 0.0001: self.state[5] = 0

        # Conversione velocità Ship -> World frame
        psi = self.state[2]
        c = math.cos(psi) # NB: In physics engine standard (math angle), psi=pi/2 is North.
        s = math.sin(psi)
        
        # Nota: Qui usiamo la rotazione standard matematica per aggiornare la posizione
        # Math X = World X, Math Y = World Y. 
        # La rotazione della nave è gestita coerentemente se psi parte da pi/2.
        # x_dot_world = u * cos(theta_nav) - v * sin(theta_nav) ?? 
        # No, standard rotation matrix:
        # x_dot = u * cos(psi) - v * sin(psi)
        # y_dot = u * sin(psi) + v * cos(psi)
        # Verifica: Se psi=90° (Nord), c=0, s=1.
        # Se u=1 (avanti), x_dot=0, y_dot=1. Nave va a Nord. CORRETTO.
        # Se v=1 (dritta/est), x_dot=-1, y_dot=0. Nave va a Ovest?
        # WAIT: In coordinate nave standard, v è positivo a Dritta (Starboard)? 
        # Solitamente X=Avanti, Y=Dritta.
        # Se Y=Dritta, allora con Psi=90 (Nord), Y nave punta a Est.
        # v=1 (Est). x_dot=-1 (Ovest). C'è un segno invertito qui o nella definizione di v.
        # Assumiamo v positivo = Dritta.
        # Matrice corretta per X=Avanti, Y=Dritta -> World (psi=angolo prua da asse X):
        # Xw_dot = u cos psi - v sin psi
        # Yw_dot = u sin psi + v cos psi
        # Con Psi=90 (Nord): Xw= -v, Yw= u. 
        # Se v=1 (Dritta/Est), Xw diventa -1 (Ovest). ERRORE.
        
        # FIX ROTAZIONE:
        # Se psi è l'angolo matematico (0=Est, 90=Nord):
        # Prua = u. Dritta = v.
        # Vettore velocità in body frame: Vb = [u, v]
        # Vettore v punta a -90 gradi rispetto a u.
        # Quindi x_dot = u cos(psi) + v cos(psi - 90) = u cos(psi) + v sin(psi)
        #        y_dot = u sin(psi) + v sin(psi - 90) = u sin(psi) - v cos(psi)
        
        x_dot = self.state[3] * c + self.state[4] * s
        y_dot = self.state[3] * s - self.state[4] * c

        self.state[0] += x_dot * dt
        self.state[1] += y_dot * dt
        self.state[2] += self.state[5] * dt
        self.state[2] = self.normalize_angle(self.state[2])
