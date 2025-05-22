# -*- coding: utf-8 -*-
"""
Created on Mon Jul 29 13:40:15 2024

@author: Paul Ledin
"""

import streamlit as st
import pandas as pd
import numpy as np
import altair as alt
from st_aggrid import AgGrid

st.set_page_config(
    page_title="America's Credit Unions",
    layout="wide",
    initial_sidebar_state="expanded")

thePassPhrase = st.secrets["thePassPhrase"]
dbConn = st.connection("snowflake")
###############################################################################
#Function Definitions
###############################################################################
def convertDateToDisplay(date):
    switcher = {
        "01": "January",
        "02": "February",
        "03": "March",
        "04": "April",
        "05": "May",
        "06": "June",
        "07": "July",
        "08": "August",
        "09": "September",
        "10": "October",
        "11": "November",
        "12": "December",
    }
    
    return switcher.get(date[4:], "**Bad Month**") + "-" + date[:4]

def convertDateToSystem(date):
    switcher = {
        "January":  "01",
        "February": "02",
        "March":    "03",
        "April":    "04",
        "May":      "05",
        "June":     "06",
        "July":     "07",
        "August":   "08",
        "September":"09",
        "October":  "10",
        "November": "11",
        "December": "12",
    }
    
    return date[len(date)-4:len(date)] + switcher.get(date[:len(date)-5], "**Bad Month**")

def getPreviousSystemMonth(month):
    system_month = int(convertDateToSystem(month)[4:])
    prev_system_year = convertDateToSystem(month)[:4]
    
    prev_system_month = system_month - 1
    if(prev_system_month == 0):
        prev_system_month = 12
        prev_system_year = str(int(prev_system_year) - 1)
           
    return (prev_system_year + str(prev_system_month).rjust(2, '0'))

def get_last_reported_period(report_periods):    
    return str(report_periods.iloc[len(report_periods) - 1, 0])

def getMetricDeltas(aflType, groupBy, month, report_periods):
    if (convertDateToSystem(month) == get_last_reported_period(report_periods)):
        retVal = pd.DataFrame({'CU AFL Delta':[],
                'Members AFL Delta':[],
                'Assets AFL Delta':[]
                })
    else:
        if (selected_group_by == 'Asset Class(9)'):
            this_month = getTableAFLTable_from_db(aflType, groupBy, month, "4")
            last_month = getTableAFLTable_from_db(aflType, groupBy, convertDateToDisplay(getPreviousSystemMonth(month)), "4")
        elif (selected_group_by == 'Asset Class(13)'):
            this_month = getTableAFLTable_from_db(aflType, groupBy, month, "3")
            last_month = getTableAFLTable_from_db(aflType, groupBy, convertDateToDisplay(getPreviousSystemMonth(month)), "3")
        else:
            this_month = getTableAFLTable_from_db(aflType, groupBy, month, "1")
            last_month = getTableAFLTable_from_db(aflType, groupBy, convertDateToDisplay(getPreviousSystemMonth(month)), "1")
        
        retVal = pd.DataFrame({'CU AFL Delta' : [str(round((this_month.iloc[len(this_month) - 1, 10] - last_month.iloc[len(this_month) - 1, 10]) * 100, 2))],
                              'Members AFL Delta' : [str(round((this_month.iloc[len(this_month) - 1, 11] - last_month.iloc[len(this_month) - 1, 11]) * 100, 2))],
                              'Assets AFL Delta' : [str(round((this_month.iloc[len(this_month) - 1, 12] - last_month.iloc[len(this_month) - 1, 12]) * 100, 2))]
                             })
    return (retVal)
    
@st.cache_data
def get_report_periods_from_db():
    return (dbConn.session().sql("SELECT DISTINCT(SUBSTR(TABLE_NAME, LENGTH(TABLE_NAME)-5, length(TABLE_NAME))) AS period FROM monthly_report.information_schema.tables WHERE table_schema!='INFORMATION_SCHEMA' ORDER BY SUBSTR(TABLE_NAME, LENGTH(TABLE_NAME)-5, LENGTH(TABLE_NAME)) DESC").to_pandas())

def get_report_periods_for_display_from_db():
    periods = get_report_periods_from_db()
    periods['report_periods_formatted'] = periods.apply(lambda row: convertDateToDisplay(str(row.PERIOD)), axis=1)                                                             
    
    return (periods)

