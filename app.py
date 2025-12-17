import tkinter as tk
from tkinter import ttk
import math

class AzimuthControlApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Simulatore Azimuthale - Side Step Vector Logic")
        self.root.geometry("600x650")
        
        # --- Variabili di Stato ---
        # Port (Sinistra)
        self.port_azimuth = tk.DoubleVar(value=0)
        self.port_power = tk.DoubleVar(value=0)
        
        # Starboard (Dritta)
        self.stbd_azimuth = tk.DoubleVar(value=0)
        self.stbd_power = tk.DoubleVar(value=0)

        # --- Interfaccia Grafica ---
        self.create_ui()
        
        # Aggiornamento iniziale grafico
        self.update_canvas()

    def create_ui(self):
        # Frame Principale
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # --- Sezione Comandi Manuali ---
        controls_frame = ttk.LabelFrame(main_frame, text="Controlli Manuali", padding="10")
        controls_frame.pack(fill=tk.X, pady=5)

        # Colonna Sinistra (PORT)
        ttk.Label(controls_frame, text="PORT THRUSTER", font=('Arial', 10, 'bold')).grid(row=0, column=0, columnspan=2, pady=5)
        
        ttk.Label(controls_frame, text="Azimuth (0-359)").grid(row=1, column=0)
        self.scale_port_az = ttk.Scale(controls_frame, from_=0, to=359, variable=self.port_azimuth, command=self.on_change)
        self.scale_port_az.grid(row=2, column=0, padx=5, sticky="ew")
        self.lbl_port_az = ttk.Label(controls_frame, text="0°")
        self.lbl_port_az.grid(row=2, column=1)

        ttk.Label(controls_frame, text="Potenza (0-100%)").grid(row=3, column=0)
        self.scale_port_pwr = ttk.Scale(controls_frame, from_=0, to=100, variable=self.port_power, command=self.on_change)
        self.scale_port_pwr.grid(row=4, column=0, padx=5, sticky="ew")
        self.lbl_port_pwr = ttk.Label(controls_frame, text="0%")
        self.lbl_port_pwr.grid(row=4, column=1)

        # Separatore verticale
        ttk.Separator(controls_frame, orient='vertical').grid(row=0, column=2, rowspan=5, padx=20, sticky='ns')

        # Colonna Dritta (STARBOARD)
        ttk.Label(controls_frame, text="STBD THRUSTER", font=('Arial', 10, 'bold')).grid(row=0, column=3, columnspan=2, pady=5)
        
        ttk.Label(controls_frame, text="Azimuth (0-359)").grid(row=1, column=3)
        self.scale_stbd_az = ttk.Scale(controls_frame, from_=0, to=359, variable=self.stbd_azimuth, command=self.on_change)
        self.scale_stbd_az.grid(row=2, column=3, padx=5, sticky="ew")
        self.lbl_stbd_az = ttk.Label(controls_frame, text="0°")
        self.lbl_stbd_az.grid(row=2, column=4)

        ttk.Label(controls_frame, text="Potenza (0-100%)").grid(row=3, column=3)
        self.scale_stbd_pwr = ttk.Scale(controls_frame, from_=0, to=100, variable=self.stbd_power, command=self.on_change)
        self.scale_stbd_pwr.grid(row=4, column=3, padx=5, sticky="ew")
        self.lbl_stbd_pwr = ttk.Label(controls_frame, text="0%")
        self.lbl_stbd_pwr.grid(row=4, column=4)

        # --- Sezione Visualizzazione (Canvas) ---
        canvas_frame = ttk.LabelFrame(main_frame, text="Visualizzazione Vettoriale", padding="10")
        canvas_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        self.canvas = tk.Canvas(canvas_frame, bg="white", height=300)
        self.canvas.pack(fill=tk.BOTH, expand=True)

        # --- Sezione Pulsanti Rapidi (Preset) ---
        btn_frame = ttk.LabelFrame(main_frame, text="Manovre Rapide", padding="10")
        btn_frame.pack(fill=tk.X, pady=5)

        # Pulsante STOP
        ttk.Button(btn_frame, text="ALL STOP", command=self.set_stop).pack(side=tk.LEFT, padx=5, expand=True, fill=tk.X)

        # Pulsante FAST SIDE STEP SINISTRA (<--)
        # Logica: SB Drive (315/50%), PS Drag (145/44%)
        btn_left = tk.Button(btn_frame, text="<< FAST SIDE PORT", bg="#ffcccc", 
                             command=lambda: self.set_fast_side_step('PORT'))
        btn_left.pack(side=tk.LEFT, padx=5, expand=True, fill=tk.X)

        # Pulsante FAST SIDE STEP DRITTA (-->)
        # Logica: PS Drive (045/50%), SB Drag (215/44%)
        btn_right = tk.Button(btn_frame, text="FAST SIDE STBD >>", bg="#ccffcc", 
                              command=lambda: self.set_fast_side_step('STARBOARD'))
        btn_right.pack(side=tk.LEFT, padx=5, expand=True, fill=tk.X)

    def on_change(self, event=None):
        """Aggiorna le etichette e il disegno quando si muovono gli slider"""
        # Aggiorna label testuali
        self.lbl_port_az.config(text=f"{int(self.port_azimuth.get())}°")
        self.lbl_port_pwr.config(text=f"{int(self.port_power.get())}%")
        self.lbl_stbd_az.config(text=f"{int(self.stbd_azimuth.get())}°")
        self.lbl_stbd_pwr.config(text=f"{int(self.stbd_power.get())}%")
        
        # Aggiorna grafica
        self.update_canvas()

    def update_canvas(self):
        """Disegna la nave e i vettori di spinta"""
        self.canvas.delete("all")
        w = self.canvas.winfo_width()
        h = self.canvas.winfo_height()
        # Fallback se la finestra non è ancora renderizzata
        if w < 10: w = 580
        if h < 10: h = 300
        
        cx, cy = w / 2, h / 2
        
        # 1. Disegna sagoma nave (stilizzata)
        ship_width = 60
        ship_length = 180
        # Coordinate vertici nave
        bow = (cx, cy - ship_length/2)
        stern_left = (cx - ship_width/2, cy + ship_length/2)
        stern_right = (cx + ship_width/2, cy + ship_length/2)
        
        self.canvas.create_polygon(bow, stern_left, stern_right, outline="black", fill="#e0e0e0", width=2)
        # Pivot Point approssimato (Y)
        self.canvas.create_oval(cx-3, cy-3, cx+3, cy+3, fill="red") 
        self.canvas.create_text(cx+10, cy, text="PP")

        # 2. Disegna Vettore PORT (Sinistra)
        # Posizione thruster sinistro (poppa sinistra)
        tx_port = cx - 20
        ty_port = cy + 70
        self.draw_vector(tx_port, ty_port, self.port_azimuth.get(), self.port_power.get(), "red", "PORT")

        # 3. Disegna Vettore STBD (Dritta)
        # Posizione thruster destro (poppa dritta)
        tx_stbd = cx + 20
        ty_stbd = cy + 70
        self.draw_vector(tx_stbd, ty_stbd, self.stbd_azimuth.get(), self.stbd_power.get(), "green", "STBD")

    def draw_vector(self, x, y, azimuth, power, color, label):
        """Disegna una freccia che rappresenta la forza"""
        if power <= 0: return

        # Conversione Azimuth (Navigazione) -> Angolo Matematico
        # 0° Nav = Nord (Alto) -> -90° Math (Tkinter Y è invertito)
        # 90° Nav = Est (Destra) -> 0° Math
        # Math_angle = Azimuth - 90
        angle_rad = math.radians(azimuth - 90)
        
        length = power * 1.0  # Scala visiva
        
        # Calcolo punto finale vettore
        end_x = x + length * math.cos(angle_rad)
        end_y = y + length * math.sin(angle_rad)
        
        self.canvas.create_line(x, y, end_x, end_y, arrow=tk.LAST, width=3, fill=color)
        self.canvas.create_text(x, y-15, text=f"{label}\n{int(azimuth)}°", fill=color, font=("Arial", 8))

    # --- LOGICA DI CONTROLLO (I nuovi pulsanti) ---

    def set_stop(self):
        self.port_power.set(0)
        self.stbd_power.set(0)
        self.on_change()

    def set_fast_side_step(self, side):
        """
        Imposta i valori per il Fast Side Step con bilanciamento vettoriale.
        Surge netto ~= 0. Sway netto ~= Max. Momento bilanciato.
        """
        # Valori base calcolati
        drive_power = 50.0  # Spinta
        drag_power = 44.0   # Freno/Bilanciamento (calcolato per annullare surge)

        if side == 'STARBOARD':
            # --- DRITTA ---
            print("Applying: Fast Side Step STARBOARD")
            # PORT (Drive): 045° | 50%
            self.port_azimuth.set(45)
            self.port_power.set(drive_power)
            
            # STBD (Drag): 215° | 44% (Annulla surge, mantiene sway residuo)
            self.stbd_azimuth.set(215)
            self.stbd_power.set(drag_power)

        elif side == 'PORT':
            # --- SINISTRA ---
            print("Applying: Fast Side Step PORT")
            # STBD (Drive): 315° (equivale a -45°) | 50%
            self.stbd_azimuth.set(315)
            self.stbd_power.set(drive_power)
            
            # PORT (Drag): 145° | 44% (Speculare al 215°)
            self.port_azimuth.set(145)
            self.port_power.set(drag_power)
        
        self.on_change()

if __name__ == "__main__":
    root = tk.Tk()
    app = AzimuthControlApp(root)
    root.mainloop()
