# main.py
import os
import uuid
import logging
from dotenv import load_dotenv
from fastapi import FastAPI, Request, UploadFile, File
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from prometheus_client import Counter, generate_latest, CONTENT_TYPE_LATEST

load_dotenv()

from agents.agent import EduAgent
from agents.quiz_agent import QuizAgent
from agents.pdf_agent import PDFAgent

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("edu_agent_app")

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="template")

MEMORY_FILE = os.getenv("MEMORY_FILE", "memory_bank.json")
agent = EduAgent(memory_file=MEMORY_FILE)
quiz_agent = QuizAgent()
pdf_agent = PDFAgent()

REQUESTS = Counter("edu_agent_requests_total", "Total bot requests")

# In-memory quiz storage (use Redis in production)
active_quizzes = {}


@app.middleware("http")
async def add_request_id(request: Request, call_next):
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("chat.html", {"request": request})


@app.post("/api/chat")
async def chat_api(request: Request):
    REQUESTS.inc()
    payload = await request.json()
    session_id = payload.get("session_id") or str(uuid.uuid4())
    user_text = payload.get("text", "")
    
    logger.info("Chat request session=%s text=%s", session_id, user_text)
    
    resp = agent.answer(session_id=session_id, user_query=user_text)
    
    response_data = {
        "reply": resp.text,
        "sources": resp.sources,
        "metadata": resp.metadata,
        "session_id": session_id,
        "is_quiz": resp.is_quiz_request
    }
    
    if resp.is_quiz_request:
        response_data["quiz_params"] = resp.quiz_params
    
    return JSONResponse(response_data)


@app.post("/api/quiz/generate")
async def generate_quiz(request: Request):
    """Generate a new quiz"""
    payload = await request.json()
    session_id = payload.get("session_id")
    topic = payload.get("topic", "Python")
    class_level = payload.get("class_level", "11")
    num_questions = payload.get("num_questions", 5)
    
    logger.info(f"Generating quiz: topic={topic}, class={class_level}, questions={num_questions}")
    
    try:
        questions = quiz_agent.generate_quiz(topic, class_level, num_questions)
        
        # Create quiz ID
        quiz_id = str(uuid.uuid4())
        
        # Store quiz in memory
        active_quizzes[quiz_id] = {
            "session_id": session_id,
            "topic": topic,
            "class_level": class_level,
            "questions": [
                {
                    "question": q.question,
                    "options": q.options,
                    "correct_answer": q.correct_answer,
                    "explanation": q.explanation
                }
                for q in questions
            ],
            "current_index": 0,
            "score": 0,
            "answers": []
        }
        
        # Return first question
        first_q = questions[0]
        return JSONResponse({
            "quiz_id": quiz_id,
            "total_questions": len(questions),
            "current_question": 1,
            "question": {
                "text": first_q.question,
                "options": first_q.options
            }
        })
    
    except Exception as e:
        logger.exception(f"Quiz generation failed: {e}")
        return JSONResponse({
            "error": "Failed to generate quiz. Please try again."
        }, status_code=500)


@app.post("/api/quiz/answer")
async def submit_answer(request: Request):
    """Submit answer and get next question"""
    payload = await request.json()
    quiz_id = payload.get("quiz_id")
    user_answer = payload.get("answer")
    
    if quiz_id not in active_quizzes:
        return JSONResponse({"error": "Quiz not found"}, status_code=404)
    
    quiz = active_quizzes[quiz_id]
    current_idx = quiz["current_index"]
    current_q = quiz["questions"][current_idx]
    
    # Check if answer is correct
    is_correct = user_answer == current_q["correct_answer"]
    
    if is_correct:
        quiz["score"] += 1
    
    # Store answer
    quiz["answers"].append({
        "question_index": current_idx,
        "user_answer": user_answer,
        "correct": is_correct
    })
    
    # Move to next question
    quiz["current_index"] += 1
    next_idx = quiz["current_index"]
    
    # Check if quiz is complete
    if next_idx >= len(quiz["questions"]):
        total = len(quiz["questions"])
        percentage = (quiz["score"] / total) * 100
        
        return JSONResponse({
            "completed": True,
            "score": quiz["score"],
            "total": total,
            "percentage": round(percentage, 1),
            "explanation": current_q["explanation"],
            "was_correct": is_correct
        })
    
    # Return next question
    next_q = quiz["questions"][next_idx]
    return JSONResponse({
        "completed": False,
        "current_question": next_idx + 1,
        "total_questions": len(quiz["questions"]),
        "question": {
            "text": next_q["question"],
            "options": next_q["options"]
        },
        "explanation": current_q["explanation"],
        "was_correct": is_correct
    })


@app.get("/api/history/{session_id}")
async def history(session_id: str):
    hist = agent.memory.get_history(session_id)
    return JSONResponse({"history": hist})


@app.get("/metrics")
async def metrics():
    data = generate_latest()
    return HTMLResponse(data, media_type=CONTENT_TYPE_LATEST)


@app.post("/api/pdf/summarize")
async def summarize_pdf(file: UploadFile = File(...)):
    """Upload and summarize a PDF file"""
    
    if not file.filename.endswith('.pdf'):
        return JSONResponse({
            "success": False,
            "error": "Only PDF files are supported"
        }, status_code=400)
    
    try:
        # Read PDF bytes
        pdf_bytes = await file.read()
        
        logger.info(f"Processing PDF: {file.filename} ({len(pdf_bytes)} bytes)")
        
        # Process PDF
        result = pdf_agent.process_pdf(pdf_bytes, summary_type="general")
        
        if result["success"]:
            return JSONResponse({
                "success": True,
                "filename": file.filename,
                "summary": result["summary"],
                "original_length": result["original_length"],
                "summary_length": result["summary_length"]
            })
        else:
            return JSONResponse({
                "success": False,
                "error": result.get("error", "Unknown error")
            }, status_code=500)
    
    except Exception as e:
        logger.exception(f"PDF processing error: {e}")
        return JSONResponse({
            "success": False,
            "error": str(e)
        }, status_code=500)