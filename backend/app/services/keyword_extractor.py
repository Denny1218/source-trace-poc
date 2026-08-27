import re
from pathlib import PurePosixPath

# C/C++ identifier, UPPER_SNAKE symbols, file names, Korean phrases
_IDENTIFIER_RE = re.compile(r"\b[A-Za-z_][A-Za-z0-9_]*\b")
_UPPER_SYMBOL_RE = re.compile(r"\b[A-Z][A-Z0-9_]{2,}\b")
_UPPER_SYMBOL_LOOSE_RE = re.compile(r"[A-Z][A-Z0-9_]{2,}")
_KOREAN_RE = re.compile(r"[가-힣]{2,}")
_FILE_IN_QUERY_RE = re.compile(
    r"\b[\w.-]+\.(?:c|h|cpp|hpp|py|js|ts|java|md|txt)\b", re.IGNORECASE
)

# Natural language noise — not used as standalone search keywords
_STOPWORDS = frozenset(
    {
        "함수",
        "변경",
        "이유",
        "왜",
        "추가",
        "수정",
        "처리",
        "코드",
        "파일",
        "함수가",
        "변경됐어",
        "변경되었",
        "변경되",
        "the",
        "and",
        "for",
        "why",
        "how",
        "what",
        "when",
        "changed",
        "change",
        "function",
        "if",
        "int",
        "return",
        "void",
        "type",
    }
)

_MIN_IDENTIFIER_LEN = 3


def _is_symbol(token: str) -> bool:
    return bool(_UPPER_SYMBOL_RE.fullmatch(token)) or (
        len(token) >= _MIN_IDENTIFIER_LEN and token[0].isupper()
    )


def _add_token(keywords: set[str], token: str) -> None:
    token = token.strip()
    if not token or len(token) < 2:
        return
    if token.lower() in _STOPWORDS:
        return
    if token.isalpha() and len(token) < _MIN_IDENTIFIER_LEN and not _is_symbol(token):
        return
    keywords.add(token)


def extract_keywords(
    query: str,
    file_path: str | None = None,
    selected_code: str | None = None,
) -> list[str]:
    """Rule-based keyword extraction. No LLM."""
    keywords: set[str] = set()

    for token in _IDENTIFIER_RE.findall(query):
        _add_token(keywords, token)
    for token in _UPPER_SYMBOL_RE.findall(query):
        _add_token(keywords, token)
    for token in _UPPER_SYMBOL_LOOSE_RE.findall(query):
        _add_token(keywords, token)
    for token in _KOREAN_RE.findall(query):
        _add_token(keywords, token)
    for token in _FILE_IN_QUERY_RE.findall(query):
        _add_token(keywords, token)

    if file_path:
        name = PurePosixPath(file_path.replace("\\", "/")).name
        stem = PurePosixPath(file_path.replace("\\", "/")).stem
        _add_token(keywords, name)
        _add_token(keywords, stem)

    if selected_code:
        for token in _IDENTIFIER_RE.findall(selected_code):
            _add_token(keywords, token)
        for token in _UPPER_SYMBOL_RE.findall(selected_code):
            _add_token(keywords, token)

    return sorted(keywords)


def symbol_keywords(keywords: list[str]) -> list[str]:
    return [k for k in keywords if _is_symbol(k) or _UPPER_SYMBOL_RE.fullmatch(k)]
