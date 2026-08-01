import accounts.models
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0005_merge_0003_0004"),
    ]

    operations = [
        migrations.CreateModel(
            name="MatchingSettings",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "tier_scores",
                    models.JSONField(default=accounts.models.default_tier_scores),
                ),
                (
                    "position_bonus",
                    models.JSONField(default=accounts.models.default_position_bonus),
                ),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "db_table": "matching_settings",
                "verbose_name_plural": "matching settings",
            },
        ),
    ]
