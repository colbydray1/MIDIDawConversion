# SPDX-FileCopyrightText: 2023 SatyrDiamond
# SPDX-License-Identifier: GPL-3.0-or-later

import plugin_plugconv

from functions import plugin_vst2
from functions import plugins
from functions_plugparams import data_vc2xml
import json
import struct
import xml.etree.ElementTree as ET

def getparam(paramname):
    global pluginid_g
    global cvpj_l_g
    paramval = plugins.get_plug_param(cvpj_l_g, pluginid_g, paramname, 0)
    return paramval[0]

def opnplug_addvalue(opnplug_params, name, value):
    temp_xml = ET.SubElement(opnplug_params, 'VALUE')
    temp_xml.set('name', str(name))
    temp_xml.set('val', str(value))

def opnplug_addbank(opnplug_params, num, name):
    bank_xml = ET.SubElement(opnplug_params, 'bank')
    opnplug_addvalue(bank_xml, 'bank', num)
    opnplug_addvalue(bank_xml, 'name', name)

opadltxt = ['m1', 'c1', 'm2', 'c2']

class plugconv(plugin_plugconv.base):
    def __init__(self): pass
    def is_dawvert_plugin(self): return 'plugconv'
    def getplugconvinfo(self): return ['fm', 'opl3', None], ['vst2', None, None], True, False
    def convert(self, cvpj_l, pluginid, plugintype, extra_json):
        print('[plug-conv] Converting OPL2 to ADLplug:',pluginid)
        global pluginid_g   
        global cvpj_l_g 
        pluginid_g = pluginid   
        cvpj_l_g = cvpj_l
    
        adlplug_root = ET.Element("ADLMIDI-state")  
        opnplug_addbank(adlplug_root, 1, 'DawVert') 
        opnplug_addbank(adlplug_root, 0, 'DawVert') 
        opnplug_params = ET.SubElement(adlplug_root, 'instrument')  
        opnplug_addvalue(opnplug_params, "four_op" ,1)  
        opnplug_addvalue(opnplug_params, "pseudo_four_op" ,0)   
        opnplug_addvalue(opnplug_params, "blank" ,0)    
        opnplug_addvalue(opnplug_params, "con12" ,getparam('con_12'))
        opnplug_addvalue(opnplug_params, "con34" ,getparam('con_34'))
        opnplug_addvalue(opnplug_params, "note_offset1" ,0) 
        opnplug_addvalue(opnplug_params, "note_offset2" ,0) 
        opnplug_addvalue(opnplug_params, "fb12" ,getparam('feedback_12'))
        opnplug_addvalue(opnplug_params, "fb34" ,getparam('feedback_34'))
        opnplug_addvalue(opnplug_params, "midi_velocity_offset" ,0) 
        opnplug_addvalue(opnplug_params, "second_voice_detune" ,0)  
        opnplug_addvalue(opnplug_params, "percussion_key_number" ,0)
    
        for opnplugopname, cvpjopname in [['m1', 'op1'], ['c1', 'op2'], ['m2', 'op3'], ['c2', 'op4']]:  
            opnplug_addvalue(opnplug_params, opnplugopname+"attack" ,(getparam(cvpjopname+"_env_attack")*-1)+15)    
            opnplug_addvalue(opnplug_params, opnplugopname+"decay" ,(getparam(cvpjopname+"_env_decay")*-1)+15)  
            opnplug_addvalue(opnplug_params, opnplugopname+"sustain" ,(getparam(cvpjopname+"_env_sustain")*-1)+15)
            opnplug_addvalue(opnplug_params, opnplugopname+"release" ,(getparam(cvpjopname+"_env_release")*-1)+15)  
            opnplug_addvalue(opnplug_params, opnplugopname+"level" ,(getparam(cvpjopname+"_level")*-1)+63)  
            opnplug_addvalue(opnplug_params, opnplugopname+"ksl" ,getparam(cvpjopname+"_ksl"))
            opnplug_addvalue(opnplug_params, opnplugopname+"fmul" ,getparam(cvpjopname+"_freqmul")) 
            opnplug_addvalue(opnplug_params, opnplugopname+"trem" ,getparam(cvpjopname+"_tremolo")) 
            opnplug_addvalue(opnplug_params, opnplugopname+"vib" ,getparam(cvpjopname+"_vibrato"))  
            opnplug_addvalue(opnplug_params, opnplugopname+"sus" ,getparam(cvpjopname+"_sustained"))
            opnplug_addvalue(opnplug_params, opnplugopname+"env" ,getparam(cvpjopname+"_ksr"))
            opnplug_addvalue(opnplug_params, opnplugopname+"wave" ,getparam(cvpjopname+"_waveform"))
    
        opnplug_addvalue(opnplug_params, "delay_off_ms" ,160)   
        opnplug_addvalue(opnplug_params, "delay_on_ms" ,386)    
        opnplug_addvalue(opnplug_params, "bank" ,0) 
        opnplug_addvalue(opnplug_params, "program" ,0)  
        opnplug_addvalue(opnplug_params, "name" ,'')
    
        opnplug_selection = ET.SubElement(adlplug_root, 'selection')    
        opnplug_addvalue(opnplug_selection, "part" ,0)  
        opnplug_addvalue(opnplug_selection, "bank" ,0)  
        opnplug_addvalue(opnplug_selection, "program" ,0)
    
        opnplug_chip = ET.SubElement(adlplug_root, 'chip')  
        opnplug_addvalue(opnplug_chip, "emulator" ,2)   
        opnplug_addvalue(opnplug_chip, "chip_count" ,2) 
        opnplug_addvalue(opnplug_chip, "4op_count" ,1)
    
        opnplug_global = ET.SubElement(adlplug_root, 'global')  
        opnplug_addvalue(opnplug_global, "volume_model" ,0) 
        opnplug_addvalue(opnplug_global, "deep_tremolo" ,getparam("tremolo_depth")) 
        opnplug_addvalue(opnplug_global, "deep_vibrato" ,getparam("vibrato_depth"))
    
        opnplug_common = ET.SubElement(adlplug_root, 'common')  
        opnplug_addvalue(opnplug_common, "bank_title" ,'DawVert')   
        opnplug_addvalue(opnplug_common, "part" ,0) 
        opnplug_addvalue(opnplug_common, "master_volume" ,1.0)
    
        outfile = ET.ElementTree(adlplug_root)
    
        plugin_vst2.replace_data(cvpj_l, pluginid, 'name','any', 'ADLplug', 'chunk', data_vc2xml.make(adlplug_root), None)
    
        plugins.add_plug_data(cvpj_l, pluginid, 'middlenotefix', -12)   
        return True