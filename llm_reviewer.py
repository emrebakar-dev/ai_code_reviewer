import os
import json
import re
from dataclasses import dataclass, field
from typing import Optional

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False


@dataclass
class AIFinding:
    severity: str
    category: str
    function_name: Optional[str]
    line_range: Optional[str]
    message: str
    suggestion: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "severity":      self.severity,
            "category":      self.category,
            "function_name": self.function_name,
            "line_range":    self.line_range,
            "message":       self.message,
            "suggestion":    self.suggestion,
        }


@dataclass
class AIReviewResult:
    findings: list = field(default_factory=list)
    raw_response: str = ""
    error: Optional[str] = None
    model_used: str = ""
    skipped: bool = False
    parse_failed: bool = False  # True: model cevap verdi ama JSON parse edilemedi


SYSTEM_PROMPT = """You are a senior multi-language software auditor and code reviewer. Your task is to analyze the provided source code (Python, C, C++, Java, etc.) and identify issues.

Review the code in these categories:
- Potential Bugs
- Security (Memory safety, Buffer Overflow, SQL Injection, Injection, Hard-coded secrets, Insecure Deserialization, Sensitive data exposure)
- Performance
- Code Quality
- Readability
- Maintainability

For Java specifically, also consider:
- SQL Injection via string concatenation (use PreparedStatement)
- Insecure deserialization (ObjectInputStream)
- Sensitive data in logs (System.out.println with passwords/tokens)
- Empty catch blocks that silently swallow exceptions
- String comparison with == instead of .equals()
- Raw types without generics

IMPORTANT RULES:
1. Only report issues you can directly observe in the code. Do NOT speculate about runtime behavior you cannot confirm.
2. If you are unsure about an issue, do NOT report it as a definite problem. Omit it or phrase it as a suggestion.
3. Be concise and actionable.

Return your findings as a JSON array with this exact structure:
[
  {
    "severity": "HIGH|MEDIUM|LOW",
    "category": "Potential Bugs|Security|Performance|Code Quality|Readability|Maintainability",
    "function_name": "function_name or null",
    "line_range": "42 or 10-25 or null",
    "message": "Clear description of the issue",
    "suggestion": "Concrete fix suggestion or null"
  }
]

Return ONLY the JSON array, no markdown fences, no extra text."""


class LLMReviewer:
    def __init__(self):
        self.api_key  = os.getenv("OPENAI_API_KEY", "")
        self.base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
        self.model    = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    def review(self, source_code: str, filepath: str) -> AIReviewResult:
        if not self.api_key:
            return AIReviewResult(
                skipped=True,
                error=(
                    "OPENAI_API_KEY bulunamadı. "
                    "AI incelemesi atlandı. "
                    ".env dosyasına API anahtarını ekleyin."
                ),
            )

        if not OPENAI_AVAILABLE:
            return AIReviewResult(
                skipped=True,
                error="openai paketi kurulu değil. 'pip install openai' komutunu çalıştırın.",
            )

        import time as _time
        client = OpenAI(api_key=self.api_key, base_url=self.base_url)
        ext = filepath.split(".")[-1].lower() if "." in filepath else "code"
        if "localhost" in self.base_url or "11434" in self.base_url:
            user_content = f"/no_think\n\nFile: {filepath}\n\n```{ext}\n{source_code}\n```"
        else:
            user_content = f"File: {filepath}\n\n```{ext}\n{source_code}\n```"

        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user",   "content": user_content},
                    ],
                    temperature=0.2,
                    max_tokens=4096,
                )
                raw      = response.choices[0].message.content or ""
                findings = self._parse_response(raw)
                return AIReviewResult(
                    findings=findings,
                    raw_response=raw,
                    model_used=self.model,
                    parse_failed=(len(findings) == 0 and len(raw.strip()) > 0),
                )
            except Exception as exc:
                err_str = str(exc).lower()
                is_rate_limit = "rate" in err_str or "429" in err_str or "limit" in err_str
                if is_rate_limit and attempt < max_retries - 1:
                    wait = 10 * (attempt + 1)
                    _time.sleep(wait)
                    continue
                return AIReviewResult(error=str(exc))

    def _parse_response(self, raw: str) -> list:
        # <think>...</think> tam blokları temizle
        cleaned = re.sub(r"<think>.*?</think>", "", raw, flags=re.DOTALL).strip()
        # Kapanmamış <think> bloğu varsa <think> sonrasındaki ilk '[' karakterine kadar olan kısmı al
        if "<think>" in cleaned and "[" in cleaned:
            cleaned = cleaned[cleaned.find("["):]
        cleaned = re.sub(r"```(?:json)?\s*", "", cleaned).strip().rstrip("`").strip()

        # 1. Doğrudan tam JSON parse
        try:
            return self._build_findings(json.loads(cleaned))
        except json.JSONDecodeError:
            pass

        # 2. Regex ile tam [ ... ] bloğu ara
        match = re.search(r"\[.*\]", cleaned, re.DOTALL)
        if match:
            try:
                return self._build_findings(json.loads(match.group(0)))
            except json.JSONDecodeError:
                pass

        # 3. Kesintiye uğramış (truncated) JSON onarımı (son kapanan '}' karakterinden kesip ']' ekle)
        if "[" in cleaned:
            json_part = cleaned[cleaned.find("["):]
            last_brace = json_part.rfind("}")
            if last_brace != -1:
                repaired = json_part[:last_brace + 1] + "\n]"
                try:
                    return self._build_findings(json.loads(repaired))
                except json.JSONDecodeError:
                    pass

        return []

    def _build_findings(self, data) -> list:
        if not isinstance(data, list):
            return []

        findings = []
        for item in data:
            if not isinstance(item, dict):
                continue
            raw_sev  = str(item.get("severity", "LOW")).upper()
            severity = raw_sev if raw_sev in ("HIGH", "MEDIUM", "LOW") else "LOW"
            try:
                findings.append(AIFinding(
                    severity=severity,
                    category=str(item.get("category", "Code Quality")),
                    function_name=item.get("function_name"),
                    line_range=str(item["line_range"]) if item.get("line_range") else None,
                    message=str(item.get("message", "")),
                    suggestion=item.get("suggestion"),
                ))
            except Exception:
                continue

        return findings
