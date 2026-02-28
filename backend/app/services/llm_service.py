import httpx
import json
import time
from typing import Dict, Optional

from ..config import settings
from ..models.schemas import RepoAnalysis


class LLMService:
    """
    LLM inference service with AMD GPU acceleration.

    Supported providers:
      • ollama  – local models accelerated by AMD ROCm (default)
      • openai  – OpenAI GPT-4 / GPT-4o API
      • gemini  – Google Gemini API
    """

    def __init__(self):
        self.provider = settings.LLM_PROVIDER
        self.ollama_url = settings.OLLAMA_BASE_URL
        self.ollama_model = settings.OLLAMA_MODEL
        self.openai_key = settings.OPENAI_API_KEY
        self.openai_model = settings.OPENAI_MODEL
        self.gemini_key = settings.GEMINI_API_KEY
        self._metrics: Dict = {}

    # ── Public API ───────────────────────────────

    async def generate(self, prompt: str, system_prompt: str = None) -> str:
        start = time.time()

        if self.provider == "ollama":
            result = await self._ollama_generate(prompt, system_prompt)
        elif self.provider == "openai":
            result = await self._openai_generate(prompt, system_prompt)
        elif self.provider == "gemini":
            result = await self._gemini_generate(prompt, system_prompt)
        else:
            raise ValueError(f"Unknown LLM provider: {self.provider}")

        self._metrics["last_generation_time"] = round(time.time() - start, 2)
        self._metrics["last_provider"] = self.provider
        return result

    async def check_health(self) -> Dict:
        health: Dict = {"provider": self.provider, "status": "unknown", "gpu_info": None}

        if self.provider == "ollama":
            try:
                async with httpx.AsyncClient(timeout=10.0) as client:
                    resp = await client.get(f"{self.ollama_url}/api/tags")
                    if resp.status_code == 200:
                        health["status"] = "healthy"
                        health["available_models"] = [m["name"] for m in resp.json().get("models", [])]
                    try:
                        ps = await client.get(f"{self.ollama_url}/api/ps")
                        if ps.status_code == 200:
                            health["gpu_info"] = ps.json()
                    except Exception:
                        pass
            except httpx.ConnectError:
                health["status"] = "offline"
                health["message"] = "Ollama is not running. Start with: ollama serve"
            except Exception as e:
                health["status"] = "error"
                health["message"] = str(e)
        elif self.provider in ("openai", "gemini"):
            health["status"] = "api_mode"

        return health

    def get_performance_metrics(self) -> Dict:
        return self._metrics.copy()

    # ── Provider implementations ─────────────────

    async def _ollama_generate(self, prompt: str, system_prompt: str = None) -> str:
        """Ollama (AMD GPU accelerated via ROCm)."""
        payload = {
            "model": self.ollama_model,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": 0.3, "top_p": 0.9, "num_predict": 4096},
        }
        if system_prompt:
            payload["system"] = system_prompt

        async with httpx.AsyncClient(timeout=300.0) as client:
            resp = await client.post(f"{self.ollama_url}/api/generate", json=payload)
            resp.raise_for_status()
            data = resp.json()

            # Capture throughput metrics from Ollama
            if "eval_count" in data and "eval_duration" in data:
                tokens = data["eval_count"]
                dur_ns = data["eval_duration"]
                tps = tokens / (dur_ns / 1e9) if dur_ns else 0
                self._metrics.update(tokens_per_second=round(tps, 2), total_tokens=tokens, gpu_accelerated=True)

            return data.get("response", "")

    async def _openai_generate(self, prompt: str, system_prompt: str = None) -> str:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        async with httpx.AsyncClient(timeout=120.0) as client:
            resp = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={"Authorization": f"Bearer {self.openai_key}", "Content-Type": "application/json"},
                json={"model": self.openai_model, "messages": messages, "temperature": 0.3, "max_tokens": 4096},
            )
            resp.raise_for_status()
            return resp.json()["choices"][0]["message"]["content"]

    async def _gemini_generate(self, prompt: str, system_prompt: str = None) -> str:
        full_prompt = f"{system_prompt}\n\n{prompt}" if system_prompt else prompt
        async with httpx.AsyncClient(timeout=120.0) as client:
            resp = await client.post(
                f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key={self.gemini_key}",
                json={
                    "contents": [{"parts": [{"text": full_prompt}]}],
                    "generationConfig": {"temperature": 0.3, "maxOutputTokens": 4096},
                },
            )
            resp.raise_for_status()
            return resp.json()["candidates"][0]["content"]["parts"][0]["text"]

    # ── Prompt builder ───────────────────────────

    def build_analysis_prompt(self, analysis: RepoAnalysis) -> tuple:
        system_prompt = (
            "You are RepoDocAI, an expert software documentation generator.\n"
            "You analyze codebases and produce comprehensive, well-structured Markdown documentation.\n"
            "Be thorough but concise. Include code examples where relevant.\n"
            "Always structure your output with clear headings and sections."
        )

        # Summarise key files (truncated)
        kf_summary = ""
        for path, content in list(analysis.key_files.items())[:10]:
            kf_summary += f"\n### {path}\n```\n{content[:3000]}\n```\n"

        fw_str = ", ".join(f"{fw.name} ({fw.category})" for fw in analysis.frameworks) or "None detected"
        dep_str = ", ".join(d.name for d in analysis.dependencies[:30]) or "None detected"
        lang_str = ", ".join(f"{l}: {c} lines" for l, c in list(analysis.languages.items())[:10])

        user_prompt = f"""Analyze this repository and generate comprehensive documentation.

## Repository Information
- **Name**: {analysis.repo_name}
- **Description**: {analysis.description or "Not provided"}
- **Languages**: {lang_str}
- **Frameworks**: {fw_str}
- **Dependencies**: {dep_str}
- **Total Files**: {analysis.file_count}
- **Total Lines**: {analysis.total_lines}
- **Has Tests**: {analysis.has_tests}
- **Has CI/CD**: {analysis.has_ci}
- **Has Docker**: {analysis.has_docker}
- **License**: {analysis.license or "Not specified"}
- **Entry Points**: {", ".join(analysis.entry_points) or "Not detected"}

## Key Files Content
{kf_summary}

## Generate the following documentation sections:

1. **Project Overview** – clear description of purpose, features, and value proposition (3-5 paragraphs).
2. **Architecture Overview** – high-level architecture, component interaction, design patterns.
3. **Technology Stack** – detailed breakdown of every technology, framework, and tool.
4. **Getting Started / Setup Guide** – step-by-step: prerequisites, install, configure, run.
5. **API Documentation** – endpoints with methods, paths, request/response. If none, state so.
6. **Project Structure** – directory layout explanation.
7. **Key Features** – list the main features.
8. **Configuration** – env vars, config files, settings.

Format each section with ## headings.  Separate sections with "---SECTION_BREAK---".
Be specific and reference actual files from the analysis."""

        return system_prompt, user_prompt
