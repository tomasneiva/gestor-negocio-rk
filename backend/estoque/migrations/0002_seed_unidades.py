from django.db import migrations


def criar_unidades(apps, schema_editor):
    Unidade = apps.get_model("estoque", "Unidade")
    for nome in ["Tomás", "Ricardo"]:
        Unidade.objects.get_or_create(nome=nome)


def remover_unidades(apps, schema_editor):
    Unidade = apps.get_model("estoque", "Unidade")
    Unidade.objects.filter(nome__in=["Tomás", "Ricardo"]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("estoque", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(criar_unidades, remover_unidades),
    ]
