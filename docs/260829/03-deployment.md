# 03. 호스팅 선정, 배포, Smithery 재등록

## 최종 구성

```
GitHub main
  └→ Railway  (google-rss-mcp-production.up.railway.app/mcp)
       └→ Smithery  @ccw7463/google-rss-mcp
            └→ Gateway  google-rss-mcp--ccw7463.run.tools
```

Smithery는 더 이상 Python 서버를 호스팅하지 않는다. 직접 호스팅한 HTTPS
엔드포인트를 등록하면 Gateway가 프록시하는 구조다.

## 호스팅 선정 — 두 번 갈아탄 기록

**교훈: 무료 티어가 있다는 것과, 그 무료 티어가 익명 트래픽을 허용하는 것은 별개다.**
아래 두 곳은 이 확인 없이 추천했다가 되돌렸다.

### Prefect Horizon — 기각

FastMCP 제작팀(Prefect)의 호스팅. 문서상 "free personal tier"라 첫 후보였고 배포도
성공했다. 그러나 무료 Personal 티어는 **조직 멤버만 접속 가능**하다.

```
Horizon Authentication
"Ensures clients connecting to your server are logged in to Horizon
 and are a member of ccw7463."
```

즉 Smithery로 들어온 외부 사용자는 전부 차단된다. 익명 접속(open authentication)은
**Developer $35/월**부터. 무료 뉴스 서버에 맞지 않아 기각.

> 부산물: Horizon은 서버를 **파일 경로**로 로드하고 의존성만 설치한다. 의존성만 깔린
> venv에서 `fastmcp inspect src/google_rss_mcp/server.py:mcp`가 `ModuleNotFoundError`로
> 실패하는 것을 확인하고, 루트에 `main.py` 엔트리포인트를 추가했다. 어느 관리형
> 호스트에서도 통하는 형태라 그대로 유지.

### Koyeb — 기각

카드 불필요 + 무절전이라 두 번째 후보였으나, **Mistral AI가 2026-02-17 인수**하면서
무료 Starter 플랜이 신규 가입자에게 폐지됐다. 최저가 **Pro $29/월**.

> *"The Starter plan will soon be removed and new users will instead need to
> subscribe to the Pro, Scale, or Enterprise plan."*

기존 사용자는 그랜드파더링되지만 신규 가입은 해당 없음.

### Railway — 채택

이미 사용 중인 서비스라는 점이 결정적이었다. 새 계정·새 결제수단이 필요 없다.

| 항목 | 값 |
| --- | --- |
| 실측 사용량 | 70 MB RAM, idle CPU 0.24% |
| 예상 비용 | 약 $1/월 (Hobby 플랜 $5 포함 사용량 내) |
| 콜드스타트 | 없음 (상시 가동) → 레지스트리 주기 스캔에 유리 |

`railway.json`을 리포에 커밋해 빌더와 헬스체크를 고정했다.

> 배포 당일 Railway에 인시던트가 있었다 (`8GL2R2U5` — Deployments slow to start,
> Monitoring → Investigating으로 역행, 전 리전 영향). 설정 문제로 오인하기 쉬우니
> 상태 페이지를 먼저 확인할 것.

### Google Cloud Run — 대안으로 보존

`deploy/cloudrun.sh`를 커밋해뒀다. 월 200만 요청 무료 + scale-to-zero라 실질 $0.
카드 등록이 필요하고 idle 후 첫 요청에 2~4초 콜드스타트가 있다. Railway가 불안정하면
여기로 옮기고 Smithery에서 URL만 바꾸면 된다 — **사용자 주소(`run.tools`)는 유지된다.**

## 배포 시 걸렸던 것들

### Railway 빌더가 `Railpack`으로 잡힘

`railway.json`에 `"builder": "DOCKERFILE"`을 넣었는데도 UI에는 Railpack으로 표시됐다.
서비스를 그 파일 푸시 **이전**에 만들어서, Railway가 자동 감지한 값을 서비스 설정에
저장해뒀기 때문. **UI 설정이 config 파일보다 우선한다.** Settings에서 수동 변경.

### `/health` 엔드포인트 추가

`/mcp` 외 모든 경로가 404였다. 호스팅 플랫폼이 HTTP `/`를 헬스체크하면 실패로
판정한다. 네트워크를 타지 않는 `/health`를 추가했다.

```json
{"status":"ok","server":"google-rss-mcp","version":"0.2.0",
 "default_language":"en","default_region":"US"}
```

Railway 실제 프로브 형태(`Host: healthcheck.railway.app`)로 검증 완료.

### 사전 검증한 것들

- `$PORT` 주입 (Cloud Run 8080, Koyeb 8000, Railway 8080) — 전부 정상
- FastMCP의 host-origin 보호가 `*.run.app` / `*.koyeb.app` / `*.up.railway.app`을
  막지 않는지 — 전부 200
- `SmitheryBot/1.0` User-Agent 차단 여부 — 200

## Smithery 재등록

**Publish via URL** → 네임스페이스 `ccw7463` / 서버 ID `google-rss-mcp`.
예전 슬러그가 비어 있어 그대로 되찾았다.

Connection settings의 파라미터는 **의도적으로 0개**로 뒀다. API 키가 필요 없어
사용자가 아무것도 입력하지 않고 연결된다. 참고로 Smithery는 URL 방식 서버에 설정값을
쿼리 파라미터/헤더로 넘기는데 우리 서버는 환경변수를 읽으므로, 여기에 `language`를
만들어도 전달되지 않는다.

### Quality Score 62 → 80 → 94

메타데이터를 채우면서 올랐다. **검색 랭킹에 직결**된다.

| 필드 | 값 |
| --- | --- |
| Description | 기능 요약 + "No API key required" (대부분의 뉴스 MCP가 유료 키를 요구하므로 실질적 차별점) |
| Homepage / Repository | GitHub 리포 |
| Server Icon | `assets/icon.png` |

> 아이콘 원본은 856×819 / 1.3 MB로 **정사각형 요구와 1 MB 상한을 둘 다 위반**했다.
> 가운데 819×819 크롭 후 512×512 축소 (409 KB). `assets/icon.png`로 커밋.

### 검증 결과

| 항목 | 결과 |
| --- | --- |
| `/health` | 200 (429 ms) |
| 익명 `initialize` | 200 — 인증 벽 없음 |
| `SmitheryBot/1.0` | 200 — 스캔 차단 없음 |
| 툴 노출 | 3개, 파라미터 스키마 정상 |
| 기본 로케일 | `en` / `US` |
| `ko` 오버라이드 | 원격에서 정상 |
| `read_article` | 제목·본문·이미지 추출 정상 |

검색 순위: `google rss` 3위, `google news` 4위, `news rss` 6위.

## 알아둘 것

- **Gateway가 익명 요청에 401을 반환하는 것은 정상이다.** `exa.run.tools`,
  `googledocs.run.tools`도 동일하다. Smithery 자체 접근 제어 레이어이며 우리 서버
  설정 문제가 아니다. 사용자가 "Add to toolbox"로 설치하면 키가 자동으로 붙는다.
- **레지스트리 API는 대시보드보다 반영이 늦다.** UI를 신뢰할 것.
- **Smithery 공식 뱃지 엔드포인트(`smithery.ai/badge/...`)는 500을 반환한다.**
  shields.io 뱃지로 대체했다.
