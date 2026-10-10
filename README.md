# Redragon M916 Wireless Fix

Tool designed to resolve the issue where the official **Redragon M916 Pro (1K / 4K)** software gets stuck on the message **"Please Connect Your Gaming Device"** while using the 2.4GHz wireless dongle.

---

### Why does this happen?
When installed, the official software sometimes writes an incorrect or missing dongle Product ID (`D_PID`) inside its internal configuration (`Config.ini`). This prevents the application from recognizing the mouse over 2.4GHz wireless, even though the mouse works normally in Windows and communicates fine via USB-C cable.

### What does this tool do?
* **Auto-detects installation:** Finds the Redragon software directory and locates `Config.ini` automatically.
* **Reads hardware PID:** Queries Windows HID devices for your Redragon dongle's real hardware ID (e.g. `F5D5` or 4K variants) under Vendor ID `3554`.
* **Safely patches configuration:** Encodes the detected hardware PID to Base64 (`RedragonXXXX`) and updates `D_PID` and `OfflineCantIn` parameters in `Config.ini`.

---

### How to use:
1. **Close the Redragon software** completely (make sure it is not running in the system tray).
2. Connect your 2.4GHz wireless receiver (dongle) to your PC and turn the mouse switch to **2.4G**.
3. Download the latest `redragon_fixer.exe` from the [Releases tab](../../releases/latest).
4. Run the executable as Administrator.
5. Verify the detected path and PID, then click **"Parchear Config.ini"**.
6. Open the official Redragon software — it will now recognize your mouse in wireless mode immediately.
