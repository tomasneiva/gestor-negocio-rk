from django.db import migrations


def criar_versao(apps, schema_editor):
    VersaoSistema = apps.get_model('sistema', 'VersaoSistema')
    VersaoSistema.objects.get_or_create(
        numero='v1.01',
        defaults={'descricao': 'Cadastro em massa de produtos pendentes ao salvar nota fiscal'},
    )


def remover_versao(apps, schema_editor):
    VersaoSistema = apps.get_model('sistema', 'VersaoSistema')
    VersaoSistema.objects.filter(numero='v1.01').delete()


class Migration(migrations.Migration):

    dependencies = [
        ('sistema', '0002_versao_v1'),
    ]

    operations = [
        migrations.RunPython(criar_versao, remover_versao),
    ]
