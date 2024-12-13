# grab all of our info we need:
# Complete history of all of the following:
    # Debt
    # Deficit
    # Suplus
# Organized by Year:[{values}]
    # values will be "year":[{{"President": president,"OfficeYears:[ints]","debt":debt,"surplus/deficit":revenueMinusExpenses}, etc for each president}]

# Make a web app with docker and use streamlit or PyQT(advanced)

# #imports
import streamlit as st
import plotly.graph_objects as go
from AmericanRealityClasses import TreasuryApi as TA
import pandas as pd
import math

# needed for numbers to display without scientific notation
# pd.options.display.float_format = '{:,.2f}'.format

#Create isntance to get data
dfInstance = TA.Treasury()
BaseUrl = r'https://api.fiscaldata.treasury.gov/services/api/fiscal_service/v2/accounting/od/debt_outstanding'
dfDebt = dfInstance.getHistoricalDebtAPIData(BaseUrl)
dfPresidents = pd.read_json('AmericanRealityClasses/resources/USAPresidents.json')

# this will dL the info on every click
# dfDeficit = dfInstance.getTaxPolicyDownload() 

# manual dfDeficit comment out when a new download is needed
path = 'AmericanRealityClasses/resources/TaxPolicyCentrHistoricRevenues.xlsx'

#start on main headers
dfDeficit = pd.read_excel(path,engine='openpyxl',skiprows=6)
# drop first row is empty
dfDeficit = dfDeficit.drop(0)
# resname lost columns
dfDeficit.rename(columns={"Unnamed: 0":"Fiscal Year","Total":"Receipts Total","Total.1":"Outlays Total","Total.2":"Surplus or Deficit(-) Total"},inplace=True)
# get rid of dat at the end of table dealing wiith estimating data
estimateIndex = dfDeficit[dfDeficit['Fiscal Year'].str.contains('Estimates',case=False,na=False)].index[0]
dfDeficit = dfDeficit.iloc[:estimateIndex-2]
dfDeficit = dfDeficit[dfDeficit['Fiscal Year']!='TQ']
dfDeficit['Fiscal Year'] = dfDeficit['Fiscal Year'].astype(int)
dfDeficit['Surplus or Deficit(-) Total'] = dfDeficit['Surplus or Deficit(-) Total'] * 1_000_000


st.title("Debt & Surplus/Defiict\nby President or Year")

# User Selection Opitions
viewType = st.selectbox('Select President Or Year by:', ['President','Year'])

