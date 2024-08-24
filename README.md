# Simple DP832 remote interface
Remote interface for Rigol DP832(A) power supplies with GUI stylised to mimic the DP832A interface (ish).

I made this because I had no space on my desk, so I had to move the power supply to the opposite side of the desk. While that involves getting up and walking towards it, which is a problem, the biggest factor was not having a visual on what the power supply is doing at a glance.

----

**Dependencies**
- NI-VISA drivers
- Pyvisa
- Colorama
- tkinter
- dp832.py (included)
- find_instrument.py (included)

Only tested on Windows 10

----

**Workflow**
1. Automatically finds any connected "DP8" devices (USB only for now)
   
![image](https://github.com/user-attachments/assets/38743e4b-e52a-403a-bcda-eed2290a87eb)

3. Use the power supply as you would with the front interface

![image](https://github.com/user-attachments/assets/f0e3796f-16cf-438e-a53c-343fe3216f8a)

-----

**Known issues**
- No support for ethernet devices when detecting 
- I wanted the entire row (where the channel information is) to be filled in; it only fills in the parts where there is text
- It does not warn you when the voltage or current limit has been triggered; the only way to tell right now is by seeing that the output enabled but the output voltage is 0.000 V
- CV in the top right of the power supply channel is a placeholder, it does not query what regulation mode is currently active 
