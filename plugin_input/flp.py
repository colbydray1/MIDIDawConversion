# SPDX-FileCopyrightText: 2022 Colby Ray 
# SPDX-License-Identifier: GPL-3.0-or-later 

import plugin_input
import json
import math
import base64
from functions import format_flp

class input_flp(plugin_input.base):
    def __init__(self): pass
    def getshortname(self): return 'flp'
    def getname(self): return 'FL Studio'
    def gettype(self): return 'mi'
    def supported_autodetect(self): return True
    def detect(self, input_file):
        bytestream = open(input_file, 'rb')
        bytestream.seek(0)
        bytesdata = bytestream.read(4)
        if bytesdata == b'FLhd': return True
        else: return False
    def parse(self, input_file, extra_param):
        FLP_Data = format_flp.deconstruct(input_file)
        #print(FLP_Data['FL_Main'])

        FL_Main = FLP_Data['FL_Main']
        FL_Patterns = FLP_Data['FL_Patterns']
        FL_Channels = FLP_Data['FL_Channels']
        FL_Mixer = FLP_Data['FL_Mixer']
        FL_Arrangements = FLP_Data['FL_Arrangements']
        FL_TimeMarkers = FLP_Data['FL_TimeMarkers']

        ppq = FL_Main['ppq']

        rootJ = {}
        rootJ['mastervol'] = 1
        rootJ['timesig_numerator'] = FL_Main['Numerator']
        rootJ['timesig_denominator'] = FL_Main['Denominator']
        rootJ['bpm'] = FL_Main['Tempo']

        instrumentsJ = {}
        instrumentsorder = []
        notelistindexJ = {}
        playlistJ = {}
        timemarkersJ = []

        id_inst = {}
        id_pat = {}

        for instrument in FL_Channels:
            channeldata = FL_Channels[instrument]
            #print(channeldata)
            instdata = {}
            if channeldata['type'] == 0 or channeldata['type'] == 2:
                singleinstdata = {}
                singleinstdata['instdata'] = {}
                singleinstdata['enabled'] = channeldata['enabled']
                singleinstdata['fxrack_channel'] = channeldata['fxchannel']
                if 'middlenote' in channeldata: singleinstdata['instdata']['middlenote'] = channeldata['middlenote']-60
                else: singleinstdata['instdata']['middlenote'] = 0
                singleinstdata['instdata']['pitch'] = channeldata['pitch']
                singleinstdata['instdata']['usemasterpitch'] = channeldata['main_pitch']
                singleinstdata['name'] = channeldata['name']
                singleinstdata['pan'] = channeldata['pan']
                singleinstdata['vol'] = channeldata['volume']
                color = channeldata['color'].to_bytes(4, "little")
                singleinstdata['color'] = [color[0]/255,color[1]/255,color[2]/255]
                if channeldata['type'] == 0:
                    singleinstdata['instdata']['plugin'] = "sampler"
                    singleinstdata['instdata']['plugindata'] = {}
                    if 'samplefilename' in channeldata:
                        singleinstdata['instdata']['plugindata']['file'] = channeldata['samplefilename']
                    else:
                        singleinstdata['instdata']['plugindata']['file'] = ''
                if channeldata['type'] == 2:
                    singleinstdata['instdata']['plugin'] = "native-fl"
                    singleinstdata['instdata']['plugindata'] = {}
                    if 'plugin' in channeldata: singleinstdata['instdata']['plugindata']['name'] = channeldata['plugin']
                    if 'pluginparams' in channeldata: singleinstdata['instdata']['plugindata']['data'] = base64.b64encode(channeldata['pluginparams']).decode('ascii')
                instrumentsJ['FLInst' + str(instrument)] = singleinstdata
                instrumentsorder.append('FLInst' + str(instrument))
                id_inst[str(instrument)] = 'FLInst' + str(instrument)

        for pattern in FL_Patterns:
            patterndata = FL_Patterns[pattern]
            notesJ = []
            if 'FLPat' + str(pattern) not in notelistindexJ:
                notelistindexJ['FLPat' + str(pattern)] = {}
            if 'notes' in patterndata:
                for flnote in patterndata['notes']:
                    noteJ = {}
                    noteJ['position'] = (flnote['pos']/ppq)*4
                    if str(flnote['rack']) in id_inst: noteJ['instrument'] = id_inst[str(flnote['rack'])]
                    else: noteJ['instrument'] = ''
                    noteJ['duration'] = (flnote['dur']/ppq)*4
                    noteJ['key'] = flnote['key']-60
                    noteJ['finepitch'] = (flnote['finep']-120)*10
                    noteJ['release'] = flnote['rel']/128
                    noteJ['pan'] = (flnote['pan']-64)/64
                    noteJ['vol'] = flnote['velocity']/100
                    noteJ['cutoff'] = flnote['mod_x']/255
                    noteJ['reso'] = flnote['mod_y']/255
                    notesJ.append(noteJ)
                notelistindexJ['FLPat' + str(pattern)]['notelist'] = notesJ
                id_pat[str(pattern)] = 'FLPat' + str(pattern)
            if 'color' in patterndata:
                color = patterndata['color'].to_bytes(4, "little")
                if color != b'HQV\x00':
                    notelistindexJ['FLPat' + str(pattern)]['color'] = [color[0]/255,color[1]/255,color[2]/255]
            if 'name' in patterndata: notelistindexJ['FLPat' + str(pattern)]['name'] = patterndata['name']

        FL_Arrangement = FL_Arrangements['0']
        for item in FL_Arrangement['items']:
            arrangementitemJ = {}
            arrangementitemJ['position'] = item['position']/ppq*4
            arrangementitemJ['duration'] = item['length']/ppq*4
            arrangementitemJ['type'] = 'instruments'
            arrangementitemJ['fromindex'] = 'FLPat' + str(item['itemindex'] - item['patternbase'])
            if 'startoffset' in item or 'endoffset' in item:
                arrangementitemJ['cut'] = {}
                if 'startoffset' in item: arrangementitemJ['cut']['start'] = item['startoffset']/ppq*4
                if 'endoffset' in item: arrangementitemJ['cut']['end'] = item['endoffset']/ppq*4
            playlistline = (item['trackindex']*-1)+500
            length = item['length']
            if str(playlistline) not in playlistJ:
                playlistJ[str(playlistline)] = {}
                playlistJ[str(playlistline)]['placements'] = []
            playlistJ[str(playlistline)]['placements'].append(arrangementitemJ)

        FL_Tracks = FL_Arrangement['tracks']

        for track in FL_Tracks:
            if str(track) not in playlistJ:
                playlistJ[str(track)] = {}
            if 'color' in FL_Tracks[track]:
                color = FL_Tracks[track]['color'].to_bytes(4, "little")
            playlistJ[str(track)]['color'] = [color[0]/255,color[1]/255,color[2]/255]
            if 'name' in FL_Tracks[track]:
                playlistJ[str(track)]['name'] = FL_Tracks[track]['name']

        for timemarker in FL_TimeMarkers:
            tm_pos = FL_TimeMarkers[timemarker]['pos']/ppq*4
            tm_type = FL_TimeMarkers[timemarker]['type']
            timemarkerJ = {}
            timemarkerJ['name'] = FL_TimeMarkers[timemarker]['name']
            timemarkerJ['position'] = FL_TimeMarkers[timemarker]['pos']/ppq*4
            if tm_type == 5: timemarkerJ['type'] = 'start'
            if tm_type == 4: timemarkerJ['type'] = 'loop'
            if tm_type == 1: timemarkerJ['type'] = 'markerloop'
            if tm_type == 2: timemarkerJ['type'] = 'markerskip'
            if tm_type == 3: timemarkerJ['type'] = 'pause'
            if tm_type == 8: 
                timemarkerJ['type'] = 'timesig'
                timemarkerJ['numerator'] = FL_TimeMarkers[timemarker]['numerator']
                timemarkerJ['denominator'] = FL_TimeMarkers[timemarker]['denominator']
            if tm_type == 9: timemarkerJ['type'] = 'punchin'
            if tm_type == 10: timemarkerJ['type'] = 'punchout'
            timemarkersJ.append(timemarkerJ)

        rootJ['instrumentsorder'] = instrumentsorder
        rootJ['instruments'] = instrumentsJ
        rootJ['notelistindex'] = notelistindexJ
        rootJ['playlist'] = playlistJ
        rootJ['timemarkers'] = timemarkersJ

        return json.dumps(rootJ, indent=2)