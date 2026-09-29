from django.db import migrations


def criar_versao(apps, schema_editor):
    VersaoSistema = apps.get_model('sistema', 'VersaoSistema')
    VersaoSistema.objects.get_or_create(
        numero='v1.03',
        defaults={'descricao': 'Bloqueio de nota fiscal duplicada pelo numero'},
    )


def remover_versao(apps, schema_editor):
    VersaoSistema = apps.get_model('sistema', 'VersaoSistema')
    VersaoSistema.objects.filter(numero='v1.03').delete()


class Migration(migrations.Migration):

    dependencies = [
        ('sistema', '0004_versao_v102'),
    ]

    operations = [
        migrations.RunPython(criar_versao, remover_versao),
    ]
