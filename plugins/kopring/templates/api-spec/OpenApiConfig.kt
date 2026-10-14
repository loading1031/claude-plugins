package __BASE_PACKAGE__.config

import io.swagger.v3.oas.models.media.StringSchema
import org.springdoc.core.utils.SpringDocUtils
import org.springframework.context.annotation.Configuration
import java.math.BigDecimal

// 스펙에도 BigDecimal을 문자열로 적는다. springdoc은 Jackson 설정(JacksonConfig)을 스펙에 반영하지 않는다
@Configuration(proxyBeanMethods = false)
class OpenApiConfig {
    init {
        SpringDocUtils.getConfig().replaceWithSchema(BigDecimal::class.java, StringSchema().format("decimal"))
    }
}
