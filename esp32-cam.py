import cv2
import requests
import numpy as np
import time
import paho.mqtt.client as mqtt
import base64
import os

from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
import pickle

SCOPES = ['https://www.googleapis.com/auth/drive.file']
CREDENTIALS_FILE = 'credentials.json'
TOKEN_FILE = 'token_drive.pickle'

def autenticar_drive():
    creds = None
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, 'rb') as token:
            creds = pickle.load(token)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN_FILE, 'wb') as token:
            pickle.dump(creds, token)

    return build('drive', 'v3', credentials=creds)

def enviar_para_drive(nome_arquivo):
    file_metadata = {'name': nome_arquivo}
    media = MediaFileUpload(nome_arquivo, mimetype='image/jpeg')
    file = drive_service.files().create(body=file_metadata, media_body=media, fields='id').execute()
    print(f"[✔] Imagem enviada ao Google Drive. ID: {file.get('id')}")

ESP32_CAM_IP = "10.64.102.3"
CAM_URL = f"http://{ESP32_CAM_IP}/capture"

broker = 'mqtt-dashboard.com'
porta = 1883
topico_mqtt = 'arduino/sensores'
client_id = 'meu_cliente_arduino'
keep_alive = 60

client = mqtt.Client(client_id=client_id, protocol=mqtt.MQTTv311)

def conectar_mqtt():
    try:
        client.connect(broker, porta, keep_alive)
        print("[MQTT] Conectado ao broker!")
    except Exception as e:
        print(f"[MQTT] Erro ao conectar no broker MQTT: {e}")
        exit()

def testar_camera():
    print("[TESTE] Verificando conexão com a câmera...")
    try:
        resposta = requests.get(CAM_URL, timeout=5)
        if resposta.status_code == 200:
            print("[✔] Câmera acessível e funcionando!")
        else:
            print(f"[✖] Câmera respondeu, mas com erro HTTP {resposta.status_code}")
            exit()
    except Exception as e:
        print(f"[✖] Erro ao conectar na câmera: {e}")
        exit()

def stream_camera():
    print("[📷] Iniciando stream da câmera... (ESC para sair)")
    contagem = 0

    while True:
        try:
            img_resp = requests.get(CAM_URL, stream=True, timeout=10)
            img_arr = np.array(bytearray(img_resp.content), dtype=np.uint8)
            frame = cv2.imdecode(img_arr, -1)

            if frame is None:
                print("[⚠️] Frame inválido, pulando...")
                continue

            cv2.imshow("ESP32-CAM Stream", frame)

            _, buffer = cv2.imencode('.jpg', frame)
            jpg_as_text = base64.b64encode(buffer).decode()

            client.publish(topico_mqtt, jpg_as_text)

            nome_arquivo = f"frame_{contagem}.jpg"
            with open(nome_arquivo, 'wb') as f:
                f.write(buffer)
            enviar_para_drive(nome_arquivo)
            os.remove(nome_arquivo)
            contagem += 1

            if cv2.waitKey(1) == 27:  # ESC
                break

        except Exception as e:
            print(f"[Erro] {e}")
            time.sleep(2)

    cv2.destroyAllWindows()

if __name__== "__main__":
    time.sleep(2)
    conectar_mqtt()
    client.loop_start()
    testar_camera()

    drive_service = autenticar_drive()
    stream_camera()
