import sys
import pyvisa as visa
import colorama
from colorama import Fore, Style

rm = visa.ResourceManager()  # assign resource manager to rm
instrument_tuple = rm.list_resources()
colorama.init(autoreset=True)


def set_channel_output_state(dp8_instrument_id: str, channels: list, state: str):
    psu = rm.open_resource(dp8_instrument_id)

    if state not in ['ON', 'OFF']:
        print(f"{Fore.RED}Error: Tried to set DP832 channel output with ID {dp8_instrument_id} to unsupported value: {state} - accepted values are ['ON' | 'OFF'] (str)")
        return False

    for channel in channels:
        if channel not in [1, 2, 3]:
            print(f"{Fore.RED}Error: Tried to configure an invalid channel of DP832 with ID {dp8_instrument_id}: CH{channel} - accepted values are 1, 2 or 3")
            return False
        psu.write(f":OUTP CH{channel},{state}")
        reply = psu.query(f":OUTP? CH{channel}")
        if reply == f"{state}\n":
            print(f"Configured DP832 power supply output CH{channel} to {state}")
        else:
            print(f"{Fore.RED}Error: Failed to set DP832 channel CH{channel} state to {state}")
            return False

    psu.close()
    return True
    

def set_ovp_state(dp8_instrument_id: str, channels: list, state: str):
    psu = rm.open_resource(dp8_instrument_id)

    if state not in ['ON', 'OFF']:
        print(f"{Fore.RED}Error: Tried to set DP832 channel OVP with ID {dp8_instrument_id} to unsupported value: {state} - accepted values are ['ON' | 'OFF'] (str)")
        return False

    for channel in channels:
        if channel not in [1, 2, 3]:
            print(f"{Fore.RED}Error: Tried to configure OVP of an invalid channel of DP832 with ID {dp8_instrument_id}: CH{channel} - accepted values are 1, 2 or 3")
            return False
        psu.write(f":SOURce[{channel}]:VOLT:PROT:STAT {state}")
        reply = psu.query(f":SOURce[{channel}]:VOLT:PROT:STAT?")
        if reply == f"{state}\n":
            print(f"Configured DP832 power supply OCP on CH {channel} to {state}")
        else:
            print(f"{Fore.RED}Error: Failed to set DP832 OCP on CH{channel} state to {state}")
            return False
            
    psu.close()
    return True
    
    
def set_ocp_state(dp8_instrument_id: str, channels: list, state: str):
    psu = rm.open_resource(dp8_instrument_id)

    if state not in ['ON', 'OFF']:
        print(f"{Fore.RED}Error: Tried to set DP832 channel OCP with ID {dp8_instrument_id} to unsupported value: {state} - accepted values are ['ON' | 'OFF'] (str)")
        return False

    for channel in channels:
        if channel not in [1, 2, 3]:
            print(f"{Fore.RED}Error: Tried to configure OCP of an invalid channel of DP832 with ID {dp8_instrument_id}: CH{channel} - accepted values are 1, 2 or 3")
            return False
        psu.write(f":SOURce[{channel}]:CURR:PROT:STAT {state}")
        reply = psu.query(f":SOURce[{channel}]:CURR:PROT:STAT?")
        if reply == f"{state}\n":
            print(f"Configured DP832 power supply OCP on CH {channel} to {state}")
        else:
            print(f"{Fore.RED}Error: Failed to set DP832 OCP on CH{channel} state to {state}")
            return False

    psu.close()
    return True


def get_channel_settings(dp8_instrument_id: str, channels: list):
    psu = rm.open_resource(dp8_instrument_id)
    channel_settings_dict = {}

    for channel in channels:
        if channel not in [1, 2, 3]:
            print(f"{Fore.RED}Error: Invalid channel {channel}.")
            return False

        # Query channel settings and process the response
        reply = psu.query(f":APPL? CH{channel}").strip()
        channel_settings = reply.split(',')

        # Store settings in the dictionary
        channel_settings_dict[channel] = {
            "voltage": float(channel_settings[1]),
            "current": float(channel_settings[2]),
            "voltage_limit": float(psu.query(f":OUTP:OVP:VAL? CH{channel}").strip()),
            "current_limit": float(psu.query(f":OUTP:OCP:VAL? CH{channel}").strip())
        }
    
    psu.close()
    return channel_settings_dict


