# -*- coding: utf-8 -*-
# Copyright 2016 Tecnativa - Antonio Espinosa
# Copyright 2017 Tecnativa - Luis M. Ontalba
# Copyright 2017 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import calendar
from odoo import models, fields, api, _
from odoo.tools import float_compare
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DF
from datetime import date, datetime
from dateutil.relativedelta import relativedelta


class AccountAssetAsset(models.Model):
    _inherit = "account.asset.asset"

    state = fields.Selection(
        selection_add=[('disposed', 'Disposed')],
    )
    disposal_date = fields.Date(string="Disposal date")
    disposal_move_id = fields.Many2one(
        comodel_name='account.move', string="Disposal move",
    )

    def _disposal_line_asset_prepare(self, date):
        self.ensure_one()
        return {
            'name': _('Asset disposal'),
            'journal_id': self.category_id.journal_id.id,
            'account_id': self.category_id.account_asset_id.id,
            'date': date,
            'debit': 0.0,
            'credit': self.value,
        }

    def _disposal_line_depreciation_prepare(self, date, loss_value):
        self.ensure_one()
        depreciation_value = self.value - loss_value
        return {
            'name': _('Asset depreciation'),
            'journal_id': self.category_id.journal_id.id,
            'account_id': self.category_id.account_depreciation_id.id,
            'date': date,
            'debit': depreciation_value,
            'credit': 0.0,
        }

    def _disposal_line_loss_prepare(self, date, loss_account, loss_value):
        self.ensure_one()
        return {
            'name': _('Asset loss'),
            'journal_id': self.category_id.journal_id.id,
            'account_id': loss_account.id,
            'analytic_account_id': self.category_id.account_analytic_id.id,
            'date': date,
            'debit': loss_value,
            'credit': 0.0,
        }

    def _disposal_move_prepare(self, date, loss_account):
        self.ensure_one()
        journal = self.category_id.journal_id
        loss_value = self.salvage_value if self.salvage_value > 0 else 0.0
        if float_compare(self.value_residual, 0,
                         precision_rounding=self.currency_id.rounding) == 1:
            loss_value += self.value_residual
        lines = [
            (0, False, self._disposal_line_asset_prepare(date)),
            (0, False, self._disposal_line_depreciation_prepare(
                date, loss_value,
            )),
        ]
        # Metemos el cálculo del depreciado en el años
        #year_depreciated_amount = asset.disposal_year_depreciation(date)
        #loss_value -= year_depreciated_amount
        if loss_value:
            lines.append((
                0, False, self._disposal_line_loss_prepare(
                    date, loss_account, loss_value,
                ),
            ))
        return {
            'journal_id': journal.id,
            'ref': self.name,
            'date': date,
            'line_ids': lines,
        }

    @api.multi
    def action_disposal(self):
        wizard_view_id = self.env.ref(
            'account_asset_disposal.account_asset_disposal_wizard_form')
        return {
            'name': _('Dispose Asset'),
            'res_model': 'account.asset.disposal.wizard',
            'type': 'ir.actions.act_window',
            'view_type': 'tree,form',
            'view_mode': 'form',
            'view_id': wizard_view_id.id,
            'target': 'new',
            'context': self.env.context,
        }


    def disposal_year_depreciation(self, depreciation_date):
        for asset in self:
            depreciation_date =datetime.strptime(depreciation_date, DF).date()
            day = depreciation_date.day
            month = depreciation_date.month
            year = depreciation_date.year
            total_days = (year % 4) and 365 or 366
            days = (depreciation_date - self.company_id.compute_fiscalyear_dates(depreciation_date)['date_from']  ).days
            if asset.method_time == 'percentage':

                percentage = self.method_percentage * days / total_days
                amount = (asset.value - asset.salvage_value) * percentage / 100
                return amount
            elif asset.method == 'linear':
                amount = ((asset.value - asset.salvage_value) / self.method_number) * days / total_days
                return amount
            else:
                return 0


    @api.multi
    def dispose(self, date, loss_account):
        moves = self.env['account.move']

        for asset in self:
            # FIX
            # Calcula amortizado en el año hasta fecha

            year_depreciated_amount = asset.disposal_year_depreciation(date)

            unposted_lines = asset.depreciation_line_ids.filtered(
                lambda x: not x.move_check
            )
            # Creamos una lina para la depreciación en el año y la posteamos
            sequence = (
                len(asset.depreciation_line_ids) - len(unposted_lines) +1
            )
            last_depr = asset.depreciation_line_ids[sequence -2 ]
            vals = {
                'amount': year_depreciated_amount,
                'asset_id': asset.id,
                'sequence': sequence,
                'name': (asset.code or '') + '/' + str(sequence),
                'remaining_value': asset.value - (last_depr.depreciated_value + year_depreciated_amount),
                # the asset is completely depreciated
                'depreciated_value': last_depr.depreciated_value + year_depreciated_amount,
                'depreciation_date': date,
            }
            year_depr = asset.depreciation_line_ids.create(vals)
            year_depr.create_move()

            move = self.env['account.move'].create(
                asset._disposal_move_prepare(date, loss_account)
            )
            asset.disposal_move_id = move.id
            move.post()

            unposted_lines = asset.depreciation_line_ids.filtered(
                lambda x: not x.move_check
            )
            if unposted_lines:
                # Remove all unposted depreciation lines
                asset.write({
                    'depreciation_line_ids': [
                        (2, line_id.id) for line_id in unposted_lines
                    ],
                })
            # Create a new depr. line with the residual amount and post it
            sequence = (
                len(asset.depreciation_line_ids) - len(unposted_lines) + 1
            )
            vals = {
                'amount': asset.value_residual,
                'asset_id': asset.id,
                'sequence': sequence,
                'name': (asset.code or '') + '/' + str(sequence),
                'remaining_value': 0,
                # the asset is completely depreciated
                'depreciated_value': asset.value - asset.salvage_value,
                'depreciation_date': date,
                'move_id': move.id,
            }
            asset.depreciation_line_ids.create(vals)
            asset.message_post(body=_('Asset disposed.'))
            moves += move
        self.write({
            'disposal_date': date,
            'state': 'disposed',
        })
        if moves:
            name = _('Disposal Move')
            view_mode = 'form'
            if len(moves) > 1:
                name = _('Disposal Moves')
                view_mode = 'tree,form'
            return {
                'name': name,
                'domain': [('id', 'in', moves.ids)],
                'view_type': 'form',
                'view_mode': view_mode,
                'res_model': 'account.move',
                'type': 'ir.actions.act_window',
                'target': 'current',
                'res_id': moves[:1].id,
            }

    @api.multi
    def action_disposal_undo(self):
        for asset in self.with_context(asset_disposal_undo=True):
            if asset.disposal_move_id:
                asset.disposal_move_id.button_cancel()
                asset.disposal_move_id.unlink()

            if asset.depreciation_line_ids[-2].move_id:
                asset.depreciation_line_ids[-2].move_id.button_cancel()
                asset.depreciation_line_ids[-2].move_id.unlink()

            asset.depreciation_line_ids[-1].unlink()
            asset.depreciation_line_ids[-1].unlink()
            if asset.currency_id.is_zero(asset.value_residual):
                asset.state = 'close'
            else:
                asset.state = 'open'
                asset.compute_depreciation_board()
            asset.message_post(body=_('Asset disposal cancelled.'))
        return self.write({
            'disposal_date': False,
            'disposal_move_id': False,
        })
