"""
Advanced analysis features for RepoDocAI.
Adds: Code Health Score, Vulnerability Scanner, Badge Generator,
      CONTRIBUTING.md generator, Code Complexity Metrics, AI Code Review.
"""

import re
import math
from typing import Dict, List, Optional, Tuple
from ..models.schemas import RepoAnalysis


# ═══════════════════════════════════════════════════
#  CODE HEALTH SCORE
# ═══════════════════════════════════════════════════

class CodeHealthScorer:
    """Rate a repo A-F based on engineering quality signals."""

    RUBRIC = {
        "has_readme":       {"weight": 15, "label": "README present"},
        "has_tests":        {"weight": 15, "label": "Test suite"},
        "has_ci":           {"weight": 12, "label": "CI/CD pipeline"},
        "has_docker":       {"weight": 8,  "label": "Containerized"},
        "has_license":      {"weight": 8,  "label": "License file"},
        "has_env_example":  {"weight": 5,  "label": ".env example"},
        "has_gitignore":    {"weight": 5,  "label": ".gitignore"},
        "code_org":         {"weight": 12, "label": "Code organization"},
        "doc_density":      {"weight": 10, "label": "Documentation density"},
        "dep_management":   {"weight": 10, "label": "Dependency management"},
    }

    def score(self, analysis: RepoAnalysis) -> Dict:
        checks: Dict[str, Tuple[bool, str]] = {}
        total = 0
        max_total = 0

        # Binary signals
        readme_keys = [k for k in analysis.key_files if k.lower().startswith("readme")]
        checks["has_readme"] = (bool(readme_keys), "README.md found" if readme_keys else "No README found")
        checks["has_tests"] = (analysis.has_tests, "Tests detected" if analysis.has_tests else "No tests found")
        checks["has_ci"] = (analysis.has_ci, "CI/CD found" if analysis.has_ci else "No CI/CD")
        checks["has_docker"] = (analysis.has_docker, "Docker found" if analysis.has_docker else "No Docker")
        checks["has_license"] = (bool(analysis.license), f"License: {analysis.license}" if analysis.license else "No license")

        env_found = any("env" in k.lower() and "example" in k.lower() for k in analysis.key_files)
        checks["has_env_example"] = (env_found, ".env.example found" if env_found else "No .env.example")

        gitignore = any(k == ".gitignore" for k in analysis.key_files)
        checks["has_gitignore"] = (gitignore, ".gitignore present" if gitignore else "Missing .gitignore")

        # Code organization — presence of a src/ or organized directory structure
        tree_dirs = [k for k, v in analysis.file_tree.items() if isinstance(v, dict) and "type" not in v]
        org_dirs = {"src", "lib", "app", "pkg", "cmd", "internal", "components", "services", "utils", "models"}
        has_org = bool(set(d.lower() for d in tree_dirs) & org_dirs)
        checks["code_org"] = (has_org, "Organized directory structure" if has_org else "Flat file structure")

        # Documentation density — markdown lines vs code lines
        md_lines = analysis.languages.get("Markdown", 0)
        code_lines = analysis.total_lines - md_lines
        doc_ratio = md_lines / max(code_lines, 1)
        good_docs = doc_ratio >= 0.05  # at least 5% docs
        checks["doc_density"] = (good_docs, f"{doc_ratio:.1%} doc-to-code ratio" if good_docs else f"Low docs ({doc_ratio:.1%})")

        # Dependency management
        has_deps = bool(analysis.dependencies)
        checks["dep_management"] = (has_deps, f"{len(analysis.dependencies)} deps managed" if has_deps else "No package manager detected")

        # Calculate score
        for key, rubric in self.RUBRIC.items():
            max_total += rubric["weight"]
            if checks.get(key, (False,))[0]:
                total += rubric["weight"]

        pct = (total / max_total * 100) if max_total > 0 else 0
        grade = self._pct_to_grade(pct)

        details = []
        for key, rubric in self.RUBRIC.items():
            passed, msg = checks.get(key, (False, "Unknown"))
            details.append({
                "check": rubric["label"],
                "passed": passed,
                "message": msg,
                "weight": rubric["weight"],
            })

        return {
            "score": round(pct),
            "grade": grade,
            "max_score": 100,
            "details": details,
            "summary": self._grade_summary(grade),
        }

    @staticmethod
    def _pct_to_grade(pct: float) -> str:
        if pct >= 90: return "A+"
        if pct >= 80: return "A"
        if pct >= 70: return "B"
        if pct >= 60: return "C"
        if pct >= 50: return "D"
        return "F"

    @staticmethod
    def _grade_summary(grade: str) -> str:
        summaries = {
            "A+": "Exceptional! This repo follows nearly all best practices.",
            "A": "Excellent engineering quality. Well-maintained and documented.",
            "B": "Good quality. A few improvements would make it great.",
            "C": "Average. Several important areas need attention.",
            "D": "Below average. Significant improvements needed.",
            "F": "Needs work. Missing most software engineering best practices.",
        }
        return summaries.get(grade, "Unknown grade.")


