from fastapi import FastAPI, File, UploadFile, Form
import json
import gridfs
import file_processor
from pymongo import MongoClient
import nltk

nltk.download('stopwords')
nltk.download('punkt_tab')

app = FastAPI()

client = MongoClient('mongodb://localhost:27017/')
db = client['SearchingProfiles']
fs = gridfs.GridFS(db)
with open('./config.json', 'r') as config_file:
    config = json.load(config_file)


@app.post("/upload")
async def upload_file(file: UploadFile = File(...), path: str = Form(...)):
    raw_text_dict = file_processor.get_raw_text(file.file, path)
    # Convert dictionary to JSON string
    raw_text_json = json.dumps(raw_text_dict)
    file_id = fs.put(raw_text_json.encode('utf-8'),
                     filename=file.filename, path=path)
    return {"filename": file.filename, "path": path, "file_id": str(file_id)}

if __name__ == '__main__':
    import uvicorn

    uvicorn.run(app="main:app",
                host=config['host'], port=config['port'], reload=True)