def configure_voltage(dp8_instrument_id: str, channels: list, voltage: float):
    psu = rm.open_resource(dp8_instrument_id)
    
    for channel in channels:
        if channel not in [1, 2, 3]:
            print(f"{Fore.RED}Error: Invalid channel {channel}.")
            return False
        if channel in [1, 2] and not 0 <= voltage <= 32.000:
            print(f"{Fore.RED}Error: Voltage for CH{channel} is outside the 0.000 - 32.000 V range.")
            return False
        if channel == 3 and not 0 <= voltage <= 5.300:
            print(f"{Fore.RED}Error: Voltage for CH3 is outside the 0.000 - 5.300 V range.")
            return False

        # configure channel
        psu.write(f":APPL CH{channel}, {voltage:.3f}")
        reply = psu.query(f":APPL? CH{channel}")

        valid_reply_ch1_ch2_dp832a = f"CH{channel}:30V/3A,{voltage:.3f}"
        valid_reply_ch1_ch2_dp832 = f"CH{channel}:30V/3A,{voltage:.2f}"

        valid_reply_ch3_dp832a = f"CH{channel}:5V/3A,{voltage:.3f}"
        valid_reply_ch3_dp832 = f"CH{channel}:5V/3A,{voltage:.2f}"

        if channel in [1, 2]:
            if valid_reply_ch1_ch2_dp832a in reply or valid_reply_ch1_ch2_dp832 in reply:
                print(f"Configured DP832 CH{channel} to {voltage:.3f} V")
            else:
                print(f"{Fore.RED}Error: Configuration for DP832(A) channel CH{channel} failed. Expected part of {valid_reply_ch1_ch2_dp832a} or {valid_reply_ch1_ch2_dp832}, got {reply}")
                return False
        elif channel == 3:
            if valid_reply_ch3_dp832a in reply or valid_reply_ch3_dp832 in reply:
                print(f"Configured DP832 CH{channel} to {voltage:.3f} V")
            else:
                print(f"{Fore.RED}Error: Configuration for DP832(A) channel CH{channel} failed. Expected part of {valid_reply_ch3_dp832a} or {valid_reply_ch3_dp832}, got {reply}")
                return False

    psu.close()
    return True
    

def configure_current(dp8_instrument_id: str, channels: list, current: float):
    psu = rm.open_resource(dp8_instrument_id)
    
    print(f"tryna set CH {channels} to {current:.3f}")
    
    for channel in channels:
        if channel not in [1, 2, 3]:
            print(f"{Fore.RED}Error: Invalid channel {channel}.")
            return False
        if not 0 <= current <= 3.200:
            print(f"{Fore.RED}Error: Current for CH{channel} is outside the 0.000 - 3.200 A range.")
            return False
            
        # configure channel
        psu.write(f":SOURce[{channel}]:CURR {current}")
        reply = psu.query(f":SOURce[{channel}]:CURR?")

        if current == float(reply.strip()):
            print(f"Configured DP832 CH{channel} to {current:.3f} A")
        else:
            print(f"{Fore.RED}Error: Configuration for DP832(A) channel CH{channel} failed. Expected reply {current}, got {reply}")
            return False

    psu.close()
    return True


def configure_voltage_limit(dp8_instrument_id: str, channels: list, voltage_limit: float):
    psu = rm.open_resource(dp8_instrument_id)

    for channel in channels:
        if channel not in [1, 2, 3]:
            print(f"{Fore.RED}Error: Invalid channel {channel}.")
            return False

        # Ensure that the correct voltage limit range is enforced per channel
        if channel in [1, 2] and not 0 <= voltage_limit <= 32.000:
            print(f"{Fore.RED}Error: Voltage limit for CH{channel} is outside the 0.000 - 32.000 V range.")
            return False
        if channel == 3 and not 0 <= voltage_limit <= 5.300:
            print(f"{Fore.RED}Error: Voltage limit for CH3 is outside the 0.000 - 5.300 V range.")
            return False

        try:
            # Set voltage protection for the correct channel using explicit formatting
            psu.write(f":OUTP:OVP:VAL CH{channel},{voltage_limit:.3f}") 
        
            # Verify the voltage limit was correctly set by querying the channel again
            reply = psu.query(f":OUTP:OVP:VAL? CH{channel}")
            
            if abs(float(reply.strip()) - voltage_limit) < 1e-3:
                print(f"Voltage limit successfully set to {voltage_limit:.3f} V on CH{channel}")
            else:
                print(f"{Fore.RED}Error: Failed to verify voltage limit on CH{channel}. Expected {voltage_limit:.3f}, got {reply}")
                return False

        except Exception as e:
            print(f"{Fore.RED}Exception occurred while setting voltage limit on CH{channel}: {str(e)}")
            return False

    psu.close()
    return True


def configure_current_limit(dp8_instrument_id: str, channels: list, current_limit: float):
    psu = rm.open_resource(dp8_instrument_id)

    for channel in channels:
        if channel not in [1, 2, 3]:
            print(f"{Fore.RED}Error: Invalid channel {channel}.")
            return False
        if not 0 <= current_limit <= 3.200:
            print(f"{Fore.RED}Error: Current limit for CH{channel} is outside the 0.000 - 3.200 A range.")
            return False

        try:
            # Set current protection for the correct channel using explicit formatting
            psu.write(f":OUTP:OCP:VAL CH{channel},{current_limit:.3f}") 
        
            # Verify the current limit was correctly set by querying the channel again
            reply = psu.query(f":OUTP:OCP:VAL? CH{channel}")
            
            if abs(float(reply.strip()) - current_limit) < 1e-3:
                print(f"Current limit successfully set to {current_limit:.3f} A on CH{channel}")
            else:
                print(f"{Fore.RED}Error: Failed to verify current limit on CH{channel}. Expected {current_limit:.3f}, got {reply}")
                return False

        except Exception as e:
            print(f"{Fore.RED}Exception occurred while setting current limit on CH{channel}: {str(e)}")
            return False
        
    psu.close()
    return True


