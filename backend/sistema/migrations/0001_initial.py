from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name='VersaoSistema',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('numero', models.CharField(max_length=20, unique=True)),
                ('descricao', models.CharField(blank=True, max_length=255)),
                ('implantado_em', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'verbose_name': 'versão do sistema',
                'verbose_name_plural': 'versões do sistema',
                'ordering': ['-implantado_em'],
            },
        ),
    ]
