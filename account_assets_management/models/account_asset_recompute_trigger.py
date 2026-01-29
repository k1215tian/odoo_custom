# -*- coding: utf-8 -*-
import logging

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class AccountAssetRecomputeTrigger(models.Model):
    _name = 'account.asset.recompute.trigger'
    _description = "Asset table recompute triggers"

    reason = fields.Char(required=True)
    company_id = fields.Many2one("res.company", string="Company", required=True)
    date_trigger = fields.Datetime(
        "Trigger Date",
        readonly=True,
        help="Date of the event triggering the need to recompute the Asset Tables.",
    )
    date_completed = fields.Datetime("Completion Date", readonly=True)
    state = fields.Selection(
        selection=[("open", "Open"), ("done", "Done")],
        default="open",
        readonly=True,
    )
