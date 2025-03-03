from Utils.AutoUtils import *
from Utils.SB_Stage import *

hwnd = get_window_handle('尘白禁区')
reader = easyocr.Reader(['ch_sim', 'en'], gpu=True)
STAGES = {}
STAGES[SB_STAGE_LOGIN] = SBStageLogin()
STAGES[SB_STAGE_MAIN] = SBStageMain()
STAGES[SB_STAGE_SHOP] = SBStageShop()
Data = get_data_class(hwnd, reader, STAGES)

img = capture_frame(get_window_rect(Data.hwnd))

current_stage = None
for stage_id, stage in Data.STAGES.items():
    if stage.IsMe(img):
        current_stage = stage
        break
if current_stage is None:
    raise Exception('未知界面')
print(current_stage.name())
current_stage.execute()