import requests
import bs4
from datetime import datetime, timezone, timedelta
import PySimpleGUI as sg
import yfinance as yf
import re
from finvizfinance.quote import finvizfinance
import matplotlib.pyplot as plt
import numpy as np
import io
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
import random
import pandas as pd


theme_dict = {'BACKGROUND': '#2B475D',
                'TEXT': '#FFFFFF',
                'INPUT': '#F2EFE8',
                'TEXT_INPUT': '#000000',
                'SCROLL': '#F2EFE8',
                'BUTTON': ('#000000', '#C2D4D8'),
                'PROGRESS': ('#FFFFFF', '#C7D5E0'),
                'BORDER': 0,'SLIDER_DEPTH': 0, 'PROGRESS_DEPTH': 0}

BORDER_COLOR = '#C7D5E0'
DARK_HEADER_COLOR = '#1B2838'
BPAD_TOP = ((10,10), (10, 10))
BPAD_LEFT = ((10,10), (0, 0))
BPAD_LEFT_INSIDE = (0, (10, 0))
BPAD_RIGHT = ((10,10), (10, 0))

font = ('Times New Roman', 12)

dark_theme_bg = 'black'
dark_theme_fg = 'white'
dark_theme_outline = '#505050'




class StockInfoApp:
    def __init__(self):
        self.ticker = None
        sg.theme('Black')

        # Define dark theme colors
        dark_theme_bg = 'black'
        dark_theme_fg = 'white'
        dark_theme_outline = '#505050'

        # Ticker Frame
        self.ticker_frame = sg.Column([
            [sg.Text('Ticker:', text_color='white'),
             sg.Input(key='-TICKER-', text_color='black', size=(6, None), background_color='white', enable_events=True),
             sg.Button('Search', key='-SEARCH-', button_color=('white', 'green')),
             sg.Button('More', key='-MORE-', button_color=('white', 'blue'), pad=(5, 5)),  
             sg.Text('', key='-ERROR-', text_color='red')]  
        ], background_color=dark_theme_bg)

        self.top_frame1 = sg.Column([[sg.Multiline(size=(40, 3), key='-f1-', background_color=dark_theme_bg, text_color=dark_theme_fg, auto_refresh=True, disabled=True, no_scrollbar=True)]], background_color=dark_theme_bg)
        self.top_frame2 = sg.Column([
            [sg.Multiline(size=(0, 0), key='-f2-', pad=(0, 0), background_color=dark_theme_bg, text_color=dark_theme_fg, auto_refresh=True, disabled=True, no_scrollbar=True)],
            [sg.Frame('', [[sg.Image(key='-PLOT-')]], background_color=dark_theme_bg, border_width=0, pad=BPAD_TOP)]
        ], background_color=dark_theme_bg)
        self.top_frame3 = sg.Column([[sg.Multiline(size=(42, 3), key='-f3-', background_color=dark_theme_bg, text_color=dark_theme_fg, auto_refresh=True, disabled=True, no_scrollbar=True)]], background_color=dark_theme_bg)


        self.middle_left_frame = sg.Column([[sg.Multiline(size=(40, 13), key='-INFO-', background_color=dark_theme_bg, text_color=dark_theme_fg, auto_refresh=True, reroute_stdout=True, disabled=True, no_scrollbar=True)]], background_color=dark_theme_bg)
        self.finviz_frame = sg.Column([[sg.Multiline(size=(30, 13), key='-FINVIZ-', background_color=dark_theme_bg, text_color=dark_theme_fg, auto_refresh=True, reroute_stdout=True, disabled=True, no_scrollbar=True)]], background_color=dark_theme_bg)
        self.finviz_frame2 = sg.Column([[sg.Multiline(size=(10, 13), key='-FINVIZ2-',pad=(0, 0), background_color=dark_theme_bg, text_color=dark_theme_fg, auto_refresh=True, reroute_stdout=True, disabled=True, no_scrollbar=True)]], background_color=dark_theme_bg)
        self.placeholder_frame = sg.Column([[sg.Multiline(size=(40, 13), key='-PLACEHOLDER-', background_color=dark_theme_bg, text_color=dark_theme_fg, auto_refresh=True, reroute_stdout=True, disabled=True, no_scrollbar=True)]], background_color=dark_theme_bg)

        # Earnings Frame
        self.earnings_frame = sg.Column([[sg.Multiline(size=(86, 8), key='-EARNINGS-', background_color=dark_theme_bg, text_color=dark_theme_fg, auto_refresh=True, reroute_stdout=True, disabled=True, no_scrollbar=True)]], background_color=dark_theme_bg)
        self.earnings_frame2 = sg.Column([[sg.Multiline(size=(63, 10), key='-EARNINGS2-', background_color=dark_theme_bg, text_color=dark_theme_fg, auto_refresh=True, reroute_stdout=True, disabled=True, no_scrollbar=True)]], background_color=dark_theme_bg)
        self.earnings_chart = sg.Column([[sg.Image(key='-EARNINGS_CHART-')]], background_color=dark_theme_bg)


        self.layout = [
            #[sg.Text('Stock Information', font=('Times New Roman', 12), text_color='white', background_color=dark_theme_bg)],
            [self.ticker_frame],
            [sg.Input("", key='Input1', visible=False)],
            [sg.Input("", key='Input2', visible=False)],
            [sg.Column([[self.top_frame1, self.top_frame3]], element_justification='stretch')],  
            [sg.Column([[self.middle_left_frame, self.finviz_frame, self.finviz_frame2,
                         ]], element_justification='stretch')],
            [sg.Column([[self.earnings_frame]], element_justification='stretch')],  # Moved earnings chart to the bottom
            [self.earnings_chart],  # Moved earnings chart to the bottom
            [sg.Frame('', [[sg.Image(key='-PLOT-')]], background_color=dark_theme_bg, border_width=0, pad=BPAD_TOP)],  # Add comma here
        ]

        window_location = ((800,-1080))
        self.window = sg.Window('Stock Information', self.layout, grab_anywhere=True, finalize=True, location=window_location)
        self.window['Input1'].bind("<Return>", "_Enter")
        self.window['Input1'].bind("<\>", "_Focus")
        # Hotkey to focus on the ticker input box
        self.window.bind("<\>", '_Focus')
        self.window.bind("<Return>", "_Enter")

    def run(self):
        while True:
            event, values = self.window.read()
            if event == sg.WINDOW_CLOSED:
                break
            if event == '-SEARCH-' or event == "_Enter":
                try:
                    ticker = values['-TICKER-'].upper()
                    self.ticker = ticker  # Assign the value to self.ticker
                    self.show_stock_info(ticker)
                except Exception as e:
                    self.window['-ERROR-'].update(str(e))
            elif event == '_Focus':
                self.window['-TICKER-'].set_focus(True)
                self.ticker = None  # Reset self.ticker when focusing on the input field
            if event == '-MORE-':
                if self.ticker:
                    # Fetch and display Stocktwits data regardless of the error
                    stocktwits_data = self.get_stocktwits_data(self.ticker)
                    if isinstance(stocktwits_data, dict):
                        self.display_stocktwits_data(stocktwits_data)                 

    def show_stock_info(self, ticker):
        plot_image = None

        self.window['-INFO-'].update('')
        self.window['-EARNINGS-'].update('')
        self.window['-FINVIZ-'].update('')
        self.window['-FINVIZ2-'].update('')
        self.window['-PLOT-'].update('')
        self.window['-f1-'].update('')
        self.window['-f3-'].update('')
        self.window['-EARNINGS_CHART-'].update('')




        try:
            finviz_stock = finvizfinance(ticker.lower())
            finviz_info = finviz_stock.ticker_fundament()

            # Display Finviz data
            keys_to_display = ['Market Cap', 'Short Float', 'Shs Float', 'Country', 'Insider Own', 'Inst Own']
            max_key_length = max(len(key) for key in keys_to_display)

            for key in keys_to_display:
                formatted_value = finviz_info.get(key, 'N/A')
                padding = max_key_length - len(key)
                formatted_line = f"{key}{' ' * padding}:{formatted_value}"
                
                # Determine text color for 'country' key
                if key == 'Country':
                    if formatted_value == 'USA':
                        text_color1 = 'limegreen'
                    elif formatted_value == 'China':
                        text_color1 = 'red'
                    else:
                        text_color1 = 'yellow'
                    self.window['-FINVIZ-'].print(formatted_line, text_color=text_color1, font=('Times New Roman', 12))
                else:
                    self.window['-FINVIZ-'].print(formatted_line, text_color='white', font=('Times New Roman', 12))

            stock = yf.Ticker(ticker)
            info = stock.info
            filtered_info = self.filter_info(info)

            self.display_info(filtered_info)


            plot_data = {k: v for k, v in filtered_info.items() if k in ['fiftyTwoWeekLow', 'fiftyTwoWeekHigh', 'dayLow', 'dayHigh', 'targetLowPrice', 'targetHighPrice', 'currentPrice', 'fiftyDayAverage', 'twoHundredDayAverage']}
            plot_fig, plot_image = self.plot_boxplot(plot_data)
            self.window['-PLOT-'].update(data=plot_image)
            self.window['-EARNINGS_CHART-'].update(data=plot_image)

            margin_info = self.calculate_margin(float(filtered_info.get('dayLow', '0').replace('$', '').replace(',', '')))
            self.display_margin_info(margin_info)

        except Exception as e:
            self.window['-ERROR-'].print(f"Error fetching data: {e}")

        # Fetch and display earnings information regardless of the error
        self.show_earnings_info(ticker)

        try:
            # Generate URL with today's date
            today = datetime.today().strftime('%Y-%m-%d')
            url = f"https://finance.yahoo.com/calendar/earnings?day={today}"
            
            # Fetch earnings calendar page
            response = requests.get(url)
            if response.status_code == 200:
                soup = bs4.BeautifulSoup(response.text, 'html.parser')
                quote_links = soup.find_all('a', {'data-test': 'quoteLink'})
                tickers = [link['href'].split('/')[-1] for link in quote_links]  # Extract tickers
                tickers_unique = list(set(tickers))  # Remove duplicates
                tickers_filtered = [ticker for ticker in tickers_unique if len(ticker) <= 4]  # Filter by ticker length
                tickers_str = '\n'.join(tickers_filtered)  # Join tickers into separate lines
                self.window['-FINVIZ2-'].update(tickers_str)
            else:
                self.window['-FINVIZ2-'].update("Failed to retrieve earnings calendar.")
        except Exception as e:
            self.window['-ERROR-'].update(f"Error: {e}")


        
    def get_earnings_data(self, ticker):
        two_years_ago = datetime.now() - timedelta(days=730)  # Calculate date two years ago
        url = f"https://www.alphaquery.com/stock/{ticker}/earnings-history"
        try:
            response = requests.get(url)
            if response.status_code == 200:
                soup = bs4.BeautifulSoup(response.text, 'html.parser')
                table = soup.find('table')
                if table:
                    rows = table.find_all('tr')[1:]  # Skip header row
                    earnings_data = []
                    for row in rows:
                        columns = row.find_all('td')
                        date = columns[0].text.strip()
                        # Format the date to match yfinance's expected format
                        formatted_date = datetime.strptime(date, '%Y-%m-%d').strftime('%Y-%m-%d')
                        if datetime.strptime(formatted_date, '%Y-%m-%d') >= two_years_ago:  # Check if the date is within the past two years
                            estimated_eps = columns[2].text.strip()
                            actual_eps = columns[3].text.strip()

                            # Fetch historical prices for the earnings date
                            earnings_low, earnings_high = self.get_earnings_prices(ticker, formatted_date)

                            earnings_data.append((formatted_date, earnings_low, earnings_high, estimated_eps, actual_eps))
                    return earnings_data
                else:
                    return None
            else:
                return None
        except Exception as e:
            self.window['-ERROR-'].update(f"Error fetching earnings data: {e}")
            return None
        
    def polygon_api(self, ticker, dates, multiplier='5', timespan='minute', api_key="4Jq5Ew8tmnwkv_Q8CMEvNGnwAqJp2AzX"):
        dataframes = []  # List to store dataframes for each date
        for date in dates:
            # Format the date as a string
            if isinstance(date, datetime):
                date = date.strftime('%Y-%m-%d')        
        url = f"https://api.polygon.io/v2/aggs/ticker/{ticker}/range/{multiplier}/{timespan}/{date}/{date}?apiKey={api_key}"
        response = requests.get(url)
        if response.status_code == 200:
            json_data = response.json()
            df = pd.DataFrame(json_data['results'])
            df['timestamp'] = pd.to_datetime(df['t'], unit='ms') - pd.Timedelta(hours=5)
            df.set_index('timestamp', inplace=True)
            dataframes.append(df)
        else:
            print(f"Failed to fetch data from Polygon API: {response.text}")

        #if i == 3:
            #time.sleep(61)


        if dataframes:
            return pd.concat(dataframes)
        else:
            return pd.DataFrame()  # Return an empty DataFrame if no data was fetched

    def get_earnings_prices(self, ticker, date):
        try:
            earnings_data = self.get_earnings_data(ticker)
            dates = [data[0] for data in earnings_data] 

            earnings = self.polygon_api(ticker, dates)


            if not earnings.empty:
                pre_market = earnings.between_time('04:00', '09:30')
                market = earnings.between_time('09:30', '16:00')
                after_market = earnings.between_time('16:00', '20:00')

                earnings_low = {
                    'pre_market': "${:.2f}".format(round(pre_market['l'].min(), 2)) if not pre_market.empty else 'N/A',
                    'market': "${:.2f}".format(round(market['l'].min(), 2)) if not market.empty else 'N/A',
                    'after_market': "${:.2f}".format(round(after_market['l'].min(), 2)) if not after_market.empty else 'N/A'
                }
                earnings_high = {
                    'pre_market': "${:.2f}".format(round(pre_market['h'].max(), 2)) if not pre_market.empty else 'N/A',
                    'market': "${:.2f}".format(round(market['h'].max(), 2)) if not market.empty else 'N/A',
                    'after_market': "${:.2f}".format(round(after_market['h'].max(), 2)) if not after_market.empty else 'N/A'
                }
                return str(earnings_low), str(earnings_high)
            else:
                return 'N/A', 'N/A'
        except Exception as e:
            self.window['-ERROR-'].update(f"Error fetching earnings low/high for {date}: {e}")
            return 'N/A', 'N/A'

    def show_earnings_info(self, ticker):
        plt.clf()
        earnings_data = self.get_earnings_data(ticker)
        if earnings_data:
            # Prepare data for plotting
            dates = [datetime.strptime(date, '%Y-%m-%d') for date, _, _, _, _ in earnings_data]
            # Extract earnings_low, earnings_high, estimated_eps, and actual_eps with error handling
            earnings_low = {'pre_market': [], 'market': [], 'after_market': []}
            earnings_high = {'pre_market': [], 'market': [], 'after_market': []}
            estimated_eps = []
            actual_eps = []
            for _, low, high, eps, actual in earnings_data:
                try:
                    low_prices = eval(low) if low not in ['N/A', '--'] else {'pre_market': 'N/A', 'market': 'N/A', 'after_market': 'N/A'}
                    high_prices = eval(high) if high not in ['N/A', '--'] else {'pre_market': 'N/A', 'market': 'N/A', 'after_market': 'N/A'}
                except SyntaxError:
                    continue
                for market in ['pre_market', 'market', 'after_market']:
                    earnings_low[market].append(low_prices[market])
                    earnings_high[market].append(high_prices[market])
                estimated_eps.append(float(eps.replace('$', '')) if eps not in ['N/A', '--'] else 0.00)
                actual_eps.append(float(actual.replace('$', '')) if actual not in ['N/A', '--'] else 0.00)



            # Calculate percentage movement label
        percentage_movement = {market: [(high - low) / low * 100 if low != 0 else 0 for low, high in zip(earnings_low[market], earnings_high[market])] for market in ['pre_market', 'market', 'after_market']}
        percentage_movement_label = {market: [f'{round(movement)}%' if movement != 0 else '' for movement in percentage_movement[market]] for market in ['pre_market', 'market', 'after_market']}



        fig, ax1 = plt.subplots(figsize=(6, 2.5))
        ax2 = ax1.twinx()

        for date, low, high, label in zip(dates, earnings_low, earnings_high, percentage_movement_label):
            if label:  # Only plot label if it's not empty
                ax1.text(date, (low + high) / 2, label, fontsize=10, ha='center', va='center', color='black', rotation=45)

        for market in ['pre_market', 'market', 'after_market']:
            for date, low, high in zip(dates, earnings_low[market], earnings_high[market]):
                if low != 'N/A' and high != 'N/A':
                    ax1.plot([date, date], [low, high], color='lightblue', linewidth=30)



            ax1.yaxis.set_major_locator(plt.MaxNLocator(nbins=10))  # Adjust the number of ticks as needed
            ax1.set_ylabel('Price', fontsize=7)
            ax2.set_ylabel('EPS', fontsize=7)
            ax1.grid(color='lightgray', linestyle='-', linewidth=0.5)
            ax1.tick_params(axis='x', rotation=45, labelsize=6)
            ax1.set_title('')
            ax1.set_xlim(min(dates), max(dates))
            ax1.set_ylim(min(earnings_low) * 0.90, max(earnings_high) * 1.10)
            plt.tight_layout()

            # Convert plot to an image buffer
            buf = io.BytesIO()
            fig.savefig(buf, format='png')
            buf.seek(0)

            self.window['-EARNINGS-'].update(
                ''.join([
                    f'Date: {date}, '
                    f'Low (pre-market): {low["pre_market"]}, Low (market): {low["market"]}, Low (after-market): {low["after_market"]}, '
                    f'High (pre-market): {high["pre_market"]}, High (market): {high["market"]}, High (after-market): {high["after_market"]}, '
                    f'Estimated EPS: {eps}, Actual EPS: {actual}\n'
                    for date, low, high, eps, actual in zip(dates, earnings_low, earnings_high, estimated_eps, actual_eps)
                ])
            )

            self.window['-EARNINGS_CHART-'].update(data=buf.getvalue())

            # Close the plot to prevent multiple windows
            plt.close(fig)
        else:
            self.window['-EARNINGS-'].update("No earnings data available.\n")
     

    def get_stocktwits_data(self, ticker):
        try:
            url = f"https://stocktwits.com/symbol/{ticker}"
            chrome_options = Options()
            chrome_options.add_argument("--headless")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3")

            service = Service('C:\\Users\\ewhip\\Desktop\\webdriver\\chromedriver.exe')
            driver = webdriver.Chrome(service=service, options=chrome_options)

            driver.get(url)
            body_element = driver.find_element("tag name", "body")
            text = body_element.text.split('\n')

            # Limit the parsing to the first 100 lines
            text = text[:100]

            # Find the first instance of 'Watchers'
            watchers_index = text.index('Watchers')
            watchers = text[watchers_index + 1] if watchers_index != -1 else "Watchers count not found"

            # Find the first instance of 'Sentiment'
            sentiment_index = text.index('Sentiment')
            sentiment_score = text[sentiment_index + 14] if sentiment_index != -1 else "Sentiment score not found"
            sentiment_text = text[sentiment_index + 15] if sentiment_index != -1 else "Sentiment text not found"

            # Find the first instance of 'Message Vol.'
            message_volume_index = text.index('Message Vol.')
            message_volume_score = text[message_volume_index + 18] if message_volume_index != -1 else "Message Volume score not found"
            message_volume_text = text[message_volume_index + 19] if message_volume_index != -1 else "Message Volume text not found"

            driver.quit()
            return {
                'Watchers'    : watchers,
                'Sentiment'   : f"{sentiment_score} - {sentiment_text}",
                'Message Volume': f"{message_volume_score} - {message_volume_text}"
            }
        except Exception as e:
            self.window['-ERROR-'].update(f"Error: {e}")


    def display_stocktwits_data(self, stocktwits_data):
        watchers = stocktwits_data.get('Watchers', 'Watchers count not found')
        sentiment = stocktwits_data.get('Sentiment', 'Sentiment not found')
        message_volume = stocktwits_data.get('Message Volume', 'Message Volume not found')

        # Prepare the text to display
        info_text = f"Watchers      : {watchers}\nSentiment     : {sentiment}\nMessage Vol : {message_volume}"

        # Update the -f3- frame with the StockTwits data
        self.window['-f3-'].update(info_text)





    def filter_info(self, info):
        desired_keys = [
            
            "floatShares", "sharesShort", "heldPercentInsiders", "heldPercentInstitutions",
            "shortPercentOfFloat","dayLow", "dayHigh", "averageVolume", "averageVolume10days",
            "fiftyTwoWeekLow", "fiftyTwoWeekHigh",
            "fiftyDayAverage", "twoHundredDayAverage", "sharesOutstanding",
            "sharesShortPriorMonth", "sharesShortPreviousMonthDate", "dateShortInterest",
            "sharesPercentSharesOut", 
            "52WeekChange", "lastDividendValue", "currentPrice",
            "targetHighPrice", "targetLowPrice"
        ]
        
        filtered_info = {key: self.format_value(key, info.get(key, 'N/A')) for key in desired_keys}
        return filtered_info





    def format_float_Shares(self, float_Shares):
        if float_Shares >= 10**9:
            return f"{float_Shares / 10**9:.2f}B"
        elif float_Shares >= 10**6:
            return f"{float_Shares / 10**6:.2f}M"
        elif float_Shares >= 10**3:
            return f"{float_Shares / 10**3:.2f}K"
        else:
            return f"{float_Shares:.2f}"

    def format_shares_Short(self, shares_Short):
        if shares_Short >= 10**9:
            return f"{shares_Short / 10**9:.2f}B"
        elif shares_Short >= 10**6:
            return f"{shares_Short / 10**6:.2f}M"
        elif shares_Short >= 10**3:
            return f"{shares_Short / 10**3:.2f}K"
        else:
            return f"{shares_Short:.2f}"

    def format_value(self, key, value):
        formats = {
            "dayLow": "${:.2f}".format,
            "dayHigh": "${:.2f}".format,
            "fiftyTwoWeekLow": "${:.2f}".format,
            "fiftyTwoWeekHigh": "${:.2f}".format,
            "fiftyDayAverage": "${:.2f}".format,
            "twoHundredDayAverage": "${:.2f}".format,
            "previousClose": "${:.2f}".format,
            "volume": "{:,}".format,
            "averageVolume": "{:,}".format,
            "averageVolume10days": "{:,}".format,
            "floatShares": self.format_float_Shares,
            "sharesShortPriorMonth": "{:,}".format,
            "shortRatio": "{:.2f}".format,
            "sharesPercentSharesOut": lambda x: "{:.2f}%".format(x * 100),
            "heldPercentInsiders": lambda x: "{:.2f}%".format(x * 100),
            "heldPercentInstitutions": lambda x: "{:.2f}%".format(x * 100),
            "shortPercentOfFloat": lambda x: "{:.2f}%".format(x * 100),
            "52WeekChange": lambda x: "{:.2f}%".format(x * 100),
            "currentPrice": "${:.2f}".format,
            "targetHighPrice": "${:.2f}".format,
            "targetLowPrice": "${:.2f}".format,
            "sharesShortPreviousMonthDate": self.format_date,
            "dateShortInterest": self.format_date,
        }
        if key in formats:
            return formats[key](value)
        return value

    def format_date(self, timestamp):
        if timestamp:
            return datetime.fromtimestamp(timestamp, timezone.utc).strftime('%Y-%m-%d')
        else:
            return 'N/A'

    def display_info(self, info):
  
        label_mapping = {
            "fiftyTwoWeekLow": "52W Low",
            "fiftyTwoWeekHigh": "52W High",
            "heldPercentInsiders": "Insiders",
            "averageVolume10days": "Avg Vol 10 day",
            "twoHundredDayAverage": "200 Day Avg.",
            "heldPercentInstitutions":"Institutions",
            "sharesShortPriorMonth":"Prev Share Short",
            "sharesShortPreviousMonthDate":"Date of Short",
            "twoHundredDayAverage":"200 Day Avg",
            "sharesPercentSharesOut":"%of Shares Out",
            "shortPercentOfFloat":"Short Float",
            "fiftyDayAverage":"50 Day Avg",
    }

        max_key_length = max(len(label_mapping.get(key, key)) for key in info.keys())

        for key, value in info.items():
            padding = max_key_length - len(label_mapping.get(key, key))
            formatted_key = f"{label_mapping.get(key, key)}{' ' * padding}  :"


            self.window['-INFO-'].print(f"{formatted_key} {value}", font=('Times New Roman', 12))



    def plot_boxplot(self, info, fig_width=6, fig_height=1.4):
        # Convert the values to floats
        values = {k: float(v.replace('$', '')) for k, v in info.items()}

        # Create a figure and axis object
        fig, ax = plt.subplots(figsize=(fig_width, fig_height))

        # Draw the thin black line
        ax.plot([min(values['targetLowPrice'], values['fiftyTwoWeekLow'], values['currentPrice'], values['dayLow']),
                 max(values['targetHighPrice'], values['fiftyTwoWeekHigh'], values['dayHigh'])],
                [1, 1], color='black', linewidth=1)

        # Adjust marker spacing to reduce overlap
        marker_spacing = 0.75  # Adjust as needed
        x_values = [values['fiftyTwoWeekLow'], values['dayLow'], values['currentPrice'], values['dayHigh'], values['fiftyTwoWeekHigh'], values['twoHundredDayAverage'], values['fiftyDayAverage'], values['targetLowPrice'], values['targetHighPrice']]
        x_values_spaced = [x + random.uniform(-marker_spacing, marker_spacing) for x in x_values]

        markers = ['<', '|', '|', '|', '>', 'x', 'x','o', 'o']
        colors = ['orange', 'blue', 'green', 'blue', 'orange', 'purple', 'purple','gray', 'gray']
        sizes = [100, 100, 500, 100, 100, 50, 30, 30]  
        labels = ['52WL', 'DayL', 'Current', 'DayH', '52WH', '200D/50D', 'TargetL&H']

        for x, marker, color, size, label in zip(x_values_spaced, markers, colors, sizes, labels):
            ax.scatter(x, 1, color=color, marker=marker, s=size, label=label)

        # Customize legend with colored labels
        handles, labels = ax.get_legend_handles_labels()
        legend_labels = [(plt.Line2D([0], [0], marker='o', color='w', markerfacecolor=color, markersize=8), label) for color, label in zip(colors, labels)]

        ax.legend(handles=[handle for handle, label in legend_labels], labels=[label for handle, label in legend_labels], loc='upper center', bbox_to_anchor=(0.5, 1.2), shadow=True, ncol=7, fontsize=6)

        # Hide y-axis
        ax.get_yaxis().set_visible(False)

        # Set x-axis label
        #ax.set_xlabel('Price in $')

        # Add grid
        ax.grid(color='lightgray', linestyle='-', linewidth=0.35)

        # Adjust x-axis limits
        ax.set_xlim(values['fiftyTwoWeekLow'], values['fiftyTwoWeekHigh'])

        # Tight layout to fit plot within figure size
        plt.tight_layout()

        # Convert plot to an image buffer
        buf = io.BytesIO()
        fig.savefig(buf, format='png')
        buf.seek(0)

        plt.close('all')


        # Return both the Figure object and the image buffer
        return fig, buf.getvalue()


    def display_finviz_info(self, finviz_info):
        keys_to_display = ['Market Cap', 'Short Float', 'Shs Float', 'Country', 'Insider Own', 'Inst Own']
        max_key_length = max(len(key) for key in keys_to_display)

        for key in keys_to_display:
            formatted_value = finviz_info.get(key, 'N/A')
            padding = max_key_length - len(key)
            formatted_line = f"{key}{' ' * padding} : {formatted_value}"
            
            # Determine text color based on the Short Float percentage value
            if key == 'Short Float' and '%' in formatted_value:
                short_float_percentage = float(formatted_value.split('%')[0])
                if short_float_percentage > 10:
                    text_color3 = 'red'
                elif 6 <= short_float_percentage <= 10:
                    text_color3 = 'yellow'
                else:
                    text_color3 = 'limegreen'
            else:
                text_color3 = 'white'  # Default color
            
            # Print the line with the appropriate text color
            self.window['-FINVIZ-'].print(formatted_line, text_color=text_color3, font=('Times New Roman', 12))


    def calculate_margin(self, lowest_price):
        lowest_price = float(lowest_price)  # Convert to float
        if lowest_price > 16.67:
            margin_percentage = 30
        elif lowest_price > 5:
            margin_percentage = (((1000 / lowest_price) * 5) / 1000) * 100
        elif lowest_price >= 2.5:
            margin_percentage = 100
        else:
            margin_percentage = (((1000 / lowest_price) * 2.5) / 1000) * 100

        margin_amount = (1000 * margin_percentage) / 100
        margin_amount_rounded = round(margin_amount)  # Round to the nearest whole dollar
        return f"{margin_percentage:.2f}% (${margin_amount_rounded})"  # Return the rounded value

    def display_margin_info(self, margin_info):
        margin_percentage = float(margin_info.split('%')[0])  # Extract the percentage value
        # Check if the margin percentage is greater than 50
        if margin_percentage > 50:
            text_color2 = 'yellow'
        else:
            text_color2 = 'white'  # or any other default color
    
        # Print the margin info with the appropriate text color
        self.window['-FINVIZ-'].print(f"Margin Req : {margin_info}", text_color=text_color2, font=('Times New Roman', 12))


if __name__ == "__main__":
    app = StockInfoApp()
    app.run()
