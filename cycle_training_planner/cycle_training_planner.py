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


class Week():
    _plan = None
    week = 0
    step = 0
    reduced = False
    distance = 0

    def __init__(self, week=0, step=0, reduced = False) -> None:
        self.week = week
        self.step = step
        self.reduced = reduced
        
    @property
    def plan(self):
        return self._plan

    @plan.setter
    def plan(self, plan=plan):
        self._plan = plan
        self.planWeek()
    
    def planWeek(self):
        longCommutes = math.ceil(self.week/(self.plan.totalWeeks/self.plan.maxLongCommutes))
        distance = self.plan.currentWeeklyDistance + (self.step * self.plan.stepDistance) 
        if self.reduced:
            distance = distance * (self.plan.restPercentage / 100)
            self.commute = self.plan.commutesPerWeek * self.plan.currentStandardCommute
        else:
            self.commute = (self.plan.currentStandardCommute * (self.plan.commutesPerWeek - longCommutes )) + (self.plan.longCommute * longCommutes)

        self.distance = round(distance)
        self.rides = self.plan.commutesPerWeek

        nonCommuteDist = max(0, self.distance - self.commute)
        maxRide = (self.plan.targetRidePercentage/100)*self.plan.targetDistance
        self.longRide = round(min(maxRide, nonCommuteDist * (100/(100 + self.plan.secondRidePercentage))))
        self.secondRide = nonCommuteDist - self.longRide

        if(self.longRide > 0 ):
            self.rides += 1

        if(self.secondRide > 0 ):
            self.rides += 1
    
        d = str(self.plan.targetYear)+"-W"+str(self.plan.startWeek - 2 + self.week)
        self.weekStart = datetime.datetime.strptime(d + '-1', "%Y-W%W-%w")-delta
        self.weekEnd= self.weekStart +      datetime.timedelta(days=6)

        
 
    @property
    def name(self):
        weekName = ""
        if self.reduced : 
            weekName = "Rest "
        weekName += "Week "+str(self.week)
        return weekName


    def __repr__(self):
        r = "\n["+str(self.week)
        r += "\tWS:"+self.weekStart.strftime("%d/%m/%Y")
        r += "\tS:"+str(self.step)
        r += "\tN:"+str(self.rides)
        r += "\tR:"+ str(self.reduced)+"\tD:"+ str(self.distance)
        r += "\tC:"+ str(self.commute)
        r += "\tLR:"+ str(self.longRide)+"\tSR:"+ str(self.secondRide)
        r += "]"
        return r

    def getRequests(self):

        requests = []
        requests.append({
            "goal_name":            self.plan.planName +" : " + self.name +" : Total",
            "goal_from_date":       self.weekStart.strftime("%d/%m/%Y"),#DD/MM/YYYY
            "goal_to_date":         self.weekEnd.strftime("%d/%m/%Y"),#DD/MM/YYYY
            "goal_workout_dist_km": self.distance,
            "goal_workout_count":   self.rides,
            "submit":               1,
        })


        monday= self.weekStart + datetime.timedelta(days=2)
        requests.append({
            "goal_name":            self.plan.planName +" : "+ self.name +" : Commute",
            "goal_from_date":       monday.strftime("%d/%m/%Y"),#DD/MM/YYYY
            "goal_to_date":         self.weekEnd.strftime("%d/%m/%Y"),#DD/MM/YYYY
            "goal_workout_dist_km": self.commute,
            "goal_workout_count":   self.plan.commutesPerWeek,
            "type_id":57086,
            "submit":1
        })

        if(self.longRide > 0):
            requests.append({
                "goal_name":            self.plan.planName +" : "+ self.name +" : Long Ride",
                "goal_from_date":       self.weekStart.strftime("%d/%m/%Y"),#DD/MM/YYYY
                "goal_to_date":         monday.strftime("%d/%m/%Y"),#DD/MM/YYYY
                "goal_workout_dist_km": self.longRide,
                "goal_workout_count":   1,
                "type_id":91557,
                "submit":1
            })

        return requests