def configure_channel_static(dp8_instrument_id: str, channels: list, voltage: float, current: float):
    psu = rm.open_resource(dp8_instrument_id)

    for channel in channels:
        # perform input check
        if channel not in [1, 2, 3]:
            print(f"{Fore.RED}Error: Tried to configure an invalid channel of DP832 with ID {dp8_instrument_id}: CH{channel} - accepted values are ['CH1' | 'CH2' | 'CH3'] (str) ")
            return False
        if not 0 <= voltage <= 32.000:
            print(f"{Fore.RED}Error: Attempted to set voltage of DP832 channel CH{channel} to {voltage:.3f} V, which is outside of the allowable range of 0.000 - 32.000 V")
            return False
        if not 0 <= current <= 3.200:
            print(f"{Fore.RED}Error: Attempted to set current of DP832 channel CH{channel} to {current:.3f} A, which is outside of the allowable range of 0.000 - 3.200 A")
            return False

        # configure channel
        psu.write(f":APPL CH{channel}, {voltage:.3f}, {current:.3f}")
        reply = psu.query(f":APPL? CH{channel}")

        valid_reply_ch1_ch2_dp832a = f"CH{channel}:30V/3A,{voltage:.3f},{current:.3f}\n"
        valid_reply_ch1_ch2_dp832 = f"CH{channel}:30V/3A,{voltage:.2f},{current:.3f}\n"

        valid_reply_ch3_dp832a = f"CH{channel}:5V/3A,{voltage:.3f},{current:.3f}\n"
        valid_reply_ch3_dp832 = f"CH{channel}:5V/3A,{voltage:.2f},{current:.3f}\n"

        if channel in [1, 2]:
            if reply == valid_reply_ch1_ch2_dp832a:
                print(f"Configured DP832A CH{channel} to {voltage:.3f} V, {current:.3f} A")
            elif reply == valid_reply_ch1_ch2_dp832:
                print(f"Configured DP832 CH{channel} to {voltage:.2f} V, {current:.3f} A")
            else:
                print(f"{Fore.RED}Error: Configuration for DP832(A) channel CH{channel} failed. Expected {valid_reply_ch1_ch2_dp832a} or {valid_reply_ch1_ch2_dp832}, got {reply}")
                return False
        elif channel in [3]:
            if reply == valid_reply_ch3_dp832a:
                print(f"Configured DP832A CH{channel} to {voltage:.3f} V, {current:.3f} A")
            elif reply == valid_reply_ch3_dp832:
                print(f"Configured DP832 CH{channel} to {voltage:.2f} V, {current:.3f} A")
            else:
                print(f"{Fore.RED}Error: Configuration for DP832(A) channel CH{channel} failed. Expected {valid_reply_ch3_dp832a} or {valid_reply_ch3_dp832}, got {reply}")
                return False
    psu.close()
    return True


def measure_output_voltage(dp8_instrument_id: str, channels: list):
    psu = rm.open_resource(dp8_instrument_id)
    measurements_dict = {}

    for channel in channels:
        measurements_dict[channel] = float(psu.query(f":MEAS:VOLT? CH{channel}").strip("\n"))

    psu.close()
    return measurements_dict


def measure_output_current(dp8_instrument_id: str, channels: list):
    psu = rm.open_resource(dp8_instrument_id)
    measurements_dict = {}

    for channel in channels:
        measurements_dict[channel] = float(psu.query(f":MEAS:CURR? CH{channel}").strip("\n"))

    psu.close()
    return measurements_dict


def measure_output_power(dp8_instrument_id: str, channels: list):
    psu = rm.open_resource(dp8_instrument_id)
    measurements_dict = {}

    for channel in channels:
        measurements_dict[channel] = float(psu.query(f":MEAS:POWE? CH{channel}").strip("\n"))

    psu.close()
    return measurements_dict


def measure_all(dp8_instrument_id: str, channels: list):
    psu = rm.open_resource(dp8_instrument_id)
    measurements_dict = {}
    for channel in channels:
        channel_results = psu.query(f":MEAS:ALL? CH{channel}").strip('\n').split(',')
        measurements_dict[channel] = {
            "voltage": float(channel_results[0]),
            "current": float(channel_results[1]),
            "power": float(channel_results[2]),
        }
    psu.close()
    return measurements_dict
