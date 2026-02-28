from typing import List
from ..models.schemas import RepoAnalysis, GeneratedDocs, DocSection, DiagramData
from .llm_service import LLMService
from .diagram_generator import DiagramGenerator
from .advanced_features import (
    CodeHealthScorer,
    VulnerabilityScanner,
    BadgeGenerator,
    ComplexityAnalyzer,
    ContributingGenerator,
    CodeReviewPromptBuilder,
)


class DocGenerator:
    """Orchestrate full documentation generation: diagrams + LLM content + advanced features."""

    def __init__(self, llm_service: LLMService):
        self.llm = llm_service
        self.diagram_gen = DiagramGenerator()
        # ── Advanced feature engines ──
        self.health_scorer = CodeHealthScorer()
        self.vuln_scanner = VulnerabilityScanner()
        self.badge_gen = BadgeGenerator()
        self.complexity_analyzer = ComplexityAnalyzer()
        self.contributing_gen = ContributingGenerator()
        self.review_builder = CodeReviewPromptBuilder()

    async def generate(self, analysis: RepoAnalysis) -> GeneratedDocs:
        # 1. Generate diagrams (no LLM needed)
        diagrams = self.diagram_gen.generate_all(analysis)

        # 2. Build LLM prompts
        system_prompt, user_prompt = self.llm.build_analysis_prompt(analysis)

        # 3. Call LLM
        raw = await self.llm.generate(user_prompt, system_prompt)

        # 4. Parse into sections
        sections = self._parse_sections(raw)

        # 5. Separate well-known sections
        overview = tech_stack = setup_guide = ""
        api_docs = None
        remaining: List[DocSection] = []

        for sec in sections:
            t = sec.title.lower()
            if "overview" in t or "description" in t:
                overview = sec.content
            elif "technology" in t or "tech stack" in t:
                tech_stack = sec.content
            elif "setup" in t or "getting started" in t or "installation" in t:
                setup_guide = sec.content
            elif "api" in t:
                api_docs = sec.content
                remaining.append(sec)
            else:
                remaining.append(sec)

        if not overview and sections:
            overview = sections[0].content

        # ── 6. Advanced features ──────────────────
        health_data = self.health_scorer.score(analysis)
        vuln_data = self.vuln_scanner.scan(analysis)
        badge_data = self.badge_gen.generate(analysis, health_data)
        complexity_data = self.complexity_analyzer.analyze(analysis)
        contributing = self.contributing_gen.generate(analysis)

        # 7. AI Code Review (separate LLM call)
        ai_review = None
        try:
            review_sys, review_user = self.review_builder.build_review_prompt(analysis)
            ai_review = await self.llm.generate(review_user, review_sys)
        except Exception:
            ai_review = "Code review generation failed — LLM may be unavailable."

        return GeneratedDocs(
            repo_name=analysis.repo_name,
            overview=overview,
            sections=remaining or sections,
            diagrams=diagrams,
            tech_stack=tech_stack,
            setup_guide=setup_guide,
            api_docs=api_docs,
            health_score=health_data,
            vulnerability_scan=vuln_data,
            badges=badge_data,
            complexity_metrics=complexity_data,
            contributing_md=contributing,
            ai_code_review=ai_review,
        )

    # ── Parsing ──────────────────────────────────

    @staticmethod
    def _parse_sections(raw: str) -> List[DocSection]:
        if "---SECTION_BREAK---" in raw:
            parts = raw.split("---SECTION_BREAK---")
        else:
            parts, buf = [], ""
            for line in raw.split("\n"):
                if line.startswith("## ") and buf:
                    parts.append(buf)
                    buf = line + "\n"
                else:
                    buf += line + "\n"
            if buf:
                parts.append(buf)

        sections: List[DocSection] = []
        for i, part in enumerate(parts):
            part = part.strip()
            if not part:
                continue
            title = f"Section {i + 1}"
            for line in part.split("\n"):
                if line.startswith("#"):
                    title = line.lstrip("#").strip()
                    break
            sections.append(DocSection(title=title, content=part, order=i))
        return sections

    # ── Export helpers ────────────────────────────

    def generate_markdown(self, docs: GeneratedDocs) -> str:
        md = f"# {docs.repo_name}\n\n"

        if docs.overview:
            md += f"## Overview\n\n{docs.overview}\n\n"
        if docs.tech_stack:
            md += f"## Technology Stack\n\n{docs.tech_stack}\n\n"

        for d in docs.diagrams:
            md += f"## {d.title}\n\n{d.description}\n\n```mermaid\n{d.mermaid_code}\n```\n\n"

        if docs.setup_guide:
            md += f"## Getting Started\n\n{docs.setup_guide}\n\n"
        if docs.api_docs:
            md += f"## API Documentation\n\n{docs.api_docs}\n\n"

        for sec in docs.sections:
            md += f"{sec.content}\n\n"

        md += "---\n\n*Generated by [RepoDocAI](https://github.com/repodocai) — AI-powered documentation with AMD GPU acceleration*\n"
        return md
