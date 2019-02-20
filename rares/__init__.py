import csv

class RareLoader:
    def __init__(self):
        f = open('rares/reference.tsv', 'r', encoding='utf-8')  # todo, fix to os.base
        self.header = f.readline().split(';')
        # station generation here

        for line in f.readlines():
            entry = dict()
            for e, k in zip(line.split(','), self.header):
                entry[k] = e
            self.reference.append(entry)

        f.close()
