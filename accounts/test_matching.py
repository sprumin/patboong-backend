from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from .models import (
    DEFAULT_POSITION_BONUS,
    DEFAULT_TIER_SCORES,
    MatchingRecord,
    MatchingRun,
    MatchingSettings,
)


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
        matching_run = MatchingRun.objects.get(id=response.data["matching_run_id"])
        self.assertEqual(matching_run.owner, self.user)
        self.assertEqual(matching_run.participants[0]["primary_position"], "top")
        self.assertEqual(matching_run.participants[0]["primary_tier"], "Gold II")

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


class MatchingHistoryAPITests(TestCase):
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
        return [
            self.participant(index, position)
            for index, position in enumerate(
                ("top", "jungle", "mid", "adc", "support") * 2,
                start=1,
            )
        ]

    def run_matching(self, participants=None):
        self.client.force_authenticate(self.user)
        return self.client.post(
            "/api/accounts/team-matching/",
            {"participants": participants or self.ten_participants()},
            format="json",
        )

    def test_recent_participants_returns_empty_when_no_run_exists(self):
        self.client.force_authenticate(self.user)

        response = self.client.get(
            "/api/accounts/team-matching/recent-participants/"
        )

        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.data["matching_run_id"])
        self.assertIsNone(response.data["created_at"])
        self.assertEqual(response.data["participants"], [])

    def test_recent_participants_preserves_order_guest_and_current_user(self):
        participants = self.ten_participants()
        participants[0]["id"] = self.user.id
        participants[9] = self.participant(
            "guest-uuid", "support", is_guest=True, tier="Silver II"
        )
        participants[9]["secondary_tier"] = "Silver IV"
        run_response = self.run_matching(participants)

        response = self.client.get(
            "/api/accounts/team-matching/recent-participants/"
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            str(response.data["matching_run_id"]),
            str(run_response.data["matching_run_id"]),
        )
        self.assertEqual(
            [item["id"] for item in response.data["participants"]],
            [item["id"] for item in participants],
        )
        self.assertIs(response.data["participants"][0]["is_current_user"], True)
        self.assertIs(response.data["participants"][9]["is_guest"], True)
        self.assertIs(response.data["participants"][9]["is_current_user"], False)
        self.assertEqual(response.data["participants"][9]["primary_tier"], "Silver II")

    def test_recent_participants_is_isolated_by_owner_and_uses_latest_run(self):
        first = self.ten_participants()
        first[0]["name"] = "First#KR1"
        self.run_matching(first)
        second = self.ten_participants()
        second[0]["name"] = "Second#KR1"
        latest = self.run_matching(second)

        other = User.objects.create_user(
            username="other",
            password="Password123!",
            email="other@example.com",
        )
        self.client.force_authenticate(other)
        other_response = self.client.get(
            "/api/accounts/team-matching/recent-participants/"
        )
        self.client.force_authenticate(self.user)
        owner_response = self.client.get(
            "/api/accounts/team-matching/recent-participants/"
        )

        self.assertEqual(other_response.data["participants"], [])
        self.assertEqual(owner_response.data["participants"][0]["name"], "Second#KR1")
        self.assertEqual(
            str(owner_response.data["matching_run_id"]),
            str(latest.data["matching_run_id"]),
        )

    def test_save_list_and_detail_preserve_original_participants_and_teams(self):
        participants = self.ten_participants()
        participants[0]["id"] = self.user.id
        participants[9] = self.participant(
            "guest-uuid", "support", is_guest=True, tier="Silver II"
        )
        run_response = self.run_matching(participants)

        save_response = self.client.post(
            "/api/accounts/team-matching/records/",
            {
                "matching_run_id": run_response.data["matching_run_id"],
                "team_number": 1,
            },
            format="json",
        )
        list_response = self.client.get("/api/accounts/team-matching/records/")
        detail_response = self.client.get(
            f"/api/accounts/team-matching/records/{save_response.data['id']}/"
        )

        self.assertEqual(save_response.status_code, 201)
        self.assertEqual(list_response.status_code, 200)
        self.assertEqual(len(list_response.data["results"]), 1)
        summary = list_response.data["results"][0]
        self.assertEqual(summary["participant_count"], 10)
        self.assertIs(summary["contains_current_user"], True)
        self.assertEqual(detail_response.status_code, 200)
        self.assertEqual(len(detail_response.data["participants"]), 10)
        self.assertEqual(len(detail_response.data["blue_team"]), 5)
        self.assertEqual(len(detail_response.data["red_team"]), 5)
        self.assertIs(detail_response.data["contains_current_user"], True)
        guest = next(
            item
            for item in detail_response.data["participants"]
            if item["id"] == "guest-uuid"
        )
        self.assertIs(guest["is_guest"], True)
        self.assertEqual(guest["primary_tier"], "Silver II")
        self.assertEqual(MatchingRecord.objects.count(), 1)

    def test_record_without_current_user_is_visible_to_owner_but_flagged_false(self):
        participants = [
            self.participant(index + 100, position)
            for index, position in enumerate(
                ("top", "jungle", "mid", "adc", "support") * 2, start=1
            )
        ]
        run_response = self.run_matching(participants)
        saved = self.client.post(
            "/api/accounts/team-matching/records/",
            {
                "matching_run_id": run_response.data["matching_run_id"],
                "team_number": 1,
            },
            format="json",
        )

        detail = self.client.get(
            f"/api/accounts/team-matching/records/{saved.data['id']}/"
        )

        self.assertEqual(detail.status_code, 200)
        self.assertIs(detail.data["contains_current_user"], False)

    def test_other_user_cannot_access_saved_record(self):
        run_response = self.run_matching()
        saved = self.client.post(
            "/api/accounts/team-matching/records/",
            {
                "matching_run_id": run_response.data["matching_run_id"],
                "team_number": 1,
            },
            format="json",
        )
        other = User.objects.create_user(
            username="other",
            password="Password123!",
            email="other@example.com",
        )
        self.client.force_authenticate(other)

        detail = self.client.get(
            f"/api/accounts/team-matching/records/{saved.data['id']}/"
        )
        listing = self.client.get("/api/accounts/team-matching/records/")

        self.assertEqual(detail.status_code, 404)
        self.assertEqual(listing.data["results"], [])


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
