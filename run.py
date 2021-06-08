import os
import csv
import time
import shutil
import sys
# from scipy.optimize import brute
import numpy as np
from geneticalgorithm import geneticalgorithm as ga

import Ss7Csv

global inputDir
global outputDir
global ModelNo
global Model_in
global TagGroup
global log

os.chdir(os.path.dirname(os.path.abspath(__file__)))
inputDir = "CSV_input"
outputDir = "CSV_output"
ModelNo = 0
starttime = time.time()


def MName(io):
    global ModelNo, inputDir, outputDir
    fn = "No_" + str(ModelNo).zfill(4)
    cd = os.path.dirname(os.path.abspath(__file__))
    if io == 'in':
        return os.path.join(cd, inputDir, fn+".csv")
    elif io == 'out':
        return os.path.join(cd, outputDir, fn+".csv")


def OverwriteSCMD(SCMDfile, ipath, opath):
    with open(SCMDfile, mode='r', encoding='shift-jis') as f:
        next(f)
        next(f)
        data = f.read()
    with open(SCMDfile, mode='w', encoding='shift-jis') as f:
        f.write('var string inputcsv_path = "' + ipath + '"\n')
        f.write('var string outputcsv_path = "' + opath + '"\n')
        f.write(data)


def Penalty(Ratio, ubound):
    p = 1
    for r in Ratio:
        if r > ubound:
            p = p * (r/ubound) ** 2
    return p


def Fun(x):
    global ModelNo, Model_in, TagGroup, log
    # print("x", x)
    x = x.tolist()
    x = [int(i) for i in x]
    ModelNo += 1
    Model_in.ChangeSec(x, TagGroup)
    Model_in.Copy(MName('in'))

    OverwriteSCMD(SCMDfile, MName('in'), MName('out'))
    os.system(SCMDfile)

    Model_out = Ss7Csv.outCSV(MName('out'))
    Model_out.Load()
    ResRatio = Model_out.TagGroupMaxRatio(TagGroup)
    ResWeight = Model_out.GetWeight()
    P = Penalty(ResRatio, 1.0)
    F = P * ResWeight

    log = open('log.csv', 'a')
    t = [
        '{:d}'.format(ModelNo),
        '{:.2f}'.format(ResWeight),
        '{:.2f}'.format(P),
        '{:.2f}'.format(P * ResWeight)
    ] + [
        '{:.2f}'.format(max(ResRatio))
    ]+[
        '{:.2f}'.format(i) for i in ResRatio
    ]
    csv.writer(log, lineterminator="\n").writerow(t)
    print("\n", t[:5], end='')

    return F


CSec = (
    '□-300x300x6x15', '□-300x300x8x20', '□-300x300x9x22.5',
    '□-300x300x12x30', '□-300x300x14x35',
    '□-300x300x16x40',
    '□-300x300x19x47.5'
)

GSec = (
    'SH-450x200x9x12x13', 'SH-450x200x9x16x13', 'SH-450x200x9x19x13', 'SH-450x200x9x22x13', 'SH-450x200x12x16x13', 'SH-450x200x12x19x13',
    'SH-450x200x12x22x13', 'SH-450x200x12x25x13', 'SH-450x250x9x12x13', 'SH-450x250x9x16x13', 'SH-450x250x9x19x13', 'SH-450x250x9x22x13',
    'SH-450x250x12x16x13', 'SH-450x250x12x19x13', 'SH-450x250x12x22x13', 'SH-450x250x12x25x13', 'SH-450x250x12x28x13'
)

TagGroup = (
    (['1SC01'], CSec), (['2SC01'], CSec), (['3SC01'], CSec), (['4SC01'], CSec),
    (['1SC02'], CSec), (['2SC02'], CSec), (['3SC02'], CSec), (['4SC02'], CSec),
    (['1SC03'], CSec), (['2SC03'], CSec), (['3SC03'], CSec), (['4SC03'], CSec),
    (['2SG01'], GSec), (['3SG01'], GSec), (['4SG01'], GSec), (['RSG01'], GSec),
    (['2SG02'], GSec), (['3SG02'], GSec), (['4SG02'], GSec), (['RSG02'], GSec),
    (['2SG11'], GSec), (['3SG11'], GSec), (['4SG11'], GSec), (['RSG11'], GSec)
)

SCMDfile = "CalcSingleModel.scmd"
Original = "base"
logfile = "log.csv"
# Path = os.path.join(inputDir, Original+".csv")
Path = os.path.join(os.getcwd(), Original+".csv")
Model_in = Ss7Csv.inpCSV(Path)
Model_in.Load()


if os.path.exists(logfile):
    os.remove(logfile)
    log = open(logfile, 'a')
    t = ['Model', 'Weight', 'Penalty', 'F(x)', '検定値Max', '検定値一覧']
    csv.writer(log, lineterminator="\n").writerow(t)
    print(t)

varbound = []
for tg, L in TagGroup:
    varbound.append([0, len(L)-1])
varbound = np.array(varbound)
d = len(TagGroup)

algorithm_param = {'max_num_iteration': 100,
                   'population_size': 25,
                   'mutation_probability': 0.1,
                   'elit_ratio': 0.1,
                   'crossover_probability': 0.5,
                   'parents_portion': 0.3,
                   'crossover_type': 'uniform',
                   'max_iteration_without_improv': 50,
                   }

model = ga(function=Fun, dimension=d, variable_type='int',
           variable_boundaries=varbound,
           algorithm_parameters=algorithm_param,
           function_timeout=10800.0)
model.run()
solution = model.output_dict
print(type(solution))
print(solution)
convergence = model.report
print(type(convergence))
print(convergence)

with open("report.csv", 'w') as report:
    writer = csv.writer(report, lineterminator="\n")
    writer.writerow(['variable'])
    writer.writerow(solution['variable'])
    writer.writerow(['function'])
    writer.writerow([solution['function']])
    writer.writerow(['convergence'])
    for s in convergence:
        report.write(str(s)+"\n")

x = solution['variable']
Model_in.ChangeSec(x, TagGroup)
Model_in.Copy('solution.csv')

print("time", time.time()-starttime)
