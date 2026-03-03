# 📓 Timeweaver Journal

## Identity
I am Timeweaver ⏳, the visionary architect of time and flow in Eldoria Quest. My focus is on ensuring that idle/auto-progression feels earned, risky, and deeply integrated into the dark fantasy survival fabric of the world. Time is a precious resource; how players spend it should carry weight.

## Core Philosophy
- **Time is the ultimate resource.** Respect it in both design and player experience.
- **Auto doesn't mean mindless.** Players should still make meaningful choices (where, how long, what to bring).
- **Risk and reward must be palpable.** Longer adventures should feel genuinely dangerous.
- **The world still breathes.** Even on auto, Eldoria's dark survival tone must persist.
- **Players should feel invested.** Coming back to find results should be exciting, not mundane.

## Design Log: Auto-Adventure Overhaul

### The Challenge
The user wants to transition Eldoria Quest from a purely manual, turn-based exploration system to one where progression can happen asynchronously via time-based expeditions. This is a massive shift. The challenge isn't just "make an idle game," it's "make an idle game that feels like a hardcore survival RPG."

### Inspirations
1.  **Melvor Idle:** The gold standard for translating deep RPG mechanics (like RuneScape) into a purely menu-driven, idle experience. I love how preparation (crafting food, equipping the right gear) is required *before* you can successfully idle a hard dungeon overnight.
2.  **Darkest Dungeon:** The "Expedition" feel. You pack your bags, choose a location, and hope your party survives. If they die, the penalties are severe. I want that tension when a player checks their 24-hour campaign results.
3.  **Standard Discord RPGs (Epic RPG, Karuta):** They rely heavily on commands and timers. The "One UI Policy" of Eldoria Quest is a great constraint here—it prevents the channel spam that usually plagues these bots, forcing a cleaner, more modern interface (embeds and buttons).

### Key Decisions
*   **The "Tick" System:** Simulating every turn of combat for hundreds of offline players would melt the bot's CPU. I've designed a deterministic abstraction. We calculate an "Offensive Rating" and "Defensive Rating" and resolve combat mathematically in batches (ticks).
*   **The Fatigue Debuff:** Why not just do 24h adventures all the time? Fatigue. As an adventure stretches on, the character gets weaker, taking more damage. This forces players to either stick to shorter, safer runs or heavily invest in top-tier supplies to survive the 24h campaigns.
*   **The Penalty:** Death *must* hurt. Losing all gathered loot and a chunk of Aurum ensures players don't just blindly send characters into the Abyss without preparation.

### Anticipated Roadblocks
*   **Database Contention:** The `SystemSmith` will need to ensure the background scheduler processes completions efficiently. If 500 players all finish a 2h adventure at the same time, the DB updates need to be batched or queued properly.
*   **Balancing the Economy:** `GameBalancer` has a tough job. If auto-adventuring is too lucrative, manual play dies. I've suggested a flat 0.8x multiplier on auto-loot drops to keep active play optimal, but this will need testing.
*   **One UI Policy:** Updating the status message in real-time (`/adventure status`) is tricky if the bot restarts. The state must be entirely driven by the database.

### Next Steps
The design document `.Jules/timeweaver_design.md` is complete. The ball is now in the court of the other agents to implement the database, scheduler, and combat abstraction.
