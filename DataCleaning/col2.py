import sys
from pyspark import SparkContext
from csv import reader
import re
import datetime


def labelReportAsExactOrRange(x):
    fromDate = x[0]
    toDate = x[1]

    if toDate.strip() and  not fromDate.strip():
        return "ENDPOINT"
    elif fromDate.strip() and not toDate.strip():
        return "EXACT"
    elif not fromDate.strip() and not toDate.strip():
        return "INVALID"
    else:
        return "RANGE"


def returnDateSemantic(datestring):
    if not datestring.strip():
        return "INVALID"
    try:
        datetime.datetime.strptime(datestring, '%m/%d/%Y')
        groups = re.search('(\d{1,2})/(\d{1,2})/(\d{4})', datestring)
        if groups:
            year_str = groups.group(3)
            year_int = int(year_str)
            if year_int < 2006 or year_int > 2016:
                return "INVALID"
            return "VALID"
    except:
        return "FORMATTING ERROR"


if __name__ == "__main__":
    sc = SparkContext()
    lines = sc.textFile(sys.argv[1])
    header = lines.first()
    lines = lines.filter(lambda x: x != header)
    lines = lines.mapPartitions(lambda x: reader(x))
    fromDate = lines.map(lambda x: (x[0],x[1]) )
    toDate = lines.map(lambda x: (x[0],x[3]) )

    # individual filtering on both dates respectively
    fromIndividual = fromDate.map(lambda x: (x[0], x[1], returnDateSemantic(x[1])))
    invalidFromDates = fromIndividual.filter(lambda x:  x[2] == "INVALID")
    validFromDates = fromIndividual.filter(lambda x:  x[2] == "VALID")
    #write output to file
    invalidFromDates.saveAsTextFile("InvalidFromDates.out")
    validFromDates.saveAsTextFile("ValidFromDates.out")

    toIndividual = toDate.map(lambda x: (x[0], x[1], returnDateSemantic(x[1])))
    invalidToDates = toIndividual.filter(lambda x: x[2] == "INVALID")
    validToDates = toIndividual.filter(lambda x: x[2] == "VALID")
    #write dates to file
    invalidToDates.saveAsTextFile("InvalidToDates.out")
    validToDates.saveAsTextFile("ValidToDates.out")
    #validDates = validFromDates.join(validToDates)
    #individual filtering complete

    #combined filtering for both dates
    fromandtodate = lines.map(lambda x: (x[0],x[1], x[3]))

    result = fromandtodate.map(lambda x: (x[0], x[1], x[2], labelReportAsExactOrRange(x[1:])))
    invalidDates = result.filter(lambda x: x[3] == "INVALID")
    invalidDates.saveAsTextFile("InvalidSematicDates.out")
    validDates = result.filter(lambda x: x[3] != "INVALID")
    validDates.saveAsTextFile("ValidSematicDates.out")

    #filtering dates based on semantics and writing individual files
    exactDates = result.filter(lambda x: x[3] == "EXACT")
    exactDates.saveAsTextFile("exactDates.out")
    rangeDates = result.filter(lambda x: x[3] == "RANGE")
    rangeDates.saveAsTextFile("rangeDates.out")
    endPointDates = result.filter(lambda x: x[3] == "ENDPOINT")
    endPointDates.saveAsTextFile("endPointDates.out")
    sc.stop()