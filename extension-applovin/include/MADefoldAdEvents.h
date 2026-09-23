#import <Foundation/Foundation.h>

NS_ASSUME_NONNULL_BEGIN

@class MAAd;

/** Native MAX callbacks for other extensions. Methods run on the iOS main thread. */
@protocol MADefoldAdEventListener <NSObject>
@optional
/** Called for displayed interstitial and rewarded ads. */
- (void)onMaxAdDisplayed:(MAAd *)ad;
/** Called for paid banner, leader, MREC, interstitial, and rewarded ads. */
- (void)onMaxAdRevenuePaid:(MAAd *)ad;
@end

@interface MADefoldAdEvents : NSObject
/** Weakly retains listeners; the caller must keep its listener alive. */
+ (void)addListener:(id<MADefoldAdEventListener>)listener;
+ (void)removeListener:(id<MADefoldAdEventListener>)listener;
@end

NS_ASSUME_NONNULL_END
