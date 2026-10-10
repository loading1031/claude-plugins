# 외부 API

결제, 택배사, 증권사, ERP 같은 외부 시스템 호출이다. **out 포트 헥사고날을 쓴다.** 외부 API는 언제든 바뀌고, 느려지고, 실패한다. 그 영향이 서비스 코드에 번지지 않게 한다.

## 1. 구조

```kotlin
// application/port/out — 우리 도메인의 언어로
interface IssueWaybillPort {
    fun issue(shipment: Shipment): Waybill
}

// adapter/out/external/carrier
@HttpExchange("/v2/waybills")
interface CjCarrierApi {                         // 외부 API의 모양 그대로
    @PostExchange
    fun create(@RequestBody request: CjWaybillRequest): CjWaybillResponse
}

@Component
class CjCarrierAdapter(private val api: CjCarrierApi) : IssueWaybillPort {
    override fun issue(shipment: Shipment): Waybill =
        try {
            api.create(CjWaybillRequest.from(shipment)).toWaybill()
        } catch (e: RestClientResponseException) {
            throw CarrierUnavailableException("CJ", e)  // 도메인 예외로 변환
        }
}
```

## 2. 컨벤션

| 컨벤션 | 부류 | 강제 |
|---|---|---|
| HTTP 클라이언트(`RestClient`, `WebClient`)는 `adapter/out/external`(계층형: `infrastructure`)과 `config`에서만 쓴다 | 범용 | 훅 (`arch/tech-client-outside-adapter`) |
| HTTP 호출은 **HTTP Interface(`@HttpExchange`)**로 선언한다. 엔드포인트가 인터페이스 메서드로 드러나서 Zed에서도 사용처 찾기가 된다 | 팀 | 리뷰 |
| 새 코드에서 `RestTemplate`을 쓰지 않는다. `RestClient`(동기) 또는 `WebClient`(코루틴·비동기)를 쓴다 | 범용 | 리뷰 |
| 외부 API의 요청·응답 DTO는 어댑터 패키지 밖으로 나가지 않는다. 포트는 도메인 타입으로 주고받는다 | 범용 | 리뷰, ArchUnit |
| 외부 오류는 어댑터에서 도메인 예외로 바꾼다. 서비스가 `RestClientResponseException`을 알지 않게 한다 | 범용 | 리뷰 |
| **연결·응답 타임아웃을 항상 명시한다.** 기본값(무한 또는 매우 김)에 기대지 않는다. 타임아웃은 `*Properties`로 설정한다 | 범용 | 리뷰 |
| 재시도는 **멱등한 호출에만** 한다. 결제·주문 생성처럼 멱등하지 않은 호출은 멱등 키를 보내거나 재시도하지 않는다 | 범용 | 리뷰 |
| 장애가 이어지면 차단기(Circuit Breaker, Resilience4j 등)로 빠르게 실패시킨다 | 범용 | 리뷰 |
| 인증 키·비밀값은 환경 변수로 주입하고 로그에 남기지 않는다 | 범용 | 리뷰 |
| 요청·응답을 로그로 남길 때 `correlationId`를 함께 남긴다 | 범용 | 리뷰 |
| 외부 API를 여러 업체로 바꿔 쓸 수 있으면 업체별 어댑터를 두고 선택은 `config`에서 한다 | Zed | 훅 (`di/selection-in-config-only`) |

## 3. 코루틴

외부 호출은 코루틴을 쓸 수 있는 경계다([코루틴](../conventions/coroutines.md)). 여러 외부 API를 동시에 부를 때 유용하다.

- 코루틴을 쓰면 `WebClient` + `awaitBody()` 또는 `RestClient`를 `withContext(ioDispatcher)`로 감싼다.
- 동시 호출은 `coroutineScope { async(CoroutineName("...")) { ... } }`로 묶어서, 하나가 실패하면 나머지가 취소되게 한다.

## 4. 테스트

- 어댑터는 WireMock 또는 `MockRestServiceServer`로 외부 API를 흉내 내서 테스트한다. 타임아웃, 5xx, 잘못된 응답 형식을 꼭 넣는다.
- 서비스는 포트를 가짜 구현으로 바꿔 Spring 없이 테스트한다.
