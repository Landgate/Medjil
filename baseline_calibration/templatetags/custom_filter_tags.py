from django import template
from math import log10 , floor

register = template.Library()

@register.filter
def multiply(value, arg):
    if value=='': return ''
    if value==0: return 0
    return value * arg


@register.filter
def sigfigs(x, sig):
    if x=='': return ''
    if x==0: return 0
    rnd=sig-int(floor(log10(abs(x))))-1
    aVal = round(x, rnd)
    if rnd <= 0: rnd=0
    fmt="{:."+str(rnd)+"f}"
    return(fmt.format(aVal))