# SPDX-FileCopyrightText: 2023 SatyrDiamond
# SPDX-License-Identifier: GPL-3.0-or-later  

import plugin_output
import json
import math
import base64
import struct
from bs4 import BeautifulSoup
from functions_plugin import flp_enc_plugins
from functions import data_values
from functions import xtramath

from objects import dv_datadef
from objects import dv_dataset

from objects_file import proj_flp
from objects_file._flp import channel
from objects_file._flp import arrangement
from objects_file._flp import fx

filename_len = {}

def decode_color(color):
    return int.from_bytes(bytes([int(color[0]*255), int(color[1]*255), int(color[2]*255)]), "little")

class output_cvpjs(plugin_output.base):
    def __init__(self): pass
    def is_dawvert_plugin(self): return 'output'
    def getshortname(self): return 'flp'
    def getname(self): return 'FL Studio'
    def gettype(self): return 'mi'
    def plugin_archs(self): return ['amd64', 'i386']
    def getdawinfo(self, dawinfo_obj): 
        dawinfo_obj.name = 'FL Studio'
        dawinfo_obj.file_ext = 'flp'
        dawinfo_obj.auto_types = ['pl_ticks']
        dawinfo_obj.track_lanes = True
        dawinfo_obj.placement_cut = True
        dawinfo_obj.fxtype = 'rack'
        dawinfo_obj.fxrack_params = ['enabled','vol','pan']
        dawinfo_obj.audio_stretch = ['rate']
        dawinfo_obj.audio_filetypes = ['wav','flac','ogg','mp3','wv','ds']
        dawinfo_obj.plugin_included = ['sampler:single','universal:arpeggiator','native-flstudio','soundfont2']
        dawinfo_obj.plugin_ext = ['vst2']
    def parse(self, convproj_obj, output_file):

        ppq = 96
        convproj_obj.change_timings(ppq, False)

        datadef = dv_datadef.datadef('./data_ddef/fl_studio.ddef')
        dataset = dv_dataset.dataset('./data_dset/fl_studio.dset')

        flp_obj = proj_flp.flp_project()
        flp_obj.ppq = ppq
        
        samplestretch = {}

        flp_obj.title = convproj_obj.metadata.name
        flp_obj.author = convproj_obj.metadata.author
        flp_obj.url = convproj_obj.metadata.genre
        flp_obj.genre = convproj_obj.metadata.url
        if convproj_obj.metadata.comment_datatype == 'html':
            bst = BeautifulSoup(convproj_obj.metadata.comment_text, "html.parser")
            flp_obj.comment = bst.get_text()
        if convproj_obj.metadata.comment_datatype == 'text': 
            flp_obj.comment = convproj_obj.metadata.comment_text
        flp_obj.comment = flp_obj.comment.replace("\r\n", "\r").replace("\n", "\r")

        if flp_obj.title or flp_obj.author or flp_obj.url or flp_obj.genre or flp_obj.comment:
            flp_obj.showinfo = 1

        flp_obj.tempo = convproj_obj.params.get('bpm',120).value

        flp_obj.numerator, flp_obj.denominator = convproj_obj.timesig
        flp_obj.mainpitch = struct.unpack('H', struct.pack('h', int(convproj_obj.params.get('pitch',0).value*100)))[0]
        flp_obj.shuffle = int(convproj_obj.params.get('shuffle',0).value*128)

        samples_id = {}
        g_inst_id = {}
        g_inst_id_count = 0

        for instentry in convproj_obj.instruments_order:
            g_inst_id[instentry] = g_inst_id_count
            g_inst_id_count += 1

        for sampleentry in convproj_obj.sample_index:
            g_inst_id[sampleentry] = g_inst_id_count
            samples_id[sampleentry] = g_inst_id_count
            g_inst_id_count += 1

        for inst_id, inst_obj in convproj_obj.iter_instrument():
            fl_channel_obj = channel.flp_channel()
            fl_channel_obj.basicparams.volume = inst_obj.params.get('vol',1).value**0.75
            fl_channel_obj.basicparams.pan = inst_obj.params.get('pan',0).value
            fl_channel_obj.enabled = int(inst_obj.params.get('enabled',True).value)
            fl_channel_obj.basicparams.pitch = inst_obj.params.get('pitch',0).value*100
            fl_channel_obj.params.main_pitch = int(inst_obj.params.get('usemasterpitch',True).value)
            middlenote = inst_obj.datavals.get('middlenote', 0)
            if middlenote != 0: fl_channel_obj.middlenote = middlenote+60
            fl_channel_obj.icon = 0

            fl_channel_obj.fxchannel = max(inst_obj.fxrack_channel, 0)

            if inst_obj.visual.name: fl_channel_obj.name = inst_obj.visual.name
            if inst_obj.visual.color: fl_channel_obj.color = decode_color(inst_obj.visual.color)

            fl_channel_obj.type = 0
            fl_channel_obj.plugin.name = ''

            plugin_found, plugin_obj = convproj_obj.get_plugin(inst_obj.pluginid)
            if plugin_found:
                if plugin_obj.check_match('sampler', 'single'):
                    fl_channel_obj.type = 0
                    fl_channel_obj.plugin.name = ''
                    fl_channel_obj.plugin.generator = True
                    fl_channel_obj.params.unkflag1 = 1
                    ref_found, sampleref_obj = plugin_obj.sampleref_fileref('sample', convproj_obj)
                    if ref_found: fl_channel_obj.samplefilename = sampleref_obj.fileref.get_path('win', True)

                fl_plugin, fl_pluginparams = flp_enc_plugins.setparams(convproj_obj, plugin_obj, datadef, dataset)
                if fl_plugin != None:
                    fl_channel_obj.type = 2
                    fl_channel_obj.plugin.name = fl_plugin
                    fl_channel_obj.plugin.params = fl_pluginparams
                    fl_channel_obj.params.unkflag1 = 1
                    fl_channel_obj.plugin.generator = True
                    windowdata_obj = convproj_obj.window_data_get(['plugin', inst_obj.pluginid])
                    if windowdata_obj.pos_x != -1: fl_channel_obj.plugin.window_p_x = windowdata_obj.pos_x
                    if windowdata_obj.pos_y != -1: fl_channel_obj.plugin.window_p_y = windowdata_obj.pos_y
                    if windowdata_obj.size_x != -1: fl_channel_obj.plugin.window_s_x = windowdata_obj.size_x
                    if windowdata_obj.size_y != -1: fl_channel_obj.plugin.window_s_y = windowdata_obj.size_y
                    if windowdata_obj.open != -1: fl_channel_obj.plugin.visible = windowdata_obj.open

                    if 'max' in plugin_obj.poly: 
                        fl_channel_obj.poly.max = plugin_obj.poly['max']
                    if 'mono' in plugin_obj.poly: 
                        if plugin_obj.poly['mono']: fl_channel_obj.poly.flags += 1
                    if 'porta' in plugin_obj.poly: 
                        if plugin_obj.poly['porta']: fl_channel_obj.poly.flags += 2

            for n in [100, 60]:
                t = channel.flp_channel_tracking()
                t.mid = n
                fl_channel_obj.tracking.append(t)
                        
            for n in range(5):
                t = channel.flp_env_lfo()

                if n == 1: t.envlfo_flags = 4

                fl_channel_obj.env_lfo.append(t)
                        
            flp_obj.channels[g_inst_id[inst_id]] = fl_channel_obj

        num_channels = len(flp_obj.channels)

        for samp_id, sre_obj in convproj_obj.iter_sampleindex():
            fl_channel_obj = channel.flp_channel()
            fl_channel_obj.type = 4

            ref_found, sampleref_obj = convproj_obj.get_sampleref(sre_obj.sampleref)
            fl_channel_obj.samplefilename = sampleref_obj.fileref.get_path('win', True) if ref_found else ""

            fl_channel_obj.basicparams.volume = sre_obj.vol
            fl_channel_obj.basicparams.pan = sre_obj.pan
            fl_channel_obj.enabled = sre_obj.enabled
            fl_channel_obj.fxchannel = max(sre_obj.fxrack_channel, 0)

            if sre_obj.visual.name: fl_channel_obj.name = sre_obj.visual.name
            if sre_obj.visual.color: fl_channel_obj.color = decode_color(sre_obj.visual.color)

            samplestretch[samp_id] = ['normal', 1]
            audiorate = 1

            if sre_obj.stretch.algorithm == 'resample': fl_channel_obj.params.stretchingmode = 0
            elif sre_obj.stretch.algorithm == 'elastique_v3': fl_channel_obj.params.stretchingmode = 1
            elif sre_obj.stretch.algorithm == 'elastique_v3_mono': fl_channel_obj.params.stretchingmode = 2
            elif sre_obj.stretch.algorithm == 'slice_stretch': fl_channel_obj.params.stretchingmode = 3
            elif sre_obj.stretch.algorithm == 'auto': fl_channel_obj.params.stretchingmode = 4
            elif sre_obj.stretch.algorithm == 'slice_map': fl_channel_obj.params.stretchingmode = 5
            elif sre_obj.stretch.algorithm == 'elastique_v2': fl_channel_obj.params.stretchingmode = 6
            elif sre_obj.stretch.algorithm == 'elastique_v2_transient': fl_channel_obj.params.stretchingmode = 7
            elif sre_obj.stretch.algorithm == 'elastique_v2_mono': fl_channel_obj.params.stretchingmode = 8
            elif sre_obj.stretch.algorithm == 'elastique_v2_speech': fl_channel_obj.params.stretchingmode = 9
            else: fl_channel_obj.params.stretchingmode = -1

            fl_channel_obj.params.stretchingpitch = int(sre_obj.pitch*100)

            if not sre_obj.stretch.uses_tempo: 
                fl_channel_obj.params.stretchingmultiplier = int(  math.log2(1/sre_obj.stretch.calc_real_speed)*10000)
            else: 
                fl_channel_obj.params.stretchingtime = int((sampleref_obj.dur_sec*384)/sre_obj.stretch.calc_tempo_speed)

            samplestretch[samp_id] = sre_obj.stretch.calc_tempo_speed

            flp_obj.channels[g_inst_id[samp_id]] = fl_channel_obj

        pat_id = {}
        pat_id_count = 1
        for nle_id, nle_obj in convproj_obj.iter_notelistindex():
            pat_id[nle_id] = pat_id_count
            pat_id_count += 1

        for pat_entry, pat_num in pat_id.items():
            fl_pattern_obj = proj_flp.flp_pattern()
            nle_obj = convproj_obj.notelist_index[pat_entry]

            if nle_obj.visual.name: fl_pattern_obj.name = nle_obj.visual.name
            if nle_obj.visual.color: fl_pattern_obj.color = decode_color(nle_obj.visual.color)

            nle_obj.notelist.notemod_conv()

            fl_notes = {}

            nle_obj.notelist.sort()
            for t_pos, t_dur, t_keys, t_vol, t_inst, t_extra, t_auto, t_slide in nle_obj.notelist.iter():
                for t_key in t_keys:
                    fl_note_obj = proj_flp.flp_note()
                    fl_note_obj.rack = g_inst_id[t_inst]
                    fl_note_obj.pos = int(t_pos)
                    fl_note_obj.dur = int(t_dur)
                    fl_note_obj.key = int(t_key)+60
                    fl_note_obj.velocity = int(xtramath.clamp(t_vol,0,1)*100)
                    if 'finepitch' in t_extra: fl_note_obj.finep = int((t_extra['finepitch']/10)+120)
                    if 'release' in t_extra: fl_note_obj.rel = int(xtramath.clamp(t_extra['release'],0,1)*128)
                    if 'cutoff' in t_extra: fl_note_obj.mod_x = int(xtramath.clamp(t_extra['cutoff'],0,1)*255)
                    if 'reso' in t_extra: fl_note_obj.mod_y = int(xtramath.clamp(t_extra['reso'],0,1)*255)
                    if 'pan' in t_extra: fl_note_obj.pan = int((xtramath.clamp(float(t_extra['pan']),-1,1)*64)+64)

                    if fl_note_obj.pos not in fl_notes: fl_notes[fl_note_obj.pos] = []
                    fl_notes[fl_note_obj.pos].append(fl_note_obj)

                    if t_slide:
                        for s_pos, s_dur, s_key, s_vol, s_extra in t_slide:
                            fl_note_obj = proj_flp.flp_note()
                            fl_note_obj.rack = g_inst_id[t_inst]
                            fl_note_obj.pos = int(t_pos + s_pos)
                            fl_note_obj.dur = int(s_dur)
                            fl_note_obj.key = int(s_key)+60
                            fl_note_obj.velocity = int(xtramath.clamp(s_vol,0,1)*100)
                            fl_note_obj.flags = 16392
                            if 'finepitch' in s_extra: fl_note_obj.finep = int((s_extra['finepitch']/10)+120)
                            if 'release' in s_extra: fl_note_obj.rel = int(xtramath.clamp(s_extra['release'],0,1)*128)
                            if 'cutoff' in s_extra: fl_note_obj.mod_x = int(xtramath.clamp(s_extra['cutoff'],0,1)*255)
                            if 'reso' in s_extra: fl_note_obj.mod_y = int(xtramath.clamp(s_extra['reso'],0,1)*255)
                            if 'pan' in s_extra: fl_note_obj.pan = int((xtramath.clamp(float(s_extra['pan']),-1,1)*64)+64)
                            if fl_note_obj.pos not in fl_notes: fl_notes[fl_note_obj.pos] = []
                            fl_notes[fl_note_obj.pos].append(fl_note_obj)
            
            for poslist in sorted(fl_notes):
                for fl_note in fl_notes[poslist]:
                    fl_pattern_obj.notes.append(fl_note)

            flp_obj.patterns[pat_num] = fl_pattern_obj


        if len(flp_obj.patterns) > 999:
            print('[error] FLP patterns over 999 is unsupported.')
            exit()

        if len(flp_obj.channels) > 256:
            print('[error] FLP channels over 256 is unsupported.')
            exit()

        FL_Playlist_BeforeSort = {}
        FL_Playlist_Sorted = {}
        FL_Playlist = []

        arrangement_obj = arrangement.flp_arrangement()

        for idnum, playlist_obj in convproj_obj.iter_playlist():

            idnum = int(idnum)+1

            for pl_obj in playlist_obj.placements.pl_notes_indexed:

                if pl_obj.fromindex in pat_id:
                    fl_clip_obj = arrangement.flp_arrangement_clip()
                    fl_clip_obj.position = int(pl_obj.position)
                    fl_clip_obj.itemindex = int(pat_id[pl_obj.fromindex] + fl_clip_obj.patternbase)
                    fl_clip_obj.length = int(pl_obj.duration)
                    fl_clip_obj.endoffset = int(pl_obj.duration)
                    fl_clip_obj.trackindex = (-500 + int(idnum))*-1
                    if pl_obj.muted == True: fl_clip_obj.flags = 12352

                    if pl_obj.cut_type == 'cut':
                        if 'start' in pl_obj.cut_data: 
                            fl_clip_obj.startoffset = int(pl_obj.cut_data['start'])
                            fl_clip_obj.endoffset += int(pl_obj.cut_data['start'])
                    if fl_clip_obj.position not in FL_Playlist_BeforeSort: FL_Playlist_BeforeSort[fl_clip_obj.position] = []
                    FL_Playlist_BeforeSort[fl_clip_obj.position].append(fl_clip_obj)


            for pl_obj in playlist_obj.placements.pl_audio_indexed:
                if pl_obj.fromindex in samples_id:
                    fl_clip_obj = arrangement.flp_arrangement_clip()
                    fl_clip_obj.position = int(pl_obj.position)
                    fl_clip_obj.itemindex = samples_id[pl_obj.fromindex]
                    fl_clip_obj.length = max(0, int(pl_obj.duration))
                    fl_clip_obj.endoffset = int(pl_obj.duration)/ppq
                    fl_clip_obj.trackindex = (-500 + int(idnum))*-1
                    if pl_obj.muted == True: fl_clip_obj.flags = 12352

                    startat = 0
                    if pl_obj.cut_type == 'cut': startat = pl_obj.cut_data['start']

                    if pl_obj.fromindex in samplestretch:
                        startat = startat/ppq
                        endat = startat+(pl_obj.duration/ppq)

                        stretchrate = samplestretch[pl_obj.fromindex]
                        #print(out_is_speed, out_rate, end=' | ')
                        #print(pl_obj.duration/ppq, end=' | ')
                        #print(startat*out_rate, end=' -S- ')
                        #print(startat, end=' | ')
                        #print(endat*out_rate, end=' -E- ')
                        #print(endat, end=' | ')
                        #print(placement_obj.duration/ppq, end=' | ')
                        #print()
                        fl_clip_obj.startoffset = (startat*stretchrate)*4
                        fl_clip_obj.endoffset = (endat*stretchrate)*4

                    #print(FL_playlistitem['startoffset'])
                    #print(FL_playlistitem['endoffset'])

                    #    if pl_stretch[0] == 'rate_tempo':
                    #        if 'start' in pl_obj.cut_data: 
                    #            FL_playlistitem['startoffset'] = pl_obj.cut_data['start']*pl_stretch[1]
                    #            FL_playlistitem['endoffset'] = pl_obj.duration*pl_stretch[1] + FL_playlistitem['startoffset']
                    #    elif pl_stretch[0] == 'rate_ignoretempo':
                    #        if 'start' in pl_obj.cut_data: 
                    #            FL_playlistitem['startoffset'] = pl_obj.cut_data['start']
                    #            FL_playlistitem['endoffset'] = pl_obj.duration + FL_playlistitem['startoffset']
                    #    elif pl_stretch[0] == 'rate_speed':
                    #        if 'start' in pl_obj.cut_data: 
                    #            FL_playlistitem['startoffset'] = (pl_obj.cut_data['start'])*pl_stretch[1]
                    #            FL_playlistitem['endoffset'] = (pl_obj.duration)*pl_stretch[1] + FL_playlistitem['startoffset']

                    #FL_playlistitem['startoffset'] /= (ppq/4)
                    #FL_playlistitem['endoffset'] /= (ppq/4)

                    if fl_clip_obj.position not in FL_Playlist_BeforeSort: FL_Playlist_BeforeSort[fl_clip_obj.position] = []
                    FL_Playlist_BeforeSort[fl_clip_obj.position].append(fl_clip_obj)

            if idnum not in arrangement_obj.tracks: 
                arrangement_obj.tracks[idnum] = arrangement.flp_track()
            if playlist_obj.visual.name: arrangement_obj.tracks[idnum].name = playlist_obj.visual.name
            if playlist_obj.visual.color: arrangement_obj.tracks[idnum].color = decode_color(playlist_obj.visual.color)
            arrangement_obj.tracks[idnum].height = playlist_obj.visual_ui.height
            arrangement_obj.tracks[idnum].enabled = int(playlist_obj.params.get('enabled',True).value)

        FL_Playlist_Sorted = dict(sorted(FL_Playlist_BeforeSort.items(), key=lambda item: item[0]))

        for itemposition in FL_Playlist_Sorted:
            playlistposvalues = FL_Playlist_Sorted[itemposition]
            for itemrow in playlistposvalues: arrangement_obj.items.append(itemrow)

        if convproj_obj.loop_active:
            flp_timemarker_obj = arrangement.flp_timemarker()
            flp_timemarker_obj.pos = convproj_obj.loop_start
            flp_timemarker_obj.type = 2
            arrangement_obj.timemarkers.append(flp_timemarker_obj)

        for pos, value in convproj_obj.timesig_auto.iter():
            flp_timemarker_obj = arrangement.flp_timemarker()
            flp_timemarker_obj.pos = pos
            flp_timemarker_obj.type = 8
            flp_timemarker_obj.name = str(value[0])+'/'+str(value[1])
            flp_timemarker_obj.numerator = value[0]
            flp_timemarker_obj.denominator = value[1]
            arrangement_obj.timemarkers.append(flp_timemarker_obj)

        for timemarker_obj in convproj_obj.timemarkers:
            flp_timemarker_obj = arrangement.flp_timemarker()
            flp_timemarker_obj.pos = timemarker_obj.position
            flp_timemarker_obj.type = 0
            flp_timemarker_obj.name = timemarker_obj.visual.name if timemarker_obj.visual.name else ""
            if timemarker_obj.type == 'start': flp_timemarker_obj.type = 5
            elif timemarker_obj.type == 'loop': flp_timemarker_obj.type = 4
            elif timemarker_obj.type == 'markerloop': flp_timemarker_obj.type = 1
            elif timemarker_obj.type == 'markerskip': flp_timemarker_obj.type = 2
            elif timemarker_obj.type == 'pause': flp_timemarker_obj.type = 3
            elif timemarker_obj.type == 'punchin': flp_timemarker_obj.type = 9
            elif timemarker_obj.type == 'punchout': flp_timemarker_obj.type = 10
            arrangement_obj.timemarkers.append(flp_timemarker_obj)

        flp_obj.arrangements[0] = arrangement_obj

        flp_obj.initfxvals.initvals['main/vol'] = int(convproj_obj.params.get('vol',1).value*12800)
        for fxnum in range(126):
            for slotnum in range(10):
                fxstxt = 'fx/'+str(fxnum)+'/slot/'+str(slotnum)+'/'
                flp_obj.initfxvals.initvals[fxstxt+'on'] = 1
                flp_obj.initfxvals.initvals[fxstxt+'wet'] = 12800

            fxptxt = 'fx/'+str(fxnum)+'/param/'
            flp_obj.initfxvals.initvals[fxptxt+'vol'] = 12800
            flp_obj.initfxvals.initvals[fxptxt+'pan'] = 0
            flp_obj.initfxvals.initvals[fxptxt+'stereo_sep'] = 0
            flp_obj.initfxvals.initvals[fxptxt+'eq1_level'] = 0
            flp_obj.initfxvals.initvals[fxptxt+'eq2_level'] = 0
            flp_obj.initfxvals.initvals[fxptxt+'eq3_level'] = 0
            flp_obj.initfxvals.initvals[fxptxt+'eq1_freq'] = 5777
            flp_obj.initfxvals.initvals[fxptxt+'eq2_freq'] = 33145
            flp_obj.initfxvals.initvals[fxptxt+'eq3_freq'] = 55825
            flp_obj.initfxvals.initvals[fxptxt+'eq1_width'] = 17500
            flp_obj.initfxvals.initvals[fxptxt+'eq2_width'] = 17500
            flp_obj.initfxvals.initvals[fxptxt+'eq3_width'] = 17500

        for fx_num, fxchannel_obj in convproj_obj.fxrack.items():

            fl_fxchan = flp_obj.mixer[fx_num]
            if fxchannel_obj.visual.name: fl_fxchan.name = fxchannel_obj.visual.name
            if fxchannel_obj.visual.color: fl_fxchan.color = decode_color(fxchannel_obj.visual.color)
 
            if 'docked' in fxchannel_obj.visual_ui.other:
                dockedpos = fxchannel_obj.visual_ui.other['docked']
                if dockedpos == 1: fl_fxchan.docked_center, fl_fxchan.docked_pos = False, True
                if dockedpos == 0: fl_fxchan.docked_center, fl_fxchan.docked_pos = True, False
                if dockedpos == -1: fl_fxchan.docked_center, fl_fxchan.docked_pos = False, False
            else:
                if fx_num == 0: fl_fxchan.docked_center, fl_fxchan.docked_pos = False, False

            fxptxt = 'fx/'+str(fx_num)+'/param/'
            flp_obj.initfxvals.initvals[fxptxt+'vol'] = int(12800*fxchannel_obj.params.get('vol', 1.0).value)
            flp_obj.initfxvals.initvals[fxptxt+'pan'] = int(6400*fxchannel_obj.params.get('pan', 0).value)
            
            if fxchannel_obj.sends.to_master_active:
                master_send_obj = fxchannel_obj.sends.to_master
                fl_fxchan.routing.append(0)
                flp_obj.initfxvals.initvals['fx/'+str(fx_num)+'/route/0'] = int(master_send_obj.params.get('amount', 1).value*12800)

            if fxchannel_obj.sends.check():
                for target, send_obj in fxchannel_obj.sends.iter():
                    fl_fxchan.routing.append(target)
                    flp_obj.initfxvals.initvals['fx/'+str(fx_num)+'/route/'+str(target)] = int(send_obj.params.get('amount', 1).value*12800)
            elif 0 < fx_num < 100:
                fl_fxchan.routing.append(0)
                flp_obj.initfxvals.initvals['fx/'+str(fx_num)+'/route/0'] = 12800


            if fx_num == 0: fxchannel_obj.outchannum = 1

            slotnum = 0
            for pluginid in fxchannel_obj.fxslots_audio:
                plugin_found, plugin_obj = convproj_obj.get_plugin(pluginid)
                if plugin_found: 
                    fl_plugin, fl_pluginparams = flp_enc_plugins.setparams(convproj_obj, plugin_obj, datadef, dataset)
                    if fl_plugin != None:
                        slotdata = fx.flp_fxslot(fx_num)
                        slotdata.plugin.name = fl_plugin
                        slotdata.plugin.params = fl_pluginparams
                        slotdata.plugin.slotnum = slotnum
                        if plugin_obj.visual.name: slotdata.name = plugin_obj.visual.name
                        if plugin_obj.visual.color: slotdata.color = decode_color(plugin_obj.visual.color)
                        fl_fxchan.slots[slotnum] = slotdata
                        fxstxt = 'fx/'+str(fx_num)+'/slot/'+str(slotnum)+'/'
                        fx_on, fx_wet = plugin_obj.fxdata_get()
                        flp_obj.initfxvals.initvals[fxstxt+'on'] = int(fx_on)
                        flp_obj.initfxvals.initvals[fxstxt+'wet'] = int(fx_wet*12800)
                        slotnum += 1
                        if slotnum == 10: break

        flp_obj.make(output_file)