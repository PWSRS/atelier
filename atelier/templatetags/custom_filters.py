# atelier/templatetags/custom_filters.py
from django import template

register = template.Library()

@register.filter(name='formatar_telefone')
def formatar_telefone(value):
    """
    Formata um número de telefone para o formato (XX) XXXXX-XXXX
    """
    # Remove qualquer caractere que não seja número
    telefone = ''.join(filter(str.isdigit, str(value)))
    
    if len(telefone) == 11:
        return f"({telefone[:2]}) {telefone[2:7]}-{telefone[7:]}"
    elif len(telefone) == 10:
        return f"({telefone[:2]}) {telefone[2:6]}-{telefone[6:]}"
    
    return value # Retorna o valor original se não tiver 10 ou 11 dígitos

@register.filter(name='formatar_moeda')
def formatar_moeda(value):
    """
    Formata um número para o formato de moeda Real (R$ X.XXX,XX)
    """
    try:
        # Garante que é um Decimal
        valor = Decimal(str(value))
        return f"R$ {valor:,.2f}".replace(",", "v").replace(".", ",").replace("v", ".")
    except (ValueError, TypeError, InvalidOperation):
        return value # Retorna o valor original se não conseguir formatar