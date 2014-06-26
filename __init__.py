# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.
from trytond.pool import Pool
from .sale import *

def register():
    Pool.register(
        SaleLine,
        Template,
        module='sale_minimum', type_='model')
