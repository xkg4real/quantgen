"""A/F1 Home: explicit daily observations and session research results; no ledger scans."""
from __future__ import annotations

from pathlib import Path
from typing import Callable

import flet as ft

from core.theme import active
from tools.status.snapshot import verify
from core.app_paths import application_root
from core.research.runs import session_for, export_bytes
from core.research.markets import load_markets, SPECS
from core.research.export import bundle_bytes, save_desktop_export

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


class ResearchHome(ft.Column):
    """Auto-load once on mount; returning Home reuses the session's observations."""
    def __init__(self, page, navigate):
        super().__init__(spacing=20, scroll=ft.ScrollMode.AUTO, expand=True)
        self.host_page = page
        self.navigate = navigate
        self.research = session_for(page)
        self.selected = None
        self.mounted = False
        self.indicator_guide=None
        self.guide_host=ft.Container(visible=False)
        self.render()

    def did_mount(self):
        self.mounted = True
        if not self.research.market_attempted:
            self.refresh_markets()

    def will_unmount(self):
        self.mounted = False

    def refresh_markets(self, e=None):
        if not self.research.start_market_refresh():
            return
        self.render()
        if self.mounted: self.update()
        def worker():
            try:
                rows = load_markets()
            except Exception:
                rows = []
            finally:
                self.research.finish_market_refresh(rows)
            if self.mounted:
                self.render()
                self.update()
        self.host_page.run_thread(worker)

    def choose(self, e):
        self.selected = e.control.value
        self.render()
        if self.mounted: self.update()

    async def download(self, run, *, bundle=False):
        try:
            extension='zip' if bundle else 'json'
            data=bundle_bytes(run,locale=getattr(self.host_page,'qg_locale',None)) if bundle else export_bytes(run)
            filename=await ft.FilePicker().save_file(file_name=f"QUANTGEN-{run['run_id']}.{extension}",
                file_type=ft.FilePickerFileType.CUSTOM, allowed_extensions=[extension],
                src_bytes=data)
            # Flet web/mobile writes src_bytes; desktop only selects a path.
            if filename and not self.host_page.web and not self.host_page.platform.is_mobile():
                import asyncio
                await asyncio.to_thread(save_desktop_export,filename,data,extension=extension)
        except Exception:
            self.host_page.show_dialog(ft.AlertDialog(title=_text('내보내기 실패'),
                content=_text('파일 저장 서비스를 사용할 수 없습니다. 앱 연결을 확인해 주세요.')))

    def guide(self, title, route, steps):
        def open_view(e):
            self.host_page.pop_dialog()
            self.navigate(route)
        self.host_page.show_dialog(ft.AlertDialog(title=_text(title,18,bold=True),
            content=_text(steps,14),actions=[ft.TextButton('분석 화면 열기',on_click=open_view)]))

    def render(self):
        from core.i18n import LocaleContext
        ctx=getattr(self.host_page,'qg_locale',LocaleContext())
        if self.indicator_guide is not None:self.indicator_guide.render_locale(ctx)
        pal = active(); navigate = self.navigate
        runs = self.research.runs(); markets = self.research.markets()
        complete = [r for r in runs if r['execution_status'] == 'COMPLETED']
        selected = next((r for r in complete if r['run_id'] == self.selected), complete[0] if complete else None)
        connected = sum(r['status'] == 'OBSERVED' for r in markets)
        summary = [_panel(label, [_text(value, 30, bold=True), _text(detail, 12, muted=True)], col={'xs':6,'md':3})
                   for label, value, detail in [
                       ('완료한 분석', str(len(complete)), '이번 앱 세션 · 투자 판정과 별개'),
                       ('진행 중', str(sum(r['execution_status'] == 'RUNNING' for r in runs)), '이번 앱 세션'),
                       ('확인할 실행', str(sum(r['execution_status'] == 'FAILED' for r in runs)), '실패한 실행 · 재시도 필요'),
                       ('시장 관측', f'{connected} / 6' if self.research.market_attempted else '—', '7일 이내 일별 관측 · 실시간 아님')]]
        recent_rows = []
        for r in runs[:8]:
            p = r['parameters']; data = r['data'] or {}
            recent_rows.append(ft.Container(ft.Column([
                ft.Row([_text(p.get('symbol', '—'), 15, bold=True), _text(r['execution_status'], 11, muted=True)], wrap=True),
                _text(f"{p.get('model', '—')} · {r['created_at'][:19]} UTC · 판정 {r['verdict']}", 11, muted=True),
                _text(f"{data.get('source', '데이터 대기')} · 관측일 {data.get('last_observation', '—')}"
                      + (' · 합성 데이터' if data.get('synthetic') else ''), 11, muted=True),
            ], spacing=5), padding=12, bgcolor=pal.surface_2, border_radius=10))
        if not recent_rows:
            recent_rows = [_empty('첫 연구를 시작하세요', 'Quant Lab에서 완료한 분석이 이 홈에 자동으로 연결됩니다.',
                                  _link('Quant Lab 열기', 'quant', navigate, primary=True))]
        recent = _panel('최근 연구', recent_rows, subtitle='이번 앱 세션의 실행 · 과거 전체 시행 수가 아닙니다', col={'xs':12,'lg':8})
        actions = _panel('다음 할 일', [
            _text('01  분석하고 근거를 확인하세요', 14, bold=True),
            _link('Quant Lab', 'quant', navigate, primary=True), _link('Strategy Lab', 'lab', navigate),
            ft.Divider(color=pal.border), _text('02  연결과 관측일을 확인하세요', 14, bold=True),
            _text('공급자 조회 실패를 합성 가격으로 채우지 않습니다.', 12, muted=True),
            _link('연결 설정', 'settings', navigate),
        ], col={'xs':12,'lg':4})
        tiles = []
        by_symbol = {r['symbol']: r for r in markets}
        for label, symbol, provider, unit, route in SPECS:
            r = by_symbol.get(symbol, {})
            value = r.get('value'); change = r.get('change')
            status = {'OBSERVED':'일별 관측', 'STALE':'오래된 관측 · 확인 필요', 'UNAVAILABLE':'조회 실패'}.get(r.get('status'), '미연결')
            detail = f"{r.get('provider', provider.upper())} · {r.get('observation_date') or '관측일 없음'}"
            tiles.append(ft.Container(ft.Column([
                _text(label, 13, bold=True), _text(symbol, 11, muted=True),
                ft.Row([_text(f'{value:,.2f}' if value is not None else '—', 24, bold=True), _text(unit, 10, muted=True)], wrap=True),
                _text(f"{change:+.2f} {'bp' if unit == '%' else '%'} · 직전 관측 대비" if change is not None else '변화 확인 불가', 11, muted=True),
                _text(status, 11, muted=True), _text(detail, 10, muted=True),
                ft.TextButton('분석 화면 열기', on_click=lambda e, n=route: navigate(n), data={'route':route}),
            ], spacing=6), padding=16, bgcolor=pal.surface_2, border_radius=12, col={'xs':6,'md':4,'xl':2}))
        dist_controls = []; evidence = []
        if selected:
            p = selected['parameters']; d = selected['data']; m = selected['metrics']
            dist_controls.append(ft.Dropdown(label='분석 결과 선택', value=selected['run_id'], on_select=self.choose,
                options=[ft.dropdown.Option(r['run_id'], f"{r['parameters'].get('symbol')} · {r['created_at'][:19]}") for r in complete]))
            dist_controls.append(ft.ResponsiveRow([
                _panel(label, [_text(f'{m[key]:,.2f}', 26, bold=True)], col=4)
                for label,key in [('P5','p05'),('P50','p50'),('P95','p95')]], spacing=10))
            dist_controls += [_text(f"현재 입력 가격 {m['spot']:,.2f} · 만기 손실 확률 {m['prob_loss']:.1%}", 13),
                              _text('합성 입력으로 계산한 분포입니다.' if d['synthetic'] else '불확실성을 표현한 가격 시뮬레이션입니다.', 12, muted=True)]
            async def download_clicked(e, r=selected): await self.download(r)
            async def bundle_clicked(e, r=selected): await self.download(r,bundle=True)
            dist_controls.append(ft.Button('ResearchRun JSON 저장', icon=ft.Icons.DOWNLOAD_OUTLINED, on_click=download_clicked))
            dist_controls.append(ft.TextButton('보고서 + JSON 묶음 저장',on_click=bundle_clicked))
            evidence = [_text(f"{p['model']} · {d['symbol']}", 15, bold=True),
                        _text(f"{d['source']} · {d['first_observation']} ~ {d['last_observation']}", 12, muted=True),
                        _text(f"{p['horizon_days']}세션 · {p['n_paths']:,}경로 · seed {p['seed']}", 12),
                        _text(f"조정 방식 {d['adjustment']} · 입력 SHA {d['fingerprint_sha256'][:12]}", 11, muted=True),
                        _text('비용 NOT_APPLIED · 전략 수익률 백테스트 아님', 12),
                        _text('검증 판정 NOT_RUN · 데이터 빈티지/권리 미검증', 12),
                        _text('재현성 PARTIAL · JSON에는 확인된 근거와 누락 상태를 함께 기록합니다.', 12, muted=True)]
        else:
            dist_controls = [_empty('선택할 분석 결과가 없습니다', 'Quant Lab에서 분석을 실행하면 P5 · P50 · P95가 표시됩니다.',
                                    _link('분포 분석 시작', 'quant', navigate))]
            evidence = [_text('분석 완료 후 데이터·가정·시드가 연결됩니다.', 13, muted=True)]
        dist_controls.append(_text('P5–P95: 시뮬레이션 분포의 중앙 90% 구간. 수익 보장이나 95% 신뢰구간이 아닙니다.', 12, muted=True))
        refresh_button = ft.Button('조회 중…' if self.research.market_loading else '시장지표 새로고침',
                                   icon=ft.Icons.REFRESH, on_click=self.refresh_markets, disabled=self.research.market_loading)
        self.controls = [
            ft.Column([_text('YOUR RESEARCH, IN PERSPECTIVE', 11, muted=True), _text('Research Home', 30, bold=True),
                       _text('관측된 시장과 내가 실행한 연구를 한눈에 확인하세요.', 14, muted=True)], spacing=7),
            ft.ResponsiveRow(summary, spacing=16, run_spacing=16),
            _panel(ctx.t('guide'),[
                _text(ctx.t('guide_intro'),14,muted=True),
                ft.Button(ctx.t('start_guide'),on_click=self.toggle_indicator_guide),self.guide_host]),
            ft.ResponsiveRow([recent, actions], spacing=20, run_spacing=20),
            _panel('주요 시장지표', [refresh_button, ft.TextButton(ctx.t('data_rights'),on_click=lambda e:navigate('system')),ft.ResponsiveRow(tiles, spacing=12, run_spacing=12)],
                   subtitle='일별 관측값 · 공급자 캐시가 사용될 수 있습니다. 관측일을 확인하세요. 공개 재배포 권리는 별도입니다.'),
            ft.ResponsiveRow([
                _panel('가능성을 하나의 숫자로 좁히지 마세요', dist_controls, subtitle='DISTRIBUTION & EVIDENCE', col={'xs':12,'lg':8}),
                _panel('가정과 근거', evidence, col={'xs':12,'lg':4})], spacing=20, run_spacing=20),
            _panel('연구 도구 바로가기', [ft.Row([_link('시장 읽기', 'macro', navigate),
                    _link('포트폴리오 · 위험', 'portfolio', navigate), _link('연구 라이브러리', 'library', navigate),
                    _link('시스템 상태', 'system', navigate)], wrap=True)]),
            _panel('연습용 연구 시작', [ft.Row([
                ft.TextButton('SPY 가격 분포',on_click=lambda e:self.guide('SPY 가격 분포','quant',
                    'Data source를 synthetic, Symbol을 SPY, Model을 gbm으로 선택하세요. Drift는 zero, Paths 500, Horizon 21로 실행한 뒤 Home에서 결과를 확인하세요. 실제 SPY 관측값이 아닌 연습용 합성 데이터입니다.')),
                ft.TextButton('KRX ETF 모멘텀',on_click=lambda e:self.guide('KRX ETF 모멘텀','lab',
                    'Strategy Lab에서 합성(synthetic) 데이터 소스와 KRX ETF 자산을 선택하고 기존 모멘텀 전략을 실행하세요. 결과는 연습용이며 이 Home의 Quant Lab 기록과는 별개입니다.')),
                ft.TextButton('USD 금리 곡선',on_click=lambda e:self.guide('USD 금리 곡선','rates',
                    'Rates에서 데이터 소스를 synthetic으로 선택해 USD 곡선을 조회하고 기존 충격/민감도 결과를 확인하세요. 합성 곡선은 현재 시장 금리가 아닙니다.')),
            ],wrap=True)],subtitle='API 키 없이 흐름 익히기 · 합성 데이터 표시를 확인하세요'),
            _text('QUANTGEN / Personal research workspace · 세션 종료 전 필요한 결과를 JSON으로 저장하세요.', 11, muted=True),
        ]

    def toggle_indicator_guide(self,e=None):
        if self.indicator_guide is None:
            from .indicator_guide import IndicatorGuide
            self.indicator_guide=IndicatorGuide(self.host_page)
            self.guide_host.content=self.indicator_guide
        self.guide_host.visible=not self.guide_host.visible
        if self.mounted:self.update()


