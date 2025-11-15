"""
messages.py

Contains static narrative messages for the Eldoria Quest bot.
All text here is purely descriptive and used for UI displays, embeds, and system prompts.
"""

import textwrap  # <-- 1. ADD THIS IMPORT

WELCOME_TITLE = "Eldoria: The Shattered Veil"

# --- 2. WRAP THE STRING IN textwrap.dedent() ---
WELCOME_MESSAGE = textwrap.dedent(
    """
    In the age after the Sundering—when the Veil between realms fractured like weathered glass—shadows spilled into the waking world. From the haunted barrows of Northgarde to the moonlit boughs of the Lunaris Forest, creatures both ancient and malformed now stalk the roads. Heroes no longer rise from noble bloodlines, but from necessity, for the meek are swallowed by the dark tide.

    **Use the buttons below to learn more about each class.**
    **When your decision is made, carve your name into fate and begin your journey.**
"""
)
# --- 3. ALL CHANGES ARE ABOVE ---
#    - The first paragraph is now one continuous line.
#    - A blank line now correctly separates the two paragraphs.
#    - dedent() removes the leading indentation.