# ═══════════════════════════════════════════════════
#  VULNERABILITY SCANNER (heuristic)
# ═══════════════════════════════════════════════════

# Well-known packages with known vulnerability history
KNOWN_VULNERABLE = {
    # npm
    "lodash": {"below": "4.17.21", "severity": "high", "cve": "Prototype pollution"},
    "minimist": {"below": "1.2.6", "severity": "critical", "cve": "Prototype pollution"},
    "node-fetch": {"below": "2.6.7", "severity": "medium", "cve": "Exposure of sensitive information"},
    "express": {"below": "4.17.3", "severity": "medium", "cve": "Open redirect"},
    "axios": {"below": "0.21.2", "severity": "high", "cve": "Server-Side Request Forgery"},
    "jsonwebtoken": {"below": "9.0.0", "severity": "high", "cve": "Insecure defaults"},
    "tar": {"below": "6.1.9", "severity": "high", "cve": "Arbitrary file creation"},
    # pip
    "django": {"below": "4.2.8", "severity": "high", "cve": "Multiple vulnerabilities"},
    "flask": {"below": "2.3.2", "severity": "medium", "cve": "Security fixes"},
    "requests": {"below": "2.31.0", "severity": "medium", "cve": "Unintended leak of Proxy-Authorization header"},
    "pillow": {"below": "10.0.1", "severity": "high", "cve": "Multiple image processing vulns"},
    "numpy": {"below": "1.22.0", "severity": "low", "cve": "Buffer overflow on complex arrays"},
    "urllib3": {"below": "2.0.7", "severity": "medium", "cve": "Cookie leak on cross-origin redirects"},
    "cryptography": {"below": "41.0.4", "severity": "high", "cve": "Multiple OpenSSL vulns"},
}


class VulnerabilityScanner:
    """Heuristic vulnerability scanner based on dependency versions."""

    def scan(self, analysis: RepoAnalysis) -> Dict:
        findings: List[Dict] = []
        total = len(analysis.dependencies)
        scanned = 0

        for dep in analysis.dependencies:
            scanned += 1
            name = dep.name.lower()
            if name in KNOWN_VULNERABLE:
                info = KNOWN_VULNERABLE[name]
                # Simple version comparison (won't always work perfectly)
                if dep.version and self._version_below(dep.version, info["below"]):
                    findings.append({
                        "package": dep.name,
                        "installed_version": dep.version,
                        "fix_version": info["below"],
                        "severity": info["severity"],
                        "description": info["cve"],
                    })

        severity_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}
        for f in findings:
            severity_counts[f["severity"]] = severity_counts.get(f["severity"], 0) + 1

        risk = "low"
        if severity_counts["critical"] > 0:
            risk = "critical"
        elif severity_counts["high"] > 0:
            risk = "high"
        elif severity_counts["medium"] > 0:
            risk = "medium"

        return {
            "total_dependencies": total,
            "scanned": scanned,
            "vulnerabilities_found": len(findings),
            "risk_level": risk,
            "severity_breakdown": severity_counts,
            "findings": findings,
        }

    @staticmethod
    def _version_below(installed: str, threshold: str) -> bool:
        """Basic semver comparison."""
        try:
            inst_parts = [int(x) for x in re.findall(r'\d+', installed)[:3]]
            thresh_parts = [int(x) for x in re.findall(r'\d+', threshold)[:3]]
            while len(inst_parts) < 3:
                inst_parts.append(0)
            while len(thresh_parts) < 3:
                thresh_parts.append(0)
            return inst_parts < thresh_parts
        except (ValueError, IndexError):
            return False


# ═══════════════════════════════════════════════════
#  BADGE GENERATOR
# ═══════════════════════════════════════════════════

