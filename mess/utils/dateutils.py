from datetime import datetime, date

''' 
Returns the difference, in three month quarters,
between two dates. Dates passed in must be one of 
four quarter values
  01/01/XX
  04/01/XX
  07/01/XX
  10/01/XX

Raises ValueError otherwise
'''
def quarter_diff(q1, q2):

  if not type(q1) is datetime and not type(q1) is date:
    raise ValueError("Parameter q1 in function quarter_diff must be of type datetime. Received parameter of type " + str(type(q1)) + ".")

  if not type(q2) is datetime and not type(q1) is date:
    raise ValueError("Parameter q2 in function quarter_diff must be of type datetime. Received parameter of type " + str(type(q2)) + ".")

  if (q1.day != 1 or
      (q1.month != 1 and
        q1.month != 4 and
        q1.month != 7 and 
        q1.month != 10
       )): 
    raise ValueError("Illegal value for argument q1 -- " + str(q1) + " -- passed into function quarter_diff.  Date passed in must be first day of financial quarter (1/1, 4/1, 7/1, or 10/1).")

  if (q2.day != 1 or
      (q2.month != 1 and
        q2.month != 4 and
        q2.month != 7 and 
        q2.month != 10
       )):
    raise ValueError("Illegal value for argument q2 -- " + str(q2) + " -- passed into function quarter_diff.  Date passed in must be first day of financial quarter (1/1, 4/1, 7/1, or 10/1).")
      
  if q1 > q2:
    gq = q1
    lq = q2
  else:
    gq = q2
    lq = q1

  gq_quarters = (gq.year * 4) + ((gq.month  + 2) / 3)
  lq_quarters = (lq.year * 4) + ((lq.month  + 2) / 3)

  return gq_quarters - lq_quarters

'''
Takes the date and rounds the date passed in to the 'nearest'
quarter. By our standards nearest quarter is the next quarter if 
the date is within 1 month of the next quarter. Otherwise it is the 
previous quarter. The four start-of-quarter dates are:
  01/01/XX
  04/01/XX
  07/01/XX
  10/01/XX
'''
def round_to_quarter(d):

  if not type(d) is datetime and not type(d) is date:
    raise ValueError("Parameter d in function round_to_quarter must be of type datetime. Received parameter of type " + str(type(d)) + ".")

  if d.month == 1 or d.month == 2:
    return datetime(d.year, 1, 1)
  elif d.month == 3 or d.month == 4 or d.month == 5:
    return datetime(d.year, 4, 1)
  elif d.month == 6 or d.month == 7 or d.month == 8:
    return datetime(d.year, 7, 1)
  elif d.month == 9 or d.month == 10 or d.month == 11:
    return datetime(d.year, 10, 1)
  else:
    return datetime(d.year + 1, 1, 1)

