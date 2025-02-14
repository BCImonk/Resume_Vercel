import os
import shutil
from fastapi import FastAPI, UploadFile, File
from fastapi.responses import JSONResponse
import openai
from mangum import Mangum

# Libraries for file parsing
import PyPDF2
import docx
import textract
from PIL import Image
import pytesseract

app = FastAPI()

# Use an environment variable for your OpenAI API key.
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "your_openai_api_key")

@app.post("/optimize")
async def optimize_resume(
    resume: UploadFile = File(...),
    jd: UploadFile = File(...)
):
    # Save uploaded files to a temporary directory (Vercel’s /tmp directory is writable)
    resume_path = f"/tmp/{resume.filename}"
    jd_path = f"/tmp/{jd.filename}"
    
    with open(resume_path, "wb") as buffer:
        shutil.copyfileobj(resume.file, buffer)
    with open(jd_path, "wb") as buffer:
        shutil.copyfileobj(jd.file, buffer)
    
    # Extract text from both files
    resume_text = extract_text(resume_path)
    jd_text = extract_text(jd_path)
    
    # Call the LLM API to optimize the resume
    optimized_resume = call_llm(resume_text, jd_text)
    
    # Return the optimized resume text (or a downloadable link if you later choose to generate a file)
    return JSONResponse(content={"optimized_resume": optimized_resume})

def extract_text(file_path: str) -> str:
    """
    Extract text from file based on its extension.
    Supported formats: .pdf, .doc, .docx, .png, .jpg, .jpeg, .txt
    """
    ext = os.path.splitext(file_path)[1].lower()
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
        text = f"Error extracting text from file {file_path}: {str(e)}"
    
    return text

def call_llm(resume_text: str, jd_text: str) -> str:
    """
    Calls the OpenAI API to optimize the resume.
    The prompt instructs the LLM to produce an ATS-optimized, keyword-rich, one-page resume.
    """
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

# Create a Mangum handler for Vercel’s serverless Python runtime.
handler = Mangum(app)
