from django.db import migrations, models


def migrate_page_format(apps, schema_editor):
    LabelSettings = apps.get_model('labels', 'LabelSettings')
    LabelSettings.objects.filter(page_format='A4').update(page_format='PDF_A4')
    LabelSettings.objects.filter(page_format='THERMAL_80MM').update(page_format='PDF_A4')


class Migration(migrations.Migration):

    dependencies = [
        ('labels', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='labelsettings',
            name='page_format',
            field=models.CharField(choices=[('PDF_A4', 'PDF — Folha A4'), ('TEXT_RAW', 'Texto — Impressão RAW (40 colunas)')], default='PDF_A4', max_length=20, verbose_name='Formato de página'),
        ),
        migrations.RunPython(migrate_page_format),
    ]