from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from .models import Friendship


User = get_user_model()


class AccountsAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def _create_user(self, username, puuid):
        return User.objects.create_user(
            username=username,
            password="Password123!",
            email=f"{username}@example.com",
            riot_game_name=username,
            riot_tag_line="KR1",
            riot_server="ASIA",
            puuid=puuid,
        )

    @patch("accounts.serializers.RiotClient.get_account_by_riot_id")
    def test_register_verifies_and_stores_riot_account(self, get_account):
        get_account.return_value = {
            "puuid": "registered-puuid",
            "gameName": "VerifiedName",
            "tagLine": "KR1",
        }
        response = self.client.post(
            "/api/accounts/register/",
            {
                "user_id": "new-user",
                "user_pw": "Password123!",
                "email": "new@example.com",
                "main_line": "mid",
                "sub_line": "top",
                "tier_top": "gold",
                "tier_jungle": "gold",
                "tier_mid": "gold",
                "tier_adc": "gold",
                "tier_support": "gold",
                "question": "pet",
                "answer": "answer",
                "service_terms": True,
                "privacy_terms": True,
                "age_terms": True,
                "riot_game_name": "InputName",
                "riot_tag_line": "KR1",
                "riot_server": "ASIA",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 201)
        user = User.objects.get(username="new-user")
        self.assertEqual(user.puuid, "registered-puuid")
        self.assertEqual(user.riot_game_name, "VerifiedName")
        self.assertIsNotNone(user.verified_at)

    @patch("accounts.serializers.RiotClient.get_account_by_riot_id")
    def test_profile_update_reverifies_changed_riot_id(self, get_account):
        user = self._create_user("owner", "old-puuid")
        self.client.force_authenticate(user)
        get_account.return_value = {
            "puuid": "new-puuid",
            "gameName": "NewName",
            "tagLine": "NEW",
        }

        response = self.client.patch(
            "/api/accounts/profile/",
            {"riot_game_name": "NewName", "riot_tag_line": "NEW"},
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        user.refresh_from_db()
        self.assertEqual(user.puuid, "new-puuid")
        self.assertEqual(user.riot_tag_line, "NEW")

    @patch("accounts.serializers.RiotClient.get_account_by_riot_id")
    def test_add_and_view_friend_by_riot_id_is_one_way(self, get_account):
        owner = self._create_user("owner", "owner-puuid")
        friend = self._create_user("friend", "friend-puuid")
        self.client.force_authenticate(owner)
        get_account.return_value = {
            "puuid": "friend-puuid",
            "gameName": "friend",
            "tagLine": "KR1",
        }

        add_response = self.client.post(
            "/api/accounts/friends/",
            {
                "riot_game_name": "friend",
                "riot_tag_line": "KR1",
                "riot_server": "ASIA",
            },
            format="json",
        )
        profile_response = self.client.get(f"/api/accounts/friends/{friend.id}/")

        self.assertEqual(add_response.status_code, 201)
        self.assertEqual(profile_response.status_code, 200)
        self.assertTrue(Friendship.objects.filter(user=owner, friend=friend).exists())
        self.assertFalse(Friendship.objects.filter(user=friend, friend=owner).exists())
        self.assertNotIn("answer", profile_response.data)

    def test_incoming_friend_requests_excludes_mutual_friends(self):
        owner = self._create_user("owner", "owner-puuid")
        follower = self._create_user("follower", "follower-puuid")
        mutual = self._create_user("mutual", "mutual-puuid")
        Friendship.objects.create(user=follower, friend=owner)
        Friendship.objects.create(user=mutual, friend=owner)
        Friendship.objects.create(user=owner, friend=mutual)
        self.client.force_authenticate(owner)

        response = self.client.get("/api/accounts/friends/incoming/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual([user["username"] for user in response.data], ["follower"])

    @patch("accounts.views.RiotClient.get_match_ids")
    def test_match_list_uses_authenticated_users_puuid(self, get_match_ids):
        user = self._create_user("owner", "owner-puuid")
        self.client.force_authenticate(user)
        get_match_ids.return_value = ["ASIA_1", "ASIA_2"]

        response = self.client.get("/api/accounts/matches/?start=1&count=2")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["match_ids"], ["ASIA_1", "ASIA_2"])
        get_match_ids.assert_called_once_with(
            "owner-puuid", "ASIA", start=1, count=2
        )

    @patch("accounts.views.RiotClient.get_account_by_puuid")
    def test_refresh_riot_profile_uses_stored_puuid(self, get_account):
        user = self._create_user("owner", "owner-puuid")
        self.client.force_authenticate(user)
        get_account.return_value = {
            "puuid": "owner-puuid",
            "gameName": "Renamed",
            "tagLine": "NEW",
        }

        response = self.client.post("/api/accounts/profile/riot/refresh/")

        self.assertEqual(response.status_code, 200)
        user.refresh_from_db()
        self.assertEqual(user.riot_game_name, "Renamed")
        self.assertEqual(user.riot_tag_line, "NEW")
