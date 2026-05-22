from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Draw",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("round_number", models.PositiveIntegerField(unique=True, verbose_name="회차")),
                (
                    "status",
                    models.CharField(
                        choices=[("open", "판매중"), ("drawn", "추첨완료")],
                        default="open",
                        max_length=10,
                    ),
                ),
                ("winning_numbers", models.JSONField(blank=True, default=list, verbose_name="당첨 번호")),
                ("bonus_number", models.PositiveSmallIntegerField(blank=True, null=True, verbose_name="보너스 번호")),
                ("drawn_at", models.DateTimeField(blank=True, null=True, verbose_name="추첨 일시")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="생성 일시")),
            ],
            options={
                "verbose_name": "추첨 회차",
                "verbose_name_plural": "추첨 회차",
                "ordering": ["-round_number"],
            },
        ),
        migrations.CreateModel(
            name="Ticket",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("numbers", models.JSONField(verbose_name="구매 번호")),
                (
                    "purchase_type",
                    models.CharField(
                        choices=[("manual", "수동"), ("auto", "자동")],
                        max_length=10,
                    ),
                ),
                ("price", models.PositiveIntegerField(default=1000, verbose_name="구매 금액")),
                ("match_count", models.PositiveSmallIntegerField(default=0, verbose_name="일치 개수")),
                ("matched_bonus", models.BooleanField(default=False, verbose_name="보너스 일치")),
                (
                    "prize_rank",
                    models.PositiveSmallIntegerField(
                        blank=True,
                        choices=[(1, "1등"), (2, "2등"), (3, "3등"), (4, "4등"), (5, "5등")],
                        null=True,
                        verbose_name="당첨 등수",
                    ),
                ),
                ("prize_amount", models.PositiveBigIntegerField(default=0, verbose_name="당첨금")),
                ("evaluated_at", models.DateTimeField(blank=True, null=True, verbose_name="당첨 확인 일시")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="구매 일시")),
                (
                    "draw",
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="tickets", to="lotto.draw"),
                ),
                (
                    "user",
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="tickets", to=settings.AUTH_USER_MODEL),
                ),
            ],
            options={
                "verbose_name": "구매 티켓",
                "verbose_name_plural": "구매 티켓",
                "ordering": ["-created_at"],
            },
        ),
    ]
