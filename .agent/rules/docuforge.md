# DocuForge AI — project rules
- Preserve the existing backend, Gemini integration, SQLite data and saved projects. Database changes are additive migrations only.
- The Gemini API key stays server-side. Never expose it in frontend code, browser storage or logs.
- Never fake results: no hardcoded stats, no pre-written "generated" docs, no fake progress percentages. Marketing examples must be labelled as illustrative.
- Every visible control must work; remove what cannot.
- Show only the languages the app really supports.
- Design: deep charcoal, warm off-white, muted grey, ONE accent colour. No purple AI gradients, no emoji icons, no generic metric-card grids.
- Respect prefers-reduced-motion; keep contrast at AA; routes must survive browser refresh.
- Do not claim a feature works until it has been run in the browser. Report failures plainly.
- Full specification: docs/REDESIGN_SPEC.md