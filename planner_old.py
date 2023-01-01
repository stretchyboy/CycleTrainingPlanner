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

planName                = "Back to 100 miles"
currentWeeklyMileage    = 80
targetDistance          = 160
currentStandardCommute  = 10
targetTotalTime         = 10
targetTotalClimb        = 1000
targetMaxInclinePercentage = 11
startWeek               = 23
targetWeek              = 34
targetYear              = 2021
restCycleWeeks          = 4
restPercentage          = 66.66667
taperWeeks              = 1
plateauWeeks            = 1
taperPercentage         = 66.66667
targetRidePercentage    = 66.66667
targetWeekPercentage    = 140
longCommute             = 24
maxLongCommutes         = 1
commutesPerWeek         = 8
secondRidePercentage    = 0
stepAfterRest           = False

totalWeeks = (targetWeek - startWeek) + 1
restWeeks = math.floor((totalWeeks - (plateauWeeks+taperWeeks)) / restCycleWeeks)
if stepAfterRest:
    steps = 1+(totalWeeks - (plateauWeeks+taperWeeks)) - restWeeks
else:
    steps = 1+(totalWeeks - (plateauWeeks+taperWeeks)) - (2*restWeeks)

stepDistance = ((targetDistance * (targetWeekPercentage/100))- currentWeeklyMileage) / steps
print("totalWeeks", totalWeeks, "restWeeks", restWeeks, "Steps", steps, "Step Distance", stepDistance)

currentDistance = currentWeeklyMileage
step = 1
thisWeekDistance = currentDistance +stepDistance
for i in range(1, totalWeeks+1):
    longCommutes = math.ceil(i/(totalWeeks/maxLongCommutes))
    restWeek = False
    week = startWeek - 1 + i
    #print(i, week)
    if (i <= totalWeeks - (plateauWeeks+taperWeeks)):
        if(i % restCycleWeeks ):
            if(stepAfterRest or (i % restCycleWeeks > 1)):
                step += 1
                currentDistance = currentWeeklyMileage + (step * stepDistance)        
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

    print(i, week,step, "Dist", thisWeekDistance, "Commute", commuteDist,
    "Big Ride",mainRide, "Second Ride", secondRide, "Left Overs",leftOvers)

    #print(i, week, "Dist", thisWeekDistance, "Commute", commuteDist,
    #"Big Ride",mainRide, "Second Ride", secondRide, "Left Overs",leftOvers)


    d = str(targetYear)+"-W"+str(week-1)
    weekStart = datetime.datetime.strptime(d + '-1', "%Y-W%W-%w")-delta
    weekEnd= weekStart +      datetime.timedelta(days=6)

    urlbase = "http://app.velohero.com/goals/edit/new"

    weekName = ""
    if restWeek : 
        weekName = "Rest "
    weekName += "Week "+str(i)

    request = {
        "goal_name":planName +" : " + weekName +" : Total",
        "goal_from_date": weekStart.strftime("%d/%m/%Y"),#DD/MM/YYYY
        "goal_to_date": weekEnd.strftime("%d/%m/%Y"),#DD/MM/YYYY
        "goal_workout_dist_km": thisWeekDistance,
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
        "goal_name":planName +" : "+ weekName +" : Commute",
        "goal_from_date": monday.strftime("%d/%m/%Y"),#DD/MM/YYYY
        "goal_to_date": weekEnd.strftime("%d/%m/%Y"),#DD/MM/YYYY
        "goal_workout_dist_km": commuteDist,
        #"goal_workout_dur_time":str(round(targetTotalTime*proportionOfMaxWeek))+":00:00" ,
        #"goal_workout_asc_m": round(targetTotalClimb * proportionOfMaxWeek),
        "goal_workout_count": commutesPerWeek,
        "submit":1,
        "type_id":57086,#commute
        #"type_id":91557, # longride
    }
    url2 = urlbase+"?"+ urlencode(request2)

    request3 = {
        "goal_name":planName +" : "+weekName+" : Long Ride",
        "goal_from_date": weekStart.strftime("%d/%m/%Y"),#DD/MM/YYYY
        "goal_to_date": monday.strftime("%d/%m/%Y"),#DD/MM/YYYY
        "goal_workout_dist_km": mainRide,
        "goal_workout_dur_time":str(round(targetTotalTime*proportionOfMaxRide))+":00:00" ,
        "goal_workout_asc_m": round(targetTotalClimb * proportionOfMaxRide),
        "goal_workout_count": 1,
        "submit":1,
        "type_id":91557, # longride
    }
    url3 = urlbase+"?"+ urlencode(request3)

    if (False):
        webbrowser.open_new_tab(url1)
        webbrowser.open_new_tab(url2)
        webbrowser.open_new_tab(url3)

    if(False)  :
        response = requests.post(url, data=request,auth = ('martyn@gmail.com', 'v1l2h3r4'))
        print(response, response.headers)
        exit()
