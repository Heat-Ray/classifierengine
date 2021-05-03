from django.shortcuts import render
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
import pandas as pd
import numpy as np
import datetime
from sklearn.tree import DecisionTreeClassifier
from sklearn.model_selection import train_test_split
import json

# Create your views here.

@csrf_exempt 
def clf(request):
    print(request.POST)
    data = request.POST['csv']
    
    csv_data = pd.DataFrame([x.split(',') for x in data.split('\n')])
    csv_data.columns = ["Day", "Time", "PackageName", "SecondsActive"]
    csv_data['Day'].replace('', np.nan, inplace=True)
    csv_data = csv_data.dropna(axis = 0)
    csv_data.reset_index(drop = True, inplace=True)
    packageCount = csv_data.PackageName.value_counts()
    packageList = csv_data.PackageName.unique()
    print(csv_data)
    print(request.POST['Day'])


    f_data = {'Day':[], 'Time':[], 'PackageName':[]}
    year = '2021'
    for row_no in range(0, csv_data.shape[0], 1):
        _row = csv_data.iloc[row_no, :]
        #Ref: https://docs.python.org/2/library/datetime.html#strftime-and-strptime-behavior
        #Weekday as a decimal number, where 0 is Sunday and 6 is Saturday.
        day_of_week = datetime.datetime.strptime(_row['Day'] + ' ' + year, "%d %B %Y").strftime('%w')
        time_of_day = _row['Time'].split(' ')[0].split(':')
        hour_of_launch = int(time_of_day[0])
        minutes_of_launch = int(time_of_day[1])
        
        if(minutes_of_launch >= 0 and minutes_of_launch < 15):
            minutes_of_launch = 0
        elif(minutes_of_launch >= 15 and minutes_of_launch < 30):
            minutes_of_launch = 15
        elif(minutes_of_launch >= 30 and minutes_of_launch < 45):
            minutes_of_launch = 30
        elif(minutes_of_launch < 60):
            minutes_of_launch = 45
        else:
            minutes_of_launch = 0
            
        time_of_day = str(hour_of_launch) + ':' + str(minutes_of_launch) + ' ' + _row['Time'].split(' ')[1]
        in_time = datetime.datetime.strptime(time_of_day, "%I:%M %p")
        time_of_day = datetime.datetime.strftime(in_time, "%H%M")
        csv_data['Day'][row_no] = day_of_week
        csv_data['Time'][row_no] = time_of_day
        used_t = int(_row['SecondsActive'])
        while(used_t > 0):
            used_t -= 10
            f_data['Day'].append(day_of_week)
            f_data['Time'].append(int(time_of_day))
            f_data['PackageName'].append(_row['PackageName'])

    final_d = pd.DataFrame.from_dict(f_data, orient='columns')

    
    
    final_d["PackageName"] = final_d["PackageName"].astype('category')
    df = dict(enumerate(final_d["PackageName"].cat.categories))
    final_d["PackageName"] = final_d["PackageName"].cat.codes

    X = final_d.values[:, 0:2]
    Y = final_d.values[:, 2:3]
    Y=Y.astype('int')

    X_train, X_test, y_train, y_test = train_test_split(X, Y, test_size=0.1, random_state=50)
    clf = DecisionTreeClassifier(random_state=0).fit(X_train, y_train)


    rdata = {'Day':[], 'Time':[]}
    day = datetime.datetime.strptime(request.POST['Day'] + ' ' + year, "%B %d %Y").strftime('%w')
    min = 0
    hrs = 0
    for i in range(24 * 4):
        rdata['Day'].append(day)
        rdata['Time'].append(hrs * 100 + min)
        min += 15
        if min % 60 == 0:
            hrs += 1
            min = 0
    rdata = pd.DataFrame.from_dict(rdata, orient = 'columns')
    print(rdata.head())
    probs = clf.predict_proba(rdata)
    best_n = []
    for i in probs:
        best_n.append(np.argsort(i)[-10:])

    out = {}
    for i in range(len(best_n)):
        ans = []
        for j in best_n[i]:
            ans += [df[j]]
        out[int(rdata['Time'][i])] = ans




    returnResponse = json.dumps(out)
    return HttpResponse(returnResponse)

