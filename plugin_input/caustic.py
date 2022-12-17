# SPDX-FileCopyrightText: 2022 Colby Ray
# SPDX-License-Identifier: GPL-3.0-or-later

caustic_instnames = {}
caustic_instnames['NULL'] = 'None'
caustic_instnames['SSYN'] = 'SubSynth'
caustic_instnames['PCMS'] = 'PCMSynth'
caustic_instnames['BLNE'] = 'BassLine'
caustic_instnames['BBOX'] = 'BeatBox'
caustic_instnames['PADS'] = 'PadSynth'
caustic_instnames['8SYN'] = '8BitSynth'
caustic_instnames['MDLR'] = 'Modular'
caustic_instnames['ORGN'] = 'Organ'
caustic_instnames['VCDR'] = 'Vocoder'
caustic_instnames['FMSN'] = 'FMSynth'
caustic_instnames['KSSN'] = 'KSSynth'
caustic_instnames['SAWS'] = 'SawSynth'

caustic_instcolors = {}
caustic_instcolors['NULL'] = [0, 0, 0]
caustic_instcolors['SSYN'] = [0.79, 0.82, 0.91]
caustic_instcolors['PCMS'] = [0.78, 0.84, 0.65]
caustic_instcolors['BLNE'] = [0.99, 0.99, 0.99]
caustic_instcolors['BBOX'] = [0.66, 0.51, 0.36]
caustic_instcolors['PADS'] = [0.99, 0.99, 0.69]
caustic_instcolors['8SYN'] = [0.82, 0.78, 0.63]
caustic_instcolors['MDLR'] = [0.45, 0.45, 0.45]
caustic_instcolors['ORGN'] = [0.68, 0.30, 0.03]
caustic_instcolors['VCDR'] = [0.74, 0.35, 0.35]
caustic_instcolors['FMSN'] = [0.29, 0.78, 0.76]
caustic_instcolors['KSSN'] = [0.55, 0.57, 0.44]
caustic_instcolors['SAWS'] = [0.99, 0.60, 0.25]

from functions import format_caustic
from functions import data_bytes
import plugin_input
import json

class input_cvpj_r(plugin_input.base):
    def __init__(self): pass
    def getshortname(self): return 'caustic'
    def getname(self): return 'Caustic 3'
    def gettype(self): return 'mi'
    def supported_autodetect(self): return False
    def parse(self, input_file, extra_param):
        CausticData = format_caustic.deconstruct_main(input_file)
        machines = CausticData['Machines']

        cvpj_l = {}
        cvpj_l_instruments = {}
        cvpj_l_instrumentsorder = []
        cvpj_l_notelistindex = {}
        cvpj_l_playlist = {}
        cvpj_l_fxrack = {}

        machnum = 0
        plnum = 0
        for machine in machines:
            machnum += 1
            plnum += 1
            cvpj_inst = {}
            cvpj_inst["enabled"] = 1
            cvpj_inst["instdata"] = {}
            cvpj_instdata = cvpj_inst["instdata"]
            cvpj_instdata['plugin'] = 'none'
            cvpj_instdata['usemasterpitch'] = 1
            cvpj_inst["name"] = caustic_instnames[machine['id']]
            cvpj_inst["color"] = caustic_instcolors[machine['id']]
            cvpj_inst["pan"] = 0.0
            cvpj_inst["vol"] = 1.0
            cvpj_l_instruments['Mach'+str(machnum)] = cvpj_inst
            cvpj_l_instrumentsorder.append('Mach'+str(machnum))
            cvpj_l_fxrack[str(machnum)] = {}
            cvpj_l_fxrack[str(machnum)]["name"] = caustic_instnames[machine['id']]
            cvpj_l_playlist[str(plnum)] = {}
            cvpj_l_playlist[str(plnum)]["name"] = caustic_instnames[machine['id']]
            cvpj_l_playlist[str(plnum)]["color"] = caustic_instcolors[machine['id']]

        cvpj_l['notelistindex'] = cvpj_l_notelistindex
        cvpj_l['fxrack'] = cvpj_l_fxrack
        cvpj_l['instruments'] = cvpj_l_instruments
        cvpj_l['instrumentsorder'] = cvpj_l_instrumentsorder
        cvpj_l['playlist'] = cvpj_l_playlist
        cvpj_l['bpm'] = 140
        return json.dumps(cvpj_l)

