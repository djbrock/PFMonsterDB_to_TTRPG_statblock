"""_summary_
    Parse Pathfinder 1e monster information from the database created by
    https://github.com/c0d3rman/PathfinderMonsterDatabase and output
    in a form suitable for use with Obsidian fantasy-statblocks plugin.
    https://github.com/valentine195/fantasy-statblocks
    
    Copyright 2023 David J. Brockley

Permission is hereby granted, free of charge, to any person obtaining a copy of 
this software and associated documentation files (the “Software”), to deal in the 
Software without restriction, including without limitation the rights to use, copy, 
modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, 
and to permit persons to whom the Software is furnished to do so, subject to the 
following conditions:

The above copyright notice and this permission notice shall be included in all 
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, 
INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A 
PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT 
HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF 
CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE 
OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

"""
import ruyaml
#ruamel.yaml.scalarstring.DoubleQuotedScalarString('hello world')
# This isn't properly quoting some special abilities, leading to the monsters not rendering
# I may need to build the output as a dict and then dump it as YAML.

# TODO
# Align tagging with TTRPG convention
# Simplify YAML to match example and use new format
# Document
# Restructure to eliminate copy-paste coding
# Restructure to have functions that create output for specific fantasy-stablock elements?

import argparse
import sys
import json
from copy import deepcopy
import regex as re
from pathlib import Path
import os

def to_desc(txt, file):
    s=str(txt).encode('unicode_escape').decode('ASCII')
    print('    desc:', '"'+s+'"', file=file)


def wq(s):
    return '"' + s + '"'


def write_monster(monster_in, filename=None, source_dict=None, keys_used=None, url=None):
    """Write monster information in dict to supplied file or stdout.

    Args:
        monster_in (dict): Dictionary containing monster info
        filename (str, optional): Filename to write to. Defaults to None.
        keys_used (dict, optional): Dictionary to collect keys accessed for checking. Defaults to None.
        url (str, optional): URL on Archive of Nethys monster info was collected from. Defaults to None.
    """
    if filename is None:
        write_monster_to_file(monster_in, sys.stdout)
    else:
        try:
            with open(filename, 'x') as f:
                write_monster_to_file(monster_in, f, source_dict=source_dict, keys_used=keys_used, url=url)
        except FileExistsError:
            print('ERROR: file', filename, 'already exists while processing key', url)