def build_home_page(page: ft.Page, *, navigate: Callable) -> ft.Control:
    return ResearchHome(page, navigate)


def build_library_page(page: ft.Page, *, navigate: Callable) -> ft.Control:
    runs=session_for(page).runs()
    return ft.Column([
        _text('Research Library', 30, bold=True),
        _text('가정과 한계를 확인하고, 기존 연구 화면으로 이어가세요.', 14, muted=True),
        ft.ResponsiveRow([
            _panel('매크로 연구', [_text('Macro의 Research register와 연구 카드에서 근거를 확인하세요.', 14),
                                 _link('Macro 열기', 'macro', navigate)], col={'xs':12,'md':6}),
            _panel('모델과 분포', [_text('Quant Lab의 모델 설명, 가정과 분석 결과를 확인하세요.', 14),
                                  _link('Quant Lab 열기', 'quant', navigate)], col={'xs':12,'md':6}),
        ], spacing=20, run_spacing=20),
        _panel('이번 세션의 연구 기록', [
            *[_text(f"{r['parameters'].get('symbol', '—')} · {r['execution_status']} · 판정 {r['verdict']}",13) for r in runs[:20]],
            _text(f'{len(runs)}개 실행 기록 · 과거 원장이나 동결 연구를 조회하지 않습니다.',12,muted=True),
            _link('Home에서 보고서 저장', 'home', navigate)]),
    ], spacing=20, scroll=ft.ScrollMode.AUTO, expand=True)


def build_system_page(page: ft.Page, *, navigate: Callable) -> ft.Control:
    from .localization import LanguageSettings
    from .data_rights import DataRightsPanel
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
        _panel('언어·지역',[LanguageSettings(page)]),
        _panel('시장 데이터 이용 조건',[DataRightsPanel(page)]),
        _panel('기록된 프로젝트 상태', rows),
        _panel('설정과 규칙', [ft.Row([_link('데이터 연결 설정', 'settings', navigate),
                                       _link('모의 실행 규칙', 'rules', navigate)], wrap=True)]),
    ], spacing=20, scroll=ft.ScrollMode.AUTO, expand=True)
