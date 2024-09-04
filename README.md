# Simple DP832 remote interface
Remote interface for Rigol DP832(A) power supplies with GUI stylised to mimic the DP832A interface (ish).

I made this because I had no space on my desk, so I had to move the power supply to the opposite side of the desk. While that involves getting up and walking towards it, which is a problem, the biggest factor was not having a visual on what the power supply is doing at a glance.

Copious amounts of ChatGPT in this code, just so you know

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

![image](https://github.com/user-attachments/assets/1213d0bf-de36-4c6b-ba6d-9eb65b739e43)
