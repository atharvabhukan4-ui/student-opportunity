import os
import json
from datetime import datetime, date
from functools import wraps
from flask import (
    Flask, render_template, request, redirect, url_for,
    session, flash, jsonify, abort
)
from werkzeug.security import generate_password_hash, check_password_hash

from database import get_db, init_db
from recommendation import engine, parse_csv_items

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret-key-student-opportunity-platform-2026")
app.config["JSON_SORT_KEYS"] = False

# Ensure database tables exist and are seeded upon startup
with app.app_context():
    init_db()

# -------------------------------------------------------------
# HELPER FUNCTIONS & DECORATORS
# -------------------------------------------------------------

def get_current_user():
    """Retrieves current logged-in user record as a dict, or None."""
    user_id = session.get("user_id")
    if not user_id:
        return None
    db = get_db()
    user = db.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    db.close()
    return dict(user) if user else None

def login_required(f):
    """Decorator to enforce login on protected student routes."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get("user_id"):
            flash("Please sign in to access this feature.", "warning")
            return redirect(url_for("login", next=request.path))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    """Decorator to enforce admin privileges."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get("user_id"):
            flash("Admin login required.", "warning")
            return redirect(url_for("admin_login"))
        user = get_current_user()
        if not user or not user.get("is_admin"):
            flash("Access denied: Admin credentials required.", "danger")
            return redirect(url_for("index"))
        return f(*args, **kwargs)
    return decorated_function

def get_deadline_info(deadline_str):
    """Computes days remaining and urgency status for an opportunity deadline."""
    try:
        deadline_date = datetime.strptime(str(deadline_str)[:10], "%Y-%m-%d").date()
        today = date.today()
        days = (deadline_date - today).days

        if days < 0:
            return {
                "days": days,
                "label": "Expired",
                "badge_class": "badge-expired",
                "is_expired": True,
                "closing_soon": False
            }
        elif days <= 5:
            return {
                "days": days,
                "label": f"{days}d left · Closing Soon",
                "badge_class": "badge-danger",
                "is_expired": False,
                "closing_soon": True
            }
        elif days <= 14:
            return {
                "days": days,
                "label": f"{days} days left",
                "badge_class": "badge-warning",
                "is_expired": False,
                "closing_soon": False
            }
        else:
            return {
                "days": days,
                "label": f"{days} days left",
                "badge_class": "badge-neutral",
                "is_expired": False,
                "closing_soon": False
            }
    except Exception:
        return {
            "days": 999,
            "label": "Ongoing",
            "badge_class": "badge-neutral",
            "is_expired": False,
            "closing_soon": False
        }

# Template Context Processors & Filters
@app.context_processor
def inject_globals():
    user = get_current_user()
    return {
        "current_user": user,
        "now_year": date.today().year,
        "active_endpoint": request.endpoint
    }

@app.template_filter("deadline_info")
def filter_deadline_info(d_str):
    return get_deadline_info(d_str)

@app.template_filter("split_skills")
def filter_split_skills(text):
    return parse_csv_items(text)

# -------------------------------------------------------------
# LANDING PAGE & PUBLIC ROUTES
# -------------------------------------------------------------

@app.route("/")
def index():
    """Modern Landing page showcasing categories, statistics, and preview opportunities."""
    db = get_db()
    
    # Aggregated platform statistics
    stats = {}
    stats["total_opportunities"] = db.execute("SELECT COUNT(*) AS c FROM opportunities").fetchone()["c"]
    stats["total_students"] = db.execute("SELECT COUNT(*) AS c FROM users WHERE is_admin = 0").fetchone()["c"]
    stats["total_applications"] = db.execute("SELECT COUNT(*) AS c FROM applications").fetchone()["c"]
    stats["total_categories"] = len(db.execute("SELECT DISTINCT type FROM opportunities").fetchall())

    # Fetch 6 featured / closing soon opportunities
    query = """
        SELECT * FROM opportunities 
        ORDER BY deadline ASC 
        LIMIT 6
    """
    raw_opps = [dict(r) for r in db.execute(query).fetchall()]
    
    current_user = get_current_user()
    featured_opps = []
    for opp in raw_opps:
        opp["deadline_info"] = get_deadline_info(opp["deadline"])
        if current_user:
            opp.update(engine.calculate_match(current_user, opp))
        else:
            opp["match_percentage"] = None
        featured_opps.append(opp)

    db.close()
    return render_template("index.html", stats=stats, featured_opps=featured_opps)