@st.cache_data
def getTableAFLTable_from_db(afl_type, group_by, month, table_number):
    sqlStmt = "SELECT * FROM monthly_report."
    
    if(afl_type == 'Legacy CUNA'):
        aflType = 'Legacycuna'
    elif(afl_type == 'Legacy NAFCU'):
        aflType = 'Legacynafcu'
    elif(afl_type == 'Member of Both'):
        aflType = 'Both'
    else:
        aflType = 'Either'
    sqlStmt += aflType + '.afl_table_' + table_number
    
    if(group_by == 'League'):
        groupBy = 'ByLeague'
    elif(group_by == 'Asset Class(9)'):
        groupBy = 'ByAcl_9'
    elif(group_by == 'Asset Class(13)'):
        groupBy = 'ByAcl_13'
    else:
        groupBy = 'ByState'
    sqlStmt += '_' + groupBy + '_' + convertDateToSystem(month)

    return (dbConn.session().sql(sqlStmt).to_pandas())

def get_report_periods():
    periods = pd.read_csv('https://raw.githubusercontent.com/paulledin/data/master/MonthlyReportPeriods.csv')
    
    retVal = list()
    index = 0
    for x in periods:
        retVal.insert(index, periods[x])
        index += 1

    return (retVal)

def get_report_periods_for_display():
    periods = pd.read_csv('https://raw.githubusercontent.com/paulledin/data/master/MonthlyReportPeriods.csv')    
    retVal = list()

    index = 0
    for x in periods:
        retVal.insert(index, periods[x])
        index += 1
        
    df_retVal = pd.DataFrame(retVal[0])
        
    for i in range(len(df_retVal)):
        period = df_retVal.loc[i, "period"]
        df_retVal.loc[df_retVal['period'] == period, 'report_periods_formatted'] = convertDateToDisplay(str(period))

    return df_retVal

def getTableAFLTable(afl_type, group_by, month, table_number):
    if(afl_type == 'Legacy CUNA'):
        aflType = 'Legacycuna'
    elif(afl_type == 'Legacy NAFCU'):
        aflType = 'Legacynafcu'
    elif(afl_type == 'Member of Both'):
        aflType = 'Both'
    else:
        aflType = 'Either'
        
    if(group_by == 'League'):
        groupBy = 'ByLeague'
    elif(group_by == 'Asset Class(9)'):
        groupBy = 'ByAcl_9'
    elif(group_by == 'Asset Class(13)'):
        groupBy = 'ByAcl_13'
    else:
        groupBy = 'ByState'
        
    return pd.DataFrame(pd.read_csv('https://raw.githubusercontent.com/paulledin/data/master/afl_table_' + table_number + '_' + groupBy + '_' + aflType + '_' + convertDateToSystem(month) + '.csv'))
###############################################################################
#Start building Streamlit App
###############################################################################
report_periods = get_report_periods_for_display_from_db()

with st.sidebar:
    st.markdown('![alt text](https://raw.githubusercontent.com/paulledin/data/master/ACUS.jpg)')
    passphrase = st.text_input("### Please enter the passphrase:")

if (passphrase != thePassPhrase):
    if len(passphrase) > 0:
        st.markdown('# Passphrase not correct....')
        st.markdown('### Please try again or contact: pledin@americascreditunions.org for assistance.')
