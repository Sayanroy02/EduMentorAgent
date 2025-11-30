# agents/agent.py
import os
import re
import uuid
import time
import logging
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime
import google.genai as genai
from google.genai import types
from tools.google_search import GoogleSearchTool
from memory.memorybank import MemoryBank

logger = logging.getLogger("edu_agent")
logger.setLevel(logging.INFO)

API_KEY = os.getenv("GOOGLE_API_KEY")
USE_GEMINI = os.getenv("USE_GEMINI", "true").lower() in ("1", "true", "yes")

if USE_GEMINI and API_KEY:
    try:
        genai.configure(api_key=API_KEY)
    except Exception:
        pass


@dataclass
class AgentResponse:
    text: str
    sources: List[Dict[str, str]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    is_quiz_request: bool = False
    quiz_params: Optional[Dict[str, Any]] = None


class EduAgent:
    def __init__(self, memory_file: str = "memory_bank.json"):
        self.search_tool = GoogleSearchTool()
        self.memory = MemoryBank(memory_file)
    
    # ---------------------------
    # Quiz Detection
    # ---------------------------
    def detect_quiz_request(self, text: str) -> Optional[Dict[str, Any]]:
        """Detect if user wants to take a test/quiz"""
        text_lower = text.lower()
        
        # Quiz trigger keywords
        quiz_keywords = [
            "take a test", "take test", "start a test", "start test",
            "quiz me", "give me a quiz", "test me", "give me a test",
            "mcq test", "mcq on", "multiple choice"
        ]
        
        is_quiz = any(keyword in text_lower for keyword in quiz_keywords)
        
        if not is_quiz:
            return None
        
        # Extract topic using regex
        topic_match = re.search(
            r'(?:on|about|for|in)\s+([a-zA-Z0-9\s]+?)(?:\s+(?:class|grade|for\s+class|for\s+grade))?',
            text_lower
        )
        
        # Extract class level
        class_match = re.search(r'class\s+(\d+)|grade\s+(\d+)', text_lower)
        
        topic = "general programming"
        class_level = "11"
        
        if topic_match:
            topic = topic_match.group(1).strip()
        
        if class_match:
            class_level = class_match.group(1) or class_match.group(2)
        
        # Extract number of questions
        num_match = re.search(r'(\d+)\s+questions?', text_lower)
        num_questions = int(num_match.group(1)) if num_match else 5
        num_questions = min(max(num_questions, 3), 10)  # Limit between 3-10
        
        return {
            "topic": topic,
            "class_level": class_level,
            "num_questions": num_questions
        }
    
    # ---------------------------
    # Greeting / preprocessing
    # ---------------------------
    def preprocess_user_input(self, text: str) -> str:
        msg = text.strip().lower()
        greetings = ["hi", "hello", "hey", "hii", "hola"]
        if msg in greetings:
            return "Greet the user politely, introduce yourself as EduMentor, and ask how you can help with studies."
        return text
    
    # ---------------------------
    # Extract text from Gemini response
    # ---------------------------
    def _extract_text_from_response(self, resp) -> str:
        try:
            if hasattr(resp, "text") and resp.text:
                return resp.text
        except:
            pass
        
        try:
            out = getattr(resp, "output", None)
            if out:
                for o in out:
                    parts = getattr(o, "content", None) or o.get("content", [])
                    for p in parts:
                        txt = p.get("text") if isinstance(p, dict) else getattr(p, "text", None)
                        if txt:
                            return txt
        except:
            pass
        
        try:
            cand = getattr(resp, "candidates", None)
            if cand:
                c0 = cand[0]
                if hasattr(c0, "content"):
                    parts = getattr(c0.content, "parts", [])
                    for p in parts:
                        txt = p.get("text") if isinstance(p, dict) else getattr(p, "text", None)
                        if txt:
                            return txt
                if hasattr(c0, "text"):
                    return c0.text
        except:
            pass
        
        return str(resp)
    
    # ---------------------------
    # Gemini API Call
    # ---------------------------
    def _call_gemini(self, prompt: str, max_output_tokens: int = 500) -> str:
        if not (USE_GEMINI and API_KEY):
            return "LLM not configured. Set GOOGLE_API_KEY in .env to enable Gemini."
        
        try:
            client = genai.Client()
            resp = client.models.generate_content(
                model="gemini-2.0-flash",
                contents=prompt,
                config=types.GenerateContentConfig(
                    max_output_tokens=max_output_tokens,
                    temperature=0.2
                )
            )
            return self._extract_text_from_response(resp)
        except Exception as outer:
            logger.exception(f"Gemini API error: {outer}")
            return f"LLM Error: {outer}"
    
    # ---------------------------
    # Build Prompt with Structure Formatting
    # ---------------------------
    def build_prompt(self, user_query: str, context: str, sources: List[Dict[str, str]]):
        src_text = "\n".join(
            [f"- {s['title']}: {s['snippet']} (url: {s['link']})"
             for s in sources]
        ) if sources else "No sources available."
        
        prompt = f"""
You are **EduMentor**, an AI study assistant. Always reply in a clean structured format.

### 📌 RULES FOR EVERY RESPONSE
- If user greets → greet warmly + introduce yourself.
- Use clean formatting:
  - Headings (###)
  - Bullet points
  - Numbered steps
  - Code blocks if needed
  - Bold for key terms
- Give clear explanations suitable for students.
- Include examples whenever possible.
- End with a **2-line summary**.
- List **up to 3 helpful sources** at the end (if available).

### 📘 CONTEXT (Recent conversation)
{context if context else "No previous context."}

### 🔎 WEB SOURCES
{src_text}

### ❓ USER QUESTION
{user_query}

### 👉 NOW RESPOND FOLLOWING ALL RULES ABOVE
"""
        return prompt
    
    # ---------------------------
    # Main Answer Function
    # ---------------------------
    def answer(self, session_id: str, user_query: str) -> AgentResponse:
        trace_id = str(uuid.uuid4())
        logger.info("[%s] Query: %s", trace_id, user_query)
        start = time.time()
        
        # Check if this is a quiz request
        quiz_params = self.detect_quiz_request(user_query)
        
        if quiz_params:
            logger.info(f"[{trace_id}] Quiz detected: {quiz_params}")
            response_text = f"""
🎯 **Quiz Mode Activated!**

I'll generate a test on **{quiz_params['topic']}** for Class {quiz_params['class_level']} 
with {quiz_params['num_questions']} questions.

Click the "Start Quiz" button below to begin!
"""
            return AgentResponse(
                text=response_text,
                sources=[],
                metadata={
                    "trace_id": trace_id,
                    "elapsed_s": time.time() - start,
                    "time": datetime.now().isoformat()
                },
                is_quiz_request=True,
                quiz_params=quiz_params
            )
        
        # Normal conversation flow
        processed_query = self.preprocess_user_input(user_query)
        context = self.memory.get_recent_context(session_id, n=5)
        
        # Only search if not a greeting
        sources = []
        if processed_query == user_query:  # Not a greeting
            sources = self.search_tool.search(user_query, top_k=3)
        
        prompt = self.build_prompt(processed_query, context, sources)
        text = self._call_gemini(prompt)
        
        # Save memory
        self.memory.add_interaction(session_id, user_query, text, sources)
        
        elapsed = time.time() - start
        logger.info("[%s] Completed in %.2fs", trace_id, elapsed)
        
        return AgentResponse(
            text=text,
            sources=sources,
            metadata={
                "trace_id": trace_id,
                "elapsed_s": elapsed,
                "time": datetime.now().isoformat()
            }
        )