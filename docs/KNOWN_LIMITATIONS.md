# Known limitations and release gates

1. **Production security gate blocked:** current latest ChromaDB 1.5.9 has unresolved
   upstream HTTP-server high/critical advisories. This app has no Chroma server entry
   point, but no package fix is available at verification time. CI deliberately flags
   the dependency. Do not expose Chroma or publicly release without resolving/reviewing it.
2. **Container/CI runtime unverified:** Docker is absent; only YAML parsing and native
   Windows runs were performed. GitHub Actions files exist but have not been pushed/run.
3. **Live LLM unverified:** no local Ollama server is available. Working mode is local
   ONNX embeddings with retrieval-only grounded guidance. Hosted calls remain disabled;
   mock token/transport tests are not live inference. No API credits were assumed.
4. **Speech is limited:** native recognition/installed voices vary by browser/language
   and may use external processing. Consent, transcript editing, controls and fallback
   are tested; live microphone STT and real en/hi/te speech output have not been verified.
5. **Localization is draft quality:** measured static dictionary coverage is reported
   in LOCALIZATION_COVERAGE.json, with browser/Unicode/persistence tests. Native-language
   semantic review is not complete. Dynamic official evidence and some server diagnostics
   remain in their source language. English embeddings do not establish Hindi/Telugu
   free-text matching quality. Never treat translated UI as verified legal translation.
6. **Limited official knowledge:** three schemes/four partial documents. The PMSBY PDF
   adds one reviewed form item, not a complete onboarding checklist. Other requirements
   remain unknown. Multiple sources need human reconciliation; no positive combined
   eligibility decision is invented. Government pages may change after review.
7. **External messaging unconfigured:** optional Twilio/Meta adapters are mock-tested,
   default off and not connected to the scheduler. No paid credentials, approved live
   templates, signed delivery callback verification or live delivery test exists.
   An accepted provider receipt is not delivery; ambiguous timeouts are not blindly retried.
8. **Local operational scope:** no public account recovery or external staff authority
   validation. Admin role changes have conservative API limits. Operators must manage
   staff onboarding, expiry and revocation governance. Registration can be disabled.
9. **Scaling/failure limits:** bounded directories (500 candidate profiles, 100 organizations),
   finite audit arrays, conservative standalone multi-document recovery and polling-based
   delivery. No distributed load test, production snapshot/restore certification,
   push transport or managed infrastructure is claimed.
10. **Accessibility review remains:** keyboard/labels/focus/mobile checks are useful,
    but screen-reader testing, complete contrast measurement, native-language readability
    and disabled/elderly user testing are still needed. No WCAG certification is claimed.

No government endorsement, MeeSeva partnership, Aadhaar authentication, biometric KYC,
automatic government application submission, benefit guarantee or public deployment exists.
