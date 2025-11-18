"""
adventure_events.py

Provides dark-fantasy narrative text for non-combat exploration events.
Optimized for performance and future biome expansion.
"""

import random

import game_systems.data.emojis as E


class AdventureEvents:
    """
    Generates atmospheric narrative lines for Eldoria’s exploration system.
    All phrase lists are defined as class constants to avoid recomputation.
    """

    # =====================================================================
    # REGENERATION PHRASES
    # =====================================================================

    REGEN_PHRASES = [
        # Base set
        f"{E.FOREST} You pause to catch your breath by a stream...",
        f"{E.FOREST} You find a safe clearing and rest your weary limbs...",
        f"{E.FOREST} The air is calm. You take a moment to meditate...",
        # Expanded atmospheric set
        f"{E.FOREST} A faint warmth settles over you as the forest seems to breathe with you.",
        f"{E.FOREST} You steady your heartbeat and let the world fall quiet around you.",
        f"{E.FOREST} Rest comes easily as the whisper of leaves soothes your thoughts.",
        f"{E.FOREST} You kneel beneath an ancient oak, drawing strength from its silent presence.",
        f"{E.FOREST} A soft glow filters through the canopy, easing the ache in your muscles.",
        f"{E.FOREST} You close your eyes, letting the earth cradle your exhaustion.",
        f"{E.FOREST} The scent of moss and rain helps clear your mind and spirit.",
        f"{E.FOREST} You wash your hands in a cold brook, feeling clarity return.",
        f"{E.FOREST} A moment of stillness blankets you, renewing both resolve and breath.",
        f"{E.FOREST} You sit upon a fallen log, allowing time itself to mend your wounds.",
        f"{E.FOREST} A distant birdsong reminds you of calmer days, easing your fatigue.",
        f"{E.FOREST} You let out a long, steady breath as your strength slowly returns.",
    ]

    # =====================================================================
    # QUEST EVENT PHRASES
    # =====================================================================

    GATHER_PHRASES = [
        f"{E.HERB} You spot a cluster of **{{}}** growing in the shade of an ancient tree. You carefully harvest it.",
        f"{E.HERB} A faint glow draws your attention — **{{}}**, thriving between twisted roots.",
        f"{E.HERB} Beneath fallen leaves, you uncover **{{}}**, still fresh and untouched.",
        f"{E.HERB} Hidden in a fold of roots you find **{{}}**; you harvest with care.",
        f"{E.HERB} A sharp herbal scent fills the air as you collect **{{}}** with steady hands.",
    ]

    LOCATE_PHRASES = [
        f"{E.MAP} After searching the creek, you find **{{}}** hiding behind a rock, frightened but safe!",
        f"{E.MAP} Tracks lead you to a hollow trunk — **{{}}** rests within, trembling softly.",
        f"{E.MAP} A soft whimper alerts you. **{{}}** lies curled beneath an outcrop.",
        f"{E.MAP} You follow tiny prints to a burrow and discover **{{}}** tucked inside.",
        f"{E.MAP} A scrap of cloth catches your eye—behind it, **{{}}** waits, quietly shaken.",
    ]

    EXAMINE_PHRASES = [
        f"{E.SCROLL} You find the **{{}}** and study it carefully, noting every mark and detail.",
        f"{E.SCROLL} Strange sigils surround the **{{}}**. You record all you can.",
        f"{E.SCROLL} You kneel, observing **{{}}** with deliberate focus.",
        f"{E.SCROLL} Dust and carvings frame the object; you catalog every clue about **{{}}**.",
        f"{E.SCROLL} The artifact hums faintly; you sketch the **{{}}** for the Guild.",
    ]

    FALLBACK_QUEST_PHRASES = [
        f"{E.CHECK} You mark **{{}}** in your Guild log.",
        f"{E.CHECK} Your search succeeds — **{{}}** confirmed.",
        f"{E.CHECK} You update the quest record: **{{}}** located.",
        f"{E.CHECK} A clue reveals **{{}}**. You take note.",
        f"{E.CHECK} You uncover useful traces tied to **{{}}**.",
        f"{E.CHECK} You document new findings concerning **{{}}**.",
        f"{E.CHECK} You study the signs; **{{}}** is now accounted for.",
        f"{E.CHECK} A crucial detail about **{{}}** is added to your notes.",
        f"{E.CHECK} You carefully bag evidence linked to **{{}}**.",
    ]

    # =====================================================================
    # NO-EVENT PHRASES
    # =====================================================================

    NO_EVENT_PHRASES = [
        # Base
        f"{E.FOREST} You search the area but find nothing of interest.",
        f"{E.FOREST} The forest is quiet... too quiet.",
        f"{E.FOREST} A cold wind blows, but no monsters appear.",
        f"{E.FOREST} You follow a game trail for a time, but it runs cold.",
        # Expanded
        f"{E.FOREST} Only the rustle of distant branches answers your search.",
        f"{E.FOREST} You sense movement, but it fades before you can track it.",
        f"{E.FOREST} A hollow stillness clings to the woods, offering no discoveries.",
        f"{E.FOREST} You find old footprints… but whatever made them is long gone.",
        f"{E.FOREST} A faint echo drifts through the trees, but nothing reveals itself.",
        f"{E.FOREST} Shadows stretch between the roots, hiding nothing of value.",
        f"{E.FOREST} A crow watches you silently before taking flight into the gloom.",
        f"{E.FOREST} Your footsteps crunch through leaves, but no path unfolds.",
        f"{E.FOREST} The air thickens with the scent of rain, but the forest remains empty.",
        f"{E.FOREST} A distant branch snaps, though no foe approaches.",
        f"{E.FOREST} You brush aside vines, only to find more wilderness ahead.",
        f"{E.FOREST} The silence grows heavier as your search yields nothing.",
        f"{E.FOREST} A lone moth drifts past before melting into the shadows.",
        f"{E.FOREST} You trace shallow scars on a tree trunk—old, not fresh; the trail ends there.",
    ]

    # =====================================================================
    # EVENT GENERATION METHODS
    # =====================================================================

    @staticmethod
    def regeneration() -> list:
        """Returns a single regen narrative line (wrapped in a list)."""
        return [random.choice(AdventureEvents.REGEN_PHRASES)]

    @staticmethod
    def quest_event(objective_type: str, target_name: str) -> str:
        """Returns a single quest-related narrative line."""
        if objective_type == "gather":
            return random.choice(AdventureEvents.GATHER_PHRASES).format(target_name)

        if objective_type == "locate":
            return random.choice(AdventureEvents.LOCATE_PHRASES).format(target_name)

        if objective_type in ("examine", "survey"):
            return random.choice(AdventureEvents.EXAMINE_PHRASES).format(target_name)

        return random.choice(AdventureEvents.FALLBACK_QUEST_PHRASES).format(target_name)

    @staticmethod
    def no_event_found() -> str:
        """Returns a narrative line for an empty exploration step."""
        return random.choice(AdventureEvents.NO_EVENT_PHRASES)
