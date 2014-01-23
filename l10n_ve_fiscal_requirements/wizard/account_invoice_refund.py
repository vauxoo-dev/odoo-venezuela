# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

import time
import datetime
from openerp.osv import fields, osv
from openerp.tools.translate import _
from openerp import netsvc

class account_invoice_refund(osv.osv_memory):
    """Refunds invoice"""

    _inherit = 'account.invoice.refund'
    
    def default_get(self, cr, uid, fields, context=None):
        """ Get default values
        @param fields: List of fields for default value
        """
        if context is None:
            context = {}
        res = super(account_invoice_refund, self).default_get(cr, uid, fields, context=context)
        if context.get('active_id'):
            code = datetime.datetime.today().strftime('%m/%Y')
            period_obj = self.pool.get('account.period')
            period_ids = period_obj.search(cr,uid,[('code','=',code)],context=context)
            period_id = period_ids and period_ids[0]
            
            res.update({'period': period_id})
        return res
   
    def _get_loc_req(self, cr, uid, context=None):
        """Get if a field is required or not by a Localization
        @param uid: Integer value of the user
        """
        context = context or {}
        res = False
        rc_obj = self.pool.get('res.company')
        u = self.pool.get('res.users').browse(cr, uid, uid, context=context)
        rc_brw = rc_obj.browse(cr, uid, u.company_id.id, context=context)
        if rc_brw.country_id and rc_brw.country_id.code == 'VE':
            res= True
        return res
    
    
    _columns = {
        'nro_ctrl': fields.char('Control Number', size=32, help="Code used for intern invoice control"),    
        'loc_req':fields.boolean('Required by Localization', help='This fields is for technical use'), 
    }

    _defaults ={
        'loc_req': _get_loc_req
            }

    def _get_journal(self, cr, uid, context=None):
        """ Return journal depending of the invoice type
        """
        obj_journal = self.pool.get('account.journal')
        if context is None:
            context = {}
        journal = obj_journal.search(cr, uid, [('type', '=', 'sale_refund')])
        if context.get('type', False):
            if context['type'] in ('in_invoice', 'in_refund'):
                journal = obj_journal.search(cr, uid, [('type', '=', 'purchase_refund')])
        return journal and journal[0] or False

    def fields_view_get(self, cr, uid, view_id=None, view_type=False, context=None, toolbar=False, submenu=False):
        """ Depending on context, options are displayed in the selection field
        """
        if context is None:
            context = {}
        
        journal_obj = self.pool.get('account.journal')
        res = super(account_invoice_refund,self).fields_view_get(cr, uid, view_id=view_id, view_type=view_type, context=context, toolbar=toolbar, submenu=submenu)
        type = context.get('journal_type', 'sale_refund')
        if type in ('sale', 'sale_refund'):
            type = 'sale_refund'
        else:
            type = 'purchase_refund'
        for field in res['fields']:
            if field == 'journal_id':
                journal_select = journal_obj._name_search(cr, uid, '', [('type', '=', type)], context=context, limit=None, name_get_uid=1)
                res['fields'][field]['selection'] = journal_select
        return res

    def compute_refund(self, cr, uid, ids, mode='refund', context=None):
        """ 
        @param ids: the account invoice refund’s ID or list of IDs
        """
        wzd_brw = self.browse(cr,uid,ids[0],context=context)
        brw = self.browse(cr,uid,ids[0],context=context)
        inv_obj = self.pool.get('account.invoice')
        reconcile_obj = self.pool.get('account.move.reconcile')
        account_m_line_obj = self.pool.get('account.move.line')
        mod_obj = self.pool.get('ir.model.data')
        act_obj = self.pool.get('ir.actions.act_window')
        wf_service = netsvc.LocalService('workflow')
        inv_tax_obj = self.pool.get('account.invoice.tax')
        inv_line_obj = self.pool.get('account.invoice.line')
        res_users_obj = self.pool.get('res.users')
        if context is None:
            context = {}
        for form in  self.read(cr, uid, ids, context=context):
            created_inv = []
            date = False
            period = False
            description = False
            nroctrl = False
            company = res_users_obj.browse(cr, uid, uid, context=context).company_id
            journal_brw = form.get('journal_id', False)
            for inv in inv_obj.browse(cr, uid, context.get('active_ids'), context=context):
                if inv.state in ['draft', 'proforma2', 'cancel']:
                    raise osv.except_osv(_('Error !'), _('Can not %s draft/proforma/cancel invoice.') % (mode))
                if inv.reconciled and mode in ('cancel', 'modify'):
                    raise osv.except_osv(_('Error !'), _('Can not %s invoice which is already reconciled, invoice should be unreconciled first. You can only Refund this invoice') % (mode))
                period = form.get('period') and form.get('period')[0] or False
                if not period:
	                #Take period from the current date
                    period = self.pool.get('account.period').find(cr, uid, context=context)
                    period = period and period[0] or False
                    if not period:
                        raise osv.except_osv(_('No Pediod Defined'), \
                                _('You have been left empty the period field that automatically fill with the current period. However there is not period defined for the current company. Please check in Accounting/Configuration/Periods'))
                    self.write(cr, uid, ids, {'period': period }, context=context)

                if not journal_brw:
                    journal_id = inv.journal_id.id
                else:
                    journal_id=journal_brw[0]

                if form['date']:
                    date = form['date']
                    if not form['period']:
                            cr.execute("select name from ir_model_fields \
                                            where model = 'account.period' \
                                            and name = 'company_id'")
                            result_query = cr.fetchone()
                            if result_query:
                                cr.execute("""select p.id from account_fiscalyear y, account_period p where y.id=p.fiscalyear_id \
                                    and date(%s) between p.date_start AND p.date_stop and y.company_id = %s limit 1""", (date, company.id,))
                            else:
                                cr.execute("""SELECT id
                                        from account_period where date(%s)
                                        between date_start AND  date_stop  \
                                        limit 1 """, (date,))
                            res = cr.fetchone()
                            if res:
                                period = res[0]
                else:
                    #Take current date
                    #date = inv.date_invoice
                    date = time.strftime('%Y-%m-%d')
                if form['description']:
                    description = form['description']
                else:
                    description = inv.name
                
                if inv.type in ('in_invoice','in_refund'):
                    if form['nro_ctrl']:
                        nroctrl = form['nro_ctrl']
                    else:
                        raise osv.except_osv(_('Control Number !'), \
                                            _('Missing Control Number on Invoice Refund!'))

                if not period:
                    raise osv.except_osv(_('Data Insufficient !'), \
                                            _('No Period found on Invoice!'))
                
                refund_id = inv_obj.refund(cr, uid, [inv.id], date, period, description, journal_id)
                
                refund = inv_obj.browse(cr, uid, refund_id[0], context=context)
                #Add parent invoice
                cr.execute("update account_invoice set date_due='%s',nro_ctrl='%s', check_total='%s', \
                            parent_id=%s where id =%s"%(date,nroctrl,inv.check_total,inv.id,refund.id))
                inv_obj.button_compute(cr, uid, refund_id)
                
                created_inv.append(refund_id[0])
                if mode in ('cancel', 'modify'):
                    movelines = inv.move_id.line_id
                    to_reconcile_ids = {}
                    for line in movelines:
                        if line.account_id.id == inv.account_id.id:
                            to_reconcile_ids[line.account_id.id] = [line.id]
                        if type(line.reconcile_id) != osv.orm.browse_null:
                            reconcile_obj.unlink(cr, uid, line.reconcile_id.id)
                    wf_service.trg_validate(uid, 'account.invoice', \
                                        refund.id, 'invoice_open', cr)
                    
                    refund = inv_obj.browse(cr, uid, refund_id[0], context=context)
                    self.cn_iva_validate(cr,uid,refund,context=context)
                    
                    for tmpline in  refund.move_id.line_id:
                        if tmpline.account_id.id == inv.account_id.id:
                            to_reconcile_ids[tmpline.account_id.id].append(tmpline.id)
                    for account in to_reconcile_ids:
                        account_m_line_obj.reconcile(cr, uid, to_reconcile_ids[account],
                                        writeoff_period_id=period,
                                        writeoff_journal_id = inv.journal_id.id,
                                        writeoff_acc_id=inv.account_id.id
                                        )
                    if mode == 'modify':
                        invoice = inv_obj.read(cr, uid, [inv.id],
                                    ['name', 'type', 'number', 'supplier_invoice_number',
                                    'comment', 'date_due', 'partner_id',
                                    'partner_insite', 'partner_contact',
                                    'partner_ref', 'payment_term', 'account_id',
                                    'currency_id', 'invoice_line', 'tax_line',
                                    'journal_id', 'period_id'], context=context)
                        invoice = invoice[0]
                        del invoice['id']
                        invoice_lines = inv_line_obj.browse(cr, uid, invoice['invoice_line'], context=context)

                        invoice_lines = inv_obj._refund_cleanup_lines(cr, uid, invoice_lines)
                        tax_lines = inv_tax_obj.browse(cr, uid, invoice['tax_line'], context=context)
                        tax_lines = inv_obj._refund_cleanup_lines(cr, uid, tax_lines)
                        #Add origin value
                        orig = self._get_orig(cr, uid, inv, invoice['supplier_invoice_number'], context)
                        invoice.update({
                            'type': inv.type,
                            'date_invoice': date,
                            'state': 'draft',
                            'number': False,
                            'invoice_line': invoice_lines,
                            'tax_line': tax_lines,
                            'period_id': period,
                            'name': description,
                            'origin': orig,
                          
                        })
                        for field in ( 'partner_id',
                                'account_id', 'currency_id', 'payment_term', 'journal_id'):
                                invoice[field] = invoice[field] and invoice[field][0]
                        inv_id = inv_obj.create(cr, uid, invoice, {})
                        if inv.payment_term.id:
                            data = inv_obj.onchange_payment_term_date_invoice(cr, uid, [inv_id], inv.payment_term.id, date)
                            if 'value' in data and data['value']:
                                inv_obj.write(cr, uid, [inv_id], data['value'])
                        created_inv.append(inv_id)
                        
                        new_inv_brw = inv_obj.browse(cr,uid,created_inv[1],context=context)
                        inv_obj.write(cr,uid,created_inv[0],{'name':wzd_brw.description,'origin':new_inv_brw.origin},context=context)
                        inv_obj.write(cr,uid,created_inv[1],{'origin':inv.origin,'name':wzd_brw.description},context=context)
            if inv.type in ('out_invoice', 'out_refund'):
                xml_id = 'action_invoice_tree3'
                #~ if hasattr(inv, 'sale_ids'):
                    #~ for i in inv.sale_ids:
                        #~ cr.execute('insert into sale_order_invoice_rel (order_id,invoice_id) values (%s,%s)', (i.id, refund_id[0]))
            else:
                xml_id = 'action_invoice_tree4'
            result = mod_obj.get_object_reference(cr, uid, 'account', xml_id)
            id = result and result[1] or False
            result = act_obj.read(cr, uid, id, context=context)
            invoice_domain = eval(result['domain'])
            invoice_domain.append(('id', 'in', created_inv))
            result['domain'] = invoice_domain
            
            if wzd_brw.filter_refund == 'cancel':
                orig = self._get_orig(cr, uid, inv, inv.supplier_invoice_number, context)
                inv_obj.write(cr,uid,created_inv[0],{'origin':orig,'name':wzd_brw.description},context=context)
            
            if wzd_brw.filter_refund == 'refund':
                orig = self._get_orig(cr, uid, inv, inv.supplier_invoice_number, context)
                inv_obj.write(cr,uid,created_inv[0],{'origin':inv.origin,'name':wzd_brw.description},context=context)
            return result


account_invoice_refund()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
