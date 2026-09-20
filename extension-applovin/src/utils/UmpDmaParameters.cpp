#include "UmpDmaParameters.h"

#include <string.h>

namespace dmAppLovin {

static bool HasAdjustConsent(const char* additionalConsent)
{
    // AC v1/v2: version~consented ATP IDs[~disclosed ATP IDs]. Only the
    // consented section counts; Adjust's ATP ID must match a complete token.
    if (!additionalConsent
        || (additionalConsent[0] != '1' && additionalConsent[0] != '2')
        || additionalConsent[1] != '~')
    {
        return false;
    }

    bool hasAdjustConsent = false;
    const char* provider = additionalConsent + 2;
    for (const char* cursor = provider; ; ++cursor)
    {
        if (*cursor >= '0' && *cursor <= '9')
        {
            continue;
        }
        if (cursor == provider || (*cursor != '.' && *cursor != '~' && *cursor != '\0'))
        {
            return false;
        }
        if (cursor - provider == 4 && memcmp(provider, "2822", 4) == 0)
        {
            hasAdjustConsent = true;
        }
        if (*cursor != '.')
        {
            return hasAdjustConsent;
        }
        provider = cursor + 1;
    }
}

UmpDmaParameters ParseUmpDmaParameters(const char* additionalConsent, const char* purposeConsents)
{
    UmpDmaParameters parameters = { false, false, false };
    parameters.m_AdjustConsent = HasAdjustConsent(additionalConsent);
    if (!parameters.m_AdjustConsent || !purposeConsents)
    {
        return parameters;
    }

    const size_t length = strlen(purposeConsents);
    for (size_t i = 0; i < length; ++i)
    {
        if (purposeConsents[i] != '0' && purposeConsents[i] != '1')
        {
            return parameters;
        }
    }

    parameters.m_AdUserData = length >= 1 && purposeConsents[0] == '1';
    parameters.m_AdPersonalization = parameters.m_AdUserData
        && length >= 4
        && purposeConsents[1] == '1'
        && purposeConsents[3] == '1';
    return parameters;
}

}//namespace dmAppLovin
