# 04. 처리 흐름 — 수집과 정제

`search_news` / `get_top_headlines`(헤드라인)와 `read_article`(본문)로 두 갈래다.
이 분리가 토큰 절감의 핵심이다.

## A. 헤드라인 수집

### 1. 로케일 결정

3단 폴백으로 `hl` / `gl`을 확정하고, 그 값으로 클라이언트 인스턴스를 만든다.

```
툴 인자 > 환경변수 > en/US
```

### 2. RSS URL 조립

```
news.google.com/rss/search?q=반도체&hl=ko&gl=KR&ceid=KR:ko
news.google.com/rss/headlines/section/topic/TECHNOLOGY?hl=...   ← 주제별
```

### 3. 피드 수신 — `_request()` 경유

동시성 상한(`Semaphore`) 안에서 GET. 429/5xx면 지수 백오프로 재시도,
TLS 오류면 즉시 포기한다(재시도해도 결과가 같다).

### 4. 파싱 + 정제

`feedparser`로 엔트리를 뽑고 항목마다:

- `clean_text()` — HTML 엔티티 복원, 태그 제거, 공백 정규화.
  **문자 allow-list 없음** — `AT&T`, `5%`, `$120`이 그대로 보존된다.
- 제목 분리 — Google이 `"제목 - 언론사"` 형태로 주므로 `rpartition(" - ")`로 쪼갠다.
- `parse_date()` — RFC 822 등 → timezone-aware datetime.

### 5. 자르기 → 그다음 URL 해석 (순서가 핵심)

```python
selected = items[:max_results]         # 먼저 자르고
resolved = await asyncio.gather(...)   # 남은 것만 해석
```

반대로 하면 버릴 기사까지 해석하느라 요청이 몇 배로 늘어난다.

### 6. Google 리다이렉트 해석 (`resolve_urls=true`, 병렬)

Google News는 모든 링크를 암호화된 리다이렉트로 감싼다.

```
news.google.com/rss/articles/CBMi...
   ↓ ① GET → HTML에서 c-wiz[data-p] 속성 추출
   ↓ ② data-p를 JSON으로 파싱해 payload 재조립
   ↓ ③ POST batchexecute (Fbv4je) — Google 내부 엔드포인트
   ↓ ④ 응답 봉투에서 실제 URL 추출
https://www.engadget.com/2246846/...
```

기사당 2회 요청이라 가장 비싼 구간이다. 실패하면 원래 링크를 그대로 반환해
전체가 죽지 않게 한다.

### 7. 직렬화

datetime → ISO 8601 문자열로 변환해 반환. **여기서 끝 — 본문은 가져오지 않는다.**

## B. 본문 추출 (`read_article`)

### 1. 필요하면 URL 해석

`news.google.com` 링크면 A-6을 수행. 이미 언론사 주소면 건너뛴다.

### 2. 페이지를 딱 한 번 GET

리팩터링 전에는 본문용·이미지용으로 두 번 받았다. 지금은 한 번 받아 한 번만
파싱하고 그 트리를 재사용한다.

### 3. 하나의 soup에서 셋을 뽑음

| 추출 | 방법 |
| --- | --- |
| 이미지 | `og:image` → `twitter:image` → `itemprop` → JSON-LD → 첫 유효 `<img>`. 상대경로는 절대경로로 변환 |
| 제목 | `og:title` → `<title>` |
| 본문 | 아래 4단계 |

### 4. 본문 정제

```
① 부속물 제거   script, style, nav, header, footer, aside, iframe, form, button
② 컨테이너 선택  article → [itemprop=articleBody] → .article-body → … → main
                (없으면 body 전체로 폴백)
③ 텍스트화      html2text (링크·이미지·강조 무시) → clean_text()
```

### 5. 길이 제한

`max_length` 초과 시 자르고 `truncated: true`를 같이 반환한다. 잘렸는지 에이전트가
알 수 있어야 하기 때문.

## 전 구간 공통

| 항목 | 내용 |
| --- | --- |
| 동시성 | `Semaphore(max_concurrency)` — 기본 5. Google의 429 방지 |
| 재시도 | 429/5xx → 지수 백오프 + 지터 / TLS 오류 → 즉시 포기 / 4xx → 상태코드 반환 |
| TLS | 시스템 저장소 대신 `certifi` 번들 (한국 언론사 인증서 체인 문제 회피) |
| 에러 | `return []` 대신 상태코드별 메시지. 403이면 "페이월이니 다른 기사를 시도하라"고 명시 |

## 전형적인 사용 흐름

```
사용자: "AI 뉴스 알려줘"
   ↓
search_news  →  헤드라인 10건 (제목·URL·매체·시각)     ← 가볍다
   ↓
에이전트가 읽고 판단: "2번이 관련 있네"
   ↓
read_article(2번 URL)  →  본문 + 이미지               ← 필요한 것만
```

리팩터링 전에는 1단계에서 본문 5건(약 8k 토큰)이 통째로 들어왔다. 지금은 헤드라인만
받고 정말 필요한 1~2건만 읽는다. 툴을 3개로 쪼갠 이유다.
