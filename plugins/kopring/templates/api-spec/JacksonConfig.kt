package __BASE_PACKAGE__.config

import com.fasterxml.jackson.annotation.JsonFormat
import org.springframework.boot.jackson.autoconfigure.JsonMapperBuilderCustomizer
import org.springframework.context.annotation.Bean
import org.springframework.context.annotation.Configuration
import java.math.BigDecimal

// BigDecimal(금액·가격·비율·환율)은 JSON 문자열로 보낸다. 정수는 숫자 그대로 둔다
@Configuration(proxyBeanMethods = false)
class JacksonConfig {
    @Bean
    fun bigDecimalAsString(): JsonMapperBuilderCustomizer = JsonMapperBuilderCustomizer { builder ->
        builder.withConfigOverride(BigDecimal::class.java) {
            it.setFormat(JsonFormat.Value.forShape(JsonFormat.Shape.STRING))
        }
    }
}
