from django.db import migrations


def criar_versao(apps, schema_editor):
    VersaoSistema = apps.get_model('sistema', 'VersaoSistema')
    VersaoSistema.objects.get_or_create(
        numero='v1.02',
        defaults={'descricao': 'Envio de notas fiscais em massa'},
    )


def remover_versao(apps, schema_editor):
    VersaoSistema = apps.get_model('sistema', 'VersaoSistema')
    VersaoSistema.objects.filter(numero='v1.02').delete()


class Migration(migrations.Migration):

    dependencies = [
        ('sistema', '0003_versao_v101'),
    ]

    operations = [
        migrations.RunPython(criar_versao, remover_versao),
    ]
