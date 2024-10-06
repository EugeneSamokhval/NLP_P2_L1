import json
import os
import time
import requests
import socket
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.responses import FileResponse
import uvicorn

# Load configuration
with open("./config.json", "r") as config_file:
    config = json.load(config_file)

directory_to_monitor = config["directory_to_monitor"]
server_url = config["server_url"]

app = FastAPI()


def get_base_url():
    hostname = socket.gethostname()
    ip_address = socket.gethostbyname(hostname)
    # Adjust the port and path as needed
    return f"http://{ip_address}:8000/files"


def find_text_files(directory):
    text_files = []
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith((".txt")):
                text_files.append(os.path.join(root, file))
    return text_files


def generate_file_url(file_path):
    relative_path = os.path.relpath(file_path, directory_to_monitor)
    return f"{get_base_url()}/{relative_path.replace(os.sep, '/')}"


def send_file_to_server(file_path, server_url):
    file_url = generate_file_url(file_path)
    response = requests.post(
        server_url + "/upload", files={"file": file},  data={"file_url": file_url}
    )
    if response.status_code == 200:
        print("code: 200, file:", file_url)
    else:
        print("code:", response.status_code, ", file:", file_url)
    return response.status_code


class FileChangeHandler(FileSystemEventHandler):
    def __init__(self, server_url):
        self.server_url = server_url

    def on_modified(self, event):
        if event.src_path.endswith((".txt")):
            send_file_to_server(event.src_path, self.server_url)


def monitor_directory(directory, server_url):
    event_handler = FileChangeHandler(server_url)
    observer = Observer()
    observer.schedule(event_handler, directory, recursive=True)
    observer.start()
    try:
        while True:
            time.sleep(10)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()


@app.get('/')
async def get_app(url: str):
    downloaded_file = open(
        config["directory_to_monitor"] + url.split('files/')[1], 'r')
    data = downloaded_file.read()
    downloaded_file.close()
    return data

if __name__ == '__main__':
    print('Client app started')
    # Find and send existing files
    text_files = find_text_files(directory_to_monitor)
    adress = socket.gethostbyname(socket.gethostname())
    uvicorn.run(app="main:app",
                host=adress, port=config["port"], reload=True)
    for file in text_files:
        send_file_to_server(file, server_url)
    monitor_directory(directory_to_monitor, server_url)
