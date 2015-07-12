#!/usr/bin/python
# -*- encoding: utf-8 -*-
# http://www.gnu.org/licenses/agpl-3.0.html

from openerp.osv import fields, osv
from openerp.tools.translate import _


class wiz_retention(osv.osv_memory):
    _name = 'wiz.fiscalseal.apply.wh'
    _description = "Wizard that changes exclusion from an invoice"

    def set_retention(self, cr, uid, ids, context=None):
        context = dict(context or {})
        ids = isinstance(ids, (int, long)) and [ids] or ids
        wzd_brw = self.browse(cr, uid, ids[0], context=context)
        if not wzd_brw.sure:
            raise osv.except_osv(
                _("Error!"),
                _("Please confirm that you want to do this by checking the"
                  " option"))

        self.pool.get('account.invoice').write(
            cr, uid, context.get('active_id'),
            {'fiscalseal_apply': wzd_brw.fiscalseal_apply},
            context=context)

        return True

    _columns = {
        'fiscalseal_apply': fields.boolean(
            'Exclude this document from Fiscal Seal Withholding'),
        'sure': fields.boolean('Are you sure?'),
    }

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
