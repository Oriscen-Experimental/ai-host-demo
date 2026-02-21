import random


def make_pairs(participant_ids: list[str]) -> list[list[str]]:
    """Split participants into pairs. If odd number, last group has 3."""
    ids = list(participant_ids)
    random.shuffle(ids)
    pairs = []
    i = 0
    while i < len(ids):
        if len(ids) - i == 3:
            pairs.append(ids[i:i+3])
            i += 3
        elif len(ids) - i >= 2:
            pairs.append(ids[i:i+2])
            i += 2
        else:
            # Single person left, add to last group
            if pairs:
                pairs[-1].append(ids[i])
            else:
                pairs.append([ids[i]])
            i += 1
    return pairs


def make_trios(participant_ids: list[str]) -> list[list[str]]:
    """Split participants into groups of 3. Remainder handled gracefully."""
    ids = list(participant_ids)
    random.shuffle(ids)
    groups = []
    i = 0
    n = len(ids)

    if n <= 3:
        return [ids]

    remainder = n % 3
    if remainder == 0:
        while i < n:
            groups.append(ids[i:i+3])
            i += 3
    elif remainder == 1:
        # Make one group of 4, rest groups of 3
        groups.append(ids[0:4])
        i = 4
        while i < n:
            groups.append(ids[i:i+3])
            i += 3
    else:  # remainder == 2
        # Make one group of 2, rest groups of 3
        while i < n - 2:
            groups.append(ids[i:i+3])
            i += 3
        groups.append(ids[i:])

    return groups


def assign_help_pairs(participant_ids: list[str]) -> dict[str, str]:
    """
    Assign each person someone to respond to.
    Returns {responder_id: requester_id}
    Ensures everyone gets exactly 1 response.
    """
    ids = list(participant_ids)
    n = len(ids)
    if n < 2:
        return {}

    random.shuffle(ids)
    assignments = {}
    for i in range(n):
        responder = ids[i]
        requester = ids[(i + 1) % n]
        assignments[responder] = requester
    return assignments
