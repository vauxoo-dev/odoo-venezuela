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
# from openerp.exceptions import except_orm, ValidationError
# from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT


class TestFiscalRequirements(TransactionCase):
    """ Test of withholding IVA """

    def setUp(self):
        """Seudo-constructor method"""
        super(TestFiscalRequirements, self).setUp()
        # self.doc_obj = self.env['account.wh.iva']
        # self.doc_line_obj = self.env['account.wh.iva.line']
        self.invoice_obj = self.env['account.invoice']
        self.invoice_line_obj = self.env['account.invoice.line']
        self.period_obj = self.env['account.period']
        self.move_obj = self.env['account.move']
        self.w_ncontrol = self.env['wiz.nroctrl']
        self.rates_obj = self.env['res.currency.rate']
        # self.txt_iva_obj = self.env['txt.iva']
        # self.txt_line_obj = self.env['txt.iva.line']
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
        self.tax_general = self.env.ref(
            'l10n_ve_fiscal_requirements.iva_purchase1')
        self.tax_except = self.env.ref(
            'l10n_ve_fiscal_requirements.iva_purchase3')
        self.tax_s_12 = self.env.ref(
            'l10n_ve_fiscal_requirements.iva_sale1')
        self.tax_s_0 = self.env.ref(
            'l10n_ve_fiscal_requirements.iva_sale3')
        self.company = self.env.ref(
            'base.main_partner')

    def _create_invoice(self, type_inv='in_invoice'):
        """Function create invoice"""
        date_now = time.strftime(DEFAULT_SERVER_DATE_FORMAT)
        invoice_dict = {
            'partner_id': self.partner_amd.id,
            'nro_ctrl': '2000-694351',
            'date_invoice': date_now,
            'date_document': date_now,
            'type': type_inv,
            'reference_type': 'none',
            'name': 'invoice iva supplier',
            'account_id': self.partner_amd.property_account_receivable.id,
        }
        if type_inv == 'in_invoice':
            invoice_dict['supplier_invoice_number'] = 'libre-123456'
            account = self.partner_amd.property_account_payable.id
            invoice_dict['account_id'] = account
        return self.invoice_obj.create(invoice_dict)

    def _create_invoice_line(self, invoice_id=None, tax=None):
        """Create invoice line"""
        line_dict = {
            'product_id': self.product_ipad.id,
            'quantity': 1,
            'price_unit': 100,
            'name': self.product_ipad.name,
            'invoice_id': invoice_id,
        }
        if tax:
            line_dict['invoice_line_tax_id'] = [(6, 0, [tax.id])]
        return self.invoice_line_obj.create(line_dict)

    def test_01_create_customer_invoice(self):
        """Test create customer invoice"""
        # Create invoice customer
        invoice = self._create_invoice('out_invoice')
        # Check initial state
        self.assertEqual(
            invoice.state, 'draft', 'Initial state should be in "draft"'
        )
        # Create invoice line with tax general
        self._create_invoice_line(invoice.id, self.tax_s_12)
        # Set invoice state open
        invoice.signal_workflow('invoice_open')
        self.assertEqual(invoice.state, 'open', 'State in open')

    def test_02_create_supplier_invoice(self):
        """Test create supplier invoice"""
        # Create invoice supplier
        invoice = self._create_invoice('in_invoice')
        # Check initial state
        self.assertEqual(
            invoice.state, 'draft', 'Initial state should be in "draft"'
        )
        # Create invoice line with tax general
        self._create_invoice_line(invoice.id, self.tax_general)
        # Set invoice state open
        invoice.signal_workflow('invoice_open')
        self.assertEqual(invoice.state, 'open', 'State in open')

    def test_03_comercial_partner(self):
        """Test comercial partner"""
        # Create invoice customer
        date_now = time.strftime(DEFAULT_SERVER_DATE_FORMAT)
        invoice_dict = {
            'partner_id': self.comercial.id,
            'nro_ctrl': '2000-694351',
            'date_invoice': date_now,
            'date_document': date_now,
            'type': 'out_invoice',
            'reference_type': 'none',
            'name': 'invoice customer',
            'account_id': self.partner_amd.property_account_receivable.id,
        }
        invoice = self.invoice_obj.create(invoice_dict)
        # Check initial state
        self.assertEqual(
            invoice.state, 'draft', 'Initial state should be in "draft"'
        )
        # Create invoice line with tax general
        self._create_invoice_line(invoice.id, self.tax_s_12)
        # Set invoice state proforma2
        invoice.signal_workflow('invoice_proforma2')
        self.assertEqual(invoice.state, 'proforma2', 'State in proforma2')
        # Check no created journal entries
        self.assertEqual(invoice.move_id, self.move_obj,
                         'There should be no move')
        # Set invoice state open
        invoice.signal_workflow('invoice_open')
        self.assertEqual(invoice.state, 'open', 'State in open')
        # Check created journal entries
        self.assertNotEqual(invoice.move_id, self.move_obj,
                            'There should be move')
        partner = invoice.move_id.partner_id
        self.assertEqual(partner.id, self.parent_com.id,
                         'Partner move should be equal to parent partner of '
                         'the comercial')

    def test_04_wizard_number_control(self):
        """Test wizard change number control in invoice"""
        # Create invoice supplier
        invoice = self._create_invoice('in_invoice')
        # Check initial state
        self.assertEqual(
            invoice.state, 'draft', 'Initial state should be in "draft"'
        )
        # Create invoice line with tax general
        self._create_invoice_line(invoice.id, self.tax_general)
        # Set invoice state open
        invoice.signal_workflow('invoice_open')
        self.assertEqual(invoice.state, 'open', 'State in open')
        # Check number control
        self.assertEqual(invoice.nro_ctrl, '2000-694351',
                         'Number control bad')
        # Test wizard number control
        context = {'active_id': invoice.id}
        value = {'name': '987654321',
                 'sure': True}
        self.w_ncontrol.with_context(context).create(value).set_noctrl()
        self.assertEqual(invoice.nro_ctrl, '987654321',
                         'Number control no chance')
