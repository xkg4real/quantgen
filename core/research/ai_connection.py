"""Safe, actionable Claude diagnostics. Never echo provider bodies or secrets."""

# One response budget for every AI commentary request; the cut-off message quotes it.
OUTPUT_TOKEN_LIMIT = 1500
# QUANTGEN sends no tools and no stop_sequences, so only end_turn is a finished reply.
COMPLETE_STOP_REASONS = ('end_turn',)
_LIMIT = f'{OUTPUT_TOKEN_LIMIT:,}'

MESSAGES = {
    'NOT_CONFIGURED': (
        'Claude API key is not configured. Set ANTHROPIC_API_KEY locally, then fully restart QUANTGEN. Never share the key.',
        'Claude API 키가 설정되지 않았습니다. 로컬 ANTHROPIC_API_KEY를 설정한 뒤 QUANTGEN을 완전히 종료하고 다시 실행하세요. 키 값은 공유하지 마세요.'),
    'AUTHENTICATION': (
        'Claude authentication failed (HTTP 401). Check that ANTHROPIC_API_KEY is an active Anthropic Console API key for the intended workspace. A Claude app login or subscription is not an API key. After changing it, fully restart QUANTGEN; an existing process environment value takes precedence over .env. Never share the key.',
        'Claude 인증 실패(HTTP 401). ANTHROPIC_API_KEY가 해당 워크스페이스의 활성 Anthropic Console API 키인지 확인하세요. Claude 앱 로그인이나 구독은 API 키가 아닙니다. 변경 후 QUANTGEN을 완전히 종료하고 다시 실행하세요. 기존 프로세스 환경변수 값이 .env보다 우선합니다. 키 값은 공유하지 마세요.'),
    'PERMISSION': (
        'Claude access denied (HTTP 403). Check the API workspace and model permissions. This is distinct from an invalid-key response.',
        'Claude 접근 거부(HTTP 403). API 워크스페이스와 모델 접근 권한을 확인하세요. 잘못된 키 응답과는 구분됩니다.'),
    'MODEL_NOT_FOUND': (
        'Claude model or resource unavailable (HTTP 404). Check QUANTGEN_AI_MODEL against models available to your API workspace. Do not replace the key solely because of this response.',
        'Claude 모델 또는 리소스를 찾을 수 없습니다(HTTP 404). QUANTGEN_AI_MODEL이 API 워크스페이스에서 이용 가능한 모델인지 확인하세요. 이 응답만으로 키를 교체할 필요는 없습니다.'),
    'BILLING': (
        'Claude API billing or credit limit prevented the request. Check the Anthropic Console API balance and billing; Claude app subscription billing is separate.',
        'Claude API 결제 또는 크레딧 한도로 요청이 거부됐습니다. Anthropic Console의 API 잔액과 결제를 확인하세요. Claude 앱 구독 결제와는 별개입니다.'),
    'RATE_LIMIT': (
        'Claude API rate limit reached (HTTP 429). Wait before requesting again and check API usage limits. No automatic retry was made.',
        'Claude API 사용량 제한에 도달했습니다(HTTP 429). 잠시 후 다시 요청하고 API 사용량 한도를 확인하세요. 자동 재시도는 하지 않았습니다.'),
    'REQUEST_TOO_LARGE': (
        'Claude request is too large (HTTP 413). Select a smaller calculation report or shorten the question.',
        'Claude 요청이 너무 큽니다(HTTP 413). 더 작은 계산 보고서를 선택하거나 질문을 줄이세요.'),
    'INVALID_REQUEST': (
        'Claude rejected the request format (HTTP 400). Check the configured model and request size. This response alone does not prove the key is invalid.',
        'Claude 요청 형식이 거부됐습니다(HTTP 400). 설정된 모델과 요청 크기를 확인하세요. 이 응답만으로 키가 잘못됐다고 판단하지 않습니다.'),
    'SERVICE_UNAVAILABLE': (
        'Claude service is temporarily unavailable. Try again later. Local calculations and their original verdicts are unchanged.',
        'Claude 서비스를 일시적으로 이용할 수 없습니다. 나중에 다시 요청하세요. 로컬 계산 결과와 원래 판정은 유지됩니다.'),
    'TIMEOUT': (
        'Claude request timed out. Check the connection and try again later. No automatic retry was made; the request may have reached the provider.',
        'Claude 요청 시간이 초과됐습니다. 연결을 확인한 뒤 나중에 다시 요청하세요. 자동 재시도는 하지 않았으며 요청이 공급자에 도달했을 수 있습니다.'),
    'NETWORK': (
        'Claude API connection failed. Check network, proxy and TLS connectivity to api.anthropic.com. This is not proof that the key was rejected.',
        'Claude API 연결에 실패했습니다. api.anthropic.com에 대한 네트워크·프록시·TLS 연결을 확인하세요. 키가 거절됐다는 뜻은 아닙니다.'),
    'INVALID_RESPONSE': (
        'Claude returned an unreadable response or no text. No AI commentary was saved. Local calculations remain available.',
        'Claude 응답을 읽을 수 없거나 텍스트가 없습니다. AI 해설은 저장하지 않았으며 로컬 계산은 계속 사용할 수 있습니다.'),
    'DEPENDENCY': (
        'The requests package is not installed. Repair the QUANTGEN installation to enable optional AI commentary.',
        'requests 패키지가 설치되지 않았습니다. 선택 AI 해설을 사용하려면 QUANTGEN 설치를 복구하세요.'),
    'REQUEST_FAILED': (
        'Claude API request failed. Check the HTTP status and API service status. No AI commentary was saved.',
        'Claude API 요청이 실패했습니다. HTTP 상태와 API 서비스 상태를 확인하세요. AI 해설은 저장하지 않았습니다.'),
    'OUTPUT_LIMIT': (
        f"Claude reached QUANTGEN's output limit of {_LIMIT} tokens before finishing (stop reason: max_tokens). "
        "The limit can include the model's internal reasoning as well as the visible text, so a long report format "
        "or long reasoning can use it up. The unfinished text was not shown or saved, and no automatic retry was made. "
        "Local calculations and official verdicts are unchanged.",
        f'Claude가 글을 끝내기 전에 QUANTGEN의 출력 한도({_LIMIT}토큰)에 도달했습니다(중단 사유: max_tokens). '
        '이 한도에는 화면에 보이는 글뿐 아니라 모델의 내부 추론이 포함될 수 있으므로, 보고서 형식이 길거나 추론이 길어지면 '
        '한도를 다 쓸 수 있습니다. 끝나지 않은 글은 표시하거나 저장하지 않았고 자동 재시도도 하지 않았습니다. '
        '로컬 계산과 공식 판정은 그대로입니다.'),
    'REFUSED': (
        'Claude declined to write this commentary (stop reason: refusal). Any partial text was not shown or saved, '
        'and no automatic retry was made. Local calculations and official verdicts are unchanged.',
        'Claude가 이 해설 작성을 거절했습니다(중단 사유: refusal). 일부 작성된 글이 있어도 표시하거나 저장하지 않았고 '
        '자동 재시도도 하지 않았습니다. 로컬 계산과 공식 판정은 그대로입니다.'),
    'INCOMPLETE_RESPONSE': (
        "Claude's reply did not end normally (its stop reason was not end_turn), so it was treated as incomplete. "
        'The text was not shown or saved, and no automatic retry was made. '
        'Local calculations and official verdicts are unchanged.',
        'Claude 응답이 정상적으로 끝나지 않아(중단 사유가 end_turn이 아님) 완성되지 않은 응답으로 처리했습니다. '
        '글은 표시하거나 저장하지 않았고 자동 재시도도 하지 않았습니다. 로컬 계산과 공식 판정은 그대로입니다.'),
}


