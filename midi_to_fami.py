import click
import pretty_midi
import os

def tab(i):
    return '\t' * i


prog_to_channel_type = {
    80: 'Square1',
    81: 'Square2',
    38: 'Triangle',
    121: 'Noise'
}

name_to_prog = {
    'p1': 80,
    'p2': 81,
    'tr': 38,
    'no': 121
}

# assign one instrument to each track
prog_to_duty_name = {80: 0, 81: 1, 38: 2, 121: 3}


def midi_to_fami(input_midi_file,
                 output_fami_file,
                 raise_triangle_volume=False,
                 lower_noise_volume=False):
    try:
        midi = pretty_midi.PrettyMIDI(input_midi_file)
    except Exception as e:
        print(f'Error with file {input_midi_file}')
        print(e)
        raise ValueError

    with open(output_fami_file, 'w') as of:
        header = f'Project Version="2.3.1" TempoMode="FamiStudio" Name="{input_midi_file}" Author="<?>" Copyright=""\n'
        of.write(header)

        # instrument names
        of.write('\tInstrument Name="Duty 0"\n')
        of.write('\tInstrument Name="Duty 1"\n')
        of.write('\tInstrument Name="Duty 2"\n')
        of.write('\tInstrument Name="Duty 3"\n')

        # compute num patterns
        # TODO adapt
        of.write(
            tab(1) +
            'Song Name="Song 3" Length="29" LoopPoint="0" PatternLength="16" BeatLength="4" NoteLength="16"\n'
        )

        for instrument_index, instrument in enumerate(midi.instruments):
            try:
                # if the names are correct, set the correct instrument program
                instrument.name = instrument.name.rstrip('\x00')
                if instrument.name in name_to_prog:
                    instrument.program = name_to_prog[instrument.name]
                    # Ableton tends to add these characters at the end

                channel_type = prog_to_channel_type[instrument.program]
                duty_name = prog_to_duty_name[instrument.program]
            except KeyError:
                raise KeyError(
                    f"Instrument {instrument.program} has not been registered in NESDataset.instruments_id. "
                    f"the instruments of the current MIDI file are {', '.join([i.program for i in midi.instruments])}."
                )

            of.write(tab(2) + f'Channel Type="{channel_type}"\n')

            current_pattern_time = -256
            current_pattern_index = 0
            write_stop = False

            for n in instrument.notes:
                # cast to the nearest integer
                start = int(n.start * 256 / 4 + 0.5)
                end = int((n.start + n.duration) * 256 / 4 + 0.5)

                if write_stop:
                    # assert end_previous_note <= start
                    if end_previous_note > start:
                        end_previous_note = start
                        print(f'Note overlap in voice {channel_type}')
                    if end_previous_note == start:
                        write_stop = False

                if write_stop:
                    # Pattern header if necessary
                    if end_previous_note >= current_pattern_time + 256:
                        current_pattern_time += 256
                        current_pattern_index += 1
                        of.write(
                            tab(3) +
                            f'Pattern Name="Pattern {current_pattern_index}"\n'
                        )

                    # write stop event
                    instant_time = end_previous_note - current_pattern_time
                    of.write(
                        tab(4) + f'Note Time="{instant_time}" Value="Stop"\n')

                # write current note
                # Pattern header if necessary
                if start >= current_pattern_time + 256:
                    current_pattern_time += 256
                    current_pattern_index += 1
                    of.write(
                        tab(3) +
                        f'Pattern Name="Pattern {current_pattern_index}"\n')
                instant_time = start - current_pattern_time
                note_name = pretty_midi.note_number_to_name(n.pitch)

                if raise_triangle_volume and channel_type == 'Triangle':
                    volume = max(n.velocity, 10)
                elif lower_noise_volume and channel_type == 'Noise':
                    volume = min(n.velocity, 7)
                else:
                    volume = n.velocity

                of.write(
                    tab(4) +
                    f'Note Time="{instant_time}" Value="{note_name}" Instrument="Duty {duty_name}" Volume="{volume}"\n'
                )
                end_previous_note = end
                write_stop = True

            # write last stop
            if end_previous_note == current_pattern_time + 256:
                write_stop = False

            if write_stop:
                # Pattern header if necessary
                if end_previous_note >= current_pattern_time + 256:
                    current_pattern_time += 256
                    current_pattern_index += 1
                    of.write(
                        tab(3) +
                        f'Pattern Name="Pattern {current_pattern_index}"\n')

                # write stop event
                instant_time = end_previous_note - current_pattern_time
                of.write(tab(4) + f'Note Time="{instant_time}" Value="Stop"\n')
            # Write pattern instances
            for pattern_time_index in range(current_pattern_index):
                of.write(
                    tab(3) +
                    f'PatternInstance Time="{pattern_time_index}" Pattern="Pattern {pattern_time_index + 1}"\n'
                )

        of.write(tab(2) + f'Channel Type="DPCM"\n')


@click.command()
@click.argument('midi_file', type=click.Path(exists=True))
@click.argument('output_famistudio_txt_file', default=None, required=False)
def cli(midi_file, output_famistudio_txt_file):
    if output_famistudio_txt_file is None:
        dir, file = os.path.split(midi_file)
        basename = os.path.splitext(file)[0]
        output_famistudio_txt_file = os.path.join(dir, f'{basename}.txt')
    midi_to_fami(input_midi_file=midi_file,
                 output_fami_file=output_famistudio_txt_file,
                 raise_triangle_volume=False,
                 lower_noise_volume=False)


if __name__ == "__main__":
    cli()
