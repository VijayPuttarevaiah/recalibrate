"""
RoadmapService — routes to 4 specialized agents based on user interest.

Agents: coding/software, fitness/health, immigration/visa, career (default).
"""


class RoadmapService:

    def generate_roadmap(
        self,
        interest: str,
        experience_level: str,
        hours_per_week: int,
        timeline_months: int,
    ) -> list[dict]:
        """
        Return a structured roadmap (list of phase dicts) tailored to the
        user's interest and experience level.
        """
        interest_lower = interest.lower() if interest else ""

        if self._is_coding(interest_lower):
            return self._coding_roadmap(experience_level)

        if self._is_fitness(interest_lower):
            return self._fitness_roadmap(experience_level)

        if self._is_immigration(interest_lower):
            return self._immigration_roadmap()

        return self._career_roadmap(experience_level)

    # ── Agent detectors ────────────────────────────────────────────────────────

    def _is_coding(self, interest: str) -> bool:
        return any(k in interest for k in ["coding", "software", "tech", "developer"])

    def _is_fitness(self, interest: str) -> bool:
        return any(k in interest for k in ["fitness", "health", "weight", "sport", "gym"])

    def _is_immigration(self, interest: str) -> bool:
        return any(k in interest for k in ["immigration", "visa", "pr", "passport", "residency"])

    # ── Coding agent ───────────────────────────────────────────────────────────

    def _coding_roadmap(self, experience_level: str) -> list[dict]:
        if experience_level == "beginner":
            return [
                {"phase": "Month 1", "steps": [
                    "Learn programming fundamentals",
                    "Practice basic exercises daily",
                ]},
                {"phase": "Month 2", "steps": [
                    "Learn data structures",
                    "Solve coding challenges",
                ]},
                {"phase": "Month 3", "steps": ["Build 2 portfolio projects"]},
                {"phase": "Month 4", "steps": [
                    "Prepare resume",
                    "Apply for roles",
                ]},
            ]
        if experience_level == "intermediate":
            return [
                {"phase": "Month 1", "steps": [
                    "Deep dive into system design",
                    "Review algorithms",
                ]},
                {"phase": "Month 2", "steps": [
                    "Build a full-stack project",
                    "Write unit tests",
                ]},
                {"phase": "Month 3", "steps": [
                    "Contribute to open source",
                    "Mock interviews",
                ]},
                {"phase": "Month 4", "steps": [
                    "Target companies",
                    "Apply and negotiate",
                ]},
            ]
        # advanced
        return [
            {"phase": "Month 1", "steps": [
                "Architect a scalable system",
                "Mentor junior developers",
            ]},
            {"phase": "Month 2", "steps": [
                "Lead a technical project",
                "Publish technical writing",
            ]},
            {"phase": "Month 3", "steps": [
                "Target senior/staff roles",
                "Build public portfolio",
            ]},
        ]

    # ── Fitness agent ──────────────────────────────────────────────────────────

    def _fitness_roadmap(self, experience_level: str) -> list[dict]:
        if experience_level == "beginner":
            return [
                {"phase": "Month 1", "steps": [
                    "Establish a 3x/week workout habit",
                    "Track daily food intake",
                ]},
                {"phase": "Month 2", "steps": [
                    "Increase to 4x/week",
                    "Add cardio sessions",
                ]},
                {"phase": "Month 3", "steps": [
                    "Measure progress and adjust plan",
                    "Focus on nutrition quality",
                ]},
                {"phase": "Month 4", "steps": [
                    "Introduce strength training",
                    "Celebrate milestones",
                ]},
            ]
        if experience_level == "intermediate":
            return [
                {"phase": "Month 1", "steps": [
                    "Audit current routine",
                    "Set specific measurable targets",
                ]},
                {"phase": "Month 2", "steps": [
                    "Progressive overload program",
                    "Optimize sleep and recovery",
                ]},
                {"phase": "Month 3", "steps": [
                    "Incorporate HIIT",
                    "Refine diet macros",
                ]},
                {"phase": "Month 4", "steps": [
                    "Reassess goals",
                    "Plan next phase",
                ]},
            ]
        # advanced
        return [
            {"phase": "Month 1", "steps": [
                "Set performance-based goals",
                "Periodization planning",
            ]},
            {"phase": "Month 2", "steps": [
                "Peak training block",
                "Competition or benchmark event",
            ]},
            {"phase": "Month 3", "steps": [
                "Deload and recover",
                "Set next cycle goals",
            ]},
        ]

    # ── Immigration agent ──────────────────────────────────────────────────────

    def _immigration_roadmap(self) -> list[dict]:
        return [
            {"phase": "Phase 1 — Research", "steps": [
                "Identify your target country and visa category",
                "Check eligibility requirements",
                "Gather required documents",
            ]},
            {"phase": "Phase 2 — Preparation", "steps": [
                "Take language proficiency test (IELTS/TOEFL)",
                "Get documents translated and notarized",
                "Engage an immigration consultant if needed",
            ]},
            {"phase": "Phase 3 — Application", "steps": [
                "Submit online application",
                "Pay application fees",
                "Track application status",
            ]},
            {"phase": "Phase 4 — Post-Approval", "steps": [
                "Receive visa/PR approval",
                "Book travel and accommodation",
                "Plan settlement: banking, housing, healthcare",
            ]},
        ]

    # ── Career agent (default) ─────────────────────────────────────────────────

    def _career_roadmap(self, experience_level: str) -> list[dict]:
        if experience_level == "beginner":
            return [
                {"phase": "Month 1", "steps": [
                    "Define your target career path",
                    "Research required skills and qualifications",
                ]},
                {"phase": "Month 2", "steps": [
                    "Enroll in relevant online courses",
                    "Build a LinkedIn profile",
                ]},
                {"phase": "Month 3", "steps": [
                    "Network with professionals in the field",
                    "Apply for entry-level roles or internships",
                ]},
            ]
        if experience_level == "intermediate":
            return [
                {"phase": "Month 1", "steps": [
                    "Identify skill gaps and fill them",
                    "Update resume and portfolio",
                ]},
                {"phase": "Month 2", "steps": [
                    "Reach out to recruiters on LinkedIn",
                    "Attend industry meetups",
                ]},
                {"phase": "Month 3", "steps": [
                    "Apply to target companies",
                    "Prepare for behavioural interviews",
                ]},
            ]
        # advanced
        return [
            {"phase": "Month 1", "steps": [
                "Define your personal brand",
                "Speak at events or publish thought leadership",
            ]},
            {"phase": "Month 2", "steps": [
                "Target executive or specialist roles",
                "Negotiate compensation packages",
            ]},
        ]