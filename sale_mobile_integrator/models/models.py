# -*- coding: utf-8 -*-

# from odoo import models, fields, api


# class /opt/odoo18/odoo/custom/addons/odoo_custom/sale_mobile_integrator(models.Model):
#     _name = '/opt/odoo18/odoo/custom/addons/odoo_custom/sale_mobile_integrator./opt/odoo18/odoo/custom/addons/odoo_custom/sale_mobile_integrator'
#     _description = '/opt/odoo18/odoo/custom/addons/odoo_custom/sale_mobile_integrator./opt/odoo18/odoo/custom/addons/odoo_custom/sale_mobile_integrator'

#     name = fields.Char()
#     value = fields.Integer()
#     value2 = fields.Float(compute="_value_pc", store=True)
#     description = fields.Text()
#
#     @api.depends('value')
#     def _value_pc(self):
#         for record in self:
#             record.value2 = float(record.value) / 100

