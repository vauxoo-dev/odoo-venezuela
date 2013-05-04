from openerp.osv import fields, osv
from datetime import datetime, timedelta

class vat_write_off(osv.osv):
    _description = ''
    _name = 'vat.write.off'
    _columns = {
        'company_id':fields.many2one('res.company','Company',
            help='Company',required=True),
        'period_id':fields.many2one('account.period','Period',
            help="Book's Fiscal Period",required=True),
        'state': fields.selection([('draft','Getting Ready'),
            ('open','Approved by Manager'),('done','Seniat Submitted')],
            string='Status', required=True),          
        'purchase_fb_id':fields.many2one('fiscal.book', 'Purchase Fiscal Book',
            help='Purchase Fiscal Book'),
        'p_get_vat_sdcf_do_sum' : fields.related('purchase_fb_id',
											  'get_vat_sdcf_do_sum',
											  type="float",
											  readonly=True,
											  store=True,), 
		'p_get_vat_all_imex_base_sum' : fields.related('purchase_fb_id',
												'get_vat_all_imex_base_sum',
												 type="float",
												 readonly=True,
												 store=True,),
		'p_get_vat_general_do_base_sum' : fields.related('purchase_fb_id',
														'get_vat_general_do_base_sum',
														type="float",
														readonly=True,
														store=True,),
		'p_get_vat_general_do_tax_sum' : fields.related('purchase_fb_id',
													'get_vat_general_do_tax_sum',
													type="float",
													readonly=True,
													store=True,),
		'p_get_vat_additional_do_base_sum' : fields.related('purchase_fb_id',
														  'get_vat_additional_do_base_sum',
														  type="float",
														  readonly=True,
														  store=True,),
		'p_get_vat_additional_do_tax_sum' : fields.related('purchase_fb_id',
														'get_vat_additional_do_tax_sum',
														type="float",
														readonly=True,
														store=True,),
		'p_get_vat_reduced_do_base_sum' : fields.related('purchase_fb_id',
													  'get_vat_reduced_do_base_sum',
													  type="float",
													  readonly=True,
													  store=True,),
		'p_get_vat_reduced_do_tax_sum' : fields.related('purchase_fb_id',
													'get_vat_reduced_do_tax_sum',
													type="float",
													readonly=True,
													store=True,),
		'p_tax_amount' : fields.related('purchase_fb_id',
									 'tax_amount',
									 type="float",
									 readonly=True,
									 store=True,),
        'sale_fb_id':fields.many2one('fiscal.book', 'Sale Fiscal Book',
            help='Sale Fiscal Book'),
        's_get_vat_sdcf_sum' : fields.related('sale_fb_id',
											'get_vat_sdcf_sum',
											type="float",
											readonly=True,
											store=True,),
		's_get_vat_general_imex_base_sum' : fields.related('sale_fb_id',
													 'get_vat_general_imex_base_sum',
													 type="float",
													 readonly=True,
													 store=True,),
		's_get_vat_general_imex_tax_sum' : fields.related('sale_fb_id',
													'get_vat_general_imex_tax_sum',
													type="float",
													readonly=True,
													store=True),
		's_get_vat_additional_imex_base_sum' : fields.related('sale_fb_id',
														  'get_vat_additional_imex_base_sum',
														  type="float",
														  readonly=True,
														  store=True),
		's_get_vat_additional_imex_tax_sum' : fields.related('sale_fb_id',
														  'get_vat_additional_imex_tax_sum',
														  type="float",
														  readonly=True,
														  store=True),
		's_get_vat_reduced_imex_base_sum' : fields.related('sale_fb_id',
													   'get_vat_reduced_imex_base_sum',
													   type="float",
													   readonly=True,
													   store=True),
		's_get_vat_reduced_imex_tax_sum' : fields.related('sale_fb_id',
													   'get_vat_reduced_imex_tax_sum',
													   type="float",
													   readonly=True,
													   store=True),
		's_get_vat_general_do_base_sum' : fields.related('sale_fb_id',
													 'get_vat_general_do_base_sum',
													 type="float",
													 readonly=True,
													 store=True),
		's_get_vat_general_do_tax_sum' : fields.related('sale_fb_id',
													  'get_vat_general_do_tax_sum',
													  type="float",
													  readonly=True,
													  store=True),
		's_get_vat_additional_do_base_sum' : fields.related('sale_fb_id',
														  'get_vat_additional_do_base_sum',
														  type="float",
														  readonly=True,
														  store=True),
		's_get_vat_additional_do_tax_sum' : fields.related('sale_fb_id',
														 'get_vat_additional_do_tax_sum',
														 type="float",
														 readonly=True,
														 store=True),
		's_get_vat_reduced_do_base_sum' : fields.related('sale_fb_id',
													  'get_vat_reduced_do_base_sum',
													  type="float",
													  readonly=True,
													  store=True),
		's_get_vat_reduced_do_tax_sum' : fields.related('sale_fb_id',
													  'get_vat_reduced_do_tax_sum',
													  type="float",
													  readonly=True,
													  store=True),
		's_base_amount' : fields.related('sale_fb_id',
									   'base_amount',
									   type="float",
									   readonly=True,
									   store=True),
		's_tax_amount' : fields.related('sale_fb_id',
									   'tax_amount',
									   type="float",
									   readonly=True,
									   store=True),
        'start_date' : fields.date(string='Start date'),
        
        'vat' : fields.related('company_id',
							   'partner_id',
							   'vat',
							   type='char',
							   string='TIN',
							   readonly=True,
							   store=True),
							   
        
    }
    _defaults = {
        'state': 'draft',
        'company_id': lambda s,c,u,ctx: \
            s.pool.get('res.users').browse(c,u,u,context=ctx).company_id.id,
        'start_date': fields.date.today, 
    }
