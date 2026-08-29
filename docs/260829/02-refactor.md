# 02. 범용화 리팩터링

목표: "범용적이고 사람들이 많이 쓸 수 있게". 그 과정에서 실제 버그 5건을 발견해
같이 고쳤다.

## A. 언어/지역 하드코딩 제거 — 가장 큰 블로커

`src/rss.py`에 `language="ko", region="KR"` 기본값이 박혀 있었고 `server.py`가
`GoogleRSSTools(timeout=timeout)`으로만 호출했다. **미국 사용자가 설치하면 한국어
기사만 나왔다.** 범용 서버로서는 치명적.

3단 폴백으로 교체했다. 좁은 범위 우선:

1. 툴 호출 인자 `language` / `region`
2. 환경변수 `GOOGLE_RSS_LANGUAGE` / `GOOGLE_RSS_REGION`
3. 중립 기본값 `en` / `US`

공개 인스턴스는 환경변수를 비워 중립으로 두고, 개인용은 클라이언트 설정에서
고정한다. 검증:

```
기본            → en/US | Trump announces new US oil agreement with Ven…
language=ko 요청 → ko/KR | 빙하 산사태가 초고속 폭류로 돌변한 이유…
```

## B. 툴 구조 재설계 — 컨텍스트 절감

기존은 `search_news` 하나가 검색과 본문 스크래핑을 한 번에 했다. 기본값이
5건 × 5000자 = **약 8k 토큰**이 무조건 컨텍스트에 들어왔다.

| 이전 | 이후 |
| --- | --- |
| `get_available_topics` (상수 반환) | 삭제 → `Literal` enum으로 스키마에 노출 |
| `search_news` (검색 + 본문) | `search_news` (헤드라인만) |
| `search_specific_topic_news` (검색 + 본문) | `get_top_headlines` (헤드라인만) |
| — | `read_article` (선택한 1건만 본문) |

에이전트가 헤드라인을 보고 필요한 것만 읽는 구조. 대부분의 질문은 헤드라인만으로
답할 수 있다.

## C. 발견해서 고친 버그 5건

### 1. `_clean_text`가 본문을 훼손 — 뉴스 도구에 치명적

allow-list 정규식 `[^\w\s\-.,!?;:()가-힣]`이 의미 있는 문자를 지우고 있었다.

| 원본 | 기존 결과 |
| --- | --- |
| `AT&T stock rose 5% to $120` | `ATT stock rose 5 to 120` |
| `C++ / C# developers @ Google` | `C C developers Google` |
| `약 $0.75` | `약 0.75` |

숫자와 회사명이 틀리게 나가고 있었다. 문자 필터를 버리고 `html.unescape()` +
공백 정규화만 남겼다. 테스트로 고정.

### 2. 날짜 파싱이 통째로 실패하고 있었음

`feedparser._parse_date`가 최신 버전에서 `feedparser.datetimes`로 이동해 존재하지
않는다. 기존 코드의 bare `except:`가 이 `AttributeError`를 삼키고 있어 아무도
몰랐다. 올바른 경로로 교체하고, 사라질 경우를 대비한 폴백도 넣었다.

### 3. SSL 인증서 체인 문제로 한국 언론사를 못 읽음

`edaily.co.kr` 등이 `CERTIFICATE_VERIFY_FAILED`로 실패했다. 시스템 인증서 저장소
대신 `certifi` 번들을 신뢰하도록 변경. 덤으로 인증서 오류는 재시도해도 결과가 같으니
재시도 대상에서 제외했다.

### 4. 페이월을 "알 수 없는 실패"로 뭉갬

NYT 등은 봇 요청에 403을 반환한다. 기존엔 `return []`이라 에이전트가 "뉴스 없음"과
"서버 고장"을 구분할 수 없었다. 상태 코드별 메시지로 교체:

```
publisher blocked automated access to <url> (HTTP 403) —
this is usually a paywall or bot protection. Try another result.
```

### 5. 서버리스에서 MCP 세션이 깨짐

MCP 세션 상태는 프로세스 메모리에 있다. Cloud Run처럼 요청마다 다른 인스턴스로
라우팅하는 환경에서는 후속 요청이 세션을 못 찾는다. 우리 툴 3개는 세션 상태가
필요 없으므로 stateless를 기본값으로 했다 (`MCP_STATELESS`, 기본 `true`).

컨테이너에서 검증: `mcp-session-id` 헤더 없음, `initialize` 없이 `tools/list` 성공.

## D. 성능·구조 개선

- **기사당 HTTP 요청 2회 → 1회.** 본문과 대표 이미지를 각각 GET 하던 것을 한 번
  받아 한 번 파싱해 둘 다 추출.
- **의존성 다이어트.** `langchain` / `langgraph` / `langchain-openai`가 런타임
  의존성에 있었으나 실제로는 `AsyncHtmlLoader` + `Html2TextTransformer`만
  사용했다. `aiohttp` + `html2text`로 대체하고 나머지는 `[examples]` extra로 이동.
  **이미지 1.07 GB → 352 MB.** (덤으로 `Html2TextTransformer`는 동기 함수라
  async 이벤트 루프를 블로킹하고 있었다.)
- **429 대응.** Google의 URL 해석 엔드포인트는 부하 시 429를 낸다. 동시성 상한
  (`Semaphore`) + 지수 백오프 추가.
- **본문 추출 품질.** `script`/`nav`/`footer` 등 페이지 부속물을 제거한 뒤 기사
  컨테이너를 우선 선택하도록 개선.
- **패키징.** site-packages에 `src`라는 최상위 패키지가 설치되던 것을
  `google_rss_mcp`로 개명. 콘솔 스크립트 `google-rss-mcp` 추가.

## E. 테스트

0개 → **33개**. 네트워크 없이 도는 순수 함수 테스트 위주.

- `clean_text`가 `&`, `%`, `$`, `+`, `#`, 따옴표를 보존하는지 (버그 1 회귀 방지)
- 날짜 파싱이 timezone-aware datetime을 반환하는지 (버그 2)
- 로케일이 인스턴스별로 적용되는지
- 본문 추출이 nav/script/footer를 버리는지
- 실패 메시지가 상태 코드별로 구분되는지 (버그 4)
- `__version__`이 `pyproject.toml`과 어긋나지 않는지
- `main.py:mcp` 엔트리포인트가 로드되는지
