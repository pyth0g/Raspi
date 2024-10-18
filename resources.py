from datetime import datetime as dt
import calendar as _c
import math

class Digital:
    def time(time: str | None = None) -> str:
        ascii = {
  "0": r"""   ___
  / _ \  
 | | | | 
 | | | | 
 | |_| | 
  \___/  """,

  "1": r"""  __     
 /_ |    
  | |    
  | |    
  | |    
  |_|""",

  "2": r"""  ___
 |__ \   
    ) |  
   / /   
  / /_   
 |____|""",

  "3": r"""  ____
 |___ \  
   __) | 
  |__ <  
  ___) | 
 |____/""",

  "4": r"""  _  _   
 | || |  
 | || |_ 
 |__   _|
    | |  
    |_|  """,

  "5": r"""  ______
 | ____| 
 | |__   
 |___ \  
  ___) | 
 |____/""",

  "6": r"""    __
   / /   
  / /_   
 | '_ \  
 | (_) | 
  \___/ """,

  "7": r"""  ______
 |____  |
     / / 
    / /  
   / /   
  /_/""",

  "8": r"""   ___
  / _ \  
 | (_) | 
  > _ <  
 | (_) | 
  \___/""",

  "9": r"""   ___
  / _ \  
 | (_) | 
  \__, | 
    / /  
   /_/ """,

   ":":"""  
  _ 
 (_)
    
  _ 
 (_)"""
        }
        
        content = ""
        time = str(dt.now().strftime("%H:%M:%S")) if not time else time
        
        for index in range(6):
            for char in time:
                content += ascii[char].split("\n")[index].ljust(10)

            content += "\n"

        return content

class Clock:
    def overlay(self, base: str, overlay: str) -> str:
        base_lines = base.splitlines()
        overlay_lines = overlay.splitlines()

        result_lines = []

        max_lines = max(len(base_lines), len(overlay_lines))

        for i in range(max_lines):
            base_line = base_lines[i] if i < len(base_lines) else ""
            overlay_line = overlay_lines[i] if i < len(overlay_lines) else ""

            base_line_list = list(base_line)
            overlay_line_list = list(overlay_line)

            max_length = max(len(base_line_list), len(overlay_line_list))

            for j in range(max_length):
                if j < len(overlay_line_list) and overlay_line_list[j] != ' ':
                    if j < len(base_line_list):
                        base_line_list[j] = overlay_line_list[j]
                    else:
                        base_line_list.append(overlay_line_list[j])

            result_lines.append("".join(base_line_list))

        return "\n".join(result_lines)

    def _line(self, x2: int, y2: int, length: int, angle_degrees: int):
        l = ""
        angle_radians = math.radians(angle_degrees)
        
        x1 = x2 - int(round(length * math.cos(angle_radians)))
        y1 = y2 - int(round(length * math.sin(angle_radians)))

        dx = abs(x2 - x1)
        dy = abs(y2 - y1)
        sx = 1 if x1 < x2 else -1
        sy = 1 if y1 < y2 else -1
        err = dx - dy

        grid = [[' ' for _ in range(2 * x2 + 1)] for _ in range(2 * y2 + 1)]

        while True:
            if dx == 0:
                ch = '|'
            elif dy == 0:
                ch = '―'
            elif abs(dy / dx) > 1.5:
                ch = '|'
            elif abs(dy / dx) < 0.5:
                ch = '―'
            else:
                if sx == sy:
                    ch = '\\'
                else:
                    ch = '/'

            grid[y1][x1] = ch
            
            if x1 == x2 and y1 == y2:
                break
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x1 += sx
            if e2 < dx:
                err += dx
                y1 += sy

        for row in grid:
            l += ''.join(row) + "\n"

        return l


    def _analog_face(self, size: int):
        diameter = size
        radius = diameter / 2 - 0.5
        r_outer = (radius + 0.5)**2
        r_inner = (radius - 0.5)**2

        circle = ""

        for i in range(diameter):
            y = (i - radius)**2
            for j in range(diameter):
                x = (j - radius)**2
                if r_inner <= x + y <= r_outer:
                    circle += f"# "
                else:
                    circle += " " * 2
            circle += '\n'

        outer = circle.rstrip()

        radius = diameter / 2
        circle = [["  " for _ in range(diameter)] for _ in range(diameter)]

        for hour in range(12):
            angle = 2 * math.pi * (hour / 12) - math.pi / 2 + 0.5
            x = int(radius + (radius - 2) * math.cos(angle))
            y = int(radius + (radius - 2) * math.sin(angle))

            circle[y][x] = f"{hour + 1:2}"

        circle = "\n".join("".join(row) for row in circle)
        inner = circle.rstrip()

        return self.overlay(outer, inner)

    def clock(self, size=14) -> str:
        now = dt.now()
        h = now.hour % 12
        m = now.minute
        s = now.second
        xm = size * 2
        ym = size

        hr = self._line(xm, ym, size - 3, h * 30 + 90 if h * 30 + 180 <= 360 else (h * 30 + 90) - 360)
        min = self._line(xm, ym, size - 3, m * 6 + 90 if m * 6 + 180 <= 360 else (m * 6 + 90) - 360)
        sec = self._line(xm, ym, size - 3, s * 6 + 90 if s * 6 + 180 <= 360 else (s * 6 + 90) - 360)

        nl = '\n'
        return self.overlay(self._analog_face(size * 2 + 1), self.overlay(hr, self.overlay(min, self.overlay(sec, f"{nl*ym}{' '*xm}+"))))

