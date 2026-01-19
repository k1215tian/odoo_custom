# -*- coding: utf-8 -*-

import logging
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class WisEmployeeChild_ids(models.TransientModel):
    _name = 'wis.employee.child_ids'
    _description = _('WisEmployeeChild_ids')

    name = fields.Char(_('Name'))

    def add(self):
        _logger.log('Hello Wizard')
