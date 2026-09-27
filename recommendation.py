import re
from typing import Dict, List, Any

# Common skill alias mapping for smart synonym resolution
SKILL_ALIASES = {
    "cpp": "c++",
    "c plus plus": "c++",
    "js": "javascript",
    "ts": "typescript",
    "ml": "machine learning",
    "ai": "ai",
    "artificial intelligence": "ai",
    "reactjs": "react",
    "react.js": "react",
    "nodejs": "node.js",
    "node": "node.js",
    "golang": "go",
    "py": "python",
    "postgres": "postgresql",
    "k8s": "kubernetes",
    "aws": "cloud",
    "azure": "cloud",
    "gcp": "cloud"
}

def clean_skill(skill: str) -> str:
    """Normalizes skill string: lowercase, stripped, stripped of special punct."""
    s = skill.lower().strip()
    s = re.sub(r'[\s\-]+', ' ', s)
    return SKILL_ALIASES.get(s, s)

def parse_csv_items(text: str) -> List[str]:
    """Parses comma or semicolon delimited string into clean list of items."""
    if not text:
        return []
    parts = re.split(r'[,;\n/]+', str(text))
    return [p.strip() for p in parts if p.strip()]

class BaseRecommendationEngine:
    """Base interface for recommendation algorithms (Rule-based, TF-IDF, ML)."""
    def rank_opportunities(self, student_profile: Dict[str, Any], opportunities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        raise NotImplementedError

class RuleBasedRecommendationEngine(BaseRecommendationEngine):
    """
    Transparent rule-based recommendation engine for student-opportunity matching.
    Designed with hooks to plug in ML/AI models (e.g. Scikit-learn, embeddings, LLM) seamlessly.
    """

    def __init__(self, skill_weight: float = 0.65, interest_weight: float = 0.20, pref_weight: float = 0.15):
        self.skill_weight = skill_weight
        self.interest_weight = interest_weight
        self.pref_weight = pref_weight

    def calculate_match(self, student_profile: Dict[str, Any], opportunity: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculates match percentage and detailed skill breakdown between a student profile and an opportunity.
        """
        raw_student_skills = parse_csv_items(student_profile.get("skills", ""))
        student_interests = parse_csv_items(student_profile.get("interests", ""))
        preferred_type = (student_profile.get("preferred_type") or "").strip().lower()
        preferred_location = (student_profile.get("preferred_location") or "").strip().lower()

        raw_req_skills = parse_csv_items(opportunity.get("required_skills", ""))
        opp_type = (opportunity.get("type") or "").strip().lower()
        opp_location = (opportunity.get("location") or "").strip().lower()
        opp_mode = (opportunity.get("mode") or "").strip().lower()
        opp_title = (opportunity.get("title") or "").lower()
        opp_desc = (opportunity.get("description") or "").lower()

        # If student has zero skills listed, return default exploratory baseline
        if not raw_student_skills:
            return {
                "match_percentage": 50,
                "matching_skills": [],
                "missing_skills": raw_req_skills,
                "match_level": "Exploratory Match",
                "match_badge_class": "badge-info",
                "explanation": "Add skills to your profile to unlock precise percentage matching.",
                "matching_count": 0,
                "total_required": len(raw_req_skills)
            }

        # Normalize student skills set
        normalized_student_skills = {clean_skill(s) for s in raw_student_skills}
        normalized_interests = {clean_skill(i) for i in student_interests}

        matching_skills = []
        missing_skills = []

        # Compare required skills against student skills
        for req in raw_req_skills:
            req_clean = clean_skill(req)
            is_match = False

            # Exact or synonym match
            if req_clean in normalized_student_skills:
                is_match = True
            else:
                # Substring match (e.g. "machine learning" covers "ai", "react" in "react.js")
                for s in normalized_student_skills:
                    if (s in req_clean and len(s) >= 3) or (req_clean in s and len(req_clean) >= 3):
                        is_match = True
                        break

            if is_match:
                matching_skills.append(req)
            else:
                missing_skills.append(req)

        # 1. Skill Match Score (0.0 to 1.0)
        total_req = len(raw_req_skills)
        if total_req > 0:
            skill_ratio = len(matching_skills) / total_req
        else:
            skill_ratio = 0.5  # Neutral if no required skills specified

        # 2. Interest Match Score (0.0 to 1.0)
        interest_hits = 0
        if normalized_interests:
            combined_text = f"{opp_title} {opp_desc} {opp_type} {opportunity.get('required_skills', '').lower()}"
            for interest in normalized_interests:
                if interest in combined_text:
                    interest_hits += 1
            interest_ratio = min(1.0, interest_hits / max(1, min(len(normalized_interests), 3)))
        else:
            interest_ratio = 0.0

        # 3. Preferences Alignment Score (0.0 to 1.0)
        pref_score = 0.0
        if preferred_type and preferred_type != "all":
            if preferred_type == opp_type:
                pref_score += 0.6
        else:
            pref_score += 0.3  # Flexible preference

        if preferred_location:
            if opp_mode == "online" or preferred_location in opp_location or opp_location in preferred_location:
                pref_score += 0.4
        else:
            pref_score += 0.2

        pref_score = min(1.0, pref_score)

        # Combined Weighted Score
        weighted_score = (
            (skill_ratio * self.skill_weight) +
            (interest_ratio * self.interest_weight) +
            (pref_score * self.pref_weight)
        )

        # Realistic mapping curve:
        # If matching 100% of skills, minimum 85% match.
        if skill_ratio == 1.0:
            match_percentage = int(round(85 + (15 * (interest_ratio * 0.6 + pref_score * 0.4))))
        elif skill_ratio > 0:
            match_percentage = int(round(max(25, min(95, weighted_score * 100))))
        else:
            # 0 matching skills but might match interests
            match_percentage = int(round(max(15, min(40, (interest_ratio * 25) + (pref_score * 15)))))

        match_percentage = min(100, max(10, match_percentage))

        # Determine Match Level and Badge Styling
        if match_percentage >= 75:
            match_level = "High Match"
            badge_class = "badge-success"
        elif match_percentage >= 50:
            match_level = "Good Match"
            badge_class = "badge-primary"
        else:
            match_level = "Potential Match"
            badge_class = "badge-neutral"

        # Build transparent explanation
        if matching_skills and missing_skills:
            explanation = f"Matches {len(matching_skills)} of {total_req} skills ({', '.join(matching_skills[:2])}). Missing: {', '.join(missing_skills[:2])}."
        elif matching_skills and not missing_skills:
            explanation = "Outstanding fit! You meet all required technical skills for this role."
        elif not matching_skills and interest_hits > 0:
            explanation = "Aligned with your interests, but requires developing new technical skills."
        else:
            explanation = "Explore this opportunity to expand your skillset and profile."

        return {
            "match_percentage": match_percentage,
            "matching_skills": matching_skills,
            "missing_skills": missing_skills,
            "match_level": match_level,
            "match_badge_class": badge_class,
            "explanation": explanation,
            "matching_count": len(matching_skills),
            "total_required": total_req
        }

    def rank_opportunities(self, student_profile: Dict[str, Any], opportunities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Attaches match calculations and returns opportunities sorted by match percentage descending."""
        scored = []
        for opp in opportunities:
            opp_dict = dict(opp)
            match_info = self.calculate_match(student_profile, opp_dict)
            opp_dict.update(match_info)
            scored.append(opp_dict)

        scored.sort(key=lambda x: x["match_percentage"], reverse=True)
        return scored

    def predict_with_ml_model(self, student_vector: Any, opportunity_vector: Any) -> float:
        """
        Placeholder / Extension hook for future ML models.
        Can be upgraded with Scikit-learn cosine similarity, sentence-transformers, or Gemini embeddings.
        """
        return 0.0

# Singleton instance
engine = RuleBasedRecommendationEngine()
