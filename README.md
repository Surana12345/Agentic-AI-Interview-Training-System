## Agentic AI-Driven Interview Training System Using Multi-Agent Architecture
_A smart, multi-agent interview training system that evaluates your speech, confidence, and body language in real time — delivering precise, AI-powered feedback that prepares you for every round, every role, and every challenge that a real interview demands._

## Project Overview
This project presents a sophisticated Agentic AI-Driven Interview Training System that reimagines interview preparation by combining agentic AI orchestration with real-time posture tracking to provide comprehensive, non-invasive coaching — evaluating what you say, how you say it, and how you present yourself, all simultaneously. Unlike traditional systems that rely on scripted interactions, keyword-based evaluation, and one-dimensional feedback, this system addresses every such limitation through a true multi-agent architecture where independent AI agents work in parallel to analyze audio confidence, language quality, content relevance, and upper-body posture using multimodal analysis. Situated strictly within the domains of Generative AI and Agentic AI, it employs a deterministic scoring mechanism that computes performance metrics mathematically, while Generative AI (Google Gemini) is used only to interpret those scores and generate concise improvement feedback — ensuring full explainability, consistency, and zero hallucination in grading.

The result is a realistic, self-paced interview practice environment with progress tracking that reduces dependency on human interviewers and measurably improves communication effectiveness.

**Key Capabilities:**

- Multi-Agent Evaluation: Parallel AI agents independently analyze speech patterns, posture, content quality, and emotional intelligence
- Real-Time Posture Tracking: MediaPipe analyzes body language and eye contact in real-time, running entirely client-side
- Three Coaching Modes: Interview Practice, Debate Training, and Self-Introduction coaching
- Performance Dashboard: Track progress across multiple sessions with historical analytics
- Secure Authentication: JWT-based user authentication with encrypted data storage
- Intelligent Intent Routing: NLP-based routing to automatically direct users to the appropriate coaching mode

---

## Objectives
- To design an Agentic AI-Driven Interview Training System for self-introduction, debate, and role-specific interview practice
- To implement a multi-agent architecture that independently evaluates speech, language, content relevance, and posture
- To provide explainable and deterministic scoring, separating evaluation from generative feedback
- To generate concise, actionable AI feedback to help users improve communication skills
- To reduce dependency on human interviewers while providing a realistic, self-paced practice environment

---

## Features

**Multi-Agent Evaluation Engine:**
The LangGraph orchestrator coordinates three specialized agents that run in parallel, each responsible for a distinct dimension of interview performance:

**Speech Analysis Agent:**
- Measures words-per-minute (WPM) to assess speaking pace
- Detects filler words ("um," "uh," "like") and calculates their frequency
- Analyzes tone and vocal confidence levels
- Calculates speech clarity and fluency scores

**Posture and Body Language Agent:**
- Eye contact detection using MediaPipe Face Mesh (468 facial landmarks)
- Body posture analysis using MediaPipe Pose (33 skeletal landmarks)
- Physical engagement and composure scoring
- Runs entirely client-side — no video is ever uploaded or stored

**Content Quality Agent:**
- Factual accuracy evaluation powered by Google Gemini LLM
- Argument structure and logical flow analysis
- Technical depth assessment for role-specific interviews
- Clarity of explanations grading

**Feature Integration and Synthesis:**
- Combines biometric and analytical data from all agents
- Aggregates multi-modal scores with weighted averaging
- Generates unified confidence classification (Low / Medium / High)
- Produces actionable feedback and specific recommendations for improvement

## Three Coaching Modes:

**Interview Mode:**
- Role-specific questions dynamically generated based on job title (Software Engineer, Data Analyst, HR Manager, etc.)
- Realistic interview scenarios with adaptive difficulty scaling
- Performance metrics specifically relevant to hiring decisions
- Real-time feedback on communication and professional presentation

**Debate Mode:**
- Users propose a topic and the AI takes the opposing side
- Argumentative reasoning and counter-argument handling evaluation
- Logical structure assessment and rhetorical effectiveness scoring
- Trains critical thinking and ability to reason under pressure

**Self-Introduction Mode:**
- Practice the classic "Tell me about yourself" elevator pitch
- Personal branding and story narrative quality evaluation
- Professional pitch effectiveness analysis
- Confidence and clarity metrics with delivery coaching

## Additional Features:

**Performance Dashboard:**
- Session-wise progress tracking with interactive charts
- Skill-wise breakdown (Logic, Confidence, Posture, Eye Contact)
- Historical trend analysis and comparative analytics across session types
- AI-generated coaching insights based on long-term patterns

