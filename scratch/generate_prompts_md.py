import json
import re
from pathlib import Path

transcript_path = Path("/Users/tejaschavan1907/.gemini/antigravity/brain/cdb0f7dc-968f-4cc8-859c-e15283e2ee5f/.system_generated/logs/transcript_full.jsonl")
if not transcript_path.exists():
    transcript_path = Path("/Users/tejaschavan1907/.gemini/antigravity/brain/cdb0f7dc-968f-4cc8-859c-e15283e2ee5f/.system_generated/logs/transcript.jsonl")

user_prompts = []
with open(transcript_path, "r", encoding="utf-8") as f:
    for line in f:
        line = line.strip()
        if not line:
            continue
        try:
            data = json.loads(line)
            if data.get("type") == "USER_INPUT" or data.get("source") == "USER_EXPLICIT":
                user_prompts.append(data)
        except Exception:
            pass

lines = [
    "# DocuForge AI — Complete Prompt History",
    "",
    "This document records all user prompts provided during the development, redesign, polish, debugging, and rate-limiting phases of DocuForge AI.",
    "",
    "---",
    ""
]

for i, p in enumerate(user_prompts, start=1):
    content = p.get("content", "")
    req_match = re.search(r"<USER_REQUEST>(.*?)</USER_REQUEST>", content, re.DOTALL)
    req = req_match.group(1).strip() if req_match else ""

    # Artifact approvals
    if "The user has approved this document." in content:
        art_match = re.search(r"Comments on artifact URI:\s*(file://[^\n]+)", content)
        art_uri = art_match.group(1) if art_match else ""
        if req:
            req = f"{req}\n\nApproved artifact plan: {art_uri}"
        else:
            req = f"Approved artifact plan: {art_uri}"

    media = p.get("media", [])
    created_at = p.get("created_at", "")

    if not req and media:
        req = "[User uploaded image / media attachment]"

    lines.append(f"## Prompt {i}")
    lines.append("")
    if created_at:
        lines.append(f"**Timestamp:** `{created_at}`")
    if media:
        media_descs = [f"`{m.get('mime_type', 'media')}` ({Path(m.get('uri', '')).name})" for m in media]
        lines.append(f"**Attachments:** {', '.join(media_descs)}")
    lines.append("")
    lines.append("```text")
    lines.append(req)
    lines.append("```")
    lines.append("")
    lines.append("---")
    lines.append("")

output_path = Path("/Users/tejaschavan1907/Downloads/docuforge/prompts.md")
output_path.write_text("\n".join(lines), encoding="utf-8")
print(f"prompts.md generated successfully with {len(user_prompts)} prompts ({output_path.stat().st_size} bytes).")
