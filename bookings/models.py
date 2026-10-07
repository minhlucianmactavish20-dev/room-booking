import uuid

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import F, Q


class Room(models.Model):
    class RoomType(models.TextChoices):
        CLASSROOM = "classroom", "Phòng học"
        LAB = "lab", "Phòng lab"
        MEETING = "meeting", "Phòng họp"

    name = models.CharField("Tên phòng", max_length=100, unique=True)
    room_type = models.CharField("Loại phòng", max_length=10, choices=RoomType.choices, default=RoomType.CLASSROOM)
    location = models.CharField("Vị trí", max_length=150, blank=True)
    capacity = models.PositiveIntegerField("Sức chứa", default=30)
    equipment = models.TextField("Thiết bị", blank=True, help_text="Ví dụ: máy chiếu, 30 máy tính, điều hòa")
    description = models.TextField("Mô tả", blank=True)
    is_active = models.BooleanField("Đang hoạt động", default=True)

    class Meta:
        verbose_name = "Phòng"
        verbose_name_plural = "Phòng"
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.get_room_type_display()})"


class Booking(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Chờ duyệt"
        APPROVED = "approved", "Đã duyệt"
        REJECTED = "rejected", "Từ chối"
        CANCELLED = "cancelled", "Đã hủy"

    ACTIVE_STATUSES = (Status.PENDING, Status.APPROVED)

    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name="bookings", verbose_name="Phòng")
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name="bookings", verbose_name="Người đặt",
    )
    purpose = models.CharField("Mục đích", max_length=200)
    start_time = models.DateTimeField("Bắt đầu")
    end_time = models.DateTimeField("Kết thúc")
    status = models.CharField("Trạng thái", max_length=10, choices=Status.choices, default=Status.PENDING)
    reject_reason = models.TextField("Lý do từ chối", blank=True)
    approver = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="approved_bookings", verbose_name="Người duyệt",
    )
    qr_token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    checked_in_at = models.DateTimeField("Check-in lúc", null=True, blank=True)
    created_at = models.DateTimeField("Ngày tạo", auto_now_add=True)

    class Meta:
        verbose_name = "Lượt đặt phòng"
        verbose_name_plural = "Lượt đặt phòng"
        ordering = ["-start_time"]
        constraints = [
            models.CheckConstraint(
                condition=Q(end_time__gt=F("start_time")),
                name="booking_end_after_start",
            ),
        ]

    def __str__(self):
        return f"{self.room.name} | {self.start_time:%d/%m/%Y %H:%M} - {self.end_time:%H:%M} | {self.user}"

    @classmethod
    def find_conflicts(cls, room, start, end, exclude_pk=None):
        """Trả về các lượt đặt bị trùng giờ với khoảng [start, end) của phòng này.

        Hai khoảng thời gian trùng nhau khi: start < end_cũ  VÀ  end > start_cũ
        """
        qs = cls.objects.filter(
            room=room,
            status__in=cls.ACTIVE_STATUSES,
            start_time__lt=end,
            end_time__gt=start,
        )
        if exclude_pk:
            qs = qs.exclude(pk=exclude_pk)
        return qs

    def clean(self):
        if self.start_time and self.end_time:
            if self.end_time <= self.start_time:
                raise ValidationError("Giờ kết thúc phải sau giờ bắt đầu.")
            if self.status in self.ACTIVE_STATUSES and self.room_id:
                if self.find_conflicts(self.room, self.start_time, self.end_time, self.pk).exists():
                    raise ValidationError("Phòng đã có người đặt trong khung giờ này.")


class Waitlist(models.Model):
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name="waitlist", verbose_name="Phòng")
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name="waitlist_entries", verbose_name="Người chờ",
    )
    purpose = models.CharField("Mục đích", max_length=200, blank=True)
    start_time = models.DateTimeField("Bắt đầu")
    end_time = models.DateTimeField("Kết thúc")
    notified = models.BooleanField("Đã thông báo", default=False)
    created_at = models.DateTimeField("Ngày đăng ký", auto_now_add=True)

    class Meta:
        verbose_name = "Hàng chờ"
        verbose_name_plural = "Hàng chờ"
        ordering = ["created_at"]

    def __str__(self):
        return f"Chờ {self.room.name} | {self.start_time:%d/%m/%Y %H:%M} | {self.user}"