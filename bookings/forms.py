from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone

from .models import Booking, Room, Waitlist

DATETIME_FORMAT = "%Y-%m-%dT%H:%M"


class BookingForm(forms.ModelForm):
    class Meta:
        model = Booking
        fields = ("room", "purpose", "start_time", "end_time")
        widgets = {
            "start_time": forms.DateTimeInput(attrs={"type": "datetime-local"}, format=DATETIME_FORMAT),
            "end_time": forms.DateTimeInput(attrs={"type": "datetime-local"}, format=DATETIME_FORMAT),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["room"].queryset = Room.objects.filter(is_active=True)
        self.fields["start_time"].input_formats = [DATETIME_FORMAT]
        self.fields["end_time"].input_formats = [DATETIME_FORMAT]

    def clean(self):
        cleaned = super().clean()
        start = cleaned.get("start_time")
        if start and start < timezone.now():
            raise ValidationError("Không thể đặt phòng trong quá khứ.")
        return cleaned


class WaitlistForm(forms.ModelForm):
    class Meta:
        model = Waitlist
        fields = ("room", "purpose", "start_time", "end_time")
        widgets = {
            "start_time": forms.DateTimeInput(attrs={"type": "datetime-local"}, format=DATETIME_FORMAT),
            "end_time": forms.DateTimeInput(attrs={"type": "datetime-local"}, format=DATETIME_FORMAT),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["room"].queryset = Room.objects.filter(is_active=True)
        self.fields["start_time"].input_formats = [DATETIME_FORMAT]
        self.fields["end_time"].input_formats = [DATETIME_FORMAT]

    def clean(self):
        cleaned = super().clean()
        room = cleaned.get("room")
        start = cleaned.get("start_time")
        end = cleaned.get("end_time")

        if room and start and end:
            if end <= start:
                raise ValidationError("Giờ kết thúc phải sau giờ bắt đầu.")
            if start < timezone.now():
                raise ValidationError("Không thể đăng ký chờ trong quá khứ.")
            if not Booking.find_conflicts(room, start, end).exists():
                raise ValidationError(
                    "Phòng đang trống trong khung giờ này, hãy bấm 'Gửi yêu cầu đặt phòng' để đặt trực tiếp."
                )
        return cleaned