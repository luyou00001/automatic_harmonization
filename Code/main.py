import music21 as m21
import os
from music21.converter.subConverters import ConverterMusicXML
import PySimpleGUI as sg
import PIL
import io
import functools
from sys import platform
import argparse
from utils import *

parser = argparse.ArgumentParser()
parser.add_argument('--path', type=str, help='The path of the input MusicXML file')
parser.add_argument('--out_fp', type=str, help='The path to store temporary files')

parser.set_defaults(
    path=None,
    out_fp='./temp/temp'
)

args = parser.parse_args()

if args.path == None:
    raise Exception('No input file path specified.')

xml_data = m21.converter.parse(args.path)

# set path for MuseScore
us = m21.environment.UserSettings()
us_path = us.getSettingsPath()
if not os.path.exists(us_path):
    us.create()

# For Mac only
if platform == "darwin":
    us['musescoreDirectPNGPath'] = '/Applications/MuseScore 3.app/Contents/MacOS/mscore'
    us['musicxmlPath'] = '/Applications/MuseScore 3.app/Contents/MacOS/mscore'
elif platform == 'win32' or platform == 'cygwin':
    # set path for windows
    us['musescoreDirectPNGPath'] = r'C:/Program Files/MuseScore 3/bin/MuseScore3.exe'
    us['musicxmlPath'] = r'C:/Program Files/MuseScore 3/bin/MuseScore3.exe'
    pass

xml_data = m21.converter.parse(args.path)

# convert xml data to png
path_dir = '/'.join(args.out_fp.split('/')[:-1])
if not os.path.exists(path_dir):
    os.makedirs(path_dir)

conv_musicxml = ConverterMusicXML()
out_filepath = conv_musicxml.write(xml_data, 'musicxml', fp=os.path.join(args.out_fp), subformats=['png'])

print("Finish converting to png")

# retrieve useful info
flat = xml_data.parts[0].flat
timeSig = flat.timeSignature.ratioString
nbeat = flat.timeSignature.numerator
nbar = int(flat.highestTime / nbeat)
key = flat.keySignature.tonic.name
mode = flat.keySignature.mode 

print("Time signature:", timeSig)
print("Number of bars:", nbar)
print("Key:", key, mode)

out_fp_prefix = out_filepath[:-5]
ext = out_filepath[-4:]
i = 1
valid_paths = []
while os.path.exists(out_fp_prefix + str(i) + ext):
    valid_paths.append(out_fp_prefix + str(i) + ext)
    i = i + 1
#print(valid_paths)

  
# create UI
phrases = []
nphrases = 0

phrase_col = sg.Column([
    [sg.Text("Phrase Selection"), sg.Button("HARMONIZE", key='-HARM-')],
    [sg.Text("________________________________________")],
    [sg.Text("Start Bar"), sg.In(key='-SBAR-', size=(5,1)), sg.Text("Beat"), sg.In(key='-SBEAT-', size=(2,1))],
    [sg.Text('End Bar'), sg.In(key='-EBAR-', size=(5,1)), sg.Text("Beat"), sg.In(key='-EBEAT-', size=(2,1))],
    [sg.Text("Cadence (PE/IM/PL/DE)"), sg.In(key='-CAD-', size=(3,1))],
    [sg.Button('Add New Phrase', key='-NEWPHRASE-')],
    [sg.Text("________________________________________")],
    [sg.Text("Phrases")],
    [sg.Text("________________________________________")],
    [sg.Text("Phrase   Start   End   Cadence", key='-PHRASES-', size=(30,nbar + 1))],
    [sg.Text("__________________________________________")],
    [sg.Text("Phrase"), sg.In(key='-P-', size=(3,1)),sg.Button('DELETE', key="DELPHRASE")], 
    [sg.Button('CLEAR ALL', key='-CLRPHRASE-')],
    [sg.Text("________________________________________")],
    [sg.Text("", size=(30, 10), key='-EMESS-')] #error message
    
], expand_y=True, key='-PHRASECOL-', scrollable=True)

layout = [
    [
        sg.Column([
            [sg.Image(data=convert_to_bytes(vp, ratio=0.5), key='-IMAGE'+str(i)+'-')] for i, vp in enumerate(valid_paths)
        ],scrollable=True, key='-COL-'),
        phrase_col
    ]
]

window = sg.Window(title="Hello World", layout = layout, resizable=True)

while True:
    event, values = window.read()
    #print(event, values)
    
    if event != sg.WIN_CLOSED:
        window['-EMESS-'].update("")
    
    if event == sg.WIN_CLOSED:
        break
        
    elif event == '-NEWPHRASE-':
        try:
            if values['-SBAR-'] and values['-EBAR-']: # and values['-H-']:
                sbar = int(values['-SBAR-'])
                ebar = int(values['-EBAR-'])
                
                sbeat = int(values['-SBEAT-']) if values['-SBEAT-'] else 1
                ebeat = int(values['-EBEAT-']) if values['-EBEAT-'] else nbeat
                    
                if sbar > nbar or ebar > nbar:
                    raise Exception("Bar number cannot exceed the number of bars")
                
                if sbeat > nbeat or ebeat > nbeat:
                    raise Exception("Beat number cannot exceed the number of beats")
                
                cad = values['-CAD-'] if values['-CAD-'] else None
                
                if cad and cad != 'PE' and cad != 'IM' and cad != 'DE' and cad != 'PL':
                    raise Exception("Cadence must have values of 'PE'/'IM'/'DE'/'PL', if entered")
                    
                if sbar * nbeat + sbeat > ebar * nbeat + ebeat:
                    raise Exception("End of phrase cannot be earlier than start of phrase")
                
                if (nphrases == nbar):
                    print("reached maximum number of phrases")
                else:
                    nphrases = nphrases + 1
                    phrases = phrases + [[sbar, sbeat, ebar, ebeat, cad]]
                    p_str = phrase_str(phrases)
                    window['-PHRASES-'].update(p_str)

                    window.refresh()
        except Exception as E:
            print(f'** Error **\n{E}')
            window['-EMESS-'].update(f'** Error **\n{E}')
            pass
        
    elif event == '-CLRPHRASE-':
        phrases = []
        nphrases = 0
        p_str = phrase_str(phrases)
        window['-PHRASES-'].update(p_str)
        
    elif event == 'DELPHRASE':
        try:
            if values['-P-']:
                phrases.pop(int(values['-P-']) - 1)
                nphrases = nphrases - 1

                p_str = phrase_str(phrases)
                window['-PHRASES-'].update(p_str)
        except Exception as E:
            print(f'** Error **\n{E}')
            window['-EMESS-'].update(f'** Error **\n{E}')
            pass
        
    elif event == '-HARM-':
        
        try:
        
            # convert to easier form
            p_offsets = phrase_to_offset(phrases, nbeat)

            # sort
            p_offsets.sort(key=functools.cmp_to_key(sort_key))

            # remove duplicate
            for i in reversed(range(1, len(p_offsets))):
                if p_offsets[i] == p_offsets[i-1]:
                    p_offsets.pop(i)

            # check for overlap
            if has_overlap(p_offsets):
                raise Exception("Overlapping exists in phrases")

            # partition the notes into phrases
            par = partition(flat.notes.sorted.elements, p_offsets)
            
            for p in par:
                print(p)
                # call harmonization function
                pass
        
        except Exception as E:
            print(f'** Error **\n{E}')
            window['-EMESS-'].update(f'** Error **\n{E}')
            pass

window.close()