#!/usr/bin/env python
# coding: utf-8

# In[ ]:


import pandas as pd
import json
import glob
import math
import os
import streamlit as st
import io

st.title("Route Summary Generator")

labor_rate = st.number_input("Enter labor rate:", value=125)
num_techs = st.number_input("Enter number of techs:", value=2)
task_length = st.number_input("Enter task length (hours):", value=20)
max_daily_hours = st.number_input("Enter maximum hours per day:", value=10)
per_diem = st.number_input("Enter per diem rate:", value=175)
cost_per_mile = st.number_input("Enter mileage rate:", value=.6)
num_trucks = st.number_input("Enter number of truck:", value=1)
uploaded_files = st.file_uploader("Upload JSON files", type="json", accept_multiple_files=True)

#instantiate summary dataframe
columns = [
    'Total_Sites', 
    'Total_Labor_Hours', 
    'Total_Travel_Hours', 
    'Total_Technician_Hours', 
    'Cost_of_Labor', 
    'Total_Days_En_Route', 
    'Total_PerDiem', 
    'Total_Mileage',
    'Total_Mileage_Cost',
    'Route_Cost_Estimate'
    ]
summary = pd.DataFrame(columns=columns)
if uploaded_files:
    for uploaded_file in uploaded_files:
        file_name = uploaded_file.name
        file_bytes = uploaded_file.read()
        data = json.loads(file_bytes.decode("utf-8"))

#read routes
#for json_file in json_files:
    #with open(json_file, 'r') as f:
       # data= json.load(f)

        stops = data["stops"]
        df = pd.DataFrame(stops)
        #convert columsn
        df['segment_distance'] = df['segment_distance'].apply(lambda x: x * 0.000621371).round(1)
        df['segment_time'] = df['segment_time'].apply(lambda x: x /60/60).round(1)

        totalSites = len(df) - 2  # remove depots.
        laborHours = totalSites * task_length
        totalLaborHours = laborHours * num_techs
        travelHours =  math.ceil(df['segment_time'].sum())
        totalTravelHours = num_techs * travelHours #convert to hours
        totalTechnicianHours = totalLaborHours + totalTravelHours
        costOfLabor = totalTechnicianHours * labor_rate
        daysEnRoute = math.ceil(((7/6) * (laborHours + travelHours)) / max_daily_hours)
        #daysEnRoute = math.ceil((7/6) * ((totalTravelHours + totalTechnicianHours) / max_daily_hours))  #adding 1 rest day per week 7/6
        totalPerDiem = daysEnRoute * per_diem * num_techs
        totalMileage = math.ceil(df['segment_distance'].sum()) # convert to miles
        totalMileageCost = math.ceil(totalMileage * cost_per_mile) * num_trucks
        routeCostEst = costOfLabor + totalPerDiem + totalMileageCost

        #gnenerate overview table for each route.
        row_name = os.path.basename(file_name)
        summary.loc[row_name] = {
            "Total_Sites": totalSites, 
            "Total_Labor_Hours": totalLaborHours, 
            "Total_Travel_Hours": totalTravelHours,
            "Total_Technician_Hours": totalTechnicianHours,
            "Cost_of_Labor": costOfLabor,
            "Total_Days_En_Route": daysEnRoute,
            "Total_PerDiem": totalPerDiem,
            "Total_Mileage": totalMileage,
            "Total_Mileage_Cost": totalMileageCost,
            "Route_Cost_Estimate": routeCostEst
        }

totals = summary.sum(numeric_only=True)
totals.name = 'Totals'  # set index label for the row
summary_with_totals = pd.concat([summary, totals.to_frame().T])
if st.button('Update'):
    # Insert your update logic here (e.g. refresh data, rerun function)
    st.dataframe(summary_with_totals)

#give option to download excel file
output = io.BytesIO()
with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
    summary_with_totals .to_excel(writer, index=False, sheet_name='Sheet1')
    writer.save()
    data = output.getvalue()

st.download_button(
    label="Download data as Excel",
    data=data,
    file_name='route_summary.xlsx',
    mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
)
