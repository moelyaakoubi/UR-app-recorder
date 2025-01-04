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

    def record_data(host, port, frequency, selected_data, output_file, buffered=False, binary=False, samples=0):
    import rtde.rtde as rtde
    import rtde.rtde_config as rtde_config
    import rtde.csv_writer as csv_writer
    import rtde.csv_binary_writer as csv_binary_writer

    # Generate a dynamic configuration file
    from tempfile import NamedTemporaryFile
    import os

    with NamedTemporaryFile(delete=False, mode='w', suffix='.xml') as tmp_config:
        tmp_config.write("<rtde_config>\n  <output>\n")
        for variable in selected_data:
            tmp_config.write(f"    <variable name=\"{variable}\" type=\"VECTOR6D\"/>\n")
        tmp_config.write("  </output>\n</rtde_config>\n")
        config_file_path = tmp_config.name

    try:
        # Load the dynamic configuration file
        conf = rtde_config.ConfigFile(config_file_path)
        output_names, output_types = conf.get_recipe("out")

        # Establish RTDE connection
        con = rtde.RTDE(host, port)
        con.connect()

        # Get the controller version
        version = con.get_controller_version()
        print(f"Connected to robot controller version: {version}")

        # Setup the RTDE output
        if not con.send_output_setup(output_names, output_types, frequency=frequency):
            raise ValueError("Unable to configure RTDE output.")

        # Start synchronization
        if not con.send_start():
            raise ValueError("Unable to start synchronization.")

        # Open the output file
        write_modes = "wb" if binary else "w"
        with open(output_file, write_modes, newline='') as csvfile:
            writer = (
                csv_binary_writer.CSVBinaryWriter(csvfile, output_names, output_types)
                if binary
                else csv_writer.CSVWriter(csvfile, output_names, output_types)
            )
            writer.writeheader()

            # Start recording
            i = 1
            keep_running = True
            while keep_running:
                if samples > 0 and i >= samples:
                    keep_running = False

                if i % frequency == 0:
                    print(f"\rRecorded {i} samples.", end="")

                try:
                    state = con.receive_buffered(binary) if buffered else con.receive(binary)
                    if state:
                        writer.writerow(state)
                        i += 1
                except KeyboardInterrupt:
                    print("\nRecording interrupted by user.")
                    break
                except rtde.RTDEException as e:
                    print(f"RTDE error: {e}")
                    break

        print("\nRecording completed successfully.")

        # Pause synchronization and disconnect
        con.send_pause()
        con.disconnect()

    finally:
        # Clean up the temporary configuration file
        if os.path.exists(config_file_path):
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
