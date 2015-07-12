#!/usr/bin/python
# -*- encoding: utf-8 -*-
# http://www.gnu.org/licenses/agpl-3.0.html

from openerp.osv import fields, osv


class AccountInvoice(osv.osv):

    _inherit = 'account.invoice'

    _columns = {
        'fiscalseal_apply': fields.boolean(
            'Exclude this document from Fiscal Seal Withholding',
            states={'draft': [('readonly', False)]},
            help="This selection indicates whether allow invoice to be"
                 "included in a withholding document"),
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
            })
        return super(AccountInvoice, self).copy(cr, uid, ids, default,
                                                context=context)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
