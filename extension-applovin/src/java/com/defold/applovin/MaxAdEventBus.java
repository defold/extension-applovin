package com.defold.applovin;

import android.util.Log;

import com.applovin.mediation.MaxAd;

import java.util.concurrent.CopyOnWriteArrayList;

/** Native ad callbacks for other extensions. Listeners run on the Android UI thread. */
public final class MaxAdEventBus
{
    private static final String TAG = "MaxAdEventBus";
    private static final CopyOnWriteArrayList<Listener> listeners = new CopyOnWriteArrayList<>();

    public interface Listener
    {
        /** Called for displayed interstitial and rewarded ads. */
        void onAdDisplayed(MaxAd ad);

        /** Called for paid banner, leader, MREC, interstitial, and rewarded ads. */
        void onAdRevenuePaid(MaxAd ad);
    }

    private MaxAdEventBus()
    {
    }

    /** Registers a listener once. The caller must remove it when no longer needed. */
    public static void addListener(final Listener listener)
    {
        if ( listener == null )
        {
            throw new IllegalArgumentException( "listener cannot be null" );
        }
        listeners.addIfAbsent( listener );
    }

    public static void removeListener(final Listener listener)
    {
        listeners.remove( listener );
    }

    static void notifyAdDisplayed(final MaxAd ad)
    {
        for ( Listener listener : listeners )
        {
            try
            {
                listener.onAdDisplayed( ad );
            }
            catch ( RuntimeException exception )
            {
                Log.e( TAG, "Ad display listener failed", exception );
            }
        }
    }

    static void notifyAdRevenuePaid(final MaxAd ad)
    {
        for ( Listener listener : listeners )
        {
            try
            {
                listener.onAdRevenuePaid( ad );
            }
            catch ( RuntimeException exception )
            {
                Log.e( TAG, "Ad revenue listener failed", exception );
            }
        }
    }
}
