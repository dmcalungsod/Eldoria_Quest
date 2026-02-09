## 2024-05-22 - Discord Interaction Price Tampering
**Vulnerability:** A shop system trusted the price value sent back from a Discord Select Menu interaction (`value="item_id:price"`). A malicious user could manipulate the interaction data to buy expensive items for 1 gold.
**Learning:** Discord interaction values are client-controlled inputs. Never trust sensitive data (like prices) embedded in them.
**Prevention:** Only embed IDs in interaction values. Always fetch prices or critical data from the server-side source of truth using those IDs.

## 2024-05-24 - Skill Trainer Logic Bypass
**Vulnerability:** Similar to the Shop vulnerability, the Skill Trainer trusted the cost and level data sent in the interaction value (`value="skill_id:cost:level"`). This allowed users to learn skills for free or set arbitrary skill levels.
**Learning:** This pattern of trusting client-side interaction data for critical game logic (costs, levels) is a recurring anti-pattern in Discord bot development when using stateful UI components.
**Prevention:** Refactor all interaction callbacks to only accept an ID. Retrieve all stateful data (costs, current levels, requirements) from the database or static configuration at the moment of execution.
