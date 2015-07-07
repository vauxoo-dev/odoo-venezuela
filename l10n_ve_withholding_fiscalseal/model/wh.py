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
            help="Fiscal Seal Withholding"),
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
            string='Withholding Fiscal Seal Rate',
            digits_compute=dp.get_precision('Withhold'),
            help="Fiscal Seal Withholding rate"),
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

    def invoice_id_change(self, cr, uid, ids, invoice, context=None):
        """ Return invoice data to assign to withholding Fiscal Seal
        @param invoice: invoice for assign a withholding Fiscal Seal
        """
        context = context or {}
        if not invoice:
            return {}
        result = {}
        domain = []
        ok = True
        ai_obj = self.pool.get('account.invoice')
        awfs_obj = self.pool.get('account.wh.fiscalseal')
        res = ai_obj.browse(cr, uid, invoice, context=context)
        cr.execute('SELECT retention_id '
                   'FROM account_wh_fiscalseal_line '
                   'WHERE invoice_id={invoice_id}'.format(
                       invoice_id=invoice))
        ret_ids = cr.fetchone()
        ok = ok and bool(ret_ids)
        if ok:
            ret = awfs_obj.browse(cr, uid, ret_ids[0], context)
            raise osv.except_osv(
                'Assigned Invoice !',
                "The invoice has already assigned in withholding"
                " Fiscal Seal code: '%s' !" % (ret.code,))

        result.update({'name': res.name,
                       'supplier_invoice_number': res.supplier_invoice_number})

        return {'value': result, 'domain': domain}


class FiscalSeal(osv.osv):

    def _get_type(self, cr, uid, context=None):
        """ Return invoice type
        """
        if context is None:
            context = {}
        inv_type = context.get('type', 'in_invoice')
        return inv_type

    def _get_journal(self, cr, uid, context):
        """ Return a fiscalseal journal depending of invoice type
        """
        if context is None:
            context = {}
        type_inv = context.get('type', 'in_invoice')
        type2journal = {'out_invoice': 'fiscalseal_sale',
                        'in_invoice': 'fiscalseal_purchase'}
        journal_obj = self.pool.get('account.journal')
        res = journal_obj.search(
            cr, uid,
            [('type', '=', type2journal.get(type_inv, 'fiscalseal_purchase'))],
            limit=1)
        if res:
            return res[0]
        return False

    def _get_currency(self, cr, uid, context):
        """ Return currency to use
        """
        user = self.pool.get('res.users').browse(cr, uid, [uid])[0]
        if user.company_id:
            return user.company_id.currency_id.id
        return self.pool.get('res.currency').search(
            cr, uid, [('rate', '=', 1.0)])[0]

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
            'Fiscal Seal Withholding lines',
            readonly=True,
            states={'draft': [('readonly', False)]},
            help="Fiscal Seal Withholding lines"),
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
        #     string='Compute amount wh. tax Fiscal Seal',
        #     multi='all',
        #     help="compute amount withholding tax Fiscal Seal"),
    }

    _defaults = {
        'code': lambda self, cr, uid, c: self.wh_fiscalseal_seq_get(cr, uid),
        'type': _get_type,
        'state': lambda *a: 'draft',
        'journal_id': _get_journal,
        'currency_id': _get_currency,
        'company_id': lambda self, cr, uid, context:
        self.pool.get('res.users').browse(cr, uid, uid,
                                          context=context).company_id.id,
    }

    def wh_fiscalseal_seq_get(self, cr, uid, context=None):
        """ Generate sequences for records of withholding fiscalseal
        """
        pool_seq = self.pool.get('ir.sequence')
        cr.execute(
            "select id,number_next,number_increment,prefix,suffix,padding "
            "from ir_sequence "
            "where code='account.wh.fiscalseal' and active=True")
        res = cr.dictfetchone()
        if res:
            if res['number_next']:
                return pool_seq._next(cr, uid, [res['id']])
            else:
                return pool_seq._process(res['prefix']) + pool_seq._process(
                    res['suffix'])
        return False
