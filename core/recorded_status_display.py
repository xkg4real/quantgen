"""Bilingual presentation of an already verified snapshot; no I/O or policy decisions."""
from dataclasses import dataclass


@dataclass(frozen=True)
class StatusText:
    en: str
    ko: str
    muted: bool = False
    bold: bool = False

    def text(self, language: str) -> str:
        return self.ko if language == 'ko' else self.en


def recorded_status_display(status: dict | None) -> tuple[StatusText, ...]:
    """Keep recorded codes/dates literal and separate the owner decision from readiness.

    Callers must use tools.status.snapshot.verify first, passing None if verification
    fails. This formatter neither verifies evidence nor changes its meaning or values.
    """
    if status is None:
        return (
            StatusText('Recorded status unavailable', '기록된 상태 확인 필요', bold=True),
            StatusText('The recorded status could not be verified. Check its source files; no approval status is shown.',
                       '기록된 상태를 검증할 수 없습니다. 출처 자료를 확인하세요. 승인 상태는 표시하지 않습니다.'),
        )

    counts = status['code_test']['counts']
    data = status['data_readiness']
    calendar = data['calendar']
    gate = status['formal_gate']
    study = status['paper_study']
    policy = status['distribution_policy']
    checks = f"{counts['PASS']} PASS / {counts['FAIL']} FAIL / {counts['NOT_RUN']} NOT_RUN"
    return (
        StatusText(f'Recorded code checks: {checks}', f'기록된 코드 검사: {checks}', bold=True),
        StatusText('These are recorded results, not a new test run. The source records no run time or commit.',
                   '기존에 기록된 결과이며 이번에 실행한 검사가 아닙니다. 원본에는 실행 시각과 커밋이 없습니다.', muted=True),
        StatusText(f"Calendar: {calendar['files']} signed metadata entries · set {calendar['version']}",
                   f"달력: {calendar['files']}개 서명 메타데이터 · 세트 {calendar['version']}"),
        StatusText(f"Signed at {calendar['signed_at']} · individual calendar files are not verified here.",
                   f"서명 시각 {calendar['signed_at']} · 파일별 서명 검증은 별도입니다.", muted=True),
        StatusText(f"Data {data['status']} · formal gate {gate['status']} (documented; verification {gate['verification']})",
                   f"데이터 {data['status']} · 공식 게이트 {gate['status']} (문서 기록; 검증 {gate['verification']})"),
        StatusText(f"Frozen study {study['status']}", f"동결 연구 {study['status']}"),
        StatusText(f"Distribution policy {policy['status']} · owner decision {policy['public_release']} · {policy['decision_date']}",
                   f"배포 정책 {policy['status']} · 소유자 결정 {policy['public_release']} · {policy['decision_date']}"),
        StatusText('This is the owner\'s commercial launch decision, not regulatory endorsement or technical readiness.',
                   '소유자의 상업화 출시 결정이며, 규제 승인이나 기술 준비 완료를 뜻하지 않습니다.', muted=True),
        StatusText('Actual public release is not established by this recorded evidence.',
                   '이 기록만으로 실제 공개 배포 여부는 확인되지 않습니다.', muted=True),
        StatusText('Sources: qa/acceptance_results.json · calendar MANIFEST · README',
                   '출처: qa/acceptance_results.json · calendar MANIFEST · README', muted=True),
        StatusText(f"Snapshot generated at: {status['generated_at']}",
                   f"상태 자료 생성 시각: {status['generated_at']}", muted=True),
    )
