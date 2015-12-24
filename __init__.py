# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.
from trytond.pool import Pool
from .sale import *
from .configuration import *

def register():
    Pool.register(
        Configuration,
        Sale,
        SaleLine,
        Template,
        module='sale_minimum', type_='model')
