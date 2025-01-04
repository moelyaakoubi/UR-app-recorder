import tkinter as tk
from tkinter import messagebox, filedialog
import threading
import csv

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
            threading.Thread(target=self.record_data, args=(host, 30004, frequency, selected_data)).start()
        except ValueError:
            messagebox.showerror("Error", "Frequency must be a valid number.")

    def record_data(self, host, port, frequency, selected_data):
        import rtde.rtde as rtde
        import rtde.rtde_config as rtde_config
        import time
        from tempfile import NamedTemporaryFile
        import os

        try:
            # Temporary Configuration File Setup
            with NamedTemporaryFile(delete=False, mode='w', suffix='.xml') as tmp_config:
                tmp_config.write("<rtde_config>\n  <output>\n")
                for variable in selected_data:
                    tmp_config.write(f"    <variable name=\"{variable}\" type=\"VECTOR6D\"/>\n")
                tmp_config.write("  </output>\n</rtde_config>\n")
                config_file_path = tmp_config.name

            # Load RTDE Configuration
            conf = rtde_config.ConfigFile(config_file_path)
            output_names, output_types = conf.get_recipe("out")
            
            # Print for debugging
            print("Output Names: ", output_names)
            print("Output Types: ", output_types)

            # Connect to Robot
            self.conn = rtde.RTDE(host, port)
            self.conn.connect()
            self.conn.get_controller_version()
            
            # Setup RTDE output
            if not self.conn.send_output_setup(output_names, output_types, frequency=frequency):
                raise ValueError("Unable to configure RTDE output.")
            
            # Start synchronization
            self.conn.send_start()

            # Start Recording
            self.data_buffer = []
            i = 0
            while self.recording:
                state = self.conn.receive()
                if state:
                    self.data_buffer.append([getattr(state, name) for name in output_names])
                    i += 1
                time.sleep(1 / frequency)

        except Exception as e:
            messagebox.showerror("Error", f"Recording failed: {e}")
        finally:
            if self.conn:
                self.conn.send_pause()
                self.conn.disconnect()
            if config_file_path:
                os.remove(config_file_path)


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
