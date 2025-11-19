# src/smart_applier/agents/resume_builder_agent.py
import io
import json
import os
import re
from pathlib import Path
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable
from reportlab.lib import colors
from dotenv import load_dotenv
import google.generativeai as genai
from smart_applier.utils.path_utils import get_data_dirs


class ResumeBuilderAgent:
    def __init__(self, user_profile: dict, output_dir: Path = None):
        if isinstance(user_profile, str):
            try:
                user_profile = json.loads(user_profile)
            except json.JSONDecodeError:
                raise ValueError("Provided profile is not valid JSON or dict.")

        self.profile = user_profile
        self.buffer = io.BytesIO()

        paths = get_data_dirs()
        self.output_dir = output_dir or paths["resumes"]
        self.output_dir.mkdir(parents=True, exist_ok=True)

        load_dotenv()
        api_key = os.getenv("GEMINI_API_KEY")
        self.model = None
        if api_key:
            try:
                genai.configure(api_key=api_key)
                self.model = genai.GenerativeModel("models/gemini-2.0-flash")
            except Exception as e:
                print(f"⚠️ Gemini init failed: {e}")

    def generate_clean_summary(self):
        if not self.model:
            return None
        try:
            skills = self.profile.get("skills", {})
            projects = self.profile.get("projects", [])
            experience = self.profile.get("experience", [])

            prompt = (
                "You are a professional resume writer.\n"
                "Write a concise 3-line professional summary.\n"
                "Avoid pronouns and generic phrases.\n\n"
                f"Skills: {skills}\nProjects: {projects}\nExperience: {experience}\n"
            )
            response = self.model.generate_content(prompt)
            summary = response.text.strip()
            summary = re.sub(r"[*•\-]+", "", summary)
            summary = re.sub(r"\n+", " ", summary)
            summary = re.sub(r"\b(I|my|me|our|we|us)\b", "", summary, flags=re.I)
            return summary.strip()
        except Exception as e:
            print(f"⚠️ Gemini summary generation failed: {e}")
            return None

    def build_resume(self) -> io.BytesIO:
        """Generate PDF in a memory buffer and return BytesIO."""
        doc = SimpleDocTemplate(
            self.buffer,
            pagesize=A4,
            leftMargin=50,
            rightMargin=50,
            topMargin=50,
            bottomMargin=30,
        )

        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            "Title",
            fontSize=20,
            textColor=colors.HexColor("#003366"),
            alignment=TA_CENTER,
            spaceAfter=12,
            leading=22,
        )
        header_style = ParagraphStyle(
            "Header",
            fontSize=14,
            textColor=colors.HexColor("#003366"),
            spaceAfter=4,
            leading=18,
        )
        normal_style = ParagraphStyle("Normal", fontSize=10, leading=14)
        bullet_style = ParagraphStyle("Bullet", leftIndent=15, fontSize=10, leading=12)

        elements = []

        # PERSONAL DETAILS
        personal = self.profile.get("personal", {})
        name = personal.get("name", "Your Name")
        email = personal.get("email", "")
        phone = personal.get("phone", "")
        location = personal.get("location", "")
        linkedin = personal.get("linkedin", "")
        github = personal.get("github", "")

        elements.append(Paragraph(f"<b>{name}</b>", title_style))
        elements.append(Spacer(1, 6))
        elements.append(
            Paragraph(
                f"{email} | {phone} | {location}",
                ParagraphStyle("center", alignment=TA_CENTER, fontSize=10),
            )
        )
        elements.append(Spacer(1, 4))

        links_html = []
        if linkedin:
            links_html.append(f'<a href="{linkedin}"><b>LinkedIn</b></a>')
        if github:
            links_html.append(f'<a href="{github}"><b>GitHub</b></a>')

        if links_html:
            elements.append(
                Paragraph(
                    " | ".join(links_html),
                    ParagraphStyle(
                        "links",
                        alignment=TA_CENTER,
                        fontSize=10,
                        textColor=colors.blue,
                        leading=14,
                    ),
                )
            )

        elements.append(Spacer(1, 14))
        elements.append(
            HRFlowable(width="100%", color=colors.HexColor("#003366"), thickness=0.6)
        )
        elements.append(Spacer(1, 10))

        # SUMMARY
        summary = self.profile.get("summary")
        if not summary:
            summary = self.generate_clean_summary() or (
                "Results-driven data analyst skilled in Python, Power BI, and cloud analytics."
            )

        elements.append(Paragraph("Professional Summary", header_style))
        elements.append(Paragraph(summary, normal_style))
        elements.append(Spacer(1, 12))
        elements.append(HRFlowable(width="100%", color=colors.grey, thickness=0.3))
        elements.append(Spacer(1, 8))

        # EDUCATION
        education = self.profile.get("education", [])
        if education:
            elements.append(Paragraph("Education", header_style))
            for edu in education:
                elements.append(Paragraph(edu, normal_style))
            elements.append(Spacer(1, 8))
            elements.append(HRFlowable(width="100%", color=colors.grey, thickness=0.3))
            elements.append(Spacer(1, 8))

        # SKILLS
        skills = self.profile.get("skills", {})
        if skills:
            elements.append(Paragraph("Skills", header_style))
            for cat, items in skills.items():
                elements.append(
                    Paragraph(f"<b>{cat}:</b> {', '.join(items)}", normal_style)
                )
            elements.append(Spacer(1, 8))
            elements.append(HRFlowable(width="100%", color=colors.grey, thickness=0.3))
            elements.append(Spacer(1, 8))

        # PROJECTS
        projects = self.profile.get("projects", [])
        if projects:
            elements.append(Paragraph("Projects", header_style))
            for proj in projects:
                elements.append(Paragraph(f"<b>{proj.get('title','')}</b>", normal_style))
                if proj.get("description"):
                    elements.append(Paragraph(proj["description"], bullet_style))
                elements.append(Spacer(1, 6))
            elements.append(HRFlowable(width="100%", color=colors.grey, thickness=0.3))
            elements.append(Spacer(1, 8))

        # EXPERIENCE
        experience = self.profile.get("experience", [])
        if experience:
            elements.append(Paragraph("Experience", header_style))
            for exp in experience:
                elements.append(Paragraph(exp, bullet_style))
            elements.append(Spacer(1, 8))
            elements.append(HRFlowable(width="100%", color=colors.grey, thickness=0.3))
            elements.append(Spacer(1, 8))

        # CERTIFICATIONS
        certs = self.profile.get("certificates", [])
        if certs:
            elements.append(Paragraph("Certifications", header_style))
            for cert in certs:
                elements.append(
                    Paragraph(f"{cert.get('name','')} - {cert.get('source','')}", bullet_style)
                )
            elements.append(Spacer(1, 8))

        doc.build(elements)
        self.buffer.seek(0)
        return self.buffer
