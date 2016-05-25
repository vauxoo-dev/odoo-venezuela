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
from openerp.tests.common import TransactionCase
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT
from openerp.exceptions import except_orm
#, ValidationError


class TestFiscalBook(TransactionCase):
    """ Test of withholding IVA """

    def setUp(self):
        """Seudo-constructor method"""
        super(TestFiscalBook, self).setUp()
        self.doc_obj = self.env['account.wh.iva']
        self.doc_line_obj = self.env['account.wh.iva.line']
        self.book_obj = self.env['fiscal.book']
        self.invoice_obj = self.env['account.invoice']
        self.invoice_line_obj = self.env['account.invoice.line']
        self.period_obj = self.env['account.period']
        self.journal_obj = self.env['account.journal']
        self.rates_obj = self.env['res.currency.rate']
        self.partner_amd = self.env.ref(
            'l10n_ve_fiscal_requirements.f_req_partner_2')
        self.partner_nwh = self.env.ref(
            'l10n_ve_fiscal_requirements.f_req_partner_7')
        self.product_ipad = self.env.ref(
            'product.product_product_6_product_template')
        self.tax_general = self.env.ref(
            'l10n_ve_fiscal_requirements.iva_purchase1')
        self.tax_add = self.env.ref(
            'l10n_ve_fiscal_requirements.iva_purchase2')
        self.tax_except = self.env.ref(
            'l10n_ve_fiscal_requirements.iva_purchase3')
        self.tax_red = self.env.ref(
            'l10n_ve_fiscal_requirements.iva_purchase4')
        self.tax_s_12 = self.env.ref(
            'l10n_ve_fiscal_requirements.iva_sale1')
        self.tax_s_22 = self.env.ref(
            'l10n_ve_fiscal_requirements.iva_sale2')
        self.tax_s_0 = self.env.ref(
            'l10n_ve_fiscal_requirements.iva_sale3')
        self.tax_s_8 = self.env.ref(
            'l10n_ve_fiscal_requirements.iva_sale4')
        self.company = self.env.ref(
            'base.main_company')
        self.m_partner = self.env.ref(
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

    def test_01_testing_purchase_book(self):
        """ Testing purchase book"""
        # Set wh_iva_agent true in partner of the company
        self.m_partner.write({'wh_iva_agent': True})
        self.assertTrue(self.m_partner.wh_iva_agent, 'Should be True')
        # Create fiscal book
        period_id = self.period_obj.find()
        values = {
            'name': 'Fiscal Book Purchase',
            'type': 'purchase',
            'period_id': period_id.id,
            'company_id': self.company.id
        }
        book = self.book_obj.create(values)
        # Check fiscal book
        self.assertEqual(book.state, 'draft', 'State should be draft')
        self.assertEqual(book.type, 'purchase', 'Type should be purchase')
        self.assertEqual(book.article_number, '75',
                         'Article number should be number 75')

        # Check flow confirmed --> done --> cancel --> draft
        # Set state confirmed in fiscal book
        book.signal_workflow('act_confirm')
        self.assertEqual(book.state, 'confirmed', 'State should be confirmed')
        # Set state done in fiscal book
        book.signal_workflow('act_done')
        self.assertEqual(book.state, 'done', 'State should be done')
        # Set state cancel in fiscal book
        book.signal_workflow('act_cancel')
        self.assertEqual(book.state, 'cancel', 'State should be cancel')
        # Set state draft in fiscal book
        book.signal_workflow('act_draft')
        self.assertEqual(book.state, 'draft', 'State should be draft')

        # Check flow confirmed --> cancel --> draft
        # Set state confirmed in fiscal book
        book.signal_workflow('act_confirm')
        self.assertEqual(book.state, 'confirmed', 'State should be confirmed')
        # Set state cancel in fiscal book
        book.signal_workflow('act_cancel')
        self.assertEqual(book.state, 'cancel', 'State should be cancel')
        # Set state draft in fiscal book
        book.signal_workflow('act_draft')
        self.assertEqual(book.state, 'draft', 'State should be draft')

        # Check can not be added draft invoices
        # Create invoice supplier
        invoice = self._create_invoice('in_invoice')
        # Create invoice line with tax general
        self._create_invoice_line(invoice.id, self.tax_general)
        # Check initial state
        self.assertEqual(
            invoice.state, 'draft', 'Initial state should be in "draft"')
        # Update fiscal book
        book.update_book()
        # Check that not draft invoices
        draft_inv = [inv for inv in book.invoice_ids if inv.state == 'draft']
        self.assertEqual(len(draft_inv), 0,
                         'There should be no draft invoices')

        # Check can be added open invoices
        # Set invoice state open
        invoice.signal_workflow('invoice_open')
        self.assertEqual(invoice.state, 'open', 'State in open')
        # Update fiscal book
        book.update_book()
        self.assertIn(invoice, book.invoice_ids, 'The invoice is not added')

        # Check can be added paid invoices
        # Set invoice state paid
        account = self.env.ref('account.cash')
        journal = self.journal_obj.search([('type', '=', 'cash')])
        invoice.pay_and_reconcile(invoice.amount_total, account.id,
                                  period_id.id, journal.id, account.id,
                                  period_id.id, journal.id, name='Test Paid')
        self.assertEqual(invoice.state, 'paid', 'State in paid')
        # Clear book
        book.clear_book()
        # Update fiscal book
        book.update_book()
        self.assertIn(invoice, book.invoice_ids, 'The invoice is not added')

        # Check that an invoice associated to a book can only be cancel
        # when the purchase book is in cancel state.
        # Create invoice supplier
        invoice_2 = self._create_invoice('in_invoice')
        # Create invoice line with tax general
        self._create_invoice_line(invoice_2.id, self.tax_general)
        # Check initial state
        self.assertEqual(
            invoice_2.state, 'draft', 'Initial state should be in "draft"')
        # Set invoice state open
        invoice_2.signal_workflow('invoice_open')
        self.assertEqual(invoice_2.state, 'open', 'State in open')
        # Invoice journal to be able to cancel entries
        invoice_2.journal_id.update_posted = True
        self.assertTrue(invoice_2.journal_id.update_posted,
                        'The attribute was not correctly updated')
        # Update fiscal book
        book.update_book()
        self.assertIn(invoice_2, book.invoice_ids, 'The invoice is not added')
        # Check book in state draft
        self.assertEqual(book.state, 'draft', 'State book should be draft')
        # Try to cancel the invoice
        with self.assertRaises(except_orm):
            invoice_2.signal_workflow('invoice_cancel')
        # # Set state confirmed in fiscal book
        # book.signal_workflow('act_confirm')
        # self.assertEqual(book.state, 'confirmed', 'State should be confirmed')
        # # Try to cancel the invoice
        # with self.assertRaises(except_orm):
        #     invoice_2.signal_workflow('invoice_cancel')
        # print invoice_2.state
        # # Set state cancel in fiscal book
        # book.signal_workflow('act_cancel')
        # self.assertEqual(book.state, 'cancel', 'State should be cancel')
