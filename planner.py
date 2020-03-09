#input currentWeeklyMileage
#input currentStandardCommute
#input targetDistance
#input targetTotalTime
#input targetDate
#input restCycleWeeks
#input weekStart
import math

currentWeeklyMileage    = 100
targetDistance          = 150
currentStandardCommute  = 6
targetTotalTime         = 16
startWeek               = 11
targetWeek              = 21
restCycleWeeks          = 3
restPercentage          = 70
taperWeeks              = 1
plateauWeeks            = 0
taperPercentage         = 50
targetRidePercentage    = 66.66667
targetWeekPercentage    = 166.6667
longCommute             = 20
maxLongCommutes         = 2
commutesPerWeek         = 10
secondRidePercentage    = 50

totalWeeks = (targetWeek - startWeek) + 1
restWeeks = round((totalWeeks - (plateauWeeks+taperWeeks)) / restCycleWeeks)
steps = (totalWeeks - (plateauWeeks+taperWeeks)) - (2*restWeeks)

stepDistance = ((targetDistance * (targetWeekPercentage/100))- currentWeeklyMileage) / steps
print("totalWeeks", totalWeeks, "restWeeks", restWeeks, "Steps", steps, "Step Distance", stepDistance)

currentDistance = currentWeeklyMileage
step = 0
thisWeekDistance = currentDistance
for i in range(1, totalWeeks+1):
    longCommutes = math.ceil(i/(totalWeeks/maxLongCommutes))
    restWeek = False
    week = startWeek - 1 + i
    #print(i, week)
    if (i <= totalWeeks - (plateauWeeks+taperWeeks)):
        if(i % restCycleWeeks ):
            if(i % restCycleWeeks > 1):
                step += 1
                currentDistance += stepDistance
            thisWeekDistance = round(currentDistance)
        else:
            restWeek = True
            thisWeekDistance = round(currentDistance * (restPercentage / 100))
    elif (i > (totalWeeks - taperWeeks)):
        restWeek = True
        thisWeekDistance = round(currentDistance * (taperPercentage/100))
    else:
        if(i % restCycleWeeks ):
            thisWeekDistance = round(currentDistance)
        else:
            restWeek = True
            thisWeekDistance = round(currentDistance * (restPercentage / 100))

    if(restWeek):
        commuteDist = commutesPerWeek * currentStandardCommute
    else:
        commuteDist = (currentStandardCommute * (commutesPerWeek - longCommutes )) + (longCommute * longCommutes)

    nonCommuteDist = max(0, thisWeekDistance-commuteDist)

    mainRide = round(min(((targetRidePercentage/100)*targetDistance),nonCommuteDist * (100/(100 + secondRidePercentage))))
    secondRide = round(mainRide*(secondRidePercentage/100))
    leftOvers = max(0,nonCommuteDist - (mainRide+secondRide))


    print(week, "Dist", thisWeekDistance, "Commute", commuteDist,
    "Big Ride",mainRide, "Second Ride", secondRide, "Left Overs",leftOvers)
