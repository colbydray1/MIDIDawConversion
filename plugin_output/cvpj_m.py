# SPDX-FileCopyrightText: 2022 Colby Ray
# SPDX-License-Identifier: GPL-3.0-or-later

import plugin_output
import json

class output_cvpj(plugin_output.base):
    def __init__(self): pass
    def getname(self): return 'DEBUG'
    def getshortname(self): return 'cvpj_m'
    def gettype(self): return 'm'
    def parse(self, convproj_json, output_file):
        projJ = json.loads(convproj_json)
        with open(output_file, "w") as fileout:
            fileout.write("CONVPROJ___M\n")
            json.dump(projJ, fileout, indent=4, sort_keys=True)