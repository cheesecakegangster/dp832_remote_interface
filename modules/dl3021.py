import pyvisa as visa
import sys
import os
import traceback

rm = visa.ResourceManager()  # assign resource manager to rm
instrument_tuple = rm.list_resources()

def set_input_state(instrument_id, state):
    try:
        load = rm.open_resource(instrument_id)
        load.write(f":SOURce:INPut:STATe {state}")
        print(f"Configured DL3021 input to {state}")
        load.close()
        return True  # it needs to return true for pytest because i think this is how it verifies the operation was a success
    except:
        sys.exit()

def get_input_state(instrument_id):
    load = rm.open_resource(instrument_id)
    dl3021_input = load.query(f":SOURce:INPut:STATe?")
    load.close()
    return dl3021_input

def configure_cc_static(dl3021_instrument_id, current, i_range, slew_rate, read_back=True, disable_input_on_change=True, vlim=155, ilim=40):
    load = rm.open_resource(dl3021_instrument_id)
    if read_back:
        print("Initialising DL3021 DC load configuration")

    dl3021_input = load.query(":SOUR:INP:STAT?")
    if read_back:
        print(f"CH1 current state is {dl3021_input}")

    if disable_input_on_change:
        if dl3021_input != "0":
            print("Disabled input of dl3021_input")
            load.write(":SOUR:INP:STAT OFF")

    load.write(":SOURce:FUNCtion CURRent")  # set CC mode
    load.write(f":SOURce:CURRent:RANGe {str(i_range)}")  # set voltage range
    load.write(f":SOURce:CURRent:SLEW:BOTH {str(slew_rate)}")  # set current range
    load.write(f":SOUR:VOLT:VLIM {vlim}")  # set voltage limit
    load.write(f":SOUR:VOLT:ILIM {ilim}")  # set current limit
    load.write(f':SOURce:CURRent:LEVel:IMMediate {str(current)}')  # set current level

    function = load.query(':SOURce:FUNCtion?').strip('\n')
    i_set = load.query(':SOURce:CURRent:LEVel:IMMediate?').strip('\n')
    i_range_set = load.query(':SOURce:CURRent:RANGe?').strip('\n')
    slew = load.query(':SOURce:CURRent:SLEW?').strip('\n')
    load.close()

    if read_back:
        print(f'DL3021 configured to {function} at {i_set} A, Irange = {i_range_set}, Slew pos = {slew}')
    return True

def configure_cv_static(dl3021_instrument_id,  voltage, v_range=150, read_back=True, disable_input_on_change=True, vlim=155, ilim=70):
    load = rm.open_resource(dl3021_instrument_id)

    if read_back:
        print("Initialising DL3021 DC load CV configuration")

    dl3021_input = load.query(":SOUR:INP:STAT?")
    if read_back:
        print(f"CH1 current state is {dl3021_input}")

    if disable_input_on_change and dl3021_input.strip() != "0":
        print("Disabled input of dl3021_input")
        load.write(":SOUR:INP:STAT OFF")

    
    load.write(":SOURce:FUNCtion VOLTage")              # set CV mode
    load.write(f":SOURce:VOLTage:RANGe {str(v_range)}") # set voltage range (150 V or 15 V i think)
    load.write(f":SOUR:VOLT:VLIM {vlim}")               # set vlim (max 155 V)
    load.write(f":SOUR:VOLT:ILIM {ilim}")               # set ilim (max 70 A, interface on DL3021 calls it C_Limit)
    load.write(f":SOURce:VOLTage:LEVel:IMMediate {str(voltage)}")   # set voltage

    function = load.query(":SOURce:FUNCtion?").strip('\n')              # get if cv is enabled    
    v_set = load.query(":SOURce:VOLTage:LEVel:IMMediate?").strip('\n')  # get voltage level
    v_range_set = load.query(":SOURce:VOLTage:RANGe?").strip('\n')      # get voltage range
    load.close()

    if read_back:
        print(f"DL3021 configured to {function} at {v_set} V, Vrange = {v_range_set}")

    return True

def measure_all(dl3021_instrument_id):
    load = rm.open_resource(dl3021_instrument_id)

    raw_inst_power_load = load.query("MEAS:POW?")
    raw_inst_voltage_load = load.query("MEAS:VOLT?")
    raw_inst_current_load = load.query("MEAS:CURR?")

    inst_power_load = float(raw_inst_power_load)
    inst_volt_load = float(raw_inst_voltage_load)
    inst_curr_load = float(raw_inst_current_load)

    load.close()

    return inst_power_load, inst_volt_load, inst_curr_load