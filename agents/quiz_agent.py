# agents/quiz_agent.py
import os
import json
import logging
import google.genai as genai
from google.genai import types
from typing import List, Dict, Any
from dataclasses import dataclass

logger = logging.getLogger("quiz_agent")
logger.setLevel(logging.INFO)

API_KEY = os.getenv("GOOGLE_API_KEY")


@dataclass
class QuizQuestion:
    question: str
    options: List[str]
    correct_answer: int  # Index of correct option (0-3)
    explanation: str


class QuizAgent:
    """Generates MCQ tests on specific topics using AI"""
    
    def __init__(self):
        self.api_key = API_KEY
        if not self.api_key:
            logger.error("GOOGLE_API_KEY not found in environment variables")
        self.client = genai.Client(api_key=self.api_key) if self.api_key else None
    
    def generate_quiz(
        self, 
        topic: str, 
        class_level: str = "11", 
        num_questions: int = 5
    ) -> List[QuizQuestion]:
        """Generate MCQ quiz dynamically using Gemini AI"""
        
        if not self.client:
            logger.error("Quiz client not initialized - API key missing")
            return self._fallback_questions(topic)
        
        prompt = f"""
You are an expert educational quiz generator. Create {num_questions} multiple-choice questions (MCQs) 
specifically about "{topic}" suitable for Class {class_level} students.

CRITICAL REQUIREMENTS:
1. Questions MUST be directly related to "{topic}" only
2. Each question must have exactly 4 options (A, B, C, D)
3. Questions should be appropriate for Class {class_level} level
4. Include a mix of difficulty: easy, medium, hard
5. Provide clear, educational explanations for correct answers
6. Make questions practical and relevant to real learning

IMPORTANT: Return ONLY a valid JSON object (no markdown, no code blocks, no extra text).

Format:
{{
  "questions": [
    {{
      "question": "Your question here about {topic}?",
      "options": ["Option A text", "Option B text", "Option C text", "Option D text"],
      "correct_answer": 0,
      "explanation": "Detailed explanation of why this answer is correct and how it relates to {topic}."
    }}
  ]
}}

Generate {num_questions} questions now focused ONLY on: {topic}
"""
        
        try:
            response = self.client.models.generate_content(
                model="gemini-2.0-flash",
                contents=prompt,
                config=types.GenerateContentConfig(
                    max_output_tokens=3000,
                    temperature=0.8
                )
            )
            
            # Extract text from response
            text = self._extract_text(response)
            
            # Clean the response - remove markdown code blocks if present
            text = text.strip()
            if text.startswith("```json"):
                text = text[7:]
            if text.startswith("```"):
                text = text[3:]
            if text.endswith("```"):
                text = text[:-3]
            text = text.strip()
            
            # Parse JSON
            data = json.loads(text)
            questions = []
            
            for q in data.get("questions", []):
                # Validate the question has all required fields
                if all(key in q for key in ["question", "options", "correct_answer", "explanation"]):
                    if len(q["options"]) == 4:  # Ensure exactly 4 options
                        questions.append(QuizQuestion(
                            question=q["question"],
                            options=q["options"],
                            correct_answer=q["correct_answer"],
                            explanation=q["explanation"]
                        ))
            
            if len(questions) >= 3:  # At least 3 valid questions
                logger.info(f"Generated {len(questions)} questions for topic: {topic}")
                return questions[:num_questions]
            else:
                logger.warning(f"Only {len(questions)} valid questions generated, using fallback")
                return self._fallback_questions(topic)
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing error: {e}")
            logger.error(f"Response text: {text[:500] if 'text' in locals() else 'No response'}")
            return self._fallback_questions(topic)
        except Exception as e:
            logger.exception(f"Quiz generation failed: {e}")
            return self._fallback_questions(topic)
    
    def _extract_text(self, response) -> str:
        """Extract text from Gemini response"""
        try:
            if hasattr(response, "text") and response.text:
                return response.text
        except:
            pass
        
        try:
            candidates = getattr(response, "candidates", None)
            if candidates:
                content = getattr(candidates[0], "content", None)
                if content:
                    parts = getattr(content, "parts", [])
                    for part in parts:
                        if hasattr(part, "text"):
                            return part.text
        except:
            pass
        
        return str(response)
    
    def _fallback_questions(self, topic: str) -> List[QuizQuestion]:
        """Fallback questions if AI generation fails"""
        return [
            QuizQuestion(
                question=f"This is a sample question about {topic}. The quiz generator encountered an error.",
                options=[
                    "Please try again",
                    "Check your API key",
                    "Restart the server",
                    "Contact support"
                ],
                correct_answer=0,
                explanation=f"The AI failed to generate questions about {topic}. Please try again or check your API configuration."
            )
        ]
    
    def evaluate_answer(self, question: QuizQuestion, user_answer: int) -> Dict[str, Any]:
        """Evaluate user's answer"""
        is_correct = user_answer == question.correct_answer
        
        return {
            "correct": is_correct,
            "correct_answer": question.correct_answer,
            "explanation": question.explanation,
            "user_answer": user_answer
        }