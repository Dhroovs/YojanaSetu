# Hosting review under a strict INR 0 limit

Checked against official provider documentation on 23 November 2026. No account,
trial, card, subscription or billable resource was created. This is a fit assessment,
not a claim that all possible free providers have been exhausted.

The complete application needs FastAPI/native ONNX/Chroma, MongoDB, persistent private
uploads/vectors, and a durable polling worker. A static React host alone cannot supply
those services. Public backend release also remains gated by unresolved Chroma advisories.

| Provider | Verified free-tier facts / card constraints | Fit for this repository |
| --- | --- | --- |
| GitHub Pages | Free for public repositories on GitHub Free; static content; soft 100GB/month bandwidth and 1GB published-site limit | Best no-new-account interview showcase: screenshots, code and verification. Cannot run FastAPI, Mongo, Chroma or worker. Existing repository is public; leave visibility unchanged. |
| Cloudflare Pages | Free static requests; 500 monthly builds; account authorization needed | Good static alternative; not the existing native Python/persistent-files/worker stack. Do not enable paid Workers or R2. |
| Render Free | No card required for Free Docker web service; sleeps after 15 idle minutes; local changes lost at restart/redeploy; workers and persistent disks require paid compute | Fails durable files/vectors and always-running worker. Do not buy disks or use keep-awake traffic. |
| Koyeb Free | 512MB/0.1vCPU; cannot be worker or attach volume; sleeps after one hour. Pricing FAQ requires card verification and describes a default paid-plan signup | Excluded by card constraint and unsuitable storage/worker/runtime capacity. No signup performed. |
| Hugging Face Spaces | Current docs require a paid plan to create Docker/Gradio compute Spaces (limited ZeroGPU exception is not this architecture); static Spaces free. CPU Basic table still says no hourly hardware charge, which is not no-plan-cost eligibility | Do not rely on older free-Docker tutorials. Ephemeral storage/sleep and native Mongo port restrictions also prevent treating it as this complete reliable platform. |
| MongoDB Atlas Free | No card required; 0.5GB Mongo storage, capped; free-cluster operational limits | Can supply only Mongo after account/network/secret setup. Does not solve Chroma/files/worker hosting. Do not select Flex, upgrades or paid backups. |
| Vercel Hobby | Free personal/noncommercial tier with quotas; serverless/static runtime | Possible frontend, not a persistent native Chroma server or always-running worker. No migration or signup performed. |
| Cloudflare Quick Tunnel | Temporary URL without account/domain; no uptime guarantee; 200 in-flight requests and no SSE | Possible short self-hosted demonstration after explicit risk review; depends on this PC staying awake and online. It is not durable hosting, and exposing the development app is not approved while the security gate remains. No tunnel started. |

Recommendation: keep the full synthetic platform local for live walkthroughs and
publish a clearly labeled static interview showcase on the existing public repository's
GitHub Pages if approved. This preserves every core feature locally and creates no
paid infrastructure. A screenshot page must never present a simulated form as a working
backend, accept credentials, or send requests to a visitor's localhost.

A public React build pointed at this PC's `localhost` would address the visitor's
computer, not this backend, and HTTPS-to-HTTP calls can be blocked. Do not publish it
as a working remote application. A genuine complete hosted deployment requires a
provider that meets the persistence/worker requirements and a resolved security gate.
No reliable fit was established among the reviewed no-card free tiers.

## Official sources

- [GitHub Pages limits](https://docs.github.com/en/pages/getting-started-with-github-pages/github-pages-limits)
- [GitHub public-repository Actions pricing](https://github.com/pricing)
- [Cloudflare Pages limits](https://developers.cloudflare.com/pages/platform/limits/)
- [Cloudflare static pricing](https://developers.cloudflare.com/pages/functions/pricing/)
- [Render free restrictions](https://render.com/docs/free)
- [Render Docker/card/worker terms](https://render.com/hosting/docker)
- [Koyeb instances](https://www.koyeb.com/docs/reference/instances)
- [Koyeb card FAQ](https://www.koyeb.com/docs/faqs/pricing)
- [Hugging Face current Spaces eligibility/storage/lifecycle](https://huggingface.co/docs/hub/spaces-overview)
- [Atlas Free storage/limits](https://www.mongodb.com/docs/atlas/reference/free-shared-limitations/)
- [Atlas no-card developer sandbox](https://www.mongodb.com/resources/basics/databases/cloud-databases/free-cloud-database)
- [Vercel Hobby](https://vercel.com/docs/plans/hobby)
- [Quick Tunnel limitations](https://developers.cloudflare.com/tunnel/get-started/quick-tunnels/)

Recheck terms and the final dashboard before any future provisioning. Do not enter a
card, accept a paid trial, or upgrade a plan under the current authorization.
