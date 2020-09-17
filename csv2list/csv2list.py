import csv
import yaml
import json
import sys
from agefromname import AgeFromName
from datetime import datetime

afn = AgeFromName()

def occusel(names, _config = None):
    if _config == None:
        global config
    else:
        config = _config
    try:
        infile = open('cache.json', 'r+')
    except FileNotFoundError:
        with open('cache.json', 'w+') as outfile:
            outfile.write('{}')
        infile = open('cache.json', 'r+')
    cache = json.load(infile)
    infile.close()
    namedic = {}
    year = datetime.now().year
    for name in names:
        namedic[name] = {}
        try:
            namedic[name]['score'] = cache[name]
        except KeyError:
            if afn.prob_female(name) >= 0.5:
                namedic[name]['gender'] = 'f'
            else:
                namedic[name]['gender'] = 'm'
            try:
                namedic[name]['year_born'] = int(afn.argmax(name, namedic[name]['gender'], minimum_age = 18))
            except ValueError:
                namedic[name]['year_born'] = 1950
            namedic[name]['age'] = year - namedic[name]['year_born']
            namedic[name]['score'] = 6
            if namedic[name]['gender'] == 'f':
                namedic[name]['score'] -= 1
            namedic[name]['score'] -= ((namedic[name]['age'] - 18) / 60) * 5
            cache[name] = namedic[name]['score']
            outfile = open('cache.json', 'w+')
            outfile.write(json.dumps(cache, indent = 2))
            outfile.close()
    selection = ''
    curr_score = -1.5
    if config['sexism']:
        for key in list(namedic.keys()):
            if namedic[key]['score'] > curr_score:
                selection = key
                curr_score = namedic[key]['score']
    else:
        print('SEXISM OFF')
        selection = list(namedic.keys())[0]
    return selection

afn = AgeFromName()

infile = open('config.yml', 'r')
config = yaml.load(infile, Loader=yaml.FullLoader)
infile.close()

raw_data =[]
infile = open(config['file'], 'r')
data_reader = csv.DictReader(infile)
for row in data_reader:
    raw_data.append(row)
infile.close()

address_dict = {}
for item in raw_data:
    try:
        item['Last Name']
        item['First Name']
        item['House Number']
        item['Pre-directional']
        item['Street']
        item['Street Suffix']
        item['Post-directional']
        item['City']
        item['State']
        item['ZIP Code']
        item['County Name']
    except KeyError:
        if config['ignore-invalid']:
            pass
        else:
            sys.exit(0)
    item['House Number'] = item['House Number'].replace(' ', '')
    address = ''
    if item['Pre-directional'] != '':
        address += f'{item["Pre-directional"]} '
    address += f'{item["House Number"]} '
    address += f'{item["Street"]} {item["Street Suffix"]}'
    if item['Post-directional'] != '':
        address += f' {item["Post-directional"]}'
    if not address in list(address_dict.keys()):
        address_dict[address] = []
    address_dict[address].append(item)

address_dict_sorted = {}
for key in list(address_dict.keys()):
    names = []
    for occupant in address_dict[key]:
        names.append(occupant['First Name'])
    name = occusel(names)
    print(f'Successfully selected occupant ({list(address_dict.keys()).index(key) + 1}/{len(list(address_dict.keys()))})')
    for occupant in address_dict[key]:
        try:
            address_dict_sorted[key]
        except:
            if occupant['First Name'] == name:
                address_dict_sorted[key] = occupant

formatted_data = {'names':[],'names_full':[],'street_addresses':[],'city_zip':[]}
for key in list(address_dict_sorted.keys()):
    formatted_data['names'].append(address_dict_sorted[key]['First Name'])
    formatted_data['names_full'].append(f'{address_dict_sorted[key]["First Name"]} {address_dict_sorted[key]["Last Name"]}')
    formatted_data['street_addresses'].append(f'{address_dict_sorted[key]["House Number"]} {address_dict_sorted[key]["Street"]} {address_dict_sorted[key]["Street Suffix"]}')
    formatted_data['city_zip'].append(f'{address_dict_sorted[key]["City"]}, {address_dict_sorted[key]["State"]}  {address_dict_sorted[key]["ZIP Code"]}')

outstr = ''
for key in list(formatted_data.keys()):
    outstr += f'''{key}: {str(formatted_data[key]).replace("'", '"')}
'''

outfile = open('out.txt', 'w+')
outfile.write(outstr)
outfile.close()