# -------------------------------------------------------------
# AUTHENTICATION (STUDENT & ADMIN)
# -------------------------------------------------------------

@app.route("/register", methods=["GET", "POST"])
def register():
    """Student registration endpoint."""
    if session.get("user_id"):
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        college = request.form.get("college", "").strip()
        degree = request.form.get("degree", "").strip()
        branch = request.form.get("branch", "").strip()
        year = request.form.get("year", "").strip()
        location = request.form.get("location", "").strip()
        skills = request.form.get("skills", "").strip()
        interests = request.form.get("interests", "").strip()

        if not name or not email or not password:
            flash("Name, email, and password are required.", "danger")
            return render_template("register.html", form_data=request.form)

        if len(password) < 6:
            flash("Password must be at least 6 characters long.", "warning")
            return render_template("register.html", form_data=request.form)

        db = get_db()
        existing = db.execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone()
        if existing:
            db.close()
            flash("An account with this email already exists. Please log in.", "warning")
            return redirect(url_for("login"))

        password_hash = generate_password_hash(password)
        cursor = db.cursor()
        cursor.execute("""
            INSERT INTO users (
                name, email, password_hash, college, degree, branch, year, location,
                skills, interests, preferred_type, preferred_location, experience_level, is_admin
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'All', '', 'Beginner', 0)
        """, (name, email, password_hash, college, degree, branch, year, location, skills, interests))
        db.commit()
        new_user_id = cursor.lastrowid
        db.close()

        # Auto login upon registration
        session["user_id"] = new_user_id
        session["user_name"] = name
        session["is_admin"] = False
        flash(f"Welcome to OpporSphere, {name}! Let's build your profile.", "success")
        return redirect(url_for("profile"))

    return render_template("register.html", form_data={})

@app.route("/login", methods=["GET", "POST"])
def login():
    """Student and admin unified login."""
    if session.get("user_id"):
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        next_url = request.form.get("next") or request.args.get("next")

        if not email or not password:
            flash("Please enter both email and password.", "danger")
            return render_template("login.html")

        db = get_db()
        user = db.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
        db.close()

        if not user or not check_password_hash(user["password_hash"], password):
            flash("Invalid email or password. Please verify your credentials.", "danger")
            return render_template("login.html", email=email)

        session["user_id"] = user["id"]
        session["user_name"] = user["name"]
        session["is_admin"] = bool(user["is_admin"])

        flash(f"Welcome back, {user['name']}!", "success")

        if user["is_admin"]:
            return redirect(url_for("admin_dashboard"))
        if next_url and next_url.startswith("/"):
            return redirect(next_url)
        return redirect(url_for("dashboard"))

    return render_template("login.html")

@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    """Specific admin login entry point."""
    if session.get("user_id"):
        user = get_current_user()
        if user and user.get("is_admin"):
            return redirect(url_for("admin_dashboard"))
    
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        
        db = get_db()
        user = db.execute("SELECT * FROM users WHERE email = ? AND is_admin = 1", (email,)).fetchone()
        db.close()

        if not user or not check_password_hash(user["password_hash"], password):
            flash("Invalid administrator credentials.", "danger")
            return render_template("login.html", is_admin_prompt=True)

        session["user_id"] = user["id"]
        session["user_name"] = user["name"]
        session["is_admin"] = True
        flash("Administrator authenticated successfully.", "success")
        return redirect(url_for("admin_dashboard"))

    return render_template("login.html", is_admin_prompt=True)

@app.route("/logout")
def logout():
    """Clears user session."""
    session.clear()
    flash("You have been signed out safely.", "info")
    return redirect(url_for("index"))

# -------------------------------------------------------------
# STUDENT PROFILE
# -------------------------------------------------------------

