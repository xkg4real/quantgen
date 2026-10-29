"""A/F1 read-only home. No provider calls, simulations or research-store scans."""
from __future__ import annotations

from pathlib import Path
from typing import Callable

import flet as ft

from core.theme import active
from tools.status.snapshot import verify
from core.app_paths import application_root

ROOT = application_root()


def recorded_status() -> tuple[dict | None, str]:
    """Read only the explicit PR-A evidence inputs; refuse stale snapshots."""
    try:
        return verify(ROOT), ''
    except (OSError, ValueError, KeyError, TypeError):
        return None, '기록된 상태를 확인할 수 없습니다. 상태 자료를 점검해 주세요.'


def _text(value, size=14, *, muted=False, bold=False):
    pal = active()
    return ft.Text(value, size=size, color=pal.muted if muted else pal.text,
                   weight=ft.FontWeight.W_600 if bold else ft.FontWeight.W_400)


def _panel(title, controls, *, subtitle='', col=12):
    pal = active()
    return ft.Container(ft.Column([
        _text(title, 17, bold=True), *([_text(subtitle, 12, muted=True)] if subtitle else []),
        ft.Container(height=4), *controls,
    ], spacing=12, horizontal_alignment=ft.CrossAxisAlignment.STRETCH), padding=22, bgcolor=pal.surface,
        border=ft.Border.all(1, pal.border), border_radius=16, col=col)


def _link(label: str, target: str, navigate: Callable, *, primary=False):
    pal = active()
    return ft.Button(label, icon=ft.Icons.ARROW_FORWARD_ROUNDED,
                     on_click=lambda e: navigate(target), data={'route': target},
                     style=ft.ButtonStyle(bgcolor=pal.accent if primary else pal.accent_soft,
                                          color=pal.on_accent if primary else pal.accent,
                                          shape=ft.RoundedRectangleBorder(radius=10)), height=44)


def _empty(title, detail, action, icon=ft.Icons.AUTO_GRAPH_ROUNDED):
    pal = active()
    return ft.Container(ft.Column([
        ft.Icon(icon, size=30, color=pal.accent), _text(title, 16, bold=True),
        _text(detail, 13, muted=True), ft.Row([action], wrap=True),
    ], spacing=12, horizontal_alignment=ft.CrossAxisAlignment.STRETCH), padding=20, bgcolor=pal.surface_2, border_radius=12)


