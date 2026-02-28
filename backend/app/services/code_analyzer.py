import os
import json
from pathlib import Path
from typing import Dict, List, Optional

from ..models.schemas import RepoAnalysis, FileInfo, DependencyInfo, FrameworkInfo

# ──────────────────────────────────────────────────
# Extension → Language map
# ──────────────────────────────────────────────────
LANGUAGE_MAP = {
    ".py": "Python",
    ".js": "JavaScript",
    ".ts": "TypeScript",
    ".jsx": "JavaScript (JSX)",
    ".tsx": "TypeScript (TSX)",
    ".java": "Java",
    ".cpp": "C++",
    ".c": "C",
    ".h": "C/C++ Header",
    ".cs": "C#",
    ".go": "Go",
    ".rs": "Rust",
    ".rb": "Ruby",
    ".php": "PHP",
    ".swift": "Swift",
    ".kt": "Kotlin",
    ".scala": "Scala",
    ".r": "R",
    ".html": "HTML",
    ".css": "CSS",
    ".scss": "SCSS",
    ".sass": "SASS",
    ".vue": "Vue",
    ".svelte": "Svelte",
    ".sql": "SQL",
    ".sh": "Shell",
    ".bash": "Shell",
    ".yml": "YAML",
    ".yaml": "YAML",
    ".json": "JSON",
    ".xml": "XML",
    ".md": "Markdown",
    ".dockerfile": "Dockerfile",
    ".proto": "Protocol Buffers",
    ".graphql": "GraphQL",
    ".gql": "GraphQL",
}

# ──────────────────────────────────────────────────
# Framework detection rules
# ──────────────────────────────────────────────────
FRAMEWORK_INDICATORS = {
    "react": {"files": ["package.json"], "keywords": ["react", "react-dom"], "category": "frontend"},
    "next.js": {"files": ["next.config.js", "next.config.mjs", "next.config.ts"], "keywords": ["next"], "category": "frontend"},
    "vue": {"files": ["vue.config.js"], "keywords": ["vue"], "category": "frontend"},
    "angular": {"files": ["angular.json"], "keywords": ["@angular/core"], "category": "frontend"},
    "svelte": {"files": ["svelte.config.js"], "keywords": ["svelte"], "category": "frontend"},
    "express": {"files": [], "keywords": ["express"], "category": "backend"},
    "fastapi": {"files": [], "keywords": ["fastapi"], "category": "backend"},
    "django": {"files": ["manage.py"], "keywords": ["django"], "category": "backend"},
    "flask": {"files": [], "keywords": ["flask"], "category": "backend"},
    "spring": {"files": ["pom.xml", "build.gradle"], "keywords": ["spring-boot", "springframework"], "category": "backend"},
    "nestjs": {"files": ["nest-cli.json"], "keywords": ["@nestjs/core"], "category": "backend"},
    "mongodb": {"files": [], "keywords": ["mongoose", "mongodb", "pymongo"], "category": "database"},
    "postgresql": {"files": [], "keywords": ["pg", "psycopg2", "postgres"], "category": "database"},
    "mysql": {"files": [], "keywords": ["mysql", "mysql2"], "category": "database"},
    "redis": {"files": [], "keywords": ["redis", "ioredis"], "category": "database"},
    "docker": {"files": ["Dockerfile", "docker-compose.yml", "docker-compose.yaml"], "keywords": [], "category": "devops"},
    "kubernetes": {"files": [], "keywords": ["kubernetes"], "category": "devops"},
    "tailwindcss": {"files": ["tailwind.config.js", "tailwind.config.ts"], "keywords": ["tailwindcss"], "category": "frontend"},
    "prisma": {"files": ["prisma/schema.prisma"], "keywords": ["prisma", "@prisma/client"], "category": "database"},
    "pytorch": {"files": [], "keywords": ["torch", "pytorch"], "category": "ml"},
    "tensorflow": {"files": [], "keywords": ["tensorflow", "tf"], "category": "ml"},
    "langchain": {"files": [], "keywords": ["langchain"], "category": "ai"},
    "transformers": {"files": [], "keywords": ["transformers"], "category": "ai"},
}

IGNORE_DIRS = {
    ".git", "node_modules", "__pycache__", ".venv", "venv", "env",
    ".next", ".nuxt", "dist", "build", ".cache", "coverage",
    ".idea", ".vscode", ".vs", "vendor", "target", "bin", "obj",
    ".tox", ".mypy_cache", ".pytest_cache", "eggs",
}

IGNORE_FILES = {
    ".DS_Store", "Thumbs.db", ".gitignore", ".gitattributes",
    "package-lock.json", "yarn.lock", "pnpm-lock.yaml",
    "poetry.lock", "Pipfile.lock", "composer.lock",
}

