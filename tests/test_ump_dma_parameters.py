from __future__ import annotations

import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
UTILS = ROOT / "extension-applovin/src/utils"


class UmpDmaParametersTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        compiler = shutil.which("c++")
        if compiler is None:
            raise unittest.SkipTest("A C++ compiler is required for the consent parser tests")

        directory = tempfile.TemporaryDirectory(prefix="applovin-ump-test-")
        cls.addClassCleanup(directory.cleanup)
        temporary = Path(directory.name)
        harness = temporary / "main.cpp"
        harness.write_text(
            '#include "UmpDmaParameters.h"\n'
            "#include <stdio.h>\n"
            "#include <string.h>\n"
            "int main(int argc, char** argv) {\n"
            "    if (argc != 3) return 1;\n"
            '    const char* additional = strcmp(argv[1], "<unset>") == 0 ? 0 : argv[1];\n'
            '    const char* purposes = strcmp(argv[2], "<unset>") == 0 ? 0 : argv[2];\n'
            "    const dmAppLovin::UmpDmaParameters result =\n"
            "        dmAppLovin::ParseUmpDmaParameters(additional, purposes);\n"
            '    printf("%d %d %d\\n", result.m_AdPersonalization,\n'
            "           result.m_AdUserData, result.m_AdjustConsent);\n"
            "    return 0;\n"
            "}\n",
            encoding="utf-8",
        )
        cls.executable = temporary / "ump-test"
        subprocess.run(
            [
                compiler, "-std=c++11", "-Wall", "-Wextra", "-Werror",
                "-I", str(UTILS), str(harness),
                str(UTILS / "UmpDmaParameters.cpp"), "-o", str(cls.executable),
            ],
            check=True,
            capture_output=True,
            text=True,
        )

    def assert_parameters(
        self,
        additional: str | None,
        purposes: str | None,
        expected: tuple[bool, bool, bool],
    ) -> None:
        result = subprocess.run(
            [
                str(self.executable),
                "<unset>" if additional is None else additional,
                "<unset>" if purposes is None else purposes,
            ],
            check=True,
            capture_output=True,
            text=True,
        )
        self.assertEqual(expected, tuple(value == "1" for value in result.stdout.split()))

    def test_consent_requires_adjust_in_the_consented_provider_list(self) -> None:
        for additional in (
            None, "", "1~", "2~~dv.2822", "2~1.35~dv.2822",
            "1~12822", "2~28220~dv.", "2~1.12822.28220~dv.2822",
        ):
            with self.subTest(additional=additional):
                self.assert_parameters(additional, "1111", (False, False, False))

    def test_both_ac_versions_and_each_provider_position(self) -> None:
        for additional in (
            "1~2822", "1~2822.35", "1~35.2822", "1~35.2822.41",
            "2~2822", "2~2822~dv.", "2~2822.35~dv.41",
            "2~35.2822~dv", "2~35.2822.41~dv.9",
        ):
            with self.subTest(additional=additional):
                self.assert_parameters(additional, "1111", (True, True, True))

    def test_missing_or_partial_purposes(self) -> None:
        for purposes, expected in (
            (None, (False, False, True)),
            ("", (False, False, True)),
            ("0", (False, False, True)),
            ("1", (False, True, True)),
            ("11", (False, True, True)),
            ("111", (False, True, True)),
            ("11010000000", (True, True, True)),
        ):
            with self.subTest(purposes=purposes):
                self.assert_parameters("2~2822~dv.", purposes, expected)

    def test_all_combinations_of_the_first_four_purposes(self) -> None:
        # Purpose 3 does not affect these DMA flags; purposes 1, 2 and 4 do.
        for number in range(16):
            purposes = format(number, "04b")
            expected = (
                purposes in ("1101", "1111"),
                number >= 8,
                True,
            )
            with self.subTest(purposes=purposes):
                self.assert_parameters("1~2822", purposes, expected)

    def test_malformed_or_unknown_additional_consent_is_not_granted(self) -> None:
        for additional in (
            "2822", "x~2822", "3~2822", "12~2822", "1", "2",
            "1~.2822", "1~2822.", "2~2822..35~dv.", "1~2822x",
            "1~x.2822", "1~2822.35x", "1~ 2822", "1~02822",
        ):
            with self.subTest(additional=additional):
                self.assert_parameters(additional, "1111", (False, False, False))

    def test_malformed_purposes_do_not_grant_dma_flags(self) -> None:
        for purposes in ("true", "1x11", "1111x", "1111 ", "1112"):
            with self.subTest(purposes=purposes):
                self.assert_parameters("1~2822", purposes, (False, False, True))
