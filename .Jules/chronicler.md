# 📓 Chronicler Journal

## 2026-03-01: Martius Update
**Status:** 🚀 Dispatched

### Summary
The **Martius 2026** update focuses on the launch of the **Auto-Adventure Overhaul**, **Frostfall Expanse** opening, **The Wailing Chasm**, **The Blind Choir's Requiem** questline, and various balance decrees.

### Key Highlights (In-World Translation)
- **Auto-Adventure Expeditions Now Available:** The Chronomancer's Guild has perfected temporal dilation.
- **The Wailing Chasm & Frostfall Expanse Open:** New subterranean abyss and eternal ice open for exploration.
- **New Questline: The Blind Choir's Requiem:** A cult of void-corrupted Delvers to investigate.
- **The Mystic Merchant in the Shadows:** Dynamic appearance during the night.
- **Guild Council Decrees & Balance Adjustments:** Bounties improved in Shrouded Fen, Thunder-Crag Coast, Shimmering Wastes. Feral Stag culling in Deepgrove Roots.
- **On the Horizon:** Alchemist class training, advanced mastery for Warriors/Rogues, Codex System.

### Learnings
- **Webhook Authentication:** When sending Discord webhooks, setting the `User-Agent` header is often necessary to avoid 403 Forbidden errors. The `requests` module does this automatically, but `urllib.request` does not. Setting it to a generic value like `ChroniclerAgent/1.0` works.

## 2026-02-25: Februarius Update
**Status:** 🚀 Dispatched

### Summary
The **Februarius 2026** update focuses on the anticipation of the **Auto-Adventure Overhaul** and the **Frostfall Expanse**. The tone is one of preparation—the calm before the storm.

### Key Highlights (In-World Translation)
- **Auto-Adventure:** Framed as "The Sands of Time" – a breakthrough by the Chronomancer's Guild.
- **Frostfall Expanse:** Teased as "A Frozen Horizon" – tales from Pathfinders about a land of eternal ice.
- **Alchemist Class:** "Science in a World of Magic" – The Apothecary Guild opening ranks to those who prefer science.
- **Balance:** "Restoring the Balance" – The Mages of the Equilibrium Circle stabilizing magic (fixing the infinite stats exploit).

### Learnings
- **Tone:** Strict adherence to "Guild Scribe Lirael" persona. No mention of agents or developers.
- **Format:** The script `scripts/chronicler/post_update.py` successfully parses the markdown headers (`#`, `##`, `---`) into a clean Discord Embed structure.
- **Execution:** The separation of content (markdown) and delivery (python script) allows for easy editing of the update text without touching the code.

### Feedback Loop
- *Pending player reaction to the Alchemist "Science" theme.*
- *Pending player reaction to the "Auto-Adventure" teaser.*