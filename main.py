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
        if self.recording:
            self.recording = False
            self.record_btn.config(text="Start Recording")
            return

        host = self.host_entry.get()
        freq = self.freq_entry.get()
        if not host or not freq:
            messagebox.showerror("Error", "Please enter Host IP and Frequency.")
            return

        self.recording = True
        self.record_btn.config(text="Stop Recording")
        self.columns = ["time"]
        for i in self.data_listbox.curselection():
            self.columns.append(self.data_listbox.get(i))

        self.data_buffer = []
        self.thread = threading.Thread(target=self.record_data, args=(host, freq))
        self.thread.start()

    def record_data(self, host, freq):
        import rtde.rtde as rtde

        # Connect to UR Controller
        self.conn = rtde.RTDE(host)
        if not self.conn.connect():
            messagebox.showerror("Error", "Failed to connect to UR Controller.")
            return

        # Start recording
        while self.recording:
            data = [self.conn.get_time()]
            for col in self.columns[1:]:
                data.append(self.conn.get_data(col))
            self.data_buffer.append(data)

        # Disconnect from UR Controller
        self.conn.disconnect


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