def build_home_page(page: ft.Page, *, navigate: Callable) -> ft.Control:
    pal = active()
    summary = []
    for label, detail in [('최근 연구', '연결된 실행 기록 기준'), ('미완료 연구', '진행 기록 연결 대기'),
                          ('데이터 확인', '데이터 상태 연결 대기'), ('결정 대기', '승인 기록 연결 대기')]:
        summary.append(_panel(label, [_text('—', 30, bold=True), _text(detail, 12, muted=True)],
                              col={'xs': 6, 'md': 3}))
    recent = _panel('최근 연구', [
        _empty('연구를 시작할 준비가 되셨나요?',
               '아직 연결된 연구 기록이 없습니다. 기존 도구에서 분석을 시작하고 결과를 확인하세요.',
               _link('Quant Lab 열기', 'quant', navigate, primary=True)),
        _text('실행 상태 · 연구 판정 · 데이터 시각은 각각 구분해 표시합니다.', 12, muted=True),
    ], subtitle='연구의 흐름을 이어가세요', col={'xs': 12, 'lg': 8})
    actions = _panel('다음 할 일', [
        _text('01  연구 질문을 정하세요', 14, bold=True),
        _text('가격 분포와 위험은 Quant Lab, 전략 검증은 Strategy Lab에서 시작하세요.', 13, muted=True),
        _link('Strategy Lab', 'lab', navigate),
        ft.Divider(color=pal.border),
        _text('02  데이터 연결을 확인하세요', 14, bold=True),
        _text('공급자별 연결 상태와 필요한 설정을 확인할 수 있습니다.', 13, muted=True),
        _link('연결 설정', 'settings', navigate),
    ], col={'xs': 12, 'lg': 4})
    markets = []
    for label, symbol, unit, target in [('S&P 500', 'SPX · 지수', 'pt', 'macro'),
                                      ('KOSPI', 'KOSPI · 지수', 'pt', 'krx'),
                                      ('USD / KRW', '원·달러 환율', 'KRW/USD', 'fx'),
                                      ('미국 10년 금리', 'Treasury 10Y', '% · 변화 bp', 'rates'),
                                      ('VIX', '변동성 지수', 'pt', 'macro'),
                                      ('Bitcoin', 'BTC / USD', 'USD', 'crypto')]:
        markets.append(ft.Container(ft.Column([
            _text(label, 13, bold=True), _text(symbol, 11, muted=True),
            ft.Row([_text('—', 26, bold=True), _text(unit, 11, muted=True)], spacing=8),
            _text('미연결 · 출처/기준 시각 없음', 11, muted=True),
            ft.TextButton('분석 화면 열기', on_click=lambda e, n=target: navigate(n),
                          data={'route': target}, style=ft.ButtonStyle(color=pal.accent)),
        ], spacing=6), padding=16, bgcolor=pal.surface_2, border_radius=12,
            col={'xs': 6, 'md': 4, 'xl': 2}))
    distribution = _panel('가능성을 하나의 숫자로 좁히지 마세요', [
        _empty('선택한 연구의 분포', '분석 결과를 선택하면 P5 · P50 · P95와 가정을 함께 확인합니다.',
               _link('분포 분석 시작', 'quant', navigate), ft.Icons.SSID_CHART_ROUNDED),
        _text('P5–P95: 시뮬레이션 분포의 중앙 90% 구간. 수익 보장이나 95% 신뢰구간이 아닙니다.', 12, muted=True),
    ], subtitle='DISTRIBUTION & EVIDENCE', col={'xs': 12, 'lg': 8})
    assumptions = _panel('가정과 근거', [
        _text('아직 선택한 결과가 없습니다.', 14),
        *[ft.Row([_text(k, 12, muted=True), _text('—', 13)], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
          for k in ('모델 · 자산', '기간 · 데이터 시각', '시드 · 경로 수', '비용 가정', '검증 판정')],
        _link('Research Library', 'library', navigate),
    ], col={'xs': 12, 'lg': 4})
    return ft.Column([
        ft.Row([ft.Column([_text('YOUR RESEARCH, IN PERSPECTIVE', 11, muted=True),
                           _text('Research Home', 30, bold=True),
                           _text('연구 진행 상황과 다음 할 일을 한눈에 확인하세요.', 14, muted=True)], spacing=7)], wrap=True),
        ft.Container(height=2),
        ft.ResponsiveRow(summary, spacing=16, run_spacing=16),
        ft.ResponsiveRow([recent, actions], spacing=20, run_spacing=20),
        _panel('주요 시장지표', [ft.ResponsiveRow(markets, spacing=12, run_spacing=12)],
               subtitle='이 홈에는 시세가 아직 연결되지 않았습니다. 각 분석 화면에서 출처와 기준 시각을 확인하세요.'),
        ft.ResponsiveRow([distribution, assumptions], spacing=20, run_spacing=20),
        _panel('연구 도구 바로가기', [ft.Row([
            _link('시장 읽기', 'macro', navigate), _link('포트폴리오 · 위험', 'portfolio', navigate),
            _link('연구 라이브러리', 'library', navigate), _link('시스템 상태', 'system', navigate),
        ], wrap=True, spacing=10, run_spacing=10)]),
        _text('QUANTGEN  /  Personal research workspace', 11, muted=True),
    ], spacing=20, scroll=ft.ScrollMode.AUTO, expand=True)


def build_library_page(page: ft.Page, *, navigate: Callable) -> ft.Control:
    return ft.Column([
        _text('Research Library', 30, bold=True),
        _text('가정과 한계를 확인하고, 기존 연구 화면으로 이어가세요.', 14, muted=True),
        ft.ResponsiveRow([
            _panel('매크로 연구', [_text('Macro의 Research register와 연구 카드에서 근거를 확인하세요.', 14),
                                 _link('Macro 열기', 'macro', navigate)], col={'xs':12,'md':6}),
            _panel('모델과 분포', [_text('Quant Lab의 모델 설명, 가정과 분석 결과를 확인하세요.', 14),
                                  _link('Quant Lab 열기', 'quant', navigate)], col={'xs':12,'md':6}),
        ], spacing=20, run_spacing=20),
        _panel('최근 보고서', [_text('아직 연결된 보고서가 없습니다.', 14),
                              _text('기존 분석 화면에서 만든 보고서를 확인하세요.', 13, muted=True)]),
    ], spacing=20, scroll=ft.ScrollMode.AUTO, expand=True)


def build_system_page(page: ft.Page, *, navigate: Callable) -> ft.Control:
    status, error = recorded_status()
    rows = []
    if error:
        rows = [_text('확인 필요', 18, bold=True), _text(error)]
    else:
        q = status['code_test']; cal = status['data_readiness']['calendar']
        rows = [
            _text(f"기록된 코드 검사  {q['counts']['PASS']} PASS / {q['counts']['FAIL']} FAIL / {q['counts']['NOT_RUN']} NOT_RUN", 15, bold=True),
            _text('새로 실행한 검사 결과가 아닙니다. 원본에는 실행 시각과 커밋이 없습니다.', 13, muted=True),
            _text(f"달력  {cal['files']}개 서명 메타데이터 · 세트 {cal['version']}", 14),
            _text(f"서명 시각 {cal['signed_at']} · 파일별 서명 검증은 별도입니다.", 12, muted=True),
            _text('데이터  NOT_VERIFIED  ·  공식 게이트  NOT_FROZEN (문서 기록)', 14),
            _text('동결 연구  NOT_INSPECTED  ·  공개 배포  NOT_APPROVED', 14),
            _text('코드 검사, 데이터 준비, 투자 판정과 배포 승인은 서로 다른 상태입니다.', 13, muted=True),
            _text('출처: qa/acceptance_results.json · calendar MANIFEST · README', 12, muted=True),
            _text('상태 자료 생성 시각: ' + status['generated_at'], 12, muted=True),
        ]
    return ft.Column([
        _text('System', 30, bold=True), _text('기록된 근거와 현재 연결을 구분해 확인하세요.', 14, muted=True),
        _panel('기록된 프로젝트 상태', rows),
        _panel('설정과 규칙', [ft.Row([_link('데이터 연결 설정', 'settings', navigate),
                                       _link('모의 실행 규칙', 'rules', navigate)], wrap=True)]),
    ], spacing=20, scroll=ft.ScrollMode.AUTO, expand=True)
