# Quest Design: The Silent Witness

**Designer:** Questweaver
**Status:** Draft
**Target Rank:** E

## Overview
A two-part investigation quest exploring the infiltration of the Guild by a shadow cult known as the "Veil-bound". This quest emphasizes narrative through item descriptions and environmental storytelling rather than direct combat grinding.

## Quest 1: The Silent Witness - Evidence
**Quest Giver:** Archivist Thorne (Library)
**Location:** Willowcreek Outskirts (Town/Guild Environs)
**Prerequisites:** Rank E

### Narrative Hook
Archivist Thorne, usually calm and composed, is visibly shaken. A page from a forbidden tome regarding the Sundering has been torn out. He suspects a traitor within the Guild is communicating with outside forces.

### Dialogue Script
**Thorne:** "Shh. Keep your voice down, initiate. See this binding? A page is missing. A page that details the rituals of the Veil-weavers. It didn't fall out; it was *taken*. I need you to quietly search the grounds. If there is a traitor, they likely left a trail."

### Objectives
1.  **Examine: Torn Journal Page**
    *   *Context:* Found near the edge of town, as if dropped in haste.
    *   *Flavor Text:* "You find a crumpled parchment caught in the brambles. It's covered in frantic scribbles about 'The Weaver's Return'."
2.  **Examine: discarded Dagger**
    *   *Context:* Hidden near the old training posts.
    *   *Flavor Text:* "A dagger with a twisted, serpentine hilt lies half-buried in the mud. The blade hums with a faint, nauseating energy."
3.  **Locate: Hooded Figure**
    *   *Context:* A contact was spotted near the bridge.
    *   *Flavor Text:* "You spot a figure in grey robes slipping into the shadows. They leave behind a pouch of strange, glowing dust."

### Completion
**Thorne:** "Let me see... The serpentine hilt. I feared this. The 'Veil-bound'. They are not just myths. They are here. And if they have the page, they are heading for the Thicket to complete the ritual."

**Rewards:**
- Experience: 400
- Aurum: 100
- Item: "Scholar's Draught"

---

## Quest 2: The Silent Witness - Justice
**Quest Giver:** Archivist Thorne
**Location:** Whispering Thicket
**Prerequisites:** Completion of "The Silent Witness - Evidence"

### Narrative Hook
Thorne has identified the destination of the traitor/spy. They have fled to the Whispering Thicket to perform a ritual using the stolen knowledge.

### Dialogue Script
**Thorne:** "There is no time to summon the Council. You must go. The traitor has fled to the Whispering Thicket. If they complete the ritual described on that page, the corruption will spread to the Guild itself. Silence them."

### Objectives
1.  **Defeat: Veil-bound Assassin**
    *   *Context:* The spy reveals their true form when cornered.
    *   *Flavor Text:* "As the assassin falls, their body dissolves into black mist, leaving only the stolen page behind."

### Completion
**Thorne:** "You have it? Good. Burn it. No... wait. I will secure it. You have done the Guild a great service today. But speak of this to no one. Panic is a sharper blade than any dagger."

**Rewards:**
- Experience: 800
- Aurum: 300
- Item: "Wardkeeper's Vial"

## Technical Implementation
- **New Quest Fields:**
    - `prerequisites`: List of Quest IDs.
    - `flavor_text`: Dictionary mapping "Objective Type:Target" to custom string.
- **Event System:** Update `EventHandler` to check `flavor_text` before using default phrases.
