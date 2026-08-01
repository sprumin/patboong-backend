from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from .models import DEFAULT_POSITION_BONUS, DEFAULT_TIER_SCORES, MatchingSettings


User = get_user_model()


class MatchingSettingsAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.admin = User.objects.create_superuser(
            username="admin",
            password="Password123!",
            email="admin@example.com",
        )
        self.user = User.objects.create_user(
            username="user",
            password="Password123!",
            email="user@example.com",
        )

    def test_matching_settings_requires_admin(self):
        unauthenticated = self.client.get("/api/admin/matching-settings/")
        self.client.force_authenticate(self.user)
        forbidden = self.client.get("/api/admin/matching-settings/")

        self.assertEqual(unauthenticated.status_code, 401)
        self.assertEqual(forbidden.status_code, 403)

    def test_get_returns_complete_defaults_without_saved_settings(self):
        self.client.force_authenticate(self.admin)

        response = self.client.get("/api/admin/matching-settings/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["tier_scores"], DEFAULT_TIER_SCORES)
        self.assertEqual(response.data["position_bonus"], DEFAULT_POSITION_BONUS)
        self.assertFalse(MatchingSettings.objects.exists())

    def test_put_safely_merges_and_persists_partial_settings(self):
        self.client.force_authenticate(self.admin)

        response = self.client.put(
            "/api/admin/matching-settings/",
            {
                "tier_scores": {"gold ii": 825},
                "position_bonus": {"JUNGLE": 5},
            },
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["tier_scores"]["Gold II"], 825)
        self.assertEqual(response.data["tier_scores"]["Iron IV"], 100)
        self.assertEqual(response.data["position_bonus"]["jungle"], 5)
        self.assertEqual(response.data["position_bonus"]["support"], 0)
        settings = MatchingSettings.objects.get(pk=1)
        self.assertEqual(settings.tier_scores, response.data["tier_scores"])

    def test_put_rejects_unknown_keys_and_out_of_range_values(self):
        self.client.force_authenticate(self.admin)

        unknown = self.client.put(
            "/api/admin/matching-settings/",
            {
                "tier_scores": {"Mythic": 2000},
                "position_bonus": {"roamer": 10},
            },
            format="json",
        )
        invalid_value = self.client.put(
            "/api/admin/matching-settings/",
            {"position_bonus": {"top": 101}},
            format="json",
        )

        self.assertEqual(unknown.status_code, 400)
        self.assertIn("Mythic", unknown.data["tier_scores"])
        self.assertIn("roamer", unknown.data["position_bonus"])
        self.assertEqual(invalid_value.status_code, 400)
        self.assertIn("top", invalid_value.data["position_bonus"])


class TeamMatchingAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="owner",
            password="Password123!",
            email="owner@example.com",
        )

    def participant(
        self,
        participant_id,
        position,
        *,
        preference="primary",
        is_guest=False,
        tier="Gold II",
    ):
        secondary = "mid" if position != "mid" else "adc"
        return {
            "id": participant_id,
            "name": f"Player{participant_id}#KR1",
            "primary_position": position,
            "primary_tier": tier,
            "secondary_position": secondary,
            "secondary_tier": "Gold IV",
            "position_preference": preference,
            "is_guest": is_guest,
        }

    def ten_participants(self):
        positions = ("top", "jungle", "mid", "adc", "support") * 2
        return [
            self.participant(index, position)
            for index, position in enumerate(positions, start=1)
        ]

    def test_team_matching_requires_authentication(self):
        response = self.client.post(
            "/api/accounts/team-matching/",
            {"participants": self.ten_participants()},
            format="json",
        )

        self.assertEqual(response.status_code, 401)

    def test_team_matching_requires_at_least_ten_participants(self):
        self.client.force_authenticate(self.user)

        response = self.client.post(
            "/api/accounts/team-matching/",
            {"participants": self.ten_participants()[:9]},
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.data,
            {"detail": "팀 매칭에는 최소 10명의 참가자가 필요합니다."},
        )

    def test_creates_balanced_five_player_teams_with_standardized_values(self):
        self.client.force_authenticate(self.user)
        participants = self.ten_participants()
        participants[0]["primary_position"] = " TOP "
        participants[0]["primary_tier"] = "gold ii"

        response = self.client.post(
            "/api/accounts/team-matching/",
            {"participants": participants},
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        match = response.data["matches"][0]
        self.assertEqual(len(match["blue_team"]), 5)
        self.assertEqual(len(match["red_team"]), 5)
        self.assertEqual(
            {item["assigned_position"] for item in match["blue_team"]},
            {"top", "jungle", "mid", "adc", "support"},
        )
        self.assertEqual(
            {item["assigned_position"] for item in match["red_team"]},
            {"top", "jungle", "mid", "adc", "support"},
        )
        self.assertEqual(match["score_difference"], 0)
        self.assertEqual(match["balance_score"], 100)

    def test_uses_saved_position_bonus_in_score(self):
        MatchingSettings.objects.create(position_bonus={"jungle": 5})
        self.client.force_authenticate(self.user)

        response = self.client.post(
            "/api/accounts/team-matching/",
            {"participants": self.ten_participants()},
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        all_players = (
            response.data["matches"][0]["blue_team"]
            + response.data["matches"][0]["red_team"]
        )
        jungle_scores = [
            player["score"]
            for player in all_players
            if player["assigned_position"] == "jungle"
        ]
        self.assertEqual(jungle_scores, [840, 840])

    def test_guest_cannot_use_none_position_preference(self):
        self.client.force_authenticate(self.user)
        participants = self.ten_participants()
        participants[0]["is_guest"] = True
        participants[0]["position_preference"] = "none"

        response = self.client.post(
            "/api/accounts/team-matching/",
            {"participants": participants},
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("position_preference", response.data["participants"][0])

    def test_none_preference_uses_position_that_improves_team_composition(self):
        self.client.force_authenticate(self.user)
        positions = (
            "top",
            "top",
            "jungle",
            "jungle",
            "mid",
            "mid",
            "adc",
            "adc",
            "support",
        )
        participants = [
            self.participant(index, position)
            for index, position in enumerate(positions, start=1)
        ]
        flexible = self.participant(10, "top", preference="none")
        flexible["secondary_position"] = "support"
        participants.append(flexible)

        response = self.client.post(
            "/api/accounts/team-matching/",
            {"participants": participants},
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        match = response.data["matches"][0]
        all_players = match["blue_team"] + match["red_team"]
        assigned = next(player for player in all_players if player["id"] == 10)
        self.assertEqual(assigned["assigned_position"], "support")

    def test_returns_extra_participants_as_unmatched(self):
        self.client.force_authenticate(self.user)
        participants = self.ten_participants() + [
            self.participant(11, "top", is_guest=True)
        ]

        response = self.client.post(
            "/api/accounts/team-matching/",
            {"participants": participants},
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["matches"]), 1)
        self.assertEqual(response.data["unmatched_participants"][0]["id"], 11)


class ProfileAdminFlagTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_profile_returns_boolean_admin_flag_and_user_id(self):
        regular = User.objects.create_user(
            username="regular",
            password="Password123!",
            email="regular@example.com",
        )
        admin = User.objects.create_superuser(
            username="admin",
            password="Password123!",
            email="admin@example.com",
        )

        self.client.force_authenticate(regular)
        regular_response = self.client.get("/api/accounts/profile/")
        self.client.force_authenticate(admin)
        admin_response = self.client.get("/api/accounts/profile/")

        self.assertEqual(regular_response.data["user_id"], "regular")
        self.assertIs(regular_response.data["is_admin"], False)
        self.assertEqual(admin_response.data["user_id"], "admin")
        self.assertIs(admin_response.data["is_admin"], True)
