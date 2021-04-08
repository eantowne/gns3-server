#!/usr/bin/env python
#
# Copyright (C) 2016 GNS3 Technologies Inc.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import os
import aiohttp
import asyncio
import urllib.parse
import xml.etree.ElementTree as ET

from gns3server.web.route import Route
from gns3server.controller import Controller


import logging
log = logging.getLogger(__name__)


class SymbolHandler:
    """
    API entry points for symbols management.
    """

    @Route.get(
        r"/symbols",
        description="List of symbols",
        status_codes={
            200: "Symbols list returned"
        })
    def list(request, response):

        controller = Controller.instance()
        response.json(controller.symbols.list())

    @Route.get(
        r"/symbols/{symbol_id:.+}/dimensions",
        description="Get the symbol dimensions",
        status_codes={
            200: "Symbol dimensions returned"
        })
    async def raw(request, response):

        controller = Controller.instance()
        symbol_id = urllib.parse.unquote(request.match_info["symbol_id"])
        try:
            file_content = open(controller.symbols.get_path(symbol_id), 'r').read()
            svg_root = ET.fromstring(file_content)

            svg_width = svg_root.get('width')
            if svg_width is not None:
                try:
                    width = int(float(svg_width))
                except:
                    log.warning("Could not get width for symbol with id: {}".format(symbol_id))
                    width = 0
            
            svg_height = svg_root.get('height')
            if svg_height is not None:
                try:
                    height = int(float(svg_height))
                except:
                    log.warning("Could not get height for symbol with id: {}".format(symbol_id))
                    height = 0
            
            symbol_dimensions = { 'width': width, 'height': height }
            response.json(symbol_dimensions)
        except (KeyError, OSError) as e:
            log.warning("Could not get symbol file: {}".format(e))
            response.set_status(404)

    @Route.get(
        r"/symbols/{symbol_id:.+}/raw",
        description="Get the symbol file",
        status_codes={
            200: "Symbol returned"
        })
    async def raw(request, response):

        controller = Controller.instance()
        symbol_id = urllib.parse.unquote(request.match_info["symbol_id"])
        try:
            await response.stream_file(controller.symbols.get_path(symbol_id))
        except (KeyError, OSError) as e:
            log.warning("Could not get symbol file: {}".format(e))
            response.set_status(404)

    @Route.post(
        r"/symbols/{symbol_id:.+}/raw",
        description="Write the symbol file",
        status_codes={
            200: "Symbol written"
        },
        raw=True)
    async def upload(request, response):

        controller = Controller.instance()
        symbol_id = urllib.parse.unquote(request.match_info["symbol_id"])
        path = os.path.join(controller.symbols.symbols_path(), os.path.basename(symbol_id))
        try:
            with open(path, "wb") as f:
                while True:
                    try:
                        chunk = await request.content.read(1024)
                    except asyncio.TimeoutError:
                        raise aiohttp.web.HTTPRequestTimeout(text="Timeout when writing to symbol '{}'".format(path))
                    if not chunk:
                        break
                    f.write(chunk)
        except (UnicodeEncodeError, OSError) as e:
            raise aiohttp.web.HTTPConflict(text="Could not write symbol file '{}': {}".format(path, e))

        # Reset the symbol list
        controller.symbols.list()
        response.set_status(204)

    @Route.get(
        r"/default_symbols",
        description="List of default symbols",
        status_codes={
            200: "Default symbols list returned"
        })
    def list_default_symbols(request, response):

        controller = Controller.instance()
        response.json(controller.symbols.default_symbols())

    # @Route.post(
    #     r"/symbol_theme",
    #     description="Create a new symbol theme",
    #     status_codes={
    #         201: "Appliance created",
    #         400: "Invalid request"
    #     },
    #     input=APPLIANCE_CREATE_SCHEMA,
    #     output=APPLIANCE_OBJECT_SCHEMA)
    # def create(request, response):
    #
    #     controller = Controller.instance()
    #     appliance = controller.add_appliance(request.json)
    #     response.set_status(201)
    #     response.json(appliance)