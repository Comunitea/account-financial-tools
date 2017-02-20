# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright 2015 Pexego Sistemas Informáticos. All Rights Reserved
#    @author Omar Castiñeira Saavedra <omar@pexego.es>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published
#    by the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

{
    "name": "Account Admin Importation Tools",
    "version": "0.1",
    "author": "Pexego",
    "website": "http://www.pexego.es",
    "category": "Enterprise Specific Modules",
    "description": """Account Importarion Tools for Administrators

Import tools:

- Import accounts from CSV files. This may be useful to import the initial
  accounts into OpenERP.

- Import account moves from CSV files. This may be useful to import the initial
  balance into OpenERP.
            """,
    "depends": ['base',
                'account',
                'account_admin_tools'],
    "data": ['admin_tools_menu.xml',
             'account_importer.xml',
             'account_move_importer.xml'],
    "installable": True,
    'license': 'AGPL-3'
}