**Secure Authentication:**
- JWT-based user authentication system
- Bcrypt password hashing for encrypted credential storage
- Protected routes ensuring private access to personal session data

**Intelligent Intent Routing:**
- NLP-based orchestrator agent analyzes natural language input
- Automatically routes users to the correct coaching mode
- Example: typing "I want to practice for a software engineer interview" routes directly to Interview Mode with the correct role pre-selected

---

## System Architecture
The system follows a modular and agent-based architecture consisting of a frontend interface and a backend processing system. The frontend allows users to select different modes and provide input in the form of audio and text. It also displays evaluation results including scores and feedback in a structured format. The backend performs all core processing — speech-to-text conversion, NLP analysis, multi-agent evaluation, score computation, and Generative AI feedback generation.

```
Session Input (Audio & Posture Data) + Chat History
                    ↓
      Data Preprocessing & Extraction
                    ↓
           Feature Integration
                    ↓
   Multi-Agent Processing (Parallel Execution)
      ┌─────────────┼─────────────┐
      ↓             ↓             ↓
┌──────────┐  ┌──────────┐  ┌──────────┐
│  Speech  │  │ Posture  │  │ Content  │
│  Agent   │  │  Agent   │  │  Agent   │
└────┬─────┘  └────┬─────┘  └────┬─────┘
     └─────────────┼─────────────┘
                   ↓
     Synthesis & Score Aggregation
                   ↓
   Confidence Classification (Low / Medium / High)
                   ↓
      Personalized Coaching Report
```

## Component Breakdown:

**Speech Agent:**
- Analyzes pacing, clarity, filler words
- Calculates words-per-minute and speech patterns
- Detects tone and confidence levels

**Posture Agent:**
- Evaluates eye contact and body alignment
- Scores physical engagement and composure
- Analyzes body language using MediaPipe skeletal tracking

**Content Agent:**
- Grades factual accuracy and argument structure
- Evaluates logical flow and technical depth
- Assesses clarity of explanations

---

## Tech Stack

**Languages and Tools:**
- Python 3.10+, SQLite, JavaScript (React), FastAPI

**Backend Libraries:**
- FastAPI 0.104+ for REST API framework
- LangGraph 0.2+ for AI agent orchestration
- LangChain 0.3+ for language model integration
- Google Generative AI for Gemini API access
- PyJWT and bcrypt for authentication
- Pandas and NumPy for data processing
- TextStat for text analysis
- Pydantic for data validation
- Pytest for testing
- Uvicorn as ASGI server

**Frontend Libraries:**
- React 18.2+ with JSX support
- Vite 4.4+ for build tooling
- React Router DOM 6.22+ for navigation
- MediaPipe Pose SDK for pose detection
- MediaPipe Face Mesh for facial tracking
- MediaPipe Camera Utils for camera access
- Recharts 2.12+ for data visualization

**Infrastructure:**
- Google Gemini API for content evaluation
- Web Audio API for real-time audio capture
- SQLite database for session persistence
- JWT-based authentication system

**Hardware Requirements:**
- Minimum 8GB RAM
- Modern web browser with WebGL support
- Webcam for posture tracking
- Microphone for audio capture

---

## Core Modules

The system is organized into five primary modules, each responsible for a distinct aspect of the interview training workflow:

### 1. Orchestration Module
The Orchestration Module acts as the central control unit. It receives user requests from the frontend through the FastAPI backend and determines which module should be activated — self-introduction, debate, or interview mode. The implementation uses LangChain/LangGraph with the Gemini language model for intelligent intent classification. When the user describes what they want to practice, the orchestration module analyzes the input using Generative AI structured output and routes it to the appropriate agent, extracting parameters like job role or debate topic automatically.

### 2. Self-Introduction Module
This module allows users to record their introduction using audio input while practicing structured responses. It provides real-time guidance and evaluates communication aspects such as clarity, confidence, and posture. The system transcribes the audio, runs it through the multi-agent evaluation pipeline, and generates a detailed coaching report covering speech quality, body language, and content delivery.

### 3. Debate Module
The debate module enables real-time conversation between the user and an AI opponent. Users can select or enter a custom topic, and the system prepares an interactive AI-driven environment for structured argumentation. The AI generates counter-arguments, evaluates the user's reasoning quality, and scores their rhetorical effectiveness. The system also incorporates posture analysis, mobile detection, multi-face detection, and real-time warnings to ensure focused and professional interaction.

