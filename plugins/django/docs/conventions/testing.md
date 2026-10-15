# 검증

프로젝트의 Django TestCase/Client 또는 pytest/pytest-django를 그대로 사용한다. 플러그인 도입을 이유로 테스트 도구를 바꾸지 않는다.

- 변경 동작의 성공·검증 실패·미로그인·다른 사용자 객체 접근을 확인한다. 조회뿐 아니라 쓰기 결과와 부작용을 검증한다.
- bound form 오류와 입력 유지, redirect와 HTML 응답, 변경 가능한 필드를 확인한다. CSRF 동작을 검증할 때 Django Client의 기본 CSRF 우회를 고려해 enforce_csrf_checks를 켠다.
- sync view는 Client, async 동작은 AsyncClient 등 실제 경계에 맞춰 검증한다. async DB 테스트의 transaction 설정은 기존 runner 관례를 따른다.
- 정적 페이지 문구나 클래스 목록을 그대로 복제하는 테스트를 추가하지 않는다. 중요한 HTML 상태는 렌더링/기능으로 확인한다.
- 템플릿을 수정했다면 정상·빈·오류 상태와 URL reverse, DTL 구문을 확인한다. 모달·HTMX 등 동작 변경은 가능한 브라우저 검증을 사용한다.
- 설정 변경은 해당 환경의 manage.py check, 모델 변경은 migration 차이를 확인한다. 운영 DB에 migration을 적용하는 것은 로컬 검증과 구분한다.
- Tailwind/DaisyUI 변경은 기존 CSS 빌드가 성공하고 필요한 클래스가 생성되는지 확인한다. collectstatic은 파일을 쓰는 검증이므로 출력 경로를 확인한다.
- 테스트 명령은 manage.py·설정 모듈·테스트 경로·패키지 매니저를 읽어 결정한다. 다른 프로젝트의 `server/apps`나 `uv` 경로를 하드코딩하지 않는다.
- 실행한 명령·결과와 실행하지 못한 항목을 구분한다. 훅 설치나 CI 통과를 실제 확인 없이 보고하지 않는다.

출처: [Django testing](https://docs.djangoproject.com/en/6.0/topics/testing/overview/).
