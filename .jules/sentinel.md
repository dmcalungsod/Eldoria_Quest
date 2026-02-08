## 2024-05-22 - Discord Interaction Price Tampering
**Vulnerability:** A shop system trusted the price value sent back from a Discord Select Menu interaction (`value="item_id:price"`). A malicious user could manipulate the interaction data to buy expensive items for 1 gold.
**Learning:** Discord interaction values are client-controlled inputs. Never trust sensitive data (like prices) embedded in them.
**Prevention:** Only embed IDs in interaction values. Always fetch prices or critical data from the server-side source of truth using those IDs.

## 2024-05-23 - Skill Trainer Cost Tampering
**Vulnerability:** The Skill Trainer trusted the cost value sent back from a Discord Select Menu interaction (`value="skill_key:cost"`). A malicious user could manipulate the interaction data to learn or upgrade expensive skills for 1 Vestige.
**Learning:** Similar to the shop vulnerability, trusting client-provided costs in interaction values is unsafe. Even if the interaction is ephemeral, the data payload can be intercepted and modified.
**Prevention:** Removed cost from interaction values. The server now looks up the skill cost from the static `SKILLS` data (for learning) or calculates it based on the current skill level in the database (for upgrading).
