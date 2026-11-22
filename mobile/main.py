"""Internal Android preview. Constructs controls only; no data, accounts or research are loaded."""
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

    page.add(ft.Container(
        content=ft.Column([
            text("QUANTGEN", 26, bold=True),
            text("Android 내부 미리보기", 16),
            text("앱 기본 화면과 공통 글꼴·색상을 확인하는 단계예요. 아래 기능의 준비 상태를 확인해 주세요.",
                 muted=True),
            panel("화면 확인", "이 미리보기에서 확인 가능",
                  "휴대폰의 화면 배치와 스크롤을 확인할 수 있어요. 실제 기기 설치·실행 검증은 별도로 필요해요."),
            panel("시장 데이터와 차트", "미제공 · 실제 데이터 미연결",
                  "이 화면은 시세를 조회하지 않으며, 예시 값을 실제 시장 데이터로 표시하지 않아요."),
            panel("Quant Lab · Monte Carlo", "미제공 · 계산 및 결과 대조 미실시",
                  "연구 계산을 실행하지 않아요. 데스크톱과의 Monte Carlo 결과 일치는 아직 검증하지 않았어요."),
            panel("로그인", "미제공 · 계정 연결 없음",
                  "이 미리보기에서는 로그인하거나 저장된 인증정보를 읽지 않아요."),
            text("내부 확인용 빌드 · 스토어 공개 또는 상용 출시 완료를 뜻하지 않아요.", 12, muted=True),
        ], spacing=16, scroll=ft.ScrollMode.AUTO, expand=True),
        padding=20, expand=True,
    ))


if __name__ == "__main__":
    ft.run(main, assets_dir="assets")
