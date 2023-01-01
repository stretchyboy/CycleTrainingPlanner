import argparse
from CycleTrainingPlanner import Plan

'''
parser = argparse.ArgumentParser(prog='Prettify GitHub Log', description='Make git logs easier for use in scenarios when communicating the progress of a project to none experts.')
parser.add_argument("-r", "--repo", default='https://github.com/UTCSheffield/lumpy_log.git')
parser.add_argument("-o", "--outputfolder", default="output")
parser.add_argument("-f", "--from", dest="from_commit", help="Commit to start at")
parser.add_argument("-t", "--to", dest="to_commit", help="Commit to end at")
parser.add_argument("-a", "--allbranches", action="store_true")
parser.add_argument("-v", "--verbose", action="store_true")
parser.add_argument("-b", "--branch", dest="branch")
parser.add_argument("--force", action="store_true")
parser.add_argument("-d", "--dryrun", action="store_true")
args = parser.parse_args()

'''

p = Plan()
p.currentWeeklyDistance    = 129
#p.restCycleWeeks = 3
#p.stepAfterRest = True
p.startWeek               = 25
p.targetWeek              = 35
p.currentStandardCommute  = 8
p.longCommute             = 13
p.maxLongCommutes         = 2
p.commutesPerWeek         = 10
p.secondRidePercentage    = 30
p.plateauWeeks            = 1
p.targetWeekPercentage    = 125
p.targetYear              = 2022

p.plan()
print("Weeks", p.weeks)
#p.requests(False)
