import pytest
from cycle_training_planner import Plan

'''
 planName                = "Test Plan"
    currentWeeklyMileage    = 0
    targetDistance          = 100
    targetTotalTime         = 10
    targetTotalClimb        = 1000
    targetMaxInclinePercentage = 10
    startWeek               = 1
    targetWeek              = 20
    targetYear              = 2022
    restCycleWeeks          = 4
    restPercentage          = 50
    taperWeeks              = 2
    plateauWeeks            = 3
    taperPercentage         = 75
    targetRidePercentage    = 75
    targetWeekPercentage    = 150
    currentStandardCommute  = 10
    longCommute             = 20
    maxLongCommutes         = 2
    commutesPerWeek         = 10
    secondRidePercentage    = 20
    stepAfterRest           = False
    '''

class TestPlanner():
    def test__planname(self):
        p = Plan()
        #p.plan()
        assert p.planName == "Test Plan"
        