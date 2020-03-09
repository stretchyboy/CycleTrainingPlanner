#input currentWeeklyMileage
#input currentStandardCommute
#input targetDistance
#input targetTotalTime
#input targetDate
#input restCycleWeeks
#input weekStart
import math
import requests

currentWeeklyMileage    = 100
targetDistance          = 150
currentStandardCommute  = 6
targetTotalTime         = 16
startWeek               = 11
targetWeek              = 21
restCycleWeeks          = 3
restPercentage          = 70
taperWeeks              = 2
plateauWeeks            = 1
taperPercentage         = 75
targetRidePercentage    = 66.66667
targetWeekPercentage    = 130
longCommute             = 20
maxLongCommutes         = 1
commutesPerWeek         = 10
secondRidePercentage    = 33.333
stepAfterRest           = True

totalWeeks = (targetWeek - startWeek) + 1
restWeeks = round((totalWeeks - (plateauWeeks+taperWeeks)) / restCycleWeeks)
if stepAfterRest:
    steps = (totalWeeks - (plateauWeeks+taperWeeks)) - restWeeks
else:
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
            if(stepAfterRest or (i % restCycleWeeks > 1)):
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


    print(i, week, "Dist", thisWeekDistance, "Commute", commuteDist,
    "Big Ride",mainRide, "Second Ride", secondRide, "Left Overs",leftOvers)

    #print(i, week, "Dist", thisWeekDistance*1.6, "Commute", commuteDist*1.6,
    #"Big Ride",mainRide*1.6, "Second Ride", secondRide*1.6, "Left Overs",leftOvers*1.6)

    if(False):
        url = "http://app.velohero.com/goals/edit/new"
        request = {
            "goal_name":"Week "+str(i),
            "goal_from_date": "07/03/2020",#DD/MM/YYYY
            "goal_to_date": "13/03/2020",#DD/MM/YYYY
            "goal_workout_dist_km":200,
            "goal_workout_dur_time":str(round(200 /16))+":00:00"
        }

        response = requests.post(url, data=request,auth = ('martyn.eggleton@gmail.com', 'M1tth2wv1l2h3r4'))
        print(response, response.headers)
        exit()
