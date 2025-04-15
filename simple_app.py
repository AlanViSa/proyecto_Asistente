from fastapi import FastAPI
import uvicorn

app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "Hello World"}

@app.get("/items/{item_id}")
def read_item(item_id: int):
    return {"item_id": item_id}

if __name__ == "__main__":
    print("Starting server on http://0.0.0.0:8000")
    print("Try accessing: http://localhost:8000 or http://127.0.0.1:8000")
    uvicorn.run("simple_app:app", host="0.0.0.0", port=8000, reload=True) 