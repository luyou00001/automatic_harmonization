import PIL
import PySimpleGUI as sg
import io
import functools

def convert_to_bytes(file_or_bytes, ratio=None):

    if isinstance(file_or_bytes, str):
        img = PIL.Image.open(file_or_bytes)
    cur_width, cur_height = img.size

    if ratio > 0:
        #new_width, new_height = resize
        #scale = min(new_height/cur_height, new_width/cur_width)
        img = img.resize((int(cur_width * ratio),int(cur_height*ratio)), PIL.Image.NEAREST)
        
    bio = io.BytesIO()
    img.save(bio, format="PNG")
    del img
    return bio.getvalue()

def phrase_str(phrases):

    p_str = [(str(elem[0])+':'+str(elem[1])).ljust(8,' ') + (str(elem[2])+':'+str(elem[3])).ljust(6,' ')
             + str(elem[4]) for elem in phrases]
    p_str = [("P"+str(i+1)).ljust(9,' ') +'   '+elem for i, elem in enumerate(p_str)]
    p_str = 'Phrase   Start   End   Cadence\n' + '\n'.join(p_str)
    
    return p_str

def phrase_to_offset(phrases, nbeat):
    return [[(elem[0] - 1)*nbeat + elem[1]-1, (elem[2]-1)*nbeat+elem[3]-1, elem[4]] for elem in phrases]

def sort_key(x, y):
    if x[0] > y[0]:
        return 1
    elif x[0] < y[0]:
        return -1
    else:
        if x[1] > y[1]:
            return 1
        elif x[1] < y[1]:
            return -1
        else:
            return 0
        
def has_overlap(offsets):
    prev = -1
    for elem in offsets:
        if elem[0] <= prev:
            return True
        else:
            prev = elem[1]
    return False

def partition(notes, offsets):
    
    np = 0
    op = 0
    par = []
    bucket = []
    
    while np < len(notes) and op < len(offsets):
    
        s, e, p = offsets[op]
        e = e + 1
        note = notes[np]
        #print(np, op)
        ##print(s, e)
        #print(note.offset)
        #print(note.quarterLength)
        
        if note.offset < s:
            np = np + 1
            continue
        
        if note.offset + note.quarterLength > e:
            if len(bucket) > 0:
                par.append([p] + bucket)
                bucket = []
            op = op + 1
            continue
        
        bucket.append(note)
        np = np + 1
    
    if op < len(offsets) and len(bucket) > 0:
        par.append([offsets[op][2]] + bucket)
    
    return par