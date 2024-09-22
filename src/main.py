from fastapi import FastAPI, File, UploadFile, Form
import shutil
import gridfs
from pymongo import MongoClient

app = FastAPI()

client = MongoClient('mongodb://localhost:27017/')
db = client['SearchingProfiles']
fs = gridfs.GridFS(db)


@app.post("/upload")
async def upload_file(file: UploadFile = File(...), path: str = Form(...)):
    file_id = fs.put(file.file, filename=file.filename, path=path)
    return {"filename": file.filename, "path": path, "file_id": str(file_id)}


if __name__ == '__main__':
    import uvicorn

    uvicorn.run(app="main:app", host='localhost', port=2000, reload=True)
