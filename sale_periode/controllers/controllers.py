# -*- coding: utf-8 -*-
# from odoo import http


# class SalePeriode(http.Controller):
#     @http.route('/sale_periode/sale_periode', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/sale_periode/sale_periode/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('sale_periode.listing', {
#             'root': '/sale_periode/sale_periode',
#             'objects': http.request.env['sale_periode.sale_periode'].search([]),
#         })

#     @http.route('/sale_periode/sale_periode/objects/<model("sale_periode.sale_periode"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('sale_periode.object', {
#             'object': obj
#         })

