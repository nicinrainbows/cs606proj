# -*- coding: utf-8 -*-
'''
Created on Mon Feb 28 20:17:15 2022

These functions and classes are for midi processing

Dummy code to define classes and functions from the assignment 2 script. Start with this first.

'''
import os
import sys
import copy
from itertools import groupby
import numpy as np

import pretty_midi

def all_equal(iterable):
    '''
    Utility function to check that all items in list are the same. For checking array lengths for each voice.
    
    Parameters
    ----------
    iterable : list
        List of the lengths of each voice (i.e. list of notes).

    Returns
    -------
        True if all lengths are the same, False otherwise

    '''
    g = groupby(iterable)
    return next(g, True) and not next(g, False)

def test_function(midi_file):
    midi_data = pretty_midi.PrettyMIDI(midi_file)
    print('time signature: ',midi_data.time_signature_changes)
    print('interval length: ',round(60000/midi_data.get_tempo_changes()[1][0]))
    print('beat locations: ',midi_data.get_beats())
    print('note onsets: ',midi_data.get_onsets())
    print('note starts (in ms): ',[[round(note.start * 1000) for note in instrument.notes] for instrument in midi_data.instruments])
    print('note starts (in beats): ',[[round(note.start/round(60/midi_data.get_tempo_changes()[1][0],3),4) for note in instrument.notes] for instrument in midi_data.instruments])
    return
def midi_to_array(midi_file):
    '''
    Function to convert midi file to array for processing.
    
    Parameters
    ----------
    midi_file : str
        File path of the midi file

    Returns
    -------
    midi_array : list
        Array of notes (int) standardised to a constant beat

    '''
    midi_data = pretty_midi.PrettyMIDI(midi_file)
    
    # get time interval (in microseconds)
    
    # confirm that there are no tempo changes in the music (i.e. tempo change only occurs once at start)
    if len(midi_data.get_tempo_changes()[0]) > 1:
        raise Exception(f'There are tempo changes in {midi_file}, do not use')
    
    # convert the tempo into a time interval (ms)
    tempo_interval = 60000/midi_data.get_tempo_changes()[1][0]
   
    # create a set of timesteps
    time_steps = list(midi_data.get_beats())
    
    # pad the beats to the end of the song
    while time_steps[-1] <= midi_data.get_end_time():    
        time_steps.append(time_steps[-1] + tempo_interval)

    # create midi_array as an array of notes with a constant beat
    midi_array = []
    
    for instrument in midi_data.instruments:
        # voice should have a length corresponding to the number of beat locations
        voice = [None] * len(time_steps)
        notes_check = []
        for note in instrument.notes:
            notes_check.append([note.start,note.end,note.pitch])
            # check if the start of the note corresponds to a beat location
            if note.start in time_steps:
                idx = time_steps.index(note.start)
                if idx + 1 == len(time_steps):
                    voice[idx] = note.pitch - 36 # transpose to mid C = 24
                else:
                    # if note lasts more than one beat, then repeat
                    while time_steps[idx+1] <= note.end:
                        voice[idx] = note.pitch - 36 # transpose to mid C = 24
                        idx += 1
        # print(notes_check)
        # add voice to midi array
        midi_array.append(voice)
    
    # check that all voices have same length
    lengths = []
    for voice in midi_array:
        lengths.append(len(voice))
        
    # print('length of each voice: ',lengths)
    
    if not all_equal(lengths):
        raise Exception('Error in array output, not all voices have same length')
    
    # print(midi_array, min_interval)
    
    return midi_array, tempo_interval


def array_to_midi(midi_array, instruments, beat, dest_file_path = '../outputs/model_output.mid'):
    '''
    Function to convert array to midi file

    Parameters
    ----------
    midi_array : nested list of int (0-127)
        Array of notes (int) standardised to a constant beat. Find the note numbers mapped at: https://www.music.mcgill.ca/~ich/classes/mumt306/StandardMIDIfileformat.html#BMA1_3
        
    instruments : list of int (0-127)
        Array of four program numbers of the selected instrument for each voice. Find the patch map at: https://www.music.mcgill.ca/~ich/classes/mumt306/StandardMIDIfileformat.html#BMA1_4        
        
    beat : int
        An integer representing the time length of each note in microseconds
        
    file_name : str
        Name of output file

    Returns
    -------
        Writes the midi file to output

    '''
    # Check validity of instrument array
    if len(instruments) != 4:
        raise Exception('Error, length of instrument array should be 4')
    
    # Create a PrettyMIDI object to store the compiled music, tempo in bpm converted from beat
    midi_output = pretty_midi.PrettyMIDI(initial_tempo = round(60000/beat))
        
        
    for i in range(len(midi_array)):
        # Create a PrettyMIDI instrument with chosen instrument
        instrument = pretty_midi.Instrument(program=instruments[i])
        # restart the note interval
        time = 0
        # Iterate over note names, which will be converted to note number later
        for note_number in midi_array[i]:
            # check if pause, i.e. note is empty
            if note_number == None:
                # skip a beat, extend the time
                time += beat/1000
            else:
                # Create a Note instance, starting at 0 and ending at 1 beat (in s)
                note = pretty_midi.Note(
                    velocity=127, pitch = note_number + 36, start = time, end = time + beat/1000)
                # Add it to our instrument
                instrument.notes.append(note)
            # extend the time
            time += beat/1000
        # Add the instrument to the PrettyMIDI object
        midi_output.instruments.append(instrument)
     
    
    # Write out the MIDI data
    midi_output.write(dest_file_path)
    
    return