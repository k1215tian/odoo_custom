# -*- coding: utf-8 -*-
# from odoo import http


# class FleetPickingTransport(http.Controller):
#     @http.route('/fleet_picking_transport/fleet_picking_transport', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/fleet_picking_transport/fleet_picking_transport/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('fleet_picking_transport.listing', {
#             'root': '/fleet_picking_transport/fleet_picking_transport',
#             'objects': http.request.env['fleet_picking_transport.fleet_picking_transport'].search([]),
#         })

#     @http.route('/fleet_picking_transport/fleet_picking_transport/objects/<model("fleet_picking_transport.fleet_picking_transport"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('fleet_picking_transport.object', {
#             'object': obj
#         })

