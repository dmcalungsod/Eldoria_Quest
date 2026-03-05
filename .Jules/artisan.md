
## 2026-03-02
- **Focus**: Alchemist Crafting Passives
- **Discoveries**: Successfully implemented a 10% material retention chance for the Alchemist class when crafting consumables. This hook integrates directly into the core `craft_item` method of the `CraftingSystem`, demonstrating that class-specific passive abilities can be embedded deeply within systems.
- **Next Steps**: Monitor the economy and success rates of Alchemists to ensure the 10% retention is balanced. Consider similar hooks for other classes if requested by Architect.

## 2026-03-11
- **Focus**: Task GH.3 (Implement "Building Materials" and Boss Trophies) from Foreman's Guild Halls expansion.
- **Changes**:
  - Added `refined_stone` and `treated_lumber` as Common Building Materials to `materials.json`.
  - Added `stuffed_feral_stag_head` and `void_wraith_core_pedestal` as Boss Trophies to `materials.json`.
  - Created recipes for the above in `recipes.py` (`refine_stone`, `treat_lumber`, `craft_stuffed_feral_stag_head`, `craft_void_wraith_core_pedestal`).
- **Coordination**: @DataSteward @SystemSmith The items needed to test the `player_halls` schema logic are now available. @GameBalancer Check if the base costs I assigned align with your exponential scaling plans.
