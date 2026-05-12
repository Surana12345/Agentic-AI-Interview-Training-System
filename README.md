# AI Interview Coach Platform 

An advanced, AI-native full-stack application designed to simulate real-world interview and debate scenarios. The platform leverages intelligent **Agentic AI Workflows** for cognitive performance evaluation and **Client-Side Computer Vision** for real-time behavioral and posture analysis.

---

##  Key Features

*   **Multi-Modal AI Architecture:** Moving beyond standard LLM wrappers, this platform utilizes **LangGraph** to orchestrate parallel AI agents. Dedicated agents simultaneously evaluate speech patterns, physical posture, semantic content, and emotion.
*   **Real-time Behavioral Tracking:** Integrates **MediaPipe** directly into the React frontend. This allows for live, client-side tracking of eye contact, slouching, fidgeting, and physical composure entirely inside the browser without heavy server rendering.
*   **Three Specialized Coaching Modules:**
    *    **Interview Mode:** Role-specific technical and HR mock interviews.
    *    **Debate Mode:** Practice formulating arguments and defending stances on complex topics.
    *    **Intro Mode:** Perfect the crucial 60-second elevator pitch.
*   **Intelligent Request Routing:** A dedicated Orchestrator Agent analyzes natural language prompts and automatically routes the user to the correct coaching module and topic.
*   **Comprehensive Data Dashboards:** Visualizes past performance, logic scores, and behavioral trends using dynamic `recharts`.

---

##  Technical Stack

This project is built using a modern, decoupled microservice-like architecture:

### Frontend (Client-Side)
*   **Framework:** React + Vite
*   **Routing:** React Router DOM
*   **Computer Vision:** `@mediapipe/camera_utils`, `pose`, `face_mesh`
*   **Styling & UI:** Custom CSS Modules, Recharts for data visualization
*   **State Management:** React Context API

### Backend (Server-Side)
*   **Framework:** FastAPI (Asynchronous Python API)
*   **AI & LLM Orchestration:** LangGraph, LangChain, Google Gemini Generative AI
*   **NLP & Audio Processing:** Specialized micro-services for audio transcription, logic scoring, and text-to-speech.
*   **Security:** JWT Authentication, Bcrypt Password Hashing

---

##  How It Works (The Engine)

The core evaluation logic heavily utilizes a graph-based state machine (`evaluation_orchestrator.py`). When a session ends:
1.  **Setup Node:** Extracts foundational metrics (chat history, raw posture data).
2.  **Parallel Execution:** 
    *   `speech_node`: Calculates words-per-minute, filler word frequency, and primary emotion.
    *   `posture_node`: Grades eye contact and physical composure based on MediaPipe telemetry.
    *   `content_node`: An LLM grades factual accuracy, argument framing, and logic.
3.  **Synthesis Node:** Aggregates multi-modal data into a cohesive confidence score and generates actionable qualitative feedback.

---

##  Installation & Setup

### Prerequisites
*   Node.js (v18+ recommended)
*   Python 3.10+
*   Google Gemini API Key

### 1. Clone the Repository
```bash
git clone <your-repository-url>
cd AI_Interview_Coach_Platform
```

### 2. Backend Setup
1. Navigate to the root directory.
2. Create `requirements.txt` environment (if not already acting in root venv):
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```
3. Establish your environment variables. Create a `.env` file in the root directory:
   ```env
   GOOGLE_API_KEY=your_gemini_api_key_here
   SECRET_KEY=your_jwt_secret_key
   ```
4. Start the FastAPI server (usually ran via the wrapper script):
   ```bash
   python run_backend.py
   ```
   *The backend will be available at `http://localhost:8000`*

### 3. Frontend Setup
1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```
2. Install dependencies:
   ```bash
   npm install
   ```
3. Start the Vite development server:
   ```bash
   npm run dev
   ```
   *The frontend will be available at `http://localhost:5173`*

---

## 📁 Project Structure

```text
📦 AI_Interview_Coach_Platform
├── 📂 backend
│   ├── 📂 app
│   │   ├── 📂 agents         # LangGraph Orchestrator, Debate/Interview Agents
│   │   ├── 📂 api            # FastAPI Routers (Auth, Realtime, Dashboard)
│   │   └── 📂 services       # Audio, NLP, Posture, and Evaluation engines
│   └── 📂 tests              # Pytest Unit Tests
├── 📂 frontend
│   ├── 📂 src
│   │   ├── 📂 components     # Reusable UI (LivePostureTracker, AudioRecorder)
│   │   ├── 📂 pages          # Route Views (Dashboard, InterviewMode, Intro)
│   │   ├── 📂 context        # AuthContext
│   │   └── 📂 services       # API client wrappers
└── 📜 run_backend.py         # Entrypoint to start Uvicorn
```

---

*This project was developed to push the boundaries of what is possible when combining realtime client-side computer vision with complex agentic AI workflows.*
