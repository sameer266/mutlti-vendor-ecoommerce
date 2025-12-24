"""No-op placeholder migration.

The real schema changes for shipping/product/orderitem/tax are handled
by the generated 0063_taxcost_delete_shippingcost_orderitem_estimated_days_and_more.py
and 0064_add_order_estimated_days.py files. Keep this file empty to avoid
duplicating operations.
"""
from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ('dashboard', '0062_alter_product_main_image_alter_userprofile_gender'),
    ]

    operations = []
