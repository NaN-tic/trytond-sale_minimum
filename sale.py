# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.
from trytond.model import fields
from trytond.pool import Pool, PoolMeta
from trytond.pyson import Bool, Eval
from trytond.exceptions import UserError
from trytond.i18n import gettext


class Template(metaclass=PoolMeta):
    __name__ = 'product.template'

    minimum_quantity = fields.Float('Minimum Quantity',
        digits=(16, Eval('sale_uom', 2)), states={
            'invisible': ~Eval('salable', False),
            })


class Product(metaclass=PoolMeta):
    __name__ = 'product.product'


class Sale(metaclass=PoolMeta):
    __name__ = 'sale.sale'

    @classmethod
    def quote(cls, sales):
        for sale in sales:
            sale.check_minimum_quantity()
        return super().quote(sales)

    def check_minimum_quantity(self):
        for line in self.lines:
            if line.type != 'line':
                continue

            minimum_quantity = line.minimum_quantity
            if minimum_quantity is not None and line.quantity < minimum_quantity:
                raise UserError(gettext(
                    'sale_minimum.msg_minimum_quantity_error',
                    line=line.rec_name,
                    quantity=line.quantity,
                    min_quantity=line.minimum_quantity))


class SaleLine(metaclass=PoolMeta):
    __name__ = 'sale.line'

    minimum_quantity = fields.Function(fields.Float('Minimum Quantity',
        digits='unit', states={
            'invisible': ~Bool(Eval('minimum_quantity')),
        }, help='The quantity must be greater or equal than minimum quantity'),
        'on_change_with_minimum_quantity')

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

    @fields.depends(methods=['_notify_minimum_quantity'])
    def on_change_notify(self):
        notifications = super().on_change_notify()
        notifications.extend(self._notify_minimum_quantity())
        return notifications

    @fields.depends('type', 'product', 'quantity', 'minimum_quantity')
    def _notify_minimum_quantity(self):
        if self.type == 'line' and self.product:
            qty = self.quantity
            min_qty = self.minimum_quantity
            if (qty is not None and min_qty is not None and (qty < min_qty)):
                yield ('warning', gettext(
                        'sale_minimum.msg_line_minimum_quantity_error',
                        product=self.product.rec_name,
                        quantity=qty,
                        min_quantity=min_qty))
