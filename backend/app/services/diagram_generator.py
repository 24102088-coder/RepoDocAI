from typing import List
from ..models.schemas import RepoAnalysis, DiagramData


class DiagramGenerator:
    """Generate Mermaid.js diagrams from repository analysis."""

    def generate_all(self, analysis: RepoAnalysis) -> List[DiagramData]:
        diagrams = []
        for fn in [
            self._architecture_diagram,
            self._structure_diagram,
            self._tech_stack_diagram,
            self._data_flow_diagram,
        ]:
            d = fn(analysis)
            if d:
                diagrams.append(d)
        return diagrams

    # ── Architecture ─────────────────────────────

    def _architecture_diagram(self, a: RepoAnalysis) -> DiagramData:
        cats: dict[str, list[str]] = {}
        for fw in a.frameworks:
            cats.setdefault(fw.category, []).append(fw.name)

        m = 'graph TB\n    subgraph "Application Architecture"\n'
        nodes = []

        layer_map = {
            "frontend": ("UI", "🖥️ Frontend"),
            "backend": ("API", "⚙️ Backend API"),
            "database": ("DB", "🗄️ Database"),
            "ml": ("ML", "🧠 AI / ML"),
            "ai": ("ML", "🧠 AI / ML"),
            "devops": ("DEVOPS", "🔧 DevOps"),
        }

        seen = set()
        for cat, fws in cats.items():
            info = layer_map.get(cat)
            if not info or info[0] in seen:
                continue
            seen.add(info[0])
            m += f'        {info[0]}["{info[1]}<br/>{", ".join(fws)}"]\n'
            nodes.append(info[0])

        if not nodes:
            top = ", ".join(list(a.languages.keys())[:3]) or "Code"
            m += f'        APP["📦 Application<br/>{top}"]\n'
            nodes.append("APP")

        m += "    end\n\n"

        edges = [("UI", "API", "HTTP/REST"), ("API", "DB", "Query"), ("API", "ML", "Inference")]
        for src, dst, label in edges:
            if src in nodes and dst in nodes:
                m += f"    {src} -->|{label}| {dst}\n"

        if "DEVOPS" in nodes:
            for n in nodes:
                if n != "DEVOPS":
                    m += f"    DEVOPS -.->|Deploy| {n}\n"

        styles = {"UI": "frontend", "API": "backend", "DB": "database", "ML": "ml", "DEVOPS": "devops"}
        colors = {
            "frontend": "#42b883,stroke:#35495e,color:#fff",
            "backend": "#3178c6,stroke:#1a4a7a,color:#fff",
            "database": "#f29111,stroke:#c77700,color:#fff",
            "ml": "#ee4c2c,stroke:#c9302c,color:#fff",
            "devops": "#326ce5,stroke:#1a4a7a,color:#fff",
        }
        for cls, color in colors.items():
            m += f"\n    classDef {cls} fill:{color}"
        m += "\n"
        for node_id, cls_name in styles.items():
            if node_id in nodes:
                m += f"    class {node_id} {cls_name}\n"

        return DiagramData(
            title="Architecture Overview",
            mermaid_code=m,
            description="High-level architecture showing major components and interactions.",
        )

    # ── Project structure ────────────────────────

    def _structure_diagram(self, a: RepoAnalysis) -> DiagramData:
        m = f'graph LR\n    ROOT["📁 {a.repo_name}"]\n'
        idx = 0
        for key, val in list(a.file_tree.items())[:12]:
            nid = f"N{idx}"
            if isinstance(val, dict) and "type" not in val:
                icon = self._folder_icon(key)
                m += f'    {nid}["{icon} {key}/"]\n    ROOT --> {nid}\n'
                si = 0
                for sk, sv in list(val.items())[:5]:
                    sid = f"S{idx}_{si}"
                    icon2 = "📁" if (isinstance(sv, dict) and "type" not in sv) else "📄"
                    m += f'    {sid}["{icon2} {sk}"]\n    {nid} --> {sid}\n'
                    si += 1
                if len(val) > 5:
                    m += f'    MORE{idx}["…"]\n    {nid} --> MORE{idx}\n'
            else:
                m += f'    {nid}["📄 {key}"]\n    ROOT --> {nid}\n'
            idx += 1

        return DiagramData(
            title="Project Structure",
            mermaid_code=m,
            description="Visual map of the project's directory layout.",
        )

    # ── Tech stack ───────────────────────────────

    def _tech_stack_diagram(self, a: RepoAnalysis) -> DiagramData:
        m = 'graph TD\n    subgraph "Technology Stack"\n'

        m += '        subgraph "Languages"\n'
        for i, (lang, lines) in enumerate(list(a.languages.items())[:6]):
            m += f'            L{i}["💻 {lang}<br/>{lines} lines"]\n'
        m += "        end\n"

        if a.frameworks:
            m += '        subgraph "Frameworks & Libraries"\n'
            icons = {"frontend": "🎨", "backend": "⚙️", "database": "🗄️", "ml": "🧠", "ai": "🧠"}
            for i, fw in enumerate(a.frameworks[:8]):
                ic = icons.get(fw.category, "🔧")
                m += f'            F{i}["{ic} {fw.name}"]\n'
            m += "        end\n"

        infra = []
        if a.has_docker:
            infra.append("🐳 Docker")
        if a.has_ci:
            infra.append("🔄 CI/CD")
        if a.has_tests:
            infra.append("✅ Tests")
        if infra:
            m += '        subgraph "Infrastructure"\n'
            for i, item in enumerate(infra):
                m += f'            I{i}["{item}"]\n'
            m += "        end\n"

        m += "    end\n"
        return DiagramData(title="Technology Stack", mermaid_code=m, description="Complete technology stack.")

    # ── Data flow ────────────────────────────────

    def _data_flow_diagram(self, a: RepoAnalysis) -> DiagramData:
        fe = [fw for fw in a.frameworks if fw.category == "frontend"]
        be = [fw for fw in a.frameworks if fw.category == "backend"]
        db = [fw for fw in a.frameworks if fw.category == "database"]

        m = "sequenceDiagram\n    participant U as 👤 User\n"
        if fe:
            m += f"    participant F as 🖥️ {fe[0].name}\n"
        if be:
            m += f"    participant B as ⚙️ {be[0].name}\n"
        if db:
            m += f"    participant D as 🗄️ {db[0].name}\n"

        if fe and be:
            m += "    U->>F: User Action\n    F->>B: API Request\n"
            if db:
                m += "    B->>D: Query Data\n    D-->>B: Return Results\n"
            m += "    B-->>F: API Response\n    F-->>U: Update UI\n"
        elif be:
            m += "    U->>B: Request\n"
            if db:
                m += "    B->>D: Query\n    D-->>B: Results\n"
            m += "    B-->>U: Response\n"
        else:
            m += '    participant APP as 📦 Application\n    U->>APP: Interact\n    APP-->>U: Response\n'

        return DiagramData(title="Data Flow", mermaid_code=m, description="Typical request/response flow.")

    # ── Helpers ───────────────────────────────────

    @staticmethod
    def _folder_icon(name: str) -> str:
        icons = {
            "src": "📦", "lib": "📚", "test": "🧪", "tests": "🧪",
            "docs": "📖", "public": "🌐", "static": "🌐",
            "config": "⚙️", "scripts": "📜", "utils": "🔧",
            "components": "🧩", "pages": "📄", "api": "🔌",
            "models": "📊", "views": "👁️", "controllers": "🎮",
            "routes": "🛤️", "middleware": "🔗", "services": "⚡",
            "assets": "🎨", "styles": "🎨", "images": "🖼️",
            "database": "🗄️", "migrations": "📋", "prisma": "🗄️",
        }
        return icons.get(name.lower(), "📁")
