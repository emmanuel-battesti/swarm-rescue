from typing import Tuple


def id_to_pixel(uid: int) -> Tuple[int, int, int]:
    """
    Convert a unique integer ID to an RGB color tuple.

    Args:
        uid (int): Unique identifier.

    Returns:
        Tuple[int, int, int]: RGB color tuple.
    """
    id_0 = uid & 255
    id_1 = (uid >> 8) & 255
    id_2 = (uid >> 16) & 255

    return id_0, id_1, id_2
