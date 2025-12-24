# -*- coding: utf-8 -*-
# from odoo import http


# class DeliveryDistanceBasewh(http.Controller):
#     @http.route('/delivery_distance_basewh/delivery_distance_basewh', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/delivery_distance_basewh/delivery_distance_basewh/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('delivery_distance_basewh.listing', {
#             'root': '/delivery_distance_basewh/delivery_distance_basewh',
#             'objects': http.request.env['delivery_distance_basewh.delivery_distance_basewh'].search([]),
#         })

#     @http.route('/delivery_distance_basewh/delivery_distance_basewh/objects/<model("delivery_distance_basewh.delivery_distance_basewh"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('delivery_distance_basewh.object', {
#             'object': obj
#         })

