# 🧞‍♂️ Study Genie - Your AI-Powered Study Companion

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**Study Genie** is an intelligent, multi-agent educational chatbot powered by Google's Gemini AI. It provides personalized study assistance, generates dynamic MCQ tests, summarizes PDFs, and maintains conversation context using session-based memory.

---

## ✨ Features

- 🤖 **AI-Powered Study Assistant** - Ask questions and get detailed, structured explanations
- 📝 **Dynamic MCQ Test Generator** - Generate custom tests on any topic for any grade level
- 📄 **PDF Summarization** - Upload PDFs and get AI-generated summaries
- 🔍 **Web Search Integration** - Fetches real-time information using Google Custom Search API
- 💾 **Session Memory** - Maintains conversation context across interactions
- 🎨 **Beautiful UI** - Responsive design with mobile support
- 📊 **Prometheus Metrics** - Built-in monitoring and analytics

---

## 🚀 Quick Start

### Prerequisites

- Python 3.9 or higher
- Google API Key (Gemini AI)
- Google Custom Search API credentials (optional)

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/study-genie.git
cd study-genie
```

### 2. Create Virtual Environment

```bash
# Create virtual environment
python -m venv venv
```

### 3. Activate Virtual Environment

**Windows:**
```bash
.\venv\Scripts\activate
```

**Linux/Mac:**
```bash
source venv/bin/activate
```

### 4. Install Dependencies

```bash
pip install -r requirements.txt
```

### 5. Setup Environment Variables

Create a `.env` file in the root directory:

```env
GOOGLE_API_KEY=your_gemini_api_key_here
GOOGLE_CSE_ID=your_custom_search_engine_id
USE_GEMINI=true
MEMORY_FILE=memory_bank.json
```

**How to get API keys:**
- **Google Gemini API**: Visit [Google AI Studio](https://aistudio.google.com/app/apikey)
- **Custom Search API**: Visit [Google Cloud Console](https://console.cloud.google.com/apis/credentials)

### 6. Start the Server

```bash
uvicorn main:app --reload
```

The application will be available at: **http://localhost:8000**

---

## 📦 Tech Stack

### Backend
- **FastAPI** - High-performance async web framework
- **Google Gemini AI** - Large language model for natural conversations
- **PyPDF2** - PDF text extraction
- **Prometheus Client** - Metrics and monitoring

### Frontend
- **HTML5/CSS3** - Modern, responsive UI
- **JavaScript (Vanilla)** - Interactive components
- **Marked.js** - Markdown rendering

### APIs & Services
- **Google Gemini 2.0 Flash** - AI model for text generation
- **Google Custom Search API** - Real-time web search
- **LocalStorage** - Session persistence

### Architecture Pattern
- **Multi-Agent System** - Specialized agents for different tasks
- **RESTful API** - Clean endpoint structure
- **Session-based Memory** - Context-aware conversations

---

## 🏗️ Project Architecture

### Directory Structure

```
study-genie/
│
├── agents/
│   ├── agent.py           # Main conversation agent
│   ├── quiz_agent.py      # MCQ test generator
│   └── pdf_agent.py       # PDF summarization agent
│
├── memory/
│   └── memorybank.py      # Session memory management
│
├── tools/
│   └── google_search.py   # Web search integration
│
├── template/
│   └── chat.html          # Main UI
│
├── static/
│   └── style.css          # Styling (if separated)
│
├── main.py                # FastAPI application
├── requirements.txt       # Python dependencies
├── .env                   # Environment variables (create this)
├── .gitignore            # Git ignore file
└── README.md             # This file
```

### System Flow

```
┌─────────────┐
│   User      │
│  Interface  │
└──────┬──────┘
       │
       ▼
