import unittest
import json
from app import app
from database import get_db, init_db

class TestOpportunityPlatform(unittest.TestCase):
    def setUp(self):
        app.config["TESTING"] = True
        app.config["WTF_CSRF_ENABLED"] = False
        self.client = app.test_client()
        with app.app_context():
            init_db()
            db = get_db()
            db.execute("DELETE FROM saved_opportunities;")
            db.execute("DELETE FROM applications;")
            db.commit()
            db.close()

    def test_01_landing_page(self):
        """Verify landing page loads and contains platform name and metrics."""
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"OpporSphere", response.data)
        self.assertIn(b"Discover Opportunities", response.data)

    def test_02_discovery_and_filtering(self):
        """Verify opportunity discovery and search filter endpoints."""
        # General discovery
        response = self.client.get("/opportunities")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Google Summer of Code", response.data)

        # Filter by type: Hackathon
        response = self.client.get("/opportunities?type=Hackathon")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Smart India Hackathon", response.data)

        # Filter by search keyword
        response = self.client.get("/opportunities?search=ISRO")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"ISRO Student Satellite", response.data)

    def test_03_student_auth_and_profile(self):
        """Test student login, invalid password check, and profile update."""
        # Invalid login
        res_fail = self.client.post("/login", data={"email": "student@college.edu", "password": "wrongpassword"})
        self.assertIn(b"Invalid email or password", res_fail.data)

        # Valid login
        res_login = self.client.post("/login", data={"email": "student@college.edu", "password": "student123"}, follow_redirects=True)
        self.assertEqual(res_login.status_code, 200)
        self.assertIn(b"Welcome back, Alex", res_login.data)

        # Profile view
        res_prof = self.client.get("/profile")
        self.assertEqual(res_prof.status_code, 200)
        self.assertIn(b"Alex Sharma", res_prof.data)

        # Update profile skills
        res_update = self.client.post("/profile", data={
            "name": "Alex Sharma",
            "college": "National Institute of Technology",
            "degree": "B.Tech",
            "branch": "Computer Science & Engineering",
            "year": "3rd Year",
            "location": "Pune, India",
            "skills": "Python, SQL, Machine Learning, React, C++",
            "interests": "AI Research, Cloud Systems",
            "preferred_type": "Internship",
            "preferred_location": "Hybrid",
            "experience_level": "Intermediate"
        }, follow_redirects=True)
        self.assertEqual(res_update.status_code, 200)
        self.assertIn(b"updated", res_update.data)

    def test_04_recommendations_and_apis(self):
        """Verify recommendation engine API and opportunity detail API."""
        # API Opportunities list
        res_api_opps = self.client.get("/api/opportunities")
        self.assertEqual(res_api_opps.status_code, 200)
        data = res_api_opps.get_json()
        self.assertEqual(data["status"], "success")
        self.assertGreaterEqual(data["count"], 10)

        # API Recommend endpoint
        rec_payload = {
            "skills": "Python, SQL, Machine Learning",
            "interests": "AI, Open Source",
            "preferred_type": "Internship"
        }
        res_rec = self.client.post("/api/recommend", json=rec_payload)
        self.assertEqual(res_rec.status_code, 200)
        rec_data = res_rec.get_json()
        self.assertTrue(len(rec_data["recommendations"]) > 0)
        top_match = rec_data["recommendations"][0]
        self.assertIn("match_percentage", top_match)
        self.assertIn("matching_skills", top_match)
        self.assertIn("missing_skills", top_match)

    def test_05_saved_and_application_tracking(self):
        """Verify bookmarking and application tracking."""
        # Sign in as student
        self.client.post("/login", data={"email": "student@college.edu", "password": "student123"})

        # Toggle save opportunity 1
        res_save = self.client.post("/api/save", json={"opportunity_id": 1})
        self.assertEqual(res_save.status_code, 200)
        save_data = res_save.get_json()
        self.assertTrue(save_data["is_saved"])

        # Check /saved page
        res_saved_page = self.client.get("/saved")
        self.assertEqual(res_saved_page.status_code, 200)
        self.assertIn(b"Google Summer of Code", res_saved_page.data)

        # Track application stage
        res_app = self.client.post("/api/application", json={
            "opportunity_id": 1,
            "status": "Applied",
            "notes": "Submitted GSoC proposal."
        })
        self.assertEqual(res_app.status_code, 200)
        app_data = res_app.get_json()
        self.assertEqual(app_data["application_status"], "Applied")

        # Check /applications page
        res_app_page = self.client.get("/applications")
        self.assertEqual(res_app_page.status_code, 200)
        self.assertIn(b"Applied", res_app_page.data)
        self.assertIn(b"Submitted GSoC proposal", res_app_page.data)

    def test_06_admin_operations(self):
        """Verify admin security and CRUD operations on opportunities."""
        # Non-admin student blocked from admin panel
        self.client.post("/login", data={"email": "student@college.edu", "password": "student123"})
        res_blocked = self.client.get("/admin", follow_redirects=True)
        self.assertIn(b"Access denied", res_blocked.data)

        # Log out student before logging in as admin
        self.client.get("/logout")

        # Login as admin
        self.client.post("/login", data={"email": "admin@platform.com", "password": "admin123"})
        res_admin = self.client.get("/admin")
        self.assertEqual(res_admin.status_code, 200)
        self.assertIn(b"Administrator Portal", res_admin.data)
        self.assertIn(b"Registered Students Directory", res_admin.data)

        # Add new opportunity
        res_add = self.client.post("/admin/opportunity/add", data={
            "title": "Quantum AI Fellowship 2026",
            "organization": "Quantum Labs Global",
            "type": "Research",
            "description": "Research in quantum machine learning algorithms.",
            "required_skills": "Python, Quantum Computing, Linear Algebra",
            "eligibility": "B.Tech/M.Tech seniors",
            "location": "Remote",
            "mode": "Online",
            "deadline": "2026-11-30",
            "application_url": "https://example.com/quantum",
            "stipend_or_prize": "$2,500/mo"
        }, follow_redirects=True)
        self.assertEqual(res_add.status_code, 200)
        self.assertIn(b"Quantum AI Fellowship", res_add.data)

        # Edit opportunity
        db = get_db()
        added_opp = db.execute("SELECT id FROM opportunities WHERE title = ?", ("Quantum AI Fellowship 2026",)).fetchone()
        db.close()
        self.assertIsNotNone(added_opp)
        opp_id = added_opp["id"]

        res_edit = self.client.post(f"/admin/opportunity/edit/{opp_id}", data={
            "title": "Quantum AI Fellowship 2026 (Updated)",
            "organization": "Quantum Labs Global",
            "type": "Research",
            "description": "Updated description.",
            "required_skills": "Python, Qiskit",
            "eligibility": "Graduating seniors",
            "location": "Remote",
            "mode": "Online",
            "deadline": "2026-12-15",
            "application_url": "https://example.com/quantum",
            "stipend_or_prize": "$3,000/mo"
        }, follow_redirects=True)
        self.assertEqual(res_edit.status_code, 200)
        self.assertIn(b"updated successfully", res_edit.data)

        # Delete opportunity
        res_delete = self.client.post(f"/admin/opportunity/delete/{opp_id}", follow_redirects=True)
        self.assertEqual(res_delete.status_code, 200)
        self.assertIn(b"permanently deleted", res_delete.data)

    def test_07_student_registration_flow(self):
        """Test creating a new student account from the registration page."""
        import time
        unique_email = f"jane_{int(time.time()*1000)}@college.edu"
        res_reg = self.client.post("/register", data={
            "name": "Jane Doe",
            "email": unique_email,
            "password": "securepass123",
            "college": "Stanford University",
            "degree": "B.Sc",
            "branch": "Computer Science",
            "year": "2nd Year",
            "location": "California, USA",
            "skills": "Python, C++, AI",
            "interests": "Machine Learning, Robotics"
        }, follow_redirects=True)
        self.assertEqual(res_reg.status_code, 200)
        self.assertIn(b"Welcome to OpporSphere, Jane Doe!", res_reg.data)

    def test_08_deadline_calculations(self):
        """Verify deadline status labels and badges."""
        from app import get_deadline_info
        from datetime import date, timedelta
        
        # Closing soon
        info_soon = get_deadline_info((date.today() + timedelta(days=2)).isoformat())
        self.assertTrue(info_soon["closing_soon"])
        self.assertIn("Closing Soon", info_soon["label"])

        # Expired
        info_expired = get_deadline_info((date.today() - timedelta(days=2)).isoformat())
        self.assertTrue(info_expired["is_expired"])
        self.assertEqual(info_expired["label"], "Expired")

    def test_09_api_errors(self):
        """Verify JSON error handling for missing authentication and non-existent IDs."""
        self.client.get("/logout")
        # Unauthorized save attempt
        res_unauth = self.client.post("/api/save", json={"opportunity_id": 1})
        self.assertEqual(res_unauth.status_code, 401)
        
        # 404 opportunity lookup
        res_404 = self.client.get("/api/opportunities/999999")
        self.assertEqual(res_404.status_code, 404)

if __name__ == "__main__":
    unittest.main()
