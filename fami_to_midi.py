import pretty_midi
import click
import os
import shutil


def fami_to_mid(input_txt_file, output_mid_file):
    """
    Returns the duration of the track
    """
    f = open(input_txt_file, 'r')
    d = f.read()
    f.close()
    d = d.replace('\t', '')
    channels = d.split('Channel Type')

    channels_list = []
    instances_list = []
    for i, channel in enumerate(channels):
        patterns = channel.split('Pattern Name')
        patterns_list = []
        instances = {}
        for j, pattern in enumerate(patterns):
            pattern_list = []
            notes = pattern.split('\n')
            for note in notes:
                if note.startswith('Note ') or note.startswith('PatternInstance '):
                    if note.startswith('Note '):
                        params_raw = note.split('Note ')[1] + '\n'
                    else:
                        params_raw = note.split('PatternInstance ')[1] + '\n'
                    open_value = False
                    temp = ''
                    params = []
                    for c in params_raw:
                        if c == '"':
                            if open_value:
                                open_value = False
                            else:
                                open_value = True
                        if c in [' ', '\n'] and not open_value:
                            params.append(temp)
                            temp = ''
                        else:
                            temp += c
                    if note.startswith('Note '):
                        notes_values = []
                        for param in params:
                            key, value = param.split('=')
                            value = value[1:-1]
                            notes_values.append((key, value))
                        pattern_list.append((pattern_name, notes_values))
                    else:
                        instance = {}
                        for param in params:
                            key, value = param.split('=')
                            value = value[1:-1]
                            instance[key] = value
                        instances[instance['Pattern']] = instance
                else:
                    if note.startswith('="Pattern '):
                        pattern_name = note[2:-1]
            patterns_list.append(pattern_list)
        channels_list.append(patterns_list)
        instances_list.append(instances)

    values_table = {
        'C': 0,
        'C#': 1,
        'D': 2,
        'D#': 3,
        'E': 4,
        'F': 5,
        'F#': 6,
        'G': 7,
        'G#': 8,
        'A': 9,
        'A#': 10,
        'B': 11
    }

    notes_times = []
    for c in channels_list:
        for p in c:
            for name, n in p:
                time = None
                for k, v in n:
                    if k == 'Time':
                        time = v
                    if k == 'Value':
                        notes_times.append(time)

    # Average Volumes
    notes_volumes = []
    current_volume = 11
    was_stop = True
    num_events = 0
    volume = 0
    for c in channels_list:
        for p in c:
            for name, n in p:
                # create dict from list of key values
                d = {}
                for k, v in n:
                    d[k] = v

                # end of note
                if 'Value' in d:
                    # TWO AGGREGATION METHODS:
                    prev_volume = None if was_stop else int(volume)
                    # prev_volume = None if was_stop else int(volume / num_events)

                    notes_volumes.append(prev_volume)
                    volume = 0
                    num_events = 0
                    if not d['Value'] == 'Stop':
                        was_stop = False

                # means it's not a Stop or other: aggregate
                if 'Volume' in d:
                    v = int(d['Volume'])
                    # TWO AGGREGATION METHODS:
                    volume = max(v, volume)
                    # volume += v
                    current_volume = v
                    num_events += 1
                else:

                    if ('Value' in d):
                        # if it's a true note, but without volume change or indication
                        if (not d['Value'] == 'Stop'):
                            # TWO AGGREGATION METHODS:
                            volume = max(current_volume, volume)
                            # volume += current_volume
                            num_events += 1
                            was_stop = False
                        else:
                            was_stop = True

    # Write midi

    # Constants:
    # channel_index_to_prog = {1: 80, 2: 81, 3: 38, 4: 121}
    # prog_to_instrument_name = {80: 'p1', 81: 'p2', 38: 'tr', 121: 'no'}
    channel_index_to_prog = {1: 80,
                             2: 81,
                             3: 38,
                             4: 121,
                             5: 122,
                             6: 82,
                             7: 83,
                             8: 84}
    prog_to_instrument_name = {80: 'p1', 81: 'p2',
                               38: 'tr', 121: 'no',
                               122: 'dpcm',
                               82: 'p12',
                               83: 'p22',
                               84: 'p32'
                               }
    # Midi
    midi = pretty_midi.PrettyMIDI(initial_tempo=120, resolution=22050)
    current_note = 0
    max_end = 0
    for channel_index, c in enumerate(channels_list):

        if channel_index not in channel_index_to_prog:
            continue
        # Instrument
        prog = channel_index_to_prog[channel_index]
        instrument_name = prog_to_instrument_name[prog]
        instrument_notes = []
        instrument = pretty_midi.Instrument(program=prog,
                                            name=instrument_name,
                                            is_drum=(prog >= 112))

        insts = instances_list[channel_index]
        for i, p in enumerate(c):
            for note_index, (name, n) in enumerate(p):
                inst = insts[name]
                inst_time = int(inst['Time']) * 256

                time = 0
                value = None

                # create dict from list of key values
                d = {}
                for k, v in n:
                    d[k] = v

                if 'Time' in d:
                    v = d['Time']
                    time = int(v) + inst_time
                    try:
                        time_end = int(
                            notes_times[current_note + 1]) + inst_time
                        length = time_end - time
                        if length < 0:
                            length = time_end - (time - 256)
                    except:
                        length = 1
                    try:
                        volume = notes_volumes[current_note + 1]
                        if volume is not None:
                            last_volume = volume
                    except:
                        # TODO pb with the last event
                        # print('Should only be the last character')
                        volume = last_volume

                if 'Value' in d:
                    current_note += 1
                    v = d['Value']
                    if v == 'Stop':
                        value = None
                    else:
                        value = values_table[v[0:-1]] + 12 * (int(v[-1]) + 1)
                # TODO never used
                # elif k == 'FinePitch':
                #     pitch = -(int(v) / 128) * 100 * 12
                if (not value is None):
                    time = float(time) / 256 * 4
                    length = float(length) / 256 * 4
                    note = pretty_midi.Note(
                        velocity=volume,
                        start=time,
                        end=time + length,
                        pitch=value
                    )

                    instrument_notes.append(note)
                    if time + length > max_end:
                        max_end = time + length

        instrument.notes = instrument_notes
        midi.instruments.append(instrument)

    ts = pretty_midi.TimeSignature(4, 4, 0)
    eos = pretty_midi.TimeSignature(1, 1, max_end)
    midi.time_signature_changes.extend([ts, eos])

    midi.write(output_mid_file)
    return max_end


@click.command()
@click.argument('famistudio_txt_file', type=click.Path(exists=True))
@click.argument('output_midi_file', default=None, required=False)
def cli(famistudio_txt_file, output_midi_file):
    if output_midi_file is None:
        dir, file = os.path.split(famistudio_txt_file)
        basename = os.path.splitext(file)[0]
        output_midi_file = os.path.join(dir, f'{basename}.mid')
    fami_to_mid(
        input_txt_file=famistudio_txt_file,
        output_mid_file=output_midi_file
    )


if __name__ == "__main__":
    cli()
