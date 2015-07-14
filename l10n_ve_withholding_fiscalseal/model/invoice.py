#!/usr/bin/python
# -*- encoding: utf-8 -*-
# http://www.gnu.org/licenses/agpl-3.0.html

from openerp.osv import fields, osv
from openerp.tools.translate import _


class AccountInvoice(osv.osv):

    _inherit = 'account.invoice'

    _columns = {
        'fiscalseal_apply': fields.boolean(
            'Exclude this document from Fiscal Seal Withholding',
            states={'draft': [('readonly', False)]},
            help="This selection indicates whether allow invoice to be"
                 "included in a withholding document"),
        'wh_fiscalseal': fields.boolean(
            string='Withheld',
            help="This Document has already been withheld"),
        'wh_fiscalseal_id': fields.many2one(
            'account.wh.fiscalseal',
            string='Fiscal Seal Withholding Document',
            help="This Document has already been withheld"),
    }

    _defaults = {'fiscalseal_apply': False}

    def copy(self, cr, uid, ids, default=None, context=None):
        """ Initialized fields to the copy a register
        """
        context = dict(context or {})
        default = dict(default or {})
        default = default.copy()
        default.update({
            'fiscalseal_apply': False,
            'wh_fiscalseal': False,
            'wh_fiscalseal_id': False,
            })
        return super(AccountInvoice, self).copy(cr, uid, ids, default,
                                                context=context)

    def _get_move_lines(self, cr, uid, ids, to_wh, period_id,
                        pay_journal_id, writeoff_acc_id,
                        writeoff_period_id, writeoff_journal_id, date,
                        name, context=None):
        """ Generate move lines in corresponding account
        @param to_wh: whether or not withheld
        @param period_id: Period
        @param pay_journal_id: pay journal of the invoice
        @param writeoff_acc_id: account where canceled
        @param writeoff_period_id: period where canceled
        @param writeoff_journal_id: journal where canceled
        @param date: current date
        @param name: description
        """
        context = context or {}
        res = super(AccountInvoice, self)._get_move_lines(
            cr, uid, ids, to_wh, period_id, pay_journal_id, writeoff_acc_id,
            writeoff_period_id, writeoff_journal_id, date, name,
            context=context)

        if not context.get('wh_fiscalseal', False):
            return res

        invoice = self.browse(cr, uid, ids[0], context=context)
        rp_obj = self.pool.get('res.partner')
        acc_part_brw = rp_obj._find_accounting_partner(invoice.partner_id)
        types = {
            'out_invoice': -1,
            'in_invoice': 1,
            'out_refund': 1, 'in_refund': -1}
        direction = types[invoice.type]

        for tax_brw in to_wh:
            if types[invoice.type] == 1:
                acc = (
                    tax_brw.retention_id.company_id.
                    wh_fiscalseal_collected_account_id and
                    tax_brw.retention_id.company_id.
                    wh_fiscalseal_collected_account_id.id or False)
            else:
                acc = (
                    tax_brw.retention_id.company_id.
                    wh_fiscalseal_paid_account_id and
                    tax_brw.retention_id.company_id.
                    wh_fiscalseal_paid_account_id.id or False)
            if not acc:
                raise osv.except_osv(
                    _('Missing Account in Company!'),
                    _("Your Company [%s] has missing account. Please, fill"
                      " the missing fields") % (
                          tax_brw.retention_id.company_id.name,))
            res.append((0, 0, {
                'debit':
                direction * tax_brw.wh_tax_amount < 0 and
                - direction * tax_brw.wh_tax_amount,
                'credit':
                direction * tax_brw.wh_tax_amount > 0 and
                direction * tax_brw.wh_tax_amount,
                'account_id': acc,
                'partner_id': acc_part_brw.id,
                'ref': invoice.number,
                'date': date,
                'currency_id': False,
                'name': name
            }))
        return res

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
