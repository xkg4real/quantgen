"""Internal Android preview. The optional simulation uses only the supplied educational example."""
from __future__ import annotations

import flet as ft

from core.theme import RADII, palette_for


def main(page: ft.Page) -> None:
    palette = palette_for("light")
    page.title = "QUANTGEN"
    page.padding = 0
    page.bgcolor = palette.bg
    page.fonts = {"QG Interface": "fonts/qg-interface.otf"}
    page.theme = ft.Theme(font_family="QG Interface", color_scheme_seed=palette.accent)
    page.theme_mode = ft.ThemeMode.LIGHT

    def text(value, size=14, *, muted=False, bold=False):
        return ft.Text(value, size=size, color=palette.muted if muted else palette.text,
                       weight=ft.FontWeight.W_600 if bold else ft.FontWeight.W_400)

    def panel(title, status, detail):
        return ft.Container(
            content=ft.Column([
                ft.Row([text(title, 16, bold=True)], wrap=True),
                ft.Container(content=text(status, 12, muted=True),
                             bgcolor=palette.surface_2, padding=8, border_radius=RADII["sm"]),
                text(detail, muted=True),
            ], spacing=12),
            padding=20, bgcolor=palette.surface,
            border=ft.Border.all(1, palette.border), border_radius=RADII["lg"],
        )

    demo_result = text("", muted=True)
    demo_result.visible = False

    def calculate_example(event):
        from datetime import date, timedelta

        try:
            from core.quant.montecarlo import run_monte_carlo
            from core.quant.supplied_history import SuppliedHistory
        except ImportError:
            demo_result.value = "이 기기에서 계산 모듈을 열 수 없어요."
        else:
            # Fixed synthetic closes are individual sessions with no exchange or calendar attached.
            closes = (100, 99.5, 101, 100.25, 101.5, 101.75, 100.5, 102, 101.25, 102.5,
                      103, 101.75, 103.5, 102.25, 103.25, 102.75, 104, 103.5, 105, 103.75,
                      105.25, 104.5, 105.75, 104.25, 105.5, 105, 106, 104.75, 106.25, 105.25)
            first = date(2024, 4, 1)
            days = (first + timedelta(days=offset) for offset in range(40))
            dates = tuple(day.isoformat() for day in days if day.weekday() < 5)
            history = SuppliedHistory("QG_SYNTHETIC", "SYNTHETIC", dates, closes)
            result = run_monte_carlo(history, model="gbm", drift="zero", seed=7, n_paths=256,
                                     horizon_days=5, target=106.0, var_level=0.95, n_sample_paths=4)
            demo_result.value = (f"5일 뒤 중앙값 {result.median_terminal:.2f} · "
                                 f"가운데 90% 범위 {result.p05:.2f}~{result.p95:.2f}")
        demo_result.visible = True
        page.update()

    demo_panel = panel("Quant Lab · Monte Carlo", "합성 가격 예시",
                       "예시 종가 105.25에서 출발해 5거래일 뒤 가격을 256번 모의 계산해요.")
    demo_panel.content.controls.extend([
        ft.FilledButton("예시 계산하기", on_click=calculate_example), demo_result,
    ])

    page.add(ft.Container(
        content=ft.Column([
            text("QUANTGEN", 26, bold=True),
            text("Android 내부 미리보기", 16),
            text("휴대폰 화면 배치를 확인하고 합성 가격으로 모의 계산을 해볼 수 있어요.",
                 muted=True),
            panel("화면 확인", "이 미리보기에서 확인 가능",
                  "휴대폰의 화면 배치와 스크롤을 확인할 수 있어요. 실제 기기 설치·실행 검증은 별도로 필요해요."),
            panel("시장 데이터와 차트", "미제공 · 실제 데이터 미연결",
                  "이 화면은 시세를 조회하지 않으며, 예시 값을 실제 시장 데이터로 표시하지 않아요."),
            demo_panel,
            panel("로그인", "미제공 · 계정 연결 없음",
                  "이 미리보기에서는 로그인하거나 저장된 인증정보를 읽지 않아요."),
            text("내부 확인용 빌드 · 스토어 공개 또는 상용 출시 완료를 뜻하지 않아요.", 12, muted=True),
        ], spacing=16, scroll=ft.ScrollMode.AUTO, expand=True),
        padding=20, expand=True,
    ))


if __name__ == "__main__":
    ft.run(main, assets_dir="assets")
