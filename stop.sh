#!/bin/bash
# ...28/Dec/24
# ...Author: LV
# ...Detener Muon Decay DAQ with
crontab -l | sed '/Muon-Decay/s/^/#/' | crontab -
echo "Muon Decay DAQ stopped ....."
date
