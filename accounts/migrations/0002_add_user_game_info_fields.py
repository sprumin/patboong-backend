from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="main_line",
            field=models.CharField(blank=True, default="", max_length=20),
        ),
        migrations.AddField(
            model_name="user",
            name="sub_line",
            field=models.CharField(blank=True, default="", max_length=20),
        ),
        migrations.AddField(
            model_name="user",
            name="tier_top",
            field=models.CharField(blank=True, default="", max_length=20),
        ),
        migrations.AddField(
            model_name="user",
            name="tier_jungle",
            field=models.CharField(blank=True, default="", max_length=20),
        ),
        migrations.AddField(
            model_name="user",
            name="tier_mid",
            field=models.CharField(blank=True, default="", max_length=20),
        ),
        migrations.AddField(
            model_name="user",
            name="tier_adc",
            field=models.CharField(blank=True, default="", max_length=20),
        ),
        migrations.AddField(
            model_name="user",
            name="tier_support",
            field=models.CharField(blank=True, default="", max_length=20),
        ),
        migrations.AddField(
            model_name="user",
            name="question",
            field=models.CharField(blank=True, default="", max_length=100),
        ),
        migrations.AddField(
            model_name="user",
            name="answer",
            field=models.CharField(blank=True, default="", max_length=200),
        ),
        migrations.AddField(
            model_name="user",
            name="service_terms",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="user",
            name="privacy_terms",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="user",
            name="age_terms",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="user",
            name="marketing_terms",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="user",
            name="event_terms",
            field=models.BooleanField(default=False),
        ),
    ]
