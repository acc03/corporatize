#!/usr/bin/python3
import os
import pdfkit
import json
import yaml
import PyPDF2
from random import randint
from datetime import date

options = {'enable-local-file-access': None}

def parse(text, answers, style):
    global config
    text = list(text)
    i = 0
    mode = 'text'
    command = ''
    argument = ''
    parsed = ''
    stylesel = ''
    tstorage = {}
    for item in answers:
        tstorage[item] = answers[item]
    while i < len(text):
        if mode == 'text':
            if text[i] == '{':
                mode = 'command'
            else:
                parsed += text[i]
        elif mode == 'command':
            if text[i] == ',':
                mode = 'argument'
            elif text[i] == '}':
                mode = 'text'
                command = ''
            else:
                command += text[i]
        elif mode == 'argument':
            if text[i] == ',':
                if command == 'pe':
                    if argument in list(answers.keys()):
                        parsed += answers[argument].replace(' ', '<span class="invis">_</span>')
                    else:
                        parsed += input(argument).replace(' ', '<span class="invis">_</span>')
                elif command == 'p':
                    if argument in list(answers.keys()):
                        parsed += answers[argument]
                    else:
                        parsed += input(argument)
                elif command == 'ret':
                    parsed += '<br>'
                elif command == 'date':
                    parsed += date.today().strftime('%m/%d/%y')
                elif command == 'print':
                    print(argument)
                elif command == 'store':
                    try:
                        tstorage[argument]
                    except KeyError:
                        tstorage[argument] = input(argument)
                elif command == 'recall':
                    parsed += tstorage[argument]
                elif command == 'style':
                    stylesel = style[argument]
                elif command == 'curr_iter':
                    parsed += str(answers['___curr-iter___'])
                elif command == 'runs':
                    parsed += str(answers['___runs___'])
                elif command == 'series':
                    parsed += str(answers['___series___'])
                mode = 'command'
                argument = ''
            else:
                argument += text[i]
        i += 1
    
    if config['top_margin_fix'] == True:
        parsed_html = f'''<!DOCTYPE html>
<head>
    <style>
    {stylesel}
    </style>
</head>
<body>
<br><br><br><br>
    {parsed}
</body>
</html>'''
    else:
        parsed_html = f'''<!DOCTYPE html>
<head>
    <style>
    {stylesel}
    </style>
</head>
<body>
    {parsed}
</body>
</html>'''
    return parsed_html

def to_pdf(html_data, output = 'temp.pdf', verbose = True):
    outfile = open('temp.html', 'w+')
    outfile.write(html_data)
    outfile.close()
    if verbose == True:
        print('''
Converting HTML code into printable format...
----------''')
    pdfkit.from_file('temp.html', output, options=options)

def printfile(file, printfile = True, mode = 'default'):
    if printfile:
        if mode == 'default':
            os.system(f'lpr -P {printer} {file}')
        elif mode == 'env2':
            os.system(f'lpr -P {printer} -o media=Custom.4.125x9.5in {file}')
        elif mode == 'short':
            os.system(f'lpr -P {printer} -o sides=two-sided-short-edge -o media=Custom.4.125x9.5in {file}')
        elif mode == 'long':
            os.system(f'lpr -P {printer} -o sides=two-sided-long-edge {file}')

def merge(files, output):
    infiles = []
    readers = []
    writer = PyPDF2.PdfFileWriter()
    for file in files:
        infiles.append(open(file, 'rb'))
    for file in infiles:
        readers.append(PyPDF2.PdfFileReader(file))
    for reader in readers:
        for pg in range(reader.numPages):
            obj = reader.getPage(pg)
            writer.addPage(obj)
    outfile = open(output, 'wb')
    writer.write(outfile)
    outfile.close()
    for file in infiles:
        file.close()

infile = open('db.json', 'r+')
db_json = json.load(infile)
for item in os.listdir('user-config'):
    db_json.update(json.load(open(f'user-config/{item}')))
db = db_json['db']
answers = db_json['answers']
answers_bulk = db_json['answers-bulk']
style = db_json['style']
envelope = db_json['db-special']['envelope']
envelope_v2 = db_json['db-special']['envelope-v2']
envelope_special = db_json['db-special']['envelope-special']
envelope_special_v2 = db_json['db-special']['envelope-special-v2']
infile.close()

infile = open('config.yml', 'r+')
config = yaml.load(infile, Loader=yaml.FullLoader)
infile.close()