### 4. Interview Questioning Module
This module allows users to customize their interview experience by selecting a job role (e.g., Software Engineer, Data Analyst, HR Manager, Product Manager) and difficulty level. The AI dynamically generates questions based on the selected parameters. During the session, the system performs multi-agent evaluation of communication, content relevance, confidence, and fluency, along with posture analysis and eye contact tracking. Questions adapt in difficulty based on the user's performance.

### 5. Performance Analysis Module
The performance analysis module provides an overview of interview training progress by displaying key metrics such as total sessions, average score, and mode-wise activity. It includes a skill assessment chart evaluating aspects like confidence, clarity, posture, and eye contact, along with session details, a progress timeline, and recent activity logs. This module helps users track performance over time and identify specific areas for improvement.

---

## Model Workflow

Understanding the complete data flow reveals the power of this Agentic AI system. Here is exactly what happens during a coaching session:

### Step 1: User Interaction (Input Stage)
The user speaks their answer into the microphone while looking at the camera. The browser simultaneously:
- Captures audio using the Web Audio API
- Extracts structural posture data (33 body landmarks + 468 face landmarks) using MediaPipe — running entirely on the client side
- No raw video is ever transmitted or stored

### Step 2: Data Transmission
Once the user finishes speaking, the audio file and the mathematical array of posture metrics are sent to the Python backend via a secure REST API call.

### Step 3: Setup Node
The LangGraph Evaluation Orchestrator takes over. The setup node:
- Transcribes the audio to text using speech processing
- Prepares the complete chat history for context
- Extracts foundational metrics for downstream agents

### Step 4: Parallel Agent Execution
Three specialized agents process the data simultaneously:

**Speech Node:** Analyzes the audio for pacing (WPM), filler word frequency, fluency score, and primary emotion detection.

**Posture Node:** Grades the MediaPipe telemetry array for eye contact percentage and physical composure score using deterministic mathematical formulas — not AI guesswork.

**Content Node:** The Generative AI (Gemini) evaluates the transcript against the original question for factual accuracy, argument structure, logical flow, and technical depth.

### Step 5: Synthesis Node
An aggregator node collects the distinct, independently computed scores from all three agents. It:
- Computes a final weighted confidence score
- Classifies overall performance as Low, Medium, or High confidence
- Generates qualitative AI feedback by interpreting the numerical scores

### Step 6: Final Output (Feedback Stage)
The system returns a comprehensive, categorized evaluation report to the user containing:
- Overall confidence score (0-100)
- Speech score (pacing, clarity, filler word count)
- Posture score (eye contact percentage, body alignment grade)
- Content score (accuracy, logic, depth)
- Personalized feedback with specific, actionable recommendations

```
evaluation_orchestrator.py workflow:

workflow = StateGraph(EvaluationState)
workflow.add_node("setup_node", setup_node)
workflow.add_node("speech_node", speech_node)
workflow.add_node("posture_node", posture_node)
workflow.add_node("content_node", content_node)
workflow.add_node("synthesis_node", synthesis_node)
workflow.add_edge(START, "setup_node")
workflow.add_edge("setup_node", "speech_node")
workflow.add_edge("setup_node", "posture_node")
workflow.add_edge("setup_node", "content_node")
workflow.add_edge("speech_node", "synthesis_node")
workflow.add_edge("posture_node", "synthesis_node")
workflow.add_edge("content_node", "synthesis_node")
workflow.add_edge("synthesis_node", END)
evaluation_orchestrator = workflow.compile()
```

This code defines the evaluation workflow using LangGraph. Different nodes handle speech analysis, posture evaluation, content scoring, and final synthesis. All results are combined to generate the final performance report. This implementation represents the multi-agent architecture used in the system.

---

## Key Components

## Backend Services:

**Audio Service:**
- Real-time audio capture from browser
- Audio transcription and speech-to-text processing
- Speech pattern extraction and analysis

**Content Analysis Service:**
- LLM-powered evaluation using Google Gemini API
- Factual accuracy grading against expected responses
- Response quality and communication effectiveness evaluation

**Emotion Service:**
- Tone detection from speech patterns
- Confidence level analysis and classification
- Emotional engagement scoring

**Evaluation Service:**
- Score aggregation from all independent agents
- Weighted scoring calculation with configurable parameters
- Overall performance grading and confidence classification

**NLP Service:**
- Text processing, cleaning, and normalization
- Linguistic metric calculation (readability, complexity, vocabulary)
- Feature extraction from transcripts for downstream analysis

## Frontend Components:

**AudioRecorder:**
- WebAudio API integration for high-quality capture
- Real-time recording control with visual feedback
- Audio quality monitoring and format handling

