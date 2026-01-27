# -*- coding: utf-8 -*-
import logging

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class HrTerminationAsset(models.Model):
    """
    Model Child untuk tracking inventaris yang dibawa karyawan.
    """
    _name = 'hr.termination.asset'
    _description = 'Employee Asset Return'
    _check_company_auto = True  # Best practice Odoo 17 untuk multi-company

    # ---------------------------
    # Relasi ke model lain
    # ---------------------------
    resignation_id = fields.Many2one(
        'hr.employee.termination',
        string='Termination Ref',
        ondelete='cascade',
        required=True,
        help="Referensi ke dokumen induk terminasi."
    )
    account_asset_id = fields.Many2one(
        'account.asset',
        string="Accounting Asset Link",
        help="Link ke master asset Accounting"
    )
    equipment_id = fields.Many2one(
        'maintenance.equipment',
        string="Maintenance Equipment Link",
        help="Link ke master equipment Maintenance"
    )

    # ---------------------------
    # Data aset
    # ---------------------------
    asset_name = fields.Char(
        string='Asset Name',
        required=True,
        help="Contoh: Laptop MacBook Pro"
    )
    serial_no = fields.Char(
        string='Serial Number',
        help="Nomor seri aset untuk validasi fisik."
    )
    qty = fields.Integer(
        string='Quantity',
        default=1,
        help="Jumlah fisik.",
        required=True
    )
    qty_return = fields.Integer(
        string='Quantity Returned',
        default=0,
        help="Jumlah aset yang dikembalikan."
    )
    is_returned = fields.Boolean(
        string='Returned',
        tracking=True,
        default=False
    )
    notes = fields.Text(
        string='Condition Notes',
        help="Catatan kondisi aset saat dikembalikan."
    )
    company_id = fields.Many2one(
        'res.company', 
        string='Company', 
        default=lambda self: self.env.company
    )
    currency_id = fields.Many2one(
        'res.currency', 
        related='company_id.currency_id'
    )
    asset_amount = fields.Monetary(
        string='Asset Amount', 
        currency_field='currency_id'
    )
    compensation_amount = fields.Monetary(
        string='Compensation Amount',
        currency_field='currency_id',
        help="Manual input jika barang rusak, atau otomatis hitung jika qty kurang."
    )

    # ---------------------------
    # Actions / Onchange
    # ---------------------------
    @api.onchange('qty', 'qty_return', 'asset_amount')
    def _onchange_return_logic(self):
        """
        Logika pembantu saat user menginput data di form.
        """
        for rec in self:
            rec.is_returned = rec.qty_return >= rec.qty and rec.qty > 0
            if rec.qty > 0 and rec.qty_return < rec.qty:
                missing_qty = rec.qty - rec.qty_return
                rec.compensation_amount = missing_qty * (rec.asset_amount / rec.qty)

    def action_mark_returned(self):
        """
        Tandai aset sebagai sudah dikembalikan.
        Mengisi qty_return sesuai qty jika belum diisi.
        """
        for rec in self:
            if rec.qty_return < rec.qty:
                rec.qty_return = rec.qty if rec.qty_return == 0 else rec.qty_return
            rec.is_returned = True

    # ---------------------------
    # Constraints
    # ---------------------------
    @api.constrains('qty', 'qty_return', 'notes', 'compensation_amount')
    def _check_qty_and_notes(self):
        for rec in self:
            if rec.qty < 1:
                raise ValidationError("Quantity (qty) tidak boleh kurang dari 1.")
            if rec.qty_return < 0:
                raise ValidationError("Quantity returned (qty_return) tidak boleh negatif.")
            if rec.qty_return > rec.qty:
                raise ValidationError("Quantity returned (qty_return) tidak boleh lebih besar dari Quantity (qty).")
            if rec.qty != rec.qty_return and not rec.notes:
                raise ValidationError(
                    "Jika Quantity berbeda dengan Quantity Returned, silakan isi alasan di Notes."
                )
            if rec.compensation_amount > 0 and not rec.notes:
                raise ValidationError(
                    _("Mohon isi Notes untuk menjelaskan alasan munculnya Compensation Amount (misal: barang rusak/hilang).")
                )

    _sql_constraints = [
        ('asset_name_required', 'CHECK(asset_name IS NOT NULL)', 'Asset name is required'),
    ]