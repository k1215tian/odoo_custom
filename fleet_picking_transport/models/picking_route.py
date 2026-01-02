# -*- coding: utf-8 -*-
import logging

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class PickingRoute(models.Model):
    _name = 'picking.route'
    _description = 'PickingRoute'

    name = fields.Char('Name')