@app.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    """Allows student to view and update skills, interests, and preferences."""
    current_user = get_current_user()
    db = get_db()

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        college = request.form.get("college", "").strip()
        degree = request.form.get("degree", "").strip()
        branch = request.form.get("branch", "").strip()
        year = request.form.get("year", "").strip()
        location = request.form.get("location", "").strip()
        skills = request.form.get("skills", "").strip()
        interests = request.form.get("interests", "").strip()
        preferred_type = request.form.get("preferred_type", "All").strip()
        preferred_location = request.form.get("preferred_location", "").strip()
        experience_level = request.form.get("experience_level", "Beginner").strip()

        db.execute("""
            UPDATE users SET
                name = ?, college = ?, degree = ?, branch = ?, year = ?, location = ?,
                skills = ?, interests = ?, preferred_type = ?, preferred_location = ?,
                experience_level = ?
            WHERE id = ?
        """, (
            name, college, degree, branch, year, location,
            skills, interests, preferred_type, preferred_location,
            experience_level, current_user["id"]
        ))
        db.commit()
        db.close()

        flash("Your profile and skill preferences have been updated!", "success")
        return redirect(url_for("profile"))

    # Also compute profile completeness
    fields = [
        current_user.get("skills"), current_user.get("interests"),
        current_user.get("college"), current_user.get("degree"),
        current_user.get("branch"), current_user.get("location")
    ]
    completed = sum(1 for f in fields if f and str(f).strip())
    completeness_pct = int(round((completed / len(fields)) * 100))

    db.close()
    return render_template("profile.html", user=current_user, completeness_pct=completeness_pct)

# -------------------------------------------------------------
# OPPORTUNITY DISCOVERY & SEARCH
# -------------------------------------------------------------

@app.route("/opportunities")
def opportunities():
    """Opportunity discovery page with multi-faceted search, filter, and match calculations."""
    current_user = get_current_user()
    db = get_db()

    # Query parameters
    search_q = request.args.get("search", "").strip()
    type_filter = request.args.get("type", "All").strip()
    skill_filter = request.args.get("skill", "").strip()
    location_filter = request.args.get("location", "").strip()
    mode_filter = request.args.get("mode", "All").strip()
    sort_by = request.args.get("sort", "match" if current_user else "deadline").strip()

    # Fetch user's saved opportunities & applied opportunities if logged in
    saved_ids = set()
    application_statuses = {}
    if current_user:
        saved_rows = db.execute("SELECT opportunity_id FROM saved_opportunities WHERE user_id = ?", (current_user["id"],)).fetchall()
        saved_ids = {r["opportunity_id"] for r in saved_rows}

        app_rows = db.execute("SELECT opportunity_id, status FROM applications WHERE user_id = ?", (current_user["id"],)).fetchall()
        application_statuses = {r["opportunity_id"]: r["status"] for r in app_rows}

    # Fetch all opportunities from database
    raw_opps = [dict(r) for r in db.execute("SELECT * FROM opportunities").fetchall()]

    # Available distinct types and modes for filter dropdowns
    available_types = [r["type"] for r in db.execute("SELECT DISTINCT type FROM opportunities ORDER BY type").fetchall()]
    available_modes = ["Online", "On-site", "Hybrid"]

    # Filter opportunities
    filtered = []
    for opp in raw_opps:
        # Search keyword match
        if search_q:
            q_lower = search_q.lower()
            in_title = q_lower in opp["title"].lower()
            in_org = q_lower in opp["organization"].lower()
            in_desc = q_lower in opp["description"].lower()
            in_skills = q_lower in opp["required_skills"].lower()
            if not (in_title or in_org or in_desc or in_skills):
                continue

        # Type filter
        if type_filter and type_filter != "All" and opp["type"].lower() != type_filter.lower():
            continue

        # Mode filter
        if mode_filter and mode_filter != "All" and opp["mode"].lower() != mode_filter.lower():
            continue

        # Location filter
        if location_filter and location_filter.lower() not in opp["location"].lower():
            continue

        # Skill filter
        if skill_filter:
            opp_skills = [s.lower() for s in parse_csv_items(opp["required_skills"])]
            if not any(skill_filter.lower() in s for s in opp_skills):
                continue

        # Attach meta information
        opp["deadline_info"] = get_deadline_info(opp["deadline"])
        opp["is_saved"] = opp["id"] in saved_ids
        opp["application_status"] = application_statuses.get(opp["id"], None)

        # Recommendation match calculation
        if current_user:
            match_data = engine.calculate_match(current_user, opp)
            opp.update(match_data)
        else:
            opp["match_percentage"] = None
            opp["matching_skills"] = []
            opp["missing_skills"] = parse_csv_items(opp["required_skills"])
            opp["match_level"] = "Sign in to Match"
            opp["match_badge_class"] = "badge-neutral"
            opp["explanation"] = "Sign in to see how your skills match."

        filtered.append(opp)

    # Sort opportunities
    if sort_by == "match" and current_user:
        filtered.sort(key=lambda x: (x.get("match_percentage") or 0), reverse=True)
    elif sort_by == "deadline":
        filtered.sort(key=lambda x: str(x.get("deadline", "9999-12-31")))
    elif sort_by == "newest":
        filtered.sort(key=lambda x: x.get("id", 0), reverse=True)
    elif sort_by == "title":
        filtered.sort(key=lambda x: x.get("title", "").lower())

    db.close()

    return render_template(
        "opportunities.html",
        opportunities=filtered,
        total_count=len(filtered),
        available_types=available_types,
        available_modes=available_modes,
        current_filters={
            "search": search_q,
            "type": type_filter,
            "skill": skill_filter,
            "location": location_filter,
            "mode": mode_filter,
            "sort": sort_by
        }
    )

