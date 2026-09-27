import os
import sqlite3
from datetime import datetime, date, timedelta
from werkzeug.security import generate_password_hash

DB_PATH = os.path.join(os.path.dirname(__file__), "database.db")

def get_db():
    """Returns an active SQLite database connection with row factory enabled."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def init_db():
    """Initializes the database schema and seeds initial data if needed."""
    conn = get_db()
    cursor = conn.cursor()

    # 1. Users Table (Compatible with MySQL)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name VARCHAR(150) NOT NULL,
        email VARCHAR(150) UNIQUE NOT NULL,
        password_hash VARCHAR(255) NOT NULL,
        college VARCHAR(200),
        degree VARCHAR(100),
        branch VARCHAR(100),
        year VARCHAR(50),
        location VARCHAR(150),
        skills TEXT,
        interests TEXT,
        preferred_type VARCHAR(100) DEFAULT 'All',
        preferred_location VARCHAR(150),
        experience_level VARCHAR(50) DEFAULT 'Beginner',
        is_admin INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # 2. Opportunities Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS opportunities (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title VARCHAR(255) NOT NULL,
        organization VARCHAR(200) NOT NULL,
        type VARCHAR(100) NOT NULL,
        description TEXT NOT NULL,
        required_skills TEXT NOT NULL,
        eligibility TEXT NOT NULL,
        location VARCHAR(150) NOT NULL,
        mode VARCHAR(50) NOT NULL,
        deadline DATE NOT NULL,
        application_url VARCHAR(500) NOT NULL,
        stipend_or_prize VARCHAR(150),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # 3. Saved Opportunities Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS saved_opportunities (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        opportunity_id INTEGER NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
        FOREIGN KEY (opportunity_id) REFERENCES opportunities(id) ON DELETE CASCADE,
        UNIQUE (user_id, opportunity_id)
    );
    """)

    # 4. Applications Tracking Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS applications (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        opportunity_id INTEGER NOT NULL,
        status VARCHAR(50) NOT NULL DEFAULT 'Interested',
        applied_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        notes TEXT,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
        FOREIGN KEY (opportunity_id) REFERENCES opportunities(id) ON DELETE CASCADE,
        UNIQUE (user_id, opportunity_id)
    );
    """)

    conn.commit()

    # Seed initial sample data if opportunities table is empty
    cursor.execute("SELECT COUNT(*) AS count FROM opportunities;")
    count = cursor.fetchone()["count"]
    if count == 0:
        seed_data(conn)

    conn.close()

def seed_data(conn):
    """Populates realistic demonstration opportunities and default accounts."""
    cursor = conn.cursor()
    today = date.today()

    # Seed Admin User
    admin_email = "admin@platform.com"
    cursor.execute("SELECT id FROM users WHERE email = ?", (admin_email,))
    if not cursor.fetchone():
        cursor.execute("""
            INSERT INTO users (
                name, email, password_hash, college, degree, branch, year, location,
                skills, interests, preferred_type, preferred_location, experience_level, is_admin
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            "Admin User",
            admin_email,
            generate_password_hash("admin123"),
            "Apex Institute of Technology",
            "M.Tech",
            "Computer Science",
            "Alumni",
            "Bangalore, India",
            "Python, SQL, System Design, Cloud",
            "Platform Administration, Mentorship",
            "All",
            "Remote",
            "Advanced",
            1
        ))

    # Seed Demo Student User
    student_email = "student@college.edu"
    cursor.execute("SELECT id FROM users WHERE email = ?", (student_email,))
    if not cursor.fetchone():
        cursor.execute("""
            INSERT INTO users (
                name, email, password_hash, college, degree, branch, year, location,
                skills, interests, preferred_type, preferred_location, experience_level, is_admin
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            "Alex Sharma",
            student_email,
            generate_password_hash("student123"),
            "National Institute of Technology",
            "B.Tech",
            "Computer Science & Engineering",
            "3rd Year",
            "Pune, India",
            "Python, SQL, HTML, CSS, JavaScript, Machine Learning",
            "AI Research, Web Development, Competitive Programming",
            "Internship",
            "Hybrid",
            "Intermediate",
            0
        ))

    # 15 Realistic, multi-category opportunities
    opportunities_data = [
        (
            "Google Summer of Code (GSoC) 2026",
            "Google Open Source",
            "Internship",
            "A global, online program focused on bringing new contributors into open source software development. GSoC contributors work with an open source organization on a 12+ week programming project under the guidance of mentors.",
            "Python, C++, Git, Open Source, Linux, JavaScript",
            "Students & open source beginners 18+ enrolled in or accepted into a post-secondary academic program.",
            "Global",
            "Online",
            (today + timedelta(days=4)).isoformat(),  # Closing Soon
            "https://summerofcode.withgoogle.com",
            "$1,500 - $3,300 Stipend"
        ),
        (
            "Smart India Hackathon 2026 - Software Edition",
            "Ministry of Education, Govt of India",
            "Hackathon",
            "Nationwide initiative providing students with a platform to solve pressing problems of ministries, departments, industries, and other organizations in healthcare, smart vehicles, agriculture, and cyber security.",
            "Python, JavaScript, React, Node.js, AI, SQL",
            "Regular college/university students in teams of 6 with at least one female teammate.",
            "New Delhi / Multiple Centers",
            "Hybrid",
            (today + timedelta(days=6)).isoformat(),  # Closing Soon
            "https://www.sih.gov.in",
            "INR 1,00,000 per problem statement"
        ),
        (
            "Microsoft Imagine Cup World Championship",
            "Microsoft",
            "Competition",
            "Empowering student developers to leverage Microsoft Azure AI and cloud technologies to solve critical global issues in health, education, earth, and equality. Finalists pitch live for global recognition.",
            "Python, Azure, AI, Machine Learning, Cloud, C#",
            "Students aged 16+ globally. Teams of 1 to 4 members.",
            "Seattle, WA, USA",
            "Hybrid",
            (today + timedelta(days=18)).isoformat(),
            "https://imaginecup.microsoft.com",
            "$100,000 + Azure Credits & Mentorship"
        ),
        (
            "AWS Solutions Architecture Student Fellowship",
            "Amazon Web Services",
            "Internship",
            "Join AWS as a Solutions Architect Intern. Partner directly with customers to design scalable, fault-tolerant cloud infrastructures, build proof-of-concepts, and deliver hands-on technical workshops.",
            "Python, SQL, Cloud, Linux, Java, Networking",
            "Penultimate or final year students in Computer Science, IT, or related STEM fields.",
            "Hyderabad / Bangalore, India",
            "Hybrid",
            (today + timedelta(days=12)).isoformat(),
            "https://aws.amazon.com/careers/students",
            "INR 75,000/month + Relocation"
        ),
        (
            "Reliance Foundation Undergraduate Scholarship",
            "Reliance Foundation",
            "Scholarship",
            "Merit-cum-means scholarship supporting exceptional undergraduate students across India pursuing degrees in engineering, technology, medicine, and fundamental sciences.",
            "Academic Excellence, Leadership, STEM",
            "First-year undergraduate students with minimum 60% in 12th Board, household income < 15 LPA.",
            "India",
            "Online",
            (today + timedelta(days=25)).isoformat(),
            "https://www.reliancefoundation.org",
            "Up to INR 2,00,000 for entire degree"
        ),
        (
            "DeepLearning.AI Machine Learning Specialization",
            "DeepLearning.AI & Stanford Online",
            "Course",
            "Master foundational AI and machine learning concepts from Andrew Ng. Covers supervised learning, neural networks, decision trees, reinforcement learning, and production ML pipelines.",
            "Python, Machine Learning, AI, Math, NumPy",
            "Open to all learners with basic high school math and beginner Python knowledge.",
            "Global",
            "Online",
            (today + timedelta(days=45)).isoformat(),
            "https://www.coursera.org/specializations/machine-learning-introduction",
            "Financial Aid Available (100% Free)"
        ),
        (
            "ISRO Student Satellite Research Fellowship",
            "Indian Space Research Organisation (ISRO)",
            "Research",
            "Conduct cutting-edge research in orbital dynamics, telemetry, embedded systems, and remote sensing image processing at the Space Applications Centre (SAC).",
            "C++, Python, Machine Learning, Image Processing, Embedded Systems",
            "3rd/4th year B.E./B.Tech or M.Tech students with CGPA >= 8.0.",
            "Ahmedabad / Bengaluru, India",
            "On-site",
            (today + timedelta(days=15)).isoformat(),
            "https://www.isro.gov.in/careers",
            "INR 35,000/month fellowship"
        ),
        (
            "Goldman Sachs Summer Engineering Analyst 2027",
            "Goldman Sachs",
            "Job",
            "Develop modern financial platforms, high-throughput microservices, distributed transaction systems, and machine learning models for risk analysis and algorithmic trading.",
            "Java, C++, Python, SQL, Data Structures, Algorithms",
            "Pre-final year students graduating in 2027 majoring in CS, Math, or Engineering.",
            "Bangalore / Mumbai, India",
            "On-site",
            (today + timedelta(days=8)).isoformat(),
            "https://www.goldmansachs.com/careers/students",
            "Competitive Industry Stipend (INR 1.2L/mo)"
        ),
        (
            "NASA International Space Apps Challenge",
            "NASA & Space Agency Partners",
            "Hackathon",
            "The world's largest annual global hackathon. Solve challenges using NASA's open-source Earth and space data over an intense 48-hour collaborative sprint.",
            "Python, Data Analysis, JavaScript, HTML, CSS, AI",
            "Open to coders, scientists, designers, storytellers, makers, and space enthusiasts worldwide.",
            "Global / 300+ Local Chapters",
            "Online",
            (today + timedelta(days=3)).isoformat(),  # Closing Soon!
            "https://www.spaceappschallenge.org",
            "Global NASA Awards & Kennedy Space Center Visit"
        ),
        (
            "CERN Summer Student Research Programme",
            "CERN European Organization for Nuclear Research",
            "Research",
            "Spend 8 to 13 weeks at Geneva working on the day-to-day work of multicultural teams in high-energy physics, detector simulation, and petabyte-scale data pipelines.",
            "C++, Python, Linux, Data Analysis, SQL",
            "Bachelor or Master students having completed at least 6 semesters in physics, engineering, or CS.",
            "Geneva, Switzerland",
            "On-site",
            (today + timedelta(days=35)).isoformat(),
            "https://careers.cern/summer",
            "CHF 90/day living allowance + travel"
        ),
        (
            "Harvard CS50: Web Programming with Python and JavaScript",
            "Harvard University (edX)",
            "Course",
            "Dive into the design and implementation of web apps with Python, JavaScript, SQL, Django, and React. Learn scalability, security, CI/CD, and user experience.",
            "Python, JavaScript, HTML, CSS, SQL, Git",
            "All college and high school students with basic CS knowledge.",
            "Global",
            "Online",
            (today + timedelta(days=60)).isoformat(),
            "https://pll.harvard.edu/course/cs50s-web-programming-python-and-javascript",
            "Free Access (Audit Verified)"
        ),
        (
            "Kaggle Community AI Innovation Cup",
            "Kaggle & Alphabet",
            "Competition",
            "Benchmark and build state-of-the-art multimodal AI models for climate resilience and renewable energy forecasting. Submit notebooks and model weights.",
            "Python, Machine Learning, AI, SQL, PyTorch",
            "Data scientists, students, and practitioners worldwide.",
            "Global",
            "Online",
            (today + timedelta(days=14)).isoformat(),
            "https://www.kaggle.com/competitions",
            "$50,000 Total Prize Pool"
        ),
        (
            "Tata Trust Merit Grant for Higher STEM Education",
            "Tata Trusts",
            "Scholarship",
            "Financial support program for deserving scholars from disadvantaged backgrounds pursuing undergraduate technical studies in recognized engineering colleges.",
            "Academic Merit, Financial Need, STEM",
            "Students enrolled in accredited B.E./B.Tech programs with aggregate > 70%.",
            "Mumbai / All India",
            "Online",
            (today + timedelta(days=22)).isoformat(),
            "https://www.tatatrusts.org",
            "Full tuition fee reimbursement"
        ),
        (
            "Stripe Associate Software Engineer - New Grad",
            "Stripe",
            "Job",
            "Design, build, and maintain APIs, services, and systems across Stripe's engineering teams that move billions of dollars per day for millions of businesses worldwide.",
            "Java, Python, SQL, JavaScript, API Design, Git",
            "Final year students or recent college graduates within 12 months of graduation.",
            "Remote / Bengaluru",
            "Hybrid",
            (today + timedelta(days=28)).isoformat(),
            "https://stripe.com/jobs",
            "Market leading compensation + RSUs"
        ),
        (
            "MIT Media Lab Open Source Research Apprenticeship",
            "Massachusetts Institute of Technology",
            "Research",
            "Collaborate with faculty and graduate researchers on human-computer interaction, cognitive artificial intelligence, and accessible hardware design.",
            "Python, AI, C++, JavaScript, UI/UX, Research",
            "Enrolled undergraduates passionate about unconventional interdisciplinary technology.",
            "Cambridge, MA / Remote",
            "Hybrid",
            (today + timedelta(days=19)).isoformat(),
            "https://www.media.mit.edu",
            "Stipend + Co-authorship credits"
        )
    ]

    for opp in opportunities_data:
        cursor.execute("""
            INSERT INTO opportunities (
                title, organization, type, description, required_skills, eligibility,
                location, mode, deadline, application_url, stipend_or_prize
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, opp)

    conn.commit()
