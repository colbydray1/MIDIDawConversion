# SPDX-FileCopyrightText: 2024 SatyrDiamond
# SPDX-License-Identifier: GPL-3.0-or-later

import os
import plugins
from functions import extpluglog

class plugconv(plugins.base):
	def __init__(self): pass
	def is_dawvert_plugin(self): return 'plugconv'
	def getplugconvinfo(self, plugconv_obj): 
		plugconv_obj.in_plugins = [['native-jummbox', None]]
		plugconv_obj.in_daws = ['jummbox']
		plugconv_obj.out_plugins = [['native-lmms', None]]
		plugconv_obj.out_daws = ['lmms']
	def convert(self, convproj_obj, plugin_obj, pluginid, dv_config):
		if plugin_obj.type.subtype in ['custom chip', 'chip', 'harmonics']:
			extpluglog.convinternal('Beepbox', plugin_obj.type.subtype, 'LMMS', 'TripleOscillator')

			samplefolder = dv_config.path_samples_generated

			os.makedirs(samplefolder, exist_ok=True)
			wave_path = os.path.join(samplefolder, pluginid+'_wave.wav')

			if plugin_obj.type.subtype in ['custom chip', 'chip']: plugin_obj.wave_get('chipwave').to_audio(wave_path)
			if plugin_obj.type.subtype in ['harmonics']: plugin_obj.harmonics_get('harmonics').to_audio(wave_path)

			plugin_obj.replace('native-lmms', 'tripleoscillator')
			convproj_obj.add_sampleref(pluginid+'_wave', wave_path)

			sampleid = pluginid+'_wave'
			sp_obj = plugin_obj.samplepart_add('userwavefile0')
			sp_obj.sampleref = sampleid
			sp_obj = plugin_obj.samplepart_add('userwavefile1')
			sp_obj.sampleref = sampleid
			sp_obj = plugin_obj.samplepart_add('userwavefile2')
			sp_obj.sampleref = sampleid

			plugin_obj.params.add('vol0', 15, 'int')
			plugin_obj.params.add('vol1', 0, 'int')
			plugin_obj.params.add('vol2', 0, 'int')
			plugin_obj.params.add('wavetype0', 7, 'int')
			plugin_obj.params.add('wavetype1', 7, 'int')
			plugin_obj.params.add('wavetype2', 7, 'int')
			plugin_obj.params.add('coarse0', -12, 'int')
			plugin_obj.params.add('coarse1', -12, 'int')
			plugin_obj.params.add('coarse2', -12, 'int')
			return 0
		else: 
			return 2