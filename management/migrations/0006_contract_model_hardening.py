from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('management', '0005_vendor_risk_tier_contract'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='contract',
            name='is_active',
        ),
        migrations.AddConstraint(
            model_name='contract',
            constraint=models.CheckConstraint(
                check=models.Q(end_date__gte=models.F('start_date')),
                name='contract_end_on_or_after_start',
            ),
        ),
        migrations.AddConstraint(
            model_name='contract',
            constraint=models.UniqueConstraint(
                fields=('vendor', 'contract_id'),
                name='uniq_contract_id_per_vendor',
            ),
        ),
        migrations.AddIndex(
            model_name='contract',
            index=models.Index(fields=['start_date', 'end_date'], name='management_c_start_d_388d81_idx'),
        ),
    ]
