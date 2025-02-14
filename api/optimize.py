import os
import shutil
import logging
from fastapi import FastAPI, UploadFile, File
from fastapi.responses import JSONResponse
import openai
from mangum import Mangum

# File parsing libraries
import PyPDF2
import docx
import textract
from PIL import Image
import pytesseract

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# Get your API key from environment variables
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "your_openai_api_key")

@app.post("/optimize")
async def optimize_resume(resume: UploadFile = File(...), jd: UploadFile = File(...)):
    try:
        logger.info("Received optimize request.")
        
        # Save files to /tmp (writable on Vercel)
        resume_path = f"/tmp/{resume.filename}"
        jd_path = f"/tmp/{jd.filename}"
        with open(resume_path, "wb") as buffer:
            shutil.copyfileobj(resume.file, buffer)
        with open(jd_path, "wb") as buffer:
            shutil.copyfileobj(jd.file, buffer)
        
        # Extract text from files
        resume_text = extract_text(resume_path)
        jd_text = extract_text(jd_path)
        
        # Call the LLM API to optimize the resume
        optimized_resume = call_llm(resume_text, jd_text)
        logger.info("Resume optimized successfully.")
        return JSONResponse(content={"optimized_resume": optimized_resume})
    except Exception as e:
        logger.exception("Error in optimize_resume endpoint:")
        return JSONResponse(content={"error": f"Internal server error: {str(e)}"}, status_code=500)


def extract_text(file_path: str) -> str:
    ext = os.path.splitext(file_path)[1].lower()
    logger.info(f"Extracting text from {file_path} with extension {ext}")
    try:
        if ext == ".txt":
            with open(file_path, "r", encoding="utf-8") as f:
                text = f.read()
        elif ext == ".pdf":
            text = ""
            with open(file_path, "rb") as f:
                reader = PyPDF2.PdfReader(f)
                for page in reader.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text
        elif ext == ".docx":
            doc = docx.Document(file_path)
            text = "\n".join([para.text for para in doc.paragraphs])
        elif ext == ".doc":
            text = textract.process(file_path).decode("utf-8")
        elif ext in [".png", ".jpg", ".jpeg"]:
            image = Image.open(file_path)
            text = pytesseract.image_to_string(image)
        else:
            text = f"Unsupported file extension: {ext}"
    except Exception as e:
        logger.exception(f"Error extracting text from {file_path}")
        text = f"Error extracting text from file {file_path}: {str(e)}"
    return text

def call_llm(resume_text: str, jd_text: str) -> str:
    openai.api_key = OPENAI_API_KEY
    prompt = f"""
Optimize the following resume based on the given job description.

Resume:
{resume_text}

Job Description:
{jd_text}

Ensure the resume is ATS optimized, keyword-rich, and condensed to one page.
"""
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "system", "content": prompt}]
    )
    return response["choices"][0]["message"]["content"]

handler = Mangum(app)
