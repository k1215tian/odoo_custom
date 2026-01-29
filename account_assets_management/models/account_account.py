# -*- coding: utf-8 -*-
import logging

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class AccountAccount(models.Model):
    _inherit = 'account.account'

    asset_profile_id = fields.Many2one(
        'account.asset.profile',
        string='Default Asset Profile',
        ondelete='set null',  # Jika profil dihapus, field ini jadi kosong
        check_company=True,
    )

    @api.constrains('asset_profile_id')
    def _check_asset_profile_account(self):
        for rec in self:
            if rec.asset_profile_id and rec.asset_profile_id.account_asset_id.id != rec.id:
                raise ValidationError(_(
                    "Akun '%s' harus sama dengan Akun Aset yang ada di Profile '%s'."
                ) % (rec.name, rec.asset_profile_id.name))
