from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models


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