**LivePostureTracker:**
- MediaPipe Pose model initialization (33 body landmarks)
- MediaPipe Face Mesh integration (468 facial landmarks)
- Real-time pose detection, visualization, and landmark tracking
- Client-side processing — no video data leaves the browser

**EvaluationReport:**
- Score visualization with categorized metrics display
- Detailed feedback presentation with strengths and weaknesses
- Performance metrics charts using Recharts

---

## File & Folder Structure

```
Agentic-AI-Driven-Interview-Training-System/
├── backend/
│   ├── app/
│   │   ├── agents/                         # AI reasoning & evaluation agents
│   │   │   ├── debate_agent.py             # Debate topic generation & AI counter-arguments
│   │   │   ├── evaluation_orchestrator.py  # LangGraph multi-agent state machine
│   │   │   ├── interview_agent.py          # Interview greeting, evaluation, follow-ups
│   │   │   ├── intro_agent.py              # Self-introduction audio analysis agent
│   │   │   ├── orchestrator_agent.py       # NLP intent routing & module selection
│   │   │   └── __init__.py
│   │   ├── api/                            # REST API endpoint routes
│   │   │   ├── routes_auth.py              # JWT login/register endpoints
│   │   │   ├── routes_dashboard.py         # Performance statistics & analytics
│   │   │   ├── routes_debate.py            # Debate session endpoints
│   │   │   ├── routes_interview.py         # Interview session endpoints
│   │   │   ├── routes_intro.py             # Self-intro evaluation endpoint
│   │   │   ├── routes_orchestrator.py      # Intent classification endpoint
│   │   │   └── __init__.py
│   │   ├── services/                       # Utility micro-services
│   │   │   ├── audio_service.py            # Audio transcription & processing
│   │   │   ├── content_analysis_service.py # LLM-powered content grading
│   │   │   ├── emotion_service.py          # Emotion & tone detection
│   │   │   ├── evaluation_service.py       # Score computation & aggregation
│   │   │   ├── nlp_service.py              # NLP utilities & text processing
│   │   │   └── __init__.py
│   │   ├── dependencies.py                 # Shared dependency injection
│   │   ├── main.py                         # FastAPI application entry point
│   │   └── __init__.py
│   ├── data/
│   │   └── questions/                      # Role-specific question banks (CSV)
│   │       ├── software_engineer.csv
│   │       ├── data_analyst.csv
│   │       ├── hr_manager.csv
│   │       ├── product_manager.csv
│   │       ├── marketing_specialist.csv
│   │       ├── software_tester.csv
│   │       └── full_stack_developer.csv
│   └── tests/                              # Automated testing suite
│       ├── test_unit.py                    # Unit tests for individual functions
│       ├── test_integration.py             # Integration tests for component interaction
│       ├── test_services.py                # Service-specific test coverage
│       ├── test_system.py                  # End-to-end system workflow tests
│       └── __init__.py
├── frontend/
│   ├── src/
│   │   ├── components/                     # Reusable UI components
│   │   │   ├── AudioRecorder.jsx           # Voice recording with Web Audio API
│   │   │   ├── LivePostureTracker.jsx      # MediaPipe posture tracking component
│   │   │   ├── EvaluationReport.jsx        # AI feedback report display
│   │   │   └── EvaluationReport.module.css
│   │   ├── pages/                          # Application page views
│   │   │   ├── Dashboard.jsx               # Performance analytics dashboard
│   │   │   ├── InterviewMode.jsx           # Interview practice interface
│   │   │   ├── DebateMode.jsx              # Debate practice interface
│   │   │   ├── SelfIntroductionMode.jsx    # Intro practice interface
│   │   │   ├── LoginPage.jsx               # Authentication page
│   │   │   ├── Dashboard.module.css
│   │   │   └── SessionMode.module.css
│   │   ├── context/
│   │   │   └── AuthContext.jsx             # React Context for authentication state
│   │   ├── api/
│   │   │   ├── config.js                   # API endpoint configuration
│   │   │   └── authFetch.js                # Authenticated HTTP client
│   │   ├── utils/
│   │   │   └── tts.js                      # Text-to-Speech utility
│   │   ├── App.jsx                         # Root application with routing
│   │   ├── main.jsx                        # React entry point
│   │   └── index.css                       # Global styles
│   ├── index.html
│   ├── package.json
│   └── vite.config.js
├── .gitignore
├── requirements.txt                        # Python dependencies
├── run_backend.py                          # Backend server launcher (Uvicorn)
└── README.md
```

---

