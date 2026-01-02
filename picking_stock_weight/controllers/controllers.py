# -*- coding: utf-8 -*-
# from odoo import http


# class PickingStockWeight(http.Controller):
#     @http.route('/picking_stock_weight/picking_stock_weight', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/picking_stock_weight/picking_stock_weight/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('picking_stock_weight.listing', {
#             'root': '/picking_stock_weight/picking_stock_weight',
#             'objects': http.request.env['picking_stock_weight.picking_stock_weight'].search([]),
#         })

#     @http.route('/picking_stock_weight/picking_stock_weight/objects/<model("picking_stock_weight.picking_stock_weight"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('picking_stock_weight.object', {
#             'object': obj
#         })

