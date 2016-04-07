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
from datetime import datetime, timedelta
from openerp.tests.common import TransactionCase
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT


class TestIslrWithholding(TransactionCase):
    ''' Test of withholding ISLR'''

    def setUp(self):
        '''Seudo-constructor method'''
        super(TestIslrWithholding, self).setUp()
        self.doc_obj = self.env['islr.wh.doc']
        self.doc_line_obj = self.env['islr.wh.doc.line']
        self.invoice_obj = self.env['account.invoice']
        self.invoice_line_obj = self.env['account.invoice.line']
        self.rates_obj = self.env['res.currency.rate']
        self.partner_amd = self.env.ref(
            'l10n_ve_fiscal_requirements.f_req_partner_2')
        self.product_ipad = self.env.ref(
            'product.product_product_6_product_template')
        self.concept = self.env.ref(
            'l10n_ve_withholding_islr.islr_wh_concept_pago_contratistas_demo')
        self.concept_wo_account = self.env.ref(
            'l10n_ve_withholding_islr.islr_wh_concept_pago_contratistas')
        self.tax_general = self.env.ref(
            'l10n_ve_fiscal_requirements.iva_purchase1')
        self.currency_usd = self.env.ref('base.USD')

    def _create_invoice(self, type_inv='in_invoice', currency=False):
        '''Function create invoice'''
        date_now = time.strftime(DEFAULT_SERVER_DATE_FORMAT)
        invoice_dict = {
            'partner_id': self.partner_amd.id,
            'nro_ctrl': '2000-694351',
            'date_invoice': date_now,
            'date_document': date_now,
            'type': type_inv,
            'reference_type': 'none',
            'name': 'invoice islr supplier',
            'account_id': self.partner_amd.property_account_payable.id,
        }
        if currency:
            invoice_dict['currency_id'] = currency
        return self.invoice_obj.create(invoice_dict)

    def _create_invoice_line(self, invoice_id=None, concept=None):
        '''Create invoice line'''
        line_dict = {
            'product_id': self.product_ipad.id,
            'quantity': 1,
            'price_unit': 100,
            'name': self.product_ipad.name,
            'concept_id': concept,
            'invoice_id': invoice_id,
            # 'invoice_line_tax_id': [(6, 0, [self.tax_general.id])],
        }
        return self.invoice_line_obj.create(line_dict)

    def test_01_validate_process_withholding_islr(self):
        '''Test create invoice supplier with data initial and
        Test validate invoice with document withholding islr'''
        invoice = self._create_invoice('in_invoice')
        # Check initial state
        # import pdb; pdb.set_trace()
        self.assertEqual(
            invoice.state, 'draft', 'Initial state should be in "draft"'
        )
        # invoice_line = self._create_invoice_line(invoice)
        self._create_invoice_line(invoice.id, self.concept.id)
        invoice.signal_workflow('invoice_open')
        self.assertEqual(
            invoice.state, 'open', 'State in open'
        )
        self.assertNotEqual(invoice.islr_wh_doc_id, self.doc_obj,
            'Not should be empty the withholding document'
        )
        islr_wh = invoice.islr_wh_doc_id

        self.assertEqual(islr_wh.state, 'draft',
            'State of withholding should be in draft'
        )
        self.assertEqual(len(islr_wh.concept_ids), 1, 'Should exist a record')
        self.assertEqual(len(islr_wh.invoice_ids), 1, 'Should exist a invoice')
        self.assertEqual(islr_wh.amount_total_ret, 2.00,
            'Amount total should be 2.00'
        )
        islr_wh.signal_workflow('act_confirm')
        self.assertEqual(islr_wh.state, 'confirmed',
            'State of withholding should be in confirmed'
        )
        islr_wh.signal_workflow('act_done')
        self.assertEqual(islr_wh.state, 'done',
            'State of withholding should be in done'
        )
        self.assertEqual(len(invoice.payment_ids), 1, 'Should exits a payment')
        self.assertEqual(invoice.residual,
            invoice.amount_total - islr_wh.amount_total_ret,
            'Amount residual invoice should be equal amount total - amount wh'
        )
        debit = 0
        credit = 0
        for doc_inv in islr_wh.invoice_ids:
            for line in doc_inv.move_id.line_id:
                if line.debit > 0:
                    debit += line.debit
                    self.assertEqual(line.account_id.id, invoice.account_id.id,
                        'Account should be equal to account invoice'
                    )
                else:
                    credit += line.credit
                    self.assertEqual(line.account_id.id,
                        self.concept.property_retencion_islr_payable.id,
                        'Account should be equal to account concept islr'
                    )
        self.assertEqual(debit, credit, 'Debit and Credit should be equal')
        self.assertEqual(debit, islr_wh.amount_total_ret,
            'Amount total withholding should be equal journal entrie'
        )

    # def test_02_constraint_account_withholding_islr(self):
    #     '''Test constraint account concept withholding islr'''
    #     invoice = self._create_invoice('in_invoice')
    #     # Check initial state
    #     self._create_invoice_line(invoice.id, self.concept_wo_account.id)
    #     invoice.signal_workflow('invoice_open')
    #     islr_wh = invoice.islr_wh_doc_id
    #     islr_wh.signal_workflow('act_confirm')
    #     with self.assertRaisesRegexp(
    #         except_orm,
    #         "Missing Account in Tax!"
    #     ):
    #         islr_wh.signal_workflow('act_done')

    def test_02_withholding_with_currency(self):
        '''Test withholding with multicurrency'''
        datetime_now = datetime.now()
        day = timedelta(days=2)
        datetime_now = datetime_now - day
        datetime_now = datetime_now.strftime(DEFAULT_SERVER_DATETIME_FORMAT)
        self.rates_obj.create({'name': datetime_now,
                                'rate': 1.25,
                                'currency_id': self.currency_usd.id})
        invoice = self._create_invoice('in_invoice', self.currency_usd.id)
        self._create_invoice_line(invoice.id, self.concept.id)
        invoice.signal_workflow('invoice_open')
        islr_wh = invoice.islr_wh_doc_id

        for concept_id in islr_wh.concept_ids:
            currency_c = concept_id.currency_base_amount /\
                            invoice.currency_id.rate_silent
            wh_currency = concept_id.currency_amount /\
                            invoice.currency_id.rate_silent
            self.assertEqual(concept_id.base_amount,
                             currency_c,
                             '''Amount base should be equal to amount invoice
                             between currency amount
                             ''')
            self.assertEqual(concept_id.amount,
                             wh_currency,
                             '''Amount base should be equal to amount invoice
                             between currency amount
                             ''')

    def test_03_validate_process_withholding_islr_customer(self):
        '''Test create invoice customer with data initial and
        Test validate invoice with document withholding islr'''
        invoice = self._create_invoice('out_invoice')
        # Check initial state
        self.assertEqual(
            invoice.state, 'draft', 'Initial state should be in "draft"'
        )
        # invoice_line = self._create_invoice_line(invoice)
        self._create_invoice_line(invoice.id, self.concept.id)
        invoice.signal_workflow('invoice_open')
        self.assertEqual(
            invoice.state, 'open', 'State in open'
        )
        self.assertEqual(invoice.islr_wh_doc_id, self.doc_obj,
            'Not should be empty the withholding document'
        )
