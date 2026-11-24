# Synthetic citizen-to-coordinator-to-worker demo

Current closure: the approved static interview showcase is live at
https://dhroovs.github.io/YojanaSetu/ . It is screenshot/code evidence, not a live
backend. The full local platform and GitHub main push are verified; see
FINAL_RELEASE_REPORT.md for exact current CI results and release limitations.

## Ready-to-inspect synthetic walkthrough

The running demo and secure role credentials are documented in LOCAL_DEMO_ACCESS.md.
Start with demo-citizen, then demo-coordinator, demo-worker and demo-admin. Sign out
on My account between roles. The NGO volunteer is a worker profile kind. Inspect the
future assigned appointment and the distinct reviewed simulated visit/feedback.
Screenshots in demo-evidence prove local behavior; they are not a public backend.

Run the three processes in LOCAL_SETUP_WINDOWS.md, ingest reviewed sources, and provision
separate worker/coordinator/admin aliases. Do not use real citizen documents, addresses,
contact details or credentials in a recorded demo. Use separate browser profiles/tabs;
session tokens are memory-only and reloading requires sign-in.

1. Register a citizen alias, consent to the notice and sign in. Switch English/Hindi/
   Telugu on registration/discovery/booking pages; official scheme names remain unchanged.
2. Open Scheme assistant while signed in (no development token). Ask about PMSBY enrolment.
   Show evidence-only mode, cited official evidence, partial/reconciliation warnings and
   the original PDF source/page. Do not describe the result as government approval.
3. Create a PMSBY assistance case. The reviewed PDF supports a limited enrolment/auto-debit
   form checklist item. Upload a synthetic PDF containing only fictional test text.
   Show technical readability and human-review status. Ask document/follow-up/status
   questions and request a human referral. Ask the matcher through the case assistant.
4. As coordinator, claim the minimal unassigned case with confirmation. Review the file
   for the internal assistance checklist, resolve/acknowledge the referral with notes,
   and schedule a follow-up. Set quiet hours to equal start/end for immediate demo
   delivery, respecting the frequency limit. Run/keep the durable worker and refresh.
5. As citizen, acknowledge a delivered reminder/update. Open the consent-based doorstep
   link from the case. Choose document help, synthetic district/mandal/village/address,
   an appropriate future window, language, optional accessibility and sharing consent.
6. As worker, submit a profile covering that category/district/language/accessibility
   and declare the same available window. As admin, review and verify it with a future
   expiry and internal-only note. Explain that this is not government certification.
7. As coordinator, claim/review the doorstep request. Load the real eligible shortlist,
   confirm an assignment and explain the conflict checks. It is still a proposal.
8. As worker, accept the assignment. Only now show the precise authorized location and
   confirmed appointment. Check in within the actual time gate, select services really
   performed, enter synthetic task/visit notes and submit the outcome. Do not bypass
   the time gate in an ordinary demo; the automated test uses isolated clock fixtures.
9. As coordinator, review and confirm completion with a note. As citizen, confirm receipt,
   give feedback or request a future follow-up. Show audit history and the generic linked
   case activity after the polling worker processes the completion outbox.
10. Show cancellation/rescheduling on another synthetic active request, unauthorized
    account denial, and worker access removal. Never overwrite a reviewed outcome.
11. On the assistant, demonstrate unsupported-speech fallback or explicitly consent to
    browser speech processing if supported. Edit a transcript before submitting. Do not
    claim any language's native speech works without testing it on that device.
12. Open admin operations/source coverage. Finish with the exact test report and remaining
    release blockers. External messaging is unconfigured; no live message was delivered.

For reproducible headless evidence use the five browser scripts in TESTING.md. Phase 5
covers registration, translations, actual PDF-backed case and all five agent paths;
Phase 3/4 cover the coordinator/worker/reminder/completion workflows in disposable fixtures.
No public deployment or paid API is needed for the core demo.
