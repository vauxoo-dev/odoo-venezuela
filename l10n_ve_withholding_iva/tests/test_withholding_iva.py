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
# from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT


class TestIvaWithholding(TransactionCase):
    ''' Test of withholding IVA'''

    def setUp(self):
        '''Seudo-constructor method'''
        super(TestIvaWithholding, self).setUp()
        self.doc_obj = self.env['account.wh.iva']
        self.doc_line_obj = self.env['account.wh.iva.line']
        self.invoice_obj = self.env['account.invoice']
        self.invoice_line_obj = self.env['account.invoice.line']
        self.rates_obj = self.env['res.currency.rate']
        self.txt_iva_obj = self.env['txt.iva']
        self.partner_amd = self.env.ref(
            'l10n_ve_fiscal_requirements.f_req_partner_2')
        self.partner_nwh = self.env.ref(
            'l10n_ve_fiscal_requirements.f_req_partner_7')
        self.product_ipad = self.env.ref(
            'product.product_product_6_product_template')
        self.tax_general = self.env.ref(
            'l10n_ve_fiscal_requirements.iva_purchase1')
        self.tax_except = self.env.ref(
            'l10n_ve_fiscal_requirements.iva_purchase3')
        self.company = self.env.ref(
            'base.main_partner')

    def _create_invoice(self, type_inv='in_invoice'):
        '''Function create invoice'''
        date_now = time.strftime(DEFAULT_SERVER_DATE_FORMAT)
        invoice_dict = {
            'partner_id': self.partner_amd.id,
            'nro_ctrl': '2000-694351',
            'date_invoice': date_now,
            'date_document': date_now,
            'type': type_inv,
            'reference_type': 'none',
            'name': 'invoice iva supplier',
            'account_id': self.partner_amd.property_account_payable.id,
        }
        return self.invoice_obj.create(invoice_dict)

    def _create_invoice_line(self, invoice_id=None, tax=None):
        '''Create invoice line'''
        line_dict = {
            'product_id': self.product_ipad.id,
            'quantity': 1,
            'price_unit': 100,
            'name': self.product_ipad.name,
            'invoice_id': invoice_id,
        }
        if tax:
            line_dict['invoice_line_tax_id'] = [(6, 0, [self.tax_general.id])]
        return self.invoice_line_obj.create(line_dict)

    def test_01_validate_process_withholding_iva(self):
        '''Test create invoice supplier with data initial and
        Test validate invoice with document withholding iva'''
        invoice = self._create_invoice('in_invoice')
        # Check initial state
        self.assertEqual(
            invoice.state, 'draft', 'Initial state should be in "draft"'
        )
        self._create_invoice_line(invoice.id, True)
        invoice.signal_workflow('invoice_open')
        self.assertEqual(invoice.state, 'open', 'State in open')
        self.assertNotEqual(invoice.wh_iva_id, self.doc_obj,
                            'Not should be empty the withholding document')
        invoice_c = invoice.copy()
        self.assertEqual(invoice_c.wh_iva, False, 'WH_IVA should be False')
        self.assertEqual(invoice_c.vat_apply, False,
                         'Vat Apply should be False')
        self.assertEqual(invoice_c.wh_iva_id, self.doc_obj,
                         'Withholding document the invoice copy'
                         'should be empty')

        iva_wh = invoice.wh_iva_id

        self.assertEqual(iva_wh.state, 'draft',
                         'State of withholding should be in draft')
        self.assertEqual(len(iva_wh.wh_lines), 1, 'Should exist a record')
        self.assertEqual(iva_wh.amount_base_ret, 100.00,
                         'Amount total should be 100.00')
        self.assertEqual(iva_wh.total_tax_ret, 9.00,
                         'Amount total should be 9.00')

        iva_wh.signal_workflow('wh_iva_confirmed')
        self.assertEqual(iva_wh.state, 'confirmed',
                         'State of withholding should be in confirmed')
        iva_wh.signal_workflow('wh_iva_done')
        self.assertEqual(iva_wh.state, 'done',
                         'State of withholding should be in done')
        self.assertEqual(len(invoice.payment_ids), 1, 'Should exits a payment')
        self.assertEqual(invoice.residual,
                         invoice.amount_total - iva_wh.total_tax_ret,
                         'Amount residual invoice should be equal amount '
                         'total - amount wh')
        debit = 0
        credit = 0
        for doc_inv in iva_wh.wh_lines:
            for line in doc_inv.move_id.line_id:
                if line.debit > 0:
                    debit += line.debit
                    self.assertEqual(line.account_id.id, invoice.account_id.id,
                                     'Account should be equal to account '
                                     'invoice')
                else:
                    credit += line.credit
                    account = self.tax_general.wh_vat_collected_account_id
                    self.assertEqual(line.account_id.id,
                                     account.id,
                                     'Account should be equal to account '
                                     'tax for withholding')
        self.assertEqual(debit, credit, 'Debit and Credit should be equal')
        self.assertEqual(debit, iva_wh.total_tax_ret,
                         'Amount total withholding should be equal '
                         'journal entrie')

    def test_02_withholding_partner_not_agent(self):
        '''Test withholding with partner not agent'''
        date_now = time.strftime(DEFAULT_SERVER_DATE_FORMAT)
        invoice_dict = {
            'partner_id': self.partner_nwh.id,
            'nro_ctrl': '2000-694351',
            'date_invoice': date_now,
            'date_document': date_now,
            'type': 'in_invoice',
            'reference_type': 'none',
            'name': 'invoice iva supplier',
            'account_id': self.partner_nwh.property_account_payable.id,
        }
        invoice = self.invoice_obj.create(invoice_dict)
        line_dict = {
            'product_id': self.product_ipad.id,
            'quantity': 1,
            'price_unit': 100,
            'name': self.product_ipad.name,
            'invoice_id': invoice.id,
            'invoice_line_tax_id': [(6, 0, [self.tax_general.id])],
        }
        self.invoice_line_obj.create(line_dict)
        invoice.signal_workflow('invoice_open')
        iva_wh = invoice.wh_iva_id
        self.assertEqual(invoice.state, 'open', 'State in open')
        self.assertNotEqual(invoice.wh_iva_id, self.doc_obj,
                            'Not should be empty the withholding document')

        self.assertEqual(iva_wh.state, 'draft',
                         'State of withholding should be in draft')
        self.assertEqual(len(iva_wh.wh_lines), 1, 'Should exist a record')
        self.assertEqual(iva_wh.amount_base_ret, 100.00,
                         'Amount total should be 100.00')
        self.assertEqual(iva_wh.total_tax_ret, 12.00,
                         'Amount total should be 12.00')

    def test_03_not_withholding_partner_not_agent(self):
        '''Test not withholding with partner not agent'''
        date_now = time.strftime(DEFAULT_SERVER_DATE_FORMAT)
        invoice_dict = {
            'partner_id': self.partner_nwh.id,
            'nro_ctrl': '2000-694351',
            'date_invoice': date_now,
            'date_document': date_now,
            'type': 'in_invoice',
            'reference_type': 'none',
            'name': 'invoice iva supplier',
            'account_id': self.partner_nwh.property_account_payable.id,
        }
        invoice = self.invoice_obj.create(invoice_dict)
        line_dict = {
            'product_id': self.product_ipad.id,
            'quantity': 1,
            'price_unit': 100,
            'name': self.product_ipad.name,
            'invoice_id': invoice.id,
            'invoice_line_tax_id': [(6, 0, [self.tax_except.id])],
        }
        self.invoice_line_obj.create(line_dict)
        invoice.signal_workflow('invoice_open')
        self.assertEqual(invoice.state, 'open', 'State in open')
        self.assertEqual(invoice.wh_iva_id, self.doc_obj,
                         'Should be empty the withholding document')

    def test_04_not_withholding_company_not_agent(self):
        '''Test not withholding with company not agent, partner not agent'''
        self.company.write({'wh_iva_agent': False})
        self.assertEqual(self.company.wh_iva_agent, False, 'Should be False')
        date_now = time.strftime(DEFAULT_SERVER_DATE_FORMAT)
        invoice_dict = {
            'company_id': self.company.id,
            'partner_id': self.partner_nwh.id,
            'nro_ctrl': '2000-694351',
            'date_invoice': date_now,
            'date_document': date_now,
            'type': 'in_invoice',
            'reference_type': 'none',
            'name': 'invoice iva supplier',
            'account_id': self.partner_nwh.property_account_payable.id,
        }
        invoice = self.invoice_obj.create(invoice_dict)
        line_dict = {
            'product_id': self.product_ipad.id,
            'quantity': 1,
            'price_unit': 100,
            'name': self.product_ipad.name,
            'invoice_id': invoice.id,
            'invoice_line_tax_id': [(6, 0, [self.tax_except.id])],
        }
        self.invoice_line_obj.create(line_dict)
        invoice.signal_workflow('invoice_open')
        self.assertEqual(invoice.state, 'open', 'State in open')
        self.assertEqual(invoice.wh_iva_id, self.doc_obj,
                         'Should be empty the withholding document')

    def test_05_not_withholding_company_not_agent_partner_agent(self):
        '''Test not withholding with company not agent, partner agent'''
        self.company.write({'wh_iva_agent': False})
        self.assertEqual(self.company.wh_iva_agent, False, 'Should be False')
        date_now = time.strftime(DEFAULT_SERVER_DATE_FORMAT)
        invoice_dict = {
            'company_id': self.company.id,
            'partner_id': self.partner_amd.id,
            'nro_ctrl': '2000-694351',
            'date_invoice': date_now,
            'date_document': date_now,
            'type': 'in_invoice',
            'reference_type': 'none',
            'name': 'invoice iva supplier',
            'account_id': self.partner_nwh.property_account_payable.id,
        }
        invoice = self.invoice_obj.create(invoice_dict)
        line_dict = {
            'product_id': self.product_ipad.id,
            'quantity': 1,
            'price_unit': 100,
            'name': self.product_ipad.name,
            'invoice_id': invoice.id,
            'invoice_line_tax_id': [(6, 0, [self.tax_general.id])],
        }
        self.invoice_line_obj.create(line_dict)
        invoice.signal_workflow('invoice_open')
        self.assertEqual(invoice.state, 'open', 'State in open')
        self.assertEqual(invoice.wh_iva_id, self.doc_obj,
                         'Should be empty the withholding document')

    # def test_06_txt_document_iva(self):
    #     '''Test create document txt vat'''
