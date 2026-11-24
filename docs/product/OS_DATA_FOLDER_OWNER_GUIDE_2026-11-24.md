# 자료 폴더 안내 (소유자용, 2026-11-24)

근거: `docs/product/OS_DATA_STORAGE_2026-11-21.md`, `core/app_paths.py` (main `b872d8c`, OS-F2 PR #136). 작성: OS_EXPANSION 세션.

## 1. 결론: 지금은 옮기지 마세요

- QUANTGEN이 지금 쓰는 자료(KIS 토큰, DART 회사 코드, 매매·매크로·FICC 상태)는 이 PC에 `~/.nextgen`이 있으면 **그 폴더 그대로** 쓰입니다. 앱을 새 버전으로 바꿔도 자동으로 옮겨지지 않고, 잃는 것도 없습니다.
- TRADEGEN이 같은 KIS 토큰 파일(`~/.nextgen/kis_token.json`)을 읽습니다. 옮기면 그 공유가 끝나고, 두 앱이 토큰을 따로 받게 됩니다.
- 앱 안의 "자료 폴더 옮기기" 동의 화면은 아직 없습니다. 옮기는 기능(`migrate_legacy_data`)은 코드에만 있고, 동의 화면이 생긴 뒤 그 화면에서 쓰는 것이 원래 방식입니다.
- 옮길 때: TRADEGEN을 더 쓰지 않거나 토큰 공유가 필요 없어졌을 때, 또는 동의 화면이 나온 뒤.

| 상황 | 앱이 쓰는 폴더 |
|---|---|
| `QUANTGEN_DATA_DIR`를 지정함 | 그 폴더 (가장 우선) |
| 모바일(Flet) 앱 | 앱 전용 저장소 |
| QUANTGEN 표시 파일(`.quantgen-data-dir`)이 있는 플랫폼 폴더가 있음 | 플랫폼 폴더 |
| `~/.nextgen`이 있음 (소유자 PC) | `~/.nextgen` |
| 둘 다 없음 (새 PC) | 플랫폼 폴더 (처음 실행 때 만들고 표시 파일을 둠) |

플랫폼 폴더: Windows `%LOCALAPPDATA%\QUANTGEN`, macOS `~/Library/Application Support/QUANTGEN`, Linux `~/.local/share/quantgen`.

## 2. 지금 어느 폴더를 쓰는지 확인 (폴더 안은 열지 않음)

저장소 폴더에서, QUANTGEN·TRADEGEN을 켠 채로 해도 됩니다.

```
python -c "from core.app_paths import data_location as d; w=d(); print(w.source, w.path, 'can_migrate=', w.can_migrate)"
```

- `legacy C:\Users\<이름>\.nextgen can_migrate= True` → 기존 폴더를 쓰는 중(정상). 옮길 수 있는 상태라는 뜻일 뿐, 옮길 필요는 없습니다.
- `platform ...\QUANTGEN` → 플랫폼 폴더를 쓰는 중.
- `override ...` → `QUANTGEN_DATA_DIR`가 지정됨. 의도한 것이 아니면 그 환경변수를 지우세요.

이 명령은 폴더가 있는지와 표시 파일이 있는지만 보고, 폴더 목록을 읽거나 파일을 만들지 않습니다.

## 3. 나중에 옮긴다면

1. QUANTGEN과 TRADEGEN을 모두 끕니다.
2. 2절 명령에서 `legacy`와 `can_migrate= True`가 나오는지 봅니다. `False`면 플랫폼 폴더가 이미 있다는 뜻이므로 멈추고 세션에 알려 주세요.
3. 같은 폴더에서:

   ```
   python -c "from core.app_paths import migrate_legacy_data as m; print(m(confirmed=True))"
   ```

4. 2절 명령이 `platform ...`을 보이면 끝입니다. 이후 TRADEGEN이 `~/.nextgen`을 다시 만들어도 QUANTGEN은 플랫폼 폴더에 남습니다(표시 파일 때문).

이 기능은 같은 디스크 안에서 폴더 이름만 바꿉니다. 복사 뒤 지우기를 하지 않고, 대상 폴더가 이미 있으면 합치지 않고 거부합니다. 거부되면 자료는 `~/.nextgen`에 그대로 있습니다(작은 표시 파일 하나가 남을 수 있으나 무해합니다).

## 4. 되돌리기

1. QUANTGEN과 TRADEGEN을 모두 끕니다.
2. `~/.nextgen`이 **없는지** 확인합니다. TRADEGEN이 새로 만들어 두었다면 멈추고 세션에 알려 주세요(두 폴더를 합치는 일은 사람이 내용을 보고 정해야 합니다).
3. 플랫폼 폴더를 `~/.nextgen`으로 되돌립니다.
   - Windows PowerShell: `Move-Item "$env:LOCALAPPDATA\QUANTGEN" "$HOME\.nextgen"`
   - macOS: `mv ~/Library/Application\ Support/QUANTGEN ~/.nextgen`
4. 2절 명령이 `legacy`를 보이면 끝입니다. 안에 남은 `.quantgen-data-dir`는 `~/.nextgen`에서는 쓰이지 않으므로 지우지 않아도 됩니다.

급할 때는 폴더를 옮기지 않고 `QUANTGEN_DATA_DIR`에 원하는 폴더를 지정해 앱이 그 폴더를 쓰게 할 수도 있습니다.

## 5. 확인한 것과 한계

- 경로 시험 3개 모듈(`tests.app_paths_acceptance`, `tests.app_storage_startup_acceptance`, `tests.credentials_acceptance`)은 임시 폴더만 씁니다. 이 안내를 쓰면서 실제 `~/.nextgen`은 열지 않았습니다.
- Windows·macOS에서 실제로 옮기는 동작은 아직 소유자 PC에서 확인하지 않았습니다. 옮기기 전에 중요한 토큰·설정은 앱에서 다시 받을 수 있는지 먼저 확인하세요.
