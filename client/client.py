import json
import os
import time
import requests
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# Load configuration
with open('./config.json', 'r') as config_file:
    config = json.load(config_file)

directory_to_monitor = config['directory_to_monitor']
server_url = config['server_url']


def find_text_files(directory):
    text_files = []
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith(('.pdf', '.doc', '.txt')):
                text_files.append(os.path.join(root, file))
    return text_files


def send_file_to_server(file_path, server_url):
    with open(file_path, 'rb') as file:
        response = requests.post(
            server_url+'/upload', files={'file': file}, data={'path': file_path})
        if response.status_code == 200:
            print('code: 200, file:', file_path)
        else:
            print('code:', response.status_code, ', file:', file_path)
    return response.status_code


class FileChangeHandler(FileSystemEventHandler):
    def __init__(self, server_url):
        self.server_url = server_url

    def on_modified(self, event):
        if event.src_path.endswith(('.pdf', '.doc', '.txt')):
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


# Find and send existing files
text_files = find_text_files(directory_to_monitor)
for file in text_files:
    send_file_to_server(file, server_url)

# Monitor directory for new or updated files
monitor_directory(directory_to_monitor, server_url)
