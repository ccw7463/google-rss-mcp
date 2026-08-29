# 2026-08-29 — Smithery 재등록 및 범용화 리팩터링

Smithery에서 사라진 `google-rss-mcp`의 원인을 규명하고, 범용 서버로 리팩터링해
재등록까지 완료한 작업 기록.

## 결과

| 항목 | 이전 | 이후 |
| --- | --- | --- |
| Smithery 레지스트리 | `{"error":"Server not found"}` | 등재 |
| 서버 페이지 | 404 | 200 |
| Quality Score | — | 94 / 100 |
| 검색 노출 (`google rss`) | 없음 | 3위 |
| 지원 언어 | 한국어 고정 | 전 언어 (3단 폴백) |
| 툴 | 2개 + 상수 반환 툴 1개 | 3개 (검색 / 헤드라인 / 본문) |
| Docker 이미지 | 1.07 GB | 352 MB |
| 기사당 HTTP 요청 | 2회 | 1회 |
| 테스트 | 0개 | 33개 |

**공개 주소**

- Smithery: <https://smithery.ai/server/@ccw7463/google-rss-mcp>
- 게이트웨이: `google-rss-mcp--ccw7463.run.tools`
- 원본 인스턴스: `https://google-rss-mcp-production.up.railway.app/mcp`

## 문서

| 파일 | 내용 |
| --- | --- |
| [01-smithery-delisting.md](01-smithery-delisting.md) | 해제 원인 규명 — 플랫폼 마이그레이션 미이행 |
| [02-refactor.md](02-refactor.md) | 범용화 리팩터링과 그 과정에서 발견한 버그 5건 |
| [03-deployment.md](03-deployment.md) | 호스팅 선정 과정, 배포, Smithery 재등록 |

## 커밋

```
f842401  refactor: make locale configurable, slim deps, serve over HTTP
dca8197  feat: add main.py entrypoint for managed MCP hosts
6245edb  docs: pin the public deployment to the neutral locale
5ca7ae3  feat: add /health endpoint for platform health checks
89d34fe  docs: lead the hosting section with the public option
e05f97a  feat: default HTTP to stateless and add a Cloud Run deploy script
068ed28  feat: add railway.json for one-click Railway deploys
4a6a58e  chore: add square server icon for registry listings
5d602aa  docs: document the hosted instance and link the Smithery listing
```

20 files changed, 4564 insertions(+), 2646 deletions(-)

## 운영 시 주의

- **공개 인스턴스에 `GOOGLE_RSS_LANGUAGE`를 설정하지 말 것.** 설정하면 전 세계
  사용자가 그 언어의 기사를 받게 된다. 로케일 고정은 각자의 클라이언트 설정에서.
- **`main` 푸시 시 Railway가 자동 재배포**한다. 공개 인스턴스에 즉시 반영된다.
- Railway 빌더가 `Railpack`으로 잡히면 `Dockerfile`로 바꿔야 한다. UI 설정이
  `railway.json`보다 우선한다.
