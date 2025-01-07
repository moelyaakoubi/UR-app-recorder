from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QWidget, QLabel, QLineEdit,
    QPushButton, QListWidget, QMessageBox,QFileDialog,QCheckBox,QDialog,QAction
)

from PyQt5.QtGui import QIcon,QPixmap

import threading
import time
import csv
import rtde_receive

class AboutDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("About")
        
        # Layout for About Dialog
        layout = QVBoxLayout()

        # Add a label with copyright info
        copyright_label = QLabel("Robot Data Recorder v0.1\n"
                                 "Created by student of UFR ST\n"
                                 "Evry Paris Saclay University\n"
                                 "This software is for data record of the UR")
        layout.addWidget(copyright_label)

        # Add Close Button
        close_button = QPushButton("Close")
        close_button.clicked.connect(self.close)
        layout.addWidget(close_button)

        self.setLayout(layout)

    def show_about_dialog(self):
        self.exec_()

class RobotDataRecorderApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("UR Robot Data Recorder V0.1")
        self.setGeometry(100, 100, 400, 300)

        # Set the icon for the window and taskbar
        self.setWindowIcon(QIcon("icon.png"))

        # Create About Dialog
        self.about_dialog = AboutDialog()

        # Add Menu Bar
        self.menu_bar = self.menuBar()
        self.create_menu()

        # Main layout
        self.layout = QVBoxLayout()

        # IP Address Input
        self.ip_label = QLabel("Enter Robot IP Address:")
        self.layout.addWidget(self.ip_label)

        self.ip_input = QLineEdit()
        self.ip_input.setPlaceholderText("e.g., 192.168.0.1")
        self.layout.addWidget(self.ip_input)

        # frequency Input
        self.freq_label = QLabel("Enter frequency of recording:")
        self.layout.addWidget(self.freq_label)

        self.freq_input = QLineEdit()
        self.freq_input.setPlaceholderText("e.g., 0.1")
        self.layout.addWidget(self.freq_input)

        # Data Type Selection
        self.data_label = QLabel("Select Data to Record:")
        self.layout.addWidget(self.data_label)

        # map of data
        self.data_functions = {
                    "Target Joint Positions": self.get_target_q,
                    "Target Joint Velocities": self.get_target_qd,
                    "Target Joint Accelerations": self.get_target_qdd,
                    "Target Joint Currents": self.get_target_current,
                    "Target Joint Moments": self.get_target_moment,
                    "Actual Joint Positions": self.get_actual_q,
                    "Actual Joint Velocities": self.get_actual_qd,
                    "Actual Joint Currents": self.get_actual_current,
                    "Joint Control Outputs": self.get_joint_control_output,
                    "Actual Tool Pose": self.get_actual_tcp_pose,
                    "Actual Tool Speed": self.get_actual_tcp_speed,
                    "Actual Tool Force": self.get_actual_tcp_force,
                    "Target Tool Pose": self.get_target_tcp_pose,
                    "Target Tool Speed": self.get_target_tcp_speed,
                    "Digital Inputs": self.get_actual_digital_input_bits,
                    "Digital Input State": self.get_digital_in_state,
                    "Tool Accelerometer": self.get_actual_tool_accelerometer,
                    "Speed Scaling": self.get_speed_scaling,
                    "Combined Speed Scaling": self.get_speed_scaling_combined,
                    "Momentum": self.get_actual_momentum,
                    "Main Voltage": self.get_actual_main_voltage,
                    "Robot Voltage": self.get_actual_robot_voltage,
                    "Robot Current": self.get_actual_robot_current,
                    "Actual Joint Voltages": self.get_actual_joint_voltage,
                    "Digital Outputs": self.get_actual_digital_output_bits,
                    "Digital Output State": self.get_digital_out_state,
                    "Program State": self.get_runtime_state,
                    "Analog Input 0": self.get_standard_analog_input0,
                    "Analog Input 1": self.get_standard_analog_input1,
                    "Analog Output 0": self.get_standard_analog_output0,
                    "Analog Output 1": self.get_standard_analog_output1,
                    "Protective Stop": self.is_protective_stopped,
                    "Emergency Stop": self.is_emergency_stopped,
                    "Output Integer Register": self.get_output_int_register,
                    "Output Double Register": self.get_output_double_register,
                    "Payload": self.get_payload,
                    "Payload Center of Gravity": self.get_payload_cog,
                    "Payload Inertia": self.get_payload_inertia,
                    "Raw Force and Torque": self.get_ft_raw_wrench
                    # Add more mappings as needed
                }

        # Select All checkbox
        self.select_all_checkbox = QCheckBox("Select All")
        self.select_all_checkbox.stateChanged.connect(self.toggle_select_all)
        #self.layout.addWidget(self.select_all_checkbox)

        self.data_list = QListWidget() 
        # Dynamically generate listbox items from the mapping
        self.data_list_items = list(self.data_functions.keys())

        # Add the items to the Listbox
        self.data_list.addItems(self.data_list_items)
        self.data_list.setSelectionMode(QListWidget.MultiSelection)
        self.layout.addWidget(self.data_list)

        # Buttons
        self.start_button = QPushButton("Start Recording")
        self.start_button.clicked.connect(self.start_recording)
        self.layout.addWidget(self.start_button)

        self.stop_button = QPushButton("Stop Recording")
        self.stop_button.setEnabled(False)
        self.stop_button.clicked.connect(self.stop_recording)
        self.layout.addWidget(self.stop_button)

        # Download Button
        self.download_button = QPushButton("Download CSV")
        self.download_button.setEnabled(False)
        self.download_button.clicked.connect(self.download_csv)
        self.layout.addWidget(self.download_button)

        # Status Label
        self.status_label = QLabel("Status: Idle")
        self.layout.addWidget(self.status_label)

        # Set main widget and layout
        container = QWidget()
        container.setLayout(self.layout)
        self.setCentralWidget(container)

        # Recorder variables
        self.is_recording = False
        self.data_log = []

        

    def toggle_select_all(self):
        # Select or deselect all items in the list based on checkbox state
        is_checked = self.select_all_checkbox.isChecked()
        for index in range(self.data_list.count()):
            item = self.data_list.item(index)
            item.setSelected(is_checked)

    def create_menu(self):
        # Create menu bar with "About" option
        menu = self.menu_bar.addMenu("Help")
        
        about_action = QAction("About", self)
        about_action.triggered.connect(self.about_dialog.show_about_dialog)
        menu.addAction(about_action)
       
    
    def get_target_q(self, rtde_r):
        return rtde_r.getTargetQ()

    def get_target_qd(self, rtde_r):
        return rtde_r.getTargetQd()

    def get_target_qdd(self, rtde_r):
        return rtde_r.getTargetQdd()

    def get_target_current(self, rtde_r):
        return rtde_r.getTargetCurrent()

    def get_target_moment(self, rtde_r):
        return rtde_r.getTargetMoment()

    def get_actual_q(self, rtde_r):
        return rtde_r.getActualQ()

    def get_actual_qd(self, rtde_r):
        return rtde_r.getActualQd()

    def get_actual_current(self, rtde_r):
        return rtde_r.getActualCurrent()

    def get_joint_control_output(self, rtde_r):
        return rtde_r.getJointControlOutput()

    def get_actual_tcp_pose(self, rtde_r):
        return rtde_r.getActualTCPPose()

    def get_actual_tcp_speed(self, rtde_r):
        return rtde_r.getActualTCPSpeed()

    def get_actual_tcp_force(self, rtde_r):
        return rtde_r.getActualTCPForce()

    def get_target_tcp_pose(self, rtde_r):
        return rtde_r.getTargetTCPPose()

    def get_target_tcp_speed(self, rtde_r):
        return rtde_r.getTargetTCPSpeed()

    def get_actual_digital_input_bits(self, rtde_r):
        return rtde_r.getActualDigitalInputBits()

    def get_digital_in_state(self, rtde_r, input_id):
        return rtde_r.getDigitalInState(input_id)

    def get_actual_tool_accelerometer(self, rtde_r):
        return rtde_r.getActualToolAccelerometer()

    def get_speed_scaling(self, rtde_r):
        return rtde_r.getSpeedScaling()

    def get_speed_scaling_combined(self, rtde_r):
        return rtde_r.getSpeedScalingCombined()

    def get_actual_momentum(self, rtde_r):
        return rtde_r.getActualMomentum()

    def get_actual_main_voltage(self, rtde_r):
        return rtde_r.getActualMainVoltage()

    def get_actual_robot_voltage(self, rtde_r):
        return rtde_r.getActualRobotVoltage()

    def get_actual_robot_current(self, rtde_r):
        return rtde_r.getActualRobotCurrent()

    def get_actual_joint_voltage(self, rtde_r):
        return rtde_r.getActualJointVoltage()

    def get_actual_digital_output_bits(self, rtde_r):
        return rtde_r.getActualDigitalOutputBits()

    def get_digital_out_state(self, rtde_r, output_id):
        return rtde_r.getDigitalOutState(output_id)

    def get_runtime_state(self, rtde_r):
        return rtde_r.getRuntimeState()

    def get_standard_analog_input0(self, rtde_r):
        return rtde_r.getStandardAnalogInput0()

    def get_standard_analog_input1(self, rtde_r):
        return rtde_r.getStandardAnalogInput1()

    def get_standard_analog_output0(self, rtde_r):
        return rtde_r.getStandardAnalogOutput0()

    def get_standard_analog_output1(self, rtde_r):
        return rtde_r.getStandardAnalogOutput1()

    def is_protective_stopped(self, rtde_r):
        return rtde_r.isProtectiveStopped()

    def is_emergency_stopped(self, rtde_r):
        return rtde_r.isEmergencyStopped()

    def get_output_int_register(self, rtde_r, output_id):
        return rtde_r.getOutputIntRegister(output_id)

    def get_output_double_register(self, rtde_r, output_id):
        return rtde_r.getOutputDoubleRegister(output_id)

    def get_payload(self, rtde_r):
        return rtde_r.getPayload()

    def get_payload_cog(self, rtde_r):
        return rtde_r.getPayloadCog()

    def get_payload_inertia(self, rtde_r):
        return rtde_r.getPayloadInertia()

    def get_ft_raw_wrench(self, rtde_r):
        return rtde_r.getFtRawWrench()

    #---------------------------------------------



    def start_recording(self):
        ip = self.ip_input.text()
        freq=float(self.freq_input.text())
        if not ip:
            QMessageBox.warning(self, "Error", "Please enter a valid IP address.")
            return

        selected_data = [item.text() for item in self.data_list.selectedItems()]
        if not selected_data:
            QMessageBox.warning(self, "Error", "Please select at least one data type to record.")
            return

        # Clear the previous data log
        self.data_log = []

        # Initialize the CSV file with headers
        fieldnames = ["timestamp"] + selected_data
        with open("recorded_data.csv", "w", newline="") as file:
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writeheader()

        self.is_recording = True
        self.status_label.setText(f"Status: Recording data from {ip}")
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)

        # Start recording in a separate thread
        threading.Thread(target=self.record_data, args=(ip, selected_data,freq), daemon=True).start()


    def stop_recording(self):
        self.is_recording = False
        self.status_label.setText("Status: Stopped")
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)

        # Save recorded data
        if self.data_log:
            self.save_data_to_file()
            QMessageBox.information(self, "Data Saved", "Recorded data has been saved to 'recorded_data.csv'.")
            self.download_button.setEnabled(True)  # Enable the download button after stopping


    def record_data(self, ip, selected_data,freq):
        try:
            # Connect to the robot
            rtde_r = rtde_receive.RTDEReceiveInterface(ip)
            start_time = time.time()

            while self.is_recording:
                data_point = {"timestamp": time.time() - start_time}

                # Loop through selected data types and call the corresponding function
                for data_type in selected_data:
                    if data_type in self.data_functions:
                        data_point[data_type] = self.data_functions[data_type](rtde_r)

                # Add the recorded data to the log
                self.data_log.append(data_point)
                print(data_point)  # For debugging
                time.sleep(freq)  # Adjust the interval for data recording

        except Exception as e:
            QMessageBox.critical(self, "Error", f"An error occurred while recording: {e}")
            self.is_recording = False
    

    def save_data_to_file(self, file_name="recorded_data.csv"):
        if not self.data_log:
            return

        headers = ["timestamp"]

        # Use a set to track added headers and avoid duplicates
        added_headers = set(headers)

        # Collect headers in the order they appear in the data_log
        for row in self.data_log:
            for key, value in row.items():
                if key != "timestamp":
                    if isinstance(value, list):
                        for i in range(len(value)):
                            new_header = f"{key}_{i}"
                            if new_header not in added_headers:
                                headers.append(new_header)
                                added_headers.add(new_header)
                    elif key not in added_headers:
                        headers.append(key)
                        added_headers.add(key)

        # Write the data to a CSV file
        with open(file_name, "w", newline="") as file:
            writer = csv.DictWriter(file, fieldnames=headers)
            writer.writeheader()

            for row in self.data_log:
                row_data = {"timestamp": row["timestamp"]}  # Keep timestamp as a numeric value

                for key, value in row.items():
                    if key == "timestamp":
                        continue
                    if isinstance(value, list):
                        for i in range(len(value)):
                            row_data[f"{key}_{i}"] = value[i]  # Keep list values as numeric
                    else:
                        row_data[key] = value  # Keep other values as is (no additional quotes)

                writer.writerow(row_data)

    def download_csv(self):
        # Open a file dialog to choose the destination folder and filename
        options = QFileDialog.Options()
        file_name, _ = QFileDialog.getSaveFileName(self, "Save CSV File", "recorded_data.csv", "CSV Files (*.csv)", options=options)

        if file_name:
            # Save the data to the chosen location
            try:
                self.save_data_to_file(file_name)  # Pass the file name to the save function
                QMessageBox.information(self, "File Saved", f"CSV file has been saved to {file_name}.")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"An error occurred: {e}")


# Run the application
if __name__ == "__main__":
    app = QApplication([])
    window = RobotDataRecorderApp()
    window.show()
    app.exec_()
