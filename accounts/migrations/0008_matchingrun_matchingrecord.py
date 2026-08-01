import uuid

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0007_alter_user_managers_alter_user_email"),
    ]

    operations = [
        migrations.CreateModel(
            name="MatchingRun",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ("participants", models.JSONField(default=list)),
                ("matches", models.JSONField(default=list)),
                ("unmatched_participants", models.JSONField(default=list)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "owner",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="matching_runs",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "db_table": "matching_runs",
                "ordering": ["-created_at"],
            },
        ),
        migrations.CreateModel(
            name="MatchingRecord",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ("team_number", models.PositiveIntegerField()),
                ("participants", models.JSONField(default=list)),
                ("blue_team", models.JSONField(default=list)),
                ("red_team", models.JSONField(default=list)),
                ("blue_total_score", models.FloatField()),
                ("red_total_score", models.FloatField()),
                ("score_difference", models.FloatField()),
                ("balance_score", models.FloatField()),
                ("saved_at", models.DateTimeField(auto_now_add=True)),
                (
                    "matching_run",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="saved_records",
                        to="accounts.matchingrun",
                    ),
                ),
                (
                    "owner",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="matching_records",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "db_table": "matching_records",
                "ordering": ["-saved_at"],
            },
        ),
        migrations.AddConstraint(
            model_name="matchingrecord",
            constraint=models.UniqueConstraint(
                fields=("owner", "matching_run", "team_number"),
                name="unique_saved_matching_team",
            ),
        ),
    ]
