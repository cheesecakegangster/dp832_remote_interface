import tkinter as tk
from tkinter import messagebox
from threading import Thread
import os
import sys
import time

# Adjust the sys.path to include the dp832 and find_instrument modules
path = os.path.join('..', '..', 'python-flexsollib.git', '.')
p = os.path.abspath(path)
sys.path.insert(1, p)

import dp832
import find_instrument  # Import the module that contains find_devices_by_pattern


class ChannelFrame(tk.Frame):
    def __init__(self, master, channel_number, color, voltage_range, current_range, instrument):
        super().__init__(master, bg="black", padx=10, pady=10)

        self.color = color
        self.channel_number = channel_number
        self.instrument = instrument
        self.voltage_range = voltage_range
        self.current_range = current_range
        self.channel_enabled = False
        self.voltage_limit_enabled = False
        self.current_limit_enabled = False
        self.refresh_rate = 2
        self.refresh_thread = None
        self.refresh_active = False

        self.ovp_ocp_monitor_thread = None
        self.monitor_ovp_ocp = False  # Flag to indicate if we should monitor OVP/OCP

        # Full row background label (Row 1)
        self.row_1_full_bg = tk.Frame(self, bg="black", height=30)
        self.row_1_full_bg.grid(row=0, column=0, columnspan=4, sticky="we")

        # Row 1: CH number and regulation state (CV in top right)
        self.row_1_label_left = tk.Label(self, text=f"CH {channel_number}: OFF", font=("Courier", 14, "bold"), fg=color,
                                         bg="black")
        self.row_1_label_left.grid(row=0, column=0, sticky="w", padx=10)

        self.row_1_label_right = tk.Label(self, text="CV", font=("Courier", 14, "bold"), fg=color, bg="black")
        self.row_1_label_right.grid(row=0, column=3, sticky="e", padx=10)

        # Divider between row 1 and row 2
        self.divider_line1 = tk.Frame(self, height=2, bg=color)
        self.divider_line1.grid(row=1, column=0, columnspan=4, sticky="we", padx=5, pady=5)

        # Row 2: Voltage Display (00.000 V)
        self.voltage_display = tk.Label(self, text="00.000 V", font=("Courier", 24, "bold"), fg="black", bg="black")
        self.voltage_display.grid(row=2, column=0, columnspan=4, sticky="e", padx=10)

        # Row 3: Current Display (0.000 A)
        self.current_display = tk.Label(self, text="0.000 A", font=("Courier", 24, "bold"), fg="black", bg="black")
        self.current_display.grid(row=3, column=0, columnspan=4, sticky="e", padx=10)

        # Row 4: Power Display (00.000 W)
        self.power_display = tk.Label(self, text="00.000 W", font=("Courier", 24, "bold"), fg="black", bg="black")
        self.power_display.grid(row=4, column=0, columnspan=4, sticky="e", padx=10)

        # Divider between row 4 and row 5
        self.divider_line2 = tk.Frame(self, height=2, bg=color)
        self.divider_line2.grid(row=5, column=0, columnspan=4, sticky="we", padx=5, pady=5)

        # Row 5: Set and Limit Table
        self.create_set_limit_table()

    def initialize_from_settings(self, settings):
        """ Initialize channel labels with the given settings. """
        self.set_voltage_label.config(text=f"{settings['voltage']:06.3f} V")
        self.set_current_label.config(text=f"{settings['current']:.3f} A")
        self.voltage_limit_label.config(text=f"{settings['voltage_limit']:06.3f} V")
        self.current_limit_label.config(text=f"{settings['current_limit']:.3f} A")

        # Synchronize output state at startup
        output_state = dp832.get_output_state(self.instrument, [self.channel_number])
        if output_state[f'CH{self.channel_number}'] == "ON":
            self.channel_enabled = True
            self.update_channel_state()
            self.start_refresh()

    def create_set_limit_table(self):
        table_frame = tk.Frame(self, bg="black")
        table_frame.grid(row=6, column=0, columnspan=4, padx=10, pady=10)

        # Header Row: Set | Limit
        set_label = tk.Label(table_frame, text="Set", font=("Courier", 12, "bold"), fg=self.color, bg="black")
        set_label.grid(row=0, column=0, padx=10, pady=5)

        limit_label = tk.Label(table_frame, text="Limit", font=("Courier", 12, "bold"), fg=self.color, bg="black")
        limit_label.grid(row=0, column=1, padx=10, pady=5)

        # Divider between Set and Limit columns
        self.divider_column = tk.Frame(table_frame, width=2, bg=self.color)
        self.divider_column.grid(row=0, column=1, rowspan=3, padx=5)

        # Row 2: Set Voltage | Voltage Limit
        self.set_voltage_label = tk.Label(table_frame, text="00.000 V", font=("Courier", 16, "bold"), fg=self.color,
                                          bg="black")
        self.set_voltage_label.grid(row=1, column=0, padx=10, pady=5, sticky="e")

        self.voltage_limit_label = tk.Label(table_frame, text="00.000 V", font=("Courier", 16, "bold"), fg="darkgray",
                                            bg="black")
        self.voltage_limit_label.grid(row=1, column=1, padx=10, pady=5, sticky="e")

        # Row 3: Set Current | Current Limit
        self.set_current_label = tk.Label(table_frame, text="0.000 A", font=("Courier", 16, "bold"), fg=self.color,
                                          bg="black")
        self.set_current_label.grid(row=2, column=0, padx=10, pady=5, sticky="e")

        self.current_limit_label = tk.Label(table_frame, text="0.000 A", font=("Courier", 16, "bold"), fg="darkgray",
                                            bg="black")
        self.current_limit_label.grid(row=2, column=1, padx=10, pady=5, sticky="e")

    def create_set_fields(self, btn_frame, row, col, label_text, param_type, value_range):
        # Create smaller text input fields and descriptions
        label = tk.Label(btn_frame, text=label_text, font=("Courier", 10), bg="#ebeaea")
        label.grid(row=row, column=col, padx=2, pady=2, sticky="w")

        entry = tk.Entry(btn_frame, width=8, font=("Courier", 10))
        entry.grid(row=row, column=col + 1, padx=2, pady=2)

        set_button = tk.Button(btn_frame, text="Set", command=lambda: self.set_value(entry, value_range, label_text),
                               width=8, bg="#757a82", fg="white")
        set_button.grid(row=row, column=col + 2, padx=2, pady=2)

    def start_refresh(self):
        if not self.refresh_active:
            self.refresh_active = True
            self.refresh_thread = Thread(target=self.refresh_loop)
            self.refresh_thread.start()

    def stop_refresh(self):
        self.refresh_active = False
        self.monitor_ovp_ocp = False  # Stop monitoring OVP/OCP

        if self.refresh_thread:
            self.refresh_thread.join()

        if self.ovp_ocp_monitor_thread:
            self.ovp_ocp_monitor_thread.join()

    def refresh_loop(self):
        while self.refresh_active:
            try:
                measurements = dp832.measure_all(self.instrument, [self.channel_number])
                voltage = measurements[self.channel_number]['voltage']
                current = measurements[self.channel_number]['current']
                power = measurements[self.channel_number]['power']

                # Query regulation mode
                regulation_mode = dp832.get_regulation_mode(self.instrument, [self.channel_number])
                reg_mode = regulation_mode[f'CH{self.channel_number}']

                # Safely update the UI in the main thread
                self.after(0, self.update_measurements, voltage, current, power, reg_mode)

            except Exception as e:
                self.after(0, self.display_error, str(e))
            time.sleep(1 / self.refresh_rate)

    def update_measurements(self, voltage, current, power, reg_mode):
        self.voltage_display.config(text=f"{voltage:06.3f} V")
        self.current_display.config(text=f"{current:.3f} A")
        self.power_display.config(text=f"{power:.3f} W")
        self.row_1_label_right.config(text=reg_mode)

    def toggle_channel(self):
        Thread(target=self._toggle_channel_task).start()

    def _toggle_channel_task(self):
        try:
            success = dp832.set_channel_output_state(self.instrument, [self.channel_number],
                                                     "ON" if not self.channel_enabled else "OFF")
            if success:
                self.channel_enabled = not self.channel_enabled
                self.after(0, self.update_channel_state)
                self.after(0, self.update_button_state)
                self.after(0, self.clear_error)
                if self.channel_enabled:
                    self.start_refresh()
                    self.monitor_ovp_ocp = True
                    self.ovp_ocp_monitor_thread = Thread(target=self.monitor_ovp_ocp_status)
                    self.ovp_ocp_monitor_thread.start()
                else:
                    self.stop_refresh()
            else:
                self.after(0, self.display_error, f"Failed to toggle output for Channel {self.channel_number}")
        except Exception as e:
            self.after(0, self.display_error, str(e))

    def monitor_ovp_ocp_status(self):
        """ Monitor OVP/OCP status periodically for this channel. """
        while self.monitor_ovp_ocp:
            try:
                if self.voltage_limit_enabled or self.current_limit_enabled:
                    # Query OVP/OCP status for this channel
                    if self.voltage_limit_enabled:
                        ovp_status = dp832.get_ovp_status(self.instrument, [self.channel_number])
                        if ovp_status[f'CH{self.channel_number}'] == "YES":
                            self.after(0, self.display_error, f"OVP triggered for CH {self.channel_number}")

                    if self.current_limit_enabled:
                        ocp_status = dp832.get_ocp_status(self.instrument, [self.channel_number])
                        if ocp_status[f'CH{self.channel_number}'] == "YES":
                            self.after(0, self.display_error, f"OCP triggered for CH {self.channel_number}")

            except Exception as e:
                self.after(0, self.display_error, str(e))

            time.sleep(1)

    def display_error(self, message):
        self.error_label.config(text=message)

    def toggle_voltage_limit(self):
        Thread(target=self._toggle_voltage_limit_task).start()

    def _toggle_voltage_limit_task(self):
        try:
            state = "ON" if not self.voltage_limit_enabled else "OFF"
            success = dp832.set_ovp_state(self.instrument, [self.channel_number], state)
            if success:
                self.voltage_limit_enabled = not self.voltage_limit_enabled
                self.after(0, self.update_voltage_limit)
                self.after(0, self.update_button_state)
                self.after(0, self.clear_error)
            else:
                self.after(0, self.display_error,
                           f"Failed to toggle voltage limit (OVP) for Channel {self.channel_number}")
        except Exception as e:
            self.after(0, self.display_error, str(e))

    def toggle_current_limit(self):
        Thread(target=self._toggle_current_limit_task).start()

    def _toggle_current_limit_task(self):
        try:
            state = "ON" if not self.current_limit_enabled else "OFF"
            success = dp832.set_ocp_state(self.instrument, [self.channel_number], state)
            if success:
                self.current_limit_enabled = not self.current_limit_enabled
                self.after(0, self.update_current_limit)
                self.after(0, self.update_button_state)
                self.after(0, self.clear_error)
            else:
                self.after(0, self.display_error,
                           f"Failed to toggle current limit (OCP) for Channel {self.channel_number}")
        except Exception as e:
            self.after(0, self.display_error, str(e))

    def set_value(self, entry, value_range, label_text):
        Thread(target=self._set_value_task, args=(entry, value_range, label_text)).start()

    def _set_value_task(self, entry, value_range, label_text):
        try:
            value = float(entry.get())
            if value_range[0] <= value <= value_range[1]:
                if "Voltage" in label_text and "Limit" not in label_text:
                    success = dp832.configure_voltage(self.instrument, [self.channel_number], value)
                elif "Current" in label_text and "Limit" not in label_text:
                    success = dp832.configure_current(self.instrument, [self.channel_number], value)
                elif "Voltage Limit" in label_text:
                    success = dp832.configure_voltage_limit(self.instrument, [self.channel_number], value)
                elif "Current Limit" in label_text:
                    success = dp832.configure_current_limit(self.instrument, [self.channel_number], value)

                if success:
                    self.after(0, self.update_set_value_label, label_text, value)
                else:
                    self.after(0, self.display_error, f"Failed to set {label_text}")
            else:
                self.after(0, self.display_error,
                           f"{label_text.split()[1]} must be between {value_range[0]:.3f} - {value_range[1]:.3f}")
        except ValueError:
            self.after(0, self.display_error, f"Invalid input for {label_text.split()[1]}")

    def update_set_value_label(self, label_text, value):
        if "Voltage" in label_text and "Limit" not in label_text:
            formatted_value = f"{value:06.3f}"
            self.set_voltage_label.config(text=f"{formatted_value} V")
        elif "Current" in label_text and "Limit" not in label_text:
            formatted_value = f"{value:.3f}"
            self.set_current_label.config(text=f"{formatted_value} A")
        elif "Voltage Limit" in label_text:
            formatted_value = f"{value:06.3f}"  # Keep leading zero for voltage limit
            self.voltage_limit_label.config(text=f"{formatted_value} V")
        elif "Current Limit" in label_text:
            formatted_value = f"{value:.3f}"
            self.current_limit_label.config(text=f"{formatted_value} A")

    def clear_error(self):
        self.error_label.config(text="")

    def update_channel_state(self):
        if self.channel_enabled:
            self.row_1_label_left.config(bg=self.color, fg="black", text=f"CH {self.channel_number}: ON")
            self.row_1_label_right.config(bg=self.color, fg="black")
            self.voltage_display.config(fg=self.color, bg="black")
            self.current_display.config(fg=self.color, bg="black")
            self.power_display.config(fg=self.color, bg="black")
        else:
            self.row_1_label_left.config(bg="black", fg=self.color, text=f"CH {self.channel_number}: OFF")
            self.row_1_label_right.config(bg="black", fg=self.color)
            self.voltage_display.config(fg="black", bg="black")
            self.current_display.config(fg="black", bg="black")
            self.power_display.config(fg="black", bg="black")

    def update_voltage_limit(self):
        if self.voltage_limit_enabled:
            self.voltage_limit_label.config(fg=self.color)
        else:
            self.voltage_limit_label.config(fg="darkgray")

    def update_current_limit(self):
        if self.current_limit_enabled:
            self.current_limit_label.config(fg=self.color)
        else:
            self.current_limit_label.config(fg="darkgray")

    def update_button_state(self):
        if self.channel_enabled:
            self.toggle_channel_btn.config(bg="#8dce7e")
        else:
            self.toggle_channel_btn.config(bg="#757a82")

        if self.voltage_limit_enabled:
            self.toggle_voltage_limit_btn.config(bg="#8dce7e")
        else:
            self.toggle_voltage_limit_btn.config(bg="#757a82")

        if self.current_limit_enabled:
            self.toggle_current_limit_btn.config(bg="#8dce7e")
        else:
            self.toggle_current_limit_btn.config(bg="#757a82")


