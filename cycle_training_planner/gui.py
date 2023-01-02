import PySimpleGUI as sg      

from cycle_training_planner import Plan


sg.theme('DarkAmber')    # Keep things interesting for your users

def getRow(name, j=None):
    field = getattr(p, name)
    if(type(field) == str):
        inp = sg.Input(key=name, default_text=str(field), size=30)
    if(type(field) == bool):
        inp = sg.Checkbox(text=name, key=name, default=field)
    if(type(field) == int):
        if "Percentage" in name:
            inp = sg.Slider(range = (0, 200), orientation="horizontal", resolution =5, key=name,  default_value=field)
        else:
            inp = sg.Input(key=name, default_text=str(field), size=10)
    if inp:
        return [sg.Text(name, size=30), inp]

p = Plan()
p.plan()

layout = [
    getRow('planName') + getRow('targetYear'), 
    getRow('startWeek') + getRow('targetWeek'),
    getRow('currentWeeklyDistance') + getRow('targetDistance'), 
    getRow('targetRidePercentage') + getRow('targetWeekPercentage'), 
    
    getRow('restCycleWeeks') + getRow('restPercentage'),
    getRow('week1Step') + getRow('stepAfterRest'),
    
    getRow('commutesPerWeek') + getRow('currentStandardCommute'),
    getRow('longCommute') + getRow('maxLongCommutes'), 
    getRow('minSecondRide') + getRow('secondRidePercentageOfL'),  
    
    getRow('plateauWeeks'),
    getRow('taperPercentage') + getRow('taperWeeks'),
        
    [sg.Button('Run'), sg.Button('VeloHero'), sg.Exit()],
    [sg.Output(key='-OUTPUT-', size=(80,20))]
    ]      

window = sg.Window('Window that stays open', layout)      

while True:                             # The Event Loop
    event, values = window.read() 
    print(values)
    p = Plan()
    for key, item in values.items():
        if key in ["week1Step", "stepAfterRest"]:
            setattr(p, key, item)
        elif key in ["planName"]:
            setattr(p, key, item)
        else :
            setattr(p, key, int(item))
    p.plan()
    print(p.weeks)
    if event == "VeloHero" : 
        p.requests(do=True)
    if event == sg.WIN_CLOSED or event == 'Exit':
        break      

window.close()

    