for key in answers_bulk.keys():
    answers_bulk[key] = answers_bulk[key][config['amount_start']:config['amount_end']]

expected_ablength = len(answers_bulk[list(answers_bulk.keys())[0]])
for item in list(answers_bulk.keys()):
    if type(answers_bulk[item]) == list:
        if not len(answers_bulk[item]) == expected_ablength:
            raise Exception('Lists in bulk answer list are mismatched')

answers['___curr-iter___'] = 'None'

with open('db.json', 'r+') as infile:
    temp = json.load(infile)

with open('db.json', 'w+') as outfile:
    temp['runs'] += 1
    runs = temp['runs']
    series = temp['series']
    outfile.write(json.dumps(temp, indent = 4))

answers['___runs___'] = runs
answers['___series___'] = series

printer = config['printer']
if config['mode'] == 'print':
    if not config['bulk_print']:
        text = db[randint(0, len(db) - 1)]
        parsed = parse(text, answers, style)
        to_pdf(parsed)
        print('''Printing...
----------''')
        printfile('temp.pdf', config['print'])
        if config['envelope_print']:
            input('Load envelopes into printer and press enter')
            parsed = parse(envelope, answers, style)
            to_pdf(parsed)
            printfile('temp.pdf', config['print'])
    elif config['bulk_print']:
        if config['letter_print']:
            i = 0
            pdfs = []
            while i < expected_ablength:
                text = db[randint(0, len(db) - 1)]
                for item in list(answers_bulk.keys()):
                    if type(answers_bulk[item]) == list:
                        temp = answers_bulk[item]
                        temp = temp[i]
                        temp = {item:temp}
                        answers.update(temp)
                answers['___curr-iter___'] = i
                parsed = parse(text, answers, style)
                to_pdf(parsed, f'pdf/letter/{i}.pdf')
                pdfs.append(f'pdf/letter/{i}.pdf')
                i += 1
            merge(pdfs, 'pdf/letter/temp.pdf')
            printfile('pdf/letter/temp.pdf', config['print'])
        if config['envelope_print']:
            i = 0
            input('Load envelopes into printer and press enter')
            pdfs = []
            while i < expected_ablength:
                for item in list(answers_bulk.keys()):
                    if type(answers_bulk[item]) == list:
                        temp = answers_bulk[item]
                        temp = temp[i]
                        temp = {item:temp}
                        answers.update(temp)
                if config['envelope_print_v2']:
                    parsed = parse(envelope_v2, answers, style)
                else:
                    parsed = parse(envelope, answers, style)
                to_pdf(parsed, f'pdf/envelope/{i}.pdf')
                pdfs.append(f'pdf/envelope/{i}.pdf')
                i += 1
            merge(pdfs, 'pdf/envelope/temp.pdf')
            if config['envelope_print_v2']:
                printfile('pdf/envelope/temp.pdf', config['print'], 'env2')
            else:
                printfile('pdf/envelope/temp.pdf', config['print'])
            if config['envelope_print_ds']:
                input('Stamping is enabled. Load flipped envelopes into printer and press enter')
                pdfs = []
                i = 0
                while i < expected_ablength:
                    for item in list(answers_bulk.keys()):
                        if type(answers_bulk[item]) == list:
                            temp = answers_bulk[item]
                            temp = temp[i]
                            temp = {item:temp}
                            answers.update(temp)
                    if config['envelope_print_v2']:
                        parsed = parse(envelope_special_v2, answers, style)
                    else:
                        parsed = parse(envelope_special, answers, style)
                    to_pdf(parsed, f'pdf/envelope-ds/{i}.pdf')
                    pdfs.append(f'pdf/envelope-ds/{i}.pdf')
                    i += 1
                merge(pdfs, 'pdf/envelope-ds/temp.pdf')
                if config['envelope_print_v2']:
                    printfile('pdf/envelope-ds/temp.pdf', config['print'], 'env2')
                else:
                    printfile('pdf/envelope-ds/temp.pdf', config['print'])
elif config['mode'] == 'testing':
    pass
if not config['debug']:
    if os.path.exists('temp.pdf'):
        os.remove('temp.pdf')
    if os.path.exists('temp.html'):
        os.remove('temp.html')
    for sd in os.listdir('pdf'):
        if not '.' in sd:
            for file in os.listdir(f'pdf/{sd}'):
                os.remove(f'pdf/{sd}/{file}')