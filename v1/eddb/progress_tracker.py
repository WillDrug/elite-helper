from progressbar import Bar, SimpleProgress, Timer, Percentage, ETA, FormatLabel, ProgressBar as pb

base_widgets = [Bar(), ' (', SimpleProgress(), ') ',
                Percentage(), ' | ', Timer(), ' | ',
                ETA(), ' | ']


def generate_bar(ln, text, redirect_stdout=False):
    return pb(min_value=0, max_value=ln, widgets=[FormatLabel(text), ] + base_widgets, redirect_stdout=redirect_stdout)

