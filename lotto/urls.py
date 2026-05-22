from django.urls import path

from . import views


urlpatterns = [
    path("", views.HomeView.as_view(), name="home"),
    path("tickets/", views.TicketListView.as_view(), name="ticket_list"),
    path("results/", views.ResultListView.as_view(), name="result_list"),
    path("purchase/manual/", views.purchase_manual, name="purchase_manual"),
    path("purchase/auto/", views.purchase_auto, name="purchase_auto"),
    path("staff/", views.StaffDashboardView.as_view(), name="staff_dashboard"),
    path("staff/sales/", views.StaffSalesView.as_view(), name="staff_sales"),
    path("staff/draw/", views.run_draw_view, name="run_draw"),
    path("staff/draws/<int:pk>/", views.StaffDrawDetailView.as_view(), name="staff_draw_detail"),
]
