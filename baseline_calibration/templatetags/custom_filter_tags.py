'''

   © 2025 Western Australian Land Information Authority

   Licensed under the Apache License, Version 2.0 (the "License");
   you may not use this file except in compliance with the License.
   You may obtain a copy of the License at

       http://www.apache.org/licenses/LICENSE-2.0

   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License.

'''
from django import template
from math import log10 , floor

register = template.Library()

@register.filter
def multiply(value, arg):
    if value=='': return 0
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


@register.filter
def style_for_E(value):
    if abs(value) > 1:
        # style with red fill
        return 'style="background-color:rgba(255, 0, 0, 0.4);"'
    elif abs(value) > 0.75:
        # style with orange fill
        return 'style="background-color:rgba(255, 165, 0, 0.4);"'
    return ''