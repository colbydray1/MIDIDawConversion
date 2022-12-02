# SPDX-FileCopyrightText: 2022 Colby Ray
# SPDX-License-Identifier: GPL-3.0-or-later

import json
import argparse
from plugin_input import base as base_input
from plugin_output import base as base_output
from functions import song_convert
from functions import plugin_convert

print('DawVert: Daw Conversion Tool')

parser = argparse.ArgumentParser()
parser.add_argument("-i", default=None)
parser.add_argument("-it", default=None)
parser.add_argument("-o", default=None)
parser.add_argument("-ot", default=None)
args = parser.parse_args()

in_file = args.i
out_file = args.o
in_format = args.it
out_format = args.ot

typelist = {}
typelist['r'] = 'Regular'
typelist['ri'] = 'RegularIndexed'
typelist['a'] = 'AnyPurpose'
typelist['m'] = 'Multiple'
typelist['mi'] = 'MultipleIndexed'
typelist['debug'] = 'debug'

extra_json = {}

# --------- Input Plugin: Get List
pluglist_input = {}
pluglist_input_auto = {}
print('  input plugins: ',end='')
for inputplugin in base_input.plugins:
	in_class_list = inputplugin()
	shortname = in_class_list.getshortname()
	pluglist_input[shortname] = in_class_list
	if in_class_list.supported_autodetect() == True:
		pluglist_input_auto[shortname] = in_class_list
		print(shortname,end='[a] ')
	else:
		print(shortname,end=' ')
print('')

# --------- Output Plugin: Get List
pluglist_output = {}
print('  output plugins: ',end='')
for outputplugin in base_output.plugins:
	out_class_list = outputplugin()
	shortname = out_class_list.getshortname()
	pluglist_output[shortname] = out_class_list
	print(shortname,end=' ')
print('')

if in_file == None: print('[error] An input file must be specified'); exit()
if out_file == None: print('[error] An output file must be specified'); exit()
if out_format == None: print('[error] An output format must be specified'); exit()

detected_format = False
detect_done = False

# --------- Input Format
if in_format == None:
	for autoplugin in pluglist_input_auto:
		temp_in_class = pluglist_input_auto[autoplugin]
		detected_format = temp_in_class.detect(in_file)
		if detected_format == True:
			in_class = temp_in_class
			in_name = in_class.getname()
			in_shortname = in_class.getshortname()
			in_format = in_shortname
			print('[info] Detected input format:',in_name,'('+ str(in_shortname)+')')
			break
	detect_done = True

if in_format == None:
	if detect_done == True:
		print('[error] could not identify the input format')
		exit()
else:
	if in_format in pluglist_input:
		in_class = pluglist_input[in_format]
	else:
		print('[error] input format plugin not found')
		exit()

# --------- Output Format
if out_format in pluglist_output:
	out_class = pluglist_output[out_format]
else:
	print('[error] output format plugin not found')
	exit()

# --------- Parse to List
in_type = in_class.gettype()
out_type = out_class.gettype()

# --------- Info
print('Input:',in_format, in_type)
print('Output:',out_format, out_type)

if in_type == out_type: print('[info] ' + typelist[in_type] + ' > ' + typelist[out_type])
elif out_type == 'debug': print('[info] ' + typelist[in_type] + ' > ' + typelist[out_type])
elif in_type == 'm' and out_type == 'mi': print('[info] ' + typelist[in_type] + ' > ' + typelist[out_type])
elif in_type == 'r' and out_type == 'm': print('[info] ' + typelist[in_type] + ' > ' + typelist[out_type])
elif in_type == 'r' and out_type == 'mi': print('[info] ' + typelist[in_type] + ' > ' + typelist[out_type])
elif in_type == 'mi' and out_type == 'm': print('[info] ' + typelist[in_type] + ' > ' + typelist[out_type])
elif in_type == 'm' and out_type == 'r': print('[info] ' + typelist[in_type] + ' > ' + typelist[out_type])
elif in_type == 'mi' and out_type == 'r': print('[info] ' + typelist[in_type] + ' > ' + typelist[out_type])
else:
	print('[info] type Conversion from ' + typelist[in_type] + ' to ' + typelist[out_type] + ' not supported.')
	exit()

# --------- Parse to List
CVPJ_j = in_class.parse(in_file, {})
if CVPJ_j == '{}' or CVPJ_j == None:
	print('[error] Input Plugin outputted no json')
	exit()

# --------- Plugins

CVPJ_C = plugin_convert.convproj(CVPJ_j, in_type, out_type, out_format)
if CVPJ_C != None: CVPJ_j = CVPJ_C


# --------- Convert Type -- mi <> m <> r

print('[info] ' + typelist[in_type] + ' > ' + typelist[out_type])
if in_type == 'm' and out_type == 'mi': 
	CVPJ_j = song_convert.m2mi(CVPJ_j)
if in_type == 'm' and out_type == 'r': 
	CVPJ_j = song_convert.m2r(CVPJ_j)

if in_type == 'r' and out_type == 'm': 
	CVPJ_j = song_convert.r2m(CVPJ_j)
if in_type == 'r' and out_type == 'mi': 
	CVPJ_j = song_convert.r2m(CVPJ_j)
	CVPJ_j = song_convert.m2mi(CVPJ_j)

if in_type == 'mi' and out_type == 'm': 
	CVPJ_j = song_convert.mi2m(CVPJ_j)
if in_type == 'mi' and out_type == 'r': 
	CVPJ_j = song_convert.mi2m(CVPJ_j)
	CVPJ_j = song_convert.m2r(CVPJ_j)

# --------- Output

out_class.parse(CVPJ_j, out_file)
