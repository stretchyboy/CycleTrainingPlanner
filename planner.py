#input currentWeeklyMileage
#input currentStandardCommute
#input targetDistance
#input targetTotalTime
#input targetDate
#input restCycleWeeks
#input weekStart
import math
import webbrowser
import requests
from urllib.parse import urlencode
from datetime import date
import datetime
delta = datetime.timedelta(days=2)

planName                = "The Longest Day"
currentWeeklyMileage    = 75
targetDistance          = 150
currentStandardCommute  = 6
targetTotalTime         = 14
targetTotalClimb        = 2440
targetMaxInclinePercentage = 11
startWeek               = 11
targetWeek              = 21
targetYear              = 2020
restCycleWeeks          = 4
restPercentage          = 66.66667
taperWeeks              = 2
plateauWeeks            = 1
taperPercentage         = 66.66667
targetRidePercentage    = 66.66667
targetWeekPercentage    = 140
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

    proportionOfMaxWeek = thisWeekDistance / ((targetWeekPercentage/100)*targetDistance)
    proportionOfMaxRide = mainRide / targetDistance

    print(i, week, "Dist", thisWeekDistance, "Commute", commuteDist,
    "Big Ride",mainRide, "Second Ride", secondRide, "Left Overs",leftOvers)

    #print(i, week, "Dist", thisWeekDistance*1.6, "Commute", commuteDist*1.6,
    #"Big Ride",mainRide*1.6, "Second Ride", secondRide*1.6, "Left Overs",leftOvers*1.6)


    d = str(targetYear)+"-W"+str(week-1)
    weekStart = datetime.datetime.strptime(d + '-1', "%Y-W%W-%w")-delta
    weekEnd= weekStart +      datetime.timedelta(days=6)

    urlbase = "http://app.velohero.com/goals/edit/new"

    request = {
        "goal_name":planName +": Week "+str(i),
        "goal_from_date": weekStart.strftime("%d/%m/%Y"),#DD/MM/YYYY
        "goal_to_date": weekEnd.strftime("%d/%m/%Y"),#DD/MM/YYYY
        "goal_workout_dist_km": thisWeekDistance*1.6,
        "goal_workout_dur_time":str(round(targetTotalTime*proportionOfMaxWeek))+":00:00" ,
        "goal_workout_asc_m": round(targetTotalClimb * proportionOfMaxWeek),
        "goal_workout_count": 12,
        "submit":1,
        #"type_id":57086,#commute
        #"type_id":91557, # longride
    }
    #print(request)
    url1 = urlbase+"?"+ urlencode(request)

    monday= weekStart +      datetime.timedelta(days=2)

    request2 = {
        "goal_name":planName +": Week "+str(i)+" Commute",
        "goal_from_date": monday.strftime("%d/%m/%Y"),#DD/MM/YYYY
        "goal_to_date": weekEnd.strftime("%d/%m/%Y"),#DD/MM/YYYY
        "goal_workout_dist_km": commuteDist*1.6,
        #"goal_workout_dur_time":str(round(targetTotalTime*proportionOfMaxWeek))+":00:00" ,
        #"goal_workout_asc_m": round(targetTotalClimb * proportionOfMaxWeek),
        "goal_workout_count": 10,
        "submit":1,
        "type_id":57086,#commute
        #"type_id":91557, # longride
    }
    url2 = urlbase+"?"+ urlencode(request2)

    request3 = {
        "goal_name":planName +": Week "+str(i)+" Long Ride",
        "goal_from_date": weekStart.strftime("%d/%m/%Y"),#DD/MM/YYYY
        "goal_to_date": monday.strftime("%d/%m/%Y"),#DD/MM/YYYY
        "goal_workout_dist_km": mainRide*1.6,
        "goal_workout_dur_time":str(round(targetTotalTime*proportionOfMaxRide))+":00:00" ,
        "goal_workout_asc_m": round(targetTotalClimb * proportionOfMaxRide),
        "goal_workout_count": 1,
        "submit":1,
        "type_id":91557, # longride
    }
    url3 = urlbase+"?"+ urlencode(request3)

    if (True):
        webbrowser.open_new_tab(url1)
        webbrowser.open_new_tab(url2)
        webbrowser.open_new_tab(url3)

    if(False)  :
        response = requests.post(url, data=request,auth = ('martyn@gmail.com', 'v1l2h3r4'))
        print(response, response.headers)
        exit()
