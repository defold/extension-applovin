"""Source contracts for the custom-data bridge; device tests are still required."""
import unittest
from pathlib import Path


SRC = Path(__file__).resolve().parents[1] / "extension-applovin/src"


def read(name):
    return (SRC / name).read_text(encoding="utf-8")


def method(source, signature):
    start = source.index(signature)
    opening = source.index("{", start)
    depth = 1
    for index in range(opening + 1, len(source)):
        depth += (source[index] == "{") - (source[index] == "}")
        if depth == 0:
            return source[opening:index + 1]
    raise AssertionError("Unclosed method: " + signature)


class CustomDataContractTests(unittest.TestCase):
    def test_fullscreen_argument_survives_each_bridge(self):
        lua = read("applovin.cpp")
        android = read("applovin_android.cpp")
        java = read("java/com/defold/applovin/MaxDefoldPlugin.java")
        ios = read("applovin_ios.mm")
        objc = read("MADefoldPlugin.mm")
        for name in ("ShowInterstitial", "ShowRewardedAd"):
            with self.subTest(name=name):
                body = method(lua, "static int Lua_" + name)
                self.assertIn('luaL_optstring(L, 2, "")', body)
                self.assertIn('luaL_optstring(L, 3, "")', body)
                self.assertRegex(body, name + r"\([^;]+, lua_placement, customData\);")
                java_name = name[0].lower() + name[1:]
                self.assertIn(
                    '"' + java_name + '", "(Ljava/lang/String;Ljava/lang/String;Ljava/lang/String;)V"',
                    android,
                )
                self.assertIn("adUnitId, placement, customData);", method(android, "void " + name))
                self.assertIn(".showAd( placement, customData, activity );", method(java, "public void " + java_name))
                self.assertIn("customData:customDataString]", method(ios, "void " + name))
                self.assertIn("customData: customData]", method(objc, "- (void)" + java_name + "ForAdUnitIdentifier:"))

    def test_banner_setter_does_not_create_or_load_ads(self):
        cases = (
            (read("java/com/defold/applovin/MaxDefoldPlugin.java"), "public void setBannerCustomData", "mBannerCustomData.put", "adView.setCustomData"),
            (read("MADefoldPlugin.mm"), "- (void)setBannerCustomData:", "self.bannerCustomData[adUnitIdentifier] =", "adView.customData ="),
        )
        for source, signature, cache, update in cases:
            body = method(source, signature)
            self.assertIn(cache, body)
            self.assertIn(update, body)
            self.assertNotRegex(body, r"retrieveAdView|loadAd|createAdView")

    def test_banner_data_is_applied_before_first_load(self):
        java = read("java/com/defold/applovin/MaxDefoldPlugin.java")
        # Android constructs and caches the view before createAdView schedules its load.
        self.assertLess(java.index("result.setCustomData("), java.index("mAdViews.put( adUnitId, result )"))
        create = method(java, "private void createAdView(")
        self.assertLess(create.index("retrieveAdView("), create.index("adView.loadAd()"))
        objc = method(read("MADefoldPlugin.mm"), "- (void)createAdViewForAdUnitIdentifier:")
        self.assertLess(objc.index("adView.customData ="), objc.index("[adView loadAd]"))

    def test_banner_cache_cleanup_does_not_depend_on_view_existence(self):
        java = read("java/com/defold/applovin/MaxDefoldPlugin.java")
        destroy = method(java, "private void destroyAdView(")
        self.assertLess(destroy.index("mBannerCustomData.remove"), destroy.index("if ( adView == null )"))
        self.assertIn("mBannerCustomData.clear();", java)
        objc = read("MADefoldPlugin.mm")
        destroy = method(objc, "- (void)destroyAdViewForAdUnitIdentifier:")
        self.assertIn("[self.bannerCustomData removeObjectForKey: adUnitIdentifier];", destroy)
        self.assertIn("[self.bannerCustomData removeAllObjects];", objc)
        for signature in ("- (void)setAdViewPlacement:", "- (void)hideAdViewForAdUnitIdentifier:"):
            self.assertNotIn("bannerCustomData", method(objc, signature))
