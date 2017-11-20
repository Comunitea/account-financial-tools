# -*- coding: utf-8 -*-
# © 2017 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.tests import common


class TestCurrencyRateUpdatePlNbp(common.SavepointCase):

    def setUp(self):
        super(TestCurrencyRateUpdatePlNbp, self).setUp()
        self.env.user.company_id.currency_id = self.env.ref('base.EUR')
        self.currency = self.env.ref('base.USD')
        self.update_service = self.env['currency.rate.update.service'].create({
            'service': 'PL_NBP',
            'currency_to_update': [(4, self.currency.id)]
        })
        currency_rates = self.env['res.currency.rate'].search(
            [('currency_id', '=', self.currency.id)])
        currency_rates.unlink()

    def test_currency_rate_update_PL_NBP(self):
        self.update_service.refresh_currency()
        currency_rates = self.env['res.currency.rate'].search(
            [('currency_id', '=', self.currency.id)])
        self.assertTrue(currency_rates)
