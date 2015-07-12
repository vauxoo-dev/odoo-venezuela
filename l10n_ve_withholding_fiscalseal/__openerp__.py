#!/usr/bin/python
# -*- encoding: utf-8 -*-
{
    "name": "Fiscal Seal Withholding",
    "version": "1.0",
    "author": "Vauxoo",
    "website": "http://vauxoo.com",
    "category": 'Generic Modules/Accounting',
    "description": """
Management withholding vat based in the Venezuelan tax laws.
""",
    "depends": [
        "l10n_ve_withholding"
    ],
    'data': [
        # 'security/wh_iva_security.xml',
        # 'security/ir.model.access.csv',
        # 'report/withholding_vat_report.xml',
        'view/wizard_retention_view.xml',
        # 'wizard/wizard_wh_nro_view.xml',
        # 'view/generate_txt_view.xml',
        'view/invoice_view.xml',
        # 'view/account_view.xml',
        # 'view/partner_view.xml',
        # 'view/res_company_view.xml',
        'view/wh_view.xml',
        # "data/l10n_ve_withholding_data.xml",
        # 'report/txt_wh_report.xml',
        # "workflow/wh_iva_workflow.xml",
        # "workflow/wh_action_server.xml",
    ],
    'demo': [
        # "demo/l10n_ve_withholding_iva_sequences_demo.xml",
        # "demo/demo_partners.xml",
        # "demo/l10n_ve_withholding_iva_demo.xml",
        # "demo/demo_taxes.xml",
        # "demo/demo_invoices.xml",
    ],

    'test': [
        # test/purchase_invoice_wh_iva.yml',
        # test/sale_invoice_wh_iva.yml',
        # test/sale_wh_iva.yml',
        # test/purchase_wh_iva.yml',
        # test/purchase_wh_iva_sequence.yml',
        # test/sale_wh_iva_sequence.yml',
        # test/purchase_wh_iva_txt.yml',
    ],
    'installable': True,
    'active': False,
}


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