class PowerSupplyControl(tk.Tk):
    def __init__(self, device):
        super().__init__()

        self.title("Power Supply Control")
        self.configure(bg="#ebeaea")
        self.geometry("1063x683")
        self.minsize(1063, 683)

        self.device = device

        # Get the current channel settings
        channel_settings = dp832.get_channel_settings(self.device, [1, 2, 3])

        channels_frame = tk.Frame(self, bg="black", bd=2, relief="ridge")
        channels_frame.grid(row=0, column=0, columnspan=5, padx=20, pady=20)

        # Initialize channel 1 with the settings
        self.channel_1_frame = ChannelFrame(
            channels_frame, channel_number=1, color="yellow",
            voltage_range=(0.0, 32.0), current_range=(0.0, 3.2),
            instrument=self.device
        )
        self.channel_1_frame.grid(row=0, column=0, padx=20, pady=10)
        self.channel_1_frame.initialize_from_settings(channel_settings[1])

        # Initialize channel 2 with the settings
        self.channel_2_frame = ChannelFrame(
            channels_frame, channel_number=2, color="cyan",
            voltage_range=(0.0, 32.0), current_range=(0.0, 3.2),
            instrument=self.device
        )
        self.channel_2_frame.grid(row=0, column=2, padx=20, pady=10)
        self.channel_2_frame.initialize_from_settings(channel_settings[2])

        # Initialize channel 3 with the settings
        self.channel_3_frame = ChannelFrame(
            channels_frame, channel_number=3, color="magenta",
            voltage_range=(0.0, 5.3), current_range=(0.0, 3.2),
            instrument=self.device
        )
        self.channel_3_frame.grid(row=0, column=4, padx=20, pady=10)
        self.channel_3_frame.initialize_from_settings(channel_settings[3])

        self.create_channel_controls(1, self.channel_1_frame)
        self.create_channel_controls(2, self.channel_2_frame)
        self.create_channel_controls(3, self.channel_3_frame)

        self.add_vertical_lines()

    def create_channel_controls(self, channel_number, channel_frame):
        btn_frame = tk.Frame(self, bg="#ebeaea")
        btn_frame.grid(row=1, column=(channel_number * 2) - 2, padx=5, pady=10)

        toggle_channel_btn = tk.Button(btn_frame, text="Toggle Output", command=channel_frame.toggle_channel,
                                       fg="white", bg="#757a82", width=15)
        toggle_channel_btn.grid(row=0, column=0, padx=2, pady=2)
        channel_frame.toggle_channel_btn = toggle_channel_btn

        toggle_voltage_limit_btn = tk.Button(btn_frame, text="Toggle Voltage Limit",
                                             command=channel_frame.toggle_voltage_limit, fg="white", bg="#757a82",
                                             width=15)
        toggle_voltage_limit_btn.grid(row=1, column=0, padx=2, pady=2)
        channel_frame.toggle_voltage_limit_btn = toggle_voltage_limit_btn

        toggle_current_limit_btn = tk.Button(btn_frame, text="Toggle Current Limit",
                                             command=channel_frame.toggle_current_limit, fg="white", bg="#757a82",
                                             width=15)
        toggle_current_limit_btn.grid(row=2, column=0, padx=2, pady=2)
        channel_frame.toggle_current_limit_btn = toggle_current_limit_btn

        btn_frame.grid_rowconfigure(3, minsize=10)

        channel_frame.create_set_fields(btn_frame, row=4, col=0, label_text="Set Voltage (V)", param_type="voltage",
                                        value_range=channel_frame.voltage_range)
        channel_frame.create_set_fields(btn_frame, row=6, col=0, label_text="Set Current (A)", param_type="current",
                                        value_range=channel_frame.current_range)
        channel_frame.create_set_fields(btn_frame, row=8, col=0, label_text="Voltage Limit (V)",
                                        param_type="voltage_limit", value_range=channel_frame.voltage_range)
        channel_frame.create_set_fields(btn_frame, row=10, col=0, label_text="Current Limit (A)",
                                        param_type="current_limit", value_range=channel_frame.current_range)

        error_label = tk.Label(btn_frame, text="", font=("Courier", 10), fg="red", bg="#ebeaea", wraplength=250,
                               justify="left", height=2)
        error_label.grid(row=11, column=0, columnspan=3, pady=5)
        channel_frame.error_label = error_label

    def add_vertical_lines(self):
        line1 = tk.Frame(self, width=2, height=100, bg="black")
        line1.grid(row=1, column=1, rowspan=1, padx=5, pady=5)

        line2 = tk.Frame(self, width=2, height=100, bg="black")
        line2.grid(row=1, column=3, rowspan=1, padx=5, pady=5)