def write_monster_to_file(monster_in, f, source_dict=None, keys_used=None, url=None):
    """Write monster information in dict to supplied file.

    Args:
        monster_in (dict): Dictionary containing monster info
        f (filehandle): File to write to
        keys_used (dict, optional): Dictionary to collect keys accessed for checking. Defaults to None.
        url (str, optional): URL on Archive of Nethys monster info was collected from. Defaults to None.
    """
    monster_name = monster_in['title2']
    if keys_used is not None: keys_used['title2'] = True

    print('---', file=f)
    
    print('statblock: inline', file=f)
    print('tags: monster', file=f)

    print('name:', monster_name, file=f)
    print('---', file=f)

    print('```statblock', file=f)
    #print('layout: Pathfinder 1e EN Layout Mod', file=f)
    print('layout: Basic Pathfinder 1e Layout', file=f)
    source = monster_in['sources'][0]['name']
    source_dict[source] = True
    if source[8:] == 'Bestiary':
        source = 'Pathfinder RPG ' + source
    if '#' in source:
        source = source.replace('#', 'No. ')
    print('source: ', '"' + source + '"', file = f)
    
    if keys_used is not None: keys_used['CR'] = True
    print('Monster_CR:', monster_in['CR'], file=f)

    if keys_used is not None: keys_used['title1'] = True
    print('name:', monster_name, file=f)

    if keys_used is not None: keys_used['XP'] = True
    print('Monster_XP:', monster_in['XP'], file=f)

    if keys_used is not None: keys_used['race'] = True
    if 'race' in monster_in:
        print('race:', monster_in['race'], file=f)

    if keys_used is not None: keys_used['classes'] = True
    if 'classes' in monster_in:
        print('class:', wq(', '.join(monster_in['classes'])), file=f)

    if keys_used is not None: keys_used['alignment'] = True
    print('alignment:', monster_in['alignment'], file=f)

    if keys_used is not None: keys_used['size'] = True
    print('size:', monster_in['size'], file=f)

    if keys_used is not None: keys_used['type'] = True
    print('type:', monster_in['type'], file=f)

    if keys_used is not None: keys_used['subtypes'] = True
    if 'subtypes' in monster_in: 
        print('subtype: ' + wq('(' + ', '.join(monster_in['subtypes']) + ')'), file=f)

    # this can be a list
    if keys_used is not None: keys_used['initiative'] = True
    if isinstance(monster_in['initiative']['bonus'], int):
        print('INI:', '{0:+}'.format(monster_in['initiative']['bonus']), file=f)
    elif 'ability' in monster_in['initiative']:
        print('INI:', '/'.join(['{0:+}'.format(i) for i in monster_in['initiative']['bonus']]) + '; ', monster_in['initiative']['ability'], file=f)
    else:
        print('INI:', '/'.join(['{0:+}'.format(i) for i in monster_in['initiative']['bonus']]), file=f)

    if 'Perception' in monster_in['skills']:
        print('perception:', '{0:+}'.format(monster_in['skills']['Perception']['_']), file=f)

    if keys_used is not None: keys_used['senses'] = True
    if 'senses' in monster_in:
        senses = []
        for key in monster_in['senses']:
            if isinstance(type(monster_in['senses'][key]), int):
                senses.append(key + ' ' + str(monster_in['senses'][key]))
            else:
                senses.append(key)
        print('senses:', wq(', '.join(senses)), file=f)

    if keys_used is not None: keys_used['auras'] = True
    if 'auras' in monster_in:
        aura = []
        for a in monster_in['auras']:
            aura.append(a['name'])
        print('aura:', wq(', '.join(aura)), file=f)

    if keys_used is not None: keys_used['AC'] = True
    ac = str(monster_in['AC']['AC']) + ', touch ' + str(monster_in['AC']['touch']) + ', flat-footed ' + str(monster_in['AC']['flat_footed'])
    if 'components' in monster_in['AC']:
        ac_bonuses = []
        at_end = ""
        for key in monster_in['AC']['components']:
            if isinstance(monster_in['AC']['components'][key], int):
                ac_bonuses.append(key + ' ' + '{0:+}'.format(monster_in['AC']['components'][key]))
            else:
                at_end = at_end + '; ' + ', '.join(monster_in['AC']['components'][key])
        ac = ac + ' (' + ', '.join(ac_bonuses) + at_end + ')'
    print('AC:', wq(ac), file=f)

    if keys_used is not None: keys_used['HP'] = True
    hp_special = []
    for key in monster_in['HP']:
        if key != 'HP' and key != 'long':
            hp_special.append( key.replace('_', ' ') + ' ' + str(monster_in['HP'][key]))
    print('HP:', str(monster_in['HP']['HP']), file=f)
    print('HP_extra:', wq('; '.join(hp_special)), file=f)

    if keys_used is not None: keys_used['HD'] = True
    print('HD:', monster_in['HP']['long'], file=f)

    if keys_used is not None: keys_used['saves'] = True
    print('saves:', wq('Fort ' + '{0:+}'.format(monster_in['saves']['fort']) + ', Ref ' + '{0:+}'.format(monster_in['saves']['ref']) + 
        ', Will ' + '{0:+}'.format(monster_in['saves']['will'])), file=f)
    if 'other' in monster_in['saves']:
        print('saves_other:', wq(monster_in['saves']['other']), file=f)
        
    if keys_used is not None: keys_used['immunities'] = True
    if 'immunities' in monster_in:
        print('immune:', wq(', '.join(monster_in['immunities'])), file=f)

    if keys_used is not None: keys_used['resistances'] = True
    if 'resistances' in monster_in:
        resist = []
        for key in monster_in['resistances']:
            resist.append(key + ' ' + str(monster_in['resistances'][key]))
        print('resist:', wq(', '.join(resist)), file=f)
    
    if keys_used is not None: keys_used['DR'] = True
    if 'DR' in monster_in:
        dr = []
        for dr_source in monster_in['DR']:
            dr.append(str(dr_source['amount']) + '/' + dr_source['weakness'])
        print('DR:', wq(', '.join(dr)), file=f)
    
    if 'defensive_abilities' in monster_in:
        if keys_used is not None: keys_used['defensive_abilities'] = True
        print('defensive_abilities:', wq(', '.join(monster_in['defensive_abilities'])), file=f)

    if keys_used is not None: keys_used['SR'] = True
    if 'SR' in monster_in:
        print('SR:', monster_in['SR'], file=f)

    if keys_used is not None: keys_used['weaknesses'] = True
    if 'weaknesses' in monster_in:
        print('weak:', wq(', '.join(monster_in['weaknesses'])), file=f)

    if keys_used is not None: keys_used['speeds'] = True
    speed = []
    if 'base' in monster_in['speeds']:
        speed = [str(monster_in['speeds']['base']) + ' ft.']
    if 'fly' in monster_in['speeds']:
        if 'fly_maneuverability' in monster_in['speeds']:
            speed.append( 'fly ' + str(monster_in['speeds']['fly']) + ' ft. (' + monster_in['speeds']['fly_maneuverability'] + ')')
        elif 'fly_other' in monster_in['speeds']:
            speed.append( 'fly ' + str(monster_in['speeds']['fly']) + ' ft. (' + monster_in['speeds']['fly_other'] + ')')
        else:
            speed.append( 'fly ' + str(monster_in['speeds']['fly']) + ' ft.')
    for key in monster_in['speeds']:
        if key == 'base': continue
        if key == 'fly': continue
        if key == 'fly_maneuverability': continue
        if key == 'base_other':
            speed.append(' ' + str(monster_in['speeds'][key]))
        else:
            speed.append(key + ' ' + str(monster_in['speeds'][key]) + ' ft.')
    print( 'speed:', wq(', '.join(speed)), file=f)

    if keys_used is not None: keys_used['attacks'] = True
    if 'attacks' in monster_in and 'melee' in monster_in['attacks']:
        melee = []
        for m in monster_in['attacks']['melee'][0]:
            melee.append(m['text'])
        print('melee:', wq(', '.join(melee)), file=f)
    if 'attacks' in monster_in and 'ranged' in monster_in['attacks']:
        ranged = []
        for r in monster_in['attacks']['ranged'][0]:
            ranged.append(r['text'])
        print('ranged:', wq(', '.join(ranged)), file=f)
    if 'attacks' in monster_in and 'special' in monster_in['attacks']:
        print('special_attacks:', wq(', '.join(monster_in['attacks']['special'])), file=f)

    if keys_used is not None: keys_used['space'] = True
    if 'space' in monster_in:
        print('space:', monster_in['space'], 'ft.', file=f)

    if keys_used is not None: keys_used['reach'] = True
    if 'reach' in monster_in:
        reach_other = ""
        if 'reach_other' in monster_in:
            if keys_used is not None: keys_used['reach_other'] = True
            reach_other = monster_in['reach_other']
            print('reach:', monster_in['reach'], 'ft. (' + reach_other + ')', file=f)
        else:
            print('reach:', monster_in['reach'], 'ft.', file=f)

    if keys_used is not None: keys_used['tactics'] = True
    if 'tactics' in monster_in:
        print('tactics:', file=f)
        for k in monster_in['tactics']:
            print('  - name:', k, file=f)
            to_desc( monster_in['tactics'][k], f)

    if keys_used is not None: keys_used['ability_scores'] = True
    stats = [str(monster_in['ability_scores']['STR']),
            str(monster_in['ability_scores']['DEX']),
            str(monster_in['ability_scores']['CON']),
            str(monster_in['ability_scores']['INT']),
            str(monster_in['ability_scores']['WIS']),
            str(monster_in['ability_scores']['CHA'])]
    print('pf1e_stats:', '[' + ', '.join(stats) + ']', file=f)

    if keys_used is not None: keys_used['BAB'] = True
    print('BAB:', monster_in['BAB'], file=f)

    if keys_used is not None: keys_used['CMB_other'] = True
    if keys_used is not None: keys_used['CMB'] = True
    if 'CMB_other' in monster_in:
        print('CMB:', monster_in['CMB'], '(' + monster_in['CMB_other'] + ')', file=f)
    else:
        print('CMB:', monster_in['CMB'], file=f)

    if keys_used is not None: keys_used['CMD_other'] = True
    if keys_used is not None: keys_used['CMD'] = True
    if 'CMD_other' in monster_in:
        print('CMD:', monster_in['CMD'], '(' + monster_in['CMD_other'] + ')', file=f)
    else:
        print('CMD:', monster_in['CMD'], file=f)

    if keys_used is not None: keys_used['feats'] = True
    if 'feats' in monster_in:
        feats = []
        for feat in monster_in['feats']:
            feats.append(feat['name'])
        print('feats:', wq(', '.join(feats)), file=f)

    if keys_used is not None: keys_used['skills'] = True
    if 'skills' in monster_in:
        skills = []
        for s in monster_in['skills'].keys():
            if s == '_racial_mods':
                continue
            key = s
            if monster_in['skills'][key]['_'] is None:
                val = ""
            else:
                val = '{0:+}'.format(monster_in['skills'][key]['_'])
            skills.append( key + ' ' + val)
        print('skills:', wq(', '.join(skills)), file=f)

        if '_racial_mods' in monster_in['skills']:
            print( 'racial_modifiers:', file=f)
            for s in monster_in['skills']['_racial_mods']:
                if '_' in monster_in['skills']['_racial_mods'][s]:
                    print( '-', s, monster_in['skills']['_racial_mods'][s]['_'], file=f)
                elif s == '_other':
                    print( '-',  monster_in['skills']['_racial_mods'][s], file=f)
                else:
                    try:
                        for k in monster_in['skills']['_racial_mods'][s]:
                            print( '-', s, monster_in['skills']['_racial_mods'][s][k], file=f)
                    except Exception as e:
                        print(e) 
                        print(monster_in['title1'])
                        print(k)
                        print(s)
                        print(monster_in['skills']['_racial_mods'][s])
                        quit()

    if keys_used is not None: keys_used['languages'] = True
    if 'languages' in monster_in:
        print( 'languages:', wq(', '.join(monster_in['languages'])), file=f)
    
    if keys_used is not None: keys_used['special_qualities'] = True
    if 'special_qualities' in monster_in:
        print( 'special_qualities:', wq(', '.join(monster_in['special_qualities'])), file=f)

    if keys_used is not None: keys_used['gear'] = True
    if 'gear' in monster_in:
        print('gear:', file=f)
        for k in monster_in['gear']:
            print('  - name:', k, file=f)
            to_desc( ', '.join(monster_in['gear'][k]), f)

    if keys_used is not None: keys_used['ecology'] = True
    if 'ecology' in monster_in:
        print("ecology:", file=f)
        if 'environment' in monster_in['ecology']:
            print('  - name: Environment', file=f)
            to_desc( monster_in['ecology']['environment'], f)
        if 'organization' in monster_in['ecology']:
            print('  - name: Organisation', file=f)
            to_desc( monster_in['ecology']['organization'], f)
        if 'treasure' in monster_in['ecology'] and 'treasure_type' in monster_in['ecology']:
            print('  - name: Treasure', file=f)
            to_desc( monster_in['ecology']['treasure_type'] + ' (' + ', '.join(monster_in['ecology']['treasure']) + ')', f)
        elif 'treasure_type' in monster_in['ecology']:
            to_desc( monster_in['ecology']['treasure_type'], f)
    
    if keys_used is not None: keys_used['special_abilities'] = True
    if 'special_abilities' in monster_in:
        print('special_abilities:', file=f)
        for sa in monster_in['special_abilities'].keys():
            print('  - name:', sa, file=f)
            to_desc(monster_in['special_abilities'][sa], f)

    if keys_used is not None: keys_used['spells'] = True
    if 'spells' in monster_in:
        for source in monster_in['spells']['sources']:
            if source['type'] == 'prepared':
                print('spells_prepared:', file=f)
            elif source['type'] == 'known':
                print('known_spells:', file=f)
            print('  - name:', file=f)
            to_desc( '(CL ' + str(source['CL']) + ')', f)
            spells = {}
            for entry in monster_in['spells']['entries']:
                this_count = ""
                this_dc = ""
                this_level = str(entry['level'])
                if 'count' in entry:
                    this_count = str(entry['count']) + 'x'
                if 'DC' in entry:
                    this_dc = ' (DC' + str(entry['DC']) + ')'
                this_spell = this_count + entry['name']
                if this_level in spells:
                    spells[this_level] = spells[this_level] + ', ' + this_spell + this_dc
                else:
                    spells[this_level] = this_spell + this_dc

            for key in spells.keys():
                nth = { '1' : 'st', '2': 'nd', '3': 'rd'}
                header = str(key)
                if key in nth:
                    header = header + nth[key]
                elif key != '0':
                    header = header + 'th'
                if 'slots' in source and key in source['slots']:
                    if key == '0':
                        header = header + ' (at-will)'
                    else:
                        header = header + ' (' + str(source['slots'][key]) + '/day)'
                print('  - name:', header, file=f)
                to_desc( spells[key], f)

    if keys_used is not None: keys_used['psychic_magic'] = True
    if 'psychic_magic' in monster_in:
        for source in monster_in['psychic_magic']['sources']:
            print('psychic_magic:', file=f)
            print('  - name:', file=f)
            to_desc( str(source['CL']) + '; Concentration ' + '{0:+})'.format(source['concentration']), f)
            psychic_magic = []
            for entry in monster_in['psychic_magic']['entries']:
                this_dc = ""
                if 'DC' in entry:
                    this_dc = '; DC' + str(entry['DC'])
                if 'PE' in entry:
                    psychic_magic.append(entry['name'] + ' (PE' + str(entry['PE']) + this_dc + ')')
                else:
                    psychic_magic.append(entry['name'])
            print('  - name:', monster_in['psychic_magic']['PE'], 'PE', file=f)
            to_desc( ', '.join(psychic_magic), f)

    if keys_used is not None: keys_used['spell_like_abilities'] = True
    if 'spell_like_abilities' in monster_in:
        print('spell-like_abilities:', file=f)
        for source in monster_in['spell_like_abilities']['sources']:
            if source['name'] == 'default':
                print('  - name:', file=f)
            else:
                print('  - name:', source['name'], file=f)
            if 'concentration' in source:
                to_desc( '(CL ' + str(source['CL']) + '; Concentration ' + '{0:+})'.format(source['concentration']), f)
            else:
                to_desc( '(CL ' + str(source['CL']) + ')', f)
            sla = {}
            for entry in monster_in['spell_like_abilities']['entries']:
                if entry['source'] != source['name']:
                    continue
                if entry['freq'] in sla:
                    if 'DC' in entry:
                        dc = ' (DC ' + str(entry['DC']) + ')'
                    else:
                        dc = ''
                    sla[entry['freq']] = sla[entry['freq']] + ', ' + entry['name'] + dc
                else:
                    if 'DC' in entry:
                        dc = ' (DC ' + str(entry['DC']) + ')'
                    else:
                        dc = ''
                    sla[entry['freq']] = entry['name'] + dc
            for key in sla.keys():
                print('  - name:', key, file=f)
                to_desc( sla[key], f)
    
    if keys_used is not None: keys_used['sources'] = True
    if 'sources' in monster_in:
        print('sources:', file=f)
        for source in monster_in['sources']:
            print('  - name:', wq(source['name'].replace('#', 'No. ')), file=f)
            to_desc( str(source['page']), f)

    if keys_used is not None: keys_used['desc_short'] = True
    if 'desc_short' in monster_in:
        print('desc_short:', monster_in['desc_short'], file=f)
    
    print('```', file=f)

    if keys_used is not None: keys_used['desc_long'] = True
    if 'desc_long' in monster_in:
        print('# Description', file=f)
        print(monster_in['desc_long'], file=f)
    
    if url is not None:
        print('# Source Link', file=f)
        print('[Archives of Nethys](' + url + ')', file=f)

    print('```encounter-table', file=f)
    print('name:', monster_name, file=f)
    print('creatures:', file=f)
    print('  - 1:', monster_name, file=f)
    print('```', file=f)


