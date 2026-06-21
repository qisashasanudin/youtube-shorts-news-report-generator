# Leak Research Methodology — Finding & Verifying Deleted Gaming Content

## Purpose
Repeatable pattern for researching gaming news leaks (especially accidentally uploaded then deleted content) within the 7-day window when original footage is unavailable.

## Trigger
- Official account posts then deletes content within minutes
- Time window: ≤ 7 days from deletion
- Topic must be tactical shooter (FPS, extraction, battle royale, tactical, looter-shooter)

## Source Hierarchy (Credibility Order)
1. **Major gaming news outlets with verified track records**
   - CharlieIntel (@charlieINTEL, 5.2M followers) — primary for Call of Duty
   - ModernWarzone (@ModernWarzone, 1.6M followers) — CoD/Battlefield focus
   - DETONATED (@DETONATEDcom, 73K followers) — detailed leak breakdowns
   - Insider Gaming, TheGamingRevolution, ForwardLeaks

2. **Established leakers/insiders with corroboration**
   - TheGhostOfHope (@TheGhostOfHope) — retired but still credible
   - dataminers (CS Bow, ForwardLeaks) — file-level verification

3. **Community aggregation (Reddit, Twitter threads)**
   - r/CoDCompetitive, r/GamingLeaksAndRumours — for clue aggregation
   - Cross-reference multiple commenters describing same details

## Research Workflow

### Step 1: Confirm Deletion Event
- Search: `[game name] [account name] deleted OR accidentally uploaded OR removed [date]`
- Look for major news account tweets confirming the deletion
- Note exact timestamp of original post and deletion

### Step 2: Gather Corroborating Reports
- Search each major source for their coverage
- Extract specific details each reports (weapons, mechanics, features shown)
- **Require ≥2 independent major sources reporting identical details** before treating as verified

### Step 3: Extract Specifics for Script
From this session (MW4 leak June 9, 2026):
- Gunsmith overhaul + Apex Attachments (new tier, unique per weapon)
- Hip-fire bloom REMOVED (predictable recoil, no RNG)
- Map Voting, Ninja Perk, Theater Mode returning
- Dual Prestige system (traditional + no-reset path)
- Riot Shield rework (deployable portable cover)
- Movement: smoother, faster handling, momentum-focused
- Specific spotted: PPSH with missile launcher, MK2 Marksman, throwing knife underbarrel

### Step 4: Fallback Footage Strategy
**Per skill rule: "rumor stories may use older official franchise trailer as fallback footage"**
- Official MW4 reveal trailer (May 2026) = clean B-roll
- Official gameplay trailers from developer/publisher channel
- Do NOT use fan re-uploads, reaction videos, or unverified mirrors

### Step 5: Label Clearly in Script
- Opening: "CoD Middle East **accidentally leaked MW4 multiplayer** — here's what they deleted"
- Body: Present as leak/rumor, not confirmed announcement
- Closing engagement question about the leak content

## Verification Checklist Before Building
- [ ] Event occurred within last 7 days
- [ ] ≥2 major credible sources report identical core details
- [ ] Details are tactical-shooter-relevant (mechanics, weapons, systems)
- [ ] Official fallback trailer identified and verified downloadable
- [ ] Story labeled as leak/rumor in narration
- [ ] Dedupe check: not already covered today in editorial_state.json

## Time-Saving Patterns
- Search Twitter/X first for major account confirmations (CharlieIntel, ModernWarzone)
- Then extract details from their tweets + replies (community spots specific UI elements)
- Skip standalone YouTube videos until major sources corroborate — most are speculation
- Reddit threads useful for aggregating but not primary sources

## Anti-Patterns to Avoid
- ❌ Trusting single YouTuber/TikToker without major source corroboration
- ❌ Using fan-reuploaded "leaked footage" mirrors (copyright strike + unverified)
- ❌ Building on uncorroborated Reddit rumors
- ❌ Treating leak details as confirmed features — always label as "leaked" / "rumored"
- ❌ Exceeding 7-day window — if older, discard unless new confirmation surfaces

## Applicable Games (Tactical Shooter Focus)
- Call of Duty (MW, BO, Warzone, DMZ)
- Battlefield
- Rainbow Six Siege
- Escape from Tarkov / Arena
- Delta Force, Ready or Not, Ground Branch, Gray Zone Warfare, Arma Reforger
- Marathon, The Finals, XDefiant

---
*Session: 2026-06-10 | MW4 Middle East leak (June 9) research pattern established*