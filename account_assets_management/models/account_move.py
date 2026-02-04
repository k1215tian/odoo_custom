# -*- coding: utf-8 -*-
import logging
from markupsafe import Markup

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

# List of move's fields that can't be modified if move is linked
# with a depreciation line
FIELDS_AFFECTS_ASSET_MOVE = {"journal_id", "date"}
# List of move line's fields that can't be modified if move is linked
# with a depreciation line
FIELDS_AFFECTS_ASSET_MOVE_LINE = {
    "credit",
    "debit",
    "account_id",
    "journal_id",
    "date",
    "asset_profile_id",
    "asset_id",
}


_logger = logging.getLogger(__name__)


class AccountMove(models.Model):
    _inherit = 'account.move'

    asset_count = fields.Integer(compute="_compute_asset_count")

    def _compute_asset_count(self):
        rg_res = self.env["account.asset.line"].read_group(
            [("move_id", "in", self.ids)], ["move_id"], ["move_id"]
        )
        mapped_data = {x["move_id"][0]: x["move_id_count"] for x in rg_res}
        for move in self:
            move.asset_count = mapped_data.get(move.id, 0)

    def unlink(self):
        # for move in self:
        deprs = (
            self.env["account.asset.line"]
            .sudo()
            .search(
                [("move_id", "in", self.ids),
                 ("type", "in", ["depreciate", "remove"])]
            )
        )
        if deprs and not self.env.context.get("unlink_from_asset"):
            raise UserError(
                self.env._(
                    "You are not allowed to remove an accounting entry "
                    "linked to an asset."
                    "\nYou should remove such entries from the asset."
                )
            )
        # trigger store function
        deprs.write({"move_id": False})
        return super().unlink()

    def write(self, vals):
        if set(vals).intersection(FIELDS_AFFECTS_ASSET_MOVE):
            deprs = (
                self.env["account.asset.line"]
                .sudo()
                .search([("move_id", "in", self.ids), ("type", "=", "depreciate")])
            )
            if deprs:
                raise UserError(
                    self.env._(
                        "You cannot change an accounting entry "
                        "linked to an asset depreciation line."
                    )
                )
        return super().write(vals)

    def _prepare_asset_vals(self, aml):
        depreciation_base = aml.balance
        return {
            "name": aml.name,
            "code": self.name,
            "profile_id": aml.asset_profile_id.id,
            "purchase_value": depreciation_base,
            "purchase_date": self.date,
            "partner_id": aml.partner_id.id,
            "date_start": self.date,
        }
    
    def action_post(self):
        """ 
        Override action_post untuk otomatis membuat record aset.
        Setiap baris invoice yang memiliki Profil Aset akan menjadi satu record Aset.
        """
        ret_val = super().action_post()
        
        for move in self:
            created_assets = []
            
            # Filter baris yang punya profil aset dan bukan baris pajak
            asset_lines = move.line_ids.filtered(
                lambda l: l.asset_profile_id and not l.tax_line_id and not l.asset_id
            )
            
            for aml in asset_lines:
                if not aml.name:
                    raise UserError(_("Nama aset harus diisi pada label baris invoice."))

                # Memanggil fungsi helper untuk menyiapkan data
                vals = move._prepare_asset_vals(aml)
                
                # Buat record aset
                asset = self.env["account.asset"].with_company(move.company_id).with_context(
                    create_asset_from_move_line=True, 
                    move_id=move.id
                ).create(vals)
                
                # Copy analytic distribution
                asset.analytic_distribution = aml.analytic_distribution
                
                # Hubungkan balik baris jurnal ke aset yang baru dibuat
                aml.with_context(allow_asset=True).write({'asset_id': asset.id})
                created_assets.append(asset)

            # Kirim pesan ke Chatter jika ada aset yang dibuat
            for asset in created_assets:
                message = _(
                    "Invoice ini telah membuat aset: <a href=# data-oe-model=account.asset data-oe-id=%s>%s</a>",
                    asset.id, asset.display_name
                )
                move.message_post(body=message)
                
        return ret_val

    def button_draft(self):
        invoices = self.filtered(lambda r: r.is_purchase_document())
        if invoices:
            invoices.line_ids.asset_id.unlink()
        return super().button_draft()

    def _reverse_move_vals(self, default_values, cancel=True):
        move_vals = super()._reverse_move_vals(default_values, cancel)
        if move_vals["move_type"] not in ("out_invoice", "out_refund"):
            for line_command in move_vals.get("line_ids", []):
                line_vals = line_command[2]  # (0, 0, {...})
                asset = self.env["account.asset"].browse(line_vals["asset_id"])
                # We remove the asset if we recognize that we are reversing
                # the asset creation
                if asset:
                    asset_line = self.env["account.asset.line"].search(
                        [("asset_id", "=", asset.id), ("type", "=", "create")], limit=1
                    )
                    if asset_line and asset_line.move_id == self:
                        asset.unlink()
                        line_vals.update(
                            asset_profile_id=False, asset_id=False)
        return move_vals

    def action_view_assets(self):
        assets = (
            self.env["account.asset.line"]
            .search([("move_id", "=", self.id)])
            .mapped("asset_id")
        )
        action = self.env.ref("account_asset_management.account_asset_action")
        action_dict = action.sudo().read()[0]
        if len(assets) == 1:
            res = self.env.ref(
                "account_asset_management.account_asset_view_form", False
            )
            action_dict["views"] = [(res and res.id or False, "form")]
            action_dict["res_id"] = assets.id
        elif assets:
            action_dict["domain"] = [("id", "in", assets.ids)]
        else:
            action_dict = {"type": "ir.actions.act_window_close"}
        return action_dict
    
    def _create_assets_from_move_lines(self):
        """ 
        Fungsi helper untuk otomatis membuat record Asset dari baris Journal Entry/Invoice.
        Logika ini dijalankan saat Invoice di-post.
        """
        asset_obj = self.env['account.asset']
        for line in self.line_ids.filtered(lambda l: l.asset_profile_id and not l.asset_id):
            # 1. Menyiapkan nilai awal aset berdasarkan baris jurnal (move line)
            # Kita mengambil setting default dari Profile yang dipilih
            vals = {
                'name': line.name or line.product_id.name or _("Asset from %s") % self.name,
                'code': self.name, # Menggunakan nomor invoice sebagai referensi awal
                'profile_id': line.asset_profile_id.id,
                'purchase_value': abs(line.balance), # Nilai perolehan (debet)
                'salvage_value': 0.0,
                'date_start': self.date, # Tanggal mulai penyusutan biasanya sama dengan tanggal invoice
                'company_id': self.company_id.id,
                'currency_id': self.currency_id.id,
                'partner_id': self.partner_id.id,
                # Link balik ke move line agar kita tahu aset ini datang dari mana
                # Pastikan field 'invoice_line_id' atau sejenisnya ada di model account.asset Anda
            }

            # 2. Sinkronisasi parameter penyusutan dari Profile ke Aset
            # Ini memastikan field seperti method_number (usia) tercopy ke record aset
            profile = line.asset_profile_id
            vals.update({
                'method': profile.method,
                'method_number': profile.method_number,
                'method_period': profile.method_period,
                'method_time': profile.method_time,
                'journal_id': profile.journal_id.id,
                'account_asset_id': profile.account_asset_id.id,
                'account_depreciation_id': profile.account_depreciation_id.id,
                'account_depreciation_expense_id': profile.account_depreciation_expense_id.id,
            })

            # 3. Create record aset
            asset = asset_obj.create(vals)
            
            # 4. Update link di move line agar tidak terproses dua kali
            line.write({'asset_id': asset.id})

            # 5. Log ke Chatter Invoice bahwa aset telah dibuat
            msg = _("Asset Created: <a href=# data-oe-model=account.asset data-oe-id=%d>%s</a>") % (asset.id, asset.name)
            self.message_post(body=msg)

        return True


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    asset_profile_id = fields.Many2one(
        comodel_name="account.asset.profile",
        string="Asset Profile",
        compute="_compute_asset_profile",
        store=True,
        readonly=False,
    )
    asset_id = fields.Many2one(
        comodel_name="account.asset",
        string="Asset",
        ondelete="restrict",
        check_company=True,
    )

    @api.depends("account_id", "asset_id")
    def _compute_asset_profile(self):
        for rec in self:
            if rec.account_id.asset_profile_id and not rec.asset_id:
                rec.asset_profile_id = rec.account_id.asset_profile_id
            elif rec.asset_id:
                rec.asset_profile_id = rec.asset_id.profile_id

    @api.onchange("asset_profile_id")
    def _onchange_asset_profile_id(self):
        if self.asset_profile_id.account_asset_id:
            self.account_id = self.asset_profile_id.account_asset_id

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            move = self.env["account.move"].browse(vals.get("move_id"))
            if not move.is_sale_document():
                if vals.get("asset_id") and not self.env.context.get("allow_asset"):
                    raise UserError(
                        self.env._(
                            "You are not allowed to link "
                            "an accounting entry to an asset."
                            "\nYou should generate such entries from the asset."
                        )
                    )
        records = super().create(vals_list)
        for record in records:
            record._expand_asset_line()
        return records

    def write(self, vals):
        if set(vals).intersection(FIELDS_AFFECTS_ASSET_MOVE_LINE) and not (
            self.env.context.get("allow_asset_removal")
            and list(vals.keys()) == ["asset_id"]
        ):
            # Check if at least one asset is linked to a move
            linked_asset = False
            for move_line in self.filtered(lambda r: not r.move_id.is_sale_document()):
                linked_asset = move_line.asset_id
                if linked_asset:
                    raise UserError(
                        self.env._(
                            "You cannot change an accounting item "
                            "linked to an asset depreciation line."
                        )
                    )

        if (
            self.filtered(lambda r: not r.move_id.is_sale_document())
            and vals.get("asset_id")
            and not self.env.context.get("allow_asset")
        ):
            raise UserError(
                self.env._(
                    "You are not allowed to link "
                    "an accounting entry to an asset."
                    "\nYou should generate such entries from the asset."
                )
            )
        super().write(vals)
        if "quantity" in vals or "asset_profile_id" in vals:
            for record in self:
                record._expand_asset_line()
        return True

    def _expand_asset_line(self):
        self.ensure_one()
        if self.asset_profile_id.asset_product_item and self.quantity > 1.0:
            aml = self.with_context(check_move_validity=False)
            qty = self.quantity
            name = self.name
            aml.write({"quantity": 1, "name": f"{name} {1}"})
            for i in range(1, int(qty)):
                aml.copy({"name": f"{name} {i + 1}"})
