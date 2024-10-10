from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.encoders import jsonable_encoder
import json
import gridfs
import file_processor
from pymongo import MongoClient, errors
import nltk
import ai_feature
from bson import ObjectId
import logging
import metrics
import os

logging.basicConfig(
    level=logging.INFO,  # Set the log level
    # Set the log format
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("fastapi.log"),  # Log to a file
        logging.StreamHandler()  # Log to the console
    ]
)

logger = logging.getLogger(__name__)


class JSONEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, ObjectId):
            return str(o)
        return super().default(o)


nltk.download("stopwords")
nltk.download("punkt_tab")

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    # Разрешить все источники, можно указать конкретные домены
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],  # Разрешить все методы
    allow_headers=["*"],  # Разрешить все заголовки
)
app.mount(
    "/static", StaticFiles(directory=os.getcwd().removesuffix('\\src') + '\\'), name="static")

client = MongoClient("mongodb://localhost:27017/")
db = client["SearchingProfiles"]
fs = gridfs.GridFS(db)
with open("./config.json", "r") as config_file:
    config = json.load(config_file)

indexes = db["documents"].index_information()
if "field_name_text" in indexes:
    db["documents"].drop_index("field_name_text")

# Ensure text index is created on the 'documents' collection
db["documents"].create_index([("raw_text", "text"), ("path", "text")])


def document_to_json(document):
    document["_id"] = str(document["_id"])
    if "file_id" in document:
        document["file_id"] = str(document["file_id"])
    return document


def is_word_correct(set_of_words, list_of_correct_words):
    for entry in set_of_words:
        if entry in list_of_correct_words:
            return True
    return False


@app.get("/", response_class=FileResponse)
async def read_index():
    response = FileResponse(os.getcwd().removesuffix('\\src') + "\\index.html")
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response


@app.post("/upload")
async def upload_file(file: UploadFile = File(...), file_path: str = Form(...)):
    file.file.seek(0)
    raw_text_dict = file_processor.get_raw_text(file.file, file_path)

    if not raw_text_dict:
        raise HTTPException(status_code=400, detail="Failed to process file")

    # Check if the document already exists based on the file path or name
    existing_doc = db["documents"].find_one(
        {"filename": file_path.split('\\')[-1]})

    # If document exists, we overwrite it
    if existing_doc:
        # Get the existing file ID to remove the old version in GridFS
        existing_file_id = existing_doc.get("file_id")

        # Remove old file from GridFS
        if existing_file_id:
            fs.delete(ObjectId(existing_file_id))

        # Store the new file in GridFS
        file_id = fs.put(file.file, filename=file.filename, url=file_path)

        # Update the existing document with the new file and metadata
        db["documents"].update_one(
            {"_id": existing_doc["_id"]},  # Query to find the document
            {
                "$set": {
                    "file_id": file_id,
                    "file_path": str(config['local_addres'] + ':' + str(config['port']) + '/storage/?file_path=' + file_path.split('\\')[-1]).replace('/', '\\'),
                    "raw_text": raw_text_dict,
                }
            }
        )
        message = "Document updated successfully"
    else:
        # If the document does not exist, we insert a new one
        file_id = fs.put(file.file, filename=file.filename, url=file_path)
        db["documents"].insert_one(
            {
                "file_id": file_id,
                "filename": file_path.split('\\')[-1],
                "file_path": str(config['local_addres'] + ':' + str(config['port']) + '/storage/?file_path=' + file_path.split('\\')[-1]).replace('/', '\\'),
                "raw_text": raw_text_dict,
            }
        )
        message = "Document uploaded successfully"

    # Save the file to local storage
    with open(os.getcwd().removesuffix('\\src') + '\\storage\\' + file_path.split('\\')[-1], 'w') as current_file:
        openable_file = file.file
        openable_file.seek(0)
        current_file.write(openable_file.read().decode('utf-8'))

    return {"filename": file.filename, "file_path": file_path, "message": message}


@app.get("/find")
async def find_file(user_input: str):
    try:
        include_terms = ai_feature.parse_query(user_input)
        query = {"raw_text": {
            "$elemMatch": {"word": {"$in": include_terms}}}}
        results = db["documents"].find(query)
        file_metadata_list = [document_to_json(doc) for doc in results]
        for entry in file_metadata_list:
            entry['raw_text'] = [found_entry for found_entry in entry.get(
                'raw_text') if is_word_correct(found_entry.values(), include_terms)]
        list_of_files = [(entry['filename'], [
            snippet['pos'] for snippet in entry['raw_text'] if type(snippet['pos']) == list]) for entry in file_metadata_list]
        best_snippets = ai_feature.get_best_snippet(list_of_files, user_input)
        for entry in file_metadata_list:
            entry['raw_text'] = best_snippets[entry['filename']]
        await metrics.calculate_metrics(file_metadata_list, user_input)
        return jsonable_encoder(file_metadata_list)

    except errors.PyMongoError as e:
        raise HTTPException(
            status_code=500, detail=f"Database error: {str(e)}")


@app.get("/storage")
async def get_file(file_path: str):
    try:
        with open(os.getcwd().removesuffix('\\src') + '\\storage\\' + file_path, 'r') as current_file:
            return current_file.read()
    except:
        raise HTTPException(
            status_code=500, detail=f"File storage error")

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app="main:app",
                host=config["host"], port=config["port"], reload=True)