if viewType == "President":

    # let use select president
    president = st.selectbox("Select President", dfPresidents['name'])

    # get president data
    presidentData = dfPresidents[dfPresidents['name'] == president].iloc[0]
    startYear = int(presidentData['start_year'])
    endYear = int(presidentData['end_year'])

    debtData = dfDebt[(dfDebt['record_fiscal_year'] >= startYear) & (dfDebt['record_fiscal_year'] <= endYear)]
    deficitData = dfDeficit[(dfDeficit['Fiscal Year'] >= startYear) & (dfDeficit['Fiscal Year'] <= endYear)]

    mergerdf = pd.merge(debtData,
                        deficitData,
                        left_on='record_fiscal_year',
                        right_on='Fiscal Year',
                        how='outer',
                        suffixes=('_debt','_deficit'))
    mergerdf['record_fiscal_year'] = mergerdf['record_fiscal_year'].astype(str)

    # # shows rpresident info
    st.write(f'{president} was in office from {startYear} to {endYear}')

    # show debt vs deficit
    st.write("Debt and Deficit/Surplus furing thier turn")
    # Create a summary string

    # Data Setup for easy ploting
    chartData = pd.DataFrame({
        'Year': mergerdf['record_fiscal_year'],
        'Debt': mergerdf['debt_outstanding_amt'],
        'Deficit/Surplus': mergerdf['Surplus or Deficit(-) Total']
    })

    chartData['Year'] = chartData['Year'].astype(int)

    # Table summary
    yearsInOffice = endYear-startYear+1

    try:
        beginningDebt = chartData[(chartData['Year'] == startYear)]['Debt'].iloc[0]
        endingDebt = chartData[(chartData['Year'] == endYear)]['Debt'].iloc[0]
    except:
        beginningDebt =None
        endingDebt = None

    try:
        beginningDefict = chartData[(chartData['Year'] == startYear)]['Deficit/Surplus'].iloc[0]
        endingDefict = chartData[(chartData['Year'] == endYear)]['Deficit/Surplus'].iloc[0]
    except:
        beginningDefict = None
        endingDefict = None

    # Function to format large numbers with appropriate labels (Million, Billion, Trillion)
    def format_large_number(value):
        sign = '-' if value <0 else ""
        value = abs(value)
        if value is None or math.isnan(value):
            return "No Data"
        
        if value >= 1e12:
            return f"{sign}${value/1e12:,.2f} Trillion"
        elif value >= 1e9:
            return f"{sign}${value/1e9:,.2f} Billion"
        elif value >= 1e6:
            return f"{sign}${value/1e6:,.2f} Million"
        else:
            return f"{sign}${value:,.2f}"


    # create a new Pandas dataframe for tab
    summaryData = {
        "Start/End":[
            'Starting Debt', 'Starting Deficit',
            'Ending Debt', 'Ending Deficit/Surplus'
        ],
        "$ Amounts": [
            format_large_number(beginningDebt), format_large_number(beginningDefict),
            format_large_number(endingDebt),format_large_number(endingDefict)

        ]
    }
    summaryDf = pd.DataFrame(summaryData)
    # Function to format the table with alternating row colors (dark blue and white text)
    def color_alternating_rows(df):
        html = df.to_html(index=False, escape=False)
        
        # Adding CSS for alternating row colors
        html = html.replace('<thead>', '<thead style="background-color:#003366; color: white;">')  # Dark blue header
        rows = html.split('<tr>')
        
        for i in range(1, len(rows)):
            if i % 2 == 0:  # Even rows: dark blue background, white text
                rows[i] = f'<tr style="background-color: #003366; color: white;">' + rows[i]
            else:  # Odd rows: keep white background and default color
                rows[i] = f'<tr style="background-color: #ffffff; color: black;">' + rows[i]
        
        return ''.join(rows)

    # Display the table with alternating row colors
    st.markdown(color_alternating_rows(summaryDf), unsafe_allow_html=True)

    # Graphs
    # create our figure
    fig = go.Figure()



    # Add Debt Linechart
    fig.add_trace(go.Scatter(
        x=chartData['Year'],
        y=chartData['Debt'],
        mode='lines',
        name='Debt',
        line=dict(color='yellow'),
        hovertemplate='%{x}: $%{y} <extra></extra>',
        yaxis='y1'
    ))


    # Add Deficit/Surplus Linechart
    fig.add_trace(go.Scatter(
        x=chartData['Year'],
        y=chartData['Deficit/Surplus'],
        mode='lines',
        name='Deficit/Surplus',
        line=dict(color="red"),
        hovertemplate='%{x}: $%{y} <extra></extra>',
        yaxis='y2'
    ))

    # add a bar chart
    fig.add_trace(go.Bar(
        x=chartData['Year'],
        y=chartData['Deficit/Surplus'],
        name='Deficit/Surplus',
        marker=dict(color='blue'),
        hovertemplate='%{x}: $%{y} <extra></extra>',
        yaxis='y2',
        opacity=0.4
    ))




    fig.update_layout(
        title=f"Debt and Deficit/Surplus during {president}'s term",
        xaxis_title='Year',
        yaxis=dict(
            title='Debt ($)',
            titlefont=dict(color='yellow'),
            tickfont=dict(color='yellow')
        ),
        yaxis2=dict(
            title='Deficit/Surplus ($)',
            titlefont=dict(color='red'),
            tickfont=dict(color='red'),
            overlaying='y',
            side='right'
        ),    
        hovermode='x unified',
        template='plotly_dark',
        barmode='group',
        width=2200,
        height=625
    )

    #show plotyly figure in Streamlit
    st.plotly_chart(fig)

