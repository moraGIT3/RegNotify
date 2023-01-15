import pygsheets
from datetime import datetime
from registration import CourseDataExtractor

def current_time():
    time = datetime.now()
    time = time.strftime("%d/%m/%Y %H:%M:%S")
    return time

def auth():
    global sheet
    # global RegisteredWorksheet
    # global UserWorksheet
    # global DataWorksheet
    # global CellWorksheet
        
    client = pygsheets.authorize(service_account_env_var='gdrive-token')
    sheet = client.open("RegBot")
    
    # RegisteredWorksheet = sheet[0]
    # UserWorksheet = sheet[3]
    # DataWorksheet = sheet[1]
    # CellWorksheet = sheet[2] 
    return 

# def AddCourse(chat_id,crn,Course_Name, Semester, Year, Section, Course_ID):
def AddCourse(chat_id,Course_Info, Semester, Year): 
    
    try:
        RedundancyWorksheet = sheet[4]
        RegisteredWorksheet = sheet[0]
    except:
        auth()
        RedundancyWorksheet = sheet[4]
        RegisteredWorksheet = sheet[0]
    
    time = current_time()    
    
    num_entries = len(Course_Info)

    CourseRow = int(RegisteredWorksheet.rows)
    RedundantRow = int(RedundancyWorksheet.rows)
    RedundancyWorksheet.add_rows(num_entries)
    RegisteredWorksheet.add_rows(num_entries)
    
    for num in range(num_entries):
        msg =  [ Course_Info[num][1] , chat_id, Course_Info[num][0], Semester, Year, Course_Info[num][3], Course_Info[num][2], time]
        row = num + 1
        RegisteredWorksheet.update_row(CourseRow + row, values=msg, col_offset=0)
        RedundancyWorksheet.update_row(RedundantRow + row, values=msg, col_offset=0)

    stat = "Success"
    return stat

def CourseDataRetriever(chat_id):
    try:
        CellWorksheet = sheet[2]
        UserWorksheet = sheet[3]
        RegisteredWorksheet = sheet[0]
    except:
        auth()
        CellWorksheet = sheet[2]
        UserWorksheet = sheet[3]
        RegisteredWorksheet = sheet[0]

    i = 0
    found = 0
    end_row = int(CellWorksheet.get_value("B1"))
    ids = UserWorksheet.get_values("A2",f"B{end_row + 1}",returnas = "matrix")
    count = len(ids)
    while i < count and found != 1:
        if ids[i][0] == str(chat_id):
            found = 1
            num_courses = int(ids[i][1])
        i = 1 + i
    ids = RegisteredWorksheet.get_col(2)
    i = 0
    found = 0
    count = len(ids)
    index = []
    PrevCRN = []
    while i < count and found <= num_courses:
        if ids[i] == str(chat_id):
            found = 1
            index.append(i)
            PrevCRN.append(RegisteredWorksheet.get_row( i + 1 ))
        i += 1
    return PrevCRN,index

def DropCourse(chat_id, index, all):
    
    try:
        RegisteredWorksheet = sheet[0]
        UserWorksheet = sheet[3]
    except:
        auth()
        RegisteredWorksheet = sheet[0]
        UserWorksheet = sheet[3]

    if all == "yes":
        count = 0
        for n in index:
            RegisteredWorksheet.delete_rows(n + 1 - count,1)
            count += 1
        i = 1
        found = 0
        ids = UserWorksheet.get_col(1)
        count = len(ids)
        num_entries = len(index)
        while i < count and found != 1:
            if ids[i] == chat_id:
                found = 1
                PrevCourses = int((UserWorksheet.get_row(i+1))[1]) 
                UserWorksheet.update_value(f"B{i + 1}", (PrevCourses - num_entries))
                i = i-1
                count = count - 1 
            i = 1 + i  
    else:
        RegisteredWorksheet.delete_rows(int(index) + 1 ,1)
        i = 1
        found = 0
        ids = UserWorksheet.get_col(1)
        count = len(ids)
        
        while i < count and found != 1:
            if ids[i] == chat_id:
                found = 1
                PrevCourses = int((UserWorksheet.get_row(i+1))[1]) 
                UserWorksheet.update_value(f"B{i + 1}", (PrevCourses - 1)) 
            i = 1 + i  

 

def CourseSeatUpdater():
    
    try:    
        DataWorksheet = sheet[1]
        CellWorksheet = sheet[2]
    except:
        DataWorksheet = sheet[1]
        CellWorksheet = sheet[2]
    
    end_row = int(CellWorksheet.get_value("A1"))

    AllCrns = DataWorksheet.get_values("A2",f"H{end_row + 1}",returnas = "matrix") # [0] for CRN and [1] for Semester [2] for Year and [3] for Available seats [4] for Chat IDS [5] Course Name [6] section [7] course ID
 
    index = []
    for m in range(len(AllCrns)):
        SeatsRemaining = (CourseDataExtractor(crns = AllCrns[m][0], Semester= AllCrns[m][1], Year= AllCrns[m][2]))[1]
        if SeatsRemaining[0]["Remaining"] != AllCrns[m][3]:
            index.append(m)
            DataWorksheet.update_value(f"D{m+2}",SeatsRemaining[0]["Remaining"])
            AllCrns[m][3] = SeatsRemaining[0]["Remaining"]

    return AllCrns,index
