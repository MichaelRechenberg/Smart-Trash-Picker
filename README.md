# Smart-Trash-Picker
This repository contains code for a Pi Zero W to be used on a "smart" trash picker (when the user picks up rubbish, send a bluetooth message to the user's phone and request the user's phone to record the current location).  Originally an INFO 490 final project

# Running the BLE Code
First, activate the smart-trash-picker conda environment

Then, run `python my-gatt-server.py`

This will start the GATT server and wait for falling edges on GPIO pin 17.  If pin 17 detects a falling edge, the GPIO thread will busy wait until the input is 1 again, and then indicate to any listening GATT clients that trash was picked up

# BLE UIUDs
Look at the header comments in my-gatt-server.py for the BLE UIUDs used for the Service and Characteristic of the smart trash picking
