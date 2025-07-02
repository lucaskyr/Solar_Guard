from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import os
import pickle

SCOPES = ['https://www.googleapis.com/auth/drive.file']

def upload_test_file():
    creds = None

    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)

        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    try:
        service = build('drive', 'v3', credentials=creds)

        test_filename = 'test_upload.jpg'
        if not os.path.exists(test_filename):
            print(f"Arquivo '{test_filename}' não encontrado. Por favor, crie um arquivo de teste com esse nome na pasta.")
            return


        file_metadata = {'name': test_filename}
        media = MediaFileUpload(test_filename, mimetype='image/jpeg')

        file = service.files().create(body=file_metadata, media_body=media, fields='id').execute()
        print(f"Upload realizado com sucesso! ID do arquivo: {file.get('id')}")

    except Exception as e:
        print(f"Erro ao enviar o arquivo: {e}")

if __name__ == '__main__':
    upload_test_file()
