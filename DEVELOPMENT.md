# Development and release

This document is for extension maintainers. Extension users should read the
[integration guide](docs/index.md).

## Prerequisites

- Defold 1.13.0 or newer
- a compatible `bob.jar` in the repository root
- Java supported by that Bob release
- Python 3
- a C++ compiler (`c++`) for the UMP consent parser tests
- Android SDK platform tools
- Xcode and signing assets for iOS device testing

Bob native-extension builds upload extension sources and manifests to the
selected Defold Extender server. See the
[Bob manual](https://defold.com/manuals/bob/) for current options.

## Check the repository

```sh
python3 -B updater/adapters.py check
python3 -B updater/android.py check
python3 -B updater/ios.py check
python3 -B -m unittest discover -s tests -v
git diff --check
```

The tests cover generated packaging, dependency pins, public Lua bindings,
callback names, resources, the example configuration, and UMP consent parsing.

## Update dependencies

The updater owns the generated Gradle, Podfile, adapter-property, ProGuard, and
iOS resource sections. Follow [the updater guide](updater/README.md) instead of
editing generated blocks by hand.

For a MAX SDK upgrade:

1. Read the Android and iOS SDK release notes.
2. Update pins and checksums in `updater/versions.json`.
3. Refresh `updater/adapters.json` when adapter versions change.
4. Run `python3 -B updater/ios.py` to update iOS SKAdNetwork IDs, resources,
   and generated manifests.
5. Regenerate the Android manifests.
5. Update the native bridge and callback serialization.
6. Update the Lua API, example, and migration guide.
7. Run repository checks and Bob builds.
8. Test both platforms and every enabled ad format.

Keep release dependencies pinned to exact versions.

## Build with Bob

The example disables all optional mediation adapters on Android and iOS
and enables R8 on Android. To build the Android example, use Defold
1.13.2 beta with staging Extender:

```sh
java -jar bob.jar \
  --archive \
  --platform armv7-android \
  --architectures armv7-android,arm64-android \
  --variant debug \
  --with-symbols \
  --bundle-format apk \
  --build-server https://build-stage.defold.com \
  --bundle-output dist/android-r8 \
  resolve build bundle
```

`game.project` selects `/builtins/manifests/android/dmengine.keep` through
`android.r8_keep_rules`. Extender automatically combines those engine rules
with `extension-applovin/manifests/android/applovin.keep` and the SDKs'
consumer rules. The extension's generated keep file preserves its JNI bridge
and includes two targeted `-dontwarn` rules for Moloco 4.12.0's optional
LevelPlay integration. Moloco guards this integration with class lookups and
exception handling, but its consumer rules omit
`com.unity3d.mediation.LevelPlay` and
`com.unity3d.mediation.impression.LevelPlayImpressionDataListener`.

The keep-file setting enables shrinking, optimization, and obfuscation independently
of the native engine variant. The debug variant allows the example's demo
SDK key to initialize MAX. `--with-symbols` retains R8's `mapping.txt` in
the bundle's symbols directory; check its R8 header to confirm the shrinker ran.
See [Defold's R8 settings](https://defold.com/manuals/project-settings/#r8-keep-rules).

When enabling Google adapters for testing, set `applovin.google_android_app_id`
to Google's public
[sample AdMob app ID](https://developers.google.com/admob/android/quick-start#configure_your_app)
in a local settings file. Use your own app ID when testing your MAX ad units.

iOS IPA:

```sh
java -jar bob.jar \
  --archive \
  --platform arm64-ios \
  --architectures arm64-ios \
  --variant debug \
  --build-server https://build.defold.com \
  resolve build bundle
```

Use `--bundle-output` for a dedicated artifact directory, but do not place it
inside Defold's reserved `build/` directory. Use
`https://build-stage.defold.com` only when testing staging.

Unsigned iOS bundles verify compilation and linking. Device testing requires a
matching signing identity and provisioning profile.

## Configure smoke tests

The repository demo key is used only by debug builds. Ad-unit IDs are not
committed. Supply them through Project Settings or a local Bob settings file:

```ini
[applovin]
demo_android_interstitial_ad_unit_id = YOUR_ANDROID_AD_UNIT_ID
demo_ios_interstitial_ad_unit_id = YOUR_IOS_AD_UNIT_ID
```

Pass the file with `--settings /path/to/test.settings`. Keep ad-unit IDs,
device IDs, and signing files out of the repository.

To test mediated networks, also enable the corresponding adapter flags in
the local settings file. All optional adapters are disabled in the checked-in
example; see the [integration guide](docs/index.md#mediated-networks) for flags.

## Android smoke test

```sh
adb install -r path/to/AppLovinMAXDefoldDemo.apk
adb logcat -c
adb shell monkey \
  -p com.defold.applovin.demo \
  -c android.intent.category.LAUNCHER 1
adb shell pidof com.defold.applovin.demo
adb logcat -d
```

Verify that:

- the process stays alive without an `AndroidRuntime` crash;
- initialization produces one `OnSdkInitializedEvent`;
- the Mediation Debugger reports the expected SDK, privacy state, and adapters;
- each configured format loads, displays, and reports failures correctly;
- rewarded and revenue callbacks contain the expected values;
- banner and MREC views survive hide/show and are destroyed on teardown.

An emulator is useful for smoke testing. Validate mediated networks and consent
behavior on physical devices before release.

## iOS smoke test

For an Apple Silicon simulator, use Bob from Defold 1.13.2 beta or newer
with the `arm64_sim-ios` target. When testing the beta, use staging Extender:

```sh
java -jar bob.jar \
  --archive \
  --platform arm64_sim-ios \
  --architectures arm64_sim-ios \
  --variant debug \
  --build-server https://build-stage.defold.com \
  --bundle-output dist/ios-simulator \
  resolve build bundle

xcrun simctl install booted dist/ios-simulator/AppLovinMAXDefoldDemo.app
xcrun simctl launch --console booted com.defold.applovin.demo
```

Use a device UUID instead of `booted` when several simulators are running.
Verify one `OnSdkInitializedEvent`, successful adapter initialization, and
the Mediation Debugger. Keep the app running long enough to catch crashes
after initialization. Enable any iOS mediation adapters needed for the test
through the local settings file.

Test a signed build on a physical device. Verify that:

- MAX initializes and the Mediation Debugger opens;
- the AppLovin resources and privacy manifest are present;
- ATT and CMP complete in the expected order;
- enabled adapters are reported correctly;
- fullscreen and view ads behave across rotation and backgrounding;
- callbacks stop after the Defold collection is finalized.

## Release checklist

- [ ] Core Android and iOS MAX versions match.
- [ ] Dependency pins and checksums are current.
- [ ] Updater checks and unit tests pass.
- [ ] Production Extender builds Android and iOS.
- [ ] The APK installs and runs through `adb`.
- [ ] A signed iOS build runs on a physical device.
- [ ] Initialization, privacy, adapters, formats, rewards, and revenue are
      tested.
- [ ] README, integration, migration, and script API documentation match.
- [ ] Only the approved demo SDK key is committed; ad-unit IDs, device IDs,
      signing profiles, and certificates are absent.
