## 2024-05-22 - Discord Interaction Price Tampering
**Vulnerability:** A shop system trusted the price value sent back from a Discord Select Menu interaction (`value="item_id:price"`). A malicious user could manipulate the interaction data to buy expensive items for 1 gold.
**Learning:** Discord interaction values are client-controlled inputs. Never trust sensitive data (like prices) embedded in them.
**Prevention:** Only embed IDs in interaction values. Always fetch prices or critical data from the server-side source of truth using those IDs.

## 2024-05-23 - Insecure JSON Construction
**Vulnerability:** Player statistics were being serialized to JSON using `str(dict).replace("'", '"')` instead of `json.dumps()`. This is brittle and can produce invalid JSON if strings contain quotes, or lead to injection if user input is ever stored in stats.
**Learning:** Never manually construct JSON strings. Python's string representation of a dict is not valid JSON.
**Prevention:** Always use the standard `json` library (`json.dumps`, `json.loads`) for serialization to ensure proper escaping and formatting.
