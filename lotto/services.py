import random

from django.db import transaction
from django.db.models import Max, Sum
from django.utils import timezone

from .models import Draw, Ticket


LOTTO_PRICE = 1000
NUMBER_MIN = 1
NUMBER_MAX = 45
NUMBER_COUNT = 6

PRIZE_TABLE = {
    1: 2_000_000_000,
    2: 50_000_000,
    3: 1_500_000,
    4: 50_000,
    5: 5_000,
}


def validate_numbers(numbers):
    normalized = sorted(int(number) for number in numbers)
    if len(normalized) != NUMBER_COUNT:
        raise ValueError("로또 번호는 6개여야 합니다.")
    if len(set(normalized)) != NUMBER_COUNT:
        raise ValueError("중복 번호는 선택할 수 없습니다.")
    if any(number < NUMBER_MIN or number > NUMBER_MAX for number in normalized):
        raise ValueError("번호는 1부터 45 사이여야 합니다.")
    return normalized


def generate_numbers():
    return sorted(random.sample(range(NUMBER_MIN, NUMBER_MAX + 1), NUMBER_COUNT))


def generate_bonus_number(winning_numbers):
    candidates = [number for number in range(NUMBER_MIN, NUMBER_MAX + 1) if number not in winning_numbers]
    return random.choice(candidates)


def next_round_number():
    current_max = Draw.objects.aggregate(max_round=Max("round_number"))["max_round"] or 0
    return current_max + 1


def get_open_draw():
    draw = Draw.objects.filter(status=Draw.STATUS_OPEN).order_by("round_number").first()
    if draw:
        return draw
    return Draw.objects.create(round_number=next_round_number())


def create_manual_ticket(user, numbers):
    return Ticket.objects.create(
        user=user,
        draw=get_open_draw(),
        numbers=validate_numbers(numbers),
        purchase_type=Ticket.TYPE_MANUAL,
        price=LOTTO_PRICE,
    )


def create_auto_tickets(user, quantity):
    quantity = int(quantity)
    if quantity < 1 or quantity > 5:
        raise ValueError("자동 구매는 한 번에 1장부터 5장까지 가능합니다.")
    draw = get_open_draw()
    return [
        Ticket.objects.create(
            user=user,
            draw=draw,
            numbers=generate_numbers(),
            purchase_type=Ticket.TYPE_AUTO,
            price=LOTTO_PRICE,
        )
        for _ in range(quantity)
    ]


def calculate_result(ticket_numbers, winning_numbers, bonus_number):
    ticket_set = set(ticket_numbers)
    winning_set = set(winning_numbers)
    match_count = len(ticket_set & winning_set)
    matched_bonus = bonus_number in ticket_set

    if match_count == 6:
        rank = 1
    elif match_count == 5 and matched_bonus:
        rank = 2
    elif match_count == 5:
        rank = 3
    elif match_count == 4:
        rank = 4
    elif match_count == 3:
        rank = 5
    else:
        rank = None

    return {
        "match_count": match_count,
        "matched_bonus": matched_bonus,
        "prize_rank": rank,
        "prize_amount": PRIZE_TABLE.get(rank, 0),
    }


def evaluate_tickets(draw):
    now = timezone.now()
    for ticket in draw.tickets.select_for_update():
        result = calculate_result(ticket.numbers, draw.winning_numbers, draw.bonus_number)
        ticket.match_count = result["match_count"]
        ticket.matched_bonus = result["matched_bonus"]
        ticket.prize_rank = result["prize_rank"]
        ticket.prize_amount = result["prize_amount"]
        ticket.evaluated_at = now
        ticket.save(update_fields=["match_count", "matched_bonus", "prize_rank", "prize_amount", "evaluated_at"])


@transaction.atomic
def run_draw():
    draw = Draw.objects.select_for_update().filter(status=Draw.STATUS_OPEN).order_by("round_number").first()
    if draw is None:
        draw = Draw.objects.create(round_number=next_round_number())

    winning_numbers = generate_numbers()
    bonus_number = generate_bonus_number(winning_numbers)
    draw.mark_drawn(winning_numbers, bonus_number)
    draw.save(update_fields=["winning_numbers", "bonus_number", "status", "drawn_at"])
    evaluate_tickets(draw)
    Draw.objects.create(round_number=next_round_number())
    return draw


def draw_rank_counts(draw):
    counts = {rank: 0 for rank in PRIZE_TABLE}
    counts["none"] = 0
    for ticket in draw.tickets.all():
        if ticket.prize_rank:
            counts[ticket.prize_rank] += 1
        else:
            counts["none"] += 1
    return counts


def dashboard_metrics():
    tickets = Ticket.objects.all()
    total_sales = tickets.aggregate(total=Sum("price"))["total"] or 0
    total_payout = tickets.aggregate(total=Sum("prize_amount"))["total"] or 0
    return {
        "ticket_count": tickets.count(),
        "total_sales": total_sales,
        "total_payout": total_payout,
        "service_profit": total_sales - total_payout,
        "open_draw": get_open_draw(),
        "drawn_count": Draw.objects.filter(status=Draw.STATUS_DRAWN).count(),
    }


def user_ticket_summary(user):
    tickets = Ticket.objects.filter(user=user)
    total_spent = tickets.aggregate(total=Sum("price"))["total"] or 0
    total_prize = tickets.aggregate(total=Sum("prize_amount"))["total"] or 0
    return {
        "ticket_count": tickets.count(),
        "total_spent": total_spent,
        "total_prize": total_prize,
        "net_result": total_prize - total_spent,
        "pending_count": tickets.filter(draw__status=Draw.STATUS_OPEN).count(),
        "win_count": tickets.filter(prize_rank__isnull=False).count(),
    }