KEY_FILES = [
    "README.md", "README.rst", "README.txt", "README",
    "package.json", "requirements.txt", "Pipfile", "pyproject.toml",
    "pom.xml", "build.gradle", "Cargo.toml", "go.mod",
    "Dockerfile", "docker-compose.yml", "docker-compose.yaml",
    ".env.example", "example.env",
    "Makefile", "Procfile",
    "app.py", "main.py", "index.js", "index.ts",
    "server.js", "server.ts", "app.js", "app.ts",
]


class CodeAnalyzer:
    """Walk a cloned repository and extract structured analysis data."""

    def analyze(self, repo_path: str) -> RepoAnalysis:
        repo_name = os.path.basename(repo_path)

        files = self._walk_files(repo_path)
        languages = self._count_languages(files)
        file_tree = self._build_file_tree(files)
        key_files = self._read_key_files(repo_path)
        dependencies = self._detect_dependencies(key_files)
        frameworks = self._detect_frameworks(repo_path, key_files, dependencies)
        entry_points = self._detect_entry_points(files)

        return RepoAnalysis(
            repo_name=repo_name,
            description=self._extract_description(key_files),
            languages=languages,
            frameworks=frameworks,
            dependencies=dependencies,
            file_tree=file_tree,
            file_count=len(files),
            total_lines=sum(f.lines for f in files),
            key_files=key_files,
            entry_points=entry_points,
            has_tests=self._has_tests(files),
            has_ci=self._has_ci(repo_path),
            has_docker=self._has_docker(repo_path),
            license=self._detect_license(repo_path),
        )

    # ── File walking ──────────────────────────────

    def _walk_files(self, repo_path: str) -> List[FileInfo]:
        files: List[FileInfo] = []
        for root, dirs, filenames in os.walk(repo_path):
            dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]
            for filename in filenames:
                if filename in IGNORE_FILES:
                    continue
                filepath = os.path.join(root, filename)
                rel_path = os.path.relpath(filepath, repo_path)
                ext = os.path.splitext(filename)[1].lower()
                if filename == "Dockerfile":
                    ext = ".dockerfile"
                language = LANGUAGE_MAP.get(ext, "Other")
                try:
                    size = os.path.getsize(filepath)
                    if size > 1_048_576:  # >1 MB → skip reading
                        files.append(FileInfo(path=rel_path, language=language, size=size, lines=0))
                        continue
                    with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                        lines = sum(1 for _ in f)
                    files.append(FileInfo(path=rel_path, language=language, size=size, lines=lines))
                except OSError:
                    continue
        return files

    def _count_languages(self, files: List[FileInfo]) -> Dict[str, int]:
        counts: Dict[str, int] = {}
        for f in files:
            if f.language != "Other" and f.lines > 0:
                counts[f.language] = counts.get(f.language, 0) + f.lines
        return dict(sorted(counts.items(), key=lambda x: x[1], reverse=True))

    def _build_file_tree(self, files: List[FileInfo]) -> Dict:
        tree: Dict = {}
        for f in files:
            parts = f.path.replace("\\", "/").split("/")
            current = tree
            for i, part in enumerate(parts):
                if i == len(parts) - 1:
                    current[part] = {"type": "file", "language": f.language, "lines": f.lines}
                else:
                    current.setdefault(part, {})
                    current = current[part]
        return tree

    # ── Key-file reading ──────────────────────────

    def _read_key_files(self, repo_path: str) -> Dict[str, str]:
        result: Dict[str, str] = {}
        for filename in KEY_FILES:
            filepath = os.path.join(repo_path, filename)
            if os.path.isfile(filepath):
                try:
                    with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                        result[filename] = f.read(50_000)
                except OSError:
                    continue

        # Also read common entry-point source files
        for pattern in [
            "src/index.ts", "src/index.js", "src/main.ts", "src/main.js",
            "src/app.ts", "src/app.js", "src/App.tsx", "src/App.jsx",
            "src/main.py", "app/__init__.py", "cmd/main.go",
            "src/lib.rs", "src/main.rs",
        ]:
            filepath = os.path.join(repo_path, pattern)
            if os.path.isfile(filepath):
                try:
                    with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                        result[pattern] = f.read(50_000)
                except OSError:
                    continue
        return result

    # ── Dependency detection ──────────────────────

    def _detect_dependencies(self, key_files: Dict[str, str]) -> List[DependencyInfo]:
        deps: List[DependencyInfo] = []

        # package.json
        if "package.json" in key_files:
            try:
                pkg = json.loads(key_files["package.json"])
                for name, ver in pkg.get("dependencies", {}).items():
                    deps.append(DependencyInfo(name=name, version=ver, type="runtime"))
                for name, ver in pkg.get("devDependencies", {}).items():
                    deps.append(DependencyInfo(name=name, version=ver, type="dev"))
            except json.JSONDecodeError:
                pass

        # requirements.txt
        if "requirements.txt" in key_files:
            for line in key_files["requirements.txt"].splitlines():
                line = line.strip()
                if line and not line.startswith("#"):
                    parts = line.split("==")
                    name = parts[0].split(">=")[0].split("<=")[0].split("~=")[0].strip()
                    version = parts[1].strip() if len(parts) > 1 else None
                    deps.append(DependencyInfo(name=name, version=version, type="runtime"))

        # pyproject.toml (lightweight parse)
        if "pyproject.toml" in key_files:
            in_deps = False
            for line in key_files["pyproject.toml"].splitlines():
                if "[project.dependencies]" in line or "[tool.poetry.dependencies]" in line:
                    in_deps = True
                    continue
                if in_deps:
                    if line.startswith("["):
                        break
                    if "=" in line:
                        name = line.split("=")[0].strip().strip('"').strip("'")
                        if name and name != "python":
                            deps.append(DependencyInfo(name=name, version=None, type="runtime"))

        # go.mod
        if "go.mod" in key_files:
            for line in key_files["go.mod"].splitlines():
                line = line.strip()
                if line and not line.startswith(("module", "go ", "//")):
                    if line.startswith("require"):
                        continue
                    parts = line.split()
                    if parts and parts[0] not in ("(", ")"):
                        deps.append(DependencyInfo(
                            name=parts[0],
                            version=parts[1] if len(parts) > 1 else None,
                            type="runtime",
                        ))

        # Cargo.toml
        if "Cargo.toml" in key_files:
            in_deps = False
            for line in key_files["Cargo.toml"].splitlines():
                if "[dependencies]" in line:
                    in_deps = True
                    continue
                if in_deps:
                    if line.startswith("["):
                        break
                    if "=" in line:
                        name = line.split("=")[0].strip()
                        deps.append(DependencyInfo(name=name, version=None, type="runtime"))

        return deps

    # ── Framework detection ───────────────────────

    def _detect_frameworks(
        self, repo_path: str, key_files: Dict[str, str], dependencies: List[DependencyInfo]
    ) -> List[FrameworkInfo]:
        dep_names = {d.name.lower() for d in dependencies}
        frameworks: List[FrameworkInfo] = []

        for name, indicators in FRAMEWORK_INDICATORS.items():
            confidence = 0.0
            for f in indicators["files"]:
                if os.path.isfile(os.path.join(repo_path, f)):
                    confidence += 0.5
            for kw in indicators["keywords"]:
                if kw.lower() in dep_names:
                    confidence += 0.5
            if confidence > 0:
                frameworks.append(FrameworkInfo(name=name, category=indicators["category"], confidence=min(confidence, 1.0)))

        return sorted(frameworks, key=lambda x: x.confidence, reverse=True)

    # ── Misc detection helpers ────────────────────

    def _detect_entry_points(self, files: List[FileInfo]) -> List[str]:
        entry_names = {"main", "index", "app", "server", "manage", "cli", "run"}
        return [f.path for f in files if os.path.splitext(os.path.basename(f.path))[0].lower() in entry_names]

    def _has_tests(self, files: List[FileInfo]) -> bool:
        indicators = ["test", "spec", "__tests__", "tests"]
        return any(any(t in f.path.lower() for t in indicators) for f in files)

    def _has_ci(self, repo_path: str) -> bool:
        ci = [".github/workflows", ".gitlab-ci.yml", ".travis.yml", "Jenkinsfile", ".circleci", "azure-pipelines.yml"]
        return any(os.path.exists(os.path.join(repo_path, p)) for p in ci)

    def _has_docker(self, repo_path: str) -> bool:
        return any(os.path.isfile(os.path.join(repo_path, f)) for f in ["Dockerfile", "docker-compose.yml", "docker-compose.yaml"])

    def _detect_license(self, repo_path: str) -> Optional[str]:
        for fname in ["LICENSE", "LICENSE.md", "LICENSE.txt", "LICENCE"]:
            filepath = os.path.join(repo_path, fname)
            if os.path.isfile(filepath):
                try:
                    with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                        content = f.read(2000)
                    for key in ["MIT", "Apache", "GPL", "BSD"]:
                        if key in content:
                            return key
                    return "Custom"
                except OSError:
                    pass
        return None

    def _extract_description(self, key_files: Dict[str, str]) -> Optional[str]:
        if "package.json" in key_files:
            try:
                desc = json.loads(key_files["package.json"]).get("description")
                if desc:
                    return desc
            except json.JSONDecodeError:
                pass
        for readme in ["README.md", "README.rst", "README.txt", "README"]:
            if readme in key_files:
                for line in key_files[readme].splitlines():
                    line = line.strip()
                    if line and not line.startswith(("#", "=", "[", "!")) and len(line) > 20:
                        return line[:500]
        return None