class Plan():
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
    _weeks                  = None
    _steps                  = None
    stepDistance            = 0

    def __init__(self) -> None:
        pass

    def isRestWeek(self, week = 1):
        """Return if it is a rest week.

        >>> p=Plan()
        >>> p.isRestWeek(1) 
        False
        >>> p.isRestWeek(p.restCycleWeeks)
        True
        >>> p.isRestWeek(-1)
        Traceback (most recent call last):
            ...
        ValueError: week must be > 0
        """
        if not week > 0:
            raise ValueError("week must be > 0")
        return (week % self.restCycleWeeks) == 0

    def isTaperWeek(self, week = 1):
        """Return if it is a taper week.

        >>> p=Plan()
        >>> p.isTaperWeek(1) 
        False
        >>> p.isTaperWeek(12)
        True
        >>> p.isTaperWeek(11)
        False
        >>> p.isTaperWeek(-1)
        Traceback (most recent call last):
            ...
        ValueError: week must be > 0
        """
        if not week > 0:
            raise ValueError("week must be > 0")
        return week > self.totalWeeks - self.taperWeeks

    def isPlateauWeek(self, week = 1):
        """Return if it is a plateau week.

        >>> p=Plan()
        >>> p.isPlateauWeek(1) 
        False
        >>> p.isPlateauWeek(12)
        False
        >>> p.isPlateauWeek(11)
        True
        >>> p.isPlateauWeek(-1)
        Traceback (most recent call last):
            ...
        ValueError: week must be > 0
        """
        if not week > 0:
            raise ValueError("week must be > 0")
        if(self.isTaperWeek(week)):
            return False
        #print ("Plateau above", (self.totalWeeks - (self.taperWeeks + self.plateauWeeks)))
        return week > (self.totalWeeks - (self.taperWeeks + self.plateauWeeks))

    def isReducedWeek(self, week = 1):
        """Return if it is a reduced week.

        >>> p=Plan()
        >>> p.isReducedWeek(1) 
        False
        >>> p.isReducedWeek(4)
        True
        >>> p.isReducedWeek(12)
        True
        >>> p.isReducedWeek(11)
        False
        >>> p.isReducedWeek(-1)
        Traceback (most recent call last):
            ...
        ValueError: week must be > 0
        """
        return self.isRestWeek(week) or self.isTaperWeek(week)
        

    def isStepWeek(self, week = 1):
        """Return if it is a step week.

        >>> p=Plan()
        >>> p.isStepWeek(1) 
        True
        >>> p.isStepWeek(4)
        False
        >>> p.isStepWeek(5) 
        False
        >>> p.isStepWeek(6) 
        True
        >>> p.isStepWeek(12)
        False
        >>> p.isStepWeek(11)
        False
        >>> p=Plan()
        >>> p.stepAfterRest = True 
        >>> p.isStepWeek(5) 
        True
        >>> p.isStepWeek(-1)
        Traceback (most recent call last):
            ...
        ValueError: week must be > 0
        """
        if (week == 1 ):
            return True
        if (self.isReducedWeek(week) or self.isPlateauWeek(week)):
            return False
        if self.stepAfterRest :
            return True
        return not self.isRestWeek(week-1)

    @property
    def totalWeeks(self):
        return (self.targetWeek - self.startWeek) + 1

    @property
    def steps(self):
        """
        >>> p=Plan()
        >>> p.steps 
        6
        """
        a = self.weeks
        return self._steps
    
    @property
    def weeks(self, force=False):
        """
        >>> p=Plan()
        
        """
        if(self._weeks != None and not force):
            return self._weeks

        self._weeks = []
        step = 0
        i = 0
        for i in range(1, self.totalWeeks+1):
            if self.isStepWeek(i):
                #print(i, "hi", step)
                step = step + 1
            
            week = Week(
                week=i,
                step=step,
                reduced= self.isReducedWeek(i)
            )
            self._weeks.append(week)
        self._steps = step
        return self._weeks

        
    
    def plan(self):
        self.stepDistance = ((self.targetDistance * (self.targetWeekPercentage/100))- self.currentWeeklyMileage) / self.steps
        print("self.steps", self.steps, "self.stepDistance", self.stepDistance)
        for week in self.weeks:
            week.plan = self
        
        map(print, self.weeks)
        
        return self.weeks

    
    def requests(self, do=False):
        urlbase = "http://app.velohero.com/goals/edit/new"
        for week in self.weeks:
            week.plan = self
            requests = week.getRequests()
            for request in requests:
                url = urlbase+"?"+ urlencode(request)
                print (url)
                if(do):
                    webbrowser.open_new_tab(url)



if __name__ == "__main__":
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
    