class DeviceSelection(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("Select Power Supply Device")
        self.geometry("600x300")  # Increased window size for a larger listbox
        self.device_selected = None

        self.label = tk.Label(self, text="Select a DP8 Power Supply Device:", font=("Arial", 12))
        self.label.pack(pady=10)

        # Make the listbox wider by increasing the width attribute
        self.device_listbox = tk.Listbox(self, height=10, width=80)  # Increased width for better display
        self.device_listbox.pack(padx=20, pady=10)

        self.connect_button = tk.Button(self, text="Connect", command=self.connect_device, width=20)
        self.connect_button.pack(pady=10)

        self.populate_device_list()

    def populate_device_list(self):
        devices = find_instrument.find_devices_by_pattern("DP8")
        for device in devices:
            self.device_listbox.insert(tk.END, device)

    def connect_device(self):
        try:
            selected_index = self.device_listbox.curselection()[0]
            self.device_selected = self.device_listbox.get(selected_index)
            self.destroy()
        except IndexError:
            messagebox.showerror("Error", "Please select a device before connecting.")


if __name__ == "__main__":
    # Step 1: Show the device selection dialog first
    device_selection_app = DeviceSelection()
    device_selection_app.mainloop()

    if device_selection_app.device_selected:
        # Step 2: Launch the main control GUI with the selected device
        app = PowerSupplyControl(device_selection_app.device_selected)
        app.mainloop()
