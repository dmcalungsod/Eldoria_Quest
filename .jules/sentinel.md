## 2024-05-22 - Discord Interaction Price Tampering
**Vulnerability:** A shop system trusted the price value sent back from a Discord Select Menu interaction (`value="item_id:price"`). A malicious user could manipulate the interaction data to buy expensive items for 1 gold.
**Learning:** Discord interaction values are client-controlled inputs. Never trust sensitive data (like prices) embedded in them.
**Prevention:** Only embed IDs in interaction values. Always fetch prices or critical data from the server-side source of truth using those IDs.

## 2024-05-23 - Insecure JSON Construction
**Vulnerability:** Player statistics were being serialized to JSON using `str(dict).replace("'", '"')` instead of `json.dumps()`. This is brittle and can produce invalid JSON if strings contain quotes, or lead to injection if user input is ever stored in stats.
**Learning:** Never manually construct JSON strings. Python's string representation of a dict is not valid JSON.
**Prevention:** Always use the standard `json` library (`json.dumps`, `json.loads`) for serialization to ensure proper escaping and formatting.

## 2024-06-03 - Skill Trainer Cost Manipulation
**Vulnerability:** The Skill Trainer trusted the cost value sent back from the "Learn/Upgrade Skill" interaction (`value="skill_key:cost"`). Malicious users could modify this value to learn expensive skills for 0 cost or even negative values.
**Learning:** This is a classic "Parameter Tampering" vulnerability. Discord interaction data is untrusted client input, even if it originated from the bot's own UI.
**Prevention:** Only use the `skill_key` or unique identifier from the interaction. Always recalculate the cost server-side based on the current player state and authoritative data source (`SKILLS`).

## 2024-06-15 - Quest Location Validation Bypass
**Vulnerability:** The quest event system progressed "locate" and other objective types whenever a random non-combat event triggered, regardless of the player's current location. This allowed players to complete location-specific quests (e.g. "Locate Hidden Cave") by simply walking in circles in a safe zone.
**Learning:** Context-sensitive actions (like finding a specific location) must be validated against the current state context (the player's location) before applying progress. Assuming "event happened = progress made" is insecure.
**Prevention:** Always validate that the current game state (location, inventory, etc.) meets the specific requirements of the objective before granting progress. Pass context explicitly to handler functions.

## 2025-10-27 - Stale State in Persistent Views
**Vulnerability:** The `InfirmaryView` used cached `PlayerStats` from initialization to calculate healing costs and apply updates. If the player's stats changed in the database (e.g., via equipment swap in another session) while the view was open, the healing logic would use outdated values, leading to potential exploits (overhealing or incorrect costs).
**Learning:** UI Views in Discord.py are persistent in memory but the underlying database state is not. Relying on `self.attributes` initialized in `__init__` for critical logic is dangerous if that state can change externally.
**Prevention:** Always re-fetch critical data (like player stats or balances) from the database at the start of any sensitive transactional method (like `_execute_heal`), ensuring the logic uses the current authoritative state.
