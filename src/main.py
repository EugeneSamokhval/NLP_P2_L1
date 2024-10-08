from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
import json
import gridfs
import file_processor
from pymongo import MongoClient, errors
import nltk
import ai_feature
from bson import ObjectId
from fastapi.encoders import jsonable_encoder
import os


class JSONEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, ObjectId):
            return str(o)
        return super().default(o)


nltk.download("stopwords")
nltk.download("punkt_tab")

app = FastAPI()

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
    # Store file in GridFS
    file_id = fs.put(file.file, filename=file.filename, url=file_path)
    with open(os.getcwd().removesuffix(
            '\\src')+'\\storage\\' + file_path.split('\\')[-1], 'w') as current_file:
        openable_file = file.file
        openable_file.seek(0)
        current_file.write(openable_file.read().decode('utf-8'))
    # Store metadata in 'documents' collection
    db["documents"].insert_one(
        {
            "file_id": file_id,
            "filename": file_path.split('\\')[-1],
            "file_path": config['local_addres']+':'+str(config['port'])+'/storage/?file_path='+file_path.split('\\')[-1],
            "raw_text": raw_text_dict,
        }
    )
    return {"filename": file.filename, "file_path": file_path, "file_id": str(file_id)}


@app.get("/find")
async def find_file(user_input: str):
    try:
        include_terms, exclude_terms = ai_feature.parse_query(user_input)

        include_query = {"raw_text": {
            "$elemMatch": {"word": {"$in": include_terms}}}}

        if exclude_terms:
            exclude_query = {"raw_text.word": {"$nin": exclude_terms}}
            query = {"$and": [include_query, exclude_query]}
        else:
            query = include_query
        results = db["documents"].find(query)
        file_metadata_list = [document_to_json(doc) for doc in results]
        for entry in file_metadata_list:
            entry['raw_text'] = [found_entry for found_entry in entry.get(
                'raw_text') if is_word_correct(found_entry.values(), include_terms)]
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
