from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    email = models.EmailField(unique=True)

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

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    USERNAME_FIELD = "username"
    REQUIRED_FIELDS = ["email"]

    class Meta:
        db_table = "users"
        ordering = ["-created_at"]

    def __str__(self):
        return self.username
