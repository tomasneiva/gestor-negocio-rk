from django.db import migrations


def criar_versao(apps, schema_editor):
    VersaoSistema = apps.get_model('sistema', 'VersaoSistema')
    VersaoSistema.objects.get_or_create(
        numero='v1',
        defaults={'descricao': 'Estoque, clientes, notas fiscais e pedidos de venda'},
    )


def remover_versao(apps, schema_editor):
    VersaoSistema = apps.get_model('sistema', 'VersaoSistema')
    VersaoSistema.objects.filter(numero='v1').delete()


class Migration(migrations.Migration):

    dependencies = [
        ('sistema', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(criar_versao, remover_versao),
    ]
