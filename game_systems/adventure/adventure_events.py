"""
adventure_events.py

Provides narrative, book-like text for non-combat exploration events,
matching the dark high-fantasy theme of Eldoria.
"""

import random
import game_systems.data.emojis as E


class AdventureEvents:
    """
    Houses all static methods for generating thematic non-combat narration.
    """

    @staticmethod
    def regeneration() -> list:
        """
        Called when the player rests and regenerates HP/MP.
        Returns a single randomly chosen narration line (as a list to match original API).
        """
        phrases = [
            # Original lines
            f"{E.FOREST} You pause to catch your breath by a stream...",
            f"{E.FOREST} You find a safe clearing and rest your weary limbs...",
            f"{E.FOREST} The air is calm. You take a moment to meditate...",
            # Added lines (12 + the original 3 = 15 total)
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
        return [random.choice(phrases)]

    @staticmethod
    def quest_event(objective_type: str, target_name: str) -> str:
        """
        Called when a non-combat quest objective is found.
        Handles common objective types and uses a fallback list for other cases.
        """
        # Gather variants
        if objective_type == "gather":
            gather_phrases = [
                f"{E.HERB} You spot a cluster of **{target_name}** growing in the shade of an ancient tree. You carefully harvest it.",
                f"{E.HERB} A faint glow draws your attention — **{target_name}**, thriving between twisted roots.",
                f"{E.HERB} Beneath fallen leaves, you uncover **{target_name}**, still fresh and untouched.",
                f"{E.HERB} Hidden in a fold of roots you find **{target_name}**; you harvest with care.",
                f"{E.HERB} The herbbed smells sharp; you collect **{target_name}** with steady hands.",
            ]
            return random.choice(gather_phrases)

        # Locate variants
        if objective_type == "locate":
            locate_phrases = [
                f"{E.MAP} After searching the creek, you find **{target_name}** hiding behind a rock, frightened but safe!",
                f"{E.MAP} Tracks lead you to a hollow trunk — **{target_name}** rests within, trembling softly.",
                f"{E.MAP} A soft whimper alerts you. **{target_name}** lies curled beneath an outcrop.",
                f"{E.MAP} You follow tiny prints to a burrow and discover **{target_name}** tucked inside.",
                f"{E.MAP} A scrap of cloth catches your eye—behind it, **{target_name}** waits, quietly shaken.",
            ]
            return random.choice(locate_phrases)

        # Examine / Survey variants
        if objective_type in ["examine", "survey"]:
            examine_phrases = [
                f"{E.SCROLL} You've found it: the **{target_name}**. You study the area and note your findings.",
                f"{E.SCROLL} Strange markings surround the **{target_name}**. You record every detail.",
                f"{E.SCROLL} You kneel, observing **{target_name}** carefully — its significance is undeniable.",
                f"{E.SCROLL} Dust and sigils surround the object; you carefully transcribe the clues about **{target_name}**.",
                f"{E.SCROLL} The artifact hums faintly; you take measurements and sketch the **{target_name}** for the Guild ledger.",
            ]
            return random.choice(examine_phrases)

        # Fallback universal quest-event variations (8+)
        fallback_phrases = [
            f"{E.CHECK} You mark the **{target_name}** in your Guild log.",
            f"{E.CHECK} Your search succeeds — **{target_name}** has been found.",
            f"{E.CHECK} You update the quest record: **{target_name}** confirmed.",
            f"{E.CHECK} A clue reveals **{target_name}**. You take note.",
            f"{E.CHECK} You uncover traces connected to **{target_name}**.",
            f"{E.CHECK} You document new findings concerning **{target_name}**.",
            f"{E.CHECK} You study the signs; **{target_name}** is now accounted for.",
            f"{E.CHECK} The investigation progresses — **{target_name}** located.",
            f"{E.CHECK} A small but useful detail about **{target_name}** is added to your notes.",
            f"{E.CHECK} You carefully bag evidence related to **{target_name}** for the Guild.",
        ]
        return random.choice(fallback_phrases)

    @staticmethod
    def no_event_found() -> str:
        """
        Called when the player explores but no combat or quest event happens.
        Returns one random narration line from a larger set.
        """
        phrases = [
            # Original lines
            f"{E.FOREST} You search the area but find nothing of interest.",
            f"{E.FOREST} The forest is quiet... too quiet.",
            f"{E.FOREST} A cold wind blows, but no monsters appear.",
            f"{E.FOREST} You follow a game trail for a time, but it runs cold.",
            # Added no-event narrations (12+)
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
            f"{E.FOREST} A single moth flutters past, and then all is still again.",
            f"{E.FOREST} You trace shallow scars on a tree trunk—old, not fresh; the trail ends there.",
        ]
        return random.choice(phrases)
