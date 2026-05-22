from django.contrib import admin

from .models import Draw, Ticket


@admin.register(Draw)
class DrawAdmin(admin.ModelAdmin):
    list_display = ["round_number", "status", "winning_numbers", "bonus_number", "drawn_at", "created_at"]
    list_filter = ["status"]
    search_fields = ["round_number"]
    ordering = ["-round_number"]


@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = ["ticket_code", "user", "draw", "numbers_display", "purchase_type", "price", "result_display", "prize_amount", "created_at"]
    list_filter = ["purchase_type", "draw__status", "prize_rank"]
    search_fields = ["ticket_code", "user__username", "draw__round_number"]
    readonly_fields = ["ticket_code", "numbers_display", "result_display"]
    ordering = ["-created_at"]
