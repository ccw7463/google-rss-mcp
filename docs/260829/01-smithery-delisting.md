# 01. Smithery 해제 원인 규명

## 결론

**정책 위반이 아니라 플랫폼 마이그레이션 미이행.** Smithery가 이 리포가 쓰던 배포
방식을 두 단계에 걸쳐 폐기했고, 그 사이 마이그레이션을 하지 않아 레지스트리에서
사라졌다.

## 사실 확인

세 경로 모두 삭제 상태였다.

```
https://smithery.ai/server/@ccw7463/google-rss-mcp   → 308 → /servers/... → 404
https://registry.smithery.ai/servers/@ccw7463/...    → {"error":"Server not found"}
https://api.smithery.ai/servers/@ccw7463/...         → {"error":"Server not found"}
```

## 폐기 1단계 — STDIO 종료 (2025-09-07)

기존 `smithery.yaml`이 폐기된 형식이었다.

```yaml
startCommand:
  type: stdio                    # ← 폐기된 형식
  commandFunction: |-
    (config) => ({ command: 'python', args: ['src/server.py'], env: {} })
```

Smithery는 HTTP 전환을 요구했다. HTTP가 동시성 20배, 지연 감소, 로드밸런싱·오토
스케일링을 가능하게 한다는 이유였다. 마이그레이션하지 않은 서버들이 이때 1차로
죽었다.

## 폐기 2단계 — 컨테이너 빌드 파이프라인 자체 제거

현행 [Smithery 문서 인덱스](https://smithery.ai/docs/llms.txt) 전체에
`smithery.yaml`, container runtime, "deploy from GitHub" 문서가 **한 페이지도
없다.** 현재 등록 경로는 둘뿐이다.

| 방식 | 내용 |
| --- | --- |
| **URL** | 직접 호스팅한 Streamable HTTP 엔드포인트 등록. Gateway가 프록시하고 `SmitheryBot/1.0`으로 스캔해 툴 목록 추출 |
| **Local (MCPB)** | stdio용 `.mcpb` 번들 업로드 |

즉 이 리포의 `smithery.yaml`과 GitHub 연동 Dockerfile 빌드는 **의미 없는 죽은
설정**이 되어 있었다. `smithery.yaml`은 삭제했다.

## 기각한 가설

처음엔 **Docker 빌드 실패**를 의심했다. 로컬 `uv sync`가 `tiktoken`의 Rust 컴파일
요구로 실패했기 때문이다. 그러나 `docker build`를 직접 돌려보니 **정상 성공**했다.
linux 이미지에는 wheel이 있어 통과한다. 빌드 문제가 아니었다.

교훈: 로컬 환경 실패를 배포 환경 실패로 넘겨짚지 말 것.

## 참고

- [Publish - Smithery Documentation](https://smithery.ai/docs/build/publish)
- [Smithery Documentation Index](https://smithery.ai/docs/llms.txt)
- [Apify — STDIO 종료일 명시](https://blog.apify.com/smithery-alternative/)
