from fastapi import FastAPI, status
from starlette.responses import JSONResponse

app = FastAPI()

@app.get("/get-tickets")
def read_root():
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "message": "Welcome to FastAPI!",
        }
    )