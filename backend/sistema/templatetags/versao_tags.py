from django import template

from sistema.models import VersaoSistema

register = template.Library()


@register.simple_tag
def versao_atual():
    return VersaoSistema.atual()
