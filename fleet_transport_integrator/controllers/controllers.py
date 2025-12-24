# -*- coding: utf-8 -*-
# from odoo import http


# class FleetTransportIntegrator(http.Controller):
#     @http.route('/fleet_transport_integrator/fleet_transport_integrator', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/fleet_transport_integrator/fleet_transport_integrator/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('fleet_transport_integrator.listing', {
#             'root': '/fleet_transport_integrator/fleet_transport_integrator',
#             'objects': http.request.env['fleet_transport_integrator.fleet_transport_integrator'].search([]),
#         })

#     @http.route('/fleet_transport_integrator/fleet_transport_integrator/objects/<model("fleet_transport_integrator.fleet_transport_integrator"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('fleet_transport_integrator.object', {
#             'object': obj
#         })

