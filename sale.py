# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.
from trytond.model import fields
from trytond.pool import Pool, PoolMeta
from trytond.pyson import If, Bool, Eval

__all__ = ['Template', 'SaleLine', 'Sale']
__metaclass__ = PoolMeta


class Template:
    __name__ = 'product.template'

    minimum_quantity = fields.Float('Minimum Quantity',
        digits=(16, Eval('sale_uom', 2)), states={
            'readonly': ~Eval('active', True),
            'invisible': ~Eval('salable', False),
            }, depends=['active', 'salable', 'sale_uom'])


class SaleLine:
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


class Sale:
    __name__ = 'sale.sale'

    @classmethod
    def __setup__(cls):
        super(Sale, cls).__setup__()
        cls._error_messages.update({
                'invalid_amount': ('The total amount (%s) of the sale %s it '
                'is not permitted, by the minimum amount (%s).'),
                })

    @classmethod
    def check_minimum_amount(cls, sales):
        Config = Pool().get('sale.configuration')
        config = Config(1)
        for sale in sales:
            if sale.total_amount < config.minimum_amount:
                cls.raise_user_error('invalid_amount', (sale.total_amount,
                        sale.rec_name, config.minimum_amount))

    @classmethod
    def quote(cls, sales):
        cls.check_minimum_amount(sales)
        super(Sale, cls).quote(sales)
