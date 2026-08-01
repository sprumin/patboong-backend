import uuid

from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models


DEFAULT_TIER_SCORES = {
    "Iron IV": 100,
    "Iron III": 150,
    "Iron II": 200,
    "Iron I": 250,
    "Bronze IV": 300,
    "Bronze III": 350,
    "Bronze II": 400,
    "Bronze I": 450,
    "Silver IV": 500,
    "Silver III": 550,
    "Silver II": 600,
    "Silver I": 650,
    "Gold IV": 700,
    "Gold III": 750,
    "Gold II": 800,
    "Gold I": 850,
    "Platinum IV": 900,
    "Platinum III": 950,
    "Platinum II": 1000,
    "Platinum I": 1050,
    "Emerald IV": 1100,
    "Emerald III": 1150,
    "Emerald II": 1200,
    "Emerald I": 1250,
    "Diamond IV": 1300,
    "Diamond III": 1350,
    "Diamond II": 1400,
    "Diamond I": 1450,
    "Master": 1500,
    "Grandmaster": 1600,
    "Challenger": 1700,
}

DEFAULT_POSITION_BONUS = {
    "top": 0,
    "jungle": 0,
    "mid": 0,
    "adc": 0,
    "support": 0,
}


def default_tier_scores():
    return DEFAULT_TIER_SCORES.copy()


def default_position_bonus():
    return DEFAULT_POSITION_BONUS.copy()


class UserManager(BaseUserManager):
    def create_user(self, username, password=None, email=None, **extra_fields):
        user = self.model(username=username, email=email or None, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, password=None, email=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        return self.create_user(username, password, email, **extra_fields)


class User(AbstractUser):
    objects = UserManager()

    email = models.EmailField(unique=True, null=True, blank=True, default=None)

    main_line = models.CharField(max_length=20, blank=True, default="")
    sub_line = models.CharField(max_length=20, blank=True, default="")

    tier_top = models.CharField(max_length=20, blank=True, default="")
    tier_jungle = models.CharField(max_length=20, blank=True, default="")
    tier_mid = models.CharField(max_length=20, blank=True, default="")
    tier_adc = models.CharField(max_length=20, blank=True, default="")
    tier_support = models.CharField(max_length=20, blank=True, default="")

    question = models.CharField(max_length=100, blank=True, default="")
    answer = models.CharField(max_length=200, blank=True, default="")

    service_terms = models.BooleanField(default=False)
    privacy_terms = models.BooleanField(default=False)
    age_terms = models.BooleanField(default=False)
    marketing_terms = models.BooleanField(default=False)
    event_terms = models.BooleanField(default=False)

    riot_game_name = models.CharField(max_length=100, blank=True, default="")
    riot_tag_line = models.CharField(max_length=50, blank=True, default="")
    riot_server = models.CharField(max_length=20, blank=True, default="")
    puuid = models.CharField(max_length=100, unique=True, null=True, blank=True)
    verified_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    USERNAME_FIELD = "username"
    REQUIRED_FIELDS = ["email"]

    class Meta:
        db_table = "users"
        ordering = ["-created_at"]

    def __str__(self):
        return self.username


class Friendship(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="friendships"
    )
    friend = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="friended_by"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "friendships"
        constraints = [
            models.UniqueConstraint(
                fields=("user", "friend"), name="unique_user_friend"
            )
        ]
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user.username} -> {self.friend.username}"


class MatchingSettings(models.Model):
    tier_scores = models.JSONField(default=default_tier_scores)
    position_bonus = models.JSONField(default=default_position_bonus)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "matching_settings"
        verbose_name_plural = "matching settings"

    def save(self, *args, **kwargs):
        # This service has one global matching configuration.
        self.pk = 1
        super().save(*args, **kwargs)

    def __str__(self):
        return "Global matching settings"


class MatchingRun(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    owner = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="matching_runs"
    )
    participants = models.JSONField(default=list)
    matches = models.JSONField(default=list)
    unmatched_participants = models.JSONField(default=list)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "matching_runs"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.owner.username} - {self.created_at}"


class MatchingRecord(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    owner = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="matching_records"
    )
    matching_run = models.ForeignKey(
        MatchingRun,
        on_delete=models.SET_NULL,
        related_name="saved_records",
        null=True,
        blank=True,
    )
    team_number = models.PositiveIntegerField()
    participants = models.JSONField(default=list)
    blue_team = models.JSONField(default=list)
    red_team = models.JSONField(default=list)
    blue_total_score = models.FloatField()
    red_total_score = models.FloatField()
    score_difference = models.FloatField()
    balance_score = models.FloatField()
    saved_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "matching_records"
        ordering = ["-saved_at"]
        constraints = [
            models.UniqueConstraint(
                fields=("owner", "matching_run", "team_number"),
                name="unique_saved_matching_team",
            )
        ]

    def __str__(self):
        return f"{self.owner.username} - team {self.team_number}"
