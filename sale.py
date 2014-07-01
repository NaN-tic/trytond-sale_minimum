# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.
from trytond.model import fields
from trytond.pool import Pool, PoolMeta
from trytond.pyson import Bool, Eval

__all__ = ['Template', 'SaleLine']
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

    minimum_quantity = fields.Float('Minimum Quantity', readonly=True,
        digits=(16, Eval('unit_digits', 2)), states={
            'invisible': ~Bool(Eval('minimum_quantity')),
            }, depends=['unit_digits'],
        help='The quantity must be greater or equal than minimum quantity')

    @fields.depends('minimum_quantity')
    def on_change_product(self):
        minimum_quantity = self._get_minimum_quantity()
        if minimum_quantity and (not self.quantity or
                self.quantity < minimum_quantity):
            self.quantity = minimum_quantity
        else:
            minimum_quantity = None

        res = super(SaleLine, self).on_change_product()
        if minimum_quantity:
            res['minimum_quantity'] = minimum_quantity
            res['quantity'] = minimum_quantity
        else:
            res['minimum_quantity'] = None
        return res

    @fields.depends('minimum_quantity')
    def on_change_quantity(self):
        minimum_quantity = None
        if self.quantity:
            minimum_quantity = self._get_minimum_quantity()
            if minimum_quantity and self.quantity < minimum_quantity:
                self.quantity = minimum_quantity
            else:
                minimum_quantity = None

        res = super(SaleLine, self).on_change_quantity()
        if minimum_quantity:
            res['minimum_quantity'] = minimum_quantity
            res['quantity'] = minimum_quantity
        else:
            res['minimum_quantity'] = None
        return res

    @fields.depends('product', '_parent_sale.party', 'quantity', 'unit',
        'minimum_quantity')
    def _get_minimum_quantity(self):
        Uom = Pool().get('product.uom')
        if not self.product or not self.sale.party:
            return
        minimum_quantity = self.product.minimum_quantity
        if minimum_quantity:
            uom_category = self.product.sale_uom.category
            if self.unit and self.unit in uom_category.uoms:
                minimum_quantity = Uom.compute_qty(self.product.sale_uom,
                    minimum_quantity, self.unit)
        return minimum_quantity