@app.route("/opportunities/<int:opp_id>")
def opportunity_details(opp_id):
    """Detailed view for a specific opportunity."""
    db = get_db()
    opp_row = db.execute("SELECT * FROM opportunities WHERE id = ?", (opp_id,)).fetchone()
    if not opp_row:
        db.close()
        abort(404)

    opp = dict(opp_row)
    opp["deadline_info"] = get_deadline_info(opp["deadline"])
    
    current_user = get_current_user()
    if current_user:
        match_data = engine.calculate_match(current_user, opp)
        opp.update(match_data)
        
        saved_row = db.execute(
            "SELECT id FROM saved_opportunities WHERE user_id = ? AND opportunity_id = ?",
            (current_user["id"], opp_id)
        ).fetchone()
        opp["is_saved"] = bool(saved_row)

        app_row = db.execute(
            "SELECT status, notes, applied_date FROM applications WHERE user_id = ? AND opportunity_id = ?",
            (current_user["id"], opp_id)
        ).fetchone()
        opp["application"] = dict(app_row) if app_row else None
    else:
        opp["match_percentage"] = None
        opp["matching_skills"] = []
        opp["missing_skills"] = parse_csv_items(opp["required_skills"])
        opp["is_saved"] = False
        opp["application"] = None

    # Similar opportunities
    similar_rows = db.execute("""
        SELECT * FROM opportunities 
        WHERE type = ? AND id != ? 
        ORDER BY deadline ASC LIMIT 3
    """, (opp["type"], opp_id)).fetchall()
    similar_opps = []
    for s in similar_rows:
        s_dict = dict(s)
        s_dict["deadline_info"] = get_deadline_info(s_dict["deadline"])
        if current_user:
            s_dict.update(engine.calculate_match(current_user, s_dict))
        similar_opps.append(s_dict)

    db.close()
    return render_template("opportunity_details.html", opp=opp, similar_opps=similar_opps)

# -------------------------------------------------------------
# STUDENT DASHBOARD
# -------------------------------------------------------------

