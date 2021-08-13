import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
import json
import os
import serial
import time
import threading
from google.cloud import storage
import datetime
import urllib.request

path_origin = os.path.dirname(__file__)
path_id_serial = os.path.join(path_origin,'id.json')
path_file = os.path.join(path_origin,'file.json')
path_cred = os.path.join(path_origin,'tesismlac-7136f6068052.json')
file_id_serial = open(path_id_serial)
json_id_serial = json.load(file_id_serial)
id_serial = json_id_serial['id_number']
cred = credentials.Certificate(path_cred)
BucketName = 'tesismlac.appspot.com'

def internet_available():
    try:
        urllib.request.urlopen('http://www.google.com', timeout=1)
        return True
    except:
        return False

while(internet_available()==False):
    print("esperando conexión")
    time.sleep(5)

if(os.path.isfile(path_file) == True):
    os.remove(path_file)

firebase_admin.initialize_app(cred)
db = firestore.client()

serial_doc_ref = db.collection('seriales').document(id_serial)
serial_doc = serial_doc_ref.get()
serial_doc_id = serial_doc.id

user_doc_ref = db.collection('usuarios')
query_ref = user_doc_ref.where('serial', '==', ''+serial_doc_id).stream()
for doc in query_ref:
    identificacion = doc.to_dict()['identificacion']
    nombre = doc.to_dict()['nombre']

humedad = []
temperatura = []
ruido = []
luz = []
emg = []
Ready_sign = 0

def portIsUsable():
    try:
       ser = serial.Serial(port='COM5')
       return True
    except:
       return False

while(portIsUsable() == False):
    print("Waiting")
    time.sleep(5)

try:
    port_ref = serial.Serial('COM5', baudrate = 115200)
except serial.SerialException:
    print('port already open')

def f1():
    to = time.time()
    if(id_serial == serial_doc_id):
        while (time.time() - to < 100):
            line = port_ref.readline()
            datos_bruto = str(line)
            datos_bruto = datos_bruto.replace("b'","")
            datos_bruto = datos_bruto.replace("r","")
            datos_bruto = datos_bruto.replace("n","")
            datos_bruto = datos_bruto.replace("\\","")
            datos_bruto = datos_bruto.replace(",'","")
            datos_bruto = datos_bruto.split(",")
            if(datos_bruto[0] == '0'):
                humedad.append(float(datos_bruto[1]))
                temperatura.append(float(datos_bruto[2]))
                ruido.append(float(datos_bruto[3]))
                luz.append(float(datos_bruto[4]))
            else:
                if(datos_bruto[1] != '-'):
                    humedad.append(float(datos_bruto[1]))
                if(datos_bruto[2] != '-'):
                    temperatura.append(float(datos_bruto[2]))
                if(datos_bruto[3] != '-'):
                    ruido.append(float(datos_bruto[3]))
                if(datos_bruto[4] != '-'):
                    luz.append(float(datos_bruto[4]))
                emg.append(float(datos_bruto[5]))
            print(humedad)

def f2():
    while(hilo1.is_alive()):
        categorias = ['nombre','identificacion','humedad','temperatura','ruido','luz','emg']
        data = {listname: globals()[listname] for listname in categorias}
        with open('file.json', 'w') as outfile:
            json.dump(data, outfile, indent=4)
        time.sleep(50)

def f3():
    while(hilo2.is_alive()):

        if(os.path.isfile(globals()['path_file']) == True):

            now = datetime.datetime.now()
            fecha = str(now.year)+"-"+str(now.month)+ "-" +str(now.day)
            CloudFilename = globals()['serial_doc_id']+"/" + fecha

            #Archivo de credenciales
            Credencial = storage.Client.from_service_account_json(json_credentials_path=globals()['path_cred'])
            #Nombre Bucket
            bucket = Credencial.get_bucket(globals()['BucketName'])
            #Nombre archivo en la nube
            CloudName = bucket.blob(CloudFilename)
            #Dirección archivo local
            CloudName.upload_from_filename(globals()['path_file'])
            print("enviado a la nube")
        print("esperando")
        time.sleep(120)

def f4():
    while(hilo1.is_alive() == True):
        print("Measuring")
        time.sleep(10)
    
    categorias = ['nombre','identificacion','humedad','temperatura','ruido','luz','emg']
    data = {listname: globals()[listname] for listname in categorias}
    with open('file.json', 'w') as outfile:
        json.dump(data, outfile, indent=4)

    now = datetime.datetime.now()
    fecha = str(now.year)+"-"+str(now.month)+ "-" +str(now.day)
    CloudFilename = globals()['serial_doc_id']+"/" + fecha

    #Archivo de credenciales
    Credencial = storage.Client.from_service_account_json(json_credentials_path=globals()['path_cred'])
    #Nombre Bucket
    bucket = Credencial.get_bucket(globals()['BucketName'])
    #Nombre archivo en la nube
    CloudName = bucket.blob(CloudFilename)
    #Dirección archivo local
    CloudName.upload_from_filename(globals()['path_file'])
    print("enviado a la nube")

hilo1 = threading.Thread(target=f1)
hilo2 = threading.Thread(target=f2)
hilo3 = threading.Thread(target=f3)
hilo4 = threading.Thread(target=f4)
hilo1.start()
hilo2.start()
hilo3.start()
hilo4.start()

