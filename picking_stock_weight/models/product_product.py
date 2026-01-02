# Copyright 2015 ADHOC SA  (http://www.adhoc.com.ar)
# Copyright 2015-2016 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.exceptions import ValidationError, UserError
from odoo.tools import float_compare, float_is_zero
from odoo import api, fields, models, _ # Pastikan _ juga di-import untuk translasi

class ProductProduct(models.Model):
    _inherit = "product.product"

    product_length = fields.Float("length")
    product_height = fields.Float("height")
    product_width = fields.Float("width")
    dimensional_uom_id = fields.Many2one(
        "uom.uom",
        "Dimensional UoM",
        domain=lambda self: self._get_dimension_uom_domain(),
        help="UoM for length, height, width",
        default=lambda self: self.env.ref("uom.product_uom_meter"),
    )
    volume = fields.Float(
        compute="_compute_volume",
        readonly=False,
        store=True,
    )

    net_weight = fields.Float(
        digits="Stock Weight",
        help="Weight of the product without container nor packaging.",
    )

    # Explicit field, renaming it
    weight = fields.Float(
        string="Gross Weight",
        help="Weight of the product with its container and packaging.",
    )
    @api.depends(
        "product_length", "product_height", "product_width", "dimensional_uom_id"
    )
    def _compute_volume(self):
        template_obj = self.env["product.template"]
        for product in self:
            product.volume = template_obj._calc_volume(
                product.product_length,
                product.product_height,
                product.product_width,
                product.dimensional_uom_id,
            )

    @api.model
    def _get_dimension_uom_domain(self):
        return [("category_id", "=", self.env.ref("uom.uom_categ_length").id)]

    @api.constrains("net_weight", "weight")
    def _check_net_weight(self):
        prec = self.env["decimal.precision"].precision_get("Stock Weight")
        for product in self:
            if (
                not float_is_zero(product.weight, precision_digits=prec)
                and float_compare(
                    product.net_weight, product.weight, precision_digits=prec
                )
                > 0
            ):
                raise ValidationError(
                    _("The net weight of product '%s' must be lower than gross weight.")
                    % product.display_name
                )