## Installation & Setup

**Prerequisites:**
- Node.js v18 or higher with npm
- Python 3.10 or higher
- Google Gemini API Key (available free at aistudio.google.com)
- Web browser with WebGL support
- Webcam and microphone

## Setup Instructions:

1. Clone and Configure:
```bash
git clone https://github.com/Surana12345/Agentic-AI-Interview-Training-System.git
cd Agentic-AI-Interview-Training-System
```

2. Add Environment Variables — create a `.env` file in the root directory:
```
GOOGLE_API_KEY=your_gemini_api_key_here
SECRET_KEY=your_jwt_secret_key_here
```

Generate JWT secret:
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

3. Start Backend Server:
```bash
python -m venv venv

# On Windows:
venv\Scripts\activate

# On macOS/Linux:
source venv/bin/activate

pip install -r requirements.txt
python run_backend.py
```
Backend API will run at: http://localhost:8000

4. Start Frontend Application:
```bash
cd frontend
npm install
npm run dev
```
Frontend will run at: http://localhost:5173

5. Access the Application:
   - Open http://localhost:5173 in your web browser
   - Create a new account with email and password
   - Begin your first coaching session

---

## Running Individual Modules
The backend is organized into modular components that can be tested independently:

**Core Services (Python modules):**
- Audio transcription and processing
- Content analysis with LLM
- Emotion and tone detection
- Evaluation and score aggregation
- NLP utilities and text processing

**Frontend Components (React):**
- Audio recording interface
- Posture tracking visualization
- Session participation UI
- Results and evaluation display

---

## System Workflow

1. Create Account:
   Sign up with email and password on the login page

2. Describe Your Goal:
   Tell the AI what you want to practice
   Example: "I want to practice for a software engineer interview"

3. Start Session:
   The system automatically routes you to the appropriate coaching mode based on your request

4. Participate in Session:
   Answer questions from the AI coach while your posture and audio are analyzed in real-time

5. Receive Evaluation:
   After the session ends, you will receive:
   - Overall confidence score (0-100)
   - Speech score (pacing, clarity, filler words)
   - Posture score (eye contact, body alignment)
   - Content score (accuracy, logic, depth)
   - Personalized feedback and actionable recommendations

6. Track Progress:
   View your performance dashboard to see:
   - Historical session data
   - Improvement trends
   - Comparative analytics across different session types

---

## Testing & Evaluation
The backend includes a comprehensive testing suite organized by scope:

Run all tests:
```bash
pytest backend/tests/ -v
```

Run unit tests only:
```bash
pytest backend/tests/test_unit.py -v
```

Run integration tests:
```bash
pytest backend/tests/test_integration.py -v
```

Run system tests:
```bash
pytest backend/tests/test_system.py -v
```

Run service-specific tests:
```bash
pytest backend/tests/test_services.py -v
```

**API Documentation:**
Access interactive API documentation at http://localhost:8000/docs (when backend server is running)

---

## Future Enhancements
Although the system provides an effective platform for interview training, several enhancements can be implemented to improve its capabilities:
- Integration of real-time video analysis for facial micro-expression evaluation
- Implementation of adaptive questioning based on overall cumulative user performance
- Addition of multilingual support for wider accessibility
- Enhancement of evaluation models for deeper contextual and reasoning analysis
- Development of mobile applications for better usability and on-the-go practice
- Integration with real interview datasets for improved accuracy and realism
- Integration of realistic 3D generative avatars to replace text-based interviewers

With these improvements, the system can evolve into a more advanced and comprehensive interview training platform.

---

## Conclusion
The Agentic AI-Driven Interview Training System for communication skill enhancement implements a multi-agent architecture enabling realistic and dynamic interview simulations. It supports self-introduction, debate, and role-specific interview questioning through multimodal analysis for evaluating confidence, clarity, posture, and content relevance. AI-generated feedback provides actionable insights for continuous improvement. The system's ability to combine deterministic evaluation with intelligent generative feedback demonstrates the effectiveness of separating scoring from interpretation. Overall, the developed system reduces dependency on human interviewers, enables self-paced learning, and enhances interview readiness through continuous feedback and performance tracking. The self-paced practice environment reduces anxiety and boosts interview performance.

---

_This project demonstrates proficiency in **multi-modal AI system design**, **agentic AI orchestration** (LangGraph), **real-time computer vision** (MediaPipe), **NLP pipeline engineering** (deterministic + LLM hybrid scoring), **full-stack web development** (React + FastAPI), and **software engineering best practices** (modular architecture, testing, authentication, error handling)._

---
