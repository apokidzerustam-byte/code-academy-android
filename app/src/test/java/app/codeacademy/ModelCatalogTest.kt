package app.codeacademy

import app.codeacademy.mentor.ModelCatalog
import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test

/** Каталог моделей: у каждой модели известны размер и SHA-256 (принимается только точная копия файла). */
class ModelCatalogTest {
    @Test fun hashesAndSizesAreSet() {
        assertEquals(2, ModelCatalog.models.size)
        for (m in ModelCatalog.models) {
            assertTrue("${m.id}: SHA-256", Regex("[0-9a-f]{64}").matches(m.sha256))
            assertTrue("${m.id}: размер", m.sizeBytes > 100_000_000)
            assertTrue("${m.id}: ссылка", m.url.startsWith("https://huggingface.co/Qwen/") && m.url.endsWith(m.fileName))
            assertEquals(m, ModelCatalog.bySha(m.sha256.uppercase()))
            assertTrue(m.minRamMb < m.recommendedRamMb)
        }
        assertEquals(null, ModelCatalog.bySha("0".repeat(64)))
    }
}