class Calendar:
    def calendar(month: int = dt.now().month, year: int = dt.now().year, weird_display: bool = False, boxed: bool = True, highlight: list = [dt.now().day], highlight_text: list[str, str] = [">", ""], size: int = 3) -> str:
        days = {0: 'Monday',
                1: 'Tuesday',
                2: 'Wednesday',
                3: 'Thursday',
                4: 'Friday',
                5: 'Saturday',
                6: 'Sunday'}
        
        _box = lambda t: f"┌{'─'*len(t) if not weird_display else '─'*(len(t) - 4)}┐\n│{t}│\n└{'─'*len(t) if not weird_display else '─'*(len(t) - 4)}┘" # Box to box in elements if boxed is true

        s_day, count = (eval(str(_c.monthrange(year, month)[0])), _c.monthrange(year, month)[1]) # Set the start day (0-6) and the number of days in month
        
        t_day = 1 # Day in month
        w_day = 0 # Day in week wrap at 5+
        l = 0 # Day counter in week wrap at 7+

        # Make the size be in a reasonable boundary
        if size < 2:
            size = 2
        
        if size > 8:
            size = 8

        # Box in the month name if boxed is true
        s = len(' '.join([i[:size] for i in list(days.values())]))

        if boxed:
            cal_str = _box(f"{_c.month_name[month]} {year}".center(s)) # Define cal_str with month boxed
        else:
            cal_str = f"{_c.month_name[month]} {year}".center(s) # Define cal_str

        # Add monday thru sunday truncated to size (size 3: Mon, size 2: Mo, ...)
        cal_str += f"\n{' '.join([i[:size] for i in list(days.values())])}\n"

        # Add the days
        for day in range(1, count + s_day + 1):
            if l >= 7:
                cal_str += "\n" # Add new line if the week is over
                l = 0

            if day >= s_day + 1: # If the day is in this month
                if t_day in highlight: # If the day should be highlighted
                    cal_str += highlight_text[0]

                    cal_str += str(t_day).center(size + 1)[1:] # The day

                else:
                    cal_str += str(t_day).center(size + 1)

                # End it
                if t_day in highlight:
                    cal_str += highlight_text[1]

                t_day += 1

            else:
                cal_str += " " * (size + 1) # Empty if day isn't in month
                
            w_day = w_day + 1 if w_day < 6 else 0 # Increment and reset the week day.

            l += 1

        return cal_str
    
def cpu_temp():
    with open("/sys/class/thermal/thermal_zone0/temp") as f:
        cpu_temp = f.read()

    return round(float(cpu_temp)/1000, 2)