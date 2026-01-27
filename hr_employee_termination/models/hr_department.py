# -*- coding: utf-8 -*-
import logging

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class HrDepartment(models.Model):
    _inherit = 'hr.department'

    is_clearance_dept = fields.Boolean(
        string='Is Termination Validator', 
        help="Check this if this department needs to validate employee termination/resignation."
    )