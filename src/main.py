from fastapi import FastAPI, File, UploadFile, Form, HTTPException
import json
import gridfs
import file_processor
from pymongo import MongoClient, errors
import nltk
import ai_feature
from bson import ObjectId
from fastapi.encoders import jsonable_encoder


class JSONEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, ObjectId):
            return str(o)
        return super().default(o)


nltk.download("stopwords")
nltk.download("punkt_tab")

app = FastAPI()

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


@app.post("/upload")
async def upload_file(file: UploadFile = File(...), path: str = Form(...)):
    raw_text_dict = file_processor.get_raw_text(file.file, path)
    if not raw_text_dict:
        raise HTTPException(status_code=400, detail="Failed to process file")
    # Store file in GridFS
    file_id = fs.put(file.file, filename=file.filename, path=path)
    # Store metadata in 'documents' collection
    db["documents"].insert_one(
        {
            "file_id": file_id,
            "filename": file.filename,
            "path": path,
            "raw_text": raw_text_dict,
        }
    )
    return {"filename": file.filename, "path": path, "file_id": str(file_id)}


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

        print(query)
        results = db["documents"].find(query)
        file_metadata_list = [document_to_json(doc) for doc in results]
        return jsonable_encoder(file_metadata_list)

    except errors.PyMongoError as e:
        raise HTTPException(
            status_code=500, detail=f"Database error: {str(e)}")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app="main:app",
                host=config["host"], port=config["port"], reload=True)