@app.route("/dashboard")
@login_required
def dashboard():
    """Student central command center with stats, recommendations, deadlines, and charts."""
    current_user = get_current_user()
    db = get_db()

    # Metric counts
    total_opps = db.execute("SELECT COUNT(*) AS c FROM opportunities").fetchone()["c"]
    
    saved_count = db.execute(
        "SELECT COUNT(*) AS c FROM saved_opportunities WHERE user_id = ?", 
        (current_user["id"],)
    ).fetchone()["c"]

    applied_count = db.execute(
        "SELECT COUNT(*) AS c FROM applications WHERE user_id = ?", 
        (current_user["id"],)
    ).fetchone()["c"]

    # Applications breakdown by status for chart
    status_counts_rows = db.execute("""
        SELECT status, COUNT(*) AS count 
        FROM applications 
        WHERE user_id = ? 
        GROUP BY status
    """, (current_user["id"],)).fetchall()
    
    status_order = ["Interested", "Applied", "Shortlisted", "Selected", "Rejected"]
    status_counts_map = {r["status"]: r["count"] for r in status_counts_rows}
    status_chart_data = {
        "labels": status_order,
        "values": [status_counts_map.get(s, 0) for s in status_order]
    }

    # Fetch all opportunities to rank by recommendation
    all_opps = [dict(r) for r in db.execute("SELECT * FROM opportunities").fetchall()]
    ranked = engine.rank_opportunities(current_user, all_opps)

    # Attach deadline info & saved state
    saved_ids = {
        r["opportunity_id"] for r in db.execute(
            "SELECT opportunity_id FROM saved_opportunities WHERE user_id = ?",
            (current_user["id"],)
        ).fetchall()
    }
    app_map = {
        r["opportunity_id"]: r["status"] for r in db.execute(
            "SELECT opportunity_id, status FROM applications WHERE user_id = ?",
            (current_user["id"],)
        ).fetchall()
    }

    for opp in ranked:
        opp["deadline_info"] = get_deadline_info(opp["deadline"])
        opp["is_saved"] = opp["id"] in saved_ids
        opp["application_status"] = app_map.get(opp["id"])

    # High match recommendations (top 4 with match >= 60%)
    top_recommended = [o for o in ranked if (o.get("match_percentage") or 0) >= 60][:4]
    if not top_recommended:
        top_recommended = ranked[:4]

    # Upcoming urgent deadlines (closing within next 10 days, not expired)
    urgent_deadlines = [
        o for o in ranked 
        if 0 <= o["deadline_info"]["days"] <= 10
    ]
    urgent_deadlines.sort(key=lambda x: x["deadline_info"]["days"])
    urgent_deadlines = urgent_deadlines[:4]

    # Recent applications
    recent_apps_rows = db.execute("""
        SELECT a.status, a.applied_date, a.notes, o.id AS opportunity_id, o.title, o.organization, o.type, o.deadline
        FROM applications a
        JOIN opportunities o ON a.opportunity_id = o.id
        WHERE a.user_id = ?
        ORDER BY a.updated_at DESC LIMIT 5
    """, (current_user["id"],)).fetchall()
    
    recent_apps = []
    for app_row in recent_apps_rows:
        a = dict(app_row)
        a["deadline_info"] = get_deadline_info(a["deadline"])
        recent_apps.append(a)

    db.close()

    return render_template(
        "dashboard.html",
        total_opps=total_opps,
        recommended_count=len([o for o in ranked if (o.get("match_percentage") or 0) >= 70]),
        saved_count=saved_count,
        applied_count=applied_count,
        top_recommended=top_recommended,
        urgent_deadlines=urgent_deadlines,
        recent_apps=recent_apps,
        status_chart_data=status_chart_data
    )

# -------------------------------------------------------------
# SAVED OPPORTUNITIES
# -------------------------------------------------------------

@app.route("/saved")
@login_required
def saved():
    """Displays all opportunities bookmarked by the student."""
    current_user = get_current_user()
    db = get_db()

    query = """
        SELECT o.*, s.created_at AS saved_at,
               a.status AS application_status
        FROM saved_opportunities s
        JOIN opportunities o ON s.opportunity_id = o.id
        LEFT JOIN applications a ON (a.opportunity_id = o.id AND a.user_id = s.user_id)
        WHERE s.user_id = ?
        ORDER BY s.created_at DESC
    """
    rows = db.execute(query, (current_user["id"],)).fetchall()
    saved_list = []
    for r in rows:
        opp = dict(r)
        opp["deadline_info"] = get_deadline_info(opp["deadline"])
        opp["is_saved"] = True
        opp.update(engine.calculate_match(current_user, opp))
        saved_list.append(opp)

    db.close()
    return render_template("saved.html", opportunities=saved_list)

# -------------------------------------------------------------
# APPLICATION TRACKER
# -------------------------------------------------------------

@app.route("/applications")
@login_required
def applications():
    """Tracks status of all student applications with status change capability."""
    current_user = get_current_user()
    status_filter = request.args.get("status", "All").strip()
    db = get_db()

    query = """
        SELECT a.id AS app_id, a.status, a.applied_date, a.notes, a.updated_at,
               o.id AS opp_id, o.title, o.organization, o.type, o.location,
               o.mode, o.deadline, o.application_url, o.required_skills
        FROM applications a
        JOIN opportunities o ON a.opportunity_id = o.id
        WHERE a.user_id = ?
    """
    params = [current_user["id"]]
    if status_filter and status_filter != "All":
        query += " AND a.status = ?"
        params.append(status_filter)

    query += " ORDER BY a.updated_at DESC"
    rows = db.execute(query, tuple(params)).fetchall()

    apps = []
    for r in rows:
        app_item = dict(r)
        app_item["deadline_info"] = get_deadline_info(app_item["deadline"])
        app_item.update(engine.calculate_match(current_user, app_item))
        apps.append(app_item)

    # Counts by status
    status_counts_rows = db.execute("""
        SELECT status, COUNT(*) AS count 
        FROM applications 
        WHERE user_id = ? 
        GROUP BY status
    """, (current_user["id"],)).fetchall()
    status_counts = {r["status"]: r["count"] for r in status_counts_rows}
    status_counts["Total"] = sum(status_counts.values())

    db.close()
    return render_template(
        "applications.html",
        applications=apps,
        status_filter=status_filter,
        status_counts=status_counts
    )

