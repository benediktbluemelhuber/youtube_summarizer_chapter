import openai
EOS_TOKENS = [".", "!", "?"]
import re

def transcribe_audio(audio_fpath, max_snt_len=100):

    with open(audio_fpath, "rb") as audio_file:
        output = openai.Audio.transcribe("whisper-1", audio_file, file_name="audio.mp3", response_format = "srt")
        #print(result)


    def read_text_file(filepath):
        with open(filepath, 'r') as file:
            data = file.read()
        return data

    def convert_time_to_seconds(time_str):
        h, m, s = map(float, re.split('[:]', time_str))
        return h * 3600 + m * 60 + s

    # Use the function
    #output=  read_text_file('input.txt')
    print(output)
    with open("output.txt", "w") as f:
        # Write the text to the file
        f.write(output)

    # Convert SRT format into a list of dictionaries
    result = {"segments": []}
    srt_lines = output.strip().split("\n")

    i = 0
    while i < len(srt_lines):
        if ' --> ' in srt_lines[i + 1]:
            start_time_str, end_time_str = re.sub(',', '.', srt_lines[i + 1]).split(' --> ')
            start_time = convert_time_to_seconds(start_time_str)
            end_time = convert_time_to_seconds(end_time_str)

            # Accumulate all the lines of the text block.
            text_lines = []
            i += 2
            while i < len(srt_lines) and srt_lines[i].strip() != "":
                text_lines.append(srt_lines[i])
                i += 1

            segment = {
                "start": start_time,
                "end": end_time,
                "text": " ".join(text_lines)  # Join multiple lines with a space.
            }
            result["segments"].append(segment)
        else:
            print(f"Warning: Unexpected line format: {srt_lines[i + 1]}")
            i += 1
        i += 1  # To move to the next block after an empty line.

    sentences = []
    snt_start = None
    snt = ""

    for segment in result["segments"]:
        snt += f'{segment["text"]} '
        if not snt_start:
            snt_start = segment["start"]
        if (
                segment["text"].strip().split()[-1][-1] in EOS_TOKENS
                or len(snt) > max_snt_len
        ):
            sentences.append(
                {"text": snt.strip(), "start": snt_start, "end": segment["end"]}
            )
            snt_start = None
            snt = ""

    if len(snt) > 0:
        sentences.append(
            {"text": snt.strip(), "start": snt_start, "end": segment["end"]}
        )
        snt_start = None
        snt = ""

    timestamped_text = ""
    for sentence in sentences:
        timestamped_text += (
            f'{sentence["start"]} {sentence["end"]} {sentence["text"]}\n'
        )
    return timestamped_text
