# -*- coding: utf-8 -*-

import logging
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class WizHrPaklaring(models.TransientModel):
    _name = 'wiz.hr.paklaring'
    _description = _('WizHrPaklaring')

    name = fields.Char(_('Name'))

    def add(self):
        _logger.log('Hello Wizard')