# -------------------------------------------------------------
# ADMIN PANEL
# -------------------------------------------------------------

@app.route("/admin")
@admin_required
def admin_dashboard():
    """Admin management dashboard for opportunities, students, and platform stats."""
    db = get_db()

    # System statistics
    stats = {}
    stats["total_opportunities"] = db.execute("SELECT COUNT(*) AS c FROM opportunities").fetchone()["c"]
    stats["total_students"] = db.execute("SELECT COUNT(*) AS c FROM users WHERE is_admin = 0").fetchone()["c"]
    stats["total_applications"] = db.execute("SELECT COUNT(*) AS c FROM applications").fetchone()["c"]
    stats["total_saved"] = db.execute("SELECT COUNT(*) AS c FROM saved_opportunities").fetchone()["c"]

    # All opportunities for management table
    opps = [dict(r) for r in db.execute("SELECT * FROM opportunities ORDER BY id DESC").fetchall()]
    for o in opps:
        o["deadline_info"] = get_deadline_info(o["deadline"])
        app_count = db.execute("SELECT COUNT(*) AS c FROM applications WHERE opportunity_id = ?", (o["id"],)).fetchone()["c"]
        o["applicant_count"] = app_count

    # All registered students
    students = [dict(r) for r in db.execute("""
        SELECT id, name, email, college, degree, branch, year, location, skills, created_at 
        FROM users WHERE is_admin = 0 
        ORDER BY id DESC
    """).fetchall()]

    db.close()
    return render_template("admin.html", stats=stats, opportunities=opps, students=students)

