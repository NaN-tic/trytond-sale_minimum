#This file is part of Tryton.  The COPYRIGHT file at the top level of
#this repository contains the full copyright notices and license terms.
from trytond.model import fields
from trytond.pool import PoolMeta
from trytond.config import config
DIGITS = config.getint('digits', 'unit_price_digits', 4)

__all__ = ['Configuration']
__metaclass__ = PoolMeta


class Configuration:
    __name__ = 'sale.configuration'

    minimum_amount = fields.Property(fields.Numeric('Minimal Amount Permited',
            digits=(16, DIGITS), required=True))
