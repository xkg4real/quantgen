"""Plain provider diagnostics and explicit UI result export, without secrets."""
import re


def safe_detail(value, *, limit=1500):
    text = str(value)
    text = re.sub(r'https?://[^\s<>]+', '[provider URL redacted]', text)
    text = re.sub(r'(?i)\bBearer\s+[^\s,;]+', 'Bearer [redacted]', text)
    text = re.sub(r'(?i)\b(api[_-]?key|access[_-]?token|secret|authorization|bearer)\s*[:=]\s*[^\s,;]+',
                  r'\1=[redacted]', text)
    return text if limit is None else text[:limit]
