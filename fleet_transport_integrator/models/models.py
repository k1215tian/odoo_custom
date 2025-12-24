# -*- coding: utf-8 -*-

# from odoo import models, fields, api


# class fleet_transport_integrator(models.Model):
#     _name = 'fleet_transport_integrator.fleet_transport_integrator'
#     _description = 'fleet_transport_integrator.fleet_transport_integrator'

#     name = fields.Char()
#     value = fields.Integer()
#     value2 = fields.Float(compute="_value_pc", store=True)
#     description = fields.Text()
#
#     @api.depends('value')
#     def _value_pc(self):
#         for record in self:
#             record.value2 = float(record.value) / 100

