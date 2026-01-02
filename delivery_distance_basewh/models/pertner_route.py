# -*- coding: utf-8 -*-
import logging

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class PertnerRoute(models.Model):
    _name = 'pertner.route'
    _description = 'PertnerRoute'

    name = fields.Char('Name')