elif viewType == 'Year':
    # Add a range slider for the user to pick a range of years
    min_year = int(dfDebt['record_fiscal_year'].min())
    max_year = int(dfDebt['record_fiscal_year'].max())
    selected_years = st.slider("Select Year Range", min_year, max_year, (min_year, max_year))

    # Filter the data for the selected year range
    debtData = dfDebt[(dfDebt['record_fiscal_year'] >= selected_years[0]) & (dfDebt['record_fiscal_year'] <= selected_years[1])]
    deficitData = dfDeficit[(dfDeficit['Fiscal Year'] >= selected_years[0]) & (dfDeficit['Fiscal Year'] <= selected_years[1])]

    mergerdf = pd.merge(
        debtData,
        deficitData,
        left_on='record_fiscal_year',
        right_on='Fiscal Year',
        how='outer',
        suffixes=('_debt', '_deficit')
    )
    mergerdf['record_fiscal_year'] = mergerdf['record_fiscal_year'].astype(str)

    # Data Setup for easy plotting
    chartData = pd.DataFrame({
        'Year': mergerdf['record_fiscal_year'],
        'Debt': mergerdf['debt_outstanding_amt'],
        'Deficit/Surplus': mergerdf['Surplus or Deficit(-) Total']
    })
    chartData['Year'] = chartData['Year'].astype(int)

    # Display the selected year range
    st.write(f"Selected Year Range: {selected_years[0]} - {selected_years[1]}")

    # Function to format large numbers with appropriate labels (Million, Billion, Trillion)
    def format_large_number(value):
        sign = '-' if value < 0 else ""
        value = abs(value)
        if value is None or math.isnan(value):
            return "No Data"
        
        if value >= 1e12:
            return f"{sign}${value / 1e12:,.2f} Trillion"
        elif value >= 1e9:
            return f"{sign}${value / 1e9:,.2f} Billion"
        elif value >= 1e6:
            return f"{sign}${value / 1e6:,.2f} Million"
        else:
            return f"{sign}${value:,.2f}"

    # Function to format the table with alternating row colors (dark blue and white text)
    def color_alternating_rows(df):
        html = df.to_html(index=False, escape=False)
        
        # Adding CSS for alternating row colors
        html = html.replace('<thead>', '<thead style="background-color:#003366; color: white;">')  # Dark blue header
        rows = html.split('<tr>')
        
        for i in range(1, len(rows)):
            if i % 2 == 0:  # Even rows: dark blue background, white text
                rows[i] = f'<tr style="background-color: #003366; color: white;">' + rows[i]
            else:  # Odd rows: keep white background and default color
                rows[i] = f'<tr style="background-color: #ffffff; color: black;">' + rows[i]
        
        return ''.join(rows)

    # Table summary for the selected year range
    try:
        beginningDebt = chartData[(chartData['Year'] == selected_years[0])]['Debt'].iloc[0]
        endingDebt = chartData[(chartData['Year'] == selected_years[1])]['Debt'].iloc[0]
    except:
        beginningDebt = None
        endingDebt = None

    try:
        beginningDeficit = chartData[(chartData['Year'] == selected_years[0])]['Deficit/Surplus'].iloc[0]
        endingDeficit = chartData[(chartData['Year'] == selected_years[1])]['Deficit/Surplus'].iloc[0]
    except:
        beginningDeficit = None
        endingDeficit = None

    summaryData = {
        "Start/End": [
            'Starting Debt', 'Starting Deficit',
            'Ending Debt', 'Ending Deficit/Surplus'
        ],
        "$ Amounts": [
            format_large_number(beginningDebt), format_large_number(beginningDeficit),
            format_large_number(endingDebt), format_large_number(endingDeficit)
        ]
    }
    summaryDf = pd.DataFrame(summaryData)
    st.markdown(color_alternating_rows(summaryDf), unsafe_allow_html=True)

    # Graphs
    fig = go.Figure()

    # Add Debt Linechart
    fig.add_trace(go.Scatter(
        x=chartData['Year'],
        y=chartData['Debt'],
        mode='lines',
        name='Debt',
        line=dict(color='yellow'),
        hovertemplate='%{x}: $%{y} <extra></extra>',
        yaxis='y1'
    ))

    # Add Deficit/Surplus Linechart
    fig.add_trace(go.Scatter(
        x=chartData['Year'],
        y=chartData['Deficit/Surplus'],
        mode='lines',
        name='Deficit/Surplus',
        line=dict(color="red"),
        hovertemplate='%{x}: $%{y} <extra></extra>',
        yaxis='y2'
    ))

    # Add a bar chart
    fig.add_trace(go.Bar(
        x=chartData['Year'],
        y=chartData['Deficit/Surplus'],
        name='Deficit/Surplus',
        marker=dict(color='blue'),
        hovertemplate='%{x}: $%{y} <extra></extra>',
        yaxis='y2',
        opacity=0.4
    ))

    fig.update_layout(
        title=f"Debt and Deficit/Surplus from {selected_years[0]} to {selected_years[1]}",
        xaxis_title='Year',
        yaxis=dict(
            title='Debt ($)',
            titlefont=dict(color='yellow'),
            tickfont=dict(color='yellow')
        ),
        yaxis2=dict(
            title='Deficit/Surplus ($)',
            titlefont=dict(color='red'),
            tickfont=dict(color='red'),
            overlaying='y',
            side='right'
        ),
        hovermode='x unified',
        template='plotly_dark',
        barmode='group',
        width=2200,
        height=625
    )

    # Show the Plotly figure in Streamlit
    st.plotly_chart(fig)


