import accounts.models
from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0002_add_user_game_info_fields"),
    ]

    operations = [
        migrations.AlterModelManagers(
            name="user",
            managers=[
                ("objects", accounts.models.UserManager()),
            ],
        ),
    ]
