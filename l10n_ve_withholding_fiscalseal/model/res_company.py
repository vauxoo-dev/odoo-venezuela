#!/usr/bin/python
# -*- encoding: utf-8 -*-
# http://www.gnu.org/licenses/agpl-3.0.html

from openerp.osv import fields, osv


class ResCompany(osv.osv):
    _inherit = "res.company"
    _columns = {
        'wh_fiscalseal_collected_account_id': fields.many2one(
            'account.account',
            string="Collected Withholding Fiscal Seal Account",
            domain="[('type', '=', 'other')]",
            help="This account will be used when applying a withhold to"
                 " an Supplier"),
        'wh_fiscalseal_paid_account_id': fields.many2one(
            'account.account',
            string="Paid Withholding Fiscal Seal Account",
            domain="[('type', '=', 'other')]",
            help="This account will be used when applying a withhold to a"
                 " Customer"),
    }

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