if __name__ == "__main__":
    # Options to add
    # Path to read from
    # Flat or heirarchy
    # Heirarchy includes AoN changes of URL
    # Logging
    # Test monster number
    # Dump unused keys
    debug = False
    
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--input_folder", action="store", help="input folder containing data.json")
    parser.add_argument("-o", "--output_folder", action="store", help="output folder that will be written into")
    parser.add_argument("-t", "--test", action="store", help="output one test monster to stdout")
    parser.add_argument("-c", "--clean", action="store_true", help="clean the output location")
    parser.add_argument("-m", "--monster", action="store", help="write a test monster 1 level up")
    args = parser.parse_args()

    if args.input_folder:
        datapath = os.path.join(args.input_folder, 'data.json')
    else:
        datapath = "data/data.json"
        
    print("Loading data...", end="", flush=True)
    with open(datapath) as f:
        d = json.load(f)
    print(" done")
    
    if args.test:
        if args.test == 1:
            example = 'https://aonprd.com/MonsterDisplay.aspx?ItemName=Brijidine'
        elif args.test == 2:
            example = 'https://aonprd.com/MonsterDisplay.aspx?ItemName=Veranallia'
        elif args.test == 3:
            example = "https://aonprd.com/MonsterDisplay.aspx?ItemName=Uinuja"
        elif args.test == 4:
            # Spontaneous
            example = 'https://aonprd.com/MonsterDisplay.aspx?ItemName=Lillend'
        elif args.test == 5:
            # Prepared
            example = 'https://aonprd.com/MonsterDisplay.aspx?ItemName=Ghaele'
        elif args.test == 6:
            example ='https://aonprd.com/MonsterDisplay.aspx?ItemName=End%27s%20Voice'
        monster_in = d[example]
        write_monster(monster_in)
    else:
        keys_present = {}
        keys_used = {}
        source_dict = {}
        
        if args.output_folder:
            outpath = args.output_folder
        else:
            outpath = "bestiary/"
        
        Path(outpath).mkdir(parents=True, exist_ok=True)
        
        if args.clean:
            myFiles = [f for f in os.listdir(outpath) if os.path.isfile(os.path.join(outpath, f))]
            for file in myFiles:
                if '.md' in file:
                    os.remove(os.path.join(outpath, file))
                
        for key in d:
            monster_in = d[key]
            
            for mkey in monster_in:
                keys_present[mkey] = True
            try:
                subdir = key.split('/')[3].split('.')[0]
                subdir = subdir.replace('Display', '')
                if 'NPCDisplay' in key:
                    fname = os.path.join(outpath, 'NPC ' + monster_in['title2'].replace('/', ' or ') + '.md')
                    monster_in['title2'] = 'NPC ' + monster_in['title2'] 
                else:
                    fname = os.path.join(outpath, monster_in['title2'].replace('/', ' or ') + '.md')
                    
                write_monster(monster_in, fname, source_dict=source_dict, keys_used=keys_used, url=key)
            except ( KeyError, TypeError ) as e:
                print('ERROR: ', e, 'with', key)

        if args.monster:
            monster_dir = os.path.dirname(os.path.dirname(os.path.join(outpath, 'test.txt')))
            filename = os.path.join(monster_dir, args.monster + '_test.md')
            with open(filename, 'w') as f:
                print('```statblock', file=f)
                print('monster:', args.monster, file=f)
                print('```', file=f)
        
        if debug:
            print(keys_present.keys() - keys_used.keys())
            print('Sources')
            print(source_dict.keys())