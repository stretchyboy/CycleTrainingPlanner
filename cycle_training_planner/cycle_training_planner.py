import math
import webbrowser
#import requests
from urllib.request import urlopen
from urllib.parse import urlencode
from datetime import date
import datetime
delta = datetime.timedelta(days=0)


class Week():
    _plan = None
    week = 0
    step = 0
    reduced = False
    distance = 0
    commuting = True
    commute = 0

    def __init__(self, week=0, step=0, reduced = False, commuting = True) -> None:
        self.week = week
        self.step = step
        self.reduced = reduced
        self.commuting = commuting
        
    @property
    def plan(self):
        return self._plan

    @plan.setter
    def plan(self, plan=plan):
        self._plan = plan
        self.planWeek()
    
    def planWeek(self):
        longCommutes = round(self.step/(self.plan.steps/self.plan.maxLongCommutes))
        distance = self.plan.currentWeeklyDistance + (self.step * self.plan.stepDistance) 
        if self.reduced:
            distance = distance * (self.plan.restPercentage / 100)
            self.commute = round(((self.plan.commutesPerRestWeek)* self.plan.currentStandardCommute))
        else:
            self.commute = round(((self.plan.currentStandardCommute * (self.plan.commutesPerWeek - longCommutes )) + (self.plan.longCommute * longCommutes)))

        if (self.commuting == False):
            self.commute = 0

        self.distance = round(distance)
        self.rides = self.plan.commutesPerWeek

        if(self.plan.week1Step == False and self.week == 1 ):
            self.commute = min(self.commute, self.distance)
        
        nonCommuteDist = max(0, self.distance - self.commute)
        maxLongRide = (self.plan.targetRidePercentage/100)*self.plan.targetDistance
        maxSecondRide = (self.plan.secondRidePercentageOfL/100)*maxLongRide
        
        self.secondRide = 0
        
        #T = L + (L * X)
        #(T/ (1 + X)) = L
        
        if self.reduced:
            self.longRide = min(maxLongRide, max(nonCommuteDist, round(self.plan.currentLRDistance + (self.step * self.plan.defaultLRStep)* (self.plan.restPercentage / 100))))
        else :
            balancedLongRide = math.ceil(nonCommuteDist/ (1+(self.plan.secondRidePercentageOfL/100)))
            potentialSecondRide = round(min(nonCommuteDist /2, nonCommuteDist - balancedLongRide , maxSecondRide))
            if(potentialSecondRide >= self.plan.minSecondRide):
                self.secondRide = potentialSecondRide
            
            self.longRide = round(min(maxLongRide, nonCommuteDist - self.secondRide))
        
        self.distance = max(self.distance, (self.commute + self.longRide))
        
        if(self.longRide > 0 ):
            self.rides += 1

        if(self.secondRide > 0 ):
            self.rides += 1
    
        
    @property
    def weekStart(self):
        d = str(self.plan.targetYear)+"-W"+str(self.plan.startWeek + self.week-1)
        #return datetime.datetime.strptime(d + '-1', "%Y-W%W-%w")-delta
        return datetime.datetime.strptime(d + '-1', "%Y-W%W-%w")-delta
    
    @property
    def weekEnd(self):
        return self.weekStart +      datetime.timedelta(days=6)  
 
    @property
    def name(self):
        weekName = ""
        if self.reduced : 
            weekName = "Rest "
        weekName += "Week "+str(self.week)
        return weekName


    def __repr__(self):
        r = "\n["+str(self.week)
        r += "  \tWS:"+self.weekStart.strftime("%d/%m/%Y")
        r += " \tS:"+str(self.step)
        r += " \tN:"+str(self.rides)
        r += " \tR:"+ str(self.reduced)+"\tD:"+ str(self.distance)
        r += " \tC:"+ str(self.commute)
        r += " \tLR:"+ str(self.longRide)+"\tSR:"+ str(self.secondRide)
        r += "]"
        return r

    def getRequests(self):

        requests = []
        
        goal_workout_asc_m = (self.step/self.plan.steps)* 1000 * self.longRide * ((self.plan.ascentPercentage/100) * self.plan.targetTotalAscent) / (1000 * self.plan.targetDistance)
        if self.reduced : 
            goal_workout_asc_m = goal_workout_asc_m * (self.plan.restPercentage / 100)
        goal_workout_asc_m = int(goal_workout_asc_m)
        #print("goal_workout_asc_m" , goal_workout_asc_m)

        monday= self.weekStart 
        friday= self.weekStart + datetime.timedelta(days=4)

        if(self.longRide > 0):
            requests.append({
                "goal_name":            self.plan.planName +" : "+ self.name +" : Long Ride",
                "goal_from_date":       friday.strftime("%d/%m/%Y"),#DD/MM/YYYY
                "goal_to_date":         self.weekEnd.strftime("%d/%m/%Y"),#DD/MM/YYYY
                "goal_workout_dist_km": self.longRide,
                "goal_workout_count":   1,
                "goal_workout_asc_m" : goal_workout_asc_m ,
                "type_id":91557,
                "submit":1
            })

        if(self.secondRide > 0):
            requests.append({
                "goal_name":            self.plan.planName +" : "+ self.name +" : Second Ride",
                "goal_from_date":       monday.strftime("%d/%m/%Y"),#DD/MM/YYYY
                "goal_to_date":         self.weekEnd.strftime("%d/%m/%Y"),#DD/MM/YYYY
                "goal_workout_dist_km": self.secondRide,
                "goal_workout_count":   1,
                "type_id":57085,
                "submit":1
            })

        if(self.commute > 0):
            requests.append({
                "goal_name":            self.plan.planName +" : "+ self.name +" : Commute",
                "goal_from_date":       monday.strftime("%d/%m/%Y"),#DD/MM/YYYY
                "goal_to_date":         friday.strftime("%d/%m/%Y"),#DD/MM/YYYY
                "goal_workout_dist_km": self.commute,
                "goal_workout_count":   self.plan.commutesPerWeek,
                "type_id":57086,
                "submit":1
            })
        
        requests.append({
            "goal_name":            self.plan.planName +" : " + self.name +" : Total",
            "goal_from_date":       self.weekStart.strftime("%d/%m/%Y"),#DD/MM/YYYY
            "goal_to_date":         self.weekEnd.strftime("%d/%m/%Y"),#DD/MM/YYYY
            "goal_workout_dist_km": self.distance,
            "goal_workout_count":   self.rides,
            "submit":               1,
        })
        
        return requests

