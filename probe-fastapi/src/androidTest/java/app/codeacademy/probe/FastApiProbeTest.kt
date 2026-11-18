package app.codeacademy.probe

import android.util.Log
import androidx.test.ext.junit.runners.AndroidJUnit4
import androidx.test.platform.app.InstrumentationRegistry
import com.chaquo.python.Python
import com.chaquo.python.android.AndroidPlatform
import org.json.JSONObject
import org.junit.Assert.assertEquals
import org.junit.Test
import org.junit.runner.RunWith

@RunWith(AndroidJUnit4::class)
class FastApiProbeTest {
    @Test fun fastApiWorksOnDevice() {
        val ctx = InstrumentationRegistry.getInstrumentation().targetContext
        if (!Python.isStarted()) Python.start(AndroidPlatform(ctx))
        val json = Python.getInstance().getModule("probe_fastapi").callAttr("run").toString()
        Log.i("CAPROBE", "fastapi: $json")
        val r = JSONObject(json)
        assertEquals(json, "OK", r.getString("testclient"))
        assertEquals(201, r.getInt("post"))
        assertEquals(404, r.getInt("notFound"))
        assertEquals(422, r.getInt("validation"))
        assertEquals(422, r.getInt("badPath"))
        assertEquals(json, "OK", r.optString("uvicorn"))
    }
}
