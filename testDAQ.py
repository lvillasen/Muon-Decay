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

# Función para comprimir un string
def compress_string(data):
    # Comprimir el string usando gzip
    buf = io.BytesIO()
    with gzip.GzipFile(fileobj=buf, mode='w') as f:
        f.write(data.encode('utf-8'))
    return buf.getvalue()

context = ssl._create_unverified_context()

url = "https://ciiec.buap.mx/Muon-Decay/muon_test.php"
ms = datetime.now()

event="Esta es una prueba " + str(ms)
print(event,strftime('%Y%m%d-%H%M%S'))
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
        
        
