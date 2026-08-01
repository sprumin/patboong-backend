from itertools import combinations, product

from .models import DEFAULT_POSITION_BONUS, DEFAULT_TIER_SCORES, MatchingSettings


POSITIONS = tuple(DEFAULT_POSITION_BONUS)
POSITION_LOOKUP = {position.casefold(): position for position in POSITIONS}
TIER_LOOKUP = {tier.casefold(): tier for tier in DEFAULT_TIER_SCORES}

TEAM_SIZE = 5
MATCH_SIZE = TEAM_SIZE * 2
MAX_BALANCE_SCORE = 100
# Fix participant 0 on blue to skip equivalent blue/red color-swapped candidates.
TEAM_INDEX_COMBINATIONS = tuple(
    (0, *indexes)
    for indexes in combinations(range(1, MATCH_SIZE), TEAM_SIZE - 1)
)


def _normalized_key(value):
    return " ".join(str(value).strip().split()).casefold()


def normalize_position(value):
    return POSITION_LOOKUP.get(_normalized_key(value))


def normalize_tier(value):
    return TIER_LOOKUP.get(_normalized_key(value))


def complete_settings(settings=None):
    tier_scores = DEFAULT_TIER_SCORES.copy()
    position_bonus = DEFAULT_POSITION_BONUS.copy()
    if settings is not None:
        tier_scores.update(
            {
                key: value
                for key, value in (settings.tier_scores or {}).items()
                if key in DEFAULT_TIER_SCORES
                and isinstance(value, int)
                and not isinstance(value, bool)
                and value >= 0
            }
        )
        position_bonus.update(
            {
                key: value
                for key, value in (settings.position_bonus or {}).items()
                if key in DEFAULT_POSITION_BONUS
                and isinstance(value, int)
                and not isinstance(value, bool)
                and 0 <= value <= 100
            }
        )
    return {
        "tier_scores": tier_scores,
        "position_bonus": position_bonus,
    }


def get_matching_settings():
    return complete_settings(MatchingSettings.objects.filter(pk=1).first())


def calculate_score(tier, position, settings):
    tier_score = settings["tier_scores"][tier]
    bonus = settings["position_bonus"][position]
    score = round(tier_score * (1 + bonus / 100), 2)
    return int(score) if score.is_integer() else score


def calculate_balance_score(blue_total, red_total):
    highest_total = max(blue_total, red_total)
    if highest_total == 0:
        return MAX_BALANCE_SCORE
    difference = abs(blue_total - red_total)
    score = MAX_BALANCE_SCORE * (1 - difference / highest_total)
    return round(max(0, min(MAX_BALANCE_SCORE, score)), 2)


def _participant_options(participant, settings):
    primary = {
        **participant,
        "assigned_position": participant["primary_position"],
        "used_tier": participant["primary_tier"],
    }
    secondary = {
        **participant,
        "assigned_position": participant["secondary_position"],
        "used_tier": participant["secondary_tier"],
    }
    preference = participant["position_preference"]
    if preference == "primary":
        choices = [primary]
    elif preference == "secondary":
        choices = [secondary]
    else:
        choices = [primary, secondary]
        if (
            primary["assigned_position"] == secondary["assigned_position"]
            and primary["used_tier"] == secondary["used_tier"]
        ):
            choices = [primary]

    for choice in choices:
        choice["score"] = calculate_score(
            choice["used_tier"], choice["assigned_position"], settings
        )
    return choices


def _position_coverage(team):
    return len({participant["assigned_position"] for participant in team})


def _response_participant(participant):
    return {
        "id": participant["id"],
        "name": participant["name"],
        "assigned_position": participant["assigned_position"],
        "used_tier": participant["used_tier"],
        "score": participant["score"],
        "is_guest": participant["is_guest"],
    }


def create_balanced_match(participants, settings, team_number):
    option_groups = [
        _participant_options(participant, settings) for participant in participants
    ]
    best_result = None
    best_objective = None

    for assigned_participants in product(*option_groups):
        for blue_indexes in TEAM_INDEX_COMBINATIONS:
            blue_index_set = set(blue_indexes)
            blue_team = [
                participant
                for index, participant in enumerate(assigned_participants)
                if index in blue_index_set
            ]
            red_team = [
                participant
                for index, participant in enumerate(assigned_participants)
                if index not in blue_index_set
            ]
            position_coverage = _position_coverage(blue_team) + _position_coverage(
                red_team
            )
            blue_total = round(sum(item["score"] for item in blue_team), 2)
            red_total = round(sum(item["score"] for item in red_team), 2)
            score_difference = round(abs(blue_total - red_total), 2)
            objective = (-position_coverage, score_difference)

            if best_objective is None or objective < best_objective:
                best_objective = objective
                best_result = {
                    "team_number": team_number,
                    "blue_team": [
                        _response_participant(item) for item in blue_team
                    ],
                    "red_team": [_response_participant(item) for item in red_team],
                    "blue_total_score": blue_total,
                    "red_total_score": red_total,
                    "score_difference": score_difference,
                    "balance_score": calculate_balance_score(
                        blue_total, red_total
                    ),
                }

    return best_result


def create_team_matches(participants, settings):
    match_count = len(participants) // MATCH_SIZE
    matches = []
    for index in range(match_count):
        start = index * MATCH_SIZE
        group = participants[start : start + MATCH_SIZE]
        matches.append(create_balanced_match(group, settings, index + 1))
    return {
        "matches": matches,
        "unmatched_participants": participants[match_count * MATCH_SIZE :],
    }
