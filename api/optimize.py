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

# Set up the OpenAI API key
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    logger.error("OPENAI_API_KEY not set!")
openai.api_key = OPENAI_API_KEY

@app.post("/optimize")
async def optimize_resume(resume: UploadFile = File(...), jd: UploadFile = File(...)):
    try:
        logger.info("Received optimize request.")

        # Save the uploaded files to /tmp (writable in Vercel)
        resume_path = f"/tmp/{resume.filename}"
        jd_path = f"/tmp/{jd.filename}"
        with open(resume_path, "wb") as buffer:
            shutil.copyfileobj(resume.file, buffer)
        with open(jd_path, "wb") as buffer:
            shutil.copyfileobj(jd.file, buffer)

        logger.info(f"Files saved: {resume_path}, {jd_path}")

        # Extract text from both files
        resume_text = extract_text(resume_path)
        jd_text = extract_text(jd_path)
        logger.info("Text extraction successful.")

        # Call the LLM API to optimize the resume (using gpt-3.5-turbo for testing)
        optimized_resume = call_llm(resume_text, jd_text)
        logger.info("LLM call successful, resume optimized.")

        return JSONResponse(content={"optimized_resume": optimized_resume})
    except Exception as e:
        logger.exception("Error in optimize_resume endpoint:")
        # Return a more detailed error message for debugging purposes (remove in production)
        return JSONResponse(content={"error": f"Internal server error: {str(e)}"}, status_code=500)

def extract_text(file_path: str) -> str:
    ext = os.path.splitext(file_path)[1].lower()
    logger.info(f"Extracting text from {file_path} (extension: {ext})")
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
        text = f"Error extracting text: {str(e)}"
    return text

def call_llm(resume_text: str, jd_text: str) -> str:
    prompt = f"""
Optimize the following resume based on the given job description.

Resume:
{resume_text}

Job Description:
{jd_text}

Ensure the resume is ATS optimized, keyword-rich, and condensed to one page.
"""
    try:
        # Using GPT-3.5-turbo for testing purposes.
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "system", "content": prompt}]
        )
        return response["choices"][0]["message"]["content"]
    except Exception as e:
        logger.exception("Error calling OpenAI API:")
        raise e

handler = Mangum(app)
