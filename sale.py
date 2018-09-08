# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.
from trytond.model import fields
from trytond.pool import Pool, PoolMeta
from trytond.pyson import If, Bool, Eval

__all__ = ['Template', 'SaleLine']


class Template(metaclass=PoolMeta):
    __name__ = 'product.template'

    minimum_quantity = fields.Float('Minimum Quantity',
        digits=(16, Eval('sale_uom', 2)), states={
            'readonly': ~Eval('active', True),
            'invisible': ~Eval('salable', False),
            }, depends=['active', 'salable', 'sale_uom'])


class SaleLine(metaclass=PoolMeta):
    __name__ = 'sale.line'

    minimum_quantity = fields.Function(fields.Float('Minimum Quantity',
            digits=(16, Eval('unit_digits', 2)),
            states={
                'invisible': ~Bool(Eval('minimum_quantity')),
                },
            depends=['unit_digits'], help='The quantity must be greater or '
            'equal than minimum quantity'),
        'on_change_with_minimum_quantity')

    @classmethod
    def __setup__(cls):
        super(SaleLine, cls).__setup__()
        minimum_domain = If(Bool(Eval('minimum_quantity', 0)),
                ('quantity', '>=', Eval('minimum_quantity', 0)),
                ())
        if not 'minimum_quantity' in cls.quantity.depends:
            cls.quantity.domain.append(minimum_domain)
            cls.quantity.depends.append('minimum_quantity')

    @fields.depends('product', 'unit')
    def on_change_with_minimum_quantity(self, name=None):
        Uom = Pool().get('product.uom')
        if not self.product:
            return
        minimum_quantity = self.product.minimum_quantity
        if minimum_quantity:
            uom_category = self.product.sale_uom.category
            if self.unit and self.unit in uom_category.uoms:
                minimum_quantity = Uom.compute_qty(self.product.sale_uom,
                    minimum_quantity, self.unit)
        return minimum_quantity
