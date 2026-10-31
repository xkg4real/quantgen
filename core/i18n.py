"""Per-view translation and CLDR formatting. No process-global user language."""
from dataclasses import dataclass
from datetime import date, datetime
from functools import lru_cache
import re
from babel import Locale, localedata, UnknownLocaleError
from babel.dates import format_date, format_datetime
from babel.numbers import format_currency, format_decimal, format_percent

from .ui_messages import MESSAGES, LEGACY
from .ui_legacy_messages import static_text, KO_TO_EN


@dataclass(frozen=True)
class LocaleContext:
    requested: str = 'ko_KR'

    @property
    def locale(self):
        try:
            return Locale.parse(self.requested.replace('-', '_'))
        except (ValueError, TypeError, LookupError, UnknownLocaleError):
            return Locale.parse('en_US')

    @property
    def language(self):
        return self.locale.language if self.locale.language in MESSAGES else 'en'

    @property
    def is_fallback(self):
        return self.locale.language not in MESSAGES

    @property
    def rtl(self):
        return Locale.parse(self.language).character_order == 'right-to-left'

    def t(self, key, **values):
        text = MESSAGES[self.language].get(key, MESSAGES['en'].get(key))
        if text is None:
            raise KeyError('Unknown translation key: '+key)
        return text.format(**values)

    def text(self, value):
        text = str(value)
        translated=static_text(text,self.language)
        if translated!=text:return translated
        key = LEGACY.get(text)
        if key:return self.t(key)
        if re.fullmatch(r'\d{4}-\d{2}-\d{2}',text):
            try:return self.date(text)
            except ValueError:pass
        if len(text)>4000:return text
        for pattern,chunks in dynamic_patterns(self.language):
            match=pattern.fullmatch(text)
            if match:
                return ''.join(part+(match.group(i+1) if i<len(chunks)-1 else '') for i,part in enumerate(chunks))
        return text

    def number(self, value, digits=2):
        if value is None:
            return '—'
        return format_decimal(value, format='#,##0'+('.'+'0'*digits if digits else ''), locale=self.locale)

    def percent(self, value, digits=1):
        pattern=self.locale.percent_formats[None].pattern
        if digits:pattern=pattern.replace('0','0.'+'0'*digits)
        return format_percent(value, format=pattern, locale=self.locale)

    def money(self, value, currency):
        return format_currency(value, currency, locale=self.locale)

    def date(self, value):
        if not value:
            return '—'
        if isinstance(value, str):
            value = date.fromisoformat(value[:10])
        return format_date(value, format='medium', locale=self.locale)

    def timestamp(self, value):
        if isinstance(value, str):
            value = datetime.fromisoformat(value.replace('Z', '+00:00'))
        return format_datetime(value, format='medium', locale=self.locale)


@lru_cache(maxsize=1)
def locale_choices():
    """CLDR locale coverage is distinct from reviewed translation coverage."""
    result = []
    for identifier in localedata.locale_identifiers():
        loc = Locale.parse(identifier)
        if not loc.territory:
            continue
        result.append((identifier, f'{loc.get_display_name("en")} · {identifier}'))
    return tuple(sorted(result, key=lambda x: x[1]))


@lru_cache(maxsize=2)
def dynamic_patterns(language):
    from .ui_dynamic_messages import TEMPLATES
    result=[]
    for source in TEMPLATES:
        english=tuple(KO_TO_EN.get(part,part) for part in source)
        if english==source:continue
        original,target=(source,english) if language=='en' else (english,source)
        result.append((re.compile('(.*?)'.join(re.escape(part) for part in original),re.DOTALL),target))
    return tuple(result)


def numeric_presentation(text,ctx):
    """A display-only conversion of known formatted numbers, never input parsing."""
    match=re.fullmatch(r'([+-]?)([0-9][0-9,]*)(?:\.([0-9]+))?(%| bp)?',str(text))
    if not match:return str(text)
    sign,whole,fraction,unit=match.groups()
    if len(whole)>1 and whole.startswith('0') and fraction is None:return str(text)
    value=float(sign+whole.replace(',','')+('.'+fraction if fraction is not None else ''))
    digits=len(fraction) if fraction is not None else 0
    rendered=ctx.percent(value/100,digits) if unit=='%' else ctx.number(value,digits)+(unit or '')
    return ('+' if sign=='+' and value>=0 else '')+rendered
