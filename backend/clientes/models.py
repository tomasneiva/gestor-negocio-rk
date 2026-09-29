from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.db import models

from .validators import somente_digitos, validar_cnpj, validar_cpf


class Cliente(models.Model):
    class TipoPessoa(models.TextChoices):
        FISICA = "PF", "Pessoa física"
        JURIDICA = "PJ", "Pessoa jurídica"

    tipo_pessoa = models.CharField(max_length=2, choices=TipoPessoa.choices, default=TipoPessoa.FISICA)
    nome = models.CharField("nome / razão social", max_length=200)
    documento = models.CharField("CPF/CNPJ", max_length=14, unique=True)
    cep = models.CharField(max_length=8, validators=[RegexValidator(r"^\d{8}$", "CEP deve ter 8 dígitos.")])
    logradouro = models.CharField(max_length=200, blank=True)
    numero = models.CharField("número", max_length=20, blank=True)
    complemento = models.CharField(max_length=100, blank=True)
    bairro = models.CharField(max_length=100, blank=True)
    cidade = models.CharField(max_length=100, blank=True)
    uf = models.CharField(max_length=2, blank=True)
    telefone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    nome_representante = models.CharField(max_length=200, blank=True)
    observacoes = models.TextField(blank=True)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "cliente"
        verbose_name_plural = "clientes"
        ordering = ["nome"]

    def __str__(self):
        return self.nome

    def clean(self):
        super().clean()
        if self.documento:
            digitos = somente_digitos(self.documento)
            self.documento = digitos
            if self.tipo_pessoa == self.TipoPessoa.FISICA:
                validar_cpf(digitos)
            else:
                validar_cnpj(digitos)
        if self.cep:
            cep_digitos = somente_digitos(self.cep)
            if len(cep_digitos) != 8:
                raise ValidationError({"cep": "CEP deve ter 8 dígitos."})
            self.cep = cep_digitos

    @property
    def documento_formatado(self):
        d = self.documento
        if self.tipo_pessoa == self.TipoPessoa.FISICA and len(d) == 11:
            return f"{d[0:3]}.{d[3:6]}.{d[6:9]}-{d[9:11]}"
        if self.tipo_pessoa == self.TipoPessoa.JURIDICA and len(d) == 14:
            return f"{d[0:2]}.{d[2:5]}.{d[5:8]}/{d[8:12]}-{d[12:14]}"
        return d

    @property
    def cep_formatado(self):
        if len(self.cep) == 8:
            return f"{self.cep[0:5]}-{self.cep[5:8]}"
        return self.cep
