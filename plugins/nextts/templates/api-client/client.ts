import "server-only";
import createClient from "openapi-fetch";
import { env } from "../env";
import type { paths } from "./schema";

// 백엔드 호출은 이 클라이언트로만 한다. schema.d.ts는 pnpm api:generate가 만든다(직접 고치지 않는다)
export const api = createClient<paths>({ baseUrl: env.__BACKEND_URL_KEY__ });

// 인증 헤더(서비스 키, 사용자 정보 등)는 미들웨어로 붙인다. 프로젝트에 맞게 채운다
// api.use({
//   onRequest({ request }) {
//     request.headers.set("X-Service-Key", env.serviceKey);
//     return request;
//   },
// });
