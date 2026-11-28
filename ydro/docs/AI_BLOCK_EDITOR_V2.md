# AI Block Editor 2.0 — stage 10 first increment

The available sections are discovered from the accepted Vue archive rather than
assuming seven hard-coded sections. A section must have an exact literal
id/data-tn-section pair (or the trusted header/footer marker), be unique,
complete, non-nested and outside dynamic Vue scopes. IDs up to 48 characters
are supported. Existing sites with only standard markers continue to work.
Unmarked sections are deliberately not inferred.

The API requires the active version UUID, checks the artifact manifest and
validates that the selected scope exists before queueing. The worker validates
the source archive SHA-256 before any provider request. A newer worker feature
acknowledgement is required. The AI can modify the selected static markup and
bounded scoped CSS, while existing bindings, links, IDs, contacts and cinematic
elements are protected. A normal copy edit no longer upgrades the film runtime
without an explicit request. One paid request, no automatic paid retry, build
and browser audit, manual accept/discard; history remains append-only.

Local worker mounts the new agent script and shared parser read-only into the
existing agent image. The Dockerfile also includes the shared parser for
normal future builds. Migration 0008 expands the section identifier.
Limitations: no arbitrary dynamic component editing, no new assets or routes,
no multi-block transaction, no autonomous paid repair. A real paid edit and
browser candidate review remain local integration acceptance checks.