┌─────────────────────────────────────────┐
│         FastAPI Server (main.py)        │
│  ┌─────────────────────────────────┐   │
│  │  /api/chat - Main conversation  │   │
│  │  /api/quiz/* - Quiz endpoints   │   │
│  │  /api/pdf/summarize - PDF proc  │   │
│  └─────────────────────────────────┘   │
└──────┬──────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────┐
│           Agent Router                  │
│  ┌─────────────────────────────────┐   │
│  │ 1. Detect Intent                │   │
│  │    - Normal question?            │   │
│  │    - Quiz request?               │   │
│  │    - PDF upload?                 │   │
│  └─────────────────────────────────┘   │
└──────┬──────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────┐
│        Specialized Agents               │
│  ┌──────────┐  ┌──────────┐  ┌──────┐  │
│  │   Main   │  │   Quiz   │  │ PDF  │  │
│  │  Agent   │  │  Agent   │  │Agent │  │
│  └────┬─────┘  └────┬─────┘  └───┬──┘  │
│       │             │             │     │
│       ▼             ▼             ▼     │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐ │
│  │ Search  │  │ Gemini  │  │PyPDF2 + │ │
│  │  Tool   │  │   AI    │  │ Gemini  │ │
│  └─────────┘  └─────────┘  └─────────┘ │
└──────┬──────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────┐
│         Memory Bank                     │
│  - Stores conversation history          │
│  - Provides context for continuity      │
│  - Session-based persistence            │
└─────────────────────────────────────────┘
```

### Detailed Flow: User Query to Response

1. **User Input** → User types a message or uploads a file

2. **Request Routing** → FastAPI receives the request at appropriate endpoint

3. **Intent Detection** → Main agent analyzes the query:
   - Keywords like "take a test" → Route to Quiz Agent
   - PDF upload → Route to PDF Agent
   - Normal question → Process with Main Agent

4. **Agent Processing**:
   - **Main Agent**: 
     - Checks memory for context
     - Searches web if needed
     - Generates response using Gemini
     - Saves to memory
   
   - **Quiz Agent**:
     - Extracts topic, grade level, question count
     - Generates MCQs using Gemini with structured prompt
     - Stores quiz state in memory
     - Returns questions one by one
   
   - **PDF Agent**:
     - Extracts text using PyPDF2
     - Sends to Gemini for summarization
     - Returns formatted summary

5. **Response Generation** → Agent formats response with markdown

6. **Memory Update** → Interaction saved to `memory_bank.json`

7. **UI Rendering** → Frontend displays response with proper formatting

---

## 🎯 Usage Examples

### 1. Ask Study Questions

```
User: "Explain photosynthesis for class 10"
Bot: [Provides detailed, structured explanation with examples]
```

### 2. Generate Quiz

```
User: "Take a test on Python Pandas for class 11 with 5 questions"
Bot: [Generates interactive MCQ test with explanations]
```

### 3. Summarize PDF

```
Click "📄 Upload PDF" → Select file → Get AI summary
```

### 4. Web Search

```
User: "What are the latest developments in quantum computing?"
Bot: [Searches web and provides current information with sources]
```

---

## 🔧 Configuration

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `GOOGLE_API_KEY` | Gemini API key | ✅ Yes |
| `GOOGLE_CSE_ID` | Custom Search Engine ID | ⚠️ Optional |
| `USE_GEMINI` | Enable/disable Gemini | ✅ Yes |
| `MEMORY_FILE` | Path to memory JSON file | ⚠️ Optional |

### API Rate Limits

- **Gemini API**: 60 requests/minute (free tier)
- **Custom Search API**: 100 queries/day (free tier)

---

## 📊 API Endpoints

### Chat Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/chat` | Main conversation endpoint |
| `GET` | `/api/history/{session_id}` | Get conversation history |

### Quiz Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/quiz/generate` | Generate new quiz |
| `POST` | `/api/quiz/answer` | Submit answer and get next question |

### PDF Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/pdf/summarize` | Upload and summarize PDF |

### Monitoring

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/metrics` | Prometheus metrics |

---

## 🧪 Testing

### Manual Testing

1. Start the server: `uvicorn main:app --reload`
2. Open browser: `http://localhost:8000`
3. Test features:
   - Chat conversation
   - Quiz generation
   - PDF upload

### Test Quiz Generation

```bash
curl -X POST "http://localhost:8000/api/quiz/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "test-123",
    "topic": "Python",
    "class_level": "11",
    "num_questions": 5
  }'
```

---

## 🐛 Troubleshooting

### Common Issues

**1. API Key Expired**
```
Error: API key expired. Please renew the API key.
```
**Solution**: Generate new API key from Google AI Studio

**2. Module Not Found**
```
ModuleNotFoundError: No module named 'google.genai'
```
**Solution**: Reinstall dependencies
```bash
pip install -r requirements.txt
```

**3. Port Already in Use**
```
Error: Address already in use
```
**Solution**: Change port or kill existing process
```bash
uvicorn main:app --reload --port 8001
```

**4. Memory Bank JSON Error**
```
json.decoder.JSONDecodeError
```
**Solution**: Delete `memory_bank.json` and restart server

---

## 🚀 Deployment

### Local Production

```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

### Docker (Optional)

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

Build and run:
```bash
docker build -t study-genie .
docker run -p 8000:8000 --env-file .env study-genie
```

---

## 🤝 Contributing

We welcome contributions! Here's how you can help:

### 1. Fork the Repository

Click the "Fork" button at the top right of this page.

### 2. Clone Your Fork

```bash
git clone https://github.com/yourusername/study-genie.git
cd study-genie
```

### 3. Create a Branch

```bash
git checkout -b feature/your-feature-name
```

### 4. Make Your Changes

- Add new features
- Fix bugs
- Improve documentation
- Optimize code

### 5. Commit Your Changes

```bash
git add .
git commit -m "Add: your feature description"
```

### 6. Push to Your Fork

```bash
git push origin feature/your-feature-name
```

### 7. Create Pull Request

Go to the original repository and click "New Pull Request"

### Contribution Guidelines

- Follow PEP 8 style guide for Python code
- Add docstrings to functions
- Test your changes before submitting
- Update README if adding new features
- Be respectful and constructive

---

## 🐛 Report Issues

Found a bug or have a feature request? Please create an issue!

### Before Creating an Issue

1. **Search existing issues** to avoid duplicates
2. **Check troubleshooting section** for common problems
3. **Gather information**:
   - Python version
   - Error messages
   - Steps to reproduce

### Create Issue

[**Report Bug**](https://github.com/yourusername/study-genie/issues/new?template=bug_report.md) | [**Request Feature**](https://github.com/yourusername/study-genie/issues/new?template=feature_request.md)

**Bug Report Template:**
```markdown
**Describe the bug**
A clear description of what the bug is.

**To Reproduce**
Steps to reproduce the behavior:
1. Go to '...'
2. Click on '....'
3. See error

**Expected behavior**
What you expected to happen.

**Screenshots**
If applicable, add screenshots.

**Environment:**
 - OS: [e.g. Windows 11]
 - Python Version: [e.g. 3.11]
 - Browser: [e.g. Chrome 120]
```

---

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- **Google Gemini AI** - For the powerful LLM API
- **FastAPI** - For the amazing web framework
- **Contributors** - Everyone who has contributed to this project

---

## 📧 Contact

**Project Maintainer**: [Your Name](mailto:your.email@example.com)

**Project Link**: [https://github.com/yourusername/study-genie](https://github.com/yourusername/study-genie)

---

## 🌟 Star This Project

If you find this project helpful, please consider giving it a ⭐️ on GitHub!

---

## 📈 Roadmap

- [ ] Add support for more file formats (DOCX, TXT)
- [ ] Implement user authentication
- [ ] Add voice input/output
- [ ] Create mobile app (Flutter)
- [ ] Add collaborative study rooms
- [ ] Integrate with educational platforms (Khan Academy, Coursera)
- [ ] Add progress tracking and analytics
- [ ] Support multiple languages

---

**Built with ❤️ for students everywhere**
