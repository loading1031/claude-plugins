# 웹 API

Zed에는 전체 HTTP 매핑을 보여 주는 Endpoints 창이 없다. 컨트롤러의 위치·이름·경로 작성법을 고정해서 검색 한 번으로 목록을 얻는다.

| 컨벤션 | 부류 | 강제 |
|---|---|---|
| 컨트롤러는 웹 진입 패키지(계층형: `api`, 헥사고날: `adapter/in/web`)에 `*Controller`라는 이름으로 둔다 | 팀 | ArchUnit |
| 클래스에 `@RequestMapping("/api/<자원>")`으로 전체 접두사를 한 번만 쓰고, 메서드에는 상대 경로만 쓴다 | 팀 | 리뷰 |
| 요청·응답 DTO는 컨트롤러와 같은 패키지에 두고, 엔티티를 응답으로 직접 반환하지 않는다 | 범용 | 리뷰 |
| 컨트롤러는 변환과 위임만 한다. 비즈니스 규칙은 application/domain에 둔다 | 범용 | 리뷰 |
| 엔드포인트 목록은 다음 검색으로 본다 | Zed | — |

```sh
grep -rn "@\(Get\|Post\|Put\|Patch\|Delete\|Request\)Mapping" src/main
```

```kotlin
@RestController
@RequestMapping("/api/stocks")
class StockController(private val stockQueryService: StockQueryService) {

    @GetMapping("/{sku}")
    fun get(@PathVariable sku: String): StockResponse =
        StockResponse.from(stockQueryService.snapshot(sku))
}
```
