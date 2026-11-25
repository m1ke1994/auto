# Offline browser audit recovery

The browser auditor records every screenshot attempt, retries timeouts once (30s then up to 45s), and caps total time spent on screenshots at 240s. Capture failures do not interrupt remaining DOM/interaction checks. The report separates functionalPassed and screenshotsComplete. passed requires both, including all 20 expected desktop/mobile images. Artistic quality remains unverified. Infrastructure failures carry errorStage; screenshot failures identify the device/frame. No screenshots or checks are fabricated, and a screenshot failure does not trigger automatic paid technical repair. The visual review scripts reject incomplete audits before billable requests.

Build and test the auditor with:
```powershell
docker build -t tracknode-studio-audit docker/studio-audit
.\studio-audit-existing.ps1 -RunDirectory ".\studio-agent-output\<existing-run>" -Profile cinema
```
The Docker build executes the capture regression tests and validates the main auditor syntax. The new command tests an existing dist without rebuilding the website, opening a credential-bearing agent, or modifying its original source or reports. Every rerun creates a separate audit-recheck-* folder. An incomplete report is not an approved source archive or a visual acceptance. Do not copy a checkpoint into a publishable archive merely to work around self-review.
