#!/usr/bin/env python

import pickle
import os
import platform
from pushbullet import Pushbullet
from Sona import Sona

# sona credentials
login = "SONA_STUDENT_USERNAME"
password = "SONA_STUDENT_PASSWORD"
sona_site = "https://usthk-markexpt.sona-systems.com"

# pushbullet
api_key = "PUSHBULLET_API_KEY"
ch_tag = "PUSHBULLET_CHANNEL_TAG"


# filesystem; redirect to usb if router
work_dir = os.path.dirname(os.path.realpath(__file__))
fpath = work_dir + '/' + ch_tag + '.p'

# sona experiment path
idpath = '/exp_info_participant.aspx?experiment_id='


# http://stackoverflow.com/questions/1158076/implement-touch-using-python
def touch(path):
    with open(path, 'a'):
        os.utime(path, None)

# http://stackoverflow.com/questions/5679638/merging-a-list-of-time-range-tuples-that-have-overlapping-time-ranges
def merge(times):
    saved = list(times[0])
    for st, en in sorted([sorted(t) for t in times]):
        if st <= saved[1]:
            saved[1] = max(saved[1], en)
        else:
            yield tuple(saved)
            saved[0] = st
            saved[1] = en
    yield tuple(saved)

def merge_dates(datetime):
    mydict = {}
    for i in datetime:
        try:
            mydict[i[0]].append(i[1])
        except:
            mydict[i[0]] = [i[1]]
    return mydict

def get_decimal_time(string):
    return float(string.split(':')[0]) + float(string.split(':')[1])/60

def get_string_time(float):
    h = int(float)
    m = int(float % 1 * 60)
    return str(h).zfill(2) + ':' + str(m).zfill(2)

def get_datetime(list):
    return [[item['timeslot_date'][:-14], item['timeslot_date'][-13:]] for item in list]

def get_metric_timeslot(list):
    # hacky get timeslots in [start, end]
    short = [[item[:5], item[-5:]] for item in list]
    decimal = [(get_decimal_time(item[0]), get_decimal_time(item[1])) for item in short]
    return decimal
 
def get_free_timeslot_string(id):
    timeslot = sona.get_free_timeslot(id)
    if timeslot:
        datetime = get_datetime(timeslot)
        timedict = merge_dates(datetime)
        output = []
        for key, value in timedict.iteritems():
            date =  ' '.join(key.split(' ')[1:3])[:-2] # get short date
            merged = list(merge(get_metric_timeslot(value)))
            time = ', '.join([get_string_time(item[0]) + '-' + get_string_time(item[1]) for item in merged])
            output.append('(%s: %s)' % (date, time))
        return ' '.join(output)

def save_pickle():
    print 'save'
    with open(fpath, 'wb') as fp:
        pickle.dump(sona, fp)

# create file if not exist
if not os.path.exists(fpath):
    touch(fpath)
    key = ''
    sona = Sona(login, password, sona_site)
    save_pickle()

# load pickle
with open(fpath, 'rb') as f:
    sona = pickle.load(f)

# load previous session and studies
key = sona.session['p_sessionToken']
studies = sona.studies

# get new session and studies, return new studies in [name, id] list
newStudies = [[item['exp_name'], item['experiment_id']] for item in sona.get_new_studies()]

if newStudies:
    # create pushbullet object and get channel
    pb = Pushbullet(api_key)
    channel = pb.get_channel(ch_tag)

    # create full url path
    url = sona.domain + idpath
    
    for item in newStudies:
        name = item[0] + ' ' + get_free_timeslot_string(item[1])
        if sona.get_study_eligibility(item[1]): # if eligible
            # private push
            push = pb.push_link(name, url + str(item[1]))

        # channel push
        push = channel.push_link(name, url + str(item[1]))
    
# save pickle if session renewed or studies changed
if key != sona.session['p_sessionToken'] or studies != sona.studies:
    save_pickle()
