# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.
from trytond.model import fields
from trytond.pool import Pool, PoolMeta
from trytond.pyson import If, Bool, Eval
from trytond.transaction import Transaction
from trytond.exceptions import UserError
from trytond.i18n import gettext


class Template(metaclass=PoolMeta):
    __name__ = 'product.template'

    minimum_quantity = fields.Float('Minimum Quantity',
        digits=(16, Eval('sale_uom', 2)), states={
            'readonly': ~Eval('active', True),
            'invisible': ~Eval('salable', False),
            }, depends=['active', 'salable', 'sale_uom'])


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

            min_quantity = line.get_minimum_quantity()
            if line.quantity < min_quantity:
                raise UserError(gettext('sale_minimum.msg_minimum_quantity_error',
                                        line=line.rec_name,
                                        quantity=line.quantity,
                                        min_quantity=min_quantity))


class SaleLine(metaclass=PoolMeta):
    __name__ = 'sale.line'

    minimum_quantity = fields.Float('Minimum Quantity', readonly=True,
        digits='unit', states={
            'invisible': ~Bool(Eval('minimum_quantity')) | (Eval('type') != 'line'),
        }, help='The quantity must be greater or equal than minimum quantity')

    @classmethod
    def __setup__(cls):
        super(SaleLine, cls).__setup__()
        minimum_domain = If(
                (Eval('type') == 'line') & (Eval('sale_state') == 'draft') & Bool(Eval('minimum_quantity', 0)),
                ('quantity', '>=', Eval('minimum_quantity', 0)),
                ())
        cls.quantity.domain.append(minimum_domain)
        for _field in ('type', 'sale_state', 'minimum_quantity'):
            if not _field in cls.quantity.depends:
                cls.quantity.depends.add(_field)

    @classmethod
    def __register__(cls, module_name):
        cursor = Transaction().connection.cursor()
        table = cls.__table_handler__(module_name)
        sql_table = cls.__table__()

        # Migration from 6.8: minium quantity is not function field
        has_minimum_quantity = table.column_exist('minimum_quantity')

        super().__register__(module_name)
        if not has_minimum_quantity:
            cursor.execute(*sql_table.update(
                    [sql_table.minimum_quantity], [sql_table.quantity],
                    where=sql_table.quantity != None))

    @fields.depends('product', 'unit')
    def on_change_product(self):
        super().on_change_product()
        self.minimum_quantity = self.get_minimum_quantity()

    def get_minimum_quantity(self):
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
