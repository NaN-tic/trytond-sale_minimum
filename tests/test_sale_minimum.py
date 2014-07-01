#!/usr/bin/env python
# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.
import doctest
import unittest
from decimal import Decimal

import trytond.tests.test_tryton
from trytond.tests.test_tryton import POOL, DB_NAME, USER, CONTEXT, test_view,\
    test_depends
from trytond.transaction import Transaction


class TestCase(unittest.TestCase):
    'Test module'

    def setUp(self):
        trytond.tests.test_tryton.install_module('sale_minimum')
        self.user = POOL.get('res.user')
        self.uom = POOL.get('product.uom')
        self.category = POOL.get('product.category')
        self.template = POOL.get('product.template')
        self.product = POOL.get('product.product')
        self.company = POOL.get('company.company')
        self.party = POOL.get('party.party')
        self.account = POOL.get('account.account')
        self.payment_term = POOL.get('account.invoice.payment_term')
        self.sale = POOL.get('sale.sale')
        self.sale_line = POOL.get('sale.line')

    def test0005views(self):
        'Test views'
        test_view('sale_minimum')

    def test0006depends(self):
        'Test depends'
        test_depends()

    def test0010on_change_product_quantity(self):
        '''
        Test minimum_quantity calculation in on_change_product and
        on_change_quantity
        '''
        with Transaction().start(DB_NAME, USER, context=CONTEXT):
            company, = self.company.search([
                    ('rec_name', '=', 'Dunder Mifflin'),
                    ])
            self.user.write([self.user(USER)], {
                'main_company': company.id,
                'company': company.id,
                })

            # Prepare product
            uom, = self.uom.search([
                    ('name', '=', 'Unit'),
                    ])
            category, = self.category.create([{'name': 'ProdCategoryTest'}])
            template, = self.template.create([{
                        'name': 'ProductTest',
                        'default_uom': uom.id,
                        'category': category.id,
                        'account_category': True,
                        'list_price': Decimal(10),
                        'cost_price': Decimal(0),
                        'salable': True,
                        'sale_uom': uom.id,
                        'minimum_quantity': 5,
                        }])
            product, = self.product.create([{
                        'template': template.id,
                        }])

            # Prepare customer
            receivable, = self.account.search([
                ('kind', '=', 'receivable'),
                ('company', '=', company.id),
                ])
            payable, = self.account.search([
                ('kind', '=', 'payable'),
                ('company', '=', company.id),
                ])
            customer, = self.party.create([{
                        'name': 'customer',
                        'addresses': [
                            ('create', [{}]),
                            ],
                        'account_receivable': receivable.id,
                        'account_payable': payable.id,
                        }])

            # Prepare sale
            payment_term, = self.payment_term.create([{
                        'name': 'Payment Term',
                        'lines': [
                            ('create', [{
                                        'sequence': 0,
                                        'type': 'remainder',
                                        'months': 0,
                                        'days': 0,
                                        }])]
                        }])
            sale, = self.sale.create([{
                        'party': customer.id,
                        'company': company.id,
                        'payment_term': payment_term.id,
                        'currency': company.currency.id,
                        'invoice_address': customer.addresses[0].id,
                        'shipment_address': customer.addresses[0].id,
                        'lines': [],
                        }])

            # Check on_change_product
            sale_line = self.sale_line(sale=sale)
            sale_line.product = product
            sale_line.quantity = None
            sale_line.unit = None
            on_change_product_res = sale_line.on_change_product()
            self.assertEqual(on_change_product_res['quantity'], 5)
            self.assertEqual(on_change_product_res['minimum_quantity'], 5)

            # Check on_change_quantity with quantity > minimum
            sale_line.quantity = 6
            on_change_quantity_res = sale_line.on_change_quantity()
            self.assertNotIn('quantity', on_change_quantity_res)
            self.assertIsNone(on_change_quantity_res['minimum_quantity'])

            # Check on_change_quantity with quantity > minimum
            sale_line.quantity = 3
            on_change_quantity_res = sale_line.on_change_quantity()
            self.assertEqual(on_change_quantity_res['quantity'], 5)
            self.assertEqual(on_change_quantity_res['minimum_quantity'], 5)


def suite():
    suite = trytond.tests.test_tryton.suite()
    from trytond.modules.company.tests import test_company
    for test in test_company.suite():
        if test not in suite:
            suite.addTest(test)
    from trytond.modules.account.tests import test_account
    for test in test_account.suite():
        if test not in suite and not isinstance(test, doctest.DocTestCase):
            suite.addTest(test)
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestCase))
    return suite
