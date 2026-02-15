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
    """

    REGEN_PHRASES = [
        f"{E.FOREST} You pause to catch your breath by a stream...",
        f"{E.FOREST} You find a safe clearing and rest your weary limbs...",
        f"{E.FOREST} The air is calm. You take a moment to meditate...",
        f"{E.FOREST} A faint warmth settles over you as the forest seems to breathe.",
        f"{E.FOREST} You steady your heartbeat and let the world fall quiet.",
        f"{E.FOREST} Rest comes easily as the whisper of leaves soothes your thoughts.",
        f"{E.FOREST} You kneel beneath an ancient oak, drawing strength from its presence.",
        f"{E.FOREST} A soft glow filters through the canopy, easing your muscles.",
        f"{E.FOREST} You close your eyes, letting the earth cradle your exhaustion.",
        f"{E.FOREST} The scent of moss and rain helps clear your mind.",
        f"{E.FOREST} You wash your hands in a cold brook, feeling clarity return.",
        f"{E.FOREST} A moment of stillness blankets you, renewing resolve.",
    ]

    GATHER_PHRASES = [
        f"{E.HERB} You spot a cluster of **{{}}** in the shade. You harvest it.",
        f"{E.HERB} A faint glow draws your attention — **{{}}**, thriving between roots.",
        f"{E.HERB} Beneath fallen leaves, you uncover **{{}}**, fresh and untouched.",
        f"{E.HERB} Hidden in a fold of roots you find **{{}}**; you collect it with care.",
        f"{E.HERB} A sharp herbal scent fills the air as you gather **{{}}**.",
    ]

    LOCATE_PHRASES = [
        f"{E.MAP} After searching the creek, you find **{{}}** hiding behind a rock!",
        f"{E.MAP} Tracks lead you to a hollow trunk — **{{}}** rests within.",
        f"{E.MAP} A soft whimper alerts you. **{{}}** lies curled beneath an outcrop.",
        f"{E.MAP} You follow tiny prints to a burrow and discover **{{}}**.",
        f"{E.MAP} A scrap of cloth catches your eye—behind it, **{{}}** waits.",
    ]

    EXAMINE_PHRASES = [
        f"{E.SCROLL} You find the **{{}}** and study it, noting every detail.",
        f"{E.SCROLL} Strange sigils surround the **{{}}**. You record them.",
        f"{E.SCROLL} You kneel, observing **{{}}** with deliberate focus.",
        f"{E.SCROLL} Dust and carvings frame the object; you catalog clues about **{{}}**.",
    ]

    FALLBACK_QUEST_PHRASES = [
        f"{E.CHECK} You mark **{{}}** in your Guild log.",
        f"{E.CHECK} Your search succeeds — **{{}}** confirmed.",
        f"{E.CHECK} You update the quest record: **{{}}** located.",
        f"{E.CHECK} A clue reveals **{{}}**. You take note.",
        f"{E.CHECK} You carefully bag evidence linked to **{{}}**.",
    ]

    WILD_GATHER_PHRASES = [
        f"{E.HERB} You stumble upon **{{}}** growing wild.",
        f"{E.HERB} A lucky find! You collect **{{}}** from the underbrush.",
        f"{E.HERB} You notice **{{}}** hidden nearby and secure it.",
        f"{E.HERB} The environment yields **{{}}** to your keen eye.",
        f"{E.HERB} You gather **{{}}** while catching your breath.",
    ]

    NO_EVENT_PHRASES = [
        f"{E.FOREST} You search the area but find nothing of interest.",
        f"{E.FOREST} The forest is quiet... too quiet.",
        f"{E.FOREST} A cold wind blows, but no monsters appear.",
        f"{E.FOREST} You follow a game trail, but it runs cold.",
        f"{E.FOREST} Only the rustle of distant branches answers your search.",
        f"{E.FOREST} You sense movement, but it fades before you can track it.",
        f"{E.FOREST} A hollow stillness clings to the woods.",
        f"{E.FOREST} You find old footprints… but whatever made them is long gone.",
        f"{E.FOREST} A faint echo drifts through the trees, revealing nothing.",
        f"{E.FOREST} Shadows stretch between the roots, hiding nothing of value.",
        f"{E.FOREST} A crow watches you silently before taking flight.",
        f"{E.FOREST} Your footsteps crunch through leaves, but no path unfolds.",
        f"{E.FOREST} The air thickens with the scent of rain.",
    ]

    SURGE_PHRASES = [
        f"{E.BUFF} Your health is full, so you push forward with renewed vigor!",
        f"{E.BUFF} Feeling unstoppable, you channel your energy into the hunt.",
        f"{E.BUFF} Vitality courses through you. You focus entirely on finding resources.",
        f"{E.BUFF} You are at peak condition. Your senses sharpen.",
        f"{E.BUFF} With no need to rest, you scour the area with double the effort.",
    ]

    SCAVENGE_AURUM_PHRASES = [
        f"{E.AURUM} You didn't find materials, but you spotted a pouch containing **{{}} Aurum**.",
        f"{E.AURUM} A gleam in the dirt reveals **{{}} Aurum**.",
        f"{E.AURUM} Hidden in a hollow stump, you find **{{}} Aurum**.",
    ]

    SCAVENGE_EXP_PHRASES = [
        f"{E.EXP} The search yielded no items, but you gained **{{}} XP** from studying the area.",
        f"{E.EXP} You find ancient markings, earning **{{}} XP**.",
        f"{E.EXP} Navigating the rough terrain grants you **{{}} XP**.",
    ]

    @staticmethod
    def regeneration() -> list:
        return [random.choice(AdventureEvents.REGEN_PHRASES)]

    @staticmethod
    def quest_event(objective_type: str, target_name: str) -> str:
        if objective_type == "gather":
            return random.choice(AdventureEvents.GATHER_PHRASES).format(target_name)
        if objective_type == "locate":
            return random.choice(AdventureEvents.LOCATE_PHRASES).format(target_name)
        if objective_type in ("examine", "survey"):
            return random.choice(AdventureEvents.EXAMINE_PHRASES).format(target_name)
        return random.choice(AdventureEvents.FALLBACK_QUEST_PHRASES).format(target_name)

    @staticmethod
    def wild_gather_event(item_name: str) -> str:
        return random.choice(AdventureEvents.WILD_GATHER_PHRASES).format(item_name)

    @staticmethod
    def surge_event() -> str:
        return random.choice(AdventureEvents.SURGE_PHRASES)

    @staticmethod
    def scavenge_event(reward_type: str, amount: int) -> str:
        if reward_type == "aurum":
            return random.choice(AdventureEvents.SCAVENGE_AURUM_PHRASES).format(amount)
        return random.choice(AdventureEvents.SCAVENGE_EXP_PHRASES).format(amount)

    @staticmethod
    def no_event_found() -> str:
        return random.choice(AdventureEvents.NO_EVENT_PHRASES)
