from progressbar import Bar, SimpleProgress, Timer, Percentage, ETA, FormatLabel, ProgressBar as pb
import time

base_widgets = [Bar(), ' (', SimpleProgress(), ') ',
                Percentage(), ' | ', Timer(), ' | ',
                ETA(), ' | ']


def generate_bar(ln, text):
    return pb(min_value=0, max_value=ln, widgets=[FormatLabel(text), ] + base_widgets)