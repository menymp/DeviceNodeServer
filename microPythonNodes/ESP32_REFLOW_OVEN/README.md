This is a project related to a reflow oven in wait to build

thanks to BetaRavener for the excelent max6675 driver https://github.com/BetaRavener/micropython-hw-lib/blob/master/MAX6675/max6675.py
thanks to rdagger for the excelent ili9341 tft driver https://github.com/rdagger/micropython-ili9341/tree/master

thanks to dukeduck1984 for the excelent reflow micropython project, more at https://github.com/dukeduck1984/uReflowOven-Esp32-Micropython

Mqtt objetives

oven state (self.oven_state in oven control)
elapsed time (UI sets to set_timer_text, called by _elapsed_timer_update in oven_control)
ssid pwd UI configs

https://www.elecrow.com/wiki/index.php?title=LVGL_ESP32_Display_Tutorial-A_Step-by-Step_Guide_to_LVGL_GUI_Development