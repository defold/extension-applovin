from __future__ import annotations

import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BUS = ROOT / "extension-applovin/src/java/com/defold/applovin/MaxAdEventBus.java"


class NativeAdEventTests(unittest.TestCase):
    @unittest.skipUnless(shutil.which("javac") and shutil.which("java"), "Java is required")
    def test_android_listener_registration_and_fault_isolation(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            temp = Path(directory)
            package = temp / "com/defold/applovin"
            package.mkdir(parents=True)
            max_ad = temp / "com/applovin/mediation/MaxAd.java"
            max_ad.parent.mkdir(parents=True)
            max_ad.write_text("package com.applovin.mediation; public interface MaxAd {}\n")
            log = temp / "android/util/Log.java"
            log.parent.mkdir(parents=True)
            log.write_text(
                "package android.util; public class Log { "
                "public static int e(String tag, String message, Throwable error) "
                "{ return 0; } }\n"
            )
            runner = package / "AdEventTest.java"
            runner.write_text('''package com.defold.applovin;
import com.applovin.mediation.MaxAd;
public class AdEventTest {
    static class Counter implements MaxAdEventBus.Listener {
        int displayed;
        int revenue;
        public void onAdDisplayed(MaxAd ad) { displayed++; }
        public void onAdRevenuePaid(MaxAd ad) { revenue++; }
    }
    static class Broken implements MaxAdEventBus.Listener {
        public void onAdDisplayed(MaxAd ad) { throw new RuntimeException("display"); }
        public void onAdRevenuePaid(MaxAd ad) { throw new RuntimeException("revenue"); }
    }
    public static void main(String[] args) {
        Counter first = new Counter();
        Counter second = new Counter();
        MaxAdEventBus.addListener(new Broken());
        MaxAdEventBus.addListener(first);
        MaxAdEventBus.addListener(first);
        MaxAdEventBus.addListener(second);
        MaxAdEventBus.notifyAdDisplayed(null);
        MaxAdEventBus.notifyAdRevenuePaid(null);
        if (first.displayed != 1 || first.revenue != 1 ||
            second.displayed != 1 || second.revenue != 1) {
            throw new AssertionError("listener delivery or deduplication failed");
        }
        MaxAdEventBus.removeListener(first);
        MaxAdEventBus.notifyAdDisplayed(null);
        MaxAdEventBus.notifyAdRevenuePaid(null);
        if (first.displayed != 1 || first.revenue != 1 ||
            second.displayed != 2 || second.revenue != 2) {
            throw new AssertionError("listener removal or fault isolation failed");
        }
    }
}
''')
            subprocess.run(
                ["javac", "-d", str(temp), str(max_ad), str(log), str(BUS), str(runner)],
                check=True,
                capture_output=True,
                text=True,
            )
            subprocess.run(
                ["java", "-cp", str(temp), "com.defold.applovin.AdEventTest"],
                check=True,
                capture_output=True,
                text=True,
            )
