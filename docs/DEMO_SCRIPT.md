# Demonstration script: truthful, repeatable and interview-ready

Use synthetic data only. The public [showcase](https://dhroovs.github.io/YojanaSetu/) is a static
fallback, not a remote application backend. The complete platform runs at http://localhost:5173/,
with API docs at http://127.0.0.1:8000/docs while services run. Read
[LOCAL_DEMO_ACCESS.md](LOCAL_DEMO_ACCESS.md) for the secure local password command and aliases.
Do not display passwords, tokens, .env or private logs while screen-sharing. No actual video exists.

## Preparation

- Verify local frontend and /api/ready rather than assuming yesterday's processes remain alive.
- Use My account -> Sign out between roles. A hard reload clears memory-only sessions; repeated
  rapid sign-ins can hit the real rate limit, so allow time instead of disabling it.
- Keep a synthetic PDF ready. The existing demo helper stores a sample locally under the ignored
  inspection directory; never upload real Aadhaar, bank records, contact details or credentials.
- Existing future assigned visits and a separate reviewed simulated completion are demonstration
  records. A future visit cannot be checked in arbitrarily early. Do not rewrite its timestamps.
- Keep [presentation](PROJECT_PRESENTATION.md), [source](ARCHITECTURE.md) and [limits](KNOWN_LIMITATIONS.md)
  available. Say when a result is recorded evidence instead of an action performed live.

## Three-minute quick demonstration

| Time | Actual navigation | What to say |
| --- | --- | --- |
| 0:00-0:30 | Homepage -> Discover; select Source type verified | "These are reviewed partial sources, not a complete government catalogue." |
| 0:30-1:15 | My account -> sign in demo-citizen -> Scheme assistant; ask PMSBY accident insurance enrolment assistance -> Find relevant schemes | "This run uses real local retrieval without a live LLM. Evidence, missing fields and unknown eligibility remain explicit." |
| 1:15-2:00 | My assistance -> Open case; show Document assistance checklist, Follow-ups & in-app reminders and Case activity timeline | "This is a real private synthetic case. Readable files still need human review, and the server delivered this recorded reminder." |
| 2:00-3:00 | SevaSetu -> Open visit request; choose the already reviewed simulated completion if showing the end state | "Worker outcome and coordinator-reviewed completion are separate. This is a simulated visit record, not real field service or approval." |

## Five-minute interview demonstration

Do the three-minute route, spending an extra minute on source citations, source freshness/unknowns and
the structured case-to-visit link. Then sign out and show demo-coordinator's /coordinator queue or
demo-worker's SevaSetu appointment agenda. End by explaining the atomic calendar guard and the
red Chroma advisory gate. Do not spend the entire interview switching accounts or waiting for jobs.

## Ten-minute detailed demonstration

1. **Minute 1:** homepage, problem, intended users and actual public/local boundary.
2. **Minutes 2-3:** citizen login, discovery/detail, real matcher, citation and follow-up question.
3. **Minutes 4-5:** existing private checklist, synthetic upload/review state, timeline, reminder/referral.
4. **Minute 6:** Request consent-based doorstep help for this case; show linked request fields and consent.
5. **Minute 7:** coordinator queue/visit ranking and explicit human assignment gate.
6. **Minute 8:** worker profile/calendar and assigned appointment; explain acceptance/check-in/outcome.
7. **Minute 9:** recorded reviewed simulated completion, feedback and linked case activity.
8. **Minute 10:** admin operations/internal worker verification, test evidence and unresolved limits.

## Complete end-to-end live rehearsal

This takes as long as real review, scheduling and preferences require; do not promise a fixed short duration.
The exact controls below are exercised by the existing browser verification scripts.

### Citizen: discovery, case and document

1. Open /login. Register a new citizen if needed using Create a citizen account, alias/password,
   language and consent; otherwise sign in with the locally revealed demo-citizen credential.
2. Choose Discover. Set Source type to verified; search PMSBY and open its details. Explain the
   partial official-source status and use the source links rather than inventing requirements.
3. Choose Scheme assistant. Enter PMSBY accident insurance enrolment assistance and optional minimal
   profile fields. Click Find relevant schemes; inspect evidence and warnings. Ask a follow-up.
4. Choose My assistance, select Scheme PMSBY and click Create my case. Note the real reference,
   revision-backed changes and initial checklist. Case state is internal assistance, not government status.
5. Select Checklist item, choose a synthetic file through Synthetic or redacted file, then Upload
   securely / retry. Explain technical/readability state and needs human review. Do not claim KYC.
6. Use What documents do I still need?, When is my next follow-up? or Request human assistance.
   Distinguish read-only guidance from a supported confirmed apply-changes request where the UI asks.
   The actual record/timeline reveals whether a referral was persisted; a static answer is not proof.
7. Inspect Follow-ups & in-app reminders, Internal human referrals and Case activity timeline.
   Acknowledge a delivered reminder if available. Quiet-hour/frequency rules may delay a new one.

### Coordinator: responsibility, review and follow-up

8. My account -> Sign out, then sign in demo-coordinator. Navigate to /coordinator using the
   Coordinator workspace link or authorized queue. Claim only an unassigned case through its confirmed
   claim flow, or open an already responsible case. Other private cases are not globally available.
9. Open the document review controls. Record a review note and an appropriate checklist status;
   accept only within the source-checklist rules. Show reviewer/time/activity rather than claiming authenticity.
10. Review follow-up controls and schedule an internal due task. Check the referral queue,
    acknowledge/resolve with a meaningful synthetic note and explain reopening/history.

### Worker preparation and admin review

11. Sign in demo-worker -> SevaSetu -> My worker profile. Inspect service districts, categories,
    languages and declared availability. For a new live visit, add an available window roughly 10-20 minutes
    ahead with a supported duration, preserving existing reserved windows. Do not alter old appointments.
12. Admin sign-in -> Worker verification & availability or /seva/workers. Inspect verification,
    expiry, service areas and internal history. Only an appropriately reviewed current worker should
    receive assignment. Unverified/suspended profiles are ineligible. Internal review is not government certification.
13. Admin /admin shows user/role controls and sanitized Operational status. Demonstrate a harmless
    synthetic review-note update only if desired; do not demote an administrator or expose secrets.
    /sources is read-only provenance; ingestion/configuration remain an operator operation.

### Citizen and coordinator: consented booking

14. Return as citizen to the case and choose Request consent-based doorstep help for this case.
    The /seva/new form carries the related case reference. Choose Assistance category, describe
    synthetic help, set a future start/end, use Demo District coverage, synthetic mandal/village/address
    and the explicit share-with-assigned-worker consent. Submit doorstep request.
15. Record the actual pending coordinator review state and request reference. Get grounded coordination
    guidance is a bounded agent query; without a confirmed assignment it does not mutate the booking.
16. Coordinator -> SevaSetu -> Show minimal unclaimed request queue -> Claim request with confirmation.
    Open visit request -> Approve for internal assignment -> Get grounded coordination guidance.
    Inspect Choose eligible worker and verify category/language/area/verification/calendar reasons.
17. Confirm the intended proposal with the latest record state. A lower-ranked worker needs an
    override reason; no override bypasses conflicts. Do not use browser retries to force stale assignment.

### Worker: performed-service record

18. Worker -> SevaSetu -> Open visit request -> Accept proposed assignment. Before acceptance,
    precise address access is restricted. A declined assignment uses the supported return-to-review path.
19. Within the permitted time window, use En route/Check in as exposed, then enter Visit / review /
    problem note, Tasks actually performed and Services actually performed. Use Submit performed-service
    outcome for review. State explicitly that this rehearsal is simulated, with no physical service.
20. If a pre-existing visit is scheduled days ahead, show its state and the separate completed fixture
    instead. Do not change stored clocks to manufacture a live check-in result.

### Coordinator and citizen: review, feedback and tracking

21. Coordinator opens the outcome, records a review note/confirmation and uses Confirm reviewed visit
    completion. Inspect Recorded visit outcome and Request activity timeline.
22. Citizen opens that reviewed visit and uses Save feedback for reviewed visit with a synthetic note.
    Show In-app updates and acknowledgements when delivered. The worker may suggest a future follow-up
    only in the supported reviewed state; cancellation/reschedule cannot erase a performed outcome.
23. Reopen the linked case, inspect the completion-sync activity and current internal status.
    Visit completion does not automatically mean legal eligibility or scheme approval.
24. Show the language switcher (en/hi/te) and persistence/account preference. Demonstrate voice text
    fallback unless physical recognition/playback has actually been verified on this device with consent.
25. My account -> Sign out. Explain the real server-side session revocation and memory-only browser token.

## Fallbacks and stop conditions

- If local services are down, follow LOCAL_SETUP_WINDOWS.md. If they cannot be restored, use the public
  screenshot showcase and say you are showing recorded evidence, not a working remote backend.
- If RAG has no relevant evidence, explain cannot verify. Do not switch to fake facts or claim there are no schemes.
- If a model/provider is unavailable, stay in the verified evidence-only mode. No paid API calls or messages.
- If no eligible worker exists, show human review/reschedule/unavailability rather than bypass verification.
- If a revision changes, refresh and inspect actual state. Do not suppress the guard or weaken test assertions.
- If CI is red, explain the actual Chroma advisory gate and the independently passed test/container jobs.

For exact current control interactions, read verify_phase3_browser.py, verify_phase4_browser.py and
verify_phase5_browser.py under backend/scripts. Their synthetic fixtures prove backend persistence,
not merely a polished UI response. [Presentation and notes](PROJECT_PRESENTATION.md).
