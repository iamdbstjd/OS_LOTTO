from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import Draw, Ticket
from .services import calculate_result, create_auto_tickets, create_manual_ticket, run_draw, validate_numbers


class LottoServiceTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="buyer", password="pass12345")

    def test_validate_numbers_sorts_and_rejects_duplicates(self):
        self.assertEqual(validate_numbers([6, 1, 3, 4, 5, 2]), [1, 2, 3, 4, 5, 6])

        with self.assertRaises(ValueError):
            validate_numbers([1, 2, 3, 4, 5, 5])

    def test_manual_ticket_uses_current_open_draw(self):
        ticket = create_manual_ticket(self.user, [1, 2, 3, 4, 5, 6])

        self.assertEqual(ticket.draw.round_number, 1)
        self.assertEqual(ticket.purchase_type, Ticket.TYPE_MANUAL)
        self.assertEqual(ticket.numbers, [1, 2, 3, 4, 5, 6])
        self.assertRegex(ticket.ticket_code, r"^L0001-\d{6}$")

    def test_auto_ticket_generation_creates_requested_quantity(self):
        tickets = create_auto_tickets(self.user, 3)

        self.assertEqual(len(tickets), 3)
        self.assertEqual(Ticket.objects.count(), 3)
        for ticket in tickets:
            self.assertEqual(len(ticket.numbers), 6)
            self.assertEqual(len(set(ticket.numbers)), 6)
            self.assertTrue(all(1 <= number <= 45 for number in ticket.numbers))

    def test_calculate_result_ranks(self):
        winning = [1, 2, 3, 4, 5, 6]

        self.assertEqual(calculate_result([1, 2, 3, 4, 5, 6], winning, 7)["prize_rank"], 1)
        self.assertEqual(calculate_result([1, 2, 3, 4, 5, 7], winning, 7)["prize_rank"], 2)
        self.assertEqual(calculate_result([1, 2, 3, 4, 5, 8], winning, 7)["prize_rank"], 3)
        self.assertEqual(calculate_result([1, 2, 3, 4, 8, 9], winning, 7)["prize_rank"], 4)
        self.assertEqual(calculate_result([1, 2, 3, 8, 9, 10], winning, 7)["prize_rank"], 5)
        self.assertIsNone(calculate_result([1, 2, 8, 9, 10, 11], winning, 7)["prize_rank"])

    def test_run_draw_evaluates_tickets_and_opens_next_round(self):
        create_manual_ticket(self.user, [1, 2, 3, 4, 5, 6])
        create_manual_ticket(self.user, [1, 2, 3, 8, 9, 10])

        with patch("lotto.services.generate_numbers", return_value=[1, 2, 3, 4, 5, 6]), patch(
            "lotto.services.generate_bonus_number", return_value=7
        ):
            draw = run_draw()

        tickets = list(Ticket.objects.order_by("id"))
        self.assertEqual(draw.status, Draw.STATUS_DRAWN)
        self.assertEqual(tickets[0].prize_rank, 1)
        self.assertEqual(tickets[1].prize_rank, 5)
        self.assertTrue(Draw.objects.filter(round_number=2, status=Draw.STATUS_OPEN).exists())


class LottoViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="buyer", password="pass12345")
        self.staff = User.objects.create_user(username="staff", password="pass12345", is_staff=True)

    def test_signup_logs_user_in(self):
        response = self.client.post(
            reverse("signup"),
            {
                "username": "newbuyer",
                "email": "newbuyer@example.com",
                "password1": "StrongPass12345",
                "password2": "StrongPass12345",
            },
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(User.objects.filter(username="newbuyer").exists())

    def test_logged_in_user_can_purchase_manual_ticket(self):
        self.client.force_login(self.user)
        response = self.client.post(
            reverse("purchase_manual"),
            {
                "number_1": 1,
                "number_2": 2,
                "number_3": 3,
                "number_4": 4,
                "number_5": 5,
                "number_6": 6,
            },
        )

        self.assertRedirects(response, reverse("ticket_list"))
        self.assertEqual(Ticket.objects.filter(user=self.user).count(), 1)

    def test_staff_can_run_draw_from_dashboard(self):
        self.client.force_login(self.staff)
        create_manual_ticket(self.user, [1, 2, 3, 4, 5, 6])

        with patch("lotto.services.generate_numbers", return_value=[1, 2, 3, 4, 5, 6]), patch(
            "lotto.services.generate_bonus_number", return_value=7
        ):
            response = self.client.post(reverse("run_draw"))

        self.assertEqual(response.status_code, 302)
        ticket = Ticket.objects.get(user=self.user)
        self.assertEqual(ticket.prize_rank, 1)

    def test_staff_dashboard_renders(self):
        self.client.force_login(self.staff)

        response = self.client.get(reverse("staff_dashboard"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "판매 및 추첨 관리")

    def test_staff_sales_renders_purchase_history(self):
        self.client.force_login(self.staff)
        ticket = create_manual_ticket(self.user, [1, 2, 3, 4, 5, 6])

        response = self.client.get(reverse("staff_sales"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "판매 내역")
        self.assertContains(response, ticket.ticket_code)

    def test_staff_draw_detail_renders_number_balls(self):
        self.client.force_login(self.staff)
        create_manual_ticket(self.user, [1, 2, 3, 4, 5, 6])

        with patch("lotto.services.generate_numbers", return_value=[1, 2, 3, 4, 5, 6]), patch(
            "lotto.services.generate_bonus_number", return_value=7
        ):
            draw = run_draw()

        response = self.client.get(reverse("staff_draw_detail", kwargs={"pk": draw.pk}))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "lotto-ball")

    def test_non_staff_cannot_run_draw(self):
        self.client.force_login(self.user)

        response = self.client.post(reverse("run_draw"))

        self.assertEqual(response.status_code, 403)
