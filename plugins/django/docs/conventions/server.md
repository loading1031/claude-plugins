# Django 서버

## 기본 구조

- Django URLconf → view → Form/ModelForm → ORM → template 흐름을 기본으로 한다. 일반 CRUD를 위해 API 서버·DRF·React·별도 서비스 계층을 추가하지 않는다.
- 기존 앱 구성·FBV/CBV 관례를 따른다. 새 도메인은 Django app으로 나누되 모든 작은 기능을 새 app으로 만들지 않는다. `server/`, `apps/`, `views/async_views.py` 같은 경로를 모든 프로젝트에 강제하지 않는다.
- 일반 요청은 동기 view와 ORM으로 작성한다. 스트리밍·외부 비동기 I/O에 이유가 있을 때 async를 선택한다. 기존 async 코드를 플러그인 도입만으로 동기로 바꾸지 않는다.
- 설치된 Django/Python 버전과 lockfile을 먼저 확인한다. 문서 예제의 버전을 기존 프로젝트에 자동으로 맞추거나 올리지 않는다.

## 입력·권한·쓰기

- Form/ModelForm의 검증과 cleaned_data를 사용한다. ModelForm의 변경 가능 필드는 명시한다. 브라우저 검증·disabled/hidden 필드는 서버 권한 검증을 대신하지 않는다.
- Django 인증·세션·권한 기능을 우선 사용한다. 객체 조회를 사용자·소유 범위로 제한하고, 조회 권한과 수정 권한을 따로 확인한다.
- 변경 요청은 POST 등 의도에 맞는 메서드로 제한한다. 성공한 일반 폼 제출은 redirect해 새로고침 재전송을 피한다. 검증 실패는 bound form과 오류를 같은 화면에 보여 준다.
- 함께 성공해야 하는 DB 변경은 transaction.atomic으로 묶고 중복·고유 제약은 DB에도 둔다. migration은 검토 가능한 파일로 만들며 데이터 변환과 운영 적용을 구분한다.
- DEBUG·시크릿·DB·허용 호스트는 환경 설정으로 관리한다. 운영 비밀값이나 실제 사용자 데이터는 규칙·테스트 fixture·로그에 쓰지 않는다.

## QuerySet과 템플릿 경계

- 템플릿은 조회·쓰기 로직을 소유하지 않는다. view에서 필터링·정렬·페이지 분할과 필요한 related loading을 처리한다.
- select_related/prefetch_related는 실제 관계 접근에 맞춰 사용한다. 큰 목록 전체를 리스트로 만들지 말고 페이지 단위로 조회한다.
- 템플릿의 필터·프로퍼티·lazy 관계 접근도 DB 쿼리를 일으킬 수 있음을 확인한다.

## async를 사용하는 경우

- 해당 Django 버전의 async API를 확인한다. 평가가 일어나는 ORM 작업은 aget/acreate/asave 등 또는 async for로 처리한다. `alist()`를 가정하지 않는다.
- 지원 버전에서는 `await request.auser()`로 인증 사용자를 얻는다. lazy request.user 접근이나 템플릿의 추가 관계 조회가 동기 DB 접근을 일으키지 않게 한다.
- async 미지원 트랜잭션은 동기 함수 안에서 완결한 뒤 sync_to_async로 호출한다. async 안전성 보호를 끄는 설정으로 우회하지 않는다.
- render/Form 검증처럼 동기 동작이 섞인 경계는 DB 접근 여부를 검토한다. async 사용 자체를 성능 보장으로 취급하지 않는다.

출처: [Django async](https://docs.djangoproject.com/en/6.0/topics/async/), [Django forms](https://docs.djangoproject.com/en/6.0/topics/forms/), [Transactions](https://docs.djangoproject.com/en/6.0/topics/db/transactions/). 설치된 버전의 문서를 사용한다.
