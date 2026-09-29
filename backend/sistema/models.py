from django.db import models


class VersaoSistema(models.Model):
    numero = models.CharField(max_length=20, unique=True)
    descricao = models.CharField(max_length=255, blank=True)
    implantado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "versão do sistema"
        verbose_name_plural = "versões do sistema"
        ordering = ["-implantado_em"]

    def __str__(self):
        return self.numero

    @classmethod
    def atual(cls):
        return cls.objects.order_by("-implantado_em").first()
