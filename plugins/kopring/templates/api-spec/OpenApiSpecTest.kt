package __BASE_PACKAGE__

import org.junit.jupiter.api.Test
import org.springframework.beans.factory.annotation.Autowired
import org.springframework.boot.test.context.SpringBootTest
import org.springframework.boot.webmvc.test.autoconfigure.AutoConfigureMockMvc
import org.springframework.test.web.servlet.MockMvc
import org.springframework.test.web.servlet.get
import tools.jackson.databind.SerializationFeature
import tools.jackson.databind.json.JsonMapper
import java.nio.file.Files
import java.nio.file.Path

// API 스펙을 openapi/openapi.json에 쓴다. 키를 정렬해 diff가 안정적이다. CI가 다시 만들어 커밋된 파일과 비교한다
@SpringBootTest
@AutoConfigureMockMvc
class OpenApiSpecTest(@Autowired private val mockMvc: MockMvc) {
    @Test
    fun `OpenAPI 스펙을 파일로 쓴다`() {
        val body = mockMvc.get("/v3/api-docs").andExpect { status { isOk() } }.andReturn().response.contentAsString
        val mapper = JsonMapper.builder()
            .enable(SerializationFeature.ORDER_MAP_ENTRIES_BY_KEYS)
            .enable(SerializationFeature.INDENT_OUTPUT)
            .build()
        val sorted = mapper.writeValueAsString(mapper.readValue(body, Map::class.java))
        val out = Path.of(System.getProperty("openapi.output") ?: error("openapi.output 시스템 속성이 없다(build.gradle.kts의 tasks.test)"))
        Files.createDirectories(out.parent)
        Files.writeString(out, sorted + "\n")
    }
}
