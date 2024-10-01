import sys
from datetime import datetime
import pandas as pd
import numpy as np
import plotly.express as px
from bs4 import BeautifulSoup
import re

####################################################################################################
# BRIEFING /----------------------------------------------------------------------------------------
# This application was created mainly for use with Hotmart search pages, but without the need for scraping, so as not to infringe any rules.
# The data is manually collected from the website, by Copy & Pasting the HTML code and saving it as a TXT file, then the application searches the TXT file and converts all relevant data into a DataFrame and exports it as a CSV file.
####################################################################################################

# Open the TXT file and get its text
def get_file_text(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read()
    except FileNotFoundError:
        return "\nERROR: File Not Found!\n"
    except Exception as e:
        return f"\nERROR:\n{e}\n"


# Extract infos from each div with the class_name, returning a list of dict's
def extract_info_from_divs(html, class_name):
    try:
        soup = BeautifulSoup(html, 'html.parser')
        divs = soup.find_all('div', class_=class_name)
        result = []
        
        for div in divs:
            info = {}

            # Extract product url from <a> inside the <href>
            a = div.find('a')
            if a and 'href' in a.attrs:
                info['product_url'] = "https://app.hotmart.com" + a['href']

            # Extract image src from <img> inside the <div>
            img = div.find('img')
            if img and 'src' in img.attrs:
                info['img_src'] = img['src']

            # Extract text from <span> with class "product-name" inside the <div>
            span = div.find('span', class_='product-name')
            if span:
                info['product_name'] = span.get_text()

            # Extract text from <p> with specified class inside the <div>
            p = div.find('p', class_='_mb-0 _text-3 _text-md-4 _text-green _font-weight-light')
            if p:
                p_text = p.get_text().strip()
                parts = p_text.split(maxsplit=1)  # Split into at most 2 parts
                if len(parts) == 2:
                    info['currency'] = parts[0]  # The currency part
                    info['commission'] = float(parts[1].replace('.', '').replace(',', '.'))  # The numeric part
                else:
                    info['commission'] = float(p_text.replace('.', '').replace(',', '.'))  # Fallback
            else:
                info['currency'] = " "
                info['commission'] = 0.0

            # Extract text from another <p> with class "_mb-0 _text-1 _text-gray-500"
            max_price_p = div.find('p', class_='_mb-0 _text-1 _text-gray-500')
            if max_price_p:
                max_price_text = max_price_p.get_text().strip()
                match = re.search(r'[\d.,]+', max_price_text)
                if match:
                    numeric_value = match.group(0).replace('.', '').replace(',', '.')
                    info['max_price'] = float(numeric_value)
                else:
                    info['max_price'] = 0.0  # Default value if not found
            else:
                info['max_price'] = 0.0  # Default value if not found

            # Extract all <span> elements with class "_mr-1 _text-1 _text-gray-800"
            comment_rating_spans = div.find_all('span', class_='_mr-1 _text-1 _text-gray-800')
            if comment_rating_spans:
                # Get the first <span> for comment_rating
                info['comment_rating'] = float(comment_rating_spans[0].get_text().strip())
                # Get the second <span> for temperature
                if len(comment_rating_spans) > 1:
                    temperature_text = comment_rating_spans[1].get_text().strip()
                    info['temperature'] = int(temperature_text.replace('°', ''))  # Remove '°' and convert to int
                else:
                    info['temperature'] = 0  # Default value if second span not found
            else:
                info['comment_rating'] = 0.0  # Default value if not found
                info['temperature'] = 0  # Default value if not found

            # Extract text from <span> with class "_ml-1 _text-1 _text-gray-500 _font-weight _d-none _d-md-inline" for comments
            comments_span = div.find('span', class_='_ml-1 _text-1 _text-gray-500 _font-weight _d-none _d-md-inline')
            if comments_span:
                comments_text = comments_span.get_text().strip()
                numeric_comments = comments_text.replace('(', '').replace(')', '').replace('.', '')
                info['comments'] = int(numeric_comments)  # Convert to int
            else:
                info['comments'] = 0  # Default value if not found

            # Only add to result if we found something useful
            if info:
                result.append(info)
        
        return result

    except Exception as e:
        return f"An error occurred: {e}"


# Creates a dataframe with a list of dict's
def create_dataframe(info_list, csv_file_name=None):
    # Create a DataFrame from the list of dictionaries
    df = pd.DataFrame(info_list)
    
    # drop duplicates by product url because some products have the exact same name
    df = df.drop_duplicates(subset=['product_url'])

    # Reorder columns
    df = df[['product_name', 'currency', 'commission', 'max_price',
    'comment_rating', 'comments', 'temperature', 'product_url', 'img_src']]
    
    # If a filename is provided, export the DataFrame to a CSV file
    if csv_file_name:
        df.to_csv(f'{csv_file_name}.csv', index=False, encoding='utf-8-sig')
    return df


# Creates a interactive scatter plot with the data of a dataframe
def create_interactive_scatter_plot(df, file_name='scatter_plot'):
    # df filter
    df = df[(df["comment_rating"]>0)&(df["commission"]>0.0)].copy()

    # categorize comment_rating
    df['symbol'] = df["comment_rating"].astype(int)
    
    # Create a scatter plot with Plotly
    fig = px.scatter(
        df,
        x='max_price',
        y='commission',
        size=df['comments']+1,
        symbol='symbol',
        color='temperature',
        color_continuous_scale='OrRd',
        range_color=[0, 150],
        title='Scatter Plot of Commission vs Max Price with Regression Line<br><span>Filtered by comment_rating > 0 and commission > 0. Size is relative to total comments.</span>',
        category_orders={'symbol':[1, 2, 3, 4, 5]},
        labels={'symbol':'Symbol (comment rating)', 'size':'Size (comments)', 'currency':'Currency', 'commission':'Commission', 'max_price':'Max Price', 'comment_rating':'Comment Rating', 'comments':'Comments', 'temperature':'Temperature'},
        hover_name='product_name',
        hover_data=['currency', 'commission', 'max_price', 'comment_rating', 'comments', 'temperature'],
        trendline='ols',  # Adds the regression line
    )
    fig.update_traces(marker=dict(line=dict(width=1, color='white')))
    fig.update_layout(legend=dict(
        orientation="h",
        yanchor="bottom",
        y=1.02,
        xanchor="right",
        x=1))
    
    # Update layout for dark theme
    fig.update_layout(template='plotly_dark')
    
    # Save the plot to an HTML file
    fig.write_html(f'{file_name}.html')


# Run the app
def _main(path):
    # get html data
    html = get_file_text(path)

    # extract infos as a list
    info_list = extract_info_from_divs(html, "hot-col-xl-3 hot-col-lg-4 hot-col-md-6 hot-col-sm-12 _py-3")

    # export file name
    timenow = str(datetime.now())[:19].replace(":", "-").replace(" ", "_")
    file_name = f'analysis\hotmart_search_{timenow}'

    # create the dataframe
    df = create_dataframe(info_list, file_name)
    print(f'\n{df}\n')

    # plot insights
    create_interactive_scatter_plot(df, file_name)

####################################################################################################
# INPUT ############################################################################################
####################################################################################################

_main("search_data.txt")
