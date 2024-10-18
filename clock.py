from datetime import datetime as dt
import math

last_str = ""

class OverPrint:
    printing = True
    def __init__(self) -> None:
        pass

    last_nrows = None
    def _csi(values: list) -> None:
        csi_up = f"\x1B[{OverPrint.last_nrows}A"
        csi_clr= "\x1B[0K"
                
        if OverPrint.last_nrows is None:
            csi_up = ""
        else:
            if OverPrint.last_nrows > len(values):
                print(f'{csi_up}{csi_clr}')
                for r in range(1,OverPrint.last_nrows): print(f'{csi_clr}')
                
        OverPrint.last_nrows = len(values)
        print(f'{csi_up}{values[0]}{csi_clr}')
        for r in range(1, len(values)): print(f'{values[r]}{csi_clr}')

def pprint(*values: object, sep: str = " ", nl_sep: str = "\n") -> None:
    """
    Grants the ability to print on the same lines multiple times.\n
    When you are done you can use 'cprint' or 'lock' to lock the print in (so it doesn't get replaced by future pprint calls)
    """
    if OverPrint.printing:
        global last_str
        for value in values:
            if len(values) > 1:
                last_str += str(value) + str(sep) if value != values[-1] else str(value)
                OverPrint._csi(last_str.split(nl_sep))
            else:
                OverPrint._csi(str(value).split(nl_sep))

def overlay(base: str, overlay: str) -> str:
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

class Time:
    def __init__(self) -> None:
        pass

    digit = {
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

        return overlay(outer, inner)

    def analog(self, size=14):
        now = dt.now()
        h = now.hour % 12
        m = now.minute
        s = now.second
        xm = size * 2
        ym = size

        hr = self._line(xm, ym, size - 3, h * 30 + 90 if h * 30 + 180 <= 360 else (h * 30 + 90) - 360)
        min = self._line(xm, ym, size - 3, m * 6 + 90 if m * 6 + 180 <= 360 else (m * 6 + 90) - 360)
        sec = self._line(xm, ym, size - 3, s * 6 + 90 if s * 6 + 180 <= 360 else (s * 6 + 90) - 360)

        return overlay(self._analog_face(size * 2 + 1), overlay(hr, overlay(min, overlay(sec, f"{'\n'*ym}{' '*xm}+"))))

    def digital(self, spacing: int = 10) -> str:
        time = str(dt.now().strftime("%H:%M:%S"))
        ascii_time = ""
        for i in range(6):
            for s in time:
                try:
                    ascii_time += self.digit[s].split("\n")[i].ljust(spacing)
                except KeyError:
                    pass

            ascii_time += "\n"

        return ascii_time

def main():
    time = Time()

    while True:
        pprint(f"{time.analog()}\n{time.digital()}")

if __name__ == "__main__":
    main()