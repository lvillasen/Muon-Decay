#!/usr/bin/python3
import time
from periphery import MMIO
import urllib.request
import ssl
import gzip
import io
from datetime import datetime
from time import strftime, localtime
import json
import os
max_evts_per_file = 10000




# Función para comprimir un string
def compress_string(data):
    # Comprimir el string usando gzip
    buf = io.BytesIO()
    with gzip.GzipFile(fileobj=buf, mode='w') as f:
        f.write(data.encode('utf-8'))
    return buf.getvalue()

# Configurar un contexto SSL que ignore la verificación del certificado
context = ssl._create_unverified_context()

# Configuración
url = "https://ciiec.buap.mx/Muon-Decay/datosReceiver10000.php"
print("Starting data taking ...",end=" ")
ms = datetime.now()
#date_epoch = time.mktime(ms.timetuple())  # UTC
#print(strftime('%Y%m%d-%H%M%S', localtime(date_epoch)))


# Ruta del archivo
file_path_evt = "/root/Muon-Decay/evtNumber.txt"

def read_event_number(file_path_evt):
    """Lee el número evt_number del archivo, o devuelve 0 si el archivo no existe."""
    if os.path.exists(file_path_evt):
        with open(file_path_evt, 'r') as file:
            try:
                return int(file.read().strip())  # Leer y convertir a entero
            except ValueError:
                return 0  # Si el contenido no es válido, asumimos 0
    else:
        return 0

def write_event_number(file_path, evt_number):
    with open(file_path, 'w') as file:
        file.write("{}\n".format(evt_number))  # Usar format para escribir el número


# Leer el número actual
evt_number = read_event_number(file_path_evt)
print("Número actual: {}".format(evt_number))


ms = datetime.now()
regset = MMIO(0x41210000, 0xc)
NumSinglesLast = regset.read32(8) % (256*256)
NumDoublesLast = int(regset.read32(8) / (256*256))
regset.close()
trig_mode = "NORMAL"




##########################################################################inputs
CHANNEL = 1 # 1
GAIN = 1 # Select 1 or 20 for +- 1 V or +- 20 V according to your RP jumper LV or HV
TRESHOLD_VOLT = -.015 # Volt
POINTS_SAVE_AFTER_TRIGGER = 1000 # ns
WINDOW_DOUBLE_PULSE = 20000 # ns
EDGE = 0 # 1 for PosEdge trigger  0 for NegEdge trigger
MODE = 1 # # MODE = 0 Single-Pulse Trigger   MODE = 1  Double-Pulse Trigger
VETO_NS = 150 # ns

WINDOW_DOUBLE_PULSE = int(WINDOW_DOUBLE_PULSE/8)
POINTS_SAVE_AFTER_TRIGGER = int(POINTS_SAVE_AFTER_TRIGGER/8)
VETO = int (VETO_NS/8)
#POINTS_BEFORE_TRIGGER = WINDOW_DOUBLE_PULSE
if (MODE == 0):
    DELAY = 3   # 3 is the constant delay of trigger in Single-pulse mode
else:
    DELAY = 5  # 5 is the constant delay if trigger in Double-pulse mode
TRESHOLD_COUNTS = int(TRESHOLD_VOLT * 2**14/(-2*GAIN) + 2**13)
#print ("TRESHOLD_COUNTS = ", TRESHOLD_COUNTS , "for TRESHOLD_VOLT =",TRESHOLD_VOLT, " Volt")
#print ("Threshold (V) =",TRESHOLD_VOLT, " EDGE = ",EDGE," MODE = ",MODE, " Trigger Mode = ",trig_mode," VETO (ns) = ",VETO_NS )

