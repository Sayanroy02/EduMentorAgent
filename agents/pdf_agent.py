# agents/pdf_agent.py
import os
import logging
import PyPDF2
import google.genai as genai
from google.genai import types
from typing import Dict, Any
from io import BytesIO

logger = logging.getLogger("pdf_agent")
logger.setLevel(logging.INFO)

API_KEY = os.getenv("GOOGLE_API_KEY")


class PDFAgent:
    """Extracts and summarizes PDF documents"""
    
    def __init__(self):
        self.api_key = API_KEY
        if not self.api_key:
            logger.error("GOOGLE_API_KEY not found")
        self.client = genai.Client(api_key=self.api_key) if self.api_key else None
        self.max_chars = 15000  # Limit to avoid token overflow
    
    def extract_text_from_pdf(self, pdf_bytes: bytes) -> str:
        """Extract text from PDF bytes"""
        try:
            pdf_file = BytesIO(pdf_bytes)
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            
            text = ""
            num_pages = len(pdf_reader.pages)
            
            # Extract text from all pages (limit to first 20 pages for free tier)
            for page_num in range(min(num_pages, 20)):
                page = pdf_reader.pages[page_num]
                text += page.extract_text() + "\n\n"
            
            logger.info(f"Extracted {len(text)} characters from {num_pages} pages")
            
            # Truncate if too long
            if len(text) > self.max_chars:
                text = text[:self.max_chars] + "\n\n[Document truncated for processing...]"
            
            return text
            
        except Exception as e:
            logger.exception(f"PDF extraction failed: {e}")
            return ""
    
    def summarize_text(self, text: str, summary_type: str = "general") -> Dict[str, Any]:
        """Summarize extracted text using Gemini"""
        
        if not text or len(text.strip()) < 100:
            return {
                "success": False,
                "error": "PDF is empty or text extraction failed"
            }
        
        if not self.client:
            return {
                "success": False,
                "error": "AI client not initialized - check API key"
            }
        
        # Different prompts based on summary type
        prompts = {
            "general": f"""
Summarize the following document in a clear, structured format:

### 📄 Document Summary

Provide:
1. **Main Topic**: What is this document about?
2. **Key Points**: List 5-7 main takeaways
3. **Important Details**: Notable facts, figures, or concepts
4. **Conclusion**: Overall summary in 2-3 sentences

Document text:
{text}
""",
            "detailed": f"""
Provide a detailed analysis of the following document:

### 📄 Detailed Analysis

Include:
1. **Executive Summary**: Overview in 3-4 sentences
2. **Main Sections**: Break down the major sections
3. **Key Concepts**: Important terms and definitions
4. **Data & Statistics**: Notable numbers, dates, facts
5. **Conclusions**: Final takeaways

Document text:
{text}
""",
            "bullet": f"""
Create a bullet-point summary of this document:

### 📄 Quick Summary

Provide:
- Main topic
- 5-10 key bullet points
- Most important takeaway

Document text:
{text}
"""
        }
        
        prompt = prompts.get(summary_type, prompts["general"])
        
        try:
            response = self.client.models.generate_content(
                model="gemini-2.0-flash",
                contents=prompt,
                config=types.GenerateContentConfig(
                    max_output_tokens=1500,
                    temperature=0.3
                )
            )
            
            summary = self._extract_text(response)
            
            return {
                "success": True,
                "summary": summary,
                "original_length": len(text),
                "summary_length": len(summary)
            }
            
        except Exception as e:
            logger.exception(f"Summarization failed: {e}")
            return {
                "success": False,
                "error": f"Summarization failed: {str(e)}"
            }
    
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
    
    def process_pdf(self, pdf_bytes: bytes, summary_type: str = "general") -> Dict[str, Any]:
        """Main method to process PDF: extract text and summarize"""
        
        # Extract text
        text = self.extract_text_from_pdf(pdf_bytes)
        
        if not text:
            return {
                "success": False,
                "error": "Could not extract text from PDF"
            }
        
        # Summarize
        result = self.summarize_text(text, summary_type)
        
        return result