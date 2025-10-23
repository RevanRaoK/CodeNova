# CodeReviewAI - AI-Powered Code Analysis Tool

## Project Overview

CodeReviewAI is a full-stack web application that uses artificial intelligence to analyze code for security vulnerabilities, code quality issues, and best practice violations. The system leverages Google's Gemini AI to provide intelligent code suggestions and feedback.

## Features

### 1. AI-Powered Code Analysis
- Analyzes code in multiple programming languages (JavaScript, Python, Java, C++, etc.)
- Detects security vulnerabilities (hardcoded passwords, SQL injection, XSS, etc.)
- Identifies code quality issues (unused variables, deprecated functions, etc.)
- Provides line-by-line suggestions with severity levels

### 2. Interactive Code Editor
- Monaco Editor integration for syntax highlighting
- Real-time code editing
- File upload support
- Multiple language support

### 3. Feedback System
- Users can accept, reject, or modify AI suggestions
- Feedback is stored for AI model improvement
- Tracks user satisfaction with suggestions

### 4. Analytics Dashboard
- View analysis statistics
- Track usage trends
- Monitor feedback distribution
- Performance metrics

### 5. Analysis History
- View past code analyses
- Reload previous results
- Track analysis over time

## Technology Stack

### Frontend
- **Framework:** React 18
- **UI Library:** Tailwind CSS
- **Code Editor:** Monaco Editor
- **Charts:** Recharts
- **HTTP Client:** Axios
- **Routing:** React Router

### Backend
- **Framework:** FastAPI (Python)
- **Database:** PostgreSQL
- **ORM:** SQLAlchemy
- **Authentication:** JWT
- **AI Integration:** Google Gemini API
- **Code Parsing:** AST Parser

### Infrastructure
- **API Documentation:** Swagger/OpenAPI
- **CORS:** Enabled for development
- **Environment:** Python 3.11+, Node.js 18+

## Setup Instructions

### Prerequisites
- Python 3.11 or higher
- Node.js 18 or higher
- PostgreSQL database
- Google Gemini API key

### Backend Setup

1. Navigate to backend directory:
```bash
cd backend
```

2. Create virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create `.env` file:
```env
DATABASE_URL=postgresql://user:password@localhost:5432/codereviewer
GEMINI_API_KEY=your_gemini_api_key_here
JWT_SECRET=your_secret_key_here
```

5. Run database migrations:
```bash
python create_tables.py
```

6. Start the backend server:
```bash
python -m uvicorn app.main:app --reload --port 8000
```

Backend will be available at: http://localhost:8000

### Frontend Setup

1. Navigate to frontend directory:
```bash
cd frontend
```

2. Install dependencies:
```bash
npm install
```

3. Create `.env` file:
```env
VITE_API_URL=http://localhost:8000/api/v1
```

4. Start the development server:
```bash
npm run dev
```

Frontend will be available at: http://localhost:5173

## Usage

### 1. Register/Login
- Create a new account or login with existing credentials
- JWT token is stored for authentication

### 2. Analyze Code
- Go to "Code Review" page
- Paste your code or upload a file
- Select the programming language
- Click "Analyze Code"
- Wait for AI analysis (30-60 seconds)
- View detected issues with suggestions

### 3. Provide Feedback
- Click thumbs up (👍) to accept a suggestion
- Click thumbs down (👎) to reject a suggestion
- Add comments for detailed feedback

### 4. View History
- Click "View History" to see past analyses
- Click "View Results" to reload previous analysis
- Track your code quality over time

### 5. Check Dashboard
- View analysis statistics
- See usage trends
- Monitor feedback distribution

## API Documentation

Once the backend is running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Key Endpoints

### Authentication
- `POST /api/v1/auth/signup` - Register new user
- `POST /api/v1/auth/login` - Login user

### Code Analysis
- `POST /api/v1/analysis/analyze-code` - Analyze code
- `GET /api/v1/analysis/direct/history` - Get analysis history
- `GET /api/v1/analysis/direct/{analysis_id}` - Get specific analysis

### Feedback
- `POST /api/v1/feedback` - Submit feedback
- `GET /api/v1/feedback/history` - Get feedback history
- `GET /api/v1/feedback/stats` - Get feedback statistics

### Analytics
- `GET /api/v1/analytics/user-stats` - Get user statistics
- `GET /api/v1/analytics/usage-trends` - Get usage trends
- `GET /api/v1/analytics/feedback-distribution` - Get feedback distribution

## Security Features

- JWT-based authentication
- Password hashing with bcrypt
- SQL injection prevention (parameterized queries)
- XSS protection
- CORS configuration
- Input validation
- Rate limiting (planned)

## AI Analysis Capabilities

The system can detect:
- **Security Issues:** Hardcoded credentials, SQL injection, XSS vulnerabilities
- **Code Quality:** Unused variables, deprecated functions, code smells
- **Best Practices:** Naming conventions, code structure, documentation
- **Performance:** Inefficient algorithms, memory leaks
- **Maintainability:** Code complexity, duplication

## Project Structure

```
project/
├── backend/
│   ├── app/
│   │   ├── api/          # API endpoints
│   │   ├── core/         # Core configuration
│   │   ├── models/       # Database models
│   │   ├── schemas/      # Pydantic schemas
│   │   ├── services/     # Business logic
│   │   └── utils/        # Utility functions
│   ├── requirements.txt
│   └── .env
├── frontend/
│   ├── components/       # React components
│   ├── pages/           # Page components
│   ├── services/        # API services
│   ├── contexts/        # React contexts
│   ├── package.json
│   └── .env
└── README.md
```

## Testing

### Backend Tests
```bash
cd backend
pytest
```

### Frontend Tests
```bash
cd frontend
npm test
```

## Known Issues

- Analysis may take 30-60 seconds for large files
- Gemini API has rate limits
- Some languages have better detection than others

## Future Enhancements

- Real-time collaboration
- GitHub integration
- Custom rule configuration
- Team workspaces
- CI/CD integration
- More AI models support

## Contributors

[Your Name]
[Your Email]
[Your College/University]

## License

This project is for educational purposes.

## Acknowledgments

- Google Gemini AI for code analysis
- FastAPI for the backend framework
- React for the frontend framework
- Monaco Editor for code editing
