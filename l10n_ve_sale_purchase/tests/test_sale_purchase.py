#!/usr/bin/python
# -*- coding: utf-8 -*-
###############################################################################
#    Module Written to OpenERP, Open Source Management Solution
#    Copyright (C) OpenERP Venezuela (<http://openerp.com.ve>).
#    All Rights Reserved
###############################################################################
#    Credits:
#    Coded by: Edgar Rivero <edgar@vauxoo.com>
#    Audited by: Humberto Arocha <hbto@vauxoo.com>
###############################################################################
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published
#    by the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
###############################################################################
import time
# from datetime import datetime, timedelta
from openerp.tests.common import TransactionCase
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT
# from openerp.exceptions import ValidationError
# from openerp.exceptions import except_orm, ValidationError
# from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT


class TestSalePurchase(TransactionCase):
    """ Test of l10_ve_sale_purchase """

    def setUp(self):
        """Seudo-constructor method"""
        super(TestSalePurchase, self).setUp()
        self.purchase_obj = self.env['purchase.order']
        self.pur_line_obj = self.env['purchase.order.line']
        self.sale_obj = self.env['sale.order']
        self.sal_line_obj = self.env['sale.order.line']
        self.picking_obj = self.env['stock.picking']
        self.partner_obj = self.env['res.partner']
        self.invoice_obj = self.env['account.invoice']
        self.invoice_line_obj = self.env['account.invoice.line']
        self.period_obj = self.env['account.period']
        self.move_obj = self.env['account.move']
        self.rates_obj = self.env['res.currency.rate']
        self.partner_amd = self.env.ref(
            'l10n_ve_fiscal_requirements.f_req_partner_2')
        self.partner_nwh = self.env.ref(
            'l10n_ve_fiscal_requirements.f_req_partner_7')
        self.comercial = self.env.ref(
            'l10n_ve_fiscal_requirements.f_req_partner_10')
        self.parent_com = self.env.ref(
            'base.res_partner_23')
        self.product_ipad = self.env.ref(
            'product.product_product_6_product_template')
        self.product_pc = self.env.ref(
            'product.product_product_3_product_template')
        self.tax_general = self.env.ref(
            'l10n_ve_fiscal_requirements.iva_purchase1')
        self.tax_except = self.env.ref(
            'l10n_ve_fiscal_requirements.iva_purchase3')
        self.tax_s_12 = self.env.ref(
            'l10n_ve_fiscal_requirements.iva_sale1')
        self.tax_s_0 = self.env.ref(
            'l10n_ve_fiscal_requirements.iva_sale3')
        self.a_sale = self.env.ref(
            'account.a_sale')
        self.main_partner = self.env.ref(
            'base.main_partner')
        self.company = self.env.ref(
            'base.main_company')
        self.currency_usd = self.env.ref('base.USD')
        self.currency_eur = self.env.ref('base.EUR')
        self.location = self.env.ref('stock.stock_location_stock')
        self.pricelist = self.env.ref('product.list0')
        self.no_concept = self.env.ref(
            'l10n_ve_withholding_islr.islr_wh_concept_no_apply_withholding')

    def test_01_purchase_order(self):
        """Test Purchase Order"""
        # Create purchase order
        date_now = time.strftime(DEFAULT_SERVER_DATE_FORMAT)
        pur_ord = self.purchase_obj.create({
            'date_order': date_now,
            'location_id': self.location.id,
            'partner_id': self.partner_amd.id,
            'invoice_method': 'order',
            'pricelist_id': self.pricelist.id,
        })
        self.pur_line_obj.create({
            'product_id': self.product_pc.id,
            'product_qty': 3,
            'price_unit': 10,
            'name': 'PC3',
            'date_planned': date_now,
            'order_id': pur_ord.id,
            'concept_id': self.no_concept.id,
        })
        self.pur_line_obj.create({
            'product_id': self.product_ipad.id,
            'product_qty': 5,
            'price_unit': 5,
            'name': 'Ipad',
            'date_planned': date_now,
            'order_id': pur_ord.id,
            'concept_id': self.no_concept.id,
        })
        # Check state purchase order
        self.assertEqual(pur_ord.state, 'draft', 'State should be draft')
        # Set purchase order state approved
        pur_ord.signal_workflow('purchase_confirm')
        self.assertEqual(pur_ord.state, 'approved', 'State should be confirm')
        # Check stock picking created
        picking = self.picking_obj.search([('origin', '=', pur_ord.name)])
        self.assertEqual(len(picking), 1, 'Picking not created')
        self.assertEqual(picking.state, 'assigned',
                         'State picking should be equal to assigned')
        self.assertEqual(len(picking.move_lines), 2,
                         'Quantity lines incorrect')
        # Check invoice created
        self.assertEqual(len(pur_ord.invoice_ids), 1,
                         'There should be a created invoice')
        self.assertEqual(pur_ord.invoice_ids.state, 'draft',
                         'State invoice should be draft')
        pur_ord.invoice_ids.signal_workflow('invoice_open')
        self.assertEqual(pur_ord.invoice_ids.state, 'open',
                         'State invoice should be open')

