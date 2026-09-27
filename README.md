# 🎓 OpporSphere — Student Opportunity Discovery Platform

> A full-stack web application connecting college students to curated internships, hackathons, scholarships, courses, competitions, full-time jobs, and research fellowships powered by a transparent skill-matching recommendation engine.

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-3.1.3-green.svg)](https://flask.palletsprojects.com/)
[![SQLite](https://img.shields.io/badge/Database-SQLite-lightgrey.svg)](https://www.sqlite.org/)
[![License](https://img.shields.io/badge/License-MIT-purple.svg)](LICENSE)

---

## 📌 Project Objective

College students often struggle with opportunity fragmentation—searching across dozens of disjointed job portals, hackathon lists, academic boards, and government scholarship sites. 

**OpporSphere** solves this problem by providing a unified, centralized platform where students discover high-impact opportunities tailored specifically to their academic degree, current technical skills, and career interests, complete with an explainable match scoring engine and an application pipeline tracker.

---

## ✨ Core Features

### 1. Modern Responsive Landing Page
- Dynamic platform statistics (Active Opportunities, Registered Students, Tracked Applications, Categories).
- Interactive 3-step *How It Works* roadmap.
- Opportunity category grid with custom visual branding.
- Closing Soon & Featured opportunities preview with urgency countdowns.

### 2. Student Authentication & Session Security
- Secure registration and login with **Werkzeug** password hashing (`pbkdf2:sha256`).
- Session-based authentication with role-based access control (`is_admin`).
- Pre-seeded **1-click demo login buttons** for instant evaluation during hackathon judging.

### 3. Student Profile & Skill Management
- Profile completeness progress meter.
- Technical skills management with clickable chip selector for popular skills (`Python`, `C++`, `Java`, `SQL`, `AI`, `Machine Learning`, `React`, etc.).
- Custom interests, academic degree, major/branch, year of study, experience level, and preferred location/work mode.

### 4. Opportunity Database & Categorization
- Pre-seeded with 15 rich, realistic opportunities across **7 distinct categories**:
  - 💼 **Internships** (Google Summer of Code, AWS Cloud Solutions Architecture)
  - ⚡ **Hackathons** (Smart India Hackathon, NASA International Space Apps)
  - 🏅 **Scholarships** (Reliance Foundation Undergraduate, Tata Trust Higher Education)
  - 📚 **Courses** (DeepLearning.AI Machine Learning Specialization, Harvard CS50 Web)
  - 🎯 **Jobs** (Goldman Sachs Summer Engineering Analyst, Stripe Associate Software Engineer)
  - 🏆 **Competitions** (Microsoft Imagine Cup, Kaggle Community AI Innovation Cup)
  - 🔬 **Research** (ISRO Student Satellite Research, CERN Summer Student Programme, MIT Media Lab)
- Structured for **seamless migration from SQLite to MySQL**.

### 5. Multi-Faceted Search & Filtering
- Keyword search across title, organization, description, and required skills.
- Category filter pills (Internship, Hackathon, Scholarship, Course, Job, Competition, Research).
- Work mode filter (Online, On-site, Hybrid).
- Skill-based query filtering and location search.
- Multi-criteria sorting:
  - Highest Match % (tailored to student's skills)
  - Deadline (soonest closing first)
  - Recently added
  - Alphabetical (A-Z)

### 6. Transparent Skill-Based Recommendation Engine
- **Direct Skill Match**: Compares student skills against required opportunity qualifications.
- **Explainable Breakdown**: Displays:
  - 🟢 **Matching Skills**: Technical skills the student currently possesses.
  - 🟡 **Missing Skills**: Required skills the student needs to acquire.
  - ⚡ **Match Percentage Badge**: High Match (75%+), Good Match (50-74%), Potential Match (<50%).
  - 💡 **Human-readable explanation**: Transparent rationale explaining why the opportunity was recommended.
- Modular architecture with clean extension hooks for future ML/AI embeddings.

### 7. Student Command Center (Dashboard)
- Visual metrics: Total Available Opportunities, High Matches, Saved Bookmarks, Tracked Applications.
- **Chart.js** Donut Chart visualizing the student's active application status distribution.
- Top recommended opportunities slider/grid.
- **Urgent Deadlines Widget**: Real-time days remaining with animated `Closing Soon` badges.

### 8. Saved Opportunities (Personal Bookmarks)
- Bookmark and un-bookmark opportunities with asynchronous 1-click toggles.
- Dedicated `/saved` page for reviewing shortlisted roles.

### 9. Application Lifecycle Tracking
- Multi-stage pipeline tracker:
  - ⭐ **Interested**
  - 📝 **Applied**
  - 🎯 **Shortlisted**
  - 🎉 **Selected**
  - ❌ **Rejected**
- Add personal notes, interview dates, and submission stage history.

### 10. Administrator Management Console
- Role-gated admin portal (`@admin_required`).
- Add, Edit, and Delete opportunities with real-time modal forms.
- View registered student directory with academic majors, years, and skill tags.
- Opportunity applicant count analytics.

---

## 🛠️ Technology Stack

| Layer | Technologies Used |
| :--- | :--- |
| **Frontend** | HTML5, CSS3 (Modern Glassmorphism & Custom Tokens), Vanilla JavaScript (ES6+), Chart.js |
| **Backend** | Python 3.10+, Flask 3.1.3, Jinja2 |
| **Security** | Werkzeug Security (Password Hashing), Session Authentication, Parameterized SQL Queries |
| **Database** | SQLite 3 (`database.db`) with MySQL-compatible DDL schemas |
| **Architecture** | RESTful APIs, MVC structure, Rule-based Recommendation Engine |

---

## 📁 Project Structure

```text
student-opportunity-platform/
│
├── app.py                     # Flask application entry point & route controllers
├── database.py                # Database connection, schemas, and seed dataset
├── recommendation.py          # Explainable recommendation engine & skill parser
├── requirements.txt           # Python package dependencies
├── database.db                # SQLite database (auto-created on first run)
├── test_app.py                # Unit & integration test suite (9 test cases)
│
├── templates/                 # Jinja2 HTML5 Templates
│   ├── base.html              # Layout shell, navigation bar, alerts, footer & modals
│   ├── index.html             # Landing page with stats, how-it-works & preview
│   ├── login.html             # Unified student & admin login with 1-click demo filler
│   ├── register.html          # Student onboarding with interactive skill pills
│   ├── dashboard.html         # Student command center with Chart.js & deadlines
│   ├── profile.html           # Skill preferences & academic profile manager
│   ├── opportunities.html     # Discovery catalog with search, filters & cards
│   ├── opportunity_details.html # Detailed view with skill breakdown & tracker
│   ├── saved.html             # Bookmarked opportunities page
│   ├── applications.html      # Application lifecycle pipeline manager
│   └── admin.html             # Admin console for CRUD operations & student list
│
├── static/                    # Frontend Static Assets
│   ├── css/
│   │   └── style.css          # Modern CSS design system & responsive layout
│   └── js/
│       └── script.js          # Asynchronous bookmarking, tracking & modal handlers
│
└── README.md                  # Comprehensive project documentation
```

---

## 🚀 Installation & Local Setup

### 1. Prerequisites
- **Python 3.10 or higher** installed on your system.
- Git (optional).

### 2. Clone or Navigate to the Project Directory
```bash
cd HACKHOTHON
```

### 3. Create and Activate Virtual Environment

**On Windows (PowerShell / Command Prompt):**
```powershell
python -m venv .venv
.venv\Scripts\activate
```

**On macOS / Linux:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 4. Install Dependencies
```bash
pip install -r requirements.txt
```

### 5. Run the Application
```bash
python app.py
```

Open your browser and navigate to:
```
http://127.0.0.1:5000
```
*(The database will automatically initialize and populate 15 sample opportunities and demo accounts on first launch!)*

---

## 🧪 Running Automated Tests

Run the complete test suite verifying authentication, APIs, recommendations, and admin functions:

```bash
python -m unittest test_app.py
```

All 9 test cases should report `OK`.

---

## 🔑 Demonstration Accounts

For hackathon presentation and quick evaluation, the system comes pre-seeded with two accounts. The login page also features **1-click buttons** to automatically fill these credentials:

| Role | Email | Password | Pre-configured Skills / Permissions |
| :--- | :--- | :--- | :--- |
| **🎓 Student** | `student@college.edu` | `student123` | Python, SQL, HTML, CSS, JavaScript, Machine Learning |
| **⚡ Administrator** | `admin@platform.com` | `admin123` | Full access to add/edit/delete opportunities & view students |

---

## 🧠 How the Recommendation Engine Works

The recommendation system in `recommendation.py` implements a transparent, explainable rule-based algorithm:

```text
Student Skills + Interests + Preferences  ──┐
                                            ├──►  Recommendation Engine  ──►  Match % + Breakdown
Opportunity Required Skills + Mode + Type ──┘
```

### Mathematical Formula:
$$\text{Score} = (\text{Skill Ratio} \times 0.65) + (\text{Interest Resonance} \times 0.20) + (\text{Preference Alignment} \times 0.15)$$

1. **Skill Normalization & Alias Resolution**:
   - Skills are normalized (e.g. `JS` $\rightarrow$ `JavaScript`, `ML` $\rightarrow$ `Machine Learning`, `C++` $\rightarrow$ `c++`).
   - Checks for exact matches and sub-skill containment (e.g. `AI` matches within `AI/ML`).
2. **Matching vs. Missing Classification**:
   - $\text{Matching Skills} = S_{\text{student}} \cap O_{\text{required}}$
   - $\text{Missing Skills} = O_{\text{required}} \setminus S_{\text{student}}$
3. **Interest & Type Boost**:
   - If student's stated interests appear in the opportunity title or description, an interest resonance bonus is awarded.
   - If the opportunity matches the student's preferred type (e.g. `Internship`), a preference alignment bonus is added.
4. **Transparent Output**:
   - Returns exact integer score (0–100%), color-coded badge (`High Match`, `Good Match`, `Potential Match`), and an English rationale.

### Future ML / AI Upgrade Hook:
The `BaseRecommendationEngine` interface contains a stub `predict_with_ml_model(...)` designed to plug in **TF-IDF cosine similarity**, **Sentence-BERT embeddings**, or **Google Gemini API** for semantic natural language matching without rewriting frontend views.

---

## 🌐 REST API Endpoints

The platform provides JSON REST endpoints for headless integrations:

| Method | Endpoint | Description | Auth Required |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/opportunities` | List opportunities with filters (`search`, `type`, `skill`, `mode`, `sort`) | No |
| `GET` | `/api/opportunities/<id>` | Retrieve detailed information and skill breakdown for one opportunity | No |
| `POST` | `/api/recommend` | Calculate match ranking for any arbitrary JSON profile payload | No |
| `POST` | `/api/save` | Toggle saved/bookmarked state for an opportunity | Yes (Student) |
| `POST` | `/api/application` | Update application stage (`Interested`, `Applied`, `Shortlisted`, `Selected`, `Rejected`) | Yes (Student) |

### Sample Payload: `POST /api/recommend`
```json
{
  "skills": "Python, SQL, Machine Learning",
  "interests": "AI Research, Data Science",
  "preferred_type": "Internship",
  "preferred_location": "Hybrid"
}
```

---

## 🔮 Future Scope & Roadmap

- **AI Resume Parser**: Upload a PDF resume to automatically extract skills, projects, and education using OCR/LLM.
- **Automated Deadline Notifications**: Email alerts 48 hours before bookmarked opportunities close.
- **College Recruiter Portal**: Verified university placement cell and employer dashboard to post campus hiring drives.
- **Collaborative Hackathon Teaming**: Connect with peer students missing the skills you need for multi-disciplinary teams.

---

## 📄 License
This project is licensed under the MIT License — feel free to use and adapt for academic and hackathon presentations.