####################################################################
regset = MMIO(0x41220000, 0xc)
regset.write32(0,POINTS_SAVE_AFTER_TRIGGER*256*256+WINDOW_DOUBLE_PULSE) # POINTS_AFTER_TRIGGER and WINDOW_DOUBLE_PULSE
regset.write32(8,MODE) # MODE = 0 SINGLE  MODE = 1 DOUBLE
regset.close()
####################################################################
start_time = time.time()
while time.time() - start_time < 60:
    daq = 1
    regset = MMIO(0x41200000, 0xc)
    regset.write32(0,TRESHOLD_COUNTS*256*256) # TRESHOLD
    ADDR_TRIG_OLD = int(regset.read32(8)/256/256) - DELAY
    #print("ADDR_TRIG_OLD = ",ADDR_TRIG_OLD)
    regset.write32(0,TRESHOLD_COUNTS*256*256+2) # TRESHOLD and ENABLE TRIGGER
    regset.write32(0,TRESHOLD_COUNTS*256*256)
    regset.close()
    ####################################################################
    regset = MMIO(0x41230000, 0xc)
    regset.write32(8,VETO*16 + EDGE) # TRIGGER EDGE and VETO
    regset.close()

    #############################################################################



    ####################################################################

    while(daq == 1):
        time.sleep(.5) # to avoid saturating the RedPitaya CPUs
        
        regset = MMIO(0x41200000, 0xc)
        ADDR_TRIG_NEW =  int(regset.read32(8)/256/256) - DELAY
        if ADDR_TRIG_NEW != ADDR_TRIG_OLD:   # TRIGGER DETECTED
            #print("ADDR_TRIG_NEW = ", ADDR_TRIG_NEW)
            daq = 0
        regset.close()
    ####################################################################
    
    ####################################################################
    if MODE == 1:
        regset = MMIO(0x41230000, 0xc)
        DT_BETWEEN_PULSES = regset.read32(0)
        regset.close()
    else:
        DT_BETWEEN_PULSES = POINTS_SAVE_AFTER_TRIGGER - 40
    ####################################################################
    evt_size =DT_BETWEEN_PULSES +40 + POINTS_SAVE_AFTER_TRIGGER
    if evt_size >166:
        # Modificar el número
        if evt_number >= max_evts_per_file:
            evt_number =  1  
        else:
            evt_number = evt_number + 1  
        write_event_number(file_path_evt, evt_number)

        print("Nuevo número guardado: {}".format(evt_number))

        event =""


        ms = datetime.now()
        date_epoch = time.mktime(ms.timetuple())  # UTC

        #print("Evt number: ",evt_number)
        #print("Tiempo ", strftime('%Y%m%d-%H%M%S', localtime(date_epoch)))
        event += strftime('%Y%m%d-%H%M%S', localtime(date_epoch)) + " "
        event +="Evt number: "+str(evt_number) +" "
        event += "Threshold (V) = "+str(TRESHOLD_VOLT) + " EDGE = " + str(EDGE) + " MODE = " + str(MODE)+ " Trigger Mode = " + str(trig_mode)+ " VETO (ns) = " + str(VETO_NS)+ " "

        print("....................Event size =  ",evt_size)
        event += "Event size =  "
        event += str(DT_BETWEEN_PULSES +40 + POINTS_SAVE_AFTER_TRIGGER)

        regset = MMIO(0x41200000, 0xc)
        event += ","
        #print("Pointer at trigger= ",ADDR_TRIG_NEW," =",hex(ADDR_TRIG_NEW))
        dat = []
        n = 0
        for ADDR_B in range(ADDR_TRIG_NEW-DT_BETWEEN_PULSES-40,ADDR_TRIG_NEW+ POINTS_SAVE_AFTER_TRIGGER,1):
            n += 1
            ADDR_B = ADDR_B%2**12
            regset.write32(0,TRESHOLD_COUNTS*256*256+ADDR_B*16)
            regset.write32(0,TRESHOLD_COUNTS*256*256+ADDR_B*16+1)
            COUNTS = regset.read32(8)%(256*256)
            DATA_VOLT = -2*GAIN*(COUNTS-2**13)/2**14
            dat.append(round(DATA_VOLT,3))
            event += str(round(DATA_VOLT,3))
            event += ","
        event += str(n)
        event += "\n"
        regset.close()
        #print(event)

        ####################################################################
        #print(event)
        time.sleep(.5)
        print(evt_number,strftime('%Y%m%d-%H%M%S', localtime(date_epoch)),end=",")
        compressed_data=compress_string(event)
        try:
            # Configurar solicitud POST
            request = urllib.request.Request(
                url,
                data=compressed_data,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
            # Enviar solicitud con contexto SSL
            with urllib.request.urlopen(request, context=context) as response:
                #print(" ",end=",")
                print(response.read().decode("utf-8"))
        except Exception as e:
            print("Error al enviar datos:", e)
        
        
