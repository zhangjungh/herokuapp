# -*- coding: UTF-8 -*-
import os
import sys
import random
from datetime import datetime, timedelta

def give_test(total, maxvalue):
    r = []
    while len(r) <= total:
        add = True
        if random.random() < 0.3334:
            add = False
        while True:
            n1 = random.randint(5, maxvalue)
            n2 = random.randint(5, maxvalue)
            if add and n1 + n2 <= maxvalue:
                r.append('%2d + %2d = ' % (n1, n2))
                break
            if not add and n1 > n2:
                r.append('%2d - %2d = ' % (n1, n2))
                break
    return r

def give_bunchof_tests(number):
    for i in range(number):
        r = give_test(32, 100)
        print ('Name: Harry    P%d    Time:\t\t\t\tScore:' % (i+1))
        line = ''
        for i in range(len(r)):
            if i % 4 == 0:
                print (line)
                line = ''
                print ('\n')
            line += r[i]+'       '
        print ('\n\n')
        

def give_y2_test(total, divides, times, multiply, maxvalue):
    r, a = [], []
    while len(r) < total-1:
        #divide, fractions and multiply
        t1 = random.randint(2, divides)
        t2 = random.randint(2, divides)
        t3 = random.randint(2, times)
        t4 = t1 * t2
        t5 = t2 * t3
        line = ''
        fraction = True
        if random.random() < 0.5:
            fraction = False
        if fraction:
            line += '%d/%d × %2d ' % (t3, t1, t4)
        else:
            line += '%2d ÷ %2d × %2d ' % (t4, t1, t3)
            
        #add and subtract
        add = True
        if random.random() < 0.6667:
            add = False
        while True:
            n1 = t5 # random.randint(5, maxvalue)
            n2 = random.randint(5, maxvalue)
            if add and n1 + n2 <= maxvalue:
                line += '+ %2d = ' % n2
                r.append(line)
                a.append(n1+n2)
                break
            if not add and n1 > n2:
                line += '- %2d = ' % n2
                r.append(line)
                a.append(n1-n2)
                break
                
    #large number multiply
    l1 = random.randint(10, multiply)
    l2 = random.randint(10, multiply)
    line = '×%d/%d = ' % (l1, l2)
    r.append(line)
    a.append(l1*l2)
    return r, a

def get_date(day):
    strDate = '09/03/20'
    objDate = datetime.strptime(strDate, '%d/%m/%y')
    #objDate = datetime.now()
    d = timedelta(days=day)
    objDate += d
    return objDate.strftime("%A %d %b %Y")
    
def give_bunchof_Y2_tests(number):
    with open('math.txt', 'wt') as f:
        with open('answer.txt', 'wt') as o:
            for i in range(number):
                r, a = give_y2_test(12, 12, 20, 30, 1500)
                f.write('Harry-%s-Score:\n' % get_date(i))
                o.write('%s\n' % get_date(i))
                line = ''
                for i in range(len(r)):
                    line += r[i]+'            '
                    if (i+1) % 3 == 0:
                        f.write(line)
                        line = ''
                        f.write('\n')
                    o.write(str(a[i])+',  ')
                f.write('\n\n')
                o.write('\n\n')
