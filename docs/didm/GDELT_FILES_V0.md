# GDELT 2.0 파일 읽기 V0 (DS-10, 2026-11-24)

- 작성: DATA_SOURCE 세션 (메인 지시 DS-10). 코드: `core/didm/ingest/gdelt_files.py`, 수집기 `python -m tools.didm.collect_daily --data-dir <폴더> --no-gdelt --gdelt-file <파일...>`, 시험: `tests/didm_gdelt_files_acceptance.py` (합성 파일, 네트워크 없음).
- **이 코드는 내려받지 않습니다.** 소유자가 받은 파일 (또는 그 바이트)을 읽습니다. 파일 이름은 GDELT 그대로: `YYYYMMDDHHMMSS.export.CSV[.zip]` (사건), `YYYYMMDDHHMMSS.gkg.csv[.zip]` (GKG). mentions 파일은 받지 않음 (거부).
- 저장: 제목·URL·메타데이터만 (`core/didm/ingest/gdelt.py`의 `parse_events`/`parse_gkg`와 같은 열). 기사 본문은 GDELT가 주지 않고, 권리는 언론사.

## 1. 약관 (원문, www.gdeltproject.org/about.html, 2026-11-24, 법률 자문 아님)

"all datasets released by the GDELT Project are available for unlimited and unrestricted use for any academic, commercial, or governmental use of any kind without fee." / "any use or redistribution of the data must include a citation to the GDELT Project and a link to this website (https://www.gdeltproject.org/)."
→ 행마다 `payload.citation` = "GDELT Project, https://www.gdeltproject.org/", 수집기는 실행 끝에 인용 문구를 출력.

## 2. 행에 더하는 필드

| 필드 | 값 |
|---|---|
| `citation` | 위 인용 |
| `file_stamp` | 파일 이름의 15분 시각 (YYYYMMDDHHMMSS, UTC) |
| `md5_verified` | GDELT 파일 목록의 MD5를 함께 줬을 때만 True (아니면 zip CRC만 검사) |

`available_at` = `file_stamp` 시각 (PREREG_V0 5절 1항: GDELT 파일은 그 시각에 공개).

## 3. 열 위치 (기존 파서 그대로)

| 파일 | 열 수 | 쓰는 열 (0부터) |
|---|---|---|
| 사건 (export) | 61 | 0 GLOBALEVENTID, 1 날짜, 7·17 행위자 국가, 26~29 CAMEO·QuadClass, 30 Goldstein, 31~33 언급·출처·기사 수, 34 논조, 53 행위 국가, 59 DATEADDED, 60 SOURCEURL |
| GKG 2.1 | 27 | 0 레코드 ID, 1 DATE, 3 출처 이름, 4 문서 URL, 7 주제, 11 인물, 13 조직, 15 논조 묶음, 26 추가 (PAGE_TITLE) |

**미검증:** 이 열 정의를 GDELT 코드북 (data.gdeltproject.org/documentation/ 의 Event Codebook V2.0, GKG Codebook V2.1 PDF)과 다시 대조하지 못했습니다 — 그 호스트는 이 환경에서 막혀 있음 (2026-11-24 시도, 응답 없음). 대조가 필요하면 `data.gdeltproject.org` 허용 요청.

## 4. 사건일 창 거르기 (`select`)

- 시간: `available_at`이 [시작, 끝] 안.
- GKG: 별칭 사전 (별칭 → entity_id, 3자 이상)의 별칭이 행의 조직 이름과 같거나 페이지 제목에 낱말 단위로 나오면 그 entity를 붙임 (대소문자·공백 무시). `require_entity`면 붙은 것이 없는 행은 뺌. **최소 규칙**입니다 — 실제 연결 규칙 (동명이인, 약칭, 사명 변경 날짜)은 DIDM_DEV 칸 (SAMPLE_EXPANSION 8절).
- 사건 (events): 조직 이름이 없으므로 국가 (행위자 1·2, 행위 장소) 집합으로만 거름.

## 5. 소유자 PC에서 (선택)

GDELT 파일은 `http://data.gdeltproject.org/gdeltv2/<시각>.export.CSV.zip` / `.gkg.csv.zip`에서 받을 수 있습니다 (소유자 PC 브라우저·명령). 받은 뒤:

```
python -m tools.didm.collect_daily --data-dir "$env:LOCALAPPDATA\QUANTGEN\didm" --no-gdelt --gdelt-file C:\path\20261105190000.gkg.csv.zip
```

기대: `GDELT file 20261105190000.gkg.csv.zip: rows N, new N` + 마지막 줄 인용 문구.
