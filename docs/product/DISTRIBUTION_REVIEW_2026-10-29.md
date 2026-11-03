# ⑩-1 Distribution review — research draft, not legal clearance

## Current decision
As of 2026-11-02, README records the owner's **commercial launch decision, OWNER_APPROVED on 2026-10-30**. That decision supersedes the earlier personal-use-only distribution policy. It does not constitute government/KOFIA endorsement, a professional legal opinion, or a provider's data license. Source-specific rights and the operational evidence in `docs/compliance/RELEASE_GAPS.md` remain separate checks; document consistency PASS is not clearance of those gaps. A deployed introductory website does not establish rights to redistribute market data or release a paid research service.

### Historical decision — 2026-10-29
At the original review date the posture was personal research only, and the 2026-10-27 roadmap's free companion was a proposal pending legal and data-right review. No site or service was deployed by that review task. These statements are retained as history, not as the current owner decision or a claim about later website work.

## Primary sources inspected 2026-10-29
- [Capital Markets Act, article 101](https://law.go.kr/lsLinkCommonInfo.do?chrClsCd=010202&lsJoLnkSeq=1017471463): the retrieved text is effective 2026-10-02. Its reporting rule concerns conducting a business providing non-individualized investment/value advice for consideration. Whether this product meets that definition depends on the actual service and business model.
- [Article 101-2](https://law.go.kr/LSW/lsLinkCommonInfo.do?chrClsCd=010202&lsJoLnkSeq=1033319315): restrictions include misleading guarantees and performance advertising. Do not frame simulated returns or the freedom logo as a promise of economic freedom.
- [FSC, 2024-08-13 explanatory release](https://www.fsc.go.kr/no010101/82887): distinguishes one-way non-individualized advice from paid interactive channels and explains the rules effective 2024-08-14. A disclaimer alone does not decide classification.
- [FRED legal terms](https://fred.stlouisfed.org/legal/) and [API terms](https://fred.stlouisfed.org/docs/api/terms_of_use.html): API access does not grant third-party series rights; personal use and redistribution/commercial uses require separate analysis and applicable attribution/permission. Do not infer one license for all FRED series.
- Yahoo terms page retrieval returned HTTP 999/Unknown Status Code. Yahoo redistribution permission was not verified. KRX/KIS/FMP/BoK/Binance/Upbit rights and any contract-specific restrictions also remain NOT_VERIFIED; installed clients do not resolve them.

## Counsel packet
Provide an actual feature/flow demonstration, target jurisdictions, personal/public audience, pricing and indirect monetization, exact output examples, interactivity, security data flow and every data source contract. Ask counsel to address: (1) tool vs investment advice classification; (2) free and paid phases separately, including advertising/referrals; (3) personalized prompts/alerts and two-way communication; (4) required registration/reporting and prohibited representations; (5) privacy/retention, consumer terms and cross-border services. Record written advice's date, reviewed version and limitations. This document does not assert that all free tools require registration or that free distribution is exempt.

## Data rights matrix
| Use | Current evidence | Implementation posture |
|---|---|---|
| Owner's local analysis | Existing source access varies; each contract applies | Existing adapters, source/time/synthetic labels |
| Personal ResearchRun export | No raw input price arrays; rights still unverified | Explicit user download; personal_research label |
| Public quote display / redistribution | No source-specific grant verified | Not released |
| Commercial derived analytics | Contract and legal treatment unverified | Not released |
| Offline design prototype using synthetic fixtures | Own generated fixture only | Private review artifact |

## Concrete release checklist
Written legal opinion with versioned feature scope; provider-by-provider rights/attribution list including derived outputs; privacy/terms and security review remain pending evidence. README policy reconciliation is recorded above and the owner's commercial decision is recorded in README; neither supplies the missing third-party evidence. A code merge records implementation without declaring those remaining items satisfied. Product deployment remains a separate operation within its approved scope.

## ⑩-2 companion preparation
An independent offline viewer prototype is prepared outside the QUANTGEN checkout. It accepts only an explicit ResearchRun export, verifies its integrity checksum and displays observations, assumptions and NOT_RUN separately. It contains no provider credentials, broker integration, order actions, telemetry, external CDN or write-back to QUANTGEN. Synthetic example only. It is not a publicly approved MVP or a production deployment.
