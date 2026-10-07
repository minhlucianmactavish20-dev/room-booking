import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Profile",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("role", models.CharField(
                    choices=[("user", "Người dùng"), ("approver", "Người duyệt"), ("admin", "Quản trị")],
                    default="user",
                    max_length=10,
                    verbose_name="Vai trò",
                )),
                ("phone", models.CharField(blank=True, max_length=15, verbose_name="Số điện thoại")),
                ("user", models.OneToOneField(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name="profile",
                    to=settings.AUTH_USER_MODEL,
                )),
            ],
            options={
                "verbose_name": "Hồ sơ người dùng",
                "verbose_name_plural": "Hồ sơ người dùng",
            },
        ),
    ]