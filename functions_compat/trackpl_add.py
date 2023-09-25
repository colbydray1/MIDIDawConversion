# SPDX-FileCopyrightText: 2023 SatyrDiamond
# SPDX-License-Identifier: GPL-3.0-or-later

from functions_compat import timesigblocks
from functions_compat import split_single_notelist

def process_r(projJ):
    timesigposs, tsblocks = timesigblocks.create_points_cut(projJ)
    split_single_notelist.add_timesigblocks(tsblocks)

    if 'do_singlenotelistcut' in projJ:
        if projJ['do_singlenotelistcut'] == True:
            track_placements = projJ['track_placements']
            for trackid in track_placements:
                islaned = False
                if 'laned' in track_placements[trackid]:
                    if track_placements[trackid]['laned'] == 1:
                        islaned = True
                if islaned == False:
                    if 'notes' in track_placements[trackid]:
                        placementdata = track_placements[trackid]['notes']
                        if len(placementdata) == 1:
                            split_single_notelist.add_notelist([False, trackid], placementdata[0]['notelist'])
                            #print('[compat] singlenotelist2placements: non-laned: splitted "'+trackid+'" to '+str(len(track_placements[trackid]['notes'])) + ' placements.')
                else:
                    for s_lanedata in track_placements[trackid]['lanedata']:
                        placementdata = track_placements[trackid]['lanedata'][s_lanedata]['notes']
                        if len(placementdata) == 1:
                            split_single_notelist.add_notelist([True, trackid, s_lanedata], placementdata[0]['notelist'])
                            #print('[compat] singlenotelist2placements: laned: splitted "'+trackid+'" from lane "'+str(s_lanedata)+'" to '+str(len(track_placements[trackid]['lanedata'][s_lanedata]['notes'])) + ' placements.')

    for inid, out_placements in split_single_notelist.get_notelist():
        if inid[0] == False: track_placements[inid[1]]['notes'] = out_placements
        if inid[0] == True: track_placements[inid[1]]['lanedata'][inid[2]]['notes'] = out_placements

    projJ['do_singlenotelistcut'] = False