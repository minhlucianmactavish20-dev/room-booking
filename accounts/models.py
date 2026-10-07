from django.conf import settings
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver


class Profile(models.Model):
    class Role(models.TextChoices):
        USER = "user", "Người dùng"
        APPROVER = "approver", "Người duyệt"
        ADMIN = "admin", "Quản trị"

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="profile",
    )
    role = models.CharField("Vai trò", max_length=10, choices=Role.choices, default=Role.USER)
    phone = models.CharField("Số điện thoại", max_length=15, blank=True)

    class Meta:
        verbose_name = "Hồ sơ người dùng"
        verbose_name_plural = "Hồ sơ người dùng"

    def __str__(self):
        return f"{self.user.username} ({self.get_role_display()})"

    @property
    def is_approver(self):
        return self.role in (self.Role.APPROVER, self.Role.ADMIN)


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_profile(sender, instance, created, **kwargs):
    if created:
        role = Profile.Role.ADMIN if instance.is_superuser else Profile.Role.USER
        Profile.objects.create(user=instance, role=role)