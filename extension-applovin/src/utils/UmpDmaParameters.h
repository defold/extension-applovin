#pragma once

namespace dmAppLovin {

struct UmpDmaParameters
{
    bool m_AdPersonalization;
    bool m_AdUserData;
    bool m_AdjustConsent;
};

UmpDmaParameters ParseUmpDmaParameters(const char* additionalConsent, const char* purposeConsents);

}//namespace dmAppLovin
