"""Local reading chrome; glossary definitions remain owned by core.education."""

# P0 catalog seam. These labels are rendered explicitly, without replacing any
# existing translations or changing source text used by reports.
PAIRS = ''

LABELS = {
    'title': ('알아보기', 'Learn terms'),
    'search': ('기존 용어 검색', 'Search existing terms'),
    'close': ('닫기 · Esc', 'Close · Esc'),
    'current': ('현재 화면의 표시값', 'Values displayed on this screen'),
    'empty': ('기존 용어를 검색하세요. 설명은 로컬 용어집에서 표시합니다.',
              'Search an existing term. Explanations come from the local glossary.'),
    'missing': ('용어집에 없는 말입니다. 검색어를 바꿔 보세요.',
                'No matching glossary term. Try a different search.'),
    'details': ('상세 정보', 'Details'),
    'learn': ('알아보기 · F1', 'Learn terms · F1'),
    'no_room': ('중요 안내를 가리지 않고 설명을 표시할 공간이 부족합니다. 페이지를 스크롤하거나 창을 넓힌 뒤 F1을 누르세요.',
                'There is not enough room to show help without covering important notices. Scroll the page or widen the window, then press F1.'),
}


def text(key, ctx):
    return LABELS[key][0 if getattr(ctx, 'language', ctx) == 'ko' else 1]
