from odoo.exceptions import ValidationError, UserError
from odoo.tools import float_compare, float_is_zero
from odoo import api, fields, models, _ # Pastikan _ juga di-import untuk translasi

class StockPicking(models.Model):
    _inherit = 'stock.picking'

    total_predicted_weight = fields.Float(
        string='Total Predicted Weight',
        compute='_compute_picking_predictions',
        help="Total estimasi berat untuk seluruh dokumen ini."
    )
    total_predicted_volume = fields.Float(
        string='Total Predicted Volume',
        compute='_compute_picking_predictions',
        help="Total estimasi volume untuk seluruh dokumen ini."
    )
    total_reserved_weight = fields.Float(
        string='Total Reserved Weight',
        compute='_compute_reserved_totals',
        help="Total berat kotor dari semua produk yang dicadangkan."
    )
    total_reserved_volume = fields.Float(
        string='Total Reserved Volume',
        compute='_compute_reserved_totals',
        help="Total volume dari semua produk yang dicadangkan."
    )

    @api.depends('move_ids.reserved_weight', 'move_ids.reserved_volume')
    def _compute_reserved_totals(self):
        for picking in self:
            picking.total_reserved_weight = sum(move.reserved_weight for move in picking.move_ids)
            picking.total_reserved_volume = sum(move.reserved_volume for move in picking.move_ids)

    @api.depends('move_ids.predicted_weight', 'move_ids.predicted_volume')
    def _compute_picking_predictions(self):
        for picking in self:
            picking.total_predicted_weight = sum(move.predicted_weight for move in picking.move_ids)
            picking.total_predicted_volume = sum(move.predicted_volume for move in picking.move_ids)

    def action_assign(self):
        res = super(StockPicking, self).action_assign()
        for picking in self:
            picking._compute_reserved_totals()
        return res