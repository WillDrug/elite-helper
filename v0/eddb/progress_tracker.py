from progressbar import Bar, SimpleProgress, Timer, Percentage, ETA, FormatLabel, ProgressBar as pb
import time

base_widgets = [Bar(), ' (', SimpleProgress(), ') ',
                Percentage(), ' | ', Timer(), ' | ',
                ETA(), ' | ']


def generate_bar(ln, text):
    return pb(min_value=0, max_value=ln, widgets=[FormatLabel(text), ] + base_widgets)

def track_job(job, name, total, update_interval=3):
    mbar = generate_bar(total, name)
    mbar.start()
    while job._number_left > 0:
        mbar.update(total - job._number_left)
        time.sleep(update_interval)
    mbar.finish()