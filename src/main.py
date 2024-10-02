from fastapi import FastAPI, File, UploadFile, Form
import json
import gridfs
import file_processor
from pymongo import MongoClient
import nltk
import ai_feature

nltk.download('stopwords')
nltk.download('punkt_tab')

app = FastAPI()

client = MongoClient('mongodb://localhost:27017/')
db = client['SearchingProfiles']
fs = gridfs.GridFS(db)
with open('./config.json', 'r') as config_file:
    config = json.load(config_file)

db['documents'].create_index([('field_name', 'text')])


@app.post("/upload")
async def upload_file(file: UploadFile = File(...), path: str = Form(...)):
    raw_text_dict = file_processor.get_raw_text(file.file, path)
    # Convert dictionary to JSON string
    raw_text_json = json.dumps(raw_text_dict)
    file_id = fs.put(raw_text_json.encode('utf-8'),
                     filename=file.filename, path=path)
    return {"filename": file.filename, "path": path, "file_id": str(file_id)}


@app.get("/find")
async def find_file(user_input: str):
    include_terms, exclude_terms = ai_feature.parse_query(user_input)

    collumn = db['documents']
    # Create MongoDB query
    include_query = " ".join(include_terms)
    query = {
        "$text": {"$search": include_query},
    }

    if exclude_terms:
        query["$nor"] = [{"$text": {"$search": term}}
                         for term in exclude_terms]
    try:
        results = collumn.find(query)
        print(list(results))
        return list(results)
    except Exception as e:
        return {"error": str(e)}

if __name__ == '__main__':
    import uvicorn

    uvicorn.run(app="main:app",
                host=config['host'], port=config['port'], reload=True)
