import pyvisa


def find_device_by_serial(serial_number: str) -> str:
    """
    Finds the device with the given serial number.

    Parameters:
    serial_number (str): The serial number of the device to find.

    Returns:
    str: The resource ID of the device with the given serial number.
    """
    rm = pyvisa.ResourceManager()
    resources = rm.list_resources()

    for resource in resources:
        if serial_number in resource:
            return resource

    raise ValueError(f"Device with serial number {serial_number} not found")


def find_devices_by_pattern(pattern: str) -> list:
    """
    Finds all connected VISA devices that match the given pattern in their IDN response.

    Parameters:
    pattern (str): The pattern to search for in the device's IDN response.

    Returns:
    list: A list of matching VISA resource strings.
    """
    rm = pyvisa.ResourceManager()
    resources = rm.list_resources()
    matching_devices = []

    for resource in resources:
        try:
            # Try to open the resource and check if it's a valid VISA instrument
            instrument = rm.open_resource(resource)
            idn_response = instrument.query("*IDN?")  # Get the IDN string
            if pattern in idn_response:  # Check if the IDN contains the pattern
                matching_devices.append(resource)
            instrument.close()  # Always close the resource
        except Exception as e:
            print(f"Error accessing {resource}: {e}")
            continue

    return matching_devices


def verify_device(resource: str) -> str:
    """
    Verifies that the device is connected by sending *IDN? query to the specified resource.

    Parameters:
    resource (str): The VISA resource string of the device to verify.

    Returns:
    str: The *IDN? response from the device.
    """
    rm = pyvisa.ResourceManager()

    try:
        instrument = rm.open_resource(resource)
        idn_response = instrument.query("*IDN?")
        instrument.close()
        return idn_response
    except Exception as e:
        raise ConnectionError(f"Failed to connect to {resource}: {e}")


if __name__ == "__main__":
    # Example for testing the functions
    # Test finding a device by serial number
    serial = "DP8C241301810"
    try:
        device_id = find_device_by_serial(serial)
        print(f"Device found: {device_id}")
    except ValueError as e:
        print(e)

    # Test finding devices by a pattern
    pattern = "DP8"  # This can be any pattern you're looking for
    try:
        devices = find_devices_by_pattern(pattern)
        if devices:
            print(f"Devices found matching pattern '{pattern}':")
            for device in devices:
                print(f"- {device}")
                idn = verify_device(device)
                print(f"  IDN: {idn}")
        else:
            print(f"No devices found matching pattern '{pattern}'.")
    except Exception as e:
        print(f"Error: {e}")
