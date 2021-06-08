import os
import csv
import random
import pandas as pd


class CSV:
    def __init__(self, path):
        self.file = open(path, 'r', encoding='CP932')
        self.reader = csv.reader(self.file)
        self.preloaded = False
        self.datadic = {}

    def __del__(self):
        self.file.close()

    def PreLoad(self):
        self.preloaded = True

        self.NameList = []
        self.RowList = []
        self.SeekList = []
        # print(row)

        i = 0
        while True:
            s = self.file.tell()
            row = self.file.readline()
            i += 1
            if row:
                # row = row.splitlines()[0]
                if 'name=' in row:
                    n = row.splitlines()[0].split(',')[0]
                    self.NameList.append(n.replace('name=', ''))
                    self.RowList.append(i)
                    self.SeekList.append(s)
            else:
                self.NameList.append('END')
                self.RowList.append(i)
                self.SeekList.append(s)
                break
        # print(self.NameList)

    def Load(self, name):
        if not self.preloaded:
            self.PreLoad()
        for n in name:
            indx = [i for i, s in enumerate(self.NameList) if s == n]
            data = []
            for i in indx:
                # print(indx)
                self.file.seek(self.SeekList[i])
                for row in self.reader:
                    if not all([x == '' for x in row]):
                        data.append(row)
                    else:
                        break
            self.datadic[n] = data


class inpCSV(CSV):
    def Load(self):
        super().Load(['S柱断面', 'S梁断面'])

    def SelectSec(self, x, tag, TagGroup):
        sec = ''
        for i, (TagG, SecList) in enumerate(TagGroup):
            # print(i, x[i], TagG, SecList)
            if tag in TagG:
                sec = SecList[int(x[i])]
        return sec

    def ChangeSec(self, x, TagGroup):
        for GorC in ['S柱断面', 'S梁断面']:
            isdata = False
            for i, d in enumerate(self.datadic[GorC]):
                if d[0] == '<data>':
                    isdata = True
                    continue
                if isdata:
                    tag = d[2]+d[1]
                    sec = self.SelectSec(x, tag, TagGroup)
                    # print('debug', tag, sec)
                    if GorC == 'S柱断面':
                        if not sec == '':
                            d[4] = sec
                    if GorC == 'S梁断面':
                        for ii in [6, 7, 8]:
                            if not sec == '':
                                d[ii] = sec

    def Copy(self, path):
        self.file.seek(0)
        fo = open(path, 'w', encoding='CP932')

        for i in range(1, self.RowList[-1]+1):
            row = self.file.readline()
            bc = self.NameList.index('S柱断面')
            bg = self.NameList.index('S梁断面')
            if self.RowList[bc] <= i < self.RowList[bc+1]:
                if i == self.RowList[bc]:
                    csv.writer(fo, lineterminator="\n").writerows(
                        self.datadic['S柱断面'])
                    fo.write("\n")
            elif self.RowList[bg] <= i < self.RowList[bg+1]:
                if i == self.RowList[bg]:
                    csv.writer(fo, lineterminator="\n").writerows(
                        self.datadic['S梁断面'])
                    fo.write("\n")
            else:
                fo.write(row)
        fo.close()


class outCSV(CSV):
    def Load(self):
        super().Load(['S柱検定比一覧', 'S梁検定比一覧', '地震用重量'])

    def LoadMaxRatio(self):
        self.TagMaxRatio = {}
        for GorC in ['S柱検定比一覧', 'S梁検定比一覧']:
            isdata = False
            for i, d in enumerate(self.datadic[GorC]):
                if d[0] == '<data>':
                    isdata = True
                    continue
                if isdata:
                    tag = d[1]
                    # 曲げ、組み合わせのみ
                    # print(d)
                    if GorC == 'S柱検定比一覧':
                        r = [float(s) for s in d[7:9]]
                    elif GorC == 'S梁検定比一覧':
                        r = [float(s) for s in d[2:5]]
                    # print(r)
                    self.TagMaxRatio[tag] = max(r)

    def TagGroupMaxRatio(self, TagGroup):
        self.LoadMaxRatio()
        res = []
        for TGG in TagGroup:
            tgl = TGG[0]
            maxratio = 0
            for t in tgl:
                maxratio = max(maxratio, self.TagMaxRatio[t])
            res.append(maxratio)
        return res

    def GetWeight(self):
        self.weight = 0
        isdata = False
        for i, d in enumerate(self.datadic['地震用重量']):
            if d[0] == '<data>':
                isdata = True
                continue
            if isdata:
                self.weight += float(d[3])
        return self.weight
