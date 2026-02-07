## 2024-05-22 - Discord Interaction Price Tampering
**Vulnerability:** A shop system trusted the price value sent back from a Discord Select Menu interaction (`value="item_id:price"`). A malicious user could manipulate the interaction data to buy expensive items for 1 gold.
**Learning:** Discord interaction values are client-controlled inputs. Never trust sensitive data (like prices) embedded in them.
**Prevention:** Only embed IDs in interaction values. Always fetch prices or critical data from the server-side source of truth using those IDs.

## 2024-05-23 - Unvalidated Adventure Location
**Vulnerability:** The `start_adventure` method accepted any string as `location_id`, allowing creation of broken adventure sessions via crafted interactions.
**Learning:** Backend logic relied implicitly on UI constraints (Discord Select Menu) to filter inputs, violating "Defense in Depth".
**Prevention:** Enforce strict validation against the source of truth (`LOCATIONS`) in the service layer, before writing to the database.
