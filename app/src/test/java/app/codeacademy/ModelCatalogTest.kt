package app.codeacademy

import app.codeacademy.mentor.ModelCatalog
import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test

/** Каталог моделей: у каждой модели известны размер и SHA-256 (принимается только точная копия файла). */
class ModelCatalogTest {
    @Test fun hashesAndSizesAreSet() {
        assertEquals(4, ModelCatalog.models.size)
        assertEquals(ModelCatalog.models.size, ModelCatalog.models.map { it.id }.toSet().size)
        assertEquals(ModelCatalog.models.size, ModelCatalog.models.map { it.fileName }.toSet().size)
        for (m in ModelCatalog.models) {
            assertTrue("${m.id}: SHA-256", Regex("[0-9a-f]{64}").matches(m.sha256))
            assertTrue("${m.id}: размер", m.sizeBytes > 100_000_000)
            assertTrue("${m.id}: ссылка", m.url.startsWith("https://huggingface.co/") && m.url.contains("/resolve/") && m.url.endsWith("/" + m.fileName))
            assertEquals(m, ModelCatalog.bySha(m.sha256.uppercase()))
            assertTrue(m.minRamMb < m.recommendedRamMb)
        }
        assertEquals(null, ModelCatalog.bySha("0".repeat(64)))
        // Только Qwen3 (не Instruct-2507) размышляет по умолчанию — ему нужен пустой блок размышлений.
        for (m in ModelCatalog.models) assertEquals(m.id, m.id.startsWith("qwen3-1.7b"), m.noThink)
        assertEquals("<think>\n\n</think>\n\n", ModelCatalog.byId("qwen3-1.7b-q4km")!!.promptSuffix)
        assertEquals("", ModelCatalog.byId("qwen3-4b-instruct-2507-q4km")!!.promptSuffix)
    }
}
