"""
game_systems/data/narrative_data.py

Contains atmospheric flavor text for mission reports and outcomes.
Used by StoryWeaver to enhance immersion.
"""

MISSION_FLAVOR_TEXT = {
    "forest_outskirts": [
        "The canopy breaks, revealing the familiar walls of Astraeon. The forest's edge feels tame now compared to what lies beyond.",
        "You emerge from the treeline, boots caked in mud but spirit unbroken. The safety of the Guild Hall beckons.",
        "Birdsong replaces the chittering of monsters as you cross back into civilized lands.",
        "The sun warms your back as you leave the tree line. It was a good hunt.",
    ],
    "whispering_thicket": [
        "The oppressive silence of the Thicket fades, replaced by the distant bustle of the city. You breathe easier.",
        "Thorns still cling to your cloak, souvenirs of a path less traveled. You’ve survived the whispers for now.",
        "Light filters through the leaves, no longer twisted by the Thicket's gloom. You made it out.",
        "The shadows of the Thicket retreat, unable to follow you into the open fields.",
    ],
    "deepgrove_roots": [
        "You shake the rot from your boots. The Deepgrove's corruption runs deep, but it could not claim you today.",
        "The air tastes sweet after the stagnant breath of the Roots. You return to the living world.",
        "Ancient roots uncoil from your memory as the city gates come into view. You have walked where few dare.",
        "The tangled undergrowth is behind you now, but the smell of damp earth lingers on your gear.",
    ],
    "shrouded_fen": [
        "The mist clings to you like a second skin, slowly burning off in the morning sun. You have escaped the Fen.",
        "Mud-slicked and weary, you trudge onto solid ground. The marsh could not pull you down.",
        "The haunting cries of the Fen fade into memory. Astraeon's stone walls never looked so welcoming.",
        "You scrape the mire from your armor. The Fen takes many, but it did not take you.",
    ],
    "sunken_grotto": [
        "You emerge from the depths, eyes adjusting to the surface light. The crushing weight of the Grotto is gone.",
        "Salt crusts on your skin and gear. The ocean's secrets remain below, but its treasures are yours.",
        "The roar of the tides is replaced by the roar of the city. You have returned from the abyss.",
        "Dripping wet and shivering, you step onto dry land. The Grotto's cold grip has finally loosened.",
    ],
    "crystal_caverns": [
        "The hum of the crystals still resonates in your bones. You step out of the glow and into the sun.",
        "Dust of crushed gems sparkles on your cloak. The beauty of the Caverns was deadly, but you survived.",
        "Your eyes ache from the subterranean brilliance. The natural light of the surface feels mercifully dim.",
        "You carry the chill of the deep earth with you, along with pockets full of potential.",
    ],
    "clockwork_halls": [
        "The grinding gears fall silent behind you. The relentless ticking of the Halls is finally gone.",
        "You wipe grease and steam from your face. The machine world continues without you, but you have its spoils.",
        "The rhythm of the city feels chaotic after the precision of the Halls. You have returned to the organic world.",
        "Heat radiates from your armor, a lingering memory of the steam vents. You made it out before the pressure peaked.",
    ],
    "molten_caldera": [
        "The ash on your cloak is a stark reminder of the fire you walked through. The cool air is a blessing.",
        "You leave the inferno behind, the heat still radiating from your gear. Survival was a trial by fire.",
        "The ground beneath your feet feels blessedly cool. You have walked the edge of the volcano and lived.",
        "Smoke trails from your pack as you return. The Caldera demanded a price, but you paid it in sweat, not blood.",
    ],
    "frostfall_expanse": [
        "The biting wind dies down, leaving your face numb but your spirit intact. You have conquered the cold.",
        "Frost melts from your armor as you approach the city gates. The Expanse's icy grip could not hold you.",
        "Your breath no longer clouds the air. You have returned from the frozen wastes to the warmth of the hearth.",
        "Snow crunches beneath your boots one last time before you hit the cobblestones. You survived the whiteout.",
    ],
    "void_sanctum": [
        "You step back into reality, the silence of the Void still ringing in your ears. The world feels... fragile.",
        "The darkness clings to your shadow, a cold reminder of the abyss you just escaped.",
        "Colors seem too bright, sounds too loud. You have looked into the nothingness and returned.",
        "You feel a strange lightness, as if gravity is welcoming you back. The Void has let you go... for now.",
    ],
    "guild_arena": [
        "The cheers (or jeers) of the crowd fade. You step out of the ring, your test concluded.",
        "Sand pours from your boots. The Arena has measured your worth.",
        "You sheathe your weapon, the adrenaline of the duel slowly fading. The Examiner has seen enough.",
    ],
}

OUTCOME_FLAVOR_TEXT = {
    "level_up": [
        "Something has shifted within you. The battles have forged you into something sharper, stronger.",
        "You feel the weight of your experience settling in. You are not the same adventurer who left the gates.",
        "Power hums beneath your skin. You have ascended a step on the long road to glory.",
        "The world looks different now. Or perhaps it is you who has changed.",
    ],
    "default": [
        "You return from the wilds, weary but burdened with spoils.",
        "Another expedition concludes. The Guild will be eager to catalog your findings.",
        "The road back is long, but the weight of your pack makes the journey worth it.",
        "Survival is its own reward, but the loot certainly helps.",
        "You make your way back to the Guild Hall, another tale added to your legend.",
    ],
}
