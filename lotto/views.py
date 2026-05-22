from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db.models import Count, Sum
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views.generic import CreateView, DetailView, ListView, TemplateView

from .forms import AutoTicketForm, ManualTicketForm, SignupForm
from .models import Draw, Ticket
from .services import (
    PRIZE_TABLE,
    create_auto_tickets,
    create_manual_ticket,
    dashboard_metrics,
    draw_rank_counts,
    get_open_draw,
    run_draw,
    user_ticket_summary,
)


class SignupView(CreateView):
    form_class = SignupForm
    template_name = "registration/signup.html"
    success_url = reverse_lazy("home")

    def form_valid(self, form):
        response = super().form_valid(form)
        login(self.request, self.object)
        return response


class StaffRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_staff


def home_context(user, manual_form=None, auto_form=None):
    return {
        "open_draw": get_open_draw(),
        "manual_form": manual_form or ManualTicketForm(),
        "auto_form": auto_form or AutoTicketForm(),
        "recent_tickets": Ticket.objects.filter(user=user).select_related("draw")[:5],
        "summary": user_ticket_summary(user),
    }


class HomeView(LoginRequiredMixin, TemplateView):
    template_name = "lotto/home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(home_context(self.request.user))
        return context


class TicketListView(LoginRequiredMixin, ListView):
    template_name = "lotto/ticket_list.html"
    context_object_name = "tickets"
    paginate_by = 20

    def get_queryset(self):
        return Ticket.objects.filter(user=self.request.user).select_related("draw")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["summary"] = user_ticket_summary(self.request.user)
        return context


class ResultListView(LoginRequiredMixin, ListView):
    template_name = "lotto/result_list.html"
    context_object_name = "tickets"
    paginate_by = 20

    def get_queryset(self):
        return Ticket.objects.filter(user=self.request.user, draw__status=Draw.STATUS_DRAWN).select_related("draw")


@login_required
def purchase_manual(request):
    if request.method != "POST":
        return redirect("home")
    form = ManualTicketForm(request.POST)
    if not form.is_valid():
        return render(request, "lotto/home.html", home_context(request.user, manual_form=form))

    ticket = create_manual_ticket(request.user, form.cleaned_data["numbers"])
    messages.success(request, f"{ticket.draw.round_number}회차 수동 번호를 구매했습니다.")
    return redirect("ticket_list")


@login_required
def purchase_auto(request):
    if request.method != "POST":
        return redirect("home")
    form = AutoTicketForm(request.POST)
    if not form.is_valid():
        return render(request, "lotto/home.html", home_context(request.user, auto_form=form))

    tickets = create_auto_tickets(request.user, form.cleaned_data["quantity"])
    messages.success(request, f"{tickets[0].draw.round_number}회차 자동 번호 {len(tickets)}장을 구매했습니다.")
    return redirect("ticket_list")


class StaffDashboardView(LoginRequiredMixin, StaffRequiredMixin, TemplateView):
    template_name = "lotto/staff_dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["metrics"] = dashboard_metrics()
        context["recent_draws"] = Draw.objects.filter(status=Draw.STATUS_DRAWN)[:10]
        return context


class StaffSalesView(LoginRequiredMixin, StaffRequiredMixin, TemplateView):
    template_name = "lotto/staff_sales.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["metrics"] = dashboard_metrics()
        draws = (
            Draw.objects.annotate(
                ticket_count=Count("tickets"),
                total_sales=Sum("tickets__price"),
                total_payout=Sum("tickets__prize_amount"),
            )
            .order_by("-round_number")
        )
        context["draw_sales"] = [
            {
                "draw": draw,
                "ticket_count": draw.ticket_count,
                "total_sales": draw.total_sales or 0,
                "total_payout": draw.total_payout or 0,
                "profit": (draw.total_sales or 0) - (draw.total_payout or 0),
            }
            for draw in draws
        ]
        context["recent_tickets"] = Ticket.objects.select_related("user", "draw")[:50]
        return context


@login_required
def run_draw_view(request):
    if not request.user.is_staff:
        raise PermissionDenied
    if request.method != "POST":
        return redirect("staff_dashboard")
    draw = run_draw()
    messages.success(request, f"{draw.round_number}회차 추첨을 완료했습니다.")
    return redirect("staff_draw_detail", pk=draw.pk)


class StaffDrawDetailView(LoginRequiredMixin, StaffRequiredMixin, DetailView):
    model = Draw
    template_name = "lotto/staff_draw_detail.html"
    context_object_name = "draw"

    def get_queryset(self):
        return Draw.objects.prefetch_related("tickets__user")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        draw = self.object
        tickets = draw.tickets.select_related("user").order_by("prize_rank", "-prize_amount", "user__username")
        context["rank_counts"] = draw_rank_counts(draw)
        context["rank_rows"] = [(rank, context["rank_counts"][rank], PRIZE_TABLE[rank]) for rank in sorted(PRIZE_TABLE)]
        context["tickets"] = tickets
        context["total_sales"] = sum(ticket.price for ticket in tickets)
        context["total_payout"] = sum(ticket.prize_amount for ticket in tickets)
        context["profit"] = context["total_sales"] - context["total_payout"]
        return context
