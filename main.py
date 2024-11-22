from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import FileResponse
import os
import tempfile
from concurrent.futures import ThreadPoolExecutor
from werkzeug.utils import secure_filename
from utility import utility

app = FastAPI()

# Ensure the output directory exists
OUTPUT_DIR = "./files"
os.makedirs(OUTPUT_DIR, exist_ok=True)

@app.post("/convert")
async def convert(file: UploadFile = File(...)):
    # Validate file type
    if not file.filename.endswith(".docx"):
        raise HTTPException(status_code=400, detail="Invalid file format. Only .docx files are allowed.")
    
    # Create a temporary directory for handling the .docx file
    temp_dir = tempfile.mkdtemp()
    filename = secure_filename(file.filename)

    try:
        # Save the uploaded .docx file in the temporary directory
        temp_input_path = os.path.join(temp_dir, filename)
        with open(temp_input_path, "wb") as temp_file:
            temp_file.write(await file.read())
        
        # Determine the output path in the ./files directory for the converted .pdf
        pdf_filename = os.path.splitext(filename)[0] + ".pdf"
        output_path = os.path.join(OUTPUT_DIR, pdf_filename)

        # Perform the conversion using ThreadPoolExecutor
        with ThreadPoolExecutor() as executor:
            executor.submit(utility, temp_input_path, output_path).result()
        
        print("Converted file stored at:", output_path)
        
        # Return the PDF file to the client
        return FileResponse(
            output_path,
            media_type="application/pdf",
            filename=pdf_filename
        )

    finally:
        # Clean up the temporary directory
        import shutil
        shutil.rmtree(temp_dir)
