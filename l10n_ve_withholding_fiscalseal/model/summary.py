#!/usr/bin/python
# -*- encoding: utf-8 -*-
# http://www.gnu.org/licenses/agpl-3.0.html

import time

from openerp.osv import fields, osv
from openerp.tools.translate import _


class AccountFiscalSealSummary(osv.osv):
    _name = "account.fiscalseal.summary"
    _description = 'Fiscal Seal Summary'

    def _get_amount_total(self, cr, uid, ids, name, args, context=None):
        """ Return withhold total amount
        """
        res = {}
        for xml in self.browse(cr, uid, ids, context):
            res[xml.id] = 0.0
            for line in xml.wh_lines:
                res[xml.id] += line.wh_tax_amount
        return res

    def _get_amount_total_base(self, cr, uid, ids, name, args, context=None):
        """ Return base total amount
        """
        res = {}
        for xml in self.browse(cr, uid, ids, context):
            res[xml.id] = 0.0
            for line in xml.wh_lines:
                res[xml.id] += line.wh_base_amount
        return res

    _columns = {
        'name': fields.char(
            'Description', 128, required=True, select=True,
            help="Description about statement of Fiscal Seal withholding"),
        'company_id': fields.many2one(
            'res.company', 'Company', required=True, help="Company"),
        'state': fields.selection([
            ('draft', 'Draft'),
            ('confirmed', 'Confirmed'),
            ('done', 'Done'),
            ('cancel', 'Cancelled')
        ], 'State', readonly=True, help="Voucher state"),
        'period_id': fields.many2one(
            'account.period',
            'Period',
            required=True,
            help="Period when the accounts entries were done"),
        'wh_tax_amount': fields.function(
            _get_amount_total,
            method=True,
            digits=(16, 2),
            readonly=True,
            string='Withheld Amount',
            help="Withheld Amount"),
        'wh_base_amount': fields.function(
            _get_amount_total_base,
            method=True,
            digits=(16, 2),
            readonly=True,
            string='Taxable Amount',
            help="Taxable Amount"),
        'wh_lines': fields.one2many(
            'account.wh.fiscalseal.line',
            'afss_id',
            'Fiscal Seal Lines',
            readonly=True,
            states={'draft': [('readonly', False)]},
            help='Fiscal Seal Line'),
        'user_id': fields.many2one(
            'res.users',
            'User',
            readonly=True,
            states={'draft': [('readonly', False)]},
            help='User Creating Document'),
    }
    _defaults = {
        'state': lambda *a: 'draft',
        'company_id': lambda self, cr, uid, context:
        self.pool.get('res.users').browse(
            cr, uid, uid, context=context).company_id.id,
        'user_id': lambda self, cr, uid, context: uid,
        'period_id': lambda self, cr, uid, context: self.period_return(
            cr, uid, context),
        'name': (lambda self, cr, uid, context:
                 'Fiscal Seal Withholding ' + time.strftime('%m/%Y'))
    }

    def copy(self, cr, uid, ids, default=None, context=None):
        """ Initialized id by duplicating
        """
        default = dict(default or {})
        default = default.copy()
        default.update({
            'wh_lines': [],
        })

        return super(AccountFiscalSealSummary, self).copy(
            cr, uid, ids, default, context)

    def period_return(self, cr, uid, context=None):
        """ Return current period
        """
        period_obj = self.pool.get('account.period')
        fecha = time.strftime('%m/%Y')
        period_id = period_obj.search(cr, uid, [('code', '=', fecha)])
        if period_id:
            return period_id[0]
        return False

    def search_period(self, cr, uid, ids, period_id, context=None):
        """ Return Fiscal Seal lines associated with the period_id
        @param period_id: period associated with returned Fiscal Seal lines
        """
        context = dict(context or {})
        res = {'value': {}}
        if period_id:
            islr_line = self.pool.get('account.wh.fiscalseal.line')
            islr_line_ids = islr_line.search(
                cr, uid, [('period_id', '=', period_id)], context=context)
            if islr_line_ids:
                res['value'].update({'wh_lines': islr_line_ids})
                return res

    def name_get(self, cr, uid, ids, context=None):
        """ Return id and name of all records
        """
        context = dict(context or {})
        if not len(ids):
            return []

        res = [(r['id'], r['name']) for r in self.read(
            cr, uid, ids, ['name'], context=context)]
        return res

    def action_draft(self, cr, uid, ids, context=None):
        """ Return the document to draft status
        """
        context = context or {}
        return self.write(cr, uid, ids, {'state': 'draft'}, context=context)

    def action_confirm(self, cr, uid, ids, context=None):
        """ Passes the document to state confirmed
        """
        # to set date_ret if don't exists
        context = context or {}
        return self.write(
            cr, uid, ids, {'state': 'confirmed'}, context=context)

    def action_done(self, cr, uid, ids, context=None):
        """ Passes the document to state done
        """
        context = context or {}
        self.write(cr, uid, ids, {'state': 'done'})
        return True

    def action_cancel(self, cr, uid, ids, context=None):
        """ Return the document to draft status
        """
        context = context or {}
        return self.write(cr, uid, ids, {'state': 'cancel'}, context=context)

    def show_items(self, cur, uid, ids, context=None):
        """
        This method is used in a button named `Show Items`
        """
        context = context or {}
        ids = isinstance(ids, (int, long)) and [ids] or ids
        awfl_ids = []
        for brw in self.browse(cur, uid, ids, context=context):
            awfl_ids += [awfl_brw.id for awfl_brw in brw.wh_lines]

        return {
            'domain': str([('id', 'in', awfl_ids)]),
            'name': _('Show Items'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'account.wh.fiscalseal.line',
            'view_id': False,
            'type': 'ir.actions.act_window'
        }


class FiscalSealLine(osv.osv):
    _inherit = "account.wh.fiscalseal.line"
    _columns = {
        'afss_id': fields.many2one(
            'account.fiscalseal.summary',
            'Fiscal Seal Summary',
            ondelete='restrict',
            help="Fiscal Seal Summary"),
    }

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
