"""String helpers."""

SEPARATOR = " "


def normalize(text):
    return SEPARATOR.join(text.split())


def slugify(text):
    return normalize(text).lower().replace(" ", "-")


def titleize(text):
    return " ".join(word.capitalize() for word in normalize(text).split())
