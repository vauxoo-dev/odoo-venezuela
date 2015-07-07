#!/usr/bin/python
# -*- encoding: utf-8 -*-
# http://www.gnu.org/licenses/agpl-3.0.html

import time

from openerp.addons import decimal_precision as dp
from openerp.osv import fields, osv
from openerp.tools.translate import _


class FiscalSealLine(osv.osv):

    _name = "account.wh.fiscalseal.line"
    _columns = {
        'name': fields.char(
            'Description',
            size=64,
            required=True,
            help="Withholding line Description"),
        'retention_id': fields.many2one(
            'account.wh.fiscalseal',
            'Fiscal Seal Withholding',
            ondelete='cascade',
            help="Vat Withholding"),
        'invoice_id': fields.many2one(
            'account.invoice',
            'Invoice',
            required=True,
            ondelete='restrict',
            help="Withholding invoice"),
        'supplier_invoice_number': fields.related(
            'invoice_id',
            'supplier_invoice_number',
            type='char',
            string='Supplier Invoice Number',
            size=64,
            store=True,
            readonly=True),
        # 'amount_tax_ret': fields.function(
        #     _amount_all,
        #     method=True,
        #     digits=(16, 4),
        #     string='Wh. tax amount',
        #     multi='all', help="Withholding tax amount"),
        # 'base_ret': fields.function(
        #     _amount_all,
        #     method=True,
        #     digits=(16, 4),
        #     string='Wh. amount',
        #     multi='all',
        #     help="Withholding without tax amount"),
        'move_id': fields.many2one(
            'account.move',
            'Account Entry',
            readonly=True,
            help="Account entry",
            ondelete='restrict'),
        'wh_rate': fields.float(
            string='Withholding Vat Rate',
            digits_compute=dp.get_precision('Withhold'),
            help="Vat Withholding rate"),
        'date': fields.related(
            'retention_id',
            'date',
            type='date',
            relation='account.wh.fiscalseal',
            string='Voucher Date',
            help='Emission/Voucher/Document date'),
        'date_ret': fields.related(
            'retention_id',
            'date_ret',
            type='date',
            relation='account.wh.fiscalyear',
            string='Accounting Date',
            help='Accouting date. Date Withholding')
    }


class FiscalSeal(osv.osv):

    _name = "account.wh.fiscalseal"
    _columns = {
        'name': fields.char(
            'Description',
            size=64,
            readonly=True,
            states={'draft': [('readonly', False)]},
            required=True,
            help="Description of withholding"),
        'code': fields.char(
            'Internal Code',
            size=32,
            readonly=True,
            states={'draft': [('readonly', False)]},
            help="Internal withholding reference"),
        'number': fields.char(
            'Number',
            size=32,
            readonly=True,
            states={'draft': [('readonly', False)]},
            help="Withholding number"),
        'type': fields.selection([
            ('out_invoice', 'Customer Withholding'),
            ('in_invoice', 'Supplier Withholding'), ],
            'Type',
            readonly=True,
            help="Withholding type"),
        'state': fields.selection([
            ('draft', 'Draft'),
            ('confirmed', 'Confirmed'),
            ('done', 'Done'),
            ('cancel', 'Cancelled')],
            'State',
            readonly=True,
            help="Withholding State"),
        'date_ret': fields.date(
            'Accounting date',
            readonly=True,
            states={'draft': [('readonly', False)]},
            help="Keep empty to use the current date"),
        'date': fields.date(
            'Document Date',
            readonly=True,
            states={'draft': [('readonly', False)]},
            help="Emission/Voucher/Document Date"),
        'account_id': fields.many2one(
            'account.account',
            'Account',
            required=True,
            readonly=True,
            states={'draft': [('readonly', False)]},
            help="The pay account used for this withholding."),
        'currency_id': fields.many2one(
            'res.currency', 'Currency',
            required=True,
            readonly=True,
            states={'draft': [('readonly', False)]},
            help="Currency"),
        'period_id': fields.many2one(
            'account.period', 'Force Period',
            domain=[('state', '<>', 'done')],
            readonly=True,
            states={'draft': [('readonly', False)]},
            help="Keep empty to use the period of the validation (Withholding"
                 " date) date."),
        'company_id': fields.many2one(
            'res.company',
            'Company',
            required=True,
            readonly=True,
            help="Company"),
        'partner_id': fields.many2one(
            'res.partner', 'Partner',
            readonly=True,
            required=True,
            states={'draft': [('readonly', False)]},
            help="Withholding customer/supplier"),
        'journal_id': fields.many2one(
            'account.journal', 'Journal',
            required=True,
            readonly=True,
            states={'draft': [('readonly', False)]},
            help="Journal entry"),
        'wh_lines': fields.one2many(
            'account.wh.fiscalseal.line',
            'retention_id',
            'Vat Withholding lines',
            readonly=True,
            states={'draft': [('readonly', False)]},
            help="Vat Withholding lines"),
        # 'amount_base_ret': fields.function(
        #     _amount_ret_all,
        #     method=True,
        #     digits_compute=dp.get_precision('Withhold'),
        #     string='Compute amount',
        #     multi='all',
        #     help="Compute amount without tax"),
        # 'total_tax_ret': fields.function(
        #     _amount_ret_all,
        #     method=True,
        #     digits_compute=dp.get_precision('Withhold'),
        #     string='Compute amount wh. tax vat',
        #     multi='all',
        #     help="compute amount withholding tax vat"),
    }
