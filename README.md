# FamiStudio to MIDI converter
Simple scripts to convert [FamiStudio](https://famistudio.org/) text format to MIDI.

# Usage
## FamiStudio -> MIDI
`> python fami_to_midi.py FAMISTUDIO_FILE.txt`

or 

`> python fami_to_midi.py FAMISTUDIO_FILE.txt OUTPUT_FILE.mid`

This creates a multi-track midi where the FamiStudio instruments are assigned to the following MIDI instruments:

    - Square1: 80
    - Square2 : 81
    - Triangle : 38
    - Noise : 121
    
This was originally designed to be compatible with [this dataset](https://github.com/chrisdonahue/nesmdb).
Only notes, velocities and durations are kept.

## MIDI -> FamiStudio
`> python midi_to_fami.py MIDI_FILE.mid`

or 

`> python midi_to_fami.py MIDI_FILE.mid OUTPUT_FILE.txt`

The input MIDI file must follow the guidelines defined above.

# Dependencies
- [Click](https://click.palletsprojects.com/en/7.x/)
- [pretty-midi](https://github.com/craffel/pretty-midi)

Run `pip install click pretty_midi` to install these packages.


Tested with Python 3.7.4. The `resources/` folder has an original FamiStudio text file named `original.txt` that is converted to midi and then back to the FamiStudio text format.



