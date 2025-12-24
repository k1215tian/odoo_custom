# -*- coding: utf-8 -*-
# from odoo import http


# class FleetTransportAccount(http.Controller):
#     @http.route('/fleet_transport_account/fleet_transport_account', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/fleet_transport_account/fleet_transport_account/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('fleet_transport_account.listing', {
#             'root': '/fleet_transport_account/fleet_transport_account',
#             'objects': http.request.env['fleet_transport_account.fleet_transport_account'].search([]),
#         })

#     @http.route('/fleet_transport_account/fleet_transport_account/objects/<model("fleet_transport_account.fleet_transport_account"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('fleet_transport_account.object', {
#             'object': obj
#         })

