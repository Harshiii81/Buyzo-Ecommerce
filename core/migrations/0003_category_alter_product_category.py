
from django.db import migrations, models
import django.db.models.deletion


def preserve_old_categories(apps, schema_editor):
    Category = apps.get_model('core', 'Category')
    Product = apps.get_model('core', 'Product')

    db = schema_editor.connection.alias

    for product in Product.objects.using(db).all():

        old_category = product.category

        if not old_category:
            continue

        category, created = Category.objects.using(db).get_or_create(
            name=old_category,
            parent=None
        )

        product.category_new_id = category.id

        product.save(
            using=db,
            update_fields=['category_new']
        )


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0002_product_image'),
    ]

    operations = [

        migrations.CreateModel(
            name='Category',
            fields=[
                ('id', models.BigAutoField(
                    auto_created=True,
                    primary_key=True,
                    serialize=False,
                    verbose_name='ID'
                )),
                ('name', models.CharField(max_length=100)),
                ('parent', models.ForeignKey(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='subcategories',
                    to='core.category'
                )),
            ],
        ),

        migrations.AddField(
            model_name='product',
            name='category_new',
            field=models.ForeignKey(
                to='core.category',
                on_delete=django.db.models.deletion.PROTECT,
                null=True,
                blank=True,
                related_name='products'
            ),
        ),

        migrations.RunPython(
            preserve_old_categories,
            migrations.RunPython.noop
        ),

        migrations.RemoveField(
            model_name='product',
            name='category',
        ),

        migrations.RenameField(
            model_name='product',
            old_name='category_new',
            new_name='category',
        ),
    ]
