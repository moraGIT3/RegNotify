import requests
from bs4 import BeautifulSoup

def CourseDataExtractor(crns, Semester, Year):
    if "Spring" in Semester:
        SemesterCode = 20
    elif "Winter" in Semester:
        SemesterCode = 15
    elif "Fall" in Semester:
        SemesterCode = 10
    else:
        SemesterCode = 30

    crns = crns.replace(" ", "")
    crns = crns.split(",")

    CourseInfo = []    
    Seats = []
    Waitlist = []
    for j, crn in enumerate(crns):
            
        url = f"https://ssb-prod.ec.aucegypt.edu/PROD/bwckschd.p_disp_detail_sched?term_in={Year}{SemesterCode}&crn_in={crn}"
        
        banner_data = (requests.get(url)).text
        soup = BeautifulSoup(banner_data, "html.parser")
        text = soup.get_text()
        data = text.split("Detailed Class Information\n\n")
        if data[2] == "'\n\xa0\n\n\n\nJan 12, 2023\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\nNo detailed class information found\n\n\n\n\n'":
            stat = "error1515"
            typo = "0"
            return crn, stat,typo
        else:
            del data[0:3]
                        
            data = (data[0].split("\n"))
            CourseInfo.append(data[0])
            CourseInfo[j] = CourseInfo[j].split(" - ") #[0] Course Name - [1] CRN - [2] Course Code - [3] Section

            Seats.append({"Total" : data[29],
            "Actual" : data[30],
            "Remaining" : data[31]
            })

            Waitlist.append({"Total" : data[35],
            "Actual" : data[36],
            "Remaining" : data[37]
            })
            

    return CourseInfo,Seats,Waitlist