def error_message(code: str, language: str = 'en', http_status: int | None = None) -> str:
    text = MESSAGES.get(code, MESSAGES['REQUEST_FAILED'])[language == 'ko']
    if type(http_status) is int and 100 <= http_status <= 599 and f'HTTP {http_status}' not in text:
        text += f' (HTTP {http_status})'
    return text


def response_error(status: int, body: object) -> str:
    # Provider text is inspected only for this known billing condition, never displayed.
    if status == 400 and isinstance(body, dict):
        error = body.get('error')
        if isinstance(error, dict):
            message = error.get('message')
            if isinstance(message, str) and any(term in message.lower() for term in
                    ('credit balance is too low', 'insufficient credits')):
                return 'BILLING'
    if 500 <= status <= 599:
        return 'SERVICE_UNAVAILABLE'
    return {400: 'INVALID_REQUEST', 401: 'AUTHENTICATION', 402: 'BILLING',
            403: 'PERMISSION', 404: 'MODEL_NOT_FOUND', 413: 'REQUEST_TOO_LARGE',
            429: 'RATE_LIMIT'}.get(status, 'REQUEST_FAILED')


def transport_error(error: Exception) -> str:
    try:
        from requests.exceptions import Timeout
        if isinstance(error, Timeout):
            return 'TIMEOUT'
    except ImportError:
        pass
    return 'NETWORK'


def reply_result(body: object) -> tuple[str, str, str]:
    """Classify an HTTP 200 Messages body as (error_code or '', text, stop_reason).

    The order is fixed: a malformed body first, then the stop reason, then the
    text. A reply that did not finish (max_tokens, refusal, pause_turn, tool_use,
    model_context_window_exceeded, stop_sequence or any other value) never
    returns its partial text. stop_details is provider text and is never read.
    """
    if not isinstance(body, dict):
        return 'INVALID_RESPONSE', '', ''
    blocks = body.get('content')
    if not isinstance(blocks, list):
        return 'INVALID_RESPONSE', '', ''
    texts = [b for b in blocks if isinstance(b, dict) and b.get('type') == 'text']
    if any(not isinstance(b.get('text'), str) for b in texts):
        return 'INVALID_RESPONSE', '', ''
    stop = body.get('stop_reason')
    if not isinstance(stop, str):
        return 'INVALID_RESPONSE', '', ''
    if stop == 'refusal':
        return 'REFUSED', '', stop
    if stop == 'max_tokens':
        return 'OUTPUT_LIMIT', '', stop
    if stop not in COMPLETE_STOP_REASONS:
        return 'INCOMPLETE_RESPONSE', '', stop
    text = '\n\n'.join(b['text'] for b in texts).strip()
    if not text:
        return 'INVALID_RESPONSE', '', stop
    return '', text, stop
