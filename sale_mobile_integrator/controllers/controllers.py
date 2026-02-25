# -*- coding: utf-8 -*-
# from odoo import http


# class /opt/odoo18/odoo/custom/addons/odooCustom/saleMobileIntegrator(http.Controller):
#     @http.route('//opt/odoo18/odoo/custom/addons/odoo_custom/sale_mobile_integrator//opt/odoo18/odoo/custom/addons/odoo_custom/sale_mobile_integrator', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('//opt/odoo18/odoo/custom/addons/odoo_custom/sale_mobile_integrator//opt/odoo18/odoo/custom/addons/odoo_custom/sale_mobile_integrator/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('/opt/odoo18/odoo/custom/addons/odoo_custom/sale_mobile_integrator.listing', {
#             'root': '//opt/odoo18/odoo/custom/addons/odoo_custom/sale_mobile_integrator//opt/odoo18/odoo/custom/addons/odoo_custom/sale_mobile_integrator',
#             'objects': http.request.env['/opt/odoo18/odoo/custom/addons/odoo_custom/sale_mobile_integrator./opt/odoo18/odoo/custom/addons/odoo_custom/sale_mobile_integrator'].search([]),
#         })

#     @http.route('//opt/odoo18/odoo/custom/addons/odoo_custom/sale_mobile_integrator//opt/odoo18/odoo/custom/addons/odoo_custom/sale_mobile_integrator/objects/<model("/opt/odoo18/odoo/custom/addons/odoo_custom/sale_mobile_integrator./opt/odoo18/odoo/custom/addons/odoo_custom/sale_mobile_integrator"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('/opt/odoo18/odoo/custom/addons/odoo_custom/sale_mobile_integrator.object', {
#             'object': obj
#         })

