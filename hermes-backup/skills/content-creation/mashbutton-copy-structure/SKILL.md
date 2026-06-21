---
name: mashbutton-copy-structure
description: Enforces MashButtonGaming title and subtitle drafting rules for candidate news stories and short-video builds.
---

# MashButtonGaming Copy Structure Skill

## Title Rule
- Keep it short, sensational, franchise-specific.
- Must mention/franchise anchor and end with at least 5 hashtags.
- Do not use "and here's what you need to know." in the title.
- Title must match the final MP4 filename exactly (sanitization rules in pipeline skill).

**Sensational/Ambiguous Title Standard (2026-06-11):** User rejected straightforward descriptive titles in favor of curiosity-gap hooks. Preferred patterns:
- "Division Devs Just Dropped Something Wild" (curiosity gap)
- "You Can *Reshape the World* in This New Survival FPS" (mechanic hook)
- "The Division Meets Nordic Horror — And It Works?" (contrast)
- "4 Players. One Monolith. The Mist Changes Everything." (stakes)
- "Former Division Devs Built a Game That Lets You Terraform" (direct + tantalizing)
- **MashButton-style filename format:** `Former Division Devs BUILT A GAME WHERE YOU RESHAPE THE WORLD` (all caps, underscores for spaces)

## Subtitle Rule (MANDATORY)

- Opening must always be one lead sentence that ends with "... and here's what you need to know."
- Never make that phrase a standalone fragment before new content.
- Then add verified factual body content.
- Close with "... but what do you think?" followed by a direct engagement question.

**Narration Punctuation Requirement (2026-06-15):** TTS engines require punctuation for natural pauses and prosody. The `--subtitle` text MUST include proper punctuation (commas, periods, question marks) — not all-caps run-on sentences. Ensure draft narration includes:
- Commas for clause separation
- Periods for sentence boundaries
- Question mark on final engagement question
- Apostrophes for contractions (here's, it's, BF2042's)

All-caps ASS output is generated internally from the punctuated source.

**Engagement Question Quality:** See `mashbutton-gaming-pipeline/references/engagement-question-guidelines.md` for detailed criteria — the question must target a specific, debatable aspect of the game (unique mechanic, dev pedigree vs. genre, design trade-off), not a generic binary or yes/no prompt.

**Validated Engagement Questions (2026-06-11):**
- HAEX: "Is the world-reshaping mechanic exciting or just a gimmick?" — targets signature mechanic
- Warzone EOS: "Forced upgrade or justified evolution?" — targets player tension (forced migration vs. technical necessity)
- Rejected: "Survival genius or just Division 2.0?" — too binary, doesn't invite substantive debate

## Research-First Workflow (MANDATORY)

Before drafting any narration for gaming content:
1. **Verify facts from primary sources** (official trailers, YouTube metadata, dev blogs) — never rely on memory or secondhand claims
2. **Use YouTube oEmbed + yt-dlp** to extract authoritative video details (title, description, tags, upload date, uploader)
3. **Mark rumors/leaks clearly** in the proposal — do not present as confirmed
4. **Never fabricate** game names, map names, dates, or features for comparisons
5. If a comparison reference is needed and uncertain, omit it rather than invent

**Violation example (2026-06-15):** Agent hallucinated fake Battlefield map "Giants of Karelia" as a flop comparison. User caught immediately. Real verified flop maps: Orbital, Hourglass, Fjell 652, Aerodrome, Manifest.

## Narration Draft Review Workflow (MANDATORY)

**Critical correction from session 2026-06-15:** The user explicitly requires seeing the narration draft BEFORE any generation occurs. This is not optional.

Required sequence:
1. Research facts and write narration draft
2. **Present narration draft to user for review/approval**
3. Only on explicit "Approved" or similar confirmation, proceed to generation
4. If user requests edits, revise draft and re-present — do not generate until approved

## Verified Facts Rule
- Only include details verified before writing.
- For rumors/leaks, mark status clearly in the proposal.

## Footage Rule
- Prefer official trailer/source first.
- If using older/as-trailer fallback footage, note why current source footage is unavailable.

## Usage
Apply this before proposing or building any candidate. Use it for every future title/subtitle/trailer draft.