else:
    with st.sidebar:
        st.title('Affiliation Report')
    
        afl_type = ['Member of Americas Credit Unions','Legacy CUNA', 'Legacy NAFCU', 'Member of Both']
        selected_afl_type = st.selectbox('Affiliation Type', afl_type)
    
        group_by = ['State', 'League', 'Asset Class(9)', 'Asset Class(13)']
        selected_group_by = st.selectbox('Group By', group_by)
    
        month = report_periods['report_periods_formatted']
        selected_month = st.selectbox('Month', month)
    
    if (selected_group_by == 'Asset Class(9)'):
        table1 = getTableAFLTable_from_db(selected_afl_type, selected_group_by, selected_month, "4")
    elif (selected_group_by == 'Asset Class(13)'):
        table1 = getTableAFLTable_from_db(selected_afl_type, selected_group_by, selected_month, "3")
    else:
        table1 = getTableAFLTable_from_db(selected_afl_type, selected_group_by, selected_month, "1")
    
    table1['% CUs Affiliated'] = round(table1['% CUs Affiliated'] * 100, 1).astype('str') + '%'
    table1['% Memberships Affiliated'] = round(table1['% Memberships Affiliated'] * 100, 1).astype('str') + '%'
    table1['% Assets Affiliated'] = round(table1['% Assets Affiliated'] * 100, 1).astype('str') + '%'

    column_configuration = {
        "Affiliated CUs": st.column_config.NumberColumn(
        "Total Affiliated CUs",
        help="Number of Affiliated Credit Unions",
        min_value=0,
        max_value=100000,
        step=1,
        format="localized",),
        "Non Affiliated CUs": st.column_config.NumberColumn(
        "Non Affiliated CUs",
        help="Number of Non-Affiliated Credit Unions",
        min_value=0,
        max_value=100000,
        step=1,
        format="localized",),
        "State Chartered": st.column_config.NumberColumn(
        "State Chartered CUs",
        help="Number of State Chartered Credit Unions",
        min_value=0,
        max_value=100000,
        step=1,
        format="localized",),
       "Fed Chartered": st.column_config.NumberColumn(
        "Fed Chartered CUs",
        help="Number of Federally Chartered Credit Unions",
        min_value=0,
        max_value=100000,
        step=1,
        format="localized",),
        "Total CUs": st.column_config.NumberColumn(
        "Total # of CUs",
        help="Total Number of Credit Unions",
        min_value=0,
        max_value=100000,
        step=1,
        format="localized",),
        "Affiliated Memberships": st.column_config.NumberColumn(
        "Affiliated Memberships",
        help="Number of Affiliated Memberships",
        min_value=0,
        max_value=100000000,
        step=1,
        format="localized",),
        "Total Memberships": st.column_config.NumberColumn(
        "Total CU Memberships",
        help="Number of Total CU Memberships",
        min_value=0,
        max_value=100000000,
        step=1,
        format="localized",),
        "Affiliated Assets": st.column_config.NumberColumn(
        "Total Affiliated Assets ($)",
        help="Affiliated Credit Union Total Assets",
        min_value=0,
        max_value=1000000000000,
        step=1,
        format="localized",),
        "Total Assets": st.column_config.NumberColumn(
        "Total CU Assets ($)",
        help="Credit Union Total Assets",
        min_value=0,
        max_value=1000000000000,
        step=1,
        format="localized",),
        }


    col = st.columns((1.5, 6.5), gap='medium')
    with col[0]:          
        metric_deltas = getMetricDeltas(selected_afl_type, selected_group_by, selected_month, report_periods)   
    
        st.markdown('#### Key Ratios')
        if selected_group_by == 'State' or selected_group_by == 'League':
            st.markdown('###### (excludes Table 2 CUs)')
            st.markdown('###### ' + 'Month Ended - ' + selected_month)
            st.markdown('---')
    
        if len(metric_deltas) == 0:
            st.metric(label = 'Credit Unions Affiliated', value = table1.iloc[len(table1) - 1, 10])
            st.metric(label = 'Members Affiliated', value = table1.iloc[len(table1) - 1, 11])
            st.metric(label = 'Assets Affiliated', value = table1.iloc[len(table1) - 1, 12])
        else:
            st.metric(label = 'Credit Unions Affiliated', value = table1.iloc[len(table1) - 1, 10], delta = metric_deltas.iloc[0, 0])
            st.metric(label = 'Members Affiliated', value = table1.iloc[len(table1) - 1, 11], delta = metric_deltas.iloc[0, 1])
            st.metric(label = 'Assets Affiliated', value = table1.iloc[len(table1) - 1, 12], delta = metric_deltas.iloc[0, 2])
            st.markdown('---')
    
        with st.expander('About', expanded=True):
            st.write('''
                     - Data: NIMBLE AMS and [NCUA Call Report Data](<https://ncua.gov/analysis/credit-union-corporate-call-report-data/quarterly-data>).
                     - Includes all 'Active' status (NIMBLE) credit unions with a call report filed for most recent reporting period (NCUA).
                     - NIMBLE data is as-of month end.
                     ''')
                     
        st.markdown('---')

    with col[1]:
        if selected_group_by == 'State' or selected_group_by == 'League':
            st.markdown('#### Table 1 - Excludes Puerto Rico/Territories')
        else:
            st.markdown('#### Table 1')
        
        st.dataframe(data = table1,
                     column_config=column_configuration,
                     hide_index = True,
                     )

        st.markdown('---')

        if selected_group_by == 'State' or selected_group_by == 'League':
            st.markdown('#### Table 2 - Puerto Rico/Territories')
            table2 = getTableAFLTable_from_db(selected_afl_type, selected_group_by, selected_month, "2")

            table2['% CUs Affiliated'] = round(table2['% CUs Affiliated'] * 100, 1).astype('str') + '%'
            table2['% Memberships Affiliated'] = round(table2['% Memberships Affiliated'] * 100, 1).astype('str') + '%'
            table2['% Assets Affiliated'] = round(table2['% Assets Affiliated'] * 100, 1).astype('str') + '%'
        
            st.dataframe(data = table2, 
                         column_config=column_configuration,
                         use_container_width = True, 
                         hide_index = True,
                         )   
            st.markdown('---')


