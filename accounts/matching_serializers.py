from rest_framework import serializers

from .matching import (
    POSITIONS,
    TIER_LOOKUP,
    normalize_position,
    normalize_tier,
)


POSITION_BONUS_MIN = 0
POSITION_BONUS_MAX = 100


class MatchingSettingsSerializer(serializers.Serializer):
    tier_scores = serializers.DictField(
        child=serializers.IntegerField(min_value=0), required=False
    )
    position_bonus = serializers.DictField(
        child=serializers.IntegerField(
            min_value=POSITION_BONUS_MIN, max_value=POSITION_BONUS_MAX
        ),
        required=False,
    )

    def validate(self, attrs):
        if not attrs:
            raise serializers.ValidationError(
                "tier_scores or position_bonus must be provided."
            )

        errors = {}
        normalized = {}
        tier_scores = attrs.get("tier_scores")
        if tier_scores is not None:
            normalized_tiers = {}
            tier_errors = {}
            for key, value in tier_scores.items():
                canonical = normalize_tier(key)
                if canonical is None:
                    tier_errors[key] = "Unknown tier."
                elif canonical in normalized_tiers:
                    tier_errors[key] = "Duplicate tier key."
                else:
                    normalized_tiers[canonical] = value
            if tier_errors:
                errors["tier_scores"] = tier_errors
            normalized["tier_scores"] = normalized_tiers

        position_bonus = attrs.get("position_bonus")
        if position_bonus is not None:
            normalized_positions = {}
            position_errors = {}
            for key, value in position_bonus.items():
                canonical = normalize_position(key)
                if canonical is None:
                    position_errors[key] = "Unknown position."
                elif canonical in normalized_positions:
                    position_errors[key] = "Duplicate position key."
                else:
                    normalized_positions[canonical] = value
            if position_errors:
                errors["position_bonus"] = position_errors
            normalized["position_bonus"] = normalized_positions

        if errors:
            raise serializers.ValidationError(errors)
        return normalized


class MatchingSettingsResponseSerializer(serializers.Serializer):
    tier_scores = serializers.DictField(child=serializers.IntegerField())
    position_bonus = serializers.DictField(child=serializers.IntegerField())


class TeamMatchingParticipantSerializer(serializers.Serializer):
    id = serializers.JSONField()
    name = serializers.CharField(max_length=150)
    primary_position = serializers.CharField(max_length=20)
    primary_tier = serializers.CharField(max_length=30)
    secondary_position = serializers.CharField(max_length=20)
    secondary_tier = serializers.CharField(max_length=30)
    position_preference = serializers.CharField(max_length=20)
    is_guest = serializers.BooleanField()

    def validate_id(self, value):
        if isinstance(value, bool) or not isinstance(value, (int, str)):
            raise serializers.ValidationError("id must be an integer or string.")
        if isinstance(value, str) and not value.strip():
            raise serializers.ValidationError("id must not be empty.")
        return value

    def _validate_position(self, value):
        normalized = normalize_position(value)
        if normalized is None:
            raise serializers.ValidationError(
                f"Position must be one of: {', '.join(POSITIONS)}."
            )
        return normalized

    def _validate_tier(self, value):
        normalized = normalize_tier(value)
        if normalized is None:
            raise serializers.ValidationError(
                f"Tier must be one of: {', '.join(TIER_LOOKUP.values())}."
            )
        return normalized

    def validate_primary_position(self, value):
        return self._validate_position(value)

    def validate_secondary_position(self, value):
        return self._validate_position(value)

    def validate_primary_tier(self, value):
        return self._validate_tier(value)

    def validate_secondary_tier(self, value):
        return self._validate_tier(value)

    def validate_position_preference(self, value):
        normalized = value.strip().lower()
        if normalized not in ("primary", "secondary", "none"):
            raise serializers.ValidationError(
                "position_preference must be primary, secondary, or none."
            )
        return normalized

    def validate(self, attrs):
        if attrs["is_guest"] and attrs["position_preference"] == "none":
            raise serializers.ValidationError(
                {
                    "position_preference": (
                        "Guest participants must choose primary or secondary."
                    )
                }
            )
        return attrs


class TeamMatchingRequestSerializer(serializers.Serializer):
    participants = TeamMatchingParticipantSerializer(many=True)

    def validate_participants(self, participants):
        if len(participants) < 10:
            raise serializers.ValidationError(
                "팀 매칭에는 최소 10명의 참가자가 필요합니다."
            )

        seen_ids = set()
        duplicate_indexes = {}
        for index, participant in enumerate(participants):
            participant_id = (type(participant["id"]).__name__, participant["id"])
            if participant_id in seen_ids:
                duplicate_indexes[index] = {"id": "Participant id must be unique."}
            seen_ids.add(participant_id)
        if duplicate_indexes:
            raise serializers.ValidationError(duplicate_indexes)
        return participants


class MatchedParticipantSerializer(serializers.Serializer):
    id = serializers.JSONField()
    name = serializers.CharField()
    assigned_position = serializers.ChoiceField(choices=POSITIONS)
    used_tier = serializers.CharField()
    score = serializers.FloatField()
    is_guest = serializers.BooleanField()


class TeamMatchSerializer(serializers.Serializer):
    team_number = serializers.IntegerField()
    blue_team = MatchedParticipantSerializer(many=True)
    red_team = MatchedParticipantSerializer(many=True)
    blue_total_score = serializers.FloatField()
    red_total_score = serializers.FloatField()
    score_difference = serializers.FloatField()
    balance_score = serializers.FloatField(min_value=0, max_value=100)


class TeamMatchingResponseSerializer(serializers.Serializer):
    matches = TeamMatchSerializer(many=True)
    unmatched_participants = TeamMatchingParticipantSerializer(many=True)


class DetailErrorSerializer(serializers.Serializer):
    detail = serializers.CharField(required=False)
    participants = serializers.JSONField(required=False)


class MatchingSettingsErrorSerializer(serializers.Serializer):
    tier_scores = serializers.JSONField(required=False)
    position_bonus = serializers.JSONField(required=False)
    non_field_errors = serializers.ListField(
        child=serializers.CharField(), required=False
    )
