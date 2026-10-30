"""Plain provider diagnostics and explicit UI result export, without secrets."""
import re


def safe_detail(value):
    text = str(value)
    text = re.sub(r'https?://[^\s<>]+', '[provider URL redacted]', text)
    text = re.sub(r'(?i)\b(api[_-]?key|access[_-]?token|secret|authorization|bearer)\s*[:=]\s*[^\s,;]+',
                  r'\1=[redacted]', text)
    return text[:1500]
