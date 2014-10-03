# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2009 Tiny SPRL (<http://tiny.be>). All Rights Reserved
#    OVL : Openerp Venezuelan Localization
#    Copyleft (Cl) 2008-2021 Vauxoo, C.A. (<http://vauxoo.com>)
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
{
    "name": "OpenERP Venezuelan Localization", 
    "version": "4.0", 
    "author": "Vauxoo", 
    "category": "Localization/Application", 
    "description": """
Install all apps needed to comply with Venezuelan laws
======================================================

This module will install for you:

  -  l10n_ve_fiscal_requirements 

  -  l10n_ve_split_invoice

  -  l10n_ve_generic

  -  l10n_ve_imex

  -  l10n_ve_withholding 

  -  l10n_ve_withholding_iva

  -  l10n_ve_withholding_islr

  -  l10n_ve_withholding_muni

  -  l10n_ve_withholding_src

  -  l10n_ve_fiscal_book

  -  l10n_ve_vat_write_off


Optionals (Not installed by default), uncomment on your/addons/path/ovl/__openerp__.py file this dependencies if you want to use them

 - "l10n_ve_sale_purchase", #Install if you want be able set islr 

Concepts from Sales and Purchase

                                     # Level Zero of Modules 
                 # First Level of Modules 
                 # Second Level of Modules 
                 # Third Level of Modules 
                 # Fourth Level of Modules 
                 # Optionals, uncomment if you want to use them Install if you
                 # want be able set islr 
                 #"l10n_ve_sale_purchase",
                 # Fifth Level of Modules 
                 #"l10n_ve_vat_write_off",
 - "l10n_ve_sale_purchase", #Install if you want be able set islr 
""", 
    "website": "http://www.vauxoo.com", 
    "license": "", 
    "depends": [
        "account", 
        "document", 
        "l10n_ve_fiscal_requirements", 
        "l10n_ve_split_invoice", 
        "l10n_ve_generic", 
        "l10n_ve_imex", 
        "l10n_ve_withholding", 
        "l10n_ve_withholding_iva", 
        "l10n_ve_withholding_islr", 
        "l10n_ve_withholding_muni", 
        "l10n_ve_withholding_src", 
        "l10n_ve_fiscal_book"
    ], 
    "demo": [], 
    "data": [
        "view/account_invoice_view.xml"
    ], 
    "test": [], 
    "js": [], 
    "css": [], 
    "qweb": [], 
    "installable": True, 
    "auto_install": False
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: