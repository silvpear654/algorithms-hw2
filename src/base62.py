"""Base62 conversion using the alphabet 0-9, a-z, A-Z."""

ALPHABET = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
BASE = len(ALPHABET)


def encode(number: int) -> str:
    if isinstance(number, bool) or not isinstance(number, int) or number < 0:
        raise ValueError("number must be a non-negative integer")
    if number == 0:
        return "0"

    encoded = []
    while number:
        number, remainder = divmod(number, BASE)
        encoded.append(ALPHABET[remainder])
    return "".join(reversed(encoded))


def decode(code: str) -> int:
    if not isinstance(code, str) or not code:
        raise ValueError("code must be a non-empty base62 string")

    number = 0
    for character in code:
        digit = ALPHABET.find(character)
        if digit < 0:
            raise ValueError(f"invalid base62 character: {character!r}")
        number = number * BASE + digit
    return number
