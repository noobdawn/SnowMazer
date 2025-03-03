from Utils.AutoUtils import *
from Utils.IntoTheVoidUtils import *

reader = easyocr.Reader(['ch_sim', 'en'], gpu=True)
text = reader.readtext('temp_cropped.png')
wave = get_wave_count(text)
print(wave)