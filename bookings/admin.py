from django.contrib import admin
from .models import Room, Booking, Waitlist


@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ("name", "room_type", "location", "capacity", "is_active")
    list_filter = ("room_type", "is_active")
    search_fields = ("name", "location")


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ("room", "user", "start_time", "end_time", "status")
    list_filter = ("status", "room")
    search_fields = ("user__username", "purpose")
    date_hierarchy = "start_time"


@admin.register(Waitlist)
class WaitlistAdmin(admin.ModelAdmin):
    list_display = ("room", "user", "start_time", "end_time", "notified")
    list_filter = ("notified", "room")