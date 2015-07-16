#!/usr/bin/python
# -*- encoding: utf-8 -*-
# http://www.gnu.org/licenses/agpl-3.0.html

import time

from openerp.report import report_sxw
from openerp.tools.translate import _


class Parser(report_sxw.rml_parse):
    # Variables Globales----------------------------------------------------
    ttcompra = 0
    ttcompra_sdcf = 0
    ttretencion = 0
    ttbase = 0
    ttiva = 0

    # ---------------------------------------------------------------------

    def __init__(self, cr, uid, name, context):
        super(Parser, self).__init__(cr, uid, name, context)
        self.localcontext.update({
            'time': time,
            'get_partner_addr': self._get_partner_addr,
        })

    def _get_partner_addr(self, idp=False):
        """ Return address2 partner
        """
        if not idp:
            return []

        addr_obj = self.pool.get('res.partner')
        addr_inv = _('NO FISCAL ADDRESS DEFINED')
        addr_inv = {}
        if idp:
            addr = addr_obj.browse(self.cr, self.uid, idp)
            addr_inv = (
                (addr.street and ('%s, ' % addr.street.title()) or '') +
                (addr.zip and ('Codigo Postal: %s, ' % addr.zip) or '') +
                (addr.city and ('%s, ' % addr.city.title()) or '') +
                (addr.state_id and ('%s, ' % addr.state_id.name.title()) or '')
                + (addr.country_id and ('%s ' % addr.country_id.name.title())
                   or '') or _('NO INVOICE ADDRESS DEFINED'))
        return addr_inv


report_sxw.report_sxw(
    'report.account.wh.fiscalseal',
    'account.wh.fiscalseal',
    'addons/l10n_ve_withholding_fiscalseal/report/wh_fiscalseal_report.rml',
    parser=Parser,
    header=False
)

report_sxw.report_sxw(
    'report.account.fiscalseal.summary',
    'account.fiscalseal.summary',
    'addons/l10n_ve_withholding_fiscalseal/report/summary_fs_report.rml',
    parser=Parser,
    header=False
)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