class BadgeGenerator:
    """Generate shields.io badge markdown for the repo."""

    def generate(self, analysis: RepoAnalysis, health_score: Dict) -> List[Dict]:
        badges: List[Dict] = []

        # Languages
        top_lang = list(analysis.languages.keys())[0] if analysis.languages else None
        if top_lang:
            color = self._lang_color(top_lang)
            badges.append({
                "label": "Language",
                "message": top_lang,
                "color": color,
                "markdown": f"![{top_lang}](https://img.shields.io/badge/Language-{top_lang.replace(' ', '%20')}-{color})",
            })

        # Frameworks
        for fw in analysis.frameworks[:3]:
            badges.append({
                "label": "Framework",
                "message": fw.name,
                "color": "blue",
                "markdown": f"![{fw.name}](https://img.shields.io/badge/Framework-{fw.name.replace(' ', '%20')}-blue)",
            })

        # Health Grade
        grade = health_score.get("grade", "?")
        grade_color = {"A+": "brightgreen", "A": "green", "B": "yellowgreen", "C": "yellow", "D": "orange", "F": "red"}.get(grade, "gray")
        badges.append({
            "label": "Code Health",
            "message": grade,
            "color": grade_color,
            "markdown": f"![Health](https://img.shields.io/badge/Code%20Health-{grade}-{grade_color})",
        })

        # Misc
        if analysis.has_tests:
            badges.append({"label": "Tests", "message": "✓", "color": "green", "markdown": "![Tests](https://img.shields.io/badge/Tests-Passing-green)"})
        if analysis.has_ci:
            badges.append({"label": "CI/CD", "message": "✓", "color": "blue", "markdown": "![CI](https://img.shields.io/badge/CI%2FCD-Configured-blue)"})
        if analysis.has_docker:
            badges.append({"label": "Docker", "message": "✓", "color": "2496ED", "markdown": "![Docker](https://img.shields.io/badge/Docker-Ready-2496ED)"})
        if analysis.license:
            badges.append({"label": "License", "message": analysis.license, "color": "lightgrey", "markdown": f"![License](https://img.shields.io/badge/License-{analysis.license}-lightgrey)"})

        return badges

    @staticmethod
    def _lang_color(lang: str) -> str:
        colors = {
            "Python": "3776AB", "JavaScript": "F7DF1E", "TypeScript": "3178C6",
            "Java": "ED8B00", "Go": "00ADD8", "Rust": "000000", "C++": "00599C",
            "C#": "239120", "Ruby": "CC342D", "PHP": "777BB4", "Swift": "FA7343",
            "Kotlin": "7F52FF", "Scala": "DC322F",
        }
        return colors.get(lang, "555555")


# ═══════════════════════════════════════════════════
#  CODE COMPLEXITY METRICS
# ═══════════════════════════════════════════════════

class ComplexityAnalyzer:
    """Compute code complexity and structure metrics."""

    def analyze(self, analysis: RepoAnalysis) -> Dict:
        # Language distribution
        total_code = sum(analysis.languages.values())
        lang_dist = [
            {"language": lang, "lines": lines, "percentage": round(lines / total_code * 100, 1) if total_code else 0}
            for lang, lines in list(analysis.languages.items())[:10]
        ]

        # Estimate average file size
        avg_lines = analysis.total_lines / max(analysis.file_count, 1)

        # Estimate number of modules/components from tree
        top_dirs = [k for k, v in analysis.file_tree.items() if isinstance(v, dict) and "type" not in v]

        # Framework categories
        categories = {}
        for fw in analysis.frameworks:
            categories.setdefault(fw.category, []).append(fw.name)

        # Dependency stats
        runtime_deps = [d for d in analysis.dependencies if d.type == "runtime"]
        dev_deps = [d for d in analysis.dependencies if d.type == "dev"]

        return {
            "total_files": analysis.file_count,
            "total_lines": analysis.total_lines,
            "avg_lines_per_file": round(avg_lines, 1),
            "language_distribution": lang_dist,
            "top_modules": top_dirs[:10],
            "framework_categories": categories,
            "dependency_stats": {
                "total": len(analysis.dependencies),
                "runtime": len(runtime_deps),
                "dev": len(dev_deps),
            },
            "codebase_size": self._categorize_size(analysis.total_lines),
        }

    @staticmethod
    def _categorize_size(lines: int) -> str:
        if lines < 500: return "Micro"
        if lines < 2000: return "Small"
        if lines < 10000: return "Medium"
        if lines < 50000: return "Large"
        return "Enterprise"


# ═══════════════════════════════════════════════════
#  CONTRIBUTING.md GENERATOR
# ═══════════════════════════════════════════════════

class ContributingGenerator:
    """Auto-generate a CONTRIBUTING.md from repo analysis."""

    def generate(self, analysis: RepoAnalysis) -> str:
        repo = analysis.repo_name
        top_lang = list(analysis.languages.keys())[0] if analysis.languages else "code"

        md = f"# Contributing to {repo}\n\n"
        md += f"Thank you for your interest in contributing to **{repo}**! "
        md += "We welcome contributions from the community.\n\n"

        md += "## Getting Started\n\n"
        md += "1. Fork the repository\n"
        md += f"2. Clone your fork: `git clone https://github.com/YOUR_USERNAME/{repo}.git`\n"
        md += f"3. Create a feature branch: `git checkout -b feature/your-feature`\n"

        # Language-specific setup
        if "Python" in analysis.languages:
            md += "4. Create a virtual environment: `python -m venv venv && source venv/bin/activate`\n"
            if "requirements.txt" in analysis.key_files:
                md += "5. Install dependencies: `pip install -r requirements.txt`\n"
            elif "pyproject.toml" in analysis.key_files:
                md += "5. Install dependencies: `pip install -e .`\n"
        elif "JavaScript" in analysis.languages or "TypeScript" in analysis.languages:
            if "package.json" in analysis.key_files:
                md += "4. Install dependencies: `npm install`\n"
        elif "Go" in analysis.languages:
            md += "4. Install dependencies: `go mod download`\n"
        elif "Rust" in analysis.languages:
            md += "4. Build: `cargo build`\n"

        md += "\n## Development Guidelines\n\n"
        md += f"- Write clean, readable {top_lang} code\n"
        md += "- Follow existing code style and conventions\n"
        md += "- Add comments for complex logic\n"

        if analysis.has_tests:
            md += "- **Write tests** for new features or bug fixes\n"
            md += "- Ensure all existing tests pass before submitting\n"

        if analysis.has_ci:
            md += "- CI/CD will automatically run on your pull request\n"

        md += "\n## Pull Request Process\n\n"
        md += "1. Update documentation if needed\n"
        md += "2. Ensure your code passes all tests and linting\n"
        md += "3. Write a clear PR description explaining your changes\n"
        md += "4. Link any related issues\n"
        md += "5. Request review from maintainers\n"

        md += "\n## Code of Conduct\n\n"
        md += "Please be respectful and constructive in all interactions. "
        md += "We are committed to providing a welcoming and inclusive experience for everyone.\n"

        md += f"\n---\n\n*Thank you for contributing to {repo}!*\n"
        return md


# ═══════════════════════════════════════════════════
#  AI CODE REVIEW PROMPTS
# ═══════════════════════════════════════════════════

class CodeReviewPromptBuilder:
    """Build prompts for AI-powered code review."""

    @staticmethod
    def build_review_prompt(analysis: RepoAnalysis) -> tuple:
        system = (
            "You are an expert Senior Software Engineer performing a code review. "
            "Analyze the codebase and provide actionable feedback across: "
            "security, performance, code quality, best practices, and architecture. "
            "Be specific — reference file names and patterns. "
            "Rate each area 1-10 and give concrete improvement suggestions."
        )

        # Gather key source code
        source_snippets = ""
        for path, content in list(analysis.key_files.items())[:8]:
            if any(path.endswith(ext) for ext in [".py", ".js", ".ts", ".tsx", ".jsx", ".go", ".rs", ".java"]):
                source_snippets += f"\n### {path}\n```\n{content[:2500]}\n```\n"

        fw_str = ", ".join(f.name for f in analysis.frameworks) or "None"
        dep_str = ", ".join(d.name for d in analysis.dependencies[:20]) or "None"

        user = f"""Perform a thorough code review for this project:

**Project**: {analysis.repo_name}
**Languages**: {", ".join(analysis.languages.keys())}
**Frameworks**: {fw_str}
**Dependencies**: {dep_str}
**Has Tests**: {analysis.has_tests}
**Has CI/CD**: {analysis.has_ci}

## Source Code Samples:
{source_snippets}

## Provide review in these sections:

1. **Security** (1-10): Authentication, input validation, secrets management, SQL injection, XSS
2. **Performance** (1-10): Caching, query optimization, memory management, async patterns
3. **Code Quality** (1-10): Readability, DRY, naming, error handling, SOLID principles
4. **Architecture** (1-10): Separation of concerns, scalability, design patterns
5. **Best Practices** (1-10): Testing, CI/CD, Docker, env management, documentation

For each section give:
- Score (1-10)
- Key findings (bullet points)
- Specific suggestions with file references

End with **Overall Score** (average) and **Top 3 Priority Actions**.

Separate sections with "---REVIEW_BREAK---"."""

        return system, user
