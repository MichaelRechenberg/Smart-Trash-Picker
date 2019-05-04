#!/bin/bash

GATT_DIR=/home/pi/Workspace/Smart-Trash-Picker

GATT_FILENAME=my-gatt-server.py

# Activate the conda environment
echo "Activating smart-trash-picker conda environment"
source activate smart-trash-picker

GATT_SCRIPT_ABS_FILEPATH=${GATT_DIR}/${GATT_FILENAME}
echo "Starting GATT server using script at ${GATT_SCRIPT_ABS_FILEPATH}"
python ${GATT_SCRIPT_ABS_FILEPATH}


