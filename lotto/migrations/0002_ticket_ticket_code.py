from django.db import migrations, models


def fill_ticket_codes(apps, schema_editor):
    Ticket = apps.get_model("lotto", "Ticket")
    for ticket in Ticket.objects.select_related("draw").filter(ticket_code__isnull=True).order_by("id"):
        ticket.ticket_code = f"L{ticket.draw.round_number:04d}-{ticket.pk:06d}"
        ticket.save(update_fields=["ticket_code"])


class Migration(migrations.Migration):
    dependencies = [
        ("lotto", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="ticket",
            name="ticket_code",
            field=models.CharField(blank=True, editable=False, max_length=20, null=True, unique=True, verbose_name="티켓 번호"),
        ),
        migrations.RunPython(fill_ticket_codes, migrations.RunPython.noop),
    ]
