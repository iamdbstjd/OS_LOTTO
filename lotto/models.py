from django.conf import settings
from django.db import models
from django.utils import timezone


class Draw(models.Model):
    STATUS_OPEN = "open"
    STATUS_DRAWN = "drawn"
    STATUS_CHOICES = [
        (STATUS_OPEN, "판매중"),
        (STATUS_DRAWN, "추첨완료"),
    ]

    round_number = models.PositiveIntegerField(unique=True, verbose_name="회차")
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=STATUS_OPEN)
    winning_numbers = models.JSONField(default=list, blank=True, verbose_name="당첨 번호")
    bonus_number = models.PositiveSmallIntegerField(null=True, blank=True, verbose_name="보너스 번호")
    drawn_at = models.DateTimeField(null=True, blank=True, verbose_name="추첨 일시")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="생성 일시")

    class Meta:
        ordering = ["-round_number"]
        verbose_name = "추첨 회차"
        verbose_name_plural = "추첨 회차"

    def __str__(self):
        return f"{self.round_number}회차 ({self.get_status_display()})"

    @property
    def is_drawn(self):
        return self.status == self.STATUS_DRAWN

    def mark_drawn(self, winning_numbers, bonus_number):
        self.winning_numbers = winning_numbers
        self.bonus_number = bonus_number
        self.status = self.STATUS_DRAWN
        self.drawn_at = timezone.now()


class Ticket(models.Model):
    TYPE_MANUAL = "manual"
    TYPE_AUTO = "auto"
    TYPE_CHOICES = [
        (TYPE_MANUAL, "수동"),
        (TYPE_AUTO, "자동"),
    ]

    RANK_CHOICES = [
        (1, "1등"),
        (2, "2등"),
        (3, "3등"),
        (4, "4등"),
        (5, "5등"),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="tickets")
    draw = models.ForeignKey(Draw, on_delete=models.CASCADE, related_name="tickets")
    ticket_code = models.CharField(max_length=20, unique=True, null=True, blank=True, editable=False, verbose_name="티켓 번호")
    numbers = models.JSONField(verbose_name="구매 번호")
    purchase_type = models.CharField(max_length=10, choices=TYPE_CHOICES)
    price = models.PositiveIntegerField(default=1000, verbose_name="구매 금액")
    match_count = models.PositiveSmallIntegerField(default=0, verbose_name="일치 개수")
    matched_bonus = models.BooleanField(default=False, verbose_name="보너스 일치")
    prize_rank = models.PositiveSmallIntegerField(choices=RANK_CHOICES, null=True, blank=True, verbose_name="당첨 등수")
    prize_amount = models.PositiveBigIntegerField(default=0, verbose_name="당첨금")
    evaluated_at = models.DateTimeField(null=True, blank=True, verbose_name="당첨 확인 일시")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="구매 일시")

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "구매 티켓"
        verbose_name_plural = "구매 티켓"

    def __str__(self):
        return f"{self.user} - {self.draw.round_number}회차 - {self.numbers_display}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if not self.ticket_code:
            self.ticket_code = f"L{self.draw.round_number:04d}-{self.pk:06d}"
            super().save(update_fields=["ticket_code"])

    @property
    def numbers_display(self):
        return " ".join(f"{number:02d}" for number in self.numbers)

    @property
    def result_display(self):
        if not self.draw.is_drawn:
            return "추첨 전"
        if self.prize_rank:
            return f"{self.prize_rank}등"
        return "낙첨"
