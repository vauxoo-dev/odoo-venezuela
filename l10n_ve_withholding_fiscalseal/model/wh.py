#!/usr/bin/python
# -*- encoding: utf-8 -*-
# http://www.gnu.org/licenses/agpl-3.0.html

import time

from openerp.addons import decimal_precision as dp
from openerp.osv import fields, osv
from openerp.tools.translate import _

STATES = [
    ('draft', 'Draft'),
    ('confirmed', 'Confirmed'),
    ('done', 'Done'),
    ('cancel', 'Cancelled'),
]


class FiscalSealLine(osv.osv):

    _name = "account.wh.fiscalseal.line"
    _columns = {
        'name': fields.char(
            'Description',
            size=64,
            required=True,
            help="Withholding line Description"),
        'parent_state': fields.related(
            'retention_id',
            'state',
            type='selection',
            selection=STATES,
            string='Withholding State',
            store=True,
            readonly=True),
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
        'invoice_total': fields.related(
            'invoice_id',
            'amount_total',
            type='float',
            string='Invoice Total',
            store=True,
            readonly=True),
        'invoice_tax': fields.related(
            'invoice_id',
            'amount_tax',
            type='float',
            string='Invoice Tax',
            store=True,
            readonly=True),
        'payment_amount': fields.float(
            string='Payment Amount',
            digits_compute=dp.get_precision('Account'),
            ),
        'payment_description': fields.related(
            'retention_id',
            'payment_description',
            type='char',
            string='Payment Order',
            size=256,
            store=True,
            readonly=True),
        'wh_base_amount': fields.float(
            string='Taxable Amount',
            digits_compute=dp.get_precision('Account'),
            help='Amount to be Withheld'
            ),
        'wh_tax_amount': fields.float(
            string='Withheld Tax',
            digits_compute=dp.get_precision('Account'),
            help='Withheld Amount'
            ),
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
            string='Withholding Fiscal Seal Rate (‰)',
            digits_compute=dp.get_precision('Account'),
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
            help='Accouting date. Date Withholding'),
        'ut_value': fields.float(
            string='Tax Unit Value',
            digits_compute=dp.get_precision('Account'),
            required=True,
            ),
        'ut_qty': fields.float(
            string='Tax Unit Quantity',
            digits=(16, 2),
            required=True,
            ),
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
        ai_brw = ai_obj.browse(cr, uid, invoice, context=context)
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

        ut_obj = self.pool.get('l10n.ut')
        ut2money = ut_obj.compute_ut_to_money
        ut_qty = 50
        date_ret = time.strftime('%Y-%m-%d')
        ut_value = ut2money(cr, uid, ut_qty, date_ret, context=context)
        result.update(
            {'name': ai_brw.name,
             'supplier_invoice_number': ai_brw.supplier_invoice_number,
             'invoice_total': ai_brw.amount_total,
             'wh_rate': 1.0,
             'invoice_tax': ai_brw.amount_tax,
             'payment_amount': ai_brw.residual,
             'ut_value': ut_value,
             'ut_qty': ut_qty,
             })

        return {'value': result, 'domain': domain}

    def load_taxes(self, cr, uid, ids, context=None):
        """ Clean and load again tax lines of the withholding
        """
        if context is None:
            context = {}

        for ret_line in self.browse(cr, uid, ids, context):
            if ret_line.invoice_id:
                pay = ret_line.payment_amount
                tax = ret_line.invoice_tax
                wh = ret_line.wh_rate
                ut_value = ret_line.ut_value
                if pay >= ut_value:
                    wh_base_amount = (pay - tax)
                else:
                    wh_base_amount = 0.0

                self.write(
                    cr, uid, ret_line.id, {
                        'wh_base_amount': wh_base_amount,
                        'wh_tax_amount': wh_base_amount * wh / 1000,
                        })

        return True


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
        'state': fields.selection(
            STATES,
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
        #     digits_compute=dp.get_precision('Account'),
        #     string='Compute amount',
        #     multi='all',
        #     help="Compute amount without tax"),
        # 'total_tax_ret': fields.function(
        #     _amount_ret_all,
        #     method=True,
        #     digits_compute=dp.get_precision('Account'),
        #     string='Compute amount wh. tax Fiscal Seal',
        #     multi='all',
        #     help="compute amount withholding tax Fiscal Seal"),
        'invoice_tax': fields.float(
            string='Invoice Tax',
            digits_compute=dp.get_precision('Account'),
            readonly=True,
            ),
        'payment_amount': fields.float(
            string='Payment Amount',
            digits_compute=dp.get_precision('Account'),
            ),
        'payment_description': fields.char(
            'Payment Order',
            size=256,
            required=True,
            help="Payment Order Description"),
        'wh_base_amount': fields.float(
            string='Taxable Amount',
            digits_compute=dp.get_precision('Account'),
            help='Amount to be Withheld'
            ),
        'wh_tax_amount': fields.float(
            string='Withheld Tax',
            digits_compute=dp.get_precision('Account'),
            help='Withheld Amount'
            ),
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

    def clear_wh_lines(self, cr, uid, ids, context=None):
        """ Clear lines of current withholding document and delete wh document
        information from the invoice.
        """
        context = context or {}
        awfl_obj = self.pool.get('account.wh.fiscalseal.line')
        ai_obj = self.pool.get('account.invoice')
        if ids:
            awfl_ids = awfl_obj.search(cr, uid, [
                ('retention_id', 'in', ids)], context=context)
            ai_ids = awfl_ids and [
                wil.invoice_id.id
                for wil in awfl_obj.browse(cr, uid, awfl_ids, context=context)]
            if ai_ids:
                ai_obj.write(cr, uid, ai_ids,
                             {'wh_iva_id': False}, context=context)
            if awfl_ids:
                awfl_obj.unlink(cr, uid, awfl_ids, context=context)

        return True

    def onchange_partner_id(self, cr, uid, ids, inv_type, partner_id,
                            context=None):
        """ Update the withholding document accounts and the withholding lines
        depending on the partner and another parameters that depend of the type
        of withholding. If the type is sale will only take into account the
        partner, but if the type is purchase would take into account the period
        changes.

        This method delete lines at right moment and unlink/link the
        withholding document to the related invoices.
        @param type: invoice type
        @param partner_id: partner_id at current view
        """
        context = context or {}
        ai_obj = self.pool.get('account.invoice')
        rp_obj = self.pool.get('res.partner')
        values_data = dict()
        acc_id = False
        wh_type = ((inv_type in ('out_invoice', 'out_refund'))
                   and 'sale' or 'purchase')

        # pull account info
        if partner_id:
            acc_part_id = rp_obj._find_accounting_partner(rp_obj.browse(
                cr, uid, partner_id))
            if wh_type == 'sale':
                acc_id = (acc_part_id.property_account_receivable and
                          acc_part_id.property_account_receivable.id or False)
            else:
                acc_id = (acc_part_id.property_account_payable and
                          acc_part_id.property_account_payable.id or False)
            values_data['account_id'] = acc_id

        # clear lines
        self.clear_wh_lines(cr, uid, ids, context=context)

        if not partner_id:
            values_data['wh_lines'] = []
            return {'value': values_data}

        # add lines
        ttype = wh_type == 'sale' and ['out_invoice'] \
            or ['in_invoice']

        args = [
            # ('state', '=', 'open'), ('wh_fiscalseal', '=', False),
            ('state', '=', 'open'),
            ('fiscalseal_apply', '=', False),
            # ('wh_fiscalseal_id', '=', False), ('type', 'in', ttype),
            ('type', 'in', ttype),
            '|',
            ('partner_id', '=', acc_part_id.id),
            ('partner_id', 'child_of', acc_part_id.id),
            ]

        ai_ids = ai_obj.search(cr, uid, args, context=context)

        if ai_ids:
            ut_obj = self.pool.get('l10n.ut')
            ut2money = ut_obj.compute_ut_to_money
            ut_qty = 50
            date_ret = time.strftime('%Y-%m-%d')
            ut_value = ut2money(cr, uid, ut_qty, date_ret, context=context)
            values_data['wh_lines'] = \
                [{'invoice_id': inv_brw.id,
                  'name': inv_brw.name or _('N/A'),
                  'supplier_invoice_number': inv_brw.supplier_invoice_number,
                  'invoice_total': inv_brw.amount_total,
                  'wh_rate': 1.0,
                  'invoice_tax': inv_brw.amount_tax,
                  'payment_amount': inv_brw.residual,
                  'ut_value': ut_value,
                  'ut_qty': ut_qty,
                  }
                 for inv_brw in ai_obj.browse(cr, uid, ai_ids, context=context)
                 ]
        return {'value': values_data}

    def compute_amount_wh(self, cr, uid, ids, context=None):
        """ Calculate withholding amount each line
        """
        context = context or {}
        awfl_obj = self.pool.get('account.wh.fiscalseal.line')

        for awf_brw in self.browse(cr, uid, ids, context=context):
            awfl_ids = [line.id for line in awf_brw.wh_lines]
            if awfl_ids:
                awfl_obj.load_taxes(cr, uid, awfl_ids, context=context)
        return True
