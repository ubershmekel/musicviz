import subprocess
import sys
import os

from PIL import Image
from PIL import ImageEnhance
import numpy as np
import scipy.io.wavfile
import tqdm

output_folder = 'out'
image_fname = 'IMG_20160828_100914.small.jpg'
wav_fname = 'LS100566.cut.wav'

if not os.path.exists(output_folder):
    os.mkdir(output_folder)

print('reading wav file')
samples_per_second, wav_array = scipy.io.wavfile.read(wav_fname)

window_seconds = 0.1 # seconds
fps = 1.0 / window_seconds
samples_per_window = samples_per_second * window_seconds

print('analyzing peaks')
i = 0
#mono = [np.mean(pair) for pair in wav_array]
flat = wav_array.flatten()
# int to avoid int16 wrapping
sample_min = int(np.min(flat))
sample_max = int(np.max(flat))
sample_peak_to_peak = sample_max - sample_min

print('analyzing windows')
averages = []
start = 0
while start < len(wav_array):
    slice = wav_array[start:start+samples_per_window]
    #avg = np.average(slice)
    # float to avoid overflow
    floats = slice.flatten().astype(float)
    avg = np.sqrt(np.mean(np.square(floats)))
    if np.isnan(avg):
        print('bug?')
    averages.append(avg)
    i += 1
    start = i * samples_per_window
    if i % 1000 == 0:
        sys.stdout.write('.')

print('')
print('outputting images')
sample_min = min(averages)
sample_max = max(averages)
sample_peak_to_peak = sample_max - sample_min
width, height = 16, 16
pixel_count_per_image = width * height
top = 0
base_image = Image.open(image_fname)
img = base_image.copy()
im_data = np.array(base_image)#base_image.getdata()
percent_step = 1.0 / len(averages)
pixel_count = len(im_data)
for j, avg in enumerate(tqdm.tqdm(averages)):
    normal_val = (avg - sample_min) * 1.0 / sample_peak_to_peak
    pixel_val = int(normal_val * 254.0)
    if pixel_val > top:
        top = pixel_val
        print(top)
    #data = [ (pixel_val, pixel_val, pixel_val) ] * pixel_count_per_image
    #img = Image.new('RGB', (width, height))
    #img.putdata(data)
    new_data = (np.array(im_data) * normal_val).astype(np.uint8)
    offset = pixel_count * percent_step * j
    new_data[:offset] = im_data[:offset]
    #shaped = new_data.astype(np.int8).reshape(base_image.shape + (base_image.bands,))
    #img.putdata(im_data)
    img = Image.fromarray(new_data)
    #img.fromarray(new_data)
    img.save(output_folder + '/image%05d.jpg' % j)

#  -vf scale=320:240
ffmpeg_fmt = 'ffmpeg -y -i {wav_fname} -framerate {fps} -i {output_folder}/image%05d.jpg output.mp4'
cmd = ffmpeg_fmt.format(wav_fname=wav_fname,
                        output_folder=output_folder,
                        fps=fps)
subprocess.check_call(cmd)

