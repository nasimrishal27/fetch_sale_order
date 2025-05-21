# -- coding: utf-8 --

from odoo import fields, models
import xmlrpc.client


class FetchSaleOrderWizard(models.TransientModel):
    """ Model for fetching the sale order """
    _name = "fetch.sale.order.wizard"
    _description = "Model for fetching sale orders"

    db = fields.Char(string="Enter DB name", required=True)
    db_url = fields.Char(string="Enter DB URL", required=True)
    db_username = fields.Char(string="Enter your DB Username", required=True)
    db_password = fields.Char(string="Enter your DB Password", required=True)

    def action_fetch_sale_order(self):
        """ Function for fetching the sale order """
        common_1 = xmlrpc.client.ServerProxy(f'{self.db_url}/xmlrpc/2/common')
        models_1 = xmlrpc.client.ServerProxy(f'{self.db_url}/xmlrpc/2/object')
        uid_db1 = common_1.authenticate(self.db, self.db_username, self.db_password, {})
        sale_orders = models_1.execute_kw(
            self.db, uid_db1, self.db_password,
            'sale.order', 'search_read', [[]],
            {'fields': ['id', 'name', 'partner_id', 'state', 'user_id', 'order_line', 'picking_ids']}
        )
        sale_order_id_map = {}
        for order in sale_orders:
            remote_sale_id = order['id']
            picking_ids = order.get('picking_ids', [])
            sale_order_vals = {
                'name': order['name'],
                'state': order['state'],
                'user_id': order['user_id'][0] if order['user_id'] else False,
                'partner_id': order['partner_id'][0] if order['partner_id'] else False,
                'picking_ids': [fields.Command.set([])],
            }
            sale_order = self.env['sale.order'].create(sale_order_vals)
            sale_order_id_map[remote_sale_id] = sale_order.id
            order_line_ids = order.get('order_line', [])
            if order_line_ids:
                order_lines = models_1.execute_kw(
                    self.db, uid_db1, self.db_password, 'sale.order.line', 'read', [order_line_ids],
                    {'fields': ['product_id', 'product_uom_qty', 'price_unit', 'name', 'tax_id', 'product_uom']})

                for line in order_lines:
                    self.env['sale.order.line'].create({
                        'order_id': sale_order.id, 'name': line['name'],
                        'product_id': line['product_id'][0] if line['product_id'] else False,
                        'product_uom_qty': line['product_uom_qty'], 'price_unit': line['price_unit']})

            if picking_ids:
                pickings = models_1.execute_kw(
                    self.db, uid_db1, self.db_password, 'stock.picking', 'read', [picking_ids],
                    {'fields': ['name', 'picking_type_id', 'location_id', 'location_dest_id',
                                'move_ids_without_package', 'scheduled_date', 'origin', 'sale_id']})

                local_picking_ids = []
                for picking in pickings:
                    local_sale_id = sale_order_id_map.get(picking['sale_id'][0]) if picking['sale_id'] else False
                    if not local_sale_id:
                        continue

                    local_picking = self.env['stock.picking'].create({
                        'origin': picking.get('origin'), 'sale_id': local_sale_id,
                        'partner_id': sale_order.partner_id.id, 'scheduled_date': picking.get('scheduled_date'),
                        'location_id': picking['location_id'][0] if picking['location_id'] else False,
                        'location_dest_id': picking['location_dest_id'][0] if picking['location_dest_id'] else False,
                        'picking_type_id': picking['picking_type_id'][0] if picking['picking_type_id'] else False,})

                    local_picking_ids.append(local_picking.id)

                    move_ids = picking.get('move_ids_without_package', [])
                    if move_ids:
                        moves = models_1.execute_kw(
                            self.db, uid_db1, self.db_password,
                            'stock.move', 'read', [move_ids],
                            {'fields': ['name', 'product_id', 'product_uom_qty', 'product_uom', 'quantity']}
                        )
                        for move in moves:
                            self.env['stock.move'].create({
                                'name': move['name'], 'picking_id': local_picking.id,
                                'product_id': move['product_id'][0] if move['product_id'] else False,
                                'product_uom_qty': move['product_uom_qty'],
                                'product_uom': move['product_uom'][0] if move['product_uom'] else False,
                                'quantity': move['quantity'],
                                'location_id': picking['location_id'][0] if picking['location_id'] else False,
                                'location_dest_id': picking['location_dest_id'][0] if picking[
                                    'location_dest_id'] else False})

                if local_picking_ids:
                    sale_order.write({'picking_ids': [fields.Command.set(local_picking_ids)]})