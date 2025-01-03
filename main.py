import tkinter as tk
from tkinter import messagebox, filedialog
import rtde.rtde as rtde
import rtde.rtde_config as rtde_config
import csv
import threading

class RobotDataRecorder:
    def __init__(self, root):
        self.root = root
        self.root.title("Universal Robot Data Recorder")

        # Initialize variables
        self.conn = None
        self.recording = False
        self.data_buffer = []
        self.columns = []
        
        # GUI Components
        self.setup_ui()
    
    def setup_ui(self):
        # Host IP
        tk.Label(self.root, text="Host IP:").grid(row=0, column=0, padx=5, pady=5, sticky="e")
        self.host_entry = tk.Entry(self.root, width=20)
        self.host_entry.grid(row=0, column=1, padx=5, pady=5)

        # Frequency
        tk.Label(self.root, text="Frequency (Hz):").grid(row=1, column=0, padx=5, pady=5, sticky="e")
        self.freq_entry = tk.Entry(self.root, width=20)
        self.freq_entry.grid(row=1, column=1, padx=5, pady=5)

        # Data Selection
        tk.Label(self.root, text="Select Data to Record:").grid(row=2, column=0, padx=5, pady=5, sticky="e")
        self.data_listbox = tk.Listbox(self.root, selectmode="multiple", height=6)
        self.data_listbox.grid(row=2, column=1, padx=5, pady=5)
        self.data_listbox.insert(0, "actual_q")
        self.data_listbox.insert(1, "actual_TCP_pose")
        self.data_listbox.insert(2, "actual_TCP_force")
        self.data_listbox.insert(3, "target_q")
        self.data_listbox.insert(4, "target_TCP_pose")

        # Buttons
        self.record_btn = tk.Button(self.root, text="Start Recording", command=self.start_recording)
        self.record_btn.grid(row=3, column=0, padx=5, pady=10)

        self.download_btn = tk.Button(self.root, text="Download CSV", command=self.download_csv)
        self.download_btn.grid(row=3, column=1, padx=5, pady=10)

    def start_recording(self):
        host = self.host_entry.get()
        try:
            frequency = int(self.freq_entry.get())
            selected_indices = self.data_listbox.curselection()
            selected_data = [self.data_listbox.get(i) for i in selected_indices]

            if not host or not selected_data or frequency <= 0:
                messagebox.showerror("Error", "Please fill in all fields correctly.")
                return
            
            self.recording = True
            self.columns = selected_data
            threading.Thread(target=self.record_data, args=(host, frequency, selected_data)).start()
        except ValueError:
            messagebox.showerror("Error", "Frequency must be a valid number.")

    def record_data(self, host, frequency, selected_data):
        try:
            # Establish RTDE connection
            conn = rtde.RTDE(host, 30004)
            conn.connect()

            # Create configuration file
            config = rtde_config.ConfigFile()
            for data in selected_data:
                config.add_output(data, "VECTOR6D")
            output_names, output_types = config.get_output_config()
            conn.send_output_setup(output_names, output_types)

            # Start streaming
            conn.start()
            self.data_buffer = []
            while self.recording:
                state = conn.receive()
                if state:
                    row = [getattr(state, col) for col in selected_data]
                    self.data_buffer.append(row)
            conn.disconnect()
        except Exception as e:
            messagebox.showerror("Connection Error", f"Error connecting to robot: {e}")
            self.recording = False

    def download_csv(self):
        if not self.data_buffer:
            messagebox.showinfo("No Data", "No data recorded to save.")
            return
        
        file_path = filedialog.asksaveasfilename(defaultextension=".csv", 
                                                 filetypes=[("CSV files", "*.csv")])
        if file_path:
            with open(file_path, 'w', newline='') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(self.columns)
                writer.writerows(self.data_buffer)
            messagebox.showinfo("Success", f"Data saved to {file_path}")
    
if __name__ == "__main__":
    root = tk.Tk()
    app = RobotDataRecorder(root)
    root.mainloop()
