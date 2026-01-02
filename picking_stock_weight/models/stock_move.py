from odoo.exceptions import ValidationError, UserError
from odoo.tools import float_compare, float_is_zero
from odoo import api, fields, models, _ # Pastikan _ juga di-import untuk translasi


class StockMove(models.Model):
    _inherit = 'stock.move'

    # Field Prediksi (Berdasarkan Qty yang dipesan/booked)
    predicted_weight = fields.Float(
        string='Predicted Gross Weight',
        compute='_compute_predicted_totals',
        store=True,
        help="Estimasi berat kotor berdasarkan jumlah pesanan."
    )
    predicted_volume = fields.Float(
        string='Predicted Volume',
        compute='_compute_predicted_totals',
        store=True,
        help="Estimasi volume berdasarkan jumlah pesanan."
    )

    # Field Ter-reservasi (Berdasarkan Qty yang benar-benar ada stoknya)
    reserved_weight = fields.Float(
        string='Reserved Gross Weight',
        compute='_compute_reserved_totals',
        store=True,
        help="Berat kotor dari jumlah produk yang berhasil dicadangkan."
    )
    reserved_volume = fields.Float(
        string='Reserved Volume',
        compute='_compute_reserved_totals',
        store=True,
        help="Volume dari jumlah produk yang berhasil dicadangkan."
    )

    @api.depends('product_id', 'product_uom_qty', 'product_id.weight', 'product_id.volume')
    def _compute_predicted_totals(self):
        for move in self:
            qty = move.product_uom_qty
            move.predicted_weight = (move.product_id.weight or 0.0) * qty
            move.predicted_volume = (move.product_id.volume or 0.0) * qty

    @api.depends('forecast_availability', 'product_id', 'product_uom')
    def _compute_reserved_totals(self):
        for move in self:
            qty_reserved = move.forecast_availability
            if qty_reserved > 0:
                qty_in_base_uom = move.product_uom._compute_quantity(
                    qty_reserved,
                    move.product_id.uom_id
                )
                move.reserved_weight = qty_in_base_uom * move.product_id.weight
                move.reserved_volume = qty_in_base_uom * move.product_id.volume
            else:
                move.reserved_weight = 0.0
                move.reserved_volume = 0.0

    def action_assign(self):
        res = super(StockMove, self).action_assign()
        for move in self:
            move._compute_predicted_totals()
            move._compute_reserved_totals()
        return res