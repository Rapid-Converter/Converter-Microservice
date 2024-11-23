import os
import tempfile
import shutil
from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from concurrent.futures import ThreadPoolExecutor
from werkzeug.utils import secure_filename
from utility import utility
import httpx  # For sending requests to Microservice 2
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],  
    allow_headers=["*"],  
)

class EncryptionServiceError(Exception):
    def __init__(self, message: str):
        self.message = message

OUTPUT_DIR = os.getenv("OUTPUT_DIR", "./files")
os.makedirs(OUTPUT_DIR, exist_ok=True)

ENCRYPTION_SERVICE_URL = os.getenv("ENCRYPTION_SERVICE_URL", "http://encryption-service:8001/encrypt")

app.mount("/files", StaticFiles(directory=OUTPUT_DIR), name="files")

@app.post("/convert")
async def convert(
    encryption: bool = Form(False),
    password: str = Form(None),
    file: UploadFile = File(...)
):
    if not file.filename.endswith(".docx"):
        raise HTTPException(status_code=400, detail="Invalid file format. Only .docx files are allowed.")
    
    temp_dir = tempfile.mkdtemp()
    filename = secure_filename(file.filename)

    try:
        temp_input_path = os.path.join(temp_dir, filename)
        with open(temp_input_path, "wb") as temp_file:
            temp_file.write(await file.read())
        
        pdf_filename = os.path.splitext(filename)[0] + ".pdf"
        output_path = os.path.join(OUTPUT_DIR, pdf_filename)

        with ThreadPoolExecutor() as executor:
            executor.submit(utility, temp_input_path, output_path).result()
        
        print("Converted file stored at:", output_path)

        if encryption:
            if not password:
                raise HTTPException(status_code=400, detail="Password is required for encryption.")
            
            try:
                encrypted_output_path = await send_to_encryption_service(output_path, password)
                return FileResponse(
                    encrypted_output_path,
                    media_type="application/pdf",
                    filename=os.path.basename(encrypted_output_path)
                )
            except EncryptionServiceError as ese:
                print(f"Encryption failed: {ese.message}")
                headers = {
                    "X-Encryption-Failed": "true",
                    "X-Encryption-Message": ese.message
                }
                return FileResponse(
                    output_path,
                    media_type="application/pdf",
                    filename=pdf_filename,
                    headers=headers
                )
        
        return FileResponse(
            output_path,
            media_type="application/pdf",
            filename=pdf_filename
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")
    finally:
        shutil.rmtree(temp_dir)

async def send_to_encryption_service(file_path: str, password: str) -> str:
    """Send the PDF file to Microservice 2 for encryption."""
    try:
        with open(file_path, "rb") as pdf_file:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    ENCRYPTION_SERVICE_URL,
                    data={"password": password},
                    files={"file": pdf_file}
                )
                response.raise_for_status()

        encrypted_filename = "encrypted_" + os.path.basename(file_path)
        encrypted_output_path = os.path.join(OUTPUT_DIR, encrypted_filename)
        with open(encrypted_output_path, "wb") as encrypted_file:
            encrypted_file.write(response.content)

        print(f"Encrypted file stored at: {encrypted_output_path}")
        return encrypted_output_path

    except httpx.RequestError as e:
        print(f"Failed to contact encryption service: {str(e)}")
        raise EncryptionServiceError("Encryption service is currently down.")
    except Exception as e:
        print(f"An error occurred during encryption: {str(e)}")
        raise EncryptionServiceError("An error occurred during encryption.")

@app.get("/list-pdfs")
async def list_pdfs():
    try:
        if not os.path.exists(OUTPUT_DIR):
            return JSONResponse(content={"pdfs": []}, status_code=200)

        pdfs = [
            {"name": f, "url": f"/files/{f}"}
            for f in os.listdir(OUTPUT_DIR)
            if f.endswith(".pdf")
        ]
        return JSONResponse(content={"pdfs": pdfs}, status_code=200)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")
