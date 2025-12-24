# -*- coding: utf-8 -*-
# from odoo import http


# class FleetTransportInteligent(http.Controller):
#     @http.route('/fleet_transport_inteligent/fleet_transport_inteligent', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/fleet_transport_inteligent/fleet_transport_inteligent/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('fleet_transport_inteligent.listing', {
#             'root': '/fleet_transport_inteligent/fleet_transport_inteligent',
#             'objects': http.request.env['fleet_transport_inteligent.fleet_transport_inteligent'].search([]),
#         })

#     @http.route('/fleet_transport_inteligent/fleet_transport_inteligent/objects/<model("fleet_transport_inteligent.fleet_transport_inteligent"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('fleet_transport_inteligent.object', {
#             'object': obj
#         })

