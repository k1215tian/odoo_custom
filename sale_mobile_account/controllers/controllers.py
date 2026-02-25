# -*- coding: utf-8 -*-
# from odoo import http


# class /opt/odoo18/odoo/custom/addons/odooCustom/saleMobileAccount(http.Controller):
#     @http.route('//opt/odoo18/odoo/custom/addons/odoo_custom/sale_mobile_account//opt/odoo18/odoo/custom/addons/odoo_custom/sale_mobile_account', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('//opt/odoo18/odoo/custom/addons/odoo_custom/sale_mobile_account//opt/odoo18/odoo/custom/addons/odoo_custom/sale_mobile_account/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('/opt/odoo18/odoo/custom/addons/odoo_custom/sale_mobile_account.listing', {
#             'root': '//opt/odoo18/odoo/custom/addons/odoo_custom/sale_mobile_account//opt/odoo18/odoo/custom/addons/odoo_custom/sale_mobile_account',
#             'objects': http.request.env['/opt/odoo18/odoo/custom/addons/odoo_custom/sale_mobile_account./opt/odoo18/odoo/custom/addons/odoo_custom/sale_mobile_account'].search([]),
#         })

#     @http.route('//opt/odoo18/odoo/custom/addons/odoo_custom/sale_mobile_account//opt/odoo18/odoo/custom/addons/odoo_custom/sale_mobile_account/objects/<model("/opt/odoo18/odoo/custom/addons/odoo_custom/sale_mobile_account./opt/odoo18/odoo/custom/addons/odoo_custom/sale_mobile_account"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('/opt/odoo18/odoo/custom/addons/odoo_custom/sale_mobile_account.object', {
#             'object': obj
#         })

