from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0008_matchingrun_matchingrecord"),
    ]

    operations = [
        migrations.AddField(
            model_name="matchingrecord",
            name="result_updated_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="matchingrecord",
            name="winning_team",
            field=models.CharField(
                blank=True,
                choices=(("blue", "Blue"), ("red", "Red")),
                max_length=4,
                null=True,
            ),
        ),
    ]