class Plan():
    planName                = "Test Plan"
    currentWeeklyDistance   = 0
    currentLRDistance       = 0 
    targetDistance          = 100
    #targetTotalTime         = 10
    targetTotalAscent        = 1000
    ascentPercentage         = 110
    
    week1Step               = False
    minSecondRide           = 15
    #targetMaxInclinePercentage = 10
    startWeek               = 1
    targetWeek              = 20
    targetYear              = 2022
    restWeeks               = []
    restCycleWeeks          = 4
    restPercentage          = 50
    taperWeeks              = 2
    plateauWeeks            = 3
    taperPercentage         = 75
    targetRidePercentage    = 75
    targetWeekPercentage    = 150
    currentStandardCommute  = 10
    longCommute             = 15
    maxLongCommutes         = 2
    commutesPerWeek         = 10
    commutesPerRestWeek     = 8
    nonCommuteWeeks          = []
    secondRidePercentageOfL = 50
    stepAfterRest           = False
    _weeks                  = None
    _steps                  = None
    stepDistance            = 0

    def __init__(self) -> None:
        pass

    
    def isCommuteWeek(self, week = 1):
        """Return if it is a commute week.

        >>> p=Plan()
        >>> p.isCommuteWeek(1) 
        True
        >>> p.isCommuteWeek(-1)
        Traceback (most recent call last):
            ...
        ValueError: week must be > 0
        """
        if not week > 0:
            raise ValueError("week must be > 0")
        if(len(self.nonCommuteWeeks)):
            return week not in self.nonCommuteWeeks
        
        return True
    

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
        if(len(self.restWeeks)):
            return week in self.restWeeks
        
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
            return self.week1Step
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
        step = 0 # if self.week1Step else 1
        i = 0
        for i in range(1, self.totalWeeks+1):
            if self.isStepWeek(i):
                #print(i, "hi", step)
                step = step + 1
            
            week = Week(
                week = i,
                step = step,
                reduced = self.isReducedWeek(i),
                commuting = self.isCommuteWeek(i)
            )
            self._weeks.append(week)
        self._steps = step
        return self._weeks

        
    
    def plan(self):
        self.stepDistance = ((self.targetDistance * (self.targetWeekPercentage/100))- self.currentWeeklyDistance) / (self.steps)
        self.defaultLRStep = ((self.targetDistance * (self.targetRidePercentage/100))- self.currentLRDistance) / (self.steps)
        print("self.steps", self.steps, "self.stepDistance", self.stepDistance)
        for week in self.weeks:
            week.plan = self
        
        map(print, self.weeks)
        
        return self.weeks

    
    def requests(self, echo=False, do=False):
        urlbase = "http://app.velohero.com/goals/edit/new"
        for week in self.weeks:
            week.plan = self
            requests = week.getRequests()
            for request in requests:
                url = urlbase+"?"+ urlencode(request)
                if echo :
                    print (url)
                if(do):
                    #urlopen(url)
                    webbrowser.open_new_tab(url)



if __name__ == "__main__":
    p = Plan()
    p.planName                  = "NbNW 24 Plan"
    p.currentWeeklyDistance     = 70
    p.startWeek                 = 1
    p.targetWeek                = 21
    p.currentStandardCommute    = 7
    p.longCommute               = 15
    p.maxLongCommutes           = 2
    p.commutesPerWeek           = 10
    p.targetYear                = 2024
    p.targetDistance            = 212
    p.targetTotalTime           = 12
    p.targetTotalAscent         = 3510
    p.restCycleWeeks            = 4
    p.restWeeks                 = [4,8,11,14,18]
    p.restPercentage            = 50
    p.taperWeeks                = 2
    p.plateauWeeks              = 0

    p.stepAfterRest             = True
    p.targetRidePercentage      = 75
    p.secondRidePercentageOfL   = 50
    p.targetWeekPercentage      = 150
    p.nonCommuteWeeks           = [1, 7, 14, 15]
    p.minSecondRide             = 10
    p.plan()
    print("Weeks", p.weeks)
    p.requests(echo=True)
    #p.requests(do=True)
    