"""
Constants for the phoneme density game
"""

# Master phoneme list - edit this list to change phonemes throughout the app
PHONEME_CHOICES = [
    ('r', '/r/ sound (as in "red", "car")'),
    ('s', '/s/ sound (as in "sun", "class")'),
    ('t', '/t/ sound (as in "top", "cat")'),
    ('n', '/n/ sound (as in "no", "can")'),
    ('l', '/l/ sound (as in "love", "call")'),
    ('k', '/k/ sound (as in "cat", "back", "key")'),
    ('f', '/f/ sound (as in "fish", "phone", "laugh")'),
    ('w', '/w/ sound (as in "water", "queen")'),
    ('y', '/j/ y sound (as in "yes", "onion")'),
]

# English phoneme frequencies (approximate percentages in typical English text)
# Based on linguistic research data - corresponds to PHONEME_CHOICES
ENGLISH_PHONEME_FREQUENCIES = {
    'r': 6.2,
    's': 6.3,
    't': 9.1,
    'n': 6.8,
    'l': 4.0,
    'k': 3.6,
    'f': 2.2,
    'w': 2.4,
    'y': 2.0,
}

# Convenience function to get just the phoneme codes
def get_phoneme_codes():
    """Return list of just the phoneme codes (e.g., ['r', 's', 't', ...])"""
    return [choice[0] for choice in PHONEME_CHOICES]

# Convenience function to get phoneme display names
def get_phoneme_display_names():
    """Return dict mapping codes to display names"""
    return dict(PHONEME_CHOICES)