@app.route("/admin/opportunity/add", methods=["POST"])
@admin_required
def admin_add_opportunity():
    """Creates a new opportunity record in the database."""
    title = request.form.get("title", "").strip()
    organization = request.form.get("organization", "").strip()
    type_ = request.form.get("type", "").strip()
    description = request.form.get("description", "").strip()
    required_skills = request.form.get("required_skills", "").strip()
    eligibility = request.form.get("eligibility", "").strip()
    location = request.form.get("location", "").strip()
    mode = request.form.get("mode", "Online").strip()
    deadline = request.form.get("deadline", "").strip()
    application_url = request.form.get("application_url", "").strip()
    stipend_or_prize = request.form.get("stipend_or_prize", "").strip()

    if not title or not organization or not type_ or not deadline or not application_url:
        flash("Title, organization, type, deadline, and application URL are required.", "danger")
        return redirect(url_for("admin_dashboard"))

    db = get_db()
    db.execute("""
        INSERT INTO opportunities (
            title, organization, type, description, required_skills, eligibility,
            location, mode, deadline, application_url, stipend_or_prize
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        title, organization, type_, description, required_skills, eligibility,
        location, mode, deadline, application_url, stipend_or_prize
    ))
    db.commit()
    db.close()

    flash(f"Opportunity '{title}' added successfully!", "success")
    return redirect(url_for("admin_dashboard"))

@app.route("/admin/opportunity/edit/<int:opp_id>", methods=["POST"])
@admin_required
def admin_edit_opportunity(opp_id):
    """Updates an existing opportunity."""
    title = request.form.get("title", "").strip()
    organization = request.form.get("organization", "").strip()
    type_ = request.form.get("type", "").strip()
    description = request.form.get("description", "").strip()
    required_skills = request.form.get("required_skills", "").strip()
    eligibility = request.form.get("eligibility", "").strip()
    location = request.form.get("location", "").strip()
    mode = request.form.get("mode", "Online").strip()
    deadline = request.form.get("deadline", "").strip()
    application_url = request.form.get("application_url", "").strip()
    stipend_or_prize = request.form.get("stipend_or_prize", "").strip()

    db = get_db()
    db.execute("""
        UPDATE opportunities SET
            title = ?, organization = ?, type = ?, description = ?,
            required_skills = ?, eligibility = ?, location = ?, mode = ?,
            deadline = ?, application_url = ?, stipend_or_prize = ?
        WHERE id = ?
    """, (
        title, organization, type_, description, required_skills, eligibility,
        location, mode, deadline, application_url, stipend_or_prize, opp_id
    ))
    db.commit()
    db.close()

    flash(f"Opportunity #{opp_id} updated successfully!", "success")
    return redirect(url_for("admin_dashboard"))

@app.route("/admin/opportunity/delete/<int:opp_id>", methods=["POST"])
@admin_required
def admin_delete_opportunity(opp_id):
    """Deletes an opportunity from the system."""
    db = get_db()
    db.execute("DELETE FROM opportunities WHERE id = ?", (opp_id,))
    db.commit()
    db.close()

    flash(f"Opportunity #{opp_id} has been permanently deleted.", "info")
    return redirect(url_for("admin_dashboard"))

# -------------------------------------------------------------
# REST API ENDPOINTS
# -------------------------------------------------------------

@app.route("/api/opportunities", methods=["GET"])
def api_get_opportunities():
    """
    GET /api/opportunities
    Returns list of opportunities with optional filters (search, type, skill, location, mode).
    If logged in, includes match score and saved status.
    """
    search_q = request.args.get("search", "").strip()
    type_filter = request.args.get("type", "").strip()
    skill_filter = request.args.get("skill", "").strip()
    location_filter = request.args.get("location", "").strip()
    mode_filter = request.args.get("mode", "").strip()
    sort_by = request.args.get("sort", "deadline").strip()

    current_user = get_current_user()
    db = get_db()
    raw_opps = [dict(r) for r in db.execute("SELECT * FROM opportunities").fetchall()]

    results = []
    for opp in raw_opps:
        if search_q:
            q = search_q.lower()
            if not (q in opp["title"].lower() or q in opp["organization"].lower() or q in opp["description"].lower() or q in opp["required_skills"].lower()):
                continue
        if type_filter and type_filter != "All" and opp["type"].lower() != type_filter.lower():
            continue
        if mode_filter and mode_filter != "All" and opp["mode"].lower() != mode_filter.lower():
            continue
        if location_filter and location_filter.lower() not in opp["location"].lower():
            continue
        if skill_filter:
            opp_skills = [s.lower() for s in parse_csv_items(opp["required_skills"])]
            if not any(skill_filter.lower() in s for s in opp_skills):
                continue

        opp["deadline_info"] = get_deadline_info(opp["deadline"])
        if current_user:
            opp.update(engine.calculate_match(current_user, opp))
        results.append(opp)

    if sort_by == "match" and current_user:
        results.sort(key=lambda x: (x.get("match_percentage") or 0), reverse=True)
    elif sort_by == "deadline":
        results.sort(key=lambda x: str(x.get("deadline", "9999-12-31")))

    db.close()
    return jsonify({
        "status": "success",
        "count": len(results),
        "data": results
    })

@app.route("/api/opportunities/<int:opp_id>", methods=["GET"])
def api_get_opportunity_detail(opp_id):
    """
    GET /api/opportunities/<id>
    Returns detailed view of an opportunity with calculated skill alignment.
    """
    db = get_db()
    opp_row = db.execute("SELECT * FROM opportunities WHERE id = ?", (opp_id,)).fetchone()
    if not opp_row:
        db.close()
        return jsonify({"status": "error", "message": "Opportunity not found"}), 404

    opp = dict(opp_row)
    opp["deadline_info"] = get_deadline_info(opp["deadline"])

    current_user = get_current_user()
    if current_user:
        opp.update(engine.calculate_match(current_user, opp))

    db.close()
    return jsonify({
        "status": "success",
        "data": opp
    })

@app.route("/api/recommend", methods=["POST"])
def api_recommend():
    """
    POST /api/recommend
    Calculates recommendations for an arbitrary input profile:
    Body: {"skills": "Python, SQL", "interests": "AI, Web", "preferred_type": "Internship"}
    """
    payload = request.get_json(silent=True) or {}
    skills = payload.get("skills", "")
    interests = payload.get("interests", "")
    pref_type = payload.get("preferred_type", "All")
    pref_loc = payload.get("preferred_location", "")

    mock_profile = {
        "skills": skills,
        "interests": interests,
        "preferred_type": pref_type,
        "preferred_location": pref_loc
    }

    db = get_db()
    all_opps = [dict(r) for r in db.execute("SELECT * FROM opportunities").fetchall()]
    db.close()

    ranked = engine.rank_opportunities(mock_profile, all_opps)
    for opp in ranked:
        opp["deadline_info"] = get_deadline_info(opp["deadline"])

    return jsonify({
        "status": "success",
        "count": len(ranked),
        "profile": mock_profile,
        "recommendations": ranked
    })

@app.route("/api/save", methods=["POST"])
def api_save():
    """
    POST /api/save
    Body: {"opportunity_id": 1}
    Toggles saved/bookmarked opportunity state for logged-in user.
    """
    current_user = get_current_user()
    if not current_user:
        return jsonify({"status": "error", "message": "Authentication required"}), 401

    payload = request.get_json(silent=True) or request.form
    opp_id = payload.get("opportunity_id")
    if not opp_id:
        return jsonify({"status": "error", "message": "opportunity_id required"}), 400

    db = get_db()
    existing = db.execute(
        "SELECT id FROM saved_opportunities WHERE user_id = ? AND opportunity_id = ?",
        (current_user["id"], opp_id)
    ).fetchone()

    if existing:
        db.execute(
            "DELETE FROM saved_opportunities WHERE user_id = ? AND opportunity_id = ?",
            (current_user["id"], opp_id)
        )
        db.commit()
        db.close()
        return jsonify({"status": "success", "action": "removed", "is_saved": False})
    else:
        db.execute(
            "INSERT INTO saved_opportunities (user_id, opportunity_id) VALUES (?, ?)",
            (current_user["id"], opp_id)
        )
        db.commit()
        db.close()
        return jsonify({"status": "success", "action": "saved", "is_saved": True})

@app.route("/api/application", methods=["POST"])
def api_application():
    """
    POST /api/application
    Body: {"opportunity_id": 1, "status": "Applied", "notes": "Submitted portfolio"}
    Creates or updates the status of an application for the logged-in student.
    """
    current_user = get_current_user()
    if not current_user:
        return jsonify({"status": "error", "message": "Authentication required"}), 401

    payload = request.get_json(silent=True) or request.form
    opp_id = payload.get("opportunity_id")
    status = payload.get("status", "Interested").strip()
    notes = payload.get("notes", "").strip()

    valid_statuses = ["Interested", "Applied", "Shortlisted", "Selected", "Rejected"]
    if status not in valid_statuses:
        return jsonify({"status": "error", "message": f"Status must be one of: {', '.join(valid_statuses)}"}), 400

    db = get_db()
    existing = db.execute(
        "SELECT id FROM applications WHERE user_id = ? AND opportunity_id = ?",
        (current_user["id"], opp_id)
    ).fetchone()

    if existing:
        db.execute("""
            UPDATE applications 
            SET status = ?, notes = ?, updated_at = CURRENT_TIMESTAMP 
            WHERE user_id = ? AND opportunity_id = ?
        """, (status, notes, current_user["id"], opp_id))
    else:
        db.execute("""
            INSERT INTO applications (user_id, opportunity_id, status, notes)
            VALUES (?, ?, ?, ?)
        """, (current_user["id"], opp_id, status, notes))

    db.commit()
    db.close()

    return jsonify({
        "status": "success",
        "opportunity_id": opp_id,
        "application_status": status,
        "message": f"Status updated to '{status}'"
    })

# -------------------------------------------------------------
# ERROR HANDLERS
# -------------------------------------------------------------

@app.errorhandler(404)
def page_not_found(e):
    if request.path.startswith("/api/"):
        return jsonify({"status": "error", "message": "Resource not found"}), 404
    return render_template("index.html", error_message="The requested page was not found."), 404

@app.errorhandler(500)
def server_error(e):
    if request.path.startswith("/api/"):
        return jsonify({"status": "error", "message": "Internal server error"}), 500
    return render_template("index.html", error_message="An unexpected server error occurred."), 500

if __name__ == "__main__":
    app.run(debug=True, port=5